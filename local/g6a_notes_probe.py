"""Measure scheduled-Note Q2-Q5 through the local stdio launcher.

Schedules ONE throwaway Note far out, finds it in the scheduled list by a unique
marker, cancels it, and confirms it is gone. Cancelling a scheduled Note deletes
it (Substack has no unschedule-to-draft), and the cancel runs in a ``finally``
so the Note is removed even if a step fails. Nothing is published.

Usage: uv run --frozen python local/g6a_notes_probe.py [--days 30]
Prints measurements only; never prints a credential.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import secrets
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


async def _listed(client: Client, marker: str) -> list[dict]:
    items = _data(await client.call_tool("list_scheduled_notes", {}))["items"]
    return [i for i in items if marker in i["body"]]


async def run(days: int) -> int:
    transport = StdioTransport(command=str(LAUNCHER), args=["--allow-schedule"])
    async with Client(transport) as client:
        tools = {t.name for t in await client.list_tools()}
        _say("note tools", sorted(t for t in tools if "note" in t))
        marker = f"sgn-{datetime.now(UTC):%Y%m%d}-{secrets.token_hex(3)}"
        when = (datetime.now(UTC) + timedelta(days=days)).replace(microsecond=0)
        note_id = None
        try:
            created = _data(
                await client.call_tool(
                    "schedule_note",
                    {
                        "content": f"{marker} throwaway scheduled note, do not publish",
                        "scheduled_at": when.isoformat(),
                    },
                )
            )
            note_id = created["id"]
            _say(
                "Q2 schedule_note",
                {"id": note_id, "scheduled_at": created["scheduled_at"]},
            )
            _say(
                "Q3+Q4 listed by marker",
                [(i["id"], i["scheduled_at"]) for i in await _listed(client, marker)],
            )
        finally:
            if note_id is not None:
                _say(
                    "Q5 unschedule_note",
                    _data(
                        await client.call_tool("unschedule_note", {"note_id": note_id})
                    ),
                )
        _say("Q5 listed after cancel", await _listed(client, marker))
        refused = await client.call_tool(
            "unschedule_note", {"note_id": note_id}, raise_on_error=False
        )
        _say("Q5 second cancel refused", bool(refused.is_error))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--days", type=int, default=30)
    raise SystemExit(asyncio.run(run(parser.parse_args().days)))


if __name__ == "__main__":
    main()
