# Operations and upgrades

## Service commands

```sh
sudo systemctl status meshcore-wxbot
sudo systemctl restart meshcore-wxbot
sudo systemctl stop meshcore-wxbot
sudo journalctl -u meshcore-wxbot -f
sudo journalctl -u meshcore-wxbot --since today
```

## One polling cycle

Stop the service first so two processes do not compete for the serial port:

```sh
sudo systemctl stop meshcore-wxbot
sudo -u meshcore-wxbot \
  /opt/meshcore-wxbot/venv/bin/meshcore-wxbot \
  -c /etc/meshcore-wxbot/config.yaml once
sudo systemctl start meshcore-wxbot
```

## Synthetic tests

```sh
sudo -u meshcore-wxbot \
  /opt/meshcore-wxbot/venv/bin/meshcore-wxbot \
  -c /etc/meshcore-wxbot/config.yaml \
  test-alert --event "Tornado Warning" --county Example
```

Exercise CAP lifecycle formatting:

```sh
... test-alert --action update
... test-alert --action cancel
```

## Back up state

The SQLite database prevents retransmission of previously delivered products:

```text
/var/lib/meshcore-wxbot/state.sqlite3
```

Stop the service before copying it. Deleting the database resets all delivery
history and can cause currently active alerts to transmit again.

## Upgrade from Git

Preserve `/etc/meshcore-wxbot/config.yaml` and the state database. From a fresh
checkout:

```sh
sudo systemctl stop meshcore-wxbot
sudo cp -a . /opt/meshcore-wxbot/app/
sudo /opt/meshcore-wxbot/venv/bin/pip install --upgrade \
  /opt/meshcore-wxbot/app
sudo cp systemd/meshcore-wxbot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start meshcore-wxbot
```

Review `CHANGELOG.md` and compare new keys in `config.example.yaml` before
starting the upgraded service.
