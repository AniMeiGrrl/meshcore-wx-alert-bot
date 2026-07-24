from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Iterable

import aiohttp

from .models import Alert

LOG = logging.getLogger(__name__)
ACTIVE_API = "https://api.weather.gov/alerts/active"
HISTORY_API = "https://api.weather.gov/alerts"
COUNTY_ZONES_API = "https://api.weather.gov/zones/county"


class NWSClient:
    def __init__(self, user_agent: str, timeout: int = 20):
        self.headers = {
            "User-Agent": user_agent,
            "Accept": "application/geo+json",
        }
        self.timeout = aiohttp.ClientTimeout(total=timeout)

    async def fetch(
        self, county_codes: Iterable[str], history_minutes: int = 15
    ) -> list[Alert]:
        since = datetime.now(timezone.utc) - timedelta(minutes=history_minutes)
        async with aiohttp.ClientSession(headers=self.headers, timeout=self.timeout) as session:
            pages = await asyncio.gather(
                *(
                    request
                    for code in county_codes
                    for request in (
                        self._county(session, ACTIVE_API, {"zone": code}),
                        self._county(
                            session,
                            HISTORY_API,
                            {"zone": code, "start": since.isoformat(timespec="seconds")},
                        ),
                    )
                ),
                return_exceptions=True,
            )
        unique: dict[str, Alert] = {}
        failures = 0
        for page in pages:
            if isinstance(page, BaseException):
                failures += 1
                LOG.warning("NWS county request failed: %s", page)
                continue
            for alert in page:
                unique[alert.identifier] = alert
        if failures == len(pages):
            raise RuntimeError("all NWS county requests failed")
        return list(unique.values())

    async def _county(
        self, session: aiohttp.ClientSession, endpoint: str, params: dict[str, str]
    ) -> list[Alert]:
        async with session.get(endpoint, params=params) as response:
            response.raise_for_status()
            payload = await response.json()
            return [Alert.from_feature(f) for f in payload.get("features", [])]

    async def list_counties(self, state: str) -> list[tuple[str, str]]:
        state = state.strip().upper()
        if len(state) != 2 or not state.isalpha():
            raise ValueError("state must be a two-letter postal abbreviation")
        async with aiohttp.ClientSession(
            headers=self.headers, timeout=self.timeout
        ) as session:
            async with session.get(
                COUNTY_ZONES_API,
                params={"area": state, "limit": "500"},
            ) as response:
                response.raise_for_status()
                payload = await response.json()
        counties = []
        for feature in payload.get("features", []):
            props = feature.get("properties") or {}
            code = str(props.get("id") or feature.get("id", "").rsplit("/", 1)[-1])
            name = str(props.get("name") or "").removesuffix(" County")
            if code and name:
                counties.append((code, name))
        return sorted(set(counties), key=lambda item: item[1])
