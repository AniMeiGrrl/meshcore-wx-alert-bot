# Troubleshooting

## Radio does not appear

```sh
lsusb
ls -l /dev/serial/by-id/
dmesg | tail -50
```

Confirm the firmware is the USB Companion variant, the cable carries data, and
the device is passed through to the correct VM.

## Permission denied

```sh
id meshcore-wxbot
ls -l /dev/ttyACM0
sudo usermod -aG dialout meshcore-wxbot
```

The account should belong to `dialout`, and the device should normally be
`root:dialout` with group read/write permission.

Authoritative open test:

```sh
sudo -u meshcore-wxbot python3 -c \
'import os; fd=os.open("/dev/ttyACM0", os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK); print("radio opened"); os.close(fd)'
```

## Device or resource busy

Only one process can own the serial connection. Stop `meshcore-cli`, browser
flashers, terminal monitors, and any existing bot process:

```sh
sudo systemctl stop meshcore-wxbot
sudo lsof /dev/ttyACM0
```

## NWS returns errors

- Confirm Internet and DNS access to `api.weather.gov`.
- Use a real contact address in `nws.user_agent`.
- Keep `poll_seconds` at 30 or more.
- Check the county code with `meshcore-wxbot list-counties STATE`.
- Review `journalctl -u meshcore-wxbot`.

The bot continues if an individual county request fails, but reports an error
when all county requests fail.

## No alerts are transmitted

Zero fetched alerts is normal when no configured product is active or recent.
Check:

- exact event names and capitalization;
- county UGC codes;
- `dry_run` value;
- `channel_index`;
- radio parameters matching the local mesh;
- the receiving device has the same channel name/key.

Run `test-alert` to separate radio/channel problems from NWS availability.

## Repeated alerts

Verify the database path is persistent and writable:

```sh
sudo -u meshcore-wxbot ls -l /var/lib/meshcore-wxbot/
```

Do not place the database in `/tmp`. If the database was removed, current active
products can be sent again.

## Unicode or truncated messages

The limit is encoded UTF-8 bytes, not Python characters. Keep
`max_message_bytes: 133` unless all participating clients have been tested with
a different value. Required shelter wording is retained before optional detail.
