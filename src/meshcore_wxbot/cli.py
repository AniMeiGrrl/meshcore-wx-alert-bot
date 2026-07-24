from __future__ import annotations

import argparse
import asyncio
import logging
from datetime import datetime, timedelta, timezone

from .app import WeatherBot
from .config import load_config
from .models import Alert
from .nws import NWSClient


def fake_alert(event: str, county: str, action: str) -> Alert:
    now = datetime.now(timezone.utc)
    headline = f"{event} issued for {county} County"
    message_type = {"new": "Alert", "update": "Update", "cancel": "Cancel"}[action]
    if action == "cancel":
        headline = f"{event} cancelled for {county} County"
    return Alert(
        identifier=f"manual-test-{now.timestamp()}",
        event=event,
        message_type=message_type,
        status="Test",
        sent=now.isoformat(),
        expires=(now + timedelta(hours=1)).isoformat(),
        ends=None,
        headline=headline,
        description="HAZARD...70 mph wind gusts and quarter size hail. SOURCE...Manual test.",
        instruction="This is only a test.",
        area_desc=f"{county} County",
        affected_zones=(),
        references=("manual-test-series",) if action != "new" else (),
        parameters={"maxWindGust": ["70 mph"], "maxHailSize": ["1.00 in"]},
    )


async def _main(args: argparse.Namespace) -> None:
    if args.command == "list-counties":
        client = NWSClient(args.user_agent)
        counties = await client.list_counties(args.state)
        for code, name in counties:
            print(f"{code:<8} {name}")
        return
    config = load_config(args.config)
    bot = WeatherBot(config)
    if args.command == "run":
        await bot.run()
    elif args.command == "once":
        try:
            await bot.poll_once()
        finally:
            await bot.close()
    else:
        try:
            await bot.process(fake_alert(args.event, args.county, args.action))
        finally:
            await bot.close()


def main() -> None:
    parser = argparse.ArgumentParser(prog="meshcore-wxbot")
    parser.add_argument("-c", "--config", default="/etc/meshcore-wxbot/config.yaml")
    parser.add_argument("--log-level", default="INFO")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("run", help="poll continuously")
    sub.add_parser("once", help="poll once and exit")
    test = sub.add_parser("test-alert", help="send a synthetic alert")
    test.add_argument("--event", default="Severe Thunderstorm Warning")
    test.add_argument("--county", default="Example")
    test.add_argument("--action", choices=["new", "update", "cancel"], default="new")
    counties = sub.add_parser(
        "list-counties",
        help="list official NWS county codes for a state",
    )
    counties.add_argument("state", help="two-letter state abbreviation, e.g. MI")
    counties.add_argument(
        "--user-agent",
        default="meshcore-wxbot-county-lookup/1.0 (admin@example.com)",
        help="identifying NWS User-Agent with contact information",
    )
    args = parser.parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(levelname)s %(name)s: %(message)s",
    )
    try:
        asyncio.run(_main(args))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
