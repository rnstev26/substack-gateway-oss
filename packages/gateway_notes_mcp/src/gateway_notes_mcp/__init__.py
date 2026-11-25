from __future__ import annotations

from typing import TYPE_CHECKING

from mcp.types import ToolAnnotations

from gateway_core.capabilities import McpCapability

if TYPE_CHECKING:
    from fastmcp import FastMCP

_FEATURES = (
    "mcp:notes:get",
    "mcp:notes:create",
    "mcp:notes:delete",
    "mcp:notes:like",
    "mcp:notes:unlike",
    "mcp:notes:reply",
    "mcp:notes:replies:list",
    "mcp:notes:schedule",
    "mcp:notes:unschedule",
    "mcp:notes:scheduled:list",
)


def _register(mcp: FastMCP) -> None:
    from gateway_notes_mcp.tools import (
        create_note,
        delete_note,
        get_note,
        like_note,
        list_note_replies,
        list_scheduled_notes,
        reply_to_note,
        schedule_note,
        unlike_note,
        unschedule_note,
    )

    mcp.tool(
        description="Publish a new note to Substack from Markdown content, with an optional link attachment. The `token` argument is optional: pass base64-encoded Substack credentials, or omit it if this deployment resolves credentials from the authenticated session.",
        tags={"notes", "write"},
        annotations=ToolAnnotations(
            title="Create Note",
            read_only_hint=False,
            destructive_hint=False,
            idempotent_hint=False,
            open_world_hint=True,
        ),
        meta={"category": "notes", "substack_endpoint": "POST /comment/feed/"},
    )(create_note)
    mcp.tool(
        description="Permanently delete a Substack note by its numeric ID. The `token` argument is optional: pass base64-encoded Substack credentials, or omit it if this deployment resolves credentials from the authenticated session.",
        tags={"notes", "write", "delete"},
        annotations=ToolAnnotations(
            title="Delete Note",
            read_only_hint=False,
            destructive_hint=True,
            idempotent_hint=True,
            open_world_hint=True,
        ),
        meta={"category": "notes", "substack_endpoint": "DELETE /comment/{note_id}"},
    )(delete_note)
    mcp.tool(
        description="Retrieve a single Substack note by its numeric ID. The `token` argument is optional: pass base64-encoded Substack credentials, or omit it if this deployment resolves credentials from the authenticated session.",
        tags={"notes", "read"},
        annotations=ToolAnnotations(
            title="Get Note",
            read_only_hint=True,
            destructive_hint=False,
            idempotent_hint=True,
            open_world_hint=True,
        ),
        meta={
            "category": "notes",
            "substack_endpoint": "GET /reader/comment/{note_id}",
        },
    )(get_note)
    mcp.tool(
        description="Add a like to a Substack note by its numeric ID. The `token` argument is optional: pass base64-encoded Substack credentials, or omit it if this deployment resolves credentials from the authenticated session.",
        tags={"notes", "write"},
        annotations=ToolAnnotations(
            title="Like Note",
            read_only_hint=False,
            destructive_hint=False,
            idempotent_hint=True,
            open_world_hint=True,
        ),
        meta={
            "category": "notes",
            "substack_endpoint": "POST /comment/{note_id}/reaction",
        },
    )(like_note)
    mcp.tool(
        description="Remove a like from a Substack note by its numeric ID. The `token` argument is optional: pass base64-encoded Substack credentials, or omit it if this deployment resolves credentials from the authenticated session.",
        tags={"notes", "write"},
        annotations=ToolAnnotations(
            title="Unlike Note",
            read_only_hint=False,
            destructive_hint=False,
            idempotent_hint=True,
            open_world_hint=True,
        ),
        meta={
            "category": "notes",
            "substack_endpoint": "DELETE /comment/{note_id}/reaction",
        },
    )(unlike_note)
    mcp.tool(
        description="Reply to a Substack note or to any comment within its thread, from Markdown content. The `token` argument is optional: pass base64-encoded Substack credentials, or omit it if this deployment resolves credentials from the authenticated session.",
        tags={"notes", "write"},
        annotations=ToolAnnotations(
            title="Reply To Note",
            read_only_hint=False,
            destructive_hint=False,
            idempotent_hint=False,
            open_world_hint=True,
        ),
        meta={"category": "notes", "substack_endpoint": "POST /comment/feed/"},
    )(reply_to_note)
    mcp.tool(
        description="List the direct replies to a Substack note by its numeric ID. The `token` argument is optional: pass base64-encoded Substack credentials, or omit it if this deployment resolves credentials from the authenticated session.",
        tags={"notes", "read"},
        annotations=ToolAnnotations(
            title="List Note Replies",
            read_only_hint=True,
            destructive_hint=False,
            idempotent_hint=True,
            open_world_hint=True,
        ),
        meta={
            "category": "notes",
            "substack_endpoint": "GET /reader/comment/{note_id}/replies",
        },
    )(list_note_replies)

    mcp.tool(
        description="Schedule a Substack note to post later. `scheduled_at` is an ISO-8601 timestamp (UTC recommended) at least 48 hours from now; sooner times are refused, so this never posts immediately. The note waits in the composer's Drafts until then. The `token` argument is optional: pass base64-encoded Substack credentials, or omit it if this deployment resolves credentials from the authenticated session.",
        tags={"notes", "write", "schedule"},
        annotations=ToolAnnotations(
            title="Schedule Note",
            read_only_hint=False,
            destructive_hint=False,
            idempotent_hint=False,
            open_world_hint=True,
        ),
        meta={"category": "notes", "substack_endpoint": "POST /comment/draft"},
    )(schedule_note)
    mcp.tool(
        description="List scheduled Substack notes (note drafts with a trigger time), with id, body and scheduled_at. The `token` argument is optional: pass base64-encoded Substack credentials, or omit it if this deployment resolves credentials from the authenticated session.",
        tags={"notes", "read", "schedule"},
        annotations=ToolAnnotations(
            title="List Scheduled Notes",
            read_only_hint=True,
            destructive_hint=False,
            idempotent_hint=True,
            open_world_hint=True,
        ),
        meta={"category": "notes", "substack_endpoint": "GET /feed/drafts"},
    )(list_scheduled_notes)
    mcp.tool(
        description="Cancel a scheduled Substack note by its numeric ID. Substack has no unschedule-to-draft for notes, so the scheduled note is deleted. Refuses any id that is not currently a scheduled note, so it cannot delete a published note. The `token` argument is optional: pass base64-encoded Substack credentials, or omit it if this deployment resolves credentials from the authenticated session.",
        tags={"notes", "write", "delete", "schedule"},
        annotations=ToolAnnotations(
            title="Unschedule Note",
            read_only_hint=False,
            destructive_hint=True,
            idempotent_hint=False,
            open_world_hint=True,
        ),
        meta={"category": "notes", "substack_endpoint": "DELETE /comment/{note_id}"},
    )(unschedule_note)


def capability() -> McpCapability:
    return McpCapability(domain="notes", register=_register, features=_FEATURES)
