"""Wire models for Substack's note drafts (scheduled notes).

Shapes measured 2026-11-24 against the web composer:

- ``POST /api/v1/comment/draft`` with ``{bodyJson, replyMinimumRole, trigger_at}``
  creates a scheduled note.
- ``GET /api/v1/feed/drafts?limit=N`` lists note drafts as
  ``{drafts: [...], hasMore, nextCursor}``.
- ``DELETE /api/v1/comment/{id}`` removes one. The same call deletes a
  published note, so callers must confirm the id is still a draft first.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SubstackNoteDraft(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    body: str = ""
    type: str | None = None
    date: str | None = None
    trigger_at: str | None = None
    reply_minimum_role: str | None = None


class SubstackNoteDraftsPage(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    drafts: list[SubstackNoteDraft] = []
    has_more: bool = Field(alias="hasMore", default=False)
    next_cursor: str | None = Field(alias="nextCursor", default=None)


class SubstackNoteDraftCreated(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
