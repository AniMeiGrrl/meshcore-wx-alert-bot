# Configuration reference

The default service reads `/etc/meshcore-wxbot/config.yaml`. Start by copying
`config.example.yaml`; do not commit a live configuration containing a private
channel key, personal email address, precise private location, or device path.

## Complete example

```yaml
nws:
  user_agent: "meshcore-wxbot/1.0 (operator@example.com)"
  poll_seconds: 60
  history_minutes: 15
  request_timeout_seconds: 20
  counties:
    - {code: MIC081, name: Kent}
  events:
    - Tornado Warning
    - Severe Thunderstorm Warning
    - Flash Flood Warning
    - Tornado Watch
    - Severe Thunderstorm Watch

meshcore:
  serial_port: /dev/serial/by-id/REPLACE_WITH_YOUR_RADIO
  baudrate: 115200
  channel_index: 1
  max_message_bytes: 133
  min_send_interval_seconds: 5
  reconnect_initial_seconds: 2
  reconnect_max_seconds: 60

app:
  database: /var/lib/meshcore-wxbot/state.sqlite3
  timezone: America/New_York
  dry_run: true
```

## NWS settings

### `user_agent`

Required by NWS. Use an application name plus real contact information so NWS
can reach the operator if the client causes a problem.

### `poll_seconds`

Seconds between cycles. The bot rejects values below 30 because NWS recommends
requesting alerts no more frequently than every 30 seconds. Sixty seconds is a
reasonable default.

### `history_minutes`

Length of the additional recent-products window. This is needed because
`/alerts/active` excludes cancellation products. SQLite removes overlap between
the active and recent queries. Fifteen minutes is normally sufficient.

### `request_timeout_seconds`

Total timeout for an individual HTTP request.

### `counties`

List of NWS county UGC codes and short display names. The code controls
filtering; the name controls message text.

```yaml
counties:
  - {code: MIC081, name: Kent}
  - {code: MIC139, name: Ottawa}
```

County codes are not ZIP codes or FIPS codes. See
[NWS county codes](NWS-COUNTIES.md).

### `events`

Exact NWS event names to forward. Event names are case-sensitive.

Common severe-weather choices:

```yaml
events:
  - Tornado Warning
  - Severe Thunderstorm Warning
  - Flash Flood Warning
  - Tornado Watch
  - Severe Thunderstorm Watch
```

Add broader products only if the extra mesh airtime is appropriate:

```yaml
  - Flood Warning
  - Flood Watch
  - Special Weather Statement
```

## MeshCore settings

### `serial_port`

Use the stable symlink from:

```sh
ls -l /dev/serial/by-id/
```

Avoid `/dev/ttyACM0` when possible because its number can change.

### `baudrate`

USB Companion firmware normally uses `115200`.

### `channel_index`

Zero-based channel slot on the Companion. Slot 0 is normally `Public`. Run
`meshcore-cli get_channels` to find the desired slot. The bot does not create or
modify radio channels.

### `max_message_bytes`

Maximum encoded UTF-8 bytes. The default is 133. Lower it for a particularly
constrained network. Raising it can reduce interoperability with clients that
enforce the current 133-character specification.

### `min_send_interval_seconds`

Minimum delay between transmissions when several alerts arrive together.

### Reconnect settings

`reconnect_initial_seconds` is the first delay after a serial failure.
`reconnect_max_seconds` caps exponential backoff.

## Application settings

### `database`

SQLite state location. The systemd unit grants write access to
`/var/lib/meshcore-wxbot`.

### `timezone`

IANA timezone used for alert expiration times, such as:

```text
America/New_York
America/Chicago
America/Denver
America/Los_Angeles
America/Detroit
```

### `dry_run`

When true, messages are logged and recorded but not sent to the radio. Use it
for initial NWS/configuration testing. Synthetic test alerts use unique IDs, so
they can be repeated.
