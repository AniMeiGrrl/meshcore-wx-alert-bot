# MeshCore radio and channels

The bot requires a radio running MeshCore **USB Companion** firmware. Configure
the radio preset, identity, path-hash size, and channels before moving it to the
server.

## Install the CLI

On a workstation:

```sh
pipx install meshcore-cli
meshcore-cli -l
meshcore-cli -s /dev/cu.usbmodemXXXXXXXX
```

Linux serial devices commonly appear under `/dev/ttyACM*`; macOS commonly uses
`/dev/cu.usbmodem*`.

Inside the interactive prompt:

```text
infos
ver
get_channels
```

## Radio parameters

Every node that should communicate must use the same frequency, bandwidth,
spreading factor, and coding rate. Use the preset agreed upon by the local mesh.
Do not assume another region’s settings.

The current recommended USA/Canada preset is documented by MeshCore as:

```text
Frequency: 910.525 MHz
Bandwidth: 62.5 kHz
Spreading factor: 7
Coding rate: 5
```

Example CLI command:

```text
set radio 910.525,62.5,7,5
reboot
```

Confirm local practice and regulatory requirements before transmitting.

## Public channel

Channel index 0 is normally the built-in Public channel:

```text
0: Public [8b3387e9c5cdea6ac9e5edbaa115cd72]
```

Use:

```yaml
channel_index: 0
```

## Hashtag channels

A channel whose name begins with `#` derives a deterministic 16-byte key from
the channel name. Anyone who knows the exact name can derive the same key, so a
hashtag channel is convenient but not private.

```text
add_channel #localweather
get_channels
```

If it appears in slot 1:

```yaml
channel_index: 1
```

Spelling and capitalization must match on every device.

## Private channels

A private channel uses a random 16-byte secret represented as 32 hexadecimal
characters. Generate one locally:

```sh
openssl rand -hex 16
```

Then use the syntax reported by your installed CLI:

```text
?set_channel
```

Common syntax is:

```text
set_channel 1 Weather 0123456789abcdef0123456789abcdef
```

Never commit a real private-channel secret to GitHub. Configure the same name,
slot, and key on every intended receiver. The bot itself needs only the channel
index because the key resides on the Companion.

## Test a channel

From `meshcore-cli`:

```text
chan 1 Test message
```

Or use `public Test message` for slot 0. Verify receipt on another device before
starting the weather service.

Official references:

- [MeshCore](https://meshcore.io/)
- [MeshCore CLI](https://github.com/meshcore-dev/meshcore-cli)
- [MeshCore Python library](https://github.com/meshcore-dev/meshcore_py)
- [MeshCore documentation](https://docs.meshcore.io/)
