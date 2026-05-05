from __future__ import annotations

from typing import Any

import pytest

from memory_stack.brain_models import RecallRequest, RememberRequest
from memory_stack.brain_service import (
    merge_entities,
    profile_entity,
    recall,
    remember,
    rebuild_cognee,
    review_recent,
    sync_cognee,
    undo_last,
)
from memory_stack.brain_store import BrainStore
from memory_stack.config import Settings


class FakeProjectionAdapter:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def remember_text(
        self,
        text: str,
        *,
        dataset_name: str,
        node_set: list[str] | None = None,
        settings: Settings | None = None,
    ) -> dict[str, str]:
        del settings
        self.calls.append(
            {
                "text": text,
                "dataset_name": dataset_name,
                "node_set": node_set or [],
            }
        )
        return {"id": f"fake-{len(self.calls)}"}


def test_review_recent_returns_recent_ingestion_memory_and_conflicts(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    receipt = remember(RememberRequest(input="Sam likes Bill Evans."), settings)

    review = review_recent(settings)

    assert review["ingestion_runs"][0]["id"] == receipt.ingestion_run_id
    assert review["memory_cards"][0]["id"] == receipt.memory_cards[0].id
    assert review["sources"] == []
    assert review["conflicts"] == []


def test_undo_last_soft_deletes_ingestion_objects_and_hides_recall(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    receipt = remember(RememberRequest(input="Sam likes Bill Evans."), settings)

    result = undo_last(settings)

    store = BrainStore(settings)
    assert result["status"] == "undone"
    assert result["deleted_memories"] == [receipt.memory_cards[0].id]
    assert store.get_memory(receipt.memory_cards[0].id)["status"] == "deleted"
    assert store.get_cognee_sync(receipt.memory_cards[0].id)[0]["status"] == "stale"
    assert recall(RecallRequest(query="Bill Evans"), settings).facts == []


def test_sync_cognee_syncs_one_memory_with_fake_adapter(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    receipt = remember(RememberRequest(input="Sam likes Bill Evans."), settings)
    adapter = FakeProjectionAdapter()

    result = sync_cognee(
        settings,
        object_type="memory",
        object_id=receipt.memory_cards[0].id,
        adapter=adapter,
    )

    row = BrainStore(settings).get_cognee_sync(receipt.memory_cards[0].id)[0]
    assert result["succeeded"] == 1
    assert row["status"] == "synced"
    assert adapter.calls[0]["dataset_name"] == "memory"


def test_rebuild_cognee_prune_requires_confirmation(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    remember(RememberRequest(input="Sam likes Bill Evans."), settings)

    with pytest.raises(ValueError, match="confirm=true"):
        rebuild_cognee(settings, prune_first=True)

    result = rebuild_cognee(settings, prune_first=True, confirm=True)

    assert result["pruned"] is True
    assert result["memory_rows_marked_stale"] == 1


def test_merge_entities_requires_confirmation_and_repoints_profile(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    sam = remember(RememberRequest(input="Sam likes Bill Evans."), settings)
    samuel = remember(RememberRequest(input="Samuel likes Sonny Rollins."), settings)
    primary = next(entity for entity in sam.entities if entity.canonical_name == "Sam")
    duplicate = next(entity for entity in samuel.entities if entity.canonical_name == "Samuel")

    with pytest.raises(ValueError, match="confirm=true"):
        merge_entities(
            settings,
            primary_entity_id=primary.id,
            duplicate_entity_id=duplicate.id,
        )

    result = merge_entities(
        settings,
        primary_entity_id=primary.id,
        duplicate_entity_id=duplicate.id,
        reason="same person",
        confirm=True,
    )

    store = BrainStore(settings)
    duplicate_entity = store.get_entity(duplicate.id)
    profile = profile_entity(settings, name="Sam")
    aliases = {alias["alias"] for alias in store.get_entity(primary.id)["aliases"]}
    assert result["status"] == "merged"
    assert duplicate_entity["status"] == "archived"
    assert duplicate_entity["metadata_json"]["merged_into"] == primary.id
    assert "Samuel" in aliases
    assert "Sonny Rollins" in profile.answer


def brain_test_settings(tmp_path) -> Settings:
    return Settings(brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}")
