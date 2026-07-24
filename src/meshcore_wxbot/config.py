from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import yaml


@dataclass(frozen=True)
class Config:
    counties: dict[str, str]
    events: frozenset[str]
    user_agent: str
    poll_seconds: int
    history_minutes: int
    request_timeout_seconds: int
    serial_port: str
    baudrate: int
    channel_index: int
    max_message_bytes: int
    min_send_interval_seconds: float
    reconnect_initial_seconds: float
    reconnect_max_seconds: float
    database: Path
    timezone: str
    dry_run: bool


def _need(data: dict[str, Any], section: str, key: str) -> Any:
    try:
        return data[section][key]
    except KeyError as exc:
        raise ValueError(f"missing configuration: {section}.{key}") from exc


def load_config(path: str | Path) -> Config:
    path = Path(path)
    data = yaml.safe_load(path.read_text()) or {}
    nws = data.get("nws", {})
    mesh = data.get("meshcore", {})
    app = data.get("app", {})
    raw_counties = _need(data, "nws", "counties")
    counties = {
        str(item["code"]).upper(): str(item["name"])
        for item in raw_counties
    }
    if not counties or any(
        re.fullmatch(r"[A-Z]{2}C\d{3}", code) is None for code in counties
    ):
        raise ValueError(
            "nws.counties must contain county UGC codes such as MIC081"
        )
    events = frozenset(str(x) for x in _need(data, "nws", "events"))
    user_agent = str(_need(data, "nws", "user_agent"))
    if "@" not in user_agent and "http" not in user_agent:
        raise ValueError("nws.user_agent must include contact information")
    poll = int(nws.get("poll_seconds", 60))
    if poll < 30:
        raise ValueError("nws.poll_seconds must be at least 30")
    max_bytes = int(mesh.get("max_message_bytes", 120))
    if not 40 <= max_bytes <= 200:
        raise ValueError("meshcore.max_message_bytes must be 40..200")
    db = Path(app.get("database", "/var/lib/meshcore-wxbot/state.sqlite3"))
    if not db.is_absolute():
        db = (path.parent / db).resolve()
    return Config(
        counties=counties,
        events=events,
        user_agent=user_agent,
        poll_seconds=poll,
        history_minutes=int(nws.get("history_minutes", 15)),
        request_timeout_seconds=int(nws.get("request_timeout_seconds", 20)),
        serial_port=str(mesh.get("serial_port", "/dev/ttyACM0")),
        baudrate=int(mesh.get("baudrate", 115200)),
        channel_index=int(mesh.get("channel_index", 0)),
        max_message_bytes=max_bytes,
        min_send_interval_seconds=float(mesh.get("min_send_interval_seconds", 5)),
        reconnect_initial_seconds=float(mesh.get("reconnect_initial_seconds", 2)),
        reconnect_max_seconds=float(mesh.get("reconnect_max_seconds", 60)),
        database=db,
        timezone=str(app.get("timezone", "America/Detroit")),
        dry_run=bool(app.get("dry_run", False)),
    )
