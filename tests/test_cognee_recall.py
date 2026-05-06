from __future__ import annotations

from typing import Any

from memory_stack.brain_models import RecallRequest, RememberRequest
from memory_stack.brain_service import profile_entity, recall, remember
from memory_stack.brain_store import BrainStore
from memory_stack.config import Settings


class FakeCogneeSearch:
    def __init__(self, result: Any = None, *, fail: bool = False) -> None:
        self.result = result
        self.fail = fail

    def search(
        self,
        query: str,
        *,
        dataset: str,
        top_k: int,
        settings: Settings,
    ) -> Any:
        del query, dataset, top_k, settings
        if self.fail:
            raise RuntimeError("cognee recall unavailable")
        return self.result


def test_profile_entity_includes_db_facts(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    remember(
        RememberRequest(input="Sam from Goldman mentioned that he likes Bill Evans."),
        settings,
    )

    profile = profile_entity(settings, name="Sam from Goldman")

    assert "likes Bill Evans" in profile.answer
    assert profile.facts[0]["kind"] == "person_interaction"


def test_recall_knowledge_graphs_returns_open_question(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    remember(RememberRequest(input="I want to learn more about knowledge graphs."), settings)

    response = recall(RecallRequest(query="knowledge graphs"), settings)

    assert any(fact["kind"] == "open_question" for fact in response.facts)
    assert "knowledge graphs" in response.answer


def test_deleted_and_superseded_memories_are_hidden_by_default_from_cognee_hydration(tmp_path) -> None:
    settings = brain_test_settings(tmp_path, brain_cognee_recall_enabled=True)
    receipt = remember(RememberRequest(input="Sam likes Bill Evans."), settings)
    store = BrainStore(settings)
    store.update_memory_status(receipt.memory_cards[0].id, "superseded")
    fake = FakeCogneeSearch(result=f"memory_id: {receipt.memory_cards[0].id}")

    response = recall(RecallRequest(query="jazz"), settings, cognee_searcher=fake)

    assert response.facts == []


def test_fake_cognee_result_memory_id_is_hydrated_from_brain_db(tmp_path) -> None:
    settings = brain_test_settings(tmp_path, brain_cognee_recall_enabled=True)
    receipt = remember(RememberRequest(input="Sam likes Bill Evans."), settings)
    fake = FakeCogneeSearch(result=[{"text": f"memory_id: {receipt.memory_cards[0].id}"}])

    response = recall(RecallRequest(query="jazz"), settings, cognee_searcher=fake)

    assert [fact["memory_id"] for fact in response.facts] == [receipt.memory_cards[0].id]
    assert "Sam likes Bill Evans" in response.answer


def test_cognee_unavailable_does_not_break_db_recall(tmp_path) -> None:
    settings = brain_test_settings(tmp_path, brain_cognee_recall_enabled=True)
    remember(RememberRequest(input="Knowledge graphs matter for Brain."), settings)
    fake = FakeCogneeSearch(fail=True)

    response = recall(RecallRequest(query="knowledge graphs"), settings, cognee_searcher=fake)

    assert "Knowledge graphs matter for Brain" in response.answer


def brain_test_settings(tmp_path, **overrides: Any) -> Settings:
    return Settings(brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}", **overrides)
