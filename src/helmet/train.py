"""Fine-tune YOLO on helmet/no_helmet/person and retain dataset provenance."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import torch
import yaml
from ultralytics import YOLO

from src.cv.detector import sha256


def train(dataset: Path, config_path: Path, checkpoint: Path, output: Path) -> None:
    config = yaml.safe_load(config_path.read_text())
    metadata = json.loads((dataset / 'manifest.json').read_text())
    if metadata['profile'] != config['profile']:
        raise ValueError('Prepared dataset and training profile differ')
    torch.set_num_threads(2)
    device = config['device']
    if device == 'auto':
        device = 0 if torch.cuda.is_available() else ('mps' if torch.backends.mps.is_available() else 'cpu')
    model = YOLO(str(checkpoint))
    model.train(data=str(dataset / 'data.yaml'), epochs=config['epochs'], imgsz=config['imgsz'],
                batch=config['batch'], freeze=config['freeze'], device=device, workers=config['workers'],
                seed=config['seed'], deterministic=True, project='runs/helmet', name=config['profile'],
                exist_ok=False, pretrained=True, plots=False, save=True, amp=False, mosaic=0.0,
                cache=False, verbose=False)
    output.mkdir(parents=True, exist_ok=True)
    best = Path(model.trainer.best)
    shutil.copyfile(best, output / 'best.pt')
    lineage = {'dataset': 'Construction-PPE (helmet/no_helmet/person subset)',
               'dataset_fingerprint': metadata['fingerprint'], 'archive_sha256': metadata['archive_sha256'],
               'profile': config['profile'], 'training_config': config, 'device': device,
               'base_checkpoint_sha256': sha256(checkpoint), 'checkpoint_sha256': sha256(output / 'best.pt'),
               'run_directory': str(model.trainer.save_dir), 'split_counts':
               {split: data['images'] for split, data in metadata['splits'].items()}}
    (output / 'lineage.json').write_text(json.dumps(lineage, indent=2) + '\n')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, default=Path('data/helmet'))
    parser.add_argument('--config', type=Path, default=Path('params.yaml'))
    parser.add_argument('--checkpoint', type=Path, default=Path('models/source/yolo11n.pt'))
    parser.add_argument('--output', type=Path, default=Path('models/helmet-training'))
    args = parser.parse_args()
    train(args.dataset.resolve(), args.config, args.checkpoint, args.output)


if __name__ == '__main__':
    main()
