from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Alert:
    identifier: str
    event: str
    message_type: str
    status: str
    sent: str
    expires: str | None
    ends: str | None
    headline: str
    description: str
    instruction: str
    area_desc: str
    affected_zones: tuple[str, ...]
    references: tuple[str, ...]
    parameters: dict[str, list[str]]

    @classmethod
    def from_feature(cls, feature: dict[str, Any]) -> "Alert":
        p = feature.get("properties") or {}
        refs = p.get("references") or []
        if isinstance(refs, str):
            refs = tuple(part.split(",")[1] for part in refs.split() if "," in part)
        else:
            refs = tuple(str(x.get("@id") or x.get("identifier") or "") for x in refs)
        return cls(
            identifier=str(feature.get("id") or p.get("id") or ""),
            event=str(p.get("event") or ""),
            message_type=str(p.get("messageType") or "Alert"),
            status=str(p.get("status") or "Actual"),
            sent=str(p.get("sent") or ""),
            expires=p.get("expires"),
            ends=p.get("ends"),
            headline=str(p.get("headline") or ""),
            description=str(p.get("description") or ""),
            instruction=str(p.get("instruction") or ""),
            area_desc=str(p.get("areaDesc") or ""),
            affected_zones=tuple(p.get("affectedZones") or ()),
            references=tuple(x for x in refs if x),
            parameters={str(k): [str(v) for v in vals] for k, vals in (p.get("parameters") or {}).items()},
        )

    @property
    def action(self) -> str:
        mt = self.message_type.lower()
        text = f"{self.headline} {self.description}".lower()
        if mt == "cancel" or "cancelled" in text or "canceled" in text:
            return "CANCEL"
        if mt in {"update", "correction"} or self.references:
            return "UPDATE"
        return "NEW"

    @property
    def series_key(self) -> str:
        return self.references[0] if self.references else self.identifier

    @property
    def event_time(self) -> datetime | None:
        raw = self.ends or self.expires
        if not raw:
            return None
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
