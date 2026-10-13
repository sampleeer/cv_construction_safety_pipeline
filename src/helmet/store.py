"""SQLite event journal. Connections are local to each operation/thread."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Iterator
from contextlib import contextmanager


class EventStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.execute('PRAGMA journal_mode=WAL')
            connection.execute('''CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY, track_id TEXT NOT NULL, camera_id TEXT NOT NULL,
                started_at REAL NOT NULL, first_seen_at REAL NOT NULL, ended_at REAL,
                end_reason TEXT, model_version TEXT NOT NULL, confidence REAL NOT NULL,
                box TEXT NOT NULL, snapshot TEXT)''')
            connection.execute('CREATE INDEX IF NOT EXISTS events_camera_time ON events(camera_id, started_at DESC)')

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def record(self, changes: list[dict[str, Any]]) -> None:
        with self.connect() as connection:
            for change in changes:
                if change['kind'] == 'started':
                    connection.execute('''INSERT INTO events
                        (event_id,track_id,camera_id,started_at,first_seen_at,model_version,confidence,box,snapshot)
                        VALUES (?,?,?,?,?,?,?,?,?)''',
                        (change['event_id'], change['track_id'], change['camera_id'], change['started_at'],
                         change['first_seen_at'], change['model_version'], change['confidence'],
                         json.dumps(change['box']), change.get('snapshot')))
                else:
                    connection.execute('UPDATE events SET ended_at=?, end_reason=? WHERE event_id=?',
                                       (change['ended_at'], change['reason'], change['event_id']))

    def list(self, camera_id: str | None = None, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        query = 'SELECT * FROM events'
        values: list[Any] = []
        if camera_id:
            query += ' WHERE camera_id=?'
            values.append(camera_id)
        query += ' ORDER BY started_at DESC, event_id DESC LIMIT ? OFFSET ?'
        values.extend([limit, offset])
        with self.connect() as connection:
            rows = connection.execute(query, values).fetchall()
        result = []
        for row in rows:
            event = dict(row)
            event['box'] = json.loads(event['box'])
            event['status'] = 'closed' if event['ended_at'] is not None else 'open'
            event['snapshot_url'] = f"/events/{event['event_id']}/snapshot" if event['snapshot'] else None
            event.pop('snapshot')
            result.append(event)
        return result

    def snapshot(self, event_id: str) -> str | None:
        with self.connect() as connection:
            row = connection.execute('SELECT snapshot FROM events WHERE event_id=?', (event_id,)).fetchone()
        return row['snapshot'] if row else None

    def close_interrupted(self, now: float) -> None:
        # Persisted open events cannot retain track identity across process restarts.
        with self.connect() as connection:
            connection.execute("UPDATE events SET ended_at=?, end_reason='server_restart' WHERE ended_at IS NULL", (now,))
