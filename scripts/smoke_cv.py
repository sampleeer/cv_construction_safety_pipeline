"""Functional checks against a running server; no external sample image required."""
import argparse
import io

import httpx
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument('--url', default='http://localhost:8000')
args = parser.parse_args()
buffer = io.BytesIO()
Image.new('RGB', (640, 480), 'white').save(buffer, format='JPEG')
with httpx.Client(base_url=args.url, timeout=30) as client:
    for endpoint in ('/health', '/ready', '/model', '/metrics'):
        client.get(endpoint).raise_for_status()
    metadata = client.get('/model').json()
    assert set(metadata['labels']) == {'helmet', 'no_helmet', 'person'}
    assert client.get('/events').status_code == 200
    assert client.get('/').status_code == 200
    inspect = client.post('/inspect?camera_id=smoke&frame_id=0', content=buffer.getvalue(),
                          headers={'Content-Type': 'image/jpeg'})
    inspect.raise_for_status()
    client.post('/cameras/smoke/end').raise_for_status()
    response = client.post('/detect', content=buffer.getvalue(), headers={'Content-Type': 'image/jpeg'})
    response.raise_for_status()
    assert isinstance(response.json()['detections'], list)
    assert response.json()['model_version']
    invalid = client.post('/detect', content=b'bad', headers={'Content-Type': 'image/jpeg'})
    assert invalid.status_code == 422
print('HelmetWatch API smoke checks passed')
