"""Measure G6a Q1-Q5 for Substack through the local stdio launcher.

Creates ONE throwaway draft titled with a unique marker, reads it back, finds it
by marker, schedules it far out (audience fields omitted, so the defaults are
what gets measured), reads the schedule back, unschedules, reads again, then
deletes it and confirms the read fails. Nothing is published: there is no
publish tool, and the schedule is removed before the probe ends, including on
failure.

Usage: .venv/bin/python local/g6a_probe.py [--days 30] [--list-tools-only]
Prints measurements only; never prints a credential.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import secrets
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

LAUNCHER = Path(__file__).with_name("substack-gateway-stdio.sh")


def _data(result: Any) -> Any:
    if result.structured_content is not None:
        sc = result.structured_content
        return sc.get("result", sc) if isinstance(sc, dict) else sc
    return result.content[0].text if result.content else None


def _say(label: str, value: Any) -> None:
    print(f"{label}: {json.dumps(value, default=str)}", flush=True)


async def run(days: int, list_only: bool, launcher: str) -> int:
    transport = StdioTransport(command=launcher, args=["--allow-schedule"])
    async with Client(transport) as client:
        tools = sorted(t.name for t in await client.list_tools())
        _say("tools", tools)
        if list_only:
            return 0

        me = _data(await client.call_tool("get_me", {}))
        _say("Q1 get_me", {k: me.get(k) for k in ("id", "handle", "name")} if isinstance(me, dict) else me)

        marker = f"sgq-{datetime.now(UTC):%Y%m%d}-{secrets.token_hex(3)}"
        title = f"[{marker}] gateway qualification test, delete me"
        created = _data(
            await client.call_tool(
                "create_draft",
                {"title": title, "body": "Throwaway draft for a publisher check. Never publish."},
            )
        )
        _say("Q2 create_draft", created)
        draft_id = int(created["id"])
        scheduled = False
        try:
            state = _data(await client.call_tool("get_draft", {"draft_id": draft_id}))
            _say(
                "Q3 get_draft",
                {k: state.get(k) for k in ("title", "audience", "is_published", "post_date", "scheduled_releases")},
            )

            listing = _data(await client.call_tool("list_drafts", {}))
            text = json.dumps(listing, default=str)
            _say("Q4 marker found in list_drafts", marker in text)

            when = (datetime.now(UTC) + timedelta(days=days)).replace(microsecond=0)
            release = _data(
                await client.call_tool(
                    "schedule_draft",
                    {"draft_id": draft_id, "scheduled_at": when.isoformat().replace("+00:00", "Z")},
                )
            )
            scheduled = True
            _say("Q5 schedule_draft (audience fields omitted)", release)
            state = _data(await client.call_tool("get_draft", {"draft_id": draft_id}))
            _say("Q5 read after schedule", {k: state.get(k) for k in ("is_published", "scheduled_releases")})

            _say("Q5 unschedule_draft", _data(await client.call_tool("unschedule_draft", {"draft_id": draft_id})))
            scheduled = False
            state = _data(await client.call_tool("get_draft", {"draft_id": draft_id}))
            _say("Q5 read after unschedule", {k: state.get(k) for k in ("is_published", "scheduled_releases")})
        finally:
            if scheduled:
                _say("cleanup unschedule", _data(await client.call_tool("unschedule_draft", {"draft_id": draft_id})))
            _say("delete_draft", _data(await client.call_tool("delete_draft", {"draft_id": draft_id})))
            gone = await client.call_tool("get_draft", {"draft_id": draft_id}, raise_on_error=False)
            _say("read after delete is_error", gone.is_error)
            if gone.is_error and gone.content:
                _say("read after delete message", gone.content[0].text[:200])
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--list-tools-only", action="store_true")
    parser.add_argument("--launcher", default=str(LAUNCHER))
    args = parser.parse_args()
    if args.days < 7:
        sys.exit("--days must be at least 7")
    sys.exit(asyncio.run(run(args.days, args.list_tools_only, args.launcher)))


if __name__ == "__main__":
    main()
