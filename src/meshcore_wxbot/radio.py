from __future__ import annotations

import asyncio
import logging
import time

LOG = logging.getLogger(__name__)


class Radio:
    def __init__(
        self,
        port: str,
        baudrate: int,
        channel: int,
        min_interval: float,
        reconnect_initial: float,
        reconnect_max: float,
        dry_run: bool,
    ):
        self.port = port
        self.baudrate = baudrate
        self.channel = channel
        self.min_interval = min_interval
        self.reconnect_initial = reconnect_initial
        self.reconnect_max = reconnect_max
        self.dry_run = dry_run
        self.client = None
        self.last_send = 0.0

    async def send(self, message: str) -> None:
        if self.dry_run:
            LOG.info("DRY RUN channel=%d message=%r", self.channel, message)
            return
        delay = self.min_interval - (time.monotonic() - self.last_send)
        if delay > 0:
            await asyncio.sleep(delay)
        backoff = self.reconnect_initial
        while True:
            try:
                if self.client is None or not self.client.is_connected:
                    await self._connect()
                result = await self.client.commands.send_chan_msg(self.channel, message)
                if getattr(getattr(result, "type", None), "value", "") == "command_error":
                    raise RuntimeError(f"radio rejected message: {result.payload}")
                self.last_send = time.monotonic()
                LOG.info("sent channel=%d bytes=%d message=%r", self.channel, len(message.encode()), message)
                return
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                LOG.warning("radio send/connect failed: %s; retrying in %.1fs", exc, backoff)
                await self.close()
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, self.reconnect_max)

    async def _connect(self) -> None:
        from meshcore import MeshCore

        LOG.info("connecting to MeshCore radio on %s", self.port)
        self.client = await MeshCore.create_serial(self.port, self.baudrate)
        LOG.info("MeshCore radio connected")

    async def close(self) -> None:
        if self.client is not None:
            try:
                await self.client.disconnect()
            except Exception:
                pass
            self.client = None
