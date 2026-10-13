"""Export a local YOLO11 checkpoint and verify PyTorch/ONNX numerical parity."""
from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import tempfile
from importlib.metadata import version
from pathlib import Path

import numpy as np
import onnxruntime as ort
import torch
import yaml
from ultralytics import YOLO

from src.cv.detector import sha256


def _build_release(checkpoint: Path, output_dir: Path, size: int = 320,
                 lineage_path: Path | None = None, quality_path: Path | None = None) -> dict[str, object]:
    if not checkpoint.is_file():
        raise FileNotFoundError(f'Download the checkpoint first: {checkpoint}')
    if size < 32 or size % 32:
        raise ValueError('Input size must be a positive multiple of 32')
    lineage = json.loads(lineage_path.read_text()) if lineage_path else None
    quality = json.loads(quality_path.read_text()) if quality_path else None
    if lineage and lineage['checkpoint_sha256'] != sha256(checkpoint):
        raise ValueError('Training lineage does not match checkpoint')
    if quality and (quality['checkpoint_sha256'] != sha256(checkpoint) or not quality['gate']['passed']):
        raise ValueError('Checkpoint has not passed evaluation')
    if quality and quality.get('input_size') != size:
        raise ValueError('Export and evaluation input sizes differ')
    model = YOLO(str(checkpoint), task='detect')
    exported = Path(model.export(format='onnx', imgsz=size, opset=17, simplify=False,
                                 dynamic=False, nms=False, batch=1, device='cpu'))
    # A seeded probe checks export parity, not detection accuracy on a dataset.
    probe = np.random.default_rng(42).random((1, 3, size, size), dtype=np.float32)
    with torch.inference_mode():
        model.model.eval()
        expected = model.model(torch.from_numpy(probe))[0].cpu().numpy()
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    session = ort.InferenceSession(str(exported), sess_options=options,
                                   providers=['CPUExecutionProvider'])
    actual = session.run(None, {session.get_inputs()[0].name: probe})[0]
    np.testing.assert_allclose(actual, expected, rtol=1e-3, atol=1e-3)
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact = output_dir / 'detector.onnx'
    shutil.copyfile(exported, artifact)
    try:
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
        dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip())
    except (OSError, subprocess.CalledProcessError):
        commit = 'unknown'
        dirty = True
    artifact_sha = sha256(artifact)
    metadata: dict[str, object] = {
        'version': artifact_sha[:12], 'artifact': artifact.name, 'sha256': artifact_sha,
        'source_checkpoint': checkpoint.name, 'source_sha256': sha256(checkpoint),
        'architecture': 'YOLO11n', 'task': 'helmet_monitoring' if lineage else 'object_detection',
        'dataset': lineage['dataset'] if lineage else 'COCO (pretrained)',
        'training': lineage, 'evaluation': quality,
        'release_status': quality['release_status'] if quality else 'generic',
        'labels': [model.names[index] for index in range(len(model.names))],
        'input_size': size, 'opset': 17, 'precision': 'FP32', 'git_commit': commit, 'git_dirty': dirty,
        'code_sha256': {f'src/cv/{path.name}': sha256(path) for path in
                        (Path(__file__), Path(__file__).with_name('detector.py'))},
        'python': platform.python_version(),
        'packages': {name: version(name) for name in ('ultralytics', 'torch', 'onnx', 'onnxruntime')},
        'parity': {'max_abs_error': float(np.max(np.abs(actual - expected))),
                   'rtol': 1e-3, 'atol': 1e-3, 'passed': True, 'probe_seed': 42},
    }
    (output_dir / 'manifest.json').write_text(json.dumps(metadata, indent=2) + '\n')
    return metadata


def export_model(checkpoint: Path, output_dir: Path, size: int = 320,
                 lineage_path: Path | None = None, quality_path: Path | None = None) -> dict[str, object]:
    """Export in isolation; publish model + manifest together only after all checks pass."""
    if not checkpoint.is_file():
        raise FileNotFoundError(checkpoint)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output_dir.parent) as temporary:
        workspace = Path(temporary)
        isolated_checkpoint = workspace / checkpoint.name
        shutil.copyfile(checkpoint, isolated_checkpoint)
        release = workspace / 'release'
        metadata = _build_release(isolated_checkpoint, release, size, lineage_path, quality_path)
        previous = workspace / 'previous'
        if output_dir.exists():
            output_dir.rename(previous)
        try:
            release.rename(output_dir)
        except OSError:
            if previous.exists():
                previous.rename(output_dir)
            raise
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', type=Path, default=Path('models/source/yolo11n.pt'))
    parser.add_argument('--output', type=Path, default=Path('models/cv'))
    parser.add_argument('--size', type=int, default=320)
    parser.add_argument('--lineage', type=Path)
    parser.add_argument('--quality', type=Path)
    parser.add_argument('--config', type=Path)
    args = parser.parse_args()
    size = int(yaml.safe_load(args.config.read_text())['imgsz']) if args.config else args.size
    export_model(args.checkpoint, args.output, size, args.lineage, args.quality)


if __name__ == '__main__':
    main()
