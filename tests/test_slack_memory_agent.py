from __future__ import annotations

from typing import Any

from memory_stack.brain_models import RememberRequest
from memory_stack.brain_service import remember
from memory_stack.brain_store import BrainStore
from memory_stack.config import Settings
from memory_stack.slack_memory_agent import SlackAgentRequest, SlackMemoryAgent, receipt_text


class FakeLLM:
    def __init__(self, response: Any) -> None:
        self.response = response
        self.prompts: list[str] = []

    def complete_json(
        self,
        prompt: str,
        schema: dict[str, Any],
        *,
        model: str | None = None,
        temperature: float = 0,
    ) -> Any:
        del schema, model, temperature
        self.prompts.append(prompt)
        return self.response


def test_explicit_remember_produces_dry_run_and_writes_nothing(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    agent = SlackMemoryAgent(settings)

    response = agent.handle(slack_request("remember Sam likes Bill Evans."))

    assert response.decision == "dry_run"
    assert response.payload["dry_run"]["dry_run"] is True
    assert response.payload["requires_confirmation"] is True
    assert response.blocks
    assert response.blocks[1]["elements"][0]["text"]["text"] == "Confirm"
    assert BrainStore(settings).search_memory("Bill Evans") == []


def test_confirmation_commits_proposed_memory(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    agent = SlackMemoryAgent(settings)
    first = agent.handle(slack_request("remember Sam likes Bill Evans."))
    proposed = first.payload["proposal"]["proposed_memory"]

    response = agent.handle(
        slack_request(
            "confirm",
            confirmed=True,
            proposed_memory=proposed,
        )
    )

    memories = BrainStore(settings).search_memory("Bill Evans")
    assert response.decision == "commit"
    assert len(memories) == 1
    assert memories[0]["metadata_json"]["slack"]["user_id"] == "U1"
    assert "memory_id:" in response.text
    assert "confidence:" in response.text
    assert "Actions: Inspect | Undo | Mark wrong" in response.text


def test_agent_receipt_text_satisfies_deterministic_contract() -> None:
    text = receipt_text(
        {
            "source": {"source_id": "src_1"},
            "memory_cards": [
                {
                    "id": "mem_1",
                    "kind": "person_interaction",
                    "statement": "Sam likes Bill Evans.",
                    "confidence": "high",
                    "status": "current",
                }
            ],
            "entities": [{"canonical_name": "Sam"}],
            "relationships": [{"predicate": "likes"}],
            "conflicts": [],
        }
    )

    for term in [
        "Stored",
        "Source ID: src_1",
        "person_interaction",
        "memory_id: mem_1",
        "confidence: high",
        "Entities: Sam",
        "Relationships: 1",
        "Inspect",
        "Undo",
        "Mark wrong",
    ]:
        assert term in text


def test_ambiguous_pronoun_asks_clarification_and_writes_nothing(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    agent = SlackMemoryAgent(settings)

    response = agent.handle(slack_request("remember He likes Bill Evans."))

    assert response.decision == "ask"
    assert "subject is unclear" in response.text
    assert BrainStore(settings).search_memory("Bill Evans") == []


def test_contradiction_complains_and_writes_nothing(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    remember(RememberRequest(input="Sam has two children."), settings)
    agent = SlackMemoryAgent(settings)

    response = agent.handle(slack_request("remember Sam has no children."))

    assert response.decision == "complain"
    assert "conflict" in response.text
    assert len(BrainStore(settings).search_memory("children")) == 1


def test_secret_token_content_is_refused(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    agent = SlackMemoryAgent(settings)

    response = agent.handle(slack_request("remember api_key=sk-testtoken123456789"))

    assert response.decision == "complain"
    assert "token/password-shaped" in response.text
    assert BrainStore(settings).search_memory("sk-testtoken") == []


def test_open_loop_phrasing_maps_to_open_question(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    agent = SlackMemoryAgent(settings)

    response = agent.handle(slack_request("remember I want to learn more about knowledge graphs."))

    assert response.decision == "dry_run"
    assert response.payload["proposal"]["proposed_memory"]["input_type"] == "open_question"


def test_correction_requires_confirmation(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    agent = SlackMemoryAgent(
        settings,
        llm_client=FakeLLM(
            {
                "decision": "commit",
                "reason": "Correction",
                "user_message": "Stored.",
                "proposed_memory": {
                    "input": "Actually, Sam likes early Coltrane, not Bill Evans.",
                    "input_type": "auto",
                    "source_policy": "memory_only",
                    "confidence": "high",
                    "entities": ["Sam", "Bill Evans", "early Coltrane"],
                },
                "questions": [],
                "conflicts": [],
                "requires_confirmation": False,
            }
        ),
    )

    response = agent.handle(slack_request("remember Actually, Sam likes early Coltrane, not Bill Evans."))

    assert response.decision == "ask"
    assert response.payload["reason"] == "commit_not_allowed_without_confirmation"


def test_malformed_llm_json_is_rejected(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    agent = SlackMemoryAgent(settings, llm_client=FakeLLM("not json"))

    response = agent.handle(slack_request("remember Sam likes Bill Evans."))

    assert response.decision == "complain"
    assert response.payload["reason"] == "invalid_guardrail_proposal"


def test_llm_bypass_missing_memory_is_rejected(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    agent = SlackMemoryAgent(
        settings,
        llm_client=FakeLLM(
            {
                "decision": "commit",
                "reason": "Bypass",
                "user_message": "Stored.",
                "proposed_memory": None,
                "questions": [],
                "conflicts": [],
                "requires_confirmation": False,
            }
        ),
    )

    response = agent.handle(slack_request("remember Sam likes Bill Evans."))

    assert response.decision == "ask"
    assert response.payload["reason"] == "commit_not_allowed_without_confirmation"


def test_recall_returns_memory_id_and_evidence(tmp_path) -> None:
    settings = brain_test_settings(tmp_path)
    receipt = remember(RememberRequest(input="Sam likes Bill Evans."), settings)
    agent = SlackMemoryAgent(settings)

    response = agent.handle(slack_request("recall Bill Evans"))

    assert response.decision == "recall"
    assert receipt.memory_cards[0].id in response.text
    assert response.payload["facts"][0]["memory_id"] == receipt.memory_cards[0].id


def test_admin_debug_snapshot_is_admin_only(tmp_path) -> None:
    settings = brain_test_settings(tmp_path, brain_slack_admin_user_ids="UADMIN")
    agent = SlackMemoryAgent(settings)

    rejected = agent.handle(slack_request("debug snapshot", user_id="U1"))
    accepted = agent.handle(slack_request("debug snapshot", user_id="UADMIN"))

    assert rejected.payload["status"] == "forbidden"
    assert "counts" in accepted.payload


def slack_request(
    text: str,
    *,
    user_id: str = "U1",
    confirmed: bool = False,
    proposed_memory: dict[str, Any] | None = None,
) -> SlackAgentRequest:
    return SlackAgentRequest(
        text=text,
        user_id=user_id,
        channel_id="C1",
        team_id="T1",
        message_ts="1700000000.0001",
        source="slash_command",
        confirmed=confirmed,
        proposed_memory=proposed_memory,
    )


def brain_test_settings(tmp_path, **overrides: Any) -> Settings:
    return Settings(brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}", **overrides)
