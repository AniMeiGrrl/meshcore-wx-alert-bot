# Proxmox USB passthrough

## Virtual machine

A VM is the simplest deployment because Proxmox can pass the complete USB
device through to the guest.

On the Proxmox host, compare `lsusb` before and after connecting the radio:

```sh
lsusb
lsusb -t
```

When several identical radios are connected, do not select only vendor/product
ID. Resolve the new device’s stable physical path:

```sh
udevadm info -q path -n /dev/bus/usb/BBB/DDD
```

Example result:

```text
/devices/.../usb1/1-9/1-9.1
```

For VM 110, attach that physical port:

```sh
qm set 110 -usb0 host=1-9.1
qm config 110 | grep usb
qm reboot 110
```

Inside the guest:

```sh
lsusb
ls -l /dev/serial/by-id/
ls -l /dev/ttyACM*
```

Use the `/dev/serial/by-id/...` path in `config.yaml`.

## LXC

An unprivileged LXC requires bind-mounting the character device and allowing its
device major/minor through the container’s device policy. USB serial device
numbers may change on reconnect, and exact configuration depends on Proxmox and
container security settings.

For a small Internet-connected alert service, a minimal Debian VM is usually
easier to maintain. If using LXC, consult the current Proxmox device-passthrough
documentation and verify behavior after host and firmware upgrades.

## Multiple identical radios

Vendor/product passthrough such as `303a:0002` can match the wrong Heltec when
several are attached. A physical topology path such as `1-9.1` is stable as long
as the radio remains connected through the same host port and hub topology.
