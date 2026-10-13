import json

import numpy as np
import pytest

from src.cv.benchmark import benchmark
from src.cv.detector import Detector, postprocess, preprocess


def test_letterbox_preserves_aspect_and_rgb():
    image = np.zeros((20, 40, 3), dtype=np.uint8)
    image[:] = [0, 0, 255]
    tensor, scale, padding = preprocess(image, 32)
    assert tensor.shape == (1, 3, 32, 32)
    assert tensor.dtype == np.float32
    assert scale == .8 and padding == (0, 8)
    assert tensor[0, 0, 8, 0] == 1
    assert tensor[0, 2, 8, 0] == 0


def test_real_onnx_class_aware_nms_and_coordinate_restore(manifest):
    detector = Detector(manifest)
    result = detector.predict(np.zeros((32, 64, 3), dtype=np.uint8))
    assert [item.label for item in result] == ['person', 'car']
    assert result[0].box == (16, 0, 48, 32)
    assert detector.predict(np.zeros((32, 32, 3), dtype=np.uint8), confidence=.99) == []


def test_checksum_tamper_fails_before_session_load(manifest):
    metadata = json.loads(manifest.read_text())
    metadata['sha256'] = 'wrong'
    manifest.write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match='checksum'):
        Detector(manifest)


@pytest.mark.parametrize('output', [np.zeros((1, 5, 2), dtype=np.float32),
                                     np.full((1, 6, 2), np.nan, dtype=np.float32)])
def test_invalid_model_output_is_rejected(output):
    with pytest.raises(ValueError):
        postprocess(output, (32, 32, 3), 1, (0, 0), ['person', 'car'], .25, .45)


def test_benchmark_has_model_identity_and_latency(manifest):
    result = benchmark(manifest, repeats=3)
    assert result['model_version'] == 'test-fixture'
    assert result['p95_ms'] > 0 and result['sequential_fps'] > 0
    with pytest.raises(ValueError):
        benchmark(manifest, repeats=1)


def test_extremely_narrow_image_does_not_produce_zero_resize_dimension():
    tensor, _, _ = preprocess(np.zeros((1000, 1, 3), dtype=np.uint8), 32)
    assert tensor.shape == (1, 3, 32, 32)
