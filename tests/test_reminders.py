from __future__ import annotations

from datetime import timedelta

from memory_stack.brain_models import RememberRequest
from memory_stack.brain_service import remember
from memory_stack.brain_store import BrainStore, now_utc
from memory_stack.config import Settings
from memory_stack.workers.reminders import (
    find_relevant_open_loops,
    list_due_open_loops,
    mark_reminded,
)


def test_open_question_creates_due_open_loop(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    receipt = remember(
        RememberRequest(input="I want to learn more about knowledge graphs."),
        settings,
    )

    loops = list_due_open_loops(settings=settings)

    assert loops[0]["id"] == receipt.open_loops[0]["id"]
    assert loops[0]["priority"] == "normal"
    assert loops[0]["reminder_policy"] == "opportunistic_or_weekly"


def test_closed_loop_is_not_returned(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    receipt = remember(
        RememberRequest(input="I want to learn more about knowledge graphs."),
        settings,
    )
    BrainStore(settings).update_open_loop_status(receipt.open_loops[0]["id"], "closed")

    assert list_due_open_loops(settings=settings) == []


def test_recently_reminded_loop_suppressed_unless_included(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    receipt = remember(
        RememberRequest(input="I want to learn more about knowledge graphs."),
        settings,
    )
    reminded_at = now_utc()

    mark_reminded(
        receipt.open_loops[0]["id"],
        settings=settings,
        reminded_at=reminded_at,
        next_review_after=timedelta(days=7),
    )

    assert list_due_open_loops(settings=settings, now=reminded_at + timedelta(hours=1)) == []
    assert list_due_open_loops(
        settings=settings,
        now=reminded_at + timedelta(hours=1),
        include_recently_reminded=True,
    ) == []

    BrainStore(settings).mark_open_loop_reminded(
        receipt.open_loops[0]["id"],
        reminded_at=reminded_at,
        next_review_at=reminded_at,
    )
    assert list_due_open_loops(settings=settings, now=reminded_at + timedelta(hours=1)) == []
    assert list_due_open_loops(
        settings=settings,
        now=reminded_at + timedelta(hours=1),
        include_recently_reminded=True,
    )


def test_topic_query_retrieves_relevant_open_loop(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    receipt = remember(
        RememberRequest(input="I want to learn more about knowledge graphs."),
        settings,
    )

    loops = find_relevant_open_loops("knowledge graph notes", settings=settings)

    assert [loop["id"] for loop in loops] == [receipt.open_loops[0]["id"]]
    assert loops[0]["relevance_score"] > 0


def brain_test_settings(tmp_path) -> Settings:
    return Settings(brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}")
