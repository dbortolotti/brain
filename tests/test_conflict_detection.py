from __future__ import annotations

from memory_stack.brain_models import RememberRequest
from memory_stack.brain_service import remember
from memory_stack.brain_store import BrainStore
from memory_stack.cfg import Settings


def test_duplicate_like_does_not_create_second_current_card(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    first = remember(RememberRequest(input="Sam likes Bill Evans."), settings)
    second = remember(RememberRequest(input="Sam likes Bill Evans"), settings)

    store = BrainStore(settings)
    current = store.search_memory("Sam Bill Evans")
    assert {memory["id"] for memory in current} == {first.memory_cards[0].id}
    assert second.memory_cards[0].status == "archived"
    assert second.conflicts[0]["relation"] == "duplicates"


def test_additive_likes_remain_current(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    first = remember(RememberRequest(input="Sam likes Bill Evans."), settings)
    second = remember(RememberRequest(input="Sam likes Sonny Rollins."), settings)

    store = BrainStore(settings)
    assert store.get_memory(first.memory_cards[0].id)["status"] == "current"
    assert store.get_memory(second.memory_cards[0].id)["status"] == "current"
    assert second.conflicts == []


def test_employment_transition_supersedes_prior_workplace(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    old = remember(RememberRequest(input="Sam works at Goldman."), settings)
    new = remember(RememberRequest(input="Sam left Goldman and joined Point72."), settings)

    store = BrainStore(settings)
    old_memory = store.get_memory(old.memory_cards[0].id)
    new_memory = store.get_memory(new.memory_cards[0].id)

    assert old_memory["status"] == "superseded"
    assert new_memory["status"] == "current"
    assert {
        (link["relation"], link["to_memory_id"])
        for link in new_memory["links"]
        if link["from_memory_id"] == new_memory["id"]
    } == {("supersedes", old_memory["id"])}
    assert new.conflicts[0]["reason"] == "employment_transition_replaces_prior_workplace"


def test_correction_supersedes_prior_like(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    old = remember(RememberRequest(input="Sam likes Bill Evans."), settings)
    new = remember(
        RememberRequest(input="Actually, Sam likes early Coltrane, not Bill Evans."),
        settings,
    )

    store = BrainStore(settings)
    old_memory = store.get_memory(old.memory_cards[0].id)
    new_memory = store.get_memory(new.memory_cards[0].id)

    assert old_memory["status"] == "superseded"
    assert new_memory["status"] == "current"
    assert any(link["relation"] == "supersedes" for link in new_memory["links"])
    assert new.conflicts[0]["reason"] == "explicit_correction_negates_prior_like"


def test_children_count_mismatch_creates_contradiction_link(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    first = remember(RememberRequest(input="Sam has two children."), settings)
    second = remember(RememberRequest(input="Sam has no children."), settings)

    store = BrainStore(settings)
    first_memory = store.get_memory(first.memory_cards[0].id)
    second_memory = store.get_memory(second.memory_cards[0].id)

    assert first_memory["status"] == "current"
    assert second_memory["status"] == "current"
    assert {
        (link["relation"], link["to_memory_id"])
        for link in second_memory["links"]
        if link["from_memory_id"] == second_memory["id"]
    } == {("contradicts", first_memory["id"])}
    assert second.conflicts[0]["type"] == "conflict"


def brain_test_settings(tmp_path) -> Settings:
    return Settings(brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}")
