from __future__ import annotations

from memory_stack.brain_models import (
    EntityReceipt,
    IngestionReceipt,
    MemoryReceipt,
    RecallResponse,
)
from memory_stack.config import Settings
from memory_stack.slack.app import SlackCommandApp
from memory_stack.slack.commands import execute_slack_command, parse_slack_command


class FakeBrainService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def remember(self, text: str) -> IngestionReceipt:
        self.calls.append(("remember", text))
        return IngestionReceipt(
            ingestion_run_id="ing_1",
            classification="basic_fact",
            memory_cards=[
                MemoryReceipt(
                    id="mem_1",
                    kind="basic_fact",
                    statement=text,
                    status="current",
                )
            ],
            entities=[EntityReceipt(id="ent_1", canonical_name="Sam", type="person")],
        )

    def article(self, url: str, why_saved: str | None = None) -> IngestionReceipt:
        self.calls.append(("article", (url, why_saved)))
        return IngestionReceipt(
            ingestion_run_id="ing_2",
            classification="article_url",
            memory_cards=[
                MemoryReceipt(
                    id="mem_2",
                    kind="article_note",
                    statement=f"Saved article for later recall: {url}",
                    status="current",
                )
            ],
        )

    def transcript(self, text: str) -> IngestionReceipt:
        self.calls.append(("transcript", text))
        return IngestionReceipt(
            ingestion_run_id="ing_3",
            classification="transcript",
            memory_cards=[
                MemoryReceipt(
                    id="mem_3",
                    kind="source_summary",
                    statement=text[:50],
                    status="current",
                )
            ],
        )

    def recall(self, query: str) -> RecallResponse:
        self.calls.append(("recall", query))
        return RecallResponse(answer=f"Known memories\n- {query}")

    def profile(self, name: str) -> RecallResponse:
        self.calls.append(("profile", name))
        return RecallResponse(answer=f"{name}\nIdentity")

    def open_loops(self) -> list[dict[str, object]]:
        self.calls.append(("open", None))
        return [{"memory_id": "mem_open", "statement": "Learn knowledge graphs."}]

    def review(self) -> dict[str, object]:
        self.calls.append(("review", None))
        return {"ingestion_runs": [{}], "memory_cards": [{}], "sources": [], "conflicts": []}

    def undo_last(self) -> dict[str, object]:
        self.calls.append(("undo_last", None))
        return {"status": "undone", "deleted_memories": ["mem_1"], "deleted_sources": []}


class FakeResponder:
    def __init__(self) -> None:
        self.responses: list[tuple[str | None, dict[str, object]]] = []

    def respond(self, response_url: str | None, payload: dict[str, object]) -> None:
        self.responses.append((response_url, payload))


def test_parse_slack_command_normalizes_brain_prefix() -> None:
    command = parse_slack_command("/brain undo-last")

    assert command.action == "undo_last"
    assert command.text == ""


def test_slack_remember_calls_brain_service_and_formats_receipt() -> None:
    service = FakeBrainService()
    response = execute_slack_command(
        "/brain remember Sam likes Bill Evans.",
        settings=Settings(),
        service=service,
    )

    assert service.calls == [("remember", "Sam likes Bill Evans.")]
    assert "Stored 1 memories" in response["text"]
    assert "memory_id: mem_1" in response["text"]
    assert "confidence: medium" in response["text"]
    assert "Entities created/updated" in response["text"]
    assert "Actions: Inspect | Undo | Mark wrong" in response["text"]


def test_slack_article_recall_review_and_undo_delegate_to_service() -> None:
    service = FakeBrainService()

    execute_slack_command(
        "/brain article https://example.com Useful for AI memory.",
        settings=Settings(),
        service=service,
    )
    execute_slack_command("/brain recall knowledge graphs", settings=Settings(), service=service)
    execute_slack_command("/brain review", settings=Settings(), service=service)
    execute_slack_command("/brain undo-last", settings=Settings(), service=service)

    assert service.calls == [
        ("article", ("https://example.com", "Useful for AI memory.")),
        ("recall", "knowledge graphs"),
        ("review", None),
        ("undo_last", None),
    ]


def test_slack_app_uses_mocked_responder_when_enabled() -> None:
    responder = FakeResponder()
    service = FakeBrainService()
    settings = Settings(brain_slack_enabled=True)
    app = SlackCommandApp(settings=settings, responder=responder, service=service)

    response = app.handle_command(
        {"text": "remember Sam likes Bill Evans.", "response_url": "https://slack.test/response"}
    )

    assert response["payload"].ingestion_run_id == "ing_1"
    assert responder.responses[0][0] == "https://slack.test/response"
    assert service.calls[0][0] == "remember"


def test_slack_app_disabled_by_default_and_does_not_call_service() -> None:
    responder = FakeResponder()
    service = FakeBrainService()
    app = SlackCommandApp(settings=Settings(), responder=responder, service=service)

    response = app.handle_command({"text": "remember Sam likes Bill Evans."})

    assert response["payload"]["status"] == "disabled"
    assert service.calls == []
    assert responder.responses[0][1]["payload"]["status"] == "disabled"
