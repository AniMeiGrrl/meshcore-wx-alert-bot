from dataclasses import replace
from pathlib import Path

from meshcore_wxbot.formatting import format_alert
from meshcore_wxbot.models import Alert
from meshcore_wxbot.state import State


def alert(**changes):
    base = Alert(
        identifier="id-1", event="Tornado Warning", message_type="Alert",
        status="Actual", sent="2026-07-24T18:00:00+00:00",
        expires="2026-07-24T19:00:00+00:00", ends=None,
        headline="Tornado Warning issued for Kent County",
        description="HAZARD...Radar indicated rotation. SOURCE...Radar.",
        instruction="", area_desc="Kent County",
        affected_zones=("https://api.weather.gov/zones/county/MIC081",),
        references=(), parameters={},
    )
    return replace(base, **changes)


def test_compact_message_is_byte_limited():
    msg = format_alert(alert(), {"MIC081": "Kent"}, "America/Detroit", 120)
    assert msg.startswith("🌪️ WX: Tornado Warning for Kent County until ")
    assert len(msg.encode()) <= 120


def test_full_severe_thunderstorm_wording():
    item = alert(
        event="Severe Thunderstorm Warning",
        parameters={"maxWindGust": ["70 mph"], "maxHailSize": ["1.00 in"]},
    )
    msg = format_alert(item, {"MIC081": "Kent"}, "America/Detroit", 120)
    assert msg.startswith(
        "⛈️ WX: Severe Thunderstorm Warning for Kent County until "
    )
    assert "70 mph wind" in msg
    assert len(msg.encode()) <= 120


def test_tornado_action_survives_byte_limit():
    item = alert(
        description=(
            "HAZARD...A long radar-indicated tornado description with "
            "many optional details. SOURCE...Radar."
        )
    )
    msg = format_alert(item, {"MIC081": "Kent"}, "America/Detroit", 90)
    assert msg.endswith("TAKE SHELTER NOW.")
    assert len(msg.encode()) <= 90


def test_considerable_severe_thunderstorm_gets_action():
    item = alert(
        event="Severe Thunderstorm Warning",
        parameters={"thunderstormDamageThreat": ["CONSIDERABLE"]},
    )
    msg = format_alert(item, {"MIC081": "Kent"}, "America/Detroit", 120)
    assert msg.endswith("TAKE SHELTER NOW.")


def test_normal_severe_thunderstorm_has_no_shelter_action():
    item = alert(event="Severe Thunderstorm Warning")
    msg = format_alert(item, {"MIC081": "Kent"}, "America/Detroit", 120)
    assert "TAKE SHELTER NOW." not in msg


def test_flood_warning_uses_wave_emoji():
    item = alert(event="Flash Flood Warning")
    msg = format_alert(item, {"MIC081": "Kent"}, "America/Detroit", 133)
    assert msg.startswith("🌊 WX: Flash Flood Warning")
    assert len(msg.encode()) <= 133


def test_actions():
    assert alert().action == "NEW"
    assert alert(message_type="Update", references=("old",)).action == "UPDATE"
    assert alert(message_type="Cancel").action == "CANCEL"


def test_state_deduplicates(tmp_path: Path):
    state = State(tmp_path / "state.db")
    item = alert()
    fp = state.fingerprint(item, "message")
    assert not state.delivered(fp)
    state.record(fp, item, "message")
    assert state.delivered(fp)
    state.close()
