from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from .config import Config
from .formatting import format_alert
from .models import Alert
from .nws import NWSClient
from .radio import Radio
from .state import State

LOG = logging.getLogger(__name__)


class WeatherBot:
    def __init__(self, config: Config):
        self.config = config
        self.nws = NWSClient(config.user_agent, config.request_timeout_seconds)
        self.state = State(config.database)
        self.radio = Radio(
            config.serial_port,
            config.baudrate,
            config.channel_index,
            config.min_send_interval_seconds,
            config.reconnect_initial_seconds,
            config.reconnect_max_seconds,
            config.dry_run,
        )

    async def process(self, alert: Alert) -> bool:
        if alert.event not in self.config.events:
            return False
        if alert.status.lower() not in {"actual", "exercise", "test", "draft"}:
            return False
        # The rolling history request finds update/cancel products. Do not
        # retransmit a newly discovered alert whose useful lifetime has ended.
        if (
            alert.action == "NEW"
            and alert.event_time
            and alert.event_time <= datetime.now(timezone.utc)
        ):
            return False
        message = format_alert(
            alert, self.config.counties, self.config.timezone, self.config.max_message_bytes
        )
        fingerprint = self.state.fingerprint(alert, message)
        if self.state.delivered(fingerprint):
            return False
        await self.radio.send(message)
        self.state.record(fingerprint, alert, message)
        return True

    async def poll_once(self) -> int:
        alerts = await self.nws.fetch(
            self.config.counties, self.config.history_minutes
        )
        sent = 0
        for alert in sorted(alerts, key=lambda a: a.sent):
            sent += await self.process(alert)
        LOG.info("poll complete: fetched=%d transmitted=%d", len(alerts), sent)
        return sent

    async def run(self) -> None:
        LOG.info("starting; dry_run=%s counties=%d events=%d", self.config.dry_run, len(self.config.counties), len(self.config.events))
        try:
            while True:
                try:
                    await self.poll_once()
                except asyncio.CancelledError:
                    raise
                except Exception:
                    LOG.exception("poll failed")
                await asyncio.sleep(self.config.poll_seconds)
        finally:
            await self.close()

    async def close(self) -> None:
        await self.radio.close()
        self.state.close()
