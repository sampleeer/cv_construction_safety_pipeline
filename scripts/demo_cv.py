"""Submit an image to the API and save an annotated detection preview."""
import argparse
from pathlib import Path

import cv2
import httpx

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--image', type=Path, required=True)
parser.add_argument('--url', default='http://localhost:8000')
parser.add_argument('--output', type=Path, default=Path('artifacts/detection.jpg'))
args = parser.parse_args()
image = cv2.imread(str(args.image))
if image is None:
    raise SystemExit(f'Cannot read {args.image}')
ok, encoded = cv2.imencode('.jpg', image)
if not ok:
    raise SystemExit('JPEG encoding failed')
response = httpx.post(args.url + '/detect', content=encoded.tobytes(),
                      headers={'Content-Type': 'image/jpeg'}, timeout=30)
response.raise_for_status()
result = response.json()
for detection in result['detections']:
    x1, y1, x2, y2 = [round(value) for value in detection['box']]
    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 200, 0), 3)
    label = f"{detection['label']} {detection['confidence']:.2f}"
    cv2.putText(image, label, (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, .7, (0, 140, 0), 2)
args.output.parent.mkdir(parents=True, exist_ok=True)
if not cv2.imwrite(str(args.output), image):
    raise SystemExit('Cannot write preview')
print(f"{len(result['detections'])} detections, {result['inference_ms']} ms; preview: {args.output}")
