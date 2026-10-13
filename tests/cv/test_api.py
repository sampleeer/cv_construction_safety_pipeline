import io
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from src.api.main import create_app


def jpeg():
    stream = io.BytesIO()
    Image.new('RGB', (64, 32)).save(stream, format='JPEG')
    return stream.getvalue()


def test_api_real_onnx_inference_metadata_and_metrics(manifest):
    with TestClient(create_app(manifest)) as client:
        assert client.get('/health').status_code == 200
        assert client.get('/ready').status_code == 200
        assert client.get('/model').json()['version'] == 'test-fixture'
        result = client.post('/detect', content=jpeg(), headers={'Content-Type': 'image/jpeg'})
        assert result.status_code == 200
        assert result.json()['width'] == 64
        assert len(result.json()['detections']) == 2
        assert 'cv_requests_total{outcome="ok"} 1.0' in client.get('/metrics').text


def test_unavailable_model_is_not_ready(tmp_path):
    with TestClient(create_app(tmp_path / 'missing.json')) as client:
        assert client.get('/health').status_code == 200
        assert client.get('/ready').status_code == 503
        assert client.get('/model').status_code == 503
        assert client.post('/detect').status_code == 503


def test_invalid_input_does_not_leak_capacity(manifest):
    with TestClient(create_app(manifest, max_inflight=1)) as client:
        assert client.post('/detect', content=b'bad').status_code == 415
        assert client.post('/detect', content=b'bad', headers={'Content-Type': 'image/jpeg'}).status_code == 422
        assert client.post('/detect?confidence=2', content=jpeg(), headers={'Content-Type': 'image/jpeg'}).status_code == 422
        assert client.post('/detect', content=b'x' * (8 * 1024 * 1024 + 1),
                           headers={'Content-Type': 'image/jpeg'}).status_code == 413
        assert client.post('/detect', content=jpeg(), headers={'Content-Type': 'image/jpeg'}).status_code == 200


def test_overload_returns_429_and_recovers(manifest):
    entered, release = threading.Event(), threading.Event()
    app = create_app(manifest, max_inflight=1)
    with TestClient(app) as client:
        original = app.state.detector.predict

        def slow(*args):
            entered.set()
            assert release.wait(5)
            return original(*args)

        app.state.detector.predict = slow
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(client.post, '/detect', content=jpeg(), headers={'Content-Type': 'image/jpeg'})
            try:
                assert entered.wait(5)
                busy = client.post('/detect', content=jpeg(), headers={'Content-Type': 'image/jpeg'})
                assert busy.status_code == 429
                assert busy.headers['retry-after'] == '1'
            finally:
                release.set()
            assert pending.result().status_code == 200
        assert client.post('/detect', content=jpeg(), headers={'Content-Type': 'image/jpeg'}).status_code == 200


def test_invalid_concurrency_limit():
    with pytest.raises(ValueError):
        create_app(max_inflight=0)


def test_inference_failure_returns_500_and_releases_slot(manifest):
    app = create_app(manifest, max_inflight=1)
    with TestClient(app) as client:
        original = app.state.detector.predict

        def fail(*args):
            raise RuntimeError('internal model detail')

        app.state.detector.predict = fail
        response = client.post('/detect', content=jpeg(), headers={'Content-Type': 'image/jpeg'})
        assert response.status_code == 500
        assert 'internal model detail' not in response.text
        app.state.detector.predict = original
        assert client.post('/detect', content=jpeg(), headers={'Content-Type': 'image/jpeg'}).status_code == 200


def test_unsupported_image_format_is_rejected(manifest):
    stream = io.BytesIO()
    Image.new('RGB', (10, 10)).save(stream, format='GIF')
    with TestClient(create_app(manifest)) as client:
        assert client.post('/detect', content=stream.getvalue(),
                           headers={'Content-Type': 'image/png'}).status_code == 422
