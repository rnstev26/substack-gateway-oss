from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from gateway_notes.service import NotesService, ScheduleRefused

_NOW = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)


def _resp(payload: object) -> MagicMock:
    r = MagicMock()
    r.json.return_value = payload
    return r


def _drafts(*items: dict) -> MagicMock:
    return _resp({"drafts": list(items), "hasMore": False, "nextCursor": None})


def _draft(note_id: int, trigger_at: str | None) -> dict:
    return {
        "id": note_id,
        "body": "hello",
        "type": "feed",
        "date": "2026-11-24T12:00:00.000Z",
        "trigger_at": trigger_at,
        "reply_minimum_role": "everyone",
        "body_json": {"type": "doc"},
        "user_id": 1,
    }


@pytest.mark.anyio
async def test_schedule_note_posts_draft_with_trigger_and_verifies_listing() -> None:
    sub = AsyncMock()
    sub.post.return_value = _resp({"id": 55})
    sub.get.return_value = _drafts(_draft(55, "2026-12-03T05:00:00.000Z"))
    service = NotesService(AsyncMock(), sub)

    draft = await service.schedule_note("hello", "2026-12-03T05:00:00Z", now=_NOW)

    assert draft.id == 55
    path = sub.post.await_args.args[0]
    body = sub.post.await_args.kwargs["json"]
    assert path == "comment/draft"
    assert set(body) == {"bodyJson", "replyMinimumRole", "trigger_at"}
    assert body["trigger_at"] == "2026-12-03T05:00:00.000Z"
    assert body["replyMinimumRole"] == "everyone"
    assert body["bodyJson"]["type"] == "doc"
    assert body["bodyJson"]["attrs"] == {"schemaVersion": "v1", "title": None}
    # Never the immediate-publish path.
    assert "comment/feed" not in path
    sub.get.assert_awaited_once_with("feed/drafts", params={"limit": 50})


@pytest.mark.anyio
async def test_schedule_note_normalizes_offset_time_to_utc() -> None:
    sub = AsyncMock()
    sub.post.return_value = _resp({"id": 7})
    sub.get.return_value = _drafts(_draft(7, "2026-12-03T05:00:00.000Z"))

    await NotesService(AsyncMock(), sub).schedule_note(
        "hi", "2026-12-02T23:00:00-06:00", now=_NOW
    )

    assert (
        sub.post.await_args.kwargs["json"]["trigger_at"] == "2026-12-03T05:00:00.000Z"
    )


@pytest.mark.anyio
@pytest.mark.parametrize(
    "when",
    [
        "2026-11-24T11:00:00Z",  # past
        "2026-11-24T12:00:00Z",  # now
        "2026-11-26T11:59:00Z",  # 1 minute short of 48 h
    ],
)
async def test_schedule_note_refuses_anything_sooner_than_min_lead(when: str) -> None:
    sub = AsyncMock()

    with pytest.raises(ScheduleRefused):
        await NotesService(AsyncMock(), sub).schedule_note("hi", when, now=_NOW)

    sub.post.assert_not_awaited()


@pytest.mark.anyio
async def test_schedule_note_accepts_exactly_min_lead() -> None:
    sub = AsyncMock()
    sub.post.return_value = _resp({"id": 9})
    sub.get.return_value = _drafts(_draft(9, "2026-11-26T12:00:00.000Z"))

    await NotesService(AsyncMock(), sub).schedule_note(
        "hi", _NOW + timedelta(hours=48), now=_NOW
    )

    sub.post.assert_awaited_once()


@pytest.mark.anyio
async def test_schedule_note_fails_loudly_when_not_found_scheduled() -> None:
    sub = AsyncMock()
    sub.post.return_value = _resp({"id": 11})
    sub.get.return_value = _drafts(_draft(12, "2026-12-03T05:00:00.000Z"))

    with pytest.raises(RuntimeError, match="not in the scheduled list"):
        await NotesService(AsyncMock(), sub).schedule_note(
            "hi", "2026-12-03T05:00:00Z", now=_NOW
        )


@pytest.mark.anyio
async def test_list_scheduled_notes_drops_drafts_without_trigger() -> None:
    sub = AsyncMock()
    sub.get.return_value = _drafts(
        _draft(1, "2026-12-03T05:00:00.000Z"), _draft(2, None)
    )

    drafts = await NotesService(AsyncMock(), sub).list_scheduled_notes()

    assert [d.id for d in drafts] == [1]


@pytest.mark.anyio
async def test_unschedule_note_deletes_only_a_listed_scheduled_note() -> None:
    sub = AsyncMock()
    sub.get.return_value = _drafts(_draft(396310605, "2026-12-03T05:00:00.000Z"))

    await NotesService(AsyncMock(), sub).unschedule_note(396310605, now=_NOW)

    sub.delete.assert_awaited_once_with("comment/396310605")


@pytest.mark.anyio
@pytest.mark.parametrize(
    "listing",
    [
        (),  # published notes never appear in the drafts list
        (_draft(5, None),),  # an unscheduled draft is not a scheduled note
    ],
)
async def test_unschedule_note_refuses_ids_that_are_not_scheduled(listing) -> None:
    sub = AsyncMock()
    sub.get.return_value = _drafts(*listing)

    with pytest.raises(ScheduleRefused):
        await NotesService(AsyncMock(), sub).unschedule_note(5, now=_NOW)

    sub.delete.assert_not_awaited()


@pytest.mark.anyio
async def test_unschedule_note_refuses_within_cutoff_of_trigger() -> None:
    sub = AsyncMock()
    sub.get.return_value = _drafts(_draft(8, "2026-11-24T12:04:00.000Z"))

    with pytest.raises(ScheduleRefused, match="posts within"):
        await NotesService(AsyncMock(), sub).unschedule_note(8, now=_NOW)

    sub.delete.assert_not_awaited()
