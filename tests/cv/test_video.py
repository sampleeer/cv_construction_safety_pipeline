import json

import cv2
import httpx
import numpy as np
import pytest

from src.cv.video import LatestFrames, detect_remote, run


def test_latest_frame_replaces_pending_frame():
    frames = LatestFrames()
    image = np.zeros((32, 32, 3), dtype=np.uint8)
    frames.put((1, 0.0, image))
    frames.put((2, 0.1, image))
    assert frames.queue.get()[0] == 2
    assert frames.dropped == 1


def test_transient_failure_retries_once(monkeypatch):
    monkeypatch.setattr('src.cv.video.time.sleep', lambda _: None)
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(429 if len(calls) == 1 else 200, json={'detections': []})

    with httpx.Client(base_url='http://test', transport=httpx.MockTransport(handler)) as client:
        assert detect_remote(client, b'image') == {'detections': []}
        assert len(calls) == 2


def test_permanent_error_is_not_retried():
    with httpx.Client(base_url='http://test', transport=httpx.MockTransport(
        lambda _: httpx.Response(422))) as client:
        with pytest.raises(httpx.HTTPStatusError):
            detect_remote(client, b'bad')


def test_exhausted_retries_fail(monkeypatch):
    monkeypatch.setattr('src.cv.video.time.sleep', lambda _: None)
    with httpx.Client(base_url='http://test', transport=httpx.MockTransport(
        lambda _: httpx.Response(503))) as client:
        with pytest.raises(RuntimeError):
            detect_remote(client, b'image')


def test_video_file_capture_and_jsonl(tmp_path, monkeypatch):
    video = tmp_path / 'sample.avi'
    writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*'MJPG'), 10, (64, 48))
    assert writer.isOpened()
    for _ in range(5):
        writer.write(np.zeros((48, 64, 3), dtype=np.uint8))
    writer.release()
    monkeypatch.setattr('src.cv.video.detect_remote', lambda *args: {'detections': [], 'model_version': 'fixture'})
    output = tmp_path / 'result.jsonl'
    summary = run(str(video), 'http://test', output, max_frames=3)
    records = [json.loads(line) for line in output.read_text().splitlines()]
    assert summary['processed'] == 3 and summary['failed'] == 0
    indices = [record['frame_index'] for record in records]
    assert len(records) == 3 and indices == sorted(set(indices))
    assert all(0 <= index < 5 for index in indices)
    assert all(record['frame_age_ms'] >= 0 for record in records)


def test_missing_source_fails(tmp_path):
    with pytest.raises(ValueError, match='Cannot open'):
        run(str(tmp_path / 'missing.avi'), 'http://test', tmp_path / 'out.jsonl')


def test_inspection_read_timeout_is_not_retried(monkeypatch):
    calls = []

    def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout('Unknown server outcome', request=request)

    with httpx.Client(base_url='http://test', transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(httpx.ReadTimeout):
            detect_remote(client, b'image', camera_id='camera', frame_id=1)
    assert len(calls) == 1


def test_inspection_request_carries_camera_and_sequence():
    def handler(request):
        assert request.url.path == '/inspect'
        assert request.url.params['camera_id'] == 'camera'
        assert request.url.params['frame_id'] == '4'
        return httpx.Response(200, json={'event_changes': []})

    with httpx.Client(base_url='http://test', transport=httpx.MockTransport(handler)) as client:
        assert detect_remote(client, b'image', camera_id='camera', frame_id=4) == {'event_changes': []}
