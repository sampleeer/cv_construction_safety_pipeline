"""Temporal helmet rules with lightweight IoU tracking of head regions."""
from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from typing import Any

from src.cv.detector import Detection

Box = tuple[float, float, float, float]


def overlap(first: Box, second: Box) -> float:
    area = max(0.0, min(first[2], second[2]) - max(first[0], second[0])) * max(
        0.0, min(first[3], second[3]) - max(first[1], second[1]))
    union = (first[2] - first[0]) * (first[3] - first[1]) + (second[2] - second[0]) * (second[3] - second[1]) - area
    return area / union if union > 0 else 0.0


@dataclass
class Track:
    track_id: str
    box: Box
    last_seen: float
    label: str
    confidence: float
    no_helmet_since: float | None = None
    no_helmet_frames: int = 0
    helmet_frames: int = 0
    event_id: str | None = None


@dataclass
class Camera:
    last_frame: int = -1
    last_time: float = -1.0
    model_version: str = ''
    tracks: dict[str, Track] = field(default_factory=dict)


class OutOfOrderFrame(ValueError):
    pass


class HelmetRules:
    """One process owns the camera state; callers serialize updates through this lock."""
    def __init__(self, min_frames: int = 3, min_seconds: float = 1.0,
                 max_gap: float = 1.5, max_cameras: int = 32) -> None:
        if min_frames < 1 or min_seconds < 0 or max_gap <= 0 or max_cameras < 1:
            raise ValueError('Invalid helmet rule configuration')
        self.min_frames = min_frames
        self.min_seconds = min_seconds
        self.max_gap = max_gap
        self.max_cameras = max_cameras
        self.cameras: dict[str, Camera] = {}
        self.lock = threading.Lock()

    def update(self, camera_id: str, frame_id: int, now: float, detections: list[Detection],
               model_version: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        with self.lock:
            if camera_id not in self.cameras:
                if len(self.cameras) >= self.max_cameras:
                    raise ValueError('Camera capacity reached; restart or reuse a configured camera ID')
                self.cameras[camera_id] = Camera(model_version=model_version)
            camera = self.cameras[camera_id]
            if frame_id <= camera.last_frame or now < camera.last_time:
                raise OutOfOrderFrame('frame_id must increase for each camera; restart uses a new camera session ID')
            changes: list[dict[str, Any]] = []

            def close(track: Track, reason: str) -> None:
                if track.event_id:
                    changes.append({'kind': 'ended', 'event_id': track.event_id, 'track_id': track.track_id,
                                    'camera_id': camera_id, 'ended_at': now, 'reason': reason})
                    track.event_id = None

            # A model version change invalidates temporal evidence from the prior model.
            if camera.model_version != model_version:
                for track in camera.tracks.values():
                    close(track, 'model_changed')
                camera.tracks.clear()
                camera.model_version = model_version
            for track_id, track in list(camera.tracks.items()):
                if now - track.last_seen > self.max_gap:
                    close(track, 'lost_track')
                    del camera.tracks[track_id]
            # Resolve mutually exclusive class detections on the same head by confidence.
            heads: list[Detection] = []
            for detection in sorted(detections, key=lambda item: item.confidence, reverse=True):
                if detection.label in {'helmet', 'no_helmet'} and not any(overlap(detection.box, head.box) > .5 for head in heads):
                    heads.append(detection)
            unmatched = set(camera.tracks)
            for head in heads:
                matching = sorted(((overlap(head.box, camera.tracks[key].box), key) for key in unmatched), reverse=True)
                if matching and matching[0][0] >= .25:
                    track = camera.tracks[matching[0][1]]
                    unmatched.remove(track.track_id)
                else:
                    track_id = str(uuid.uuid4())
                    track = Track(track_id, head.box, now, head.label, head.confidence)
                    camera.tracks[track_id] = track
                # Consecutive means adjacent accepted observations, not repeated stale frames.
                if track.last_seen < camera.last_time:
                    track.no_helmet_since, track.no_helmet_frames, track.helmet_frames = None, 0, 0
                track.box, track.last_seen = head.box, now
                track.label, track.confidence = head.label, head.confidence
                if head.label == 'no_helmet':
                    track.helmet_frames = 0
                    if track.no_helmet_since is None:
                        track.no_helmet_since = now
                    track.no_helmet_frames += 1
                    if (not track.event_id and track.no_helmet_frames >= self.min_frames
                            and now - track.no_helmet_since >= self.min_seconds):
                        track.event_id = str(uuid.uuid4())
                        changes.append({'kind': 'started', 'event_id': track.event_id, 'track_id': track.track_id,
                                        'camera_id': camera_id, 'started_at': now, 'first_seen_at': track.no_helmet_since,
                                        'model_version': model_version, 'confidence': head.confidence, 'box': head.box})
                else:
                    track.no_helmet_frames, track.no_helmet_since = 0, None
                    track.helmet_frames += 1
                    if track.helmet_frames >= 2:
                        close(track, 'helmet_seen')
            # A missing head breaks candidate confirmation, but active events survive short gaps.
            for track_id in unmatched:
                track = camera.tracks[track_id]
                track.no_helmet_since, track.no_helmet_frames, track.helmet_frames = None, 0, 0
            camera.last_frame, camera.last_time = frame_id, now
            tracks = [{'track_id': track.track_id, 'box': track.box, 'label':
                       track.label if track.last_seen == now else 'unknown',
                       'confidence': track.confidence, 'event_id': track.event_id,
                       'state': 'violation' if track.event_id else ('pending' if track.no_helmet_frames else 'unconfirmed')}
                      for track in camera.tracks.values()]
            return changes, tracks

    def finish(self, camera_id: str, now: float) -> list[dict[str, Any]]:
        with self.lock:
            camera = self.cameras.pop(camera_id, None)
            if camera is None:
                return []
            return [{'kind': 'ended', 'event_id': track.event_id, 'track_id': track.track_id,
                     'camera_id': camera_id, 'ended_at': now, 'reason': 'stream_ended'}
                    for track in camera.tracks.values() if track.event_id]
