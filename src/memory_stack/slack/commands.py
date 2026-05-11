from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from memory_stack.config import Settings
from memory_stack.slack_memory_agent import (
    SlackAgentRequest,
    SlackMemoryAgent,
    normalize_agent_text,
    split_intent,
)


@dataclass(frozen=True)
class SlackCommand:
    action: str
    text: str = ""


def parse_slack_command(text: str) -> SlackCommand:
    """Compatibility wrapper around the canonical SlackMemoryAgent parser."""
    normalized = normalize_agent_text(text)
    if not normalized:
        return SlackCommand(action="help")
    action, argument = split_intent(normalized)
    return SlackCommand(action=action, text=argument)


def execute_slack_command(
    command_text: str,
    *,
    settings: Settings,
    service: Any | None = None,
) -> dict[str, Any]:
    """Execute a Slack command through the canonical SlackMemoryAgent path.

    The service parameter is retained for legacy callers but is intentionally no
    longer used; command behavior must be defined in SlackMemoryAgent only.
    """
    del service
    response = SlackMemoryAgent(settings).handle(
        SlackAgentRequest(
            text=command_text,
            user_id="",
            channel_id="",
            team_id="",
            source="slash_command",
        )
    )
    return response.as_slack_payload()
