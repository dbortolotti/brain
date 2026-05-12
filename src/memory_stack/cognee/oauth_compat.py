from __future__ import annotations

import asyncio
import importlib
import json
import os
from typing import Any

import httpx
from pydantic import BaseModel

from memory_stack.config import Settings
from memory_stack.provider_auth import resolve_openai_text_bearer


JSON_OBJECT_RE = r"\{.*\}"


class CogneeOAuthCompatError(RuntimeError):
    pass


def cognee_oauth_compat_enabled(settings: Settings) -> bool:
    return settings.llm_provider == "openai" and settings.openai_auth_mode == "oauth"


def configure_cognee_oauth_environment(settings: Settings) -> dict[str, str]:
    if not cognee_oauth_compat_enabled(settings):
        return {}

    bearer = resolve_openai_text_bearer(settings)
    values = {
        "LLM_PROVIDER": "openai",
        "LLM_MODEL": settings.llm_model,
        "LLM_API_KEY": bearer,
        "LLM_ENDPOINT": settings.openai_codex_base_url.rstrip("/"),
    }
    if settings.embedding_provider == "openai":
        values.update(
            {
                "EMBEDDING_PROVIDER": "openai",
                "EMBEDDING_MODEL": f"openai/{settings.embedding_model}",
                "EMBEDDING_DIMENSIONS": str(settings.embedding_dimensions),
                "EMBEDDING_API_KEY": bearer,
            }
        )
    os.environ.update(values)
    return values


def install_cognee_oauth_llm_adapter(settings: Settings) -> bool:
    if not cognee_oauth_compat_enabled(settings):
        return False

    try:
        llm_config_module = importlib.import_module("cognee.infrastructure.llm.config")
        client_module = importlib.import_module(
            "cognee.infrastructure.llm.structured_output_framework.litellm_instructor.llm.get_llm_client"
        )
    except Exception as exc:
        raise CogneeOAuthCompatError("Could not install Cognee OAuth LLM compatibility layer.") from exc

    if hasattr(llm_config_module.get_llm_config, "cache_clear"):
        llm_config_module.get_llm_config.cache_clear()
    cached_factory = getattr(client_module, "_get_llm_client_cached", None)
    if cached_factory is not None and hasattr(cached_factory, "cache_clear"):
        cached_factory.cache_clear()

    client_module.get_llm_client = lambda raise_api_key_error=True: CogneeOAuthLLMAdapter(settings)
    return True


def prepare_cognee_oauth_runtime(settings: Settings) -> bool:
    configure_cognee_oauth_environment(settings)
    return install_cognee_oauth_llm_adapter(settings)


class CogneeOAuthLLMAdapter:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.model = settings.llm_model
        self.endpoint = settings.openai_codex_base_url.rstrip("/")
        self.max_completion_tokens = settings.llm_max_tokens

    async def acreate_structured_output(
        self,
        text_input: str,
        system_prompt: str,
        response_model: type[BaseModel] | type[str],
        **kwargs: Any,
    ) -> BaseModel | str:
        del kwargs
        prompt = _prompt_for_response_model(text_input, response_model)
        payload: dict[str, Any] = {
            "model": self.model,
            "instructions": system_prompt,
            "input": [{"role": "user", "content": prompt}],
            "store": False,
            "stream": True,
            "reasoning": {"effort": _openai_reasoning_effort(self.model)},
        }
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.endpoint}/responses",
                headers={"Authorization": f"Bearer {resolve_openai_text_bearer(self.settings)}"},
                json=payload,
            )
        text = _openai_stream_response_text(response)
        if not text:
            raise CogneeOAuthCompatError("OpenAI OAuth response did not include text.")
        if response_model is str:
            return text.strip()
        return response_model.model_validate(_parse_json_object(text))

    def create_structured_output(
        self,
        text_input: str,
        system_prompt: str,
        response_model: type[BaseModel] | type[str],
        **kwargs: Any,
    ) -> BaseModel | str:
        return asyncio.run(
            self.acreate_structured_output(
                text_input=text_input,
                system_prompt=system_prompt,
                response_model=response_model,
                **kwargs,
            )
        )

    async def create_transcript(self, input: Any, **kwargs: Any) -> Any:
        del input, kwargs
        raise CogneeOAuthCompatError("Cognee OAuth compatibility layer does not support transcription.")

    async def transcribe_image(self, input: Any, **kwargs: Any) -> Any:
        del input, kwargs
        raise CogneeOAuthCompatError("Cognee OAuth compatibility layer does not support image transcription.")


def _parse_json_object(raw_text: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw_text)
    except ValueError:
        import re

        match = re.search(JSON_OBJECT_RE, raw_text, re.DOTALL)
        if not match:
            raise CogneeOAuthCompatError("Model output did not contain a JSON object.")
        payload = json.loads(match.group(0))
    if not isinstance(payload, dict):
        raise CogneeOAuthCompatError("Model output JSON was not an object.")
    return payload


def _prompt_for_response_model(
    text_input: str,
    response_model: type[BaseModel] | type[str],
) -> str:
    if response_model is str:
        return text_input
    schema = response_model.model_json_schema()
    return "\n".join(
        [
            text_input,
            "Return only one JSON object. Do not wrap it in Markdown.",
            "JSON schema:",
            json.dumps(schema, separators=(",", ":")),
        ]
    )


def _openai_reasoning_effort(model: str) -> str:
    if model.startswith(("gpt-5.4", "gpt-5.5")):
        return "low"
    return "minimal"


def _openai_stream_response_text(response: httpx.Response) -> str | None:
    if response.status_code >= 400:
        raise CogneeOAuthCompatError(f"OpenAI OAuth request failed: HTTP {response.status_code}.")
    chunks: list[str] = []
    final_text: str | None = None
    for line in response.text.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        data = line.removeprefix("data:").strip()
        if not data or data == "[DONE]":
            continue
        try:
            event = json.loads(data)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        event_type = str(event.get("type") or "")
        if event_type in {"response.output_text.delta", "response.refusal.delta"} and isinstance(
            event.get("delta"), str
        ):
            chunks.append(event["delta"])
        elif event_type == "response.completed" and isinstance(event.get("response"), dict):
            final_text = _openai_response_text(event["response"])
        elif isinstance(event.get("output_text"), str):
            final_text = event["output_text"]
    if chunks:
        return "".join(chunks)
    if final_text:
        return final_text
    try:
        return _openai_response_text(response.json())
    except ValueError:
        return None


def _openai_response_text(payload: dict[str, Any]) -> str | None:
    text = payload.get("output_text")
    if isinstance(text, str) and text.strip():
        return text
    chunks: list[str] = []
    for item in payload.get("output") or []:
        if not isinstance(item, dict):
            continue
        for content in item.get("content") or []:
            if isinstance(content, dict) and content.get("type") in {"output_text", "text"}:
                if content.get("text"):
                    chunks.append(str(content["text"]))
    return "\n".join(chunks) if chunks else None
