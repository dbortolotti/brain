from __future__ import annotations

from typing import Any, Protocol

from memory_stack.config import Settings, load_settings
from memory_stack.slack.commands import SlackBrainService, execute_slack_command


class SlackResponder(Protocol):
    def respond(self, response_url: str | None, payload: dict[str, Any]) -> None:
        ...


class SlackCommandApp:
    def __init__(
        self,
        *,
        settings: Settings | None = None,
        responder: SlackResponder | None = None,
        service: SlackBrainService | None = None,
    ) -> None:
        self.settings = settings or load_settings()
        self.responder = responder
        self.service = service

    def handle_command(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.brain_slack_enabled:
            response = {
                "response_type": "ephemeral",
                "text": "Slack capture is disabled. Set BRAIN_SLACK_ENABLED=true to enable it.",
                "payload": {"status": "disabled"},
            }
        else:
            response = execute_slack_command(
                str(payload.get("text") or ""),
                settings=self.settings,
                service=self.service,
            )
        if self.responder is not None:
            self.responder.respond(payload.get("response_url"), response)
        return response
