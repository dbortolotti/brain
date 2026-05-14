from __future__ import annotations

import json
from typing import Any, Protocol

import httpx

from memory_stack.cognee.oauth_compat import CogneeOAuthLLMAdapter
from memory_stack.cfg import Settings
from memory_stack.provider_auth import resolve_openai_text_bearer


class LLMClient(Protocol):
    def complete_json(self, prompt: str, schema: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Return JSON that conforms to the requested schema."""


class ConfiguredLLMClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def complete_json(self, prompt: str, schema: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        if self.settings.llm_provider != "openai":
            raise RuntimeError(f"Unsupported Brain LLM provider: {self.settings.llm_provider}")

        model = str(kwargs.get("model") or self.settings.llm_model)
        if self.settings.openai_auth_mode == "oauth":
            return self._complete_json_with_cognee_oauth(prompt, schema, **kwargs)

        payload: dict[str, Any] = {
            "model": model,
            "instructions": "Return only one JSON object matching the requested schema.",
            "input": [{"role": "user", "content": prompt}],
            "store": False,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": str(kwargs.get("schema_name") or "brain_json_response"),
                    "strict": True,
                    "schema": schema,
                }
            },
        }
        endpoint = self.settings.llm_endpoint or "https://api.openai.com/v1"
        bearer = resolve_openai_text_bearer(self.settings)
        for key in ("tools", "tool_choice", "include"):
            if key in kwargs:
                payload[key] = kwargs[key]
        reasoning_effort = kwargs.get("reasoning_effort")
        if reasoning_effort:
            payload["reasoning"] = {"effort": str(reasoning_effort)}
        if max_tokens := kwargs.get("max_output_tokens", self.settings.llm_max_tokens):
            payload["max_output_tokens"] = max_tokens
        with httpx.Client(timeout=60) as client:
            response = client.post(
                f"{endpoint.rstrip('/')}/responses",
                headers={"Authorization": f"Bearer {bearer}"},
                json=payload,
            )
        if response.status_code >= 400:
            raise RuntimeError(
                f"OpenAI Responses request failed: HTTP {response.status_code}: {response.text}"
            )
        text = openai_response_text(response.json())
        if not text:
            raise RuntimeError("OpenAI Responses request did not return text.")
        return json.loads(text)

    def _complete_json_with_cognee_oauth(
        self,
        prompt: str,
        schema: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        adapter = CogneeOAuthLLMAdapter(self.settings)
        text = adapter.create_structured_output(
            text_input=prompt_with_schema(prompt, schema),
            system_prompt="Return only one JSON object matching the requested schema.",
            response_model=str,
            **{
                key: kwargs[key]
                for key in ("model", "reasoning_effort", "tools", "tool_choice", "include")
                if key in kwargs
            },
        )
        return json.loads(str(text))


def prompt_with_schema(prompt: str, schema: dict[str, Any]) -> str:
    return "\n".join(
        [
            prompt,
            "Return only one JSON object. Do not wrap it in Markdown.",
            "JSON schema:",
            json.dumps(schema, separators=(",", ":")),
        ]
    )


def openai_response_text(payload: dict[str, Any]) -> str:
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]
    chunks: list[str] = []
    for item in payload.get("output") or []:
        for content in item.get("content") or []:
            if content.get("type") in {"output_text", "text"} and isinstance(
                content.get("text"),
                str,
            ):
                chunks.append(content["text"])
    if chunks:
        return "\n".join(chunks)
    message = payload.get("message")
    if isinstance(message, dict) and isinstance(message.get("content"), str):
        return message["content"]
    return ""


def build_llm_client(settings: Settings) -> LLMClient | None:
    if not settings.brain_llm_enabled:
        return None
    return ConfiguredLLMClient(settings)
