"""Prevent application tests from writing to a developer's actual event journal."""
import pytest


@pytest.fixture(autouse=True)
def isolate_event_storage(tmp_path, monkeypatch):
    monkeypatch.setenv('HELMET_DB', str(tmp_path / 'events.sqlite'))
    monkeypatch.setenv('HELMET_SNAPSHOTS', str(tmp_path / 'snapshots'))
