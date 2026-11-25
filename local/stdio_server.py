"""Local stdio MCP server for one Substack account, credentials from the Keychain.

Run it through ``local/substack-gateway-stdio.sh``, never directly. The launcher
reads the ``substack.sid`` cookie from the macOS Keychain and hands it to this
process on file descriptor 3. It is read once, the descriptor is closed, and
the value lives only in this process's memory: never in argv, the environment,
a file or a log.

Transport is stdio and nothing else. There is no listening socket, so the
single-account credential resolver below can never answer a network caller.

Tools that write in public immediately (notes, comments, replies, likes,
restacks) are not registered. Scheduling is registered only with
``--allow-schedule``; without it the server can create and edit drafts but
cannot put anything on a path to publication.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from typing import Any

_COOKIE_FD = 3
_DEFAULT_PUBLICATION_URL = "https://theunstagedself.substack.com"

# Reads plus draft work. Every tool not listed here is left unregistered.
_BASE_TOOLS = frozenset(
    {
        "get_me",
        "list_drafts",
        "get_draft",
        "create_draft",
        "update_draft",
        "delete_draft",
        "check_draft",
        "get_ai_detection",
        "upload_image",
        "get_my_posts",
        "get_post",
        "get_post_counts",
        "get_my_notes",
        "get_note",
        "get_dashboard_summary",
        "get_dashboard_period",
        "get_subscriber_timeseries",
        "get_email_timeseries",
        "get_post_engagement",
        "get_post_recipients",
        "get_post_traffic",
        "get_post_growth",
    }
)
_SCHEDULE_TOOLS = frozenset(
    {
        "schedule_draft",
        "unschedule_draft",
        "schedule_note",
        "unschedule_note",
        "list_scheduled_notes",
    }
)


def _fail(message: str, code: int = 2) -> None:
    print(f"substack-gateway-stdio: {message}", file=sys.stderr)
    sys.exit(code)


def _read_cookie() -> str:
    try:
        chunks = []
        while True:
            chunk = os.read(_COOKIE_FD, 4096)
            if not chunk:
                break
            chunks.append(chunk)
    except OSError:
        _fail("no credential on fd 3; start this through the launcher")
    finally:
        try:
            os.close(_COOKIE_FD)
        except OSError:
            pass
    try:
        value = b"".join(chunks).decode("utf-8", errors="strict").strip()
    except UnicodeDecodeError:
        # Generic message: the exception text would quote a byte of the value.
        _fail("the Keychain item is not UTF-8 text")
    if not value:
        _fail("the Keychain item is empty")
    if any(c.isspace() for c in value):
        _fail("the Keychain item holds whitespace; store the cookie value only")
    return value


class _SingleAccountResolver:
    """Returns the one stored credential set. Safe only because transport is stdio."""

    def __init__(self, credentials: Any) -> None:
        self._credentials = credentials

    async def resolve(self, access_token: Any) -> Any:
        return self._credentials


async def _filtered_server(full: Any, allowed: frozenset[str]) -> Any:
    from fastmcp import FastMCP

    server = FastMCP("substack-gateway-local")
    tools = await full.list_tools()
    names = set()
    for tool in tools:
        if tool.name in allowed:
            server.add_tool(tool)
            names.add(tool.name)
    missing = allowed - names
    if missing:
        _fail(f"allowlisted tools not found in this gateway build: {sorted(missing)}")
    return server


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--allow-schedule",
        action="store_true",
        help="also register the draft and note scheduling tools",
    )
    args = parser.parse_args()

    # Read the credential before importing the gateway, so nothing else runs first.
    cookie = _read_cookie()
    logging.basicConfig(level=logging.WARNING, stream=sys.stderr)

    from fastmcp import FastMCP

    from gateway_core.auth import BearerCredentials, validate_bearer_credentials
    from gateway_core.credentials import set_credential_resolver
    from substack_gateway.registry import load_mcp_capabilities

    credentials = BearerCredentials(
        publication_url=os.environ.get("SG_PUBLICATION_URL", _DEFAULT_PUBLICATION_URL),
        substack_sid=cookie,
        # Her account has no connect.sid; Substack accepts substack.sid in both
        # slots (measured 2026-11-20), and the gateway refuses an empty one.
        connect_sid=cookie,
    )
    del cookie
    validate_bearer_credentials(credentials, source="Keychain credentials")
    set_credential_resolver(_SingleAccountResolver(credentials))

    full = FastMCP("substack-gateway-full")
    for cap in load_mcp_capabilities():
        cap.register(full)

    allowed = _BASE_TOOLS | (_SCHEDULE_TOOLS if args.allow_schedule else frozenset())
    server = asyncio.run(_filtered_server(full, allowed))
    server.run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main()
