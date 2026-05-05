from __future__ import annotations

from memory_stack.brain_models import RecallRequest, RememberRequest
from memory_stack.brain_service import list_open_loops, profile_entity, recall, remember
from memory_stack.config import Settings


def test_family_fact_creates_single_card_entities_and_relationships(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)

    receipt = remember(RememberRequest(input="Nur and Sara are my twin daughters."), settings)

    assert receipt.classification == "family_fact"
    assert len(receipt.memory_cards) == 1
    assert receipt.memory_cards[0].kind == "family_fact"
    assert receipt.memory_cards[0].statement == "Nur and Sara are Daniele's twin daughters."
    assert {entity.canonical_name for entity in receipt.entities} == {"Daniele", "Nur", "Sara"}
    assert {
        (relationship["predicate"], relationship["confidence"])
        for relationship in receipt.relationships
    } == {
        ("daughter_of", "high"),
        ("twin_of", "high"),
    }

    answer = recall(RecallRequest(query="Who are my daughters?"), settings)
    assert "Nur and Sara are Daniele's twin daughters" in answer.answer


def test_person_interaction_profile_is_entity_centric(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)

    receipt = remember(
        RememberRequest(input="Sam from Goldman mentioned that he likes Bill Evans."),
        settings,
    )

    assert receipt.classification == "person_interaction"
    assert {entity.canonical_name for entity in receipt.entities} == {
        "Sam from Goldman",
        "Goldman",
        "Bill Evans",
    }
    assert {relationship["predicate"] for relationship in receipt.relationships} == {
        "associated_with",
        "likes",
    }

    profile = profile_entity(settings, name="Sam from Goldman")
    assert "Sam from Goldman" in profile.answer
    assert "Sam" in profile.answer
    assert "associated_with Goldman" in profile.answer
    assert "likes Bill Evans" in profile.answer


def test_open_question_creates_open_loop(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)

    receipt = remember(
        RememberRequest(input="I want to learn more about knowledge graphs."),
        settings,
    )

    assert receipt.classification == "open_question"
    assert receipt.open_loops[0]["status"] == "open"
    assert receipt.memory_cards[0].statement == "Daniele wants to learn more about knowledge graphs."

    loops = list_open_loops(settings, topic="knowledge graphs")
    assert len(loops) == 1
    assert loops[0]["topics"] == ["knowledge_graphs"]
    assert "knowledge graphs" in loops[0]["statement"]


def brain_test_settings(tmp_path) -> Settings:
    return Settings(brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}")
