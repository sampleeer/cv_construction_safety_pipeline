"""YOLO11 detection with ONNX Runtime; no PyTorch in the serving process."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import numpy.typing as npt
import onnxruntime as ort

ImageArray = npt.NDArray[np.uint8]
FloatArray = npt.NDArray[np.float32]


@dataclass(frozen=True)
class Detection:
    class_id: int
    label: str
    confidence: float
    box: tuple[float, float, float, float]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def preprocess(image: ImageArray, size: int) -> tuple[FloatArray, float, tuple[int, int]]:
    """Letterbox BGR input, then convert to normalized RGB NCHW."""
    height, width = image.shape[:2]
    scale = min(size / width, size / height)
    new_width, new_height = max(1, round(width * scale)), max(1, round(height * scale))
    resized = cv2.resize(image, (new_width, new_height))
    left, top = (size - new_width) // 2, (size - new_height) // 2
    canvas = np.full((size, size, 3), 114, dtype=np.uint8)
    canvas[top:top + new_height, left:left + new_width] = resized
    tensor = canvas[:, :, ::-1].transpose(2, 0, 1)[None].astype(np.float32) / 255.0
    return np.ascontiguousarray(tensor), scale, (left, top)


def postprocess(
    output: FloatArray, image_shape: tuple[int, ...], scale: float,
    padding: tuple[int, int], labels: list[str], confidence: float, iou: float,
    max_detections: int = 100,
) -> list[Detection]:
    """Decode raw [1, 4 + classes, anchors] output and apply class-aware NMS."""
    if output.ndim != 3 or output.shape[0] != 1 or output.shape[1] != 4 + len(labels):
        raise ValueError('Expected YOLO11 detect output [1, 4 + classes, anchors]')
    predictions = output[0].T
    if not np.isfinite(predictions).all():
        raise ValueError('Model produced non-finite predictions')
    scores = predictions[:, 4:]
    classes = scores.argmax(axis=1)
    best_scores = scores.max(axis=1)
    mask = best_scores >= confidence
    predictions, classes, best_scores = predictions[mask], classes[mask], best_scores[mask]
    if not len(predictions):
        return []
    boxes = predictions[:, :4].copy()
    boxes[:, :2] -= boxes[:, 2:] / 2  # xywh center -> xywh top-left
    boxes[:, 0] = (boxes[:, 0] - padding[0]) / scale
    boxes[:, 1] = (boxes[:, 1] - padding[1]) / scale
    boxes[:, 2:] /= scale
    detections: list[Detection] = []
    for class_id in np.unique(classes):
        positions = np.flatnonzero(classes == class_id)
        kept = cv2.dnn.NMSBoxes(
            boxes[positions].tolist(), best_scores[positions].tolist(),
            confidence, iou,
        )
        for local_index in np.asarray(kept).reshape(-1):
            index = positions[int(local_index)]
            x, y, width, height = boxes[index]
            image_height, image_width = image_shape[:2]
            box = (
                float(np.clip(x, 0, image_width)), float(np.clip(y, 0, image_height)),
                float(np.clip(x + width, 0, image_width)),
                float(np.clip(y + height, 0, image_height)),
            )
            if box[2] > box[0] and box[3] > box[1]:
                detections.append(Detection(int(class_id), labels[int(class_id)],
                                            float(best_scores[index]), box))
    return sorted(detections, key=lambda item: item.confidence, reverse=True)[:max_detections]


class Detector:
    def __init__(self, manifest_path: Path, threads: int = 2) -> None:
        self.metadata: dict[str, Any] = json.loads(manifest_path.read_text())
        self.model_path = manifest_path.parent / self.metadata['artifact']
        if sha256(self.model_path) != self.metadata['sha256']:
            raise ValueError('Model checksum does not match manifest')
        self.labels: list[str] = self.metadata['labels']
        self.size = int(self.metadata['input_size'])
        options = ort.SessionOptions()
        options.intra_op_num_threads = threads
        options.inter_op_num_threads = 1
        self.session = ort.InferenceSession(str(self.model_path), sess_options=options,
                                            providers=['CPUExecutionProvider'])
        inputs = self.session.get_inputs()
        if len(inputs) != 1 or inputs[0].type != 'tensor(float)' or inputs[0].shape != [1, 3, self.size, self.size]:
            raise ValueError('Expected static float32 input [1, 3, size, size]')
        self.input_name = inputs[0].name
        # Fail startup on incompatible output format, rather than on the first request.
        self.predict(np.zeros((self.size, self.size, 3), dtype=np.uint8))

    def predict(self, image: ImageArray, confidence: float = 0.25,
                iou: float = 0.45) -> list[Detection]:
        tensor, scale, padding = preprocess(image, self.size)
        output = self.session.run(None, {self.input_name: tensor})[0]
        return postprocess(output, image.shape, scale, padding, self.labels, confidence, iou)
