"""SQLite-backed history store.

Zero configuration: a single file (``~/.local/share/nettop/nettop.db`` by
default) holds every scan so ``device --history`` and the daemon can look back
in time. Each scan is stored as a row plus its full JSON payload, which keeps
the schema simple while still allowing structured queries on the summary.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from ..models import ScanResult
from ..utils.logging import get_logger

log = get_logger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS scans (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    network         TEXT NOT NULL,
    scan_timestamp  TEXT NOT NULL,
    device_count    INTEGER NOT NULL,
    online_count    INTEGER NOT NULL,
    payload         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS devices (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id    INTEGER NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    ip         TEXT NOT NULL,
    mac        TEXT,
    hostname   TEXT,
    os         TEXT,
    status     TEXT,
    last_seen  TEXT
);

CREATE INDEX IF NOT EXISTS idx_devices_ip ON devices(ip);
CREATE INDEX IF NOT EXISTS idx_scans_network ON scans(network);
"""


def default_db_path() -> Path:
    """Return the platform-appropriate default database path."""
    home = Path.home()
    base = home / ".local" / "share" / "nettop"
    return base / "nettop.db"


class Database:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else default_db_path()
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    @contextmanager
    def _cursor(self) -> Iterator[sqlite3.Cursor]:
        cur = self._conn.cursor()
        try:
            yield cur
            self._conn.commit()
        finally:
            cur.close()

    def save_scan(self, result: ScanResult) -> int:
        """Persist a scan and return its row id."""
        payload = json.dumps(result.to_dict(), ensure_ascii=False)
        with self._cursor() as cur:
            cur.execute(
                "INSERT INTO scans (network, scan_timestamp, device_count, "
                "online_count, payload) VALUES (?, ?, ?, ?, ?)",
                (
                    result.network,
                    result.scan_timestamp,
                    len(result.devices),
                    result.online_count,
                    payload,
                ),
            )
            scan_id = cur.lastrowid
            cur.executemany(
                "INSERT INTO devices (scan_id, ip, mac, hostname, os, status, "
                "last_seen) VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        scan_id,
                        d.ip,
                        d.mac,
                        d.hostname,
                        d.os,
                        d.status.value,
                        d.last_seen,
                    )
                    for d in result.devices
                ],
            )
        log.debug("Saved scan %s (%d devices)", scan_id, len(result.devices))
        return int(scan_id)

    def latest_scan(self, network: str | None = None) -> ScanResult | None:
        query = "SELECT payload FROM scans"
        params: tuple[object, ...] = ()
        if network:
            query += " WHERE network = ?"
            params = (network,)
        query += " ORDER BY id DESC LIMIT 1"
        row = self._conn.execute(query, params).fetchone()
        if row is None:
            return None
        return ScanResult.from_dict(json.loads(row["payload"]))

    def device_history(self, ip: str, limit: int = 20) -> list[dict[str, object]]:
        """Return recent sightings of a single device across scans."""
        rows = self._conn.execute(
            "SELECT s.scan_timestamp, d.status, d.hostname, d.os "
            "FROM devices d JOIN scans s ON s.id = d.scan_id "
            "WHERE d.ip = ? ORDER BY s.id DESC LIMIT ?",
            (ip, limit),
        ).fetchall()
        return [dict(row) for row in rows]

    def list_scans(self, limit: int = 20) -> list[dict[str, object]]:
        rows = self._conn.execute(
            "SELECT id, network, scan_timestamp, device_count, online_count "
            "FROM scans ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
