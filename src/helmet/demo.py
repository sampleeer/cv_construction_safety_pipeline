"""Create a reproducible successful validation example and a replay clip for event testing."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2

from src.cv.detector import Detector
from src.helmet.events import overlap


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, default=Path('data/helmet'))
    parser.add_argument('--manifest', type=Path, default=Path('models/cv/manifest.json'))
    parser.add_argument('--output', type=Path, default=Path('artifacts'))
    args = parser.parse_args()
    detector = Detector(args.manifest)
    for path in sorted((args.dataset / 'images/val').glob('*')):
        label = args.dataset / 'labels/val' / (path.stem + '.txt')
        targets = [list(map(float, line.split()[1:])) for line in label.read_text().splitlines()
                   if line.startswith('1 ')]
        if not targets:
            continue
        image = cv2.imread(str(path))
        if image is None:
            raise ValueError(f'Invalid image: {path}')
        height, width = image.shape[:2]
        boxes = [((x - bw / 2) * width, (y - bh / 2) * height,
                  (x + bw / 2) * width, (y + bh / 2) * height) for x, y, bw, bh in targets]
        correct = [item for item in detector.predict(image, confidence=.4)
                   if item.label == 'no_helmet' and any(overlap(item.box, box) >= .5 for box in boxes)]
        if not correct:
            continue
        args.output.mkdir(parents=True, exist_ok=True)
        if not cv2.imwrite(str(args.output / 'helmet-sample.jpg'), image):
            raise OSError('Could not write demo image')
        clip = cv2.resize(image, (max(2, round(480 * width / height) // 2 * 2), 480))
        writer = cv2.VideoWriter(str(args.output / 'helmet-demo.avi'), cv2.VideoWriter_fourcc(*'MJPG'),
                                 10, (clip.shape[1], clip.shape[0]))
        if not writer.isOpened():
            raise OSError('MJPEG video writer unavailable')
        try:
            for _ in range(40):
                writer.write(clip)
        finally:
            writer.release()
        result = {'source': str(path), 'correct_no_helmet_detections': len(correct),
                  'confidence': [item.confidence for item in correct],
                  'note': 'Selected successful validation example; replayed still image, not real camera footage'}
        (args.output / 'helmet-demo-source.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result))
        return
    raise SystemExit('No correct no_helmet validation example at confidence 0.4')


if __name__ == '__main__':
    main()
