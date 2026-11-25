"""The local stdio launcher registers note scheduling only behind --allow-schedule."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from gateway_notes_mcp import capability

_PATH = Path(__file__).resolve().parents[1] / "local" / "stdio_server.py"


def _load():
    spec = importlib.util.spec_from_file_location("local_stdio_server", _PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_NOTE_SCHEDULE = {"schedule_note", "unschedule_note"}
_PUBLIC_NOW = {
    "create_note",
    "reply_to_note",
    "like_note",
    "unlike_note",
    "delete_note",
}


def test_note_schedule_tools_are_schedule_gated_only() -> None:
    m = _load()
    assert _NOTE_SCHEDULE <= m._SCHEDULE_TOOLS
    assert not (_NOTE_SCHEDULE & m._BASE_TOOLS)


def test_scheduled_notes_list_is_a_base_read() -> None:
    m = _load()
    assert "list_scheduled_notes" in m._BASE_TOOLS
    assert "list_scheduled_notes" not in m._SCHEDULE_TOOLS


def test_no_immediate_public_write_tool_is_ever_registered() -> None:
    m = _load()
    assert not (_PUBLIC_NOW & (m._BASE_TOOLS | m._SCHEDULE_TOOLS))


@pytest.mark.anyio
async def test_note_schedule_tools_exist_in_the_gateway_build() -> None:
    from fastmcp import FastMCP

    mcp = FastMCP("t")
    capability().register(mcp)
    names = {t.name for t in await mcp.list_tools()}
    assert _NOTE_SCHEDULE | {"list_scheduled_notes"} <= names
