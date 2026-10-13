import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from src.api.main import create_app
from tests.helmet.test_rules import head


def image_bytes():
    stream = io.BytesIO()
    Image.new('RGB', (64, 64)).save(stream, format='JPEG')
    return stream.getvalue()


@pytest.fixture
def manifest(tmp_path):
    # Share the real ONNX infrastructure fixture used by the generic detection tests.
    from tests.cv.conftest import manifest as fixture
    return fixture.__wrapped__(tmp_path)


def test_dashboard_and_generic_weights_cannot_generate_helmet_events(manifest, tmp_path):
    with TestClient(create_app(manifest, event_db=tmp_path / 'events.sqlite')) as client:
        assert 'HelmetWatch' in client.get('/').text
        result = client.post('/inspect?camera_id=a&frame_id=0', content=image_bytes(),
                             headers={'Content-Type': 'image/jpeg'})
        assert result.status_code == 503
        assert client.get('/events').json() == []
        assert client.get('/events/missing/snapshot').status_code == 404


def test_confirmed_event_snapshot_duplicate_frame_and_session_end(manifest, tmp_path, monkeypatch):
    app = create_app(manifest, event_db=tmp_path / 'events.sqlite', snapshot_dir=tmp_path / 'snapshots')
    clock = {'now': 100.0}
    with TestClient(app) as client:
        monkeypatch.setattr('src.api.main.time.time', lambda: clock['now'])
        app.state.detector.labels = ['helmet', 'no_helmet', 'person']
        app.state.detector.predict = lambda *args: [head()]
        for frame in range(3):
            clock['now'] = 100 + frame * .5
            response = client.post(f'/inspect?camera_id=a&frame_id={frame}', content=image_bytes(),
                                   headers={'Content-Type': 'image/jpeg'})
            assert response.status_code == 200
        assert response.json()['event_changes'][0]['kind'] == 'started'
        events = client.get('/events?camera_id=a').json()
        assert len(events) == 1 and events[0]['status'] == 'open'
        snapshot = client.get(events[0]['snapshot_url'])
        assert snapshot.status_code == 200 and snapshot.headers['content-type'] == 'image/jpeg'
        duplicate = client.post('/inspect?camera_id=a&frame_id=2', content=image_bytes(),
                                headers={'Content-Type': 'image/jpeg'})
        assert duplicate.status_code == 409 and len(client.get('/events').json()) == 1
        assert client.post('/cameras/a/end').status_code == 200
        assert client.get('/events').json()[0]['end_reason'] == 'stream_ended'
        assert 'helmet_events_total 1.0' in client.get('/metrics').text


def test_failed_journal_write_restores_rules_and_removes_orphan_snapshot(manifest, tmp_path, monkeypatch):
    app = create_app(manifest, event_db=tmp_path / 'events.sqlite', snapshot_dir=tmp_path / 'snapshots')
    clock = {'now': 100.0}
    with TestClient(app) as client:
        monkeypatch.setattr('src.api.main.time.time', lambda: clock['now'])
        app.state.detector.labels = ['helmet', 'no_helmet', 'person']
        app.state.detector.predict = lambda *args: [head()]
        for frame in range(2):
            clock['now'] = 100 + frame * .5
            assert client.post(f'/inspect?camera_id=a&frame_id={frame}', content=image_bytes(),
                               headers={'Content-Type': 'image/jpeg'}).status_code == 200
        original = app.state.store.record

        def fail(changes):
            raise OSError('Disk unavailable')

        app.state.store.record = fail
        clock['now'] = 101
        result = client.post('/inspect?camera_id=a&frame_id=2', content=image_bytes(),
                             headers={'Content-Type': 'image/jpeg'})
        assert result.status_code == 500
        assert not list((tmp_path / 'snapshots').glob('*.jpg'))
        app.state.store.record = original
        result = client.post('/inspect?camera_id=a&frame_id=2', content=image_bytes(),
                             headers={'Content-Type': 'image/jpeg'})
        assert result.status_code == 200 and len(client.get('/events').json()) == 1
