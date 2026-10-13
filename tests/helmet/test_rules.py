import pytest

from src.cv.detector import Detection
from src.helmet.events import HelmetRules, OutOfOrderFrame, overlap


def head(label='no_helmet', box=(10., 10., 30., 30.), score=.9):
    return Detection(1 if label == 'no_helmet' else 0, label, score, box)


def test_violation_needs_duration_and_consecutive_observations():
    rules = HelmetRules()
    assert rules.update('camera', 0, 0, [head()], 'v1')[0] == []
    assert rules.update('camera', 1, .5, [head()], 'v1')[0] == []
    changes, tracks = rules.update('camera', 2, 1, [head()], 'v1')
    assert len(changes) == 1 and changes[0]['kind'] == 'started'
    assert tracks[0]['state'] == 'violation'
    assert rules.update('camera', 3, 1.5, [head()], 'v1')[0] == []


def test_absence_of_detection_does_not_prove_violation():
    rules = HelmetRules()
    for frame in range(4):
        assert rules.update('camera', frame, frame * .5, [], 'v1') == ([], [])


def test_gap_resets_unconfirmed_candidate():
    rules = HelmetRules()
    rules.update('camera', 0, 0, [head()], 'v1')
    rules.update('camera', 1, .5, [], 'v1')
    assert rules.update('camera', 2, 1, [head()], 'v1')[0] == []
    assert rules.update('camera', 3, 1.5, [head()], 'v1')[0] == []
    assert len(rules.update('camera', 4, 2, [head()], 'v1')[0]) == 1


def test_short_gap_keeps_event_but_disappearance_closes_as_lost_track():
    rules = HelmetRules(min_frames=1, min_seconds=0)
    rules.update('camera', 0, 0, [head()], 'v1')
    changes, tracks = rules.update('camera', 1, 1, [], 'v1')
    assert changes == [] and tracks[0]['label'] == 'unknown'
    changes, tracks = rules.update('camera', 2, 2, [], 'v1')
    assert changes[0]['reason'] == 'lost_track' and tracks == []


def test_helmet_requires_two_confirmations_to_close():
    rules = HelmetRules(min_frames=1, min_seconds=0)
    rules.update('camera', 0, 0, [head()], 'v1')
    assert rules.update('camera', 1, .5, [head('helmet')], 'v1')[0] == []
    assert rules.update('camera', 2, 1, [head('helmet')], 'v1')[0][0]['reason'] == 'helmet_seen'


def test_conflicting_head_classes_choose_highest_confidence():
    rules = HelmetRules(min_frames=1, min_seconds=0)
    assert rules.update('camera', 0, 0, [head(score=.6), head('helmet', score=.9)], 'v1')[0] == []


def test_camera_isolation_and_model_change():
    rules = HelmetRules(min_frames=1, min_seconds=0)
    rules.update('a', 0, 0, [head()], 'v1')
    assert rules.update('b', 0, 0, [head('helmet')], 'v1')[0] == []
    changes, _ = rules.update('a', 1, .5, [head('helmet')], 'v2')
    assert changes[0]['reason'] == 'model_changed'
    assert rules.finish('a', 1) == []
    changes = rules.finish('b', 1)
    assert changes == []


def test_stale_frame_does_not_advance_state_and_stream_end_closes_event():
    rules = HelmetRules(min_frames=1, min_seconds=0, max_cameras=1)
    rules.update('a', 1, 0, [head()], 'v1')
    with pytest.raises(OutOfOrderFrame):
        rules.update('a', 1, .5, [head()], 'v1')
    with pytest.raises(ValueError, match='capacity'):
        rules.update('b', 0, 1, [], 'v1')
    assert rules.finish('a', 1)[0]['reason'] == 'stream_ended'
    assert rules.finish('a', 2) == []
    rules.update('b', 0, 2, [], 'v1')


def test_invalid_configuration_and_disjoint_boxes():
    with pytest.raises(ValueError):
        HelmetRules(min_frames=0)
    assert overlap((0, 0, 10, 10), (20, 20, 30, 30)) == 0
