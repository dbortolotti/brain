from __future__ import annotations

from typing import Any

from memory_stack.config import Settings
from memory_stack.slack.app import SlackCommandApp
from memory_stack.slack.commands import execute_slack_command, parse_slack_command


class FakeResponder:
    def __init__(self) -> None:
        self.responses: list[tuple[str | None, dict[str, object]]] = []

    def respond(self, response_url: str | None, payload: dict[str, object]) -> None:
        self.responses.append((response_url, payload))


def test_parse_slack_command_delegates_to_canonical_intent_parser() -> None:
    command = parse_slack_command("/brain undo-last")
    empty = parse_slack_command("/brain")
    short_help = parse_slack_command("/brain h")
    natural_recall = parse_slack_command("what do we know about Sam?")

    assert command.action == "undo_last"
    assert command.text == ""
    assert empty.action == "help"
    assert short_help.action == "help"
    assert natural_recall.action == "recall"
    assert natural_recall.text == "what do we know about Sam?"


def test_execute_slack_command_uses_canonical_help(tmp_path) -> None:
    response = execute_slack_command("/brain help", settings=brain_test_settings(tmp_path))

    assert response["payload"]["commands"] == [
        "remember",
        "confirm",
        "recall",
        "profile",
        "open-loops",
        "get-memory",
        "review",
        "undo-last",
        "help",
    ]
    assert "/brain remember <memory>" in response["text"]
    assert "/brain recall <query>" in response["text"]
    assert "/brain help" in response["text"]


def test_execute_slack_command_uses_canonical_memory_agent(tmp_path) -> None:
    response = execute_slack_command(
        "/brain remember Sam likes Bill Evans.",
        settings=brain_test_settings(tmp_path),
    )

    assert response["payload"]["requires_confirmation"] is True
    assert response["payload"]["dry_run"]["dry_run"] is True
    assert response["payload"]["proposal"]["proposed_memory"]["input"] == (
        "Sam likes Bill Evans."
    )


def test_slack_app_uses_canonical_executor_when_enabled(tmp_path) -> None:
    responder = FakeResponder()
    app = SlackCommandApp(
        settings=brain_test_settings(tmp_path, brain_slack_enabled=True),
        responder=responder,
    )

    response = app.handle_command(
        {"text": "help", "response_url": "https://slack.test/response"}
    )

    assert response["payload"]["commands"][0] == "remember"
    assert responder.responses[0][0] == "https://slack.test/response"
    assert responder.responses[0][1]["payload"]["commands"][0] == "remember"


def test_slack_app_disabled_by_default() -> None:
    responder = FakeResponder()
    app = SlackCommandApp(settings=Settings(), responder=responder)

    response = app.handle_command({"text": "remember Sam likes Bill Evans."})

    assert response["payload"]["status"] == "disabled"
    assert responder.responses[0][1]["payload"]["status"] == "disabled"


def brain_test_settings(tmp_path, **overrides: Any) -> Settings:
    return Settings(brain_database_url=f"sqlite:///{tmp_path / 'brain.db'}", **overrides)
