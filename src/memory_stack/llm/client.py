from __future__ import annotations

from typing import Any, Protocol

from memory_stack.config import Settings


class LLMClient(Protocol):
    def complete_json(self, prompt: str, schema: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Return JSON that conforms to the requested schema."""


class ConfiguredLLMClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def complete_json(self, prompt: str, schema: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        del prompt, schema, kwargs
        provider = self.settings.brain_llm_provider or self.settings.llm_provider
        raise RuntimeError(
            f"Brain LLM provider '{provider}' is configured but no real provider client is wired yet."
        )


def build_llm_client(settings: Settings) -> LLMClient | None:
    if not settings.brain_llm_enabled:
        return None
    return ConfiguredLLMClient(settings)
