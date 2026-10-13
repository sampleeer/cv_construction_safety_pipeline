from src.helmet.events import HelmetRules
from src.helmet.store import EventStore
from tests.helmet.test_rules import head


def test_event_persistence_filtering_close_and_restart(tmp_path):
    store = EventStore(tmp_path / 'events.sqlite')
    rules = HelmetRules(min_frames=1, min_seconds=0)
    first, _ = rules.update('a', 0, 1, [head()], 'version')
    first[0]['snapshot'] = 'sample.jpg'
    store.record(first)
    second, _ = rules.update('b', 0, 2, [head()], 'version')
    store.record(second)
    assert len(store.list()) == 2
    assert store.list('a')[0]['status'] == 'open'
    assert store.snapshot(first[0]['event_id']) == 'sample.jpg'
    assert store.snapshot('missing') is None
    store.record(rules.finish('a', 3))
    assert store.list('a')[0]['end_reason'] == 'stream_ended'
    store.close_interrupted(4)
    assert store.list('b')[0]['end_reason'] == 'server_restart'
    assert store.list(limit=1, offset=1)[0]['camera_id'] == 'a'
    assert store.list("a' OR 1=1 --") == []
