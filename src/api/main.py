"""Bounded CV serving API with readiness and Prometheus metrics."""
from __future__ import annotations

import io
import logging
import os
import threading
import time
from contextlib import asynccontextmanager
from dataclasses import asdict
from copy import deepcopy
from pathlib import Path
from typing import AsyncIterator, cast

import cv2
import numpy as np
from fastapi import FastAPI, HTTPException, Query, Request
from PIL import Image, ImageOps, UnidentifiedImageError
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Histogram, generate_latest
from starlette.concurrency import run_in_threadpool
from starlette.responses import Response, FileResponse, HTMLResponse

from src.cv.detector import Detector, ImageArray
from src.helmet.events import HelmetRules, OutOfOrderFrame
from src.helmet.store import EventStore

logger = logging.getLogger(__name__)
MAX_BODY_BYTES = 8 * 1024 * 1024
MAX_IMAGE_PIXELS = 12_000_000


def create_app(manifest: Path | None = None, max_inflight: int = 2,
               event_db: Path | None = None, snapshot_dir: Path | None = None) -> FastAPI:
    if max_inflight < 1:
        raise ValueError('max_inflight must be positive')
    registry = CollectorRegistry()
    requests = Counter('cv_requests_total', 'Detection requests by outcome', ['outcome'], registry=registry)
    latency = Histogram('cv_inference_seconds', 'Decode and detection latency', registry=registry)
    slots = threading.BoundedSemaphore(max_inflight)
    rules = HelmetRules()
    event_lock = threading.Lock()
    snapshots = snapshot_dir or Path(os.getenv('HELMET_SNAPSHOTS', 'artifacts/snapshots'))
    events_created = Counter('helmet_events_total', 'Confirmed no-helmet events', registry=registry)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.store = EventStore(event_db or Path(os.getenv('HELMET_DB', 'artifacts/events.sqlite')))
        app.state.store.close_interrupted(time.time())
        app.state.detector = None
        app.state.load_error = None
        try:
            app.state.detector = await run_in_threadpool(
                Detector, manifest or Path(os.getenv('CV_MANIFEST', 'models/cv/manifest.json')),
                int(os.getenv('ORT_THREADS', '2')),
            )
        except Exception:
            logger.exception('Model initialization failed')
            app.state.load_error = 'Model unavailable; check server logs'
        yield
        app.state.detector = None

    app = FastAPI(title='HelmetWatch — Construction Helmet Monitoring', version='2.0.0', lifespan=lifespan)

    @app.get('/', response_class=HTMLResponse)
    def dashboard() -> HTMLResponse:
        return HTMLResponse((Path(__file__).resolve().parents[1] / 'helmet' / 'dashboard.html').read_text())

    @app.get('/events')
    def events(request: Request, camera_id: str | None = Query(None, pattern=r'^[a-zA-Z0-9_-]{1,64}$'),
               limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)) -> list[dict[str, object]]:
        return request.app.state.store.list(camera_id, limit, offset)

    @app.get('/events/{event_id}/snapshot')
    def snapshot(request: Request, event_id: str) -> FileResponse:
        name = request.app.state.store.snapshot(event_id)
        if not name or Path(name).name != name or not (snapshots / name).is_file():
            raise HTTPException(404, 'Snapshot not found')
        return FileResponse(snapshots / name, media_type='image/jpeg')

    @app.post('/cameras/{camera_id}/end')
    def end_camera(request: Request, camera_id: str) -> dict[str, str]:
        with event_lock:
            previous = deepcopy(rules.cameras)
            try:
                changes = rules.finish(camera_id, time.time())
                request.app.state.store.record(changes)
            except Exception:
                rules.cameras = previous
                raise
        return {'status': 'ended'}

    @app.get('/health')
    def health() -> dict[str, str]:
        return {'status': 'ok'}

    @app.get('/ready')
    def ready(request: Request) -> dict[str, str]:
        if request.app.state.detector is None:
            raise HTTPException(503, request.app.state.load_error)
        return {'status': 'ready'}

    @app.get('/model')
    def model(request: Request) -> dict[str, object]:
        detector = request.app.state.detector
        if detector is None:
            raise HTTPException(503, request.app.state.load_error)
        return {**detector.metadata, 'providers': detector.session.get_providers()}

    @app.get('/metrics')
    def metrics() -> Response:
        return Response(generate_latest(registry), headers={'Content-Type': CONTENT_TYPE_LATEST})

    def infer(payload: bytes, detector: Detector, confidence: float, iou: float,
              camera_id: str | None = None, frame_id: int | None = None,
              store: EventStore | None = None) -> dict[str, object]:
        with latency.time():
            try:
                with Image.open(io.BytesIO(payload)) as picture:
                    if picture.format not in {'JPEG', 'PNG'}:
                        raise ValueError('Only JPEG and PNG are supported')
                    if picture.width * picture.height > MAX_IMAGE_PIXELS:
                        raise ValueError('Image exceeds 12 megapixels')
                    image = cast(ImageArray, cv2.cvtColor(np.asarray(cast(Image.Image, ImageOps.exif_transpose(picture)).convert('RGB')), cv2.COLOR_RGB2BGR))
            except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as error:
                raise HTTPException(422, 'Invalid image or unsupported image dimensions') from error
            started = time.perf_counter()
            detections = detector.predict(image, confidence, iou)
            result: dict[str, object] = {
                'model_version': detector.metadata['version'],
                'width': image.shape[1], 'height': image.shape[0],
                'inference_ms': round((time.perf_counter() - started) * 1000, 3),
                'detections': [asdict(item) for item in detections],
            }
            if camera_id is not None and frame_id is not None and store is not None:
                if set(detector.labels) != {'helmet', 'no_helmet', 'person'}:
                    raise HTTPException(503, 'Helmet model required; generic COCO weights cannot detect missing helmets')
                with event_lock:
                    previous = deepcopy(rules.cameras)
                    created_snapshots: list[Path] = []
                    try:
                        changes, tracks = rules.update(camera_id, frame_id, time.time(), detections,
                                                       detector.metadata['version'])
                        for change in changes:
                            if change['kind'] == 'started':
                                snapshots.mkdir(parents=True, exist_ok=True)
                                name = change['event_id'] + '.jpg'
                                preview = image.copy()
                                x1, y1, x2, y2 = [round(value) for value in change['box']]
                                cv2.rectangle(preview, (x1, y1), (x2, y2), (0, 0, 255), 3)
                                created_snapshots.append(snapshots / name)
                                if not cv2.imwrite(str(snapshots / name), preview):
                                    raise OSError('Snapshot could not be saved')
                                change['snapshot'] = name
                        store.record(changes)
                    except OutOfOrderFrame as error:
                        rules.cameras = previous
                        raise HTTPException(409, str(error)) from error
                    except ValueError as error:
                        rules.cameras = previous
                        raise HTTPException(429, str(error)) from error
                    except Exception:
                        rules.cameras = previous
                        for snapshot_path in created_snapshots:
                            snapshot_path.unlink(missing_ok=True)
                        raise
                for change in changes:
                    if change['kind'] == 'started':
                        events_created.inc()
                result.update(camera_id=camera_id, frame_id=frame_id, event_changes=changes, tracks=tracks)
            return result

    async def process(request: Request, confidence: float, iou: float,
                      camera_id: str | None = None, frame_id: int | None = None) -> dict[str, object]:
        detector = request.app.state.detector
        if detector is None:
            requests.labels('unavailable').inc()
            raise HTTPException(503, request.app.state.load_error)
        if request.headers.get('content-type', '').split(';')[0] not in {'image/jpeg', 'image/png'}:
            requests.labels('invalid').inc()
            raise HTTPException(415, 'Send JPEG/PNG bytes with image/jpeg or image/png Content-Type')
        # Slots cover both upload and inference, bounding retained image memory too.
        if not slots.acquire(blocking=False):
            requests.labels('busy').inc()
            raise HTTPException(429, 'Inference capacity reached', headers={'Retry-After': '1'})
        try:
            body = bytearray()
            async for chunk in request.stream():
                if len(body) + len(chunk) > MAX_BODY_BYTES:
                    raise HTTPException(413, 'Image exceeds 8 MiB')
                body.extend(chunk)
            result = await run_in_threadpool(infer, bytes(body), detector, confidence, iou,
                                              camera_id, frame_id, request.app.state.store)
            requests.labels('ok').inc()
            return result
        except HTTPException:
            requests.labels('invalid').inc()
            raise
        except Exception:
            requests.labels('error').inc()
            logger.exception('Detection failed')
            raise HTTPException(500, 'Detection failed') from None
        finally:
            slots.release()

    @app.post('/detect')
    async def detect(request: Request, confidence: float = Query(0.25, ge=0.01, le=1),
                     iou: float = Query(0.45, ge=0.01, le=1)) -> dict[str, object]:
        return await process(request, confidence, iou)

    @app.post('/inspect')
    async def inspect(request: Request, camera_id: str = Query(..., pattern=r'^[a-zA-Z0-9_-]{1,64}$'),
                      frame_id: int = Query(..., ge=0), confidence: float = Query(0.4, ge=0.01, le=1),
                      iou: float = Query(0.45, ge=0.01, le=1)) -> dict[str, object]:
        return await process(request, confidence, iou, camera_id, frame_id)

    return app


app = create_app(max_inflight=int(os.getenv('MAX_INFLIGHT', '2')))
