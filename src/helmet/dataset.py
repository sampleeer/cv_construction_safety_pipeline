"""Prepare an audited three-class YOLO dataset from the official PPE archive."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import yaml
from PIL import Image

from src.cv.detector import sha256

SOURCE_URL = 'https://github.com/ultralytics/assets/releases/download/v0.0.0/construction-ppe.zip'
CLASS_MAP = {0: 0, 7: 1, 6: 2}
LABELS = ['helmet', 'no_helmet', 'person']


def convert_labels(text: str) -> list[str]:
    result = []
    for line in text.splitlines():
        values = line.split()
        if not values:
            continue
        if len(values) != 5:
            raise ValueError('Expected YOLO detection label: class x y width height')
        class_id = int(values[0])
        if class_id not in range(11):
            raise ValueError('Unknown source class')
        coordinates = [float(value) for value in values[1:]]
        if not all(0 <= value <= 1 for value in coordinates) or coordinates[2] <= 0 or coordinates[3] <= 0:
            raise ValueError('Invalid normalized bounding box')
        if class_id in CLASS_MAP:
            result.append(str(CLASS_MAP[class_id]) + ' ' + ' '.join(values[1:]))
    return result


def prepare(archive: Path, output: Path, config_path: Path) -> dict[str, Any]:
    config = yaml.safe_load(config_path.read_text())
    if output.exists():
        marker = output / 'manifest.json'
        if not marker.is_file() or json.loads(marker.read_text()).get('source_url') != SOURCE_URL:
            raise FileExistsError(f'Refusing to replace a directory not created by this pipeline: {output}')
    output.parent.mkdir(parents=True, exist_ok=True)
    counts: dict[str, Any] = {}
    seen: set[str] = set()
    # Preserve official split membership. Prefer test over val over train for exact duplicates.
    with tempfile.TemporaryDirectory(dir=output.parent) as temporary:
        temporary_path = Path(temporary)
        with zipfile.ZipFile(archive) as bundle:
            for member in bundle.infolist():
                path = Path(member.filename)
                if path.is_absolute() or '..' in path.parts:
                    raise ValueError('Unsafe archive path')
            bundle.extractall(temporary_path)
        matches = list(temporary_path.rglob('images/train'))
        if len(matches) != 1:
            raise ValueError('Expected exactly one official images/train directory')
        source = matches[0].parent.parent
        # Build in temporary storage; publish only a complete prepared dataset.
        prepared = temporary_path / 'prepared'
        entries = []
        for split in ('test', 'val', 'train'):
            candidates = sorted((source / 'images' / split).glob('*'))
            candidates = [path for path in candidates if path.suffix.lower() in {'.jpg', '.jpeg', '.png'}]
            random.Random(int(config['seed'])).shuffle(candidates)
            if split == 'train' and config.get('prioritize_no_helmet', False):
                def priority(image: Path) -> bool:
                    label = source / 'labels' / split / (image.stem + '.txt')
                    return not any(line.split()[0] == '7' for line in label.read_text().splitlines() if line.strip())
                candidates.sort(key=priority)
            records: list[dict[str, str]] = []
            duplicates = 0
            limit = int(config[f'max_{split}'])
            for image in candidates:
                image_sha = sha256(image)
                if image_sha in seen:
                    duplicates += 1
                    continue
                # Mark every image, including images excluded by demo limits, to avoid split leakage.
                seen.add(image_sha)
                annotation = source / 'labels' / split / (image.stem + '.txt')
                if not annotation.exists():
                    raise FileNotFoundError(f'Missing annotation: {annotation}')
                labels = convert_labels(annotation.read_text())
                with Image.open(image) as picture:
                    picture.verify()
                if limit and len(records) >= limit:
                    continue
                image_dest = prepared / 'images' / split / image.name
                label_dest = prepared / 'labels' / split / annotation.name
                image_dest.parent.mkdir(parents=True, exist_ok=True)
                label_dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(image, image_dest)
                label_dest.write_text('\n'.join(labels) + ('\n' if labels else ''))
                records.append({'image': image.name, 'image_sha256': image_sha,
                                'labels_sha256': sha256(label_dest)})
                entries.append(f'{split}/{image.name}:{image_sha}:{sha256(label_dest)}')
            if not records:
                raise ValueError(f'Empty split: {split}')
            class_counts = [0, 0, 0]
            for label_file in (prepared / 'labels' / split).glob('*.txt'):
                for line in label_file.read_text().splitlines():
                    class_counts[int(line.split()[0])] += 1
            counts[split] = {'images': len(records), 'objects': dict(zip(LABELS, class_counts)),
                             'duplicates_removed': duplicates, 'samples': records}
        fingerprint = hashlib.sha256('\n'.join(sorted(entries)).encode()).hexdigest()
        metadata = {'source_url': SOURCE_URL, 'archive_sha256': sha256(archive),
                    'license': 'AGPL-3.0 (upstream dataset)', 'profile': config['profile'],
                    'seed': config['seed'], 'labels': LABELS, 'fingerprint': fingerprint, 'splits': counts}
        (prepared / 'manifest.json').write_text(json.dumps(metadata, indent=2) + '\n')
        # Omit path: the absolute YAML filename supplied by train/evaluate defines the root.
        dataset_yaml = {'train': 'images/train', 'val': 'images/val',
                        'test': 'images/test', 'names': dict(enumerate(LABELS))}
        (prepared / 'data.yaml').write_text(yaml.safe_dump(dataset_yaml, sort_keys=False))
        if output.exists():
            shutil.rmtree(output)
        shutil.move(str(prepared), output)
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, default=Path('data/raw/ppe/construction-ppe.zip'))
    parser.add_argument('--output', type=Path, default=Path('data/helmet'))
    parser.add_argument('--config', type=Path, default=Path('params.yaml'))
    args = parser.parse_args()
    result = prepare(args.archive, args.output, args.config)
    print(json.dumps({split: values['images'] for split, values in result['splits'].items()}))


if __name__ == '__main__':
    main()
