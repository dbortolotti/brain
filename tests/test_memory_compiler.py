from __future__ import annotations

from memory_stack.brain_models import IngestSourceRequest, RememberRequest
from memory_stack.brain_service import ingest_source, remember
from memory_stack.cfg import Settings
from memory_stack.llm.fake import FakeLLMClient


def test_llm_enabled_uses_llm_even_when_rule_compiler_is_confident(tmp_path) -> None:
    settings = brain_test_settings(tmp_path, brain_llm_enabled=True)
    fake_llm = FakeLLMClient(
        {
            "classification": "family_fact",
            "source": {"should_create": False},
            "memory_cards": [
                {
                    "kind": "family_fact",
                    "statement": "Nur and Sara are Daniele's twin daughters.",
                    "confidence": "high",
                    "entities": [
                        {"name": "Daniele", "type": "person", "role": "parent"},
                        {"name": "Nur", "type": "person", "role": "child"},
                        {"name": "Sara", "type": "person", "role": "child"},
                    ],
                    "relationships": [
                        {"subject": "Nur", "predicate": "daughter_of", "object": "Daniele"},
                        {"subject": "Sara", "predicate": "daughter_of", "object": "Daniele"},
                        {"subject": "Nur", "predicate": "twin_of", "object": "Sara"},
                    ],
                }
            ],
            "possible_conflicts": [],
            "questions_for_user": [],
        }
    )

    receipt = remember(
        RememberRequest(input="Nur and Sara are my twin daughters."),
        settings,
        llm_client=fake_llm,
    )

    assert receipt.classification == "family_fact"
    assert fake_llm.calls


def test_fake_llm_transcript_extracts_multiple_cards(tmp_path) -> None:
    settings = brain_test_settings(tmp_path, brain_llm_enabled=True)
    fake_llm = FakeLLMClient(
        {
            "classification": "transcript",
            "source": {
                "should_create": True,
                "kind": "transcript",
                "title": "Brain design conversation",
                "summary": "Daniele and Sam discussed Brain/Cognee architecture.",
            },
            "memory_cards": [
                {
                    "kind": "decision",
                    "statement": "Brain DB should remain the source of truth.",
                    "summary": "Keep Brain DB authoritative.",
                    "entities": [
                        {"name": "Brain DB", "type": "artifact", "role": "subject"},
                    ],
                    "topics": ["brain", "ai_memory"],
                    "confidence": "high",
                    "source_quote": "Daniele: Brain DB stays source of truth.",
                },
                {
                    "kind": "open_question",
                    "statement": "Daniele wants to research Cognee-backed recall quality.",
                    "summary": "Research Cognee-backed recall quality.",
                    "entities": [
                        {"name": "Cognee", "type": "artifact", "role": "topic"},
                    ],
                    "topics": ["cognee", "recall"],
                    "confidence": "medium",
                },
            ],
            "possible_conflicts": [],
            "questions_for_user": [],
        }
    )
    transcript = "\n".join(
        [
            "Daniele: Brain DB stays source of truth.",
            "Sam: Cognee can be rebuilt from projection.",
            "Daniele: Need to research Cognee-backed recall quality.",
        ]
    )

    receipt = ingest_source(
        IngestSourceRequest(source=transcript, source_kind="transcript"),
        settings,
        llm_client=fake_llm,
    )

    assert receipt.classification == "transcript"
    assert [card.kind for card in receipt.memory_cards] == ["decision", "open_question"]
    assert receipt.open_loops[0]["status"] == "open"
    assert fake_llm.calls
    prompt = fake_llm.calls[0]["prompt"]
    assert "Use the same role contracts that the model eval harness tests." in prompt
    assert "Role markdown from src/memory_stack/agents/roles/source_classifier.md" in prompt
    assert "Role markdown from src/memory_stack/agents/roles/atomic_card_extractor.md" in prompt
    assert "Agent markdown excerpt from src/memory_stack/agents/shared/memory_agent_rules.md#Mission" in prompt


def test_fake_llm_article_extracts_takeaways_and_open_question(tmp_path) -> None:
    settings = brain_test_settings(tmp_path, brain_llm_enabled=True)
    fake_llm = FakeLLMClient(
        {
            "classification": "article",
            "source": {
                "should_create": True,
                "kind": "article",
                "title": "AI memory article",
                "summary": "Article about durable AI memory.",
            },
            "memory_cards": [
                {
                    "kind": "article_note",
                    "statement": "Saved an article about durable AI memory.",
                    "summary": "Article about durable AI memory.",
                    "topics": ["ai_memory"],
                    "confidence": "medium",
                },
                {
                    "kind": "key_takeaway",
                    "statement": "Memory systems need source-backed recall to stay grounded.",
                    "summary": "Source-backed recall improves groundedness.",
                    "topics": ["ai_memory", "recall"],
                    "confidence": "high",
                },
                {
                    "kind": "open_question",
                    "statement": "Daniele wants to compare vector and graph recall quality.",
                    "summary": "Compare vector and graph recall quality.",
                    "topics": ["recall"],
                    "confidence": "medium",
                },
            ],
            "possible_conflicts": [],
            "questions_for_user": [],
        }
    )

    receipt = ingest_source(
        IngestSourceRequest(
            source="# AI Memory\nMemory systems need source-backed recall.",
            source_kind="article",
        ),
        settings,
        llm_client=fake_llm,
    )

    assert [card.kind for card in receipt.memory_cards] == [
        "article_note",
        "key_takeaway",
        "open_question",
    ]
    assert receipt.open_loops[0]["status"] == "open"


def brain_test_settings(tmp_path, **overrides) -> Settings:
    return Settings(
        brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}",
        **overrides,
    )
