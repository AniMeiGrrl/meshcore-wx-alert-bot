from __future__ import annotations

import re
from zoneinfo import ZoneInfo

from .models import Alert

EVENT_EMOJIS = {
    "Tornado Warning": "🌪️",
    "Tornado Watch": "🌪️",
    "Severe Thunderstorm Warning": "⛈️",
    "Severe Thunderstorm Watch": "⛈️",
    "Flash Flood Warning": "🌊",
    "Flood Warning": "🌊",
    "Flood Watch": "🌊",
    "Special Weather Statement": "⚠️",
}

def _parameter(alert: Alert, *names: str) -> str:
    for name in names:
        vals = alert.parameters.get(name)
        if vals:
            return vals[0]
    return ""


def _counties(alert: Alert, configured: dict[str, str]) -> str:
    names = []
    for zone in alert.affected_zones:
        code = zone.rstrip("/").rsplit("/", 1)[-1]
        if code in configured:
            names.append(configured[code])
    if not names:
        low = alert.area_desc.lower()
        names = [name for name in configured.values() if name.lower() in low]
    return "/".join(dict.fromkeys(names)) or alert.area_desc.split(";")[0].strip()


def _detail(alert: Alert) -> str:
    wind = _parameter(alert, "maxWindGust")
    hail = _parameter(alert, "maxHailSize")
    bits = []
    if wind:
        bits.append(f"{wind} wind")
    if hail:
        bits.append(f"{hail} hail")
    text = re.sub(r"\s+", " ", alert.description)
    motion = re.search(
        r"\bmoving\s+(?:north|south|east|west|northeast|northwest|"
        r"southeast|southwest|N|S|E|W|NE|NW|SE|SW)"
        r"(?:ward)?\s+(?:at\s+)?\d+\s*mph\b",
        text,
        re.IGNORECASE,
    )
    if motion:
        bits.append(motion.group(0))
    if bits:
        return ", ".join(bits).rstrip(".") + "."
    patterns = [
        r"(?:HAZARD\.\.\.|HAZARD\.\s*)(.*?)(?:SOURCE\.\.\.|SOURCE\.)",
        r"(?:At [^.]{0,80},\s*)([^.]{10,100}\.)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip(" .")
    return ""


def _protective_action(alert: Alert) -> str:
    if alert.action == "CANCEL":
        return ""
    if alert.event == "Tornado Warning":
        return "TAKE SHELTER NOW."
    if alert.event != "Severe Thunderstorm Warning":
        return ""
    threat = _parameter(
        alert,
        "thunderstormDamageThreat",
        "damageThreat",
    ).lower()
    fallback = f"{alert.headline} {alert.description}".lower()
    if threat in {"considerable", "destructive"}:
        return "TAKE SHELTER NOW."
    if "considerable damage threat" in fallback or "destructive" in fallback:
        return "TAKE SHELTER NOW."
    return ""


def _fit(text: str, max_bytes: int) -> str:
    text = re.sub(r"[ \t]+", " ", text).strip()
    if len(text.encode("utf-8")) <= max_bytes:
        return text
    raw = text.encode("utf-8")[: max_bytes - 3]
    while True:
        try:
            short = raw.decode("utf-8")
            break
        except UnicodeDecodeError:
            raw = raw[:-1]
    if " " in short:
        short = short.rsplit(" ", 1)[0]
    return short.rstrip(" ,.;:-") + "..."


def _assemble(first: str, detail: str, action: str, max_bytes: int) -> str:
    required = "\n".join(part for part in (first, action) if part)
    if not detail:
        return _fit(required, max_bytes)
    full = "\n".join(part for part in (first, detail, action) if part)
    if len(full.encode("utf-8")) <= max_bytes:
        return full
    separator_bytes = 1
    available = (
        max_bytes
        - len(required.encode("utf-8"))
        - separator_bytes
    )
    if available < 8:
        return _fit(required, max_bytes)
    fitted_detail = _fit(detail, available)
    return "\n".join(part for part in (first, fitted_detail, action) if part)


def format_alert(
    alert: Alert,
    counties: dict[str, str],
    timezone: str,
    max_bytes: int,
) -> str:
    prefix = {"NEW": "WX", "UPDATE": "WX Update", "CANCEL": "WX Cancellation"}[
        alert.action
    ]
    emoji = EVENT_EMOJIS.get(alert.event, "⚠️")
    county = _counties(alert, counties)
    if county.lower().endswith(" county"):
        place = county
    else:
        place = f"{county} County"
    until = ""
    if alert.event_time and alert.action != "CANCEL":
        local = alert.event_time.astimezone(ZoneInfo(timezone))
        until = f" until {local.strftime('%-I:%M%p').lower()}"
    first = f"{emoji} {prefix}: {alert.event} for {place}{until}."
    detail = (
        "Cancelled by the National Weather Service."
        if alert.action == "CANCEL"
        else _detail(alert)
    )
    action = _protective_action(alert)
    return _assemble(first, detail, action, max_bytes)
