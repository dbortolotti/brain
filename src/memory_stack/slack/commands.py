from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from memory_stack.brain_models import IngestSourceRequest, RecallRequest, RememberRequest
from memory_stack.brain_service import (
    ingest_source,
    list_open_loops,
    profile_entity,
    recall,
    remember,
    review_recent,
    undo_last,
)
from memory_stack.config import Settings
from memory_stack.slack.formatter import (
    format_ingestion_receipt,
    format_open_loops,
    format_recall_response,
    format_review,
    format_undo,
)


@dataclass(frozen=True)
class SlackCommand:
    action: str
    text: str = ""


class SlackBrainService(Protocol):
    def remember(self, text: str) -> Any:
        ...

    def article(self, url: str, why_saved: str | None = None) -> Any:
        ...

    def transcript(self, text: str) -> Any:
        ...

    def recall(self, query: str) -> Any:
        ...

    def profile(self, name: str) -> Any:
        ...

    def open_loops(self) -> list[dict[str, Any]]:
        ...

    def review(self) -> dict[str, Any]:
        ...

    def undo_last(self) -> dict[str, Any]:
        ...


class BrainServiceAdapter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def remember(self, text: str) -> Any:
        return remember(RememberRequest(input=text), self.settings)

    def article(self, url: str, why_saved: str | None = None) -> Any:
        return ingest_source(
            IngestSourceRequest(
                source=url,
                source_kind="article",
                why_saved=why_saved,
            ),
            self.settings,
        )

    def transcript(self, text: str) -> Any:
        return ingest_source(
            IngestSourceRequest(source=text, source_kind="transcript"),
            self.settings,
        )

    def recall(self, query: str) -> Any:
        return recall(RecallRequest(query=query), self.settings)

    def profile(self, name: str) -> Any:
        return profile_entity(self.settings, name=name)

    def open_loops(self) -> list[dict[str, Any]]:
        return list_open_loops(self.settings)

    def review(self) -> dict[str, Any]:
        return review_recent(self.settings)

    def undo_last(self) -> dict[str, Any]:
        return undo_last(self.settings)


def parse_slack_command(text: str) -> SlackCommand:
    stripped = text.strip()
    if stripped.startswith("/brain"):
        stripped = stripped.removeprefix("/brain").strip()
    if not stripped:
        return SlackCommand(action="help")

    action, _, rest = stripped.partition(" ")
    return SlackCommand(action=action.replace("-", "_"), text=rest.strip())


def execute_slack_command(
    command_text: str,
    *,
    settings: Settings,
    service: SlackBrainService | None = None,
) -> dict[str, Any]:
    command = parse_slack_command(command_text)
    active_service = service or BrainServiceAdapter(settings)

    if command.action == "remember":
        _require_text(command, "Usage: /brain remember <text>")
        receipt = active_service.remember(command.text)
        return _message(format_ingestion_receipt(receipt), payload=receipt)

    if command.action == "article":
        _require_text(command, "Usage: /brain article <url> [why]")
        url, why_saved = _split_first(command.text)
        receipt = active_service.article(url, why_saved or None)
        return _message(format_ingestion_receipt(receipt), payload=receipt)

    if command.action == "transcript":
        _require_text(command, "Usage: /brain transcript <text>")
        receipt = active_service.transcript(command.text)
        return _message(format_ingestion_receipt(receipt), payload=receipt)

    if command.action == "recall":
        _require_text(command, "Usage: /brain recall <query>")
        response = active_service.recall(command.text)
        return _message(format_recall_response(response), payload=response)

    if command.action == "profile":
        _require_text(command, "Usage: /brain profile <entity>")
        response = active_service.profile(command.text)
        return _message(format_recall_response(response), payload=response)

    if command.action == "open":
        loops = active_service.open_loops()
        return _message(format_open_loops(loops), payload={"open_loops": loops})

    if command.action == "review":
        review = active_service.review()
        return _message(format_review(review), payload=review)

    if command.action == "undo_last":
        result = active_service.undo_last()
        return _message(format_undo(result), payload=result)

    return _message(
        "Usage: /brain remember|article|transcript|recall|profile|open|review|undo-last",
        payload={"action": "help"},
    )


def _message(text: str, *, payload: Any) -> dict[str, Any]:
    return {"response_type": "ephemeral", "text": text, "payload": payload}


def _require_text(command: SlackCommand, message: str) -> None:
    if not command.text:
        raise ValueError(message)


def _split_first(text: str) -> tuple[str, str]:
    first, _, rest = text.partition(" ")
    return first, rest.strip()
