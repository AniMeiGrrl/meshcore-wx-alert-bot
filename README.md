# MeshCore WX Bot

MeshCore WX Bot polls the official United States National Weather Service API
and transmits selected watches, warnings, updates, corrections, and
cancellations to a MeshCore channel through a USB Companion radio.

It is designed to run continuously on Debian or Ubuntu, including a Proxmox VM.

```text
NWS api.weather.gov
        │
        ▼
 meshcore-wxbot ── SQLite deduplication
        │ USB serial
        ▼
 MeshCore Companion ── LoRa mesh channel
```

Example:

```text
🌪️ WX: Tornado Warning for Kent County until 4:59pm.
Radar indicated rotation.
TAKE SHELTER NOW.
```

> [!WARNING]
> This is an unofficial redistribution tool. It is not a replacement for NOAA
> Weather Radio, Wireless Emergency Alerts, local sirens, or instructions from
> public-safety officials. Do not use NWS CAP data to activate EAS equipment.

## Features

- configurable U.S. counties and NWS event types;
- compact Unicode messages with an enforced UTF-8 byte ceiling;
- priority protective wording for Tornado Warnings and NWS-tagged
  considerable/destructive Severe Thunderstorm Warnings;
- CAP alert/update/correction/cancellation handling;
- SQLite delivery deduplication;
- active-alert polling plus a recent-history window for cancellations;
- multi-county alert merging by NWS identifier;
- automatic serial reconnect with exponential backoff;
- configurable radio transmission spacing;
- safe dry-run mode and synthetic test alerts;
- stdout/stderr logging suited to journald;
- hardened systemd unit;
- built-in NWS county-code lookup.

## Requirements

- Debian 12/13 or Ubuntu 22/24/26;
- Python 3.11 or newer;
- Internet access to `api.weather.gov`;
- a supported radio running MeshCore **USB Companion** firmware;
- a configured MeshCore radio preset and channel.

This project uses the [`meshcore`](https://github.com/meshcore-dev/meshcore_py)
Python package and its current `MeshCore.create_serial(...)` and
`commands.send_chan_msg(...)` interfaces.

## Quick start

Clone or download the repository, then:

```sh
sudo apt update
sudo apt install -y python3 python3-venv

sudo useradd --system \
  --home /var/lib/meshcore-wxbot \
  --shell /usr/sbin/nologin \
  meshcore-wxbot

sudo install -d \
  -o meshcore-wxbot -g meshcore-wxbot \
  /opt/meshcore-wxbot/app \
  /etc/meshcore-wxbot \
  /var/lib/meshcore-wxbot

sudo cp -a . /opt/meshcore-wxbot/app/
sudo python3 -m venv /opt/meshcore-wxbot/venv
sudo /opt/meshcore-wxbot/venv/bin/pip install /opt/meshcore-wxbot/app
sudo cp config.example.yaml /etc/meshcore-wxbot/config.yaml
sudo cp systemd/meshcore-wxbot.service /etc/systemd/system/
sudo usermod -aG dialout meshcore-wxbot
```

Find the radio:

```sh
ls -l /dev/serial/by-id/
```

Edit `/etc/meshcore-wxbot/config.yaml` and set:

- a real contact address in `nws.user_agent`;
- one or more county codes;
- the stable `/dev/serial/by-id/...` radio path;
- the channel index shown by `meshcore-cli get_channels`;
- the local IANA timezone;
- `dry_run: true` during setup.

See [Configuration](docs/CONFIGURATION.md) for every setting.

## Find county codes

After installation:

```sh
/opt/meshcore-wxbot/venv/bin/meshcore-wxbot \
  list-counties MI \
  --user-agent "meshcore-wxbot/1.0 (operator@example.com)"
```

Example output:

```text
MIC081   Kent
MIC139   Ottawa
```

Copy the desired entries into the YAML configuration. See
[Finding NWS county codes](docs/NWS-COUNTIES.md) for alternative official
lookup methods and an explanation of county UGC codes.

## Configure a MeshCore channel

With `meshcore-cli` connected to the USB Companion:

```text
get_channels
add_channel #localweather
get_channels
```

If the new channel is shown as index 1, configure:

```yaml
meshcore:
  channel_index: 1
```

A hashtag channel derives its shared key deterministically from its name; it is
not private. Private channels require a separately generated 16-byte key. See
[MeshCore channels](docs/MESHCORE-CHANNELS.md).

## Test safely

With `dry_run: true`:

```sh
sudo -u meshcore-wxbot \
  /opt/meshcore-wxbot/venv/bin/meshcore-wxbot \
  -c /etc/meshcore-wxbot/config.yaml once

sudo -u meshcore-wxbot \
  /opt/meshcore-wxbot/venv/bin/meshcore-wxbot \
  -c /etc/meshcore-wxbot/config.yaml \
  test-alert --county Example
```

The journal should show `DRY RUN`, and nothing will be transmitted.

When ready, set `dry_run: false`, make sure another device is listening on the
configured channel, and repeat `test-alert`.

## Start the service

```sh
sudo systemctl daemon-reload
sudo systemctl enable --now meshcore-wxbot
sudo systemctl status meshcore-wxbot
sudo journalctl -u meshcore-wxbot -f
```

## Documentation

- [Configuration reference](docs/CONFIGURATION.md)
- [Finding NWS county codes](docs/NWS-COUNTIES.md)
- [MeshCore radio and channels](docs/MESHCORE-CHANNELS.md)
- [Proxmox USB passthrough](docs/PROXMOX.md)
- [Operations and upgrades](docs/OPERATIONS.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## How deduplication works

The bot fingerprints the NWS identifier, CAP message type, sent timestamp, and
rendered message. It records the fingerprint only after a successful radio send
(or intentional dry run). Repeated county results and repeated polling cycles
therefore do not retransmit the same product, while updates, corrections, and
cancellations remain distinct.

The NWS active-alert filter excludes cancellation products. The bot also queries
a short recent-history window and merges both result sets before processing.

## Message size

The default is a conservative 133 UTF-8 bytes. Official MeshCore client
documentation describes a 133-character text limit, while underlying frames are
byte-oriented and emoji use multiple UTF-8 bytes. Enforcing bytes avoids
splitting Unicode or relying on client-specific character counting.

Optional detail is truncated before required protective wording, so
`TAKE SHELTER NOW.` remains intact.

## Development

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
pytest
```

## License

GNU Public
