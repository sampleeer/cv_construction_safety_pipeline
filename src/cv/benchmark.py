"""Measure local end-to-end detector latency; synthetic input is not an accuracy test."""
from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path
from typing import cast

import numpy as np

from src.cv.detector import Detector


def benchmark(manifest: Path, repeats: int = 30, threads: int = 2) -> dict[str, object]:
    if repeats < 2:
        raise ValueError('At least two repetitions required')
    detector = Detector(manifest, threads)
    image = np.random.default_rng(42).integers(0, 256, (480, 640, 3), dtype=np.uint8)
    for _ in range(5):
        detector.predict(image)
    elapsed = []
    for _ in range(repeats):
        started = time.perf_counter()
        detector.predict(image)
        elapsed.append((time.perf_counter() - started) * 1000)
    return {
        'model_version': detector.metadata['version'], 'model_sha256': detector.metadata['sha256'],
        'input': 'seeded synthetic 640x480 BGR image; NOT a dataset accuracy evaluation',
        'input_size': detector.size, 'platform': platform.platform(),
        'machine': platform.machine(), 'python': platform.python_version(),
        'providers': detector.session.get_providers(), 'ort_threads': threads,
        'repeats': repeats, 'warmup': 5, 'mean_ms': float(np.mean(elapsed)),
        'p50_ms': float(np.percentile(elapsed, 50)), 'p95_ms': float(np.percentile(elapsed, 95)),
        'sequential_fps': 1000 / float(np.mean(elapsed)),
        'scope': 'preprocess + ONNX inference + NMS; excludes network and image decoding',
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=Path('models/cv/manifest.json'))
    parser.add_argument('--output', type=Path, default=Path('reports/cv-benchmark.json'))
    parser.add_argument('--repeats', type=int, default=30)
    parser.add_argument('--threads', type=int, default=2)
    parser.add_argument('--max-p95-ms', type=float, default=None)
    args = parser.parse_args()
    result = benchmark(args.manifest, args.repeats, args.threads)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    if args.max_p95_ms is not None and cast(float, result['p95_ms']) > args.max_p95_ms:
        raise SystemExit('Latency gate failed')


if __name__ == '__main__':
    main()
