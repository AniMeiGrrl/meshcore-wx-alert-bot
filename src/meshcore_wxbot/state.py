from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

from .models import Alert


class State:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute(
            """CREATE TABLE IF NOT EXISTS deliveries (
                fingerprint TEXT PRIMARY KEY,
                alert_id TEXT NOT NULL,
                series_key TEXT NOT NULL,
                action TEXT NOT NULL,
                message TEXT NOT NULL,
                delivered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        self.db.commit()

    @staticmethod
    def fingerprint(alert: Alert, message: str) -> str:
        basis = "\x1f".join((alert.identifier, alert.message_type, alert.sent, message))
        return hashlib.sha256(basis.encode()).hexdigest()

    def delivered(self, fingerprint: str) -> bool:
        row = self.db.execute(
            "SELECT 1 FROM deliveries WHERE fingerprint=?", (fingerprint,)
        ).fetchone()
        return row is not None

    def record(self, fingerprint: str, alert: Alert, message: str) -> None:
        self.db.execute(
            """INSERT OR IGNORE INTO deliveries
               (fingerprint, alert_id, series_key, action, message)
               VALUES (?, ?, ?, ?, ?)""",
            (fingerprint, alert.identifier, alert.series_key, alert.action, message),
        )
        self.db.commit()

    def close(self) -> None:
        self.db.close()
