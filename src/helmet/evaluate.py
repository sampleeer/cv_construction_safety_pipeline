"""Evaluate the selected checkpoint on untouched test images; enforce release gates."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
import yaml
from ultralytics import YOLO

from src.cv.detector import sha256
from src.helmet.quality import passes_gate


def evaluate(dataset: Path, training: Path, config_path: Path, output: Path) -> dict[str, object]:
    config = yaml.safe_load(config_path.read_text())
    torch.set_num_threads(2)
    model = YOLO(str(training / 'best.pt'))
    result = model.val(data=str(dataset.resolve() / 'data.yaml'), split='test',
                       imgsz=config['imgsz'], batch=config['batch'], device='cpu',
                       workers=0, plots=False, verbose=False, project='runs/helmet-evaluation',
                       name=config['profile'])
    classes = {}
    for position, class_id in enumerate(result.box.ap_class_index):
        classes[model.names[int(class_id)]] = {
            'precision': float(result.box.p[position]), 'recall': float(result.box.r[position]),
            'map50': float(result.box.ap50[position]), 'map50_95': float(result.box.ap[position]),
        }
    no_helmet_recall = classes.get('no_helmet', {}).get('recall', 0.0)
    passed = passes_gate(float(result.box.map50), no_helmet_recall,
                         config['min_map50'], config['min_no_helmet_recall'])
    metrics = {'profile': config['profile'], 'split': 'test', 'input_size': config['imgsz'], 'checkpoint_sha256': sha256(training / 'best.pt'),
               'map50': float(result.box.map50), 'map50_95': float(result.box.map), 'classes': classes,
               'gate': {'passed': passed, 'min_map50': config['min_map50'],
                        'min_no_helmet_recall': config['min_no_helmet_recall']},
               'release_status': 'experimental' if config['profile'] == 'demo' else ('qualified' if passed else 'rejected')}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(metrics, indent=2) + '\n')
    if not passed:
        raise RuntimeError('Helmet quality gate failed; inspect the test metrics')
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, default=Path('data/helmet'))
    parser.add_argument('--training', type=Path, default=Path('models/helmet-training'))
    parser.add_argument('--config', type=Path, default=Path('params.yaml'))
    parser.add_argument('--output', type=Path, default=Path('reports/helmet-quality.json'))
    args = parser.parse_args()
    print(json.dumps(evaluate(args.dataset, args.training, args.config, args.output), indent=2))


if __name__ == '__main__':
    main()
