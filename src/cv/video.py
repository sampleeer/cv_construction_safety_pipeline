"""Video/camera client: latest-frame queue and bounded HTTP retries."""
from __future__ import annotations

import argparse
import json
import queue
import threading
import time
from pathlib import Path
from typing import Any, cast

import cv2
import httpx

from src.cv.detector import ImageArray


class LatestFrames:
    """Drop old pending frames when inference cannot keep up with capture."""
    def __init__(self) -> None:
        self.queue: queue.Queue[tuple[int, float, ImageArray]] = queue.Queue(maxsize=1)
        self.dropped = 0

    def put(self, item: tuple[int, float, ImageArray]) -> None:
        try:
            self.queue.put_nowait(item)
        except queue.Full:
            try:
                self.queue.get_nowait()
                self.dropped += 1
            except queue.Empty:
                pass
            self.queue.put_nowait(item)


def detect_remote(client: httpx.Client, payload: bytes, attempts: int = 3,
                  camera_id: str | None = None, frame_id: int | None = None) -> dict[str, Any]:
    for attempt in range(attempts):
        try:
            response = client.post('/inspect' if camera_id else '/detect', content=payload,
                                   params={'camera_id': camera_id, 'frame_id': frame_id} if camera_id else None,
                                   headers={'Content-Type': 'image/jpeg'})
            if response.status_code not in {429, 503}:
                response.raise_for_status()
                return response.json()
        except httpx.TransportError as error:
            if camera_id and not isinstance(error, (httpx.ConnectError, httpx.ConnectTimeout)):
                raise
            if attempt == attempts - 1:
                raise
        if attempt < attempts - 1:
            time.sleep(0.2 * 2 ** attempt)
    raise RuntimeError('Server unavailable after bounded retries')


def run(source: str, base_url: str, output: Path, max_frames: int = 0,
        camera_id: str | None = None) -> dict[str, int]:
    capture = cv2.VideoCapture(int(source) if source.isdigit() else source)
    if not capture.isOpened():
        raise ValueError(f'Cannot open video source: {source}')
    frames = LatestFrames()
    stop = threading.Event()
    finished = threading.Event()
    errors: list[BaseException] = []
    fps = capture.get(cv2.CAP_PROP_FPS)
    fps = fps if 0 < fps < 240 else 25.0
    live = source.isdigit() or '://' in source

    def read_frames() -> None:
        try:
            index = 0
            while not stop.is_set():
                started = time.monotonic()
                ok, image = capture.read()
                if not ok:
                    break
                frames.put((index, started, cast(ImageArray, image)))
                index += 1
                # Replay files at original FPS instead of draining the file instantly.
                if not live:
                    stop.wait(max(0.0, 1 / fps - (time.monotonic() - started)))
        except BaseException as error:
            errors.append(error)
        finally:
            capture.release()
            finished.set()

    reader = threading.Thread(target=read_frames, name='capture', daemon=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    processed, failed = 0, 0
    reader.start()
    try:
        with httpx.Client(base_url=base_url, timeout=10) as client, output.open('w') as stream:
            while not finished.is_set() or not frames.queue.empty():
                try:
                    index, captured, image = frames.queue.get(timeout=0.2)
                except queue.Empty:
                    continue
                ok, encoded = cv2.imencode('.jpg', image)
                if not ok:
                    failed += 1
                    continue
                try:
                    result = (detect_remote(client, encoded.tobytes(), camera_id=camera_id, frame_id=index)
                              if camera_id else detect_remote(client, encoded.tobytes()))
                except (httpx.HTTPError, RuntimeError) as error:
                    failed += 1
                    print(f'Frame {index}: {error}')
                    continue
                result.update(frame_index=index, frame_age_ms=round((time.monotonic() - captured) * 1000, 2))
                stream.write(json.dumps(result) + '\n')
                stream.flush()
                processed += 1
                if max_frames and processed >= max_frames:
                    break
    finally:
        stop.set()
        reader.join(timeout=5)
        if camera_id:
            try:
                with httpx.Client(base_url=base_url, timeout=10) as end_client:
                    end_client.post(f'/cameras/{camera_id}/end').raise_for_status()
            except httpx.HTTPError as error:
                failed += 1
                print(f'Could not close camera session: {error}')
    if reader.is_alive():
        raise RuntimeError('Capture did not stop; video backend read may be blocked')
    if errors:
        raise RuntimeError('Capture failed') from errors[0]
    summary = {'processed': processed, 'failed': failed, 'dropped': frames.dropped}
    print(json.dumps(summary))
    if processed == 0 or failed:
        raise RuntimeError(f'Video run incomplete: {summary}')
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, help='Video path, camera index, or stream URL')
    parser.add_argument('--url', default='http://localhost:8000')
    parser.add_argument('--output', type=Path, default=Path('reports/video.jsonl'))
    parser.add_argument('--max-frames', type=int, default=0)
    parser.add_argument('--inspect', action='store_true', help='Record confirmed helmet violations')
    parser.add_argument('--camera', default='site-1', help='Unique camera session ID')
    args = parser.parse_args()
    run(args.source, args.url, args.output, args.max_frames, args.camera if args.inspect else None)


if __name__ == '__main__':
    main()
