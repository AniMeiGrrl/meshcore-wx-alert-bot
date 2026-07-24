from pathlib import Path

from meshcore_wxbot.config import load_config


def test_non_michigan_county_is_valid(tmp_path: Path):
    config = tmp_path / "config.yaml"
    config.write_text(
        """
nws:
  user_agent: "meshcore-wxbot/1.0 (operator@example.com)"
  poll_seconds: 60
  counties:
    - {code: TXC201, name: Harris}
  events:
    - Tornado Warning
meshcore:
  serial_port: /dev/ttyACM0
  channel_index: 0
app:
  database: state.sqlite3
  timezone: America/Chicago
  dry_run: true
"""
    )
    loaded = load_config(config)
    assert loaded.counties == {"TXC201": "Harris"}
    assert loaded.database == (tmp_path / "state.sqlite3").resolve()
