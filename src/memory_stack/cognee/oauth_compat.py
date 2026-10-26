from __future__ import annotations

import asyncio
import concurrent.futures
import importlib
import json
import os
import random
from typing import Any, Coroutine, TypeVar

import httpx
from pydantic import BaseModel

from memory_stack.cfg import Settings
from memory_stack.provider_auth import (
    openai_embeddings_base_url,
    openai_responses_base_url,
    resolve_openai_text_bearer,
)

T = TypeVar("T")


JSON_OBJECT_RE = r"\{.*\}"
# One JSON value embedded in prose: an object or an array.
JSON_VALUE_RE = r"[\{\[].*[\}\]]"


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
        "LLM_ENDPOINT": openai_responses_base_url(settings),
    }
    if settings.embedding_provider == "openai":
        values.update(
            {
                "EMBEDDING_PROVIDER": "openai",
                "EMBEDDING_MODEL": f"openai/{settings.embedding_model}",
                "EMBEDDING_DIMENSIONS": str(settings.embedding_dimensions),
                "EMBEDDING_API_KEY": bearer,
                "EMBEDDING_ENDPOINT": openai_embeddings_base_url(settings),
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
        self.endpoint = openai_responses_base_url(settings)
        self.max_completion_tokens = settings.llm_max_tokens

    async def acreate_structured_output(
        self,
        text_input: str,
        system_prompt: str,
        response_model: type[BaseModel] | type[str],
        **kwargs: Any,
    ) -> BaseModel | str:
        prompt = _prompt_for_response_model(text_input, response_model)
        model = str(kwargs.get("model") or self.model)
        payload: dict[str, Any] = {
            "model": model,
            "instructions": system_prompt,
            "input": [{"role": "user", "content": prompt}],
            "store": False,
            "stream": True,
        }
        for key in ("tools", "tool_choice", "include"):
            if key in kwargs:
                payload[key] = kwargs[key]
        if _openai_supports_reasoning(model):
            payload["reasoning"] = {
                "effort": _openai_reasoning_effort(
                    model,
                    configured=kwargs.get("reasoning_effort"),
                )
            }
        text = None
        last_transport_error: httpx.TransportError | None = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=120) as client:
                    response = await client.post(
                        f"{self.endpoint}/responses",
                        headers={"Authorization": f"Bearer {resolve_openai_text_bearer(self.settings)}"},
                        json=payload,
                    )
                text = _openai_stream_response_text(response)
            except httpx.TransportError as exc:
                last_transport_error = exc
                text = None
            if text:
                break
            if attempt < 2:
                await asyncio.sleep(0.5 * (attempt + 1) + random.random() * 0.25)
        if not text:
            if last_transport_error is not None:
                raise CogneeOAuthCompatError(
                    "OpenAI OAuth request failed after transport retries."
                ) from last_transport_error
            raise CogneeOAuthCompatError("OpenAI OAuth response did not include text.")
        if response_model is str:
            return text.strip()
        payload = coerce_payload_for_model(_parse_json_value(text), response_model)
        return response_model.model_validate(payload)

    def create_structured_output(
        self,
        text_input: str,
        system_prompt: str,
        response_model: type[BaseModel] | type[str],
        **kwargs: Any,
    ) -> BaseModel | str:
        """Synchronous bridge for callers that are not coroutines.

        Palate enrichment (`ConfiguredLLMClient.complete_json`) is synchronous
        but runs inside the MCP server's event loop. `asyncio.run` refuses to
        start a loop from a running one, so the coroutine was created and never
        awaited and every live enrichment failed with "asyncio.run() cannot be
        called from a running event loop" (prod journal, 2026-10-15 onwards;
        `brain_palate_describe_item` returned `enrichment: null`). When a loop
        is already running in this thread, run the coroutine to completion on
        a private loop in a worker thread instead.
        """
        coroutine = self.acreate_structured_output(
            text_input=text_input,
            system_prompt=system_prompt,
            response_model=response_model,
            **kwargs,
        )
        return run_coroutine_blocking(coroutine)

    async def create_transcript(self, input: Any, **kwargs: Any) -> Any:
        del input, kwargs
        raise CogneeOAuthCompatError("Cognee OAuth compatibility layer does not support transcription.")

    async def transcribe_image(self, input: Any, **kwargs: Any) -> Any:
        del input, kwargs
        raise CogneeOAuthCompatError("Cognee OAuth compatibility layer does not support image transcription.")


def run_coroutine_blocking(coroutine: Coroutine[Any, Any, T]) -> T:
    """Run `coroutine` to completion from synchronous code.

    Outside any event loop this is plain `asyncio.run`. Inside a running loop
    (the MCP server, a notebook) it hands the coroutine to a one-off worker
    thread with its own loop and blocks on the result, so synchronous callers
    behave the same wherever they are invoked from.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coroutine)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coroutine).result()


def _parse_json_value(raw_text: str) -> Any:
    """Parse the model's reply as JSON, tolerating prose around one value."""
    try:
        return json.loads(raw_text)
    except ValueError:
        import re

        match = re.search(JSON_VALUE_RE, raw_text, re.DOTALL)
        if not match:
            raise CogneeOAuthCompatError("Model output did not contain a JSON object.")
        return json.loads(match.group(0))


def _parse_json_object(raw_text: str) -> dict[str, Any]:
    payload = _parse_json_value(raw_text)
    if not isinstance(payload, dict):
        raise CogneeOAuthCompatError("Model output JSON was not an object.")
    return payload


def _list_fields(response_model: type[BaseModel]) -> list[str]:
    import typing

    names: list[str] = []
    for name, field in response_model.model_fields.items():
        annotation = field.annotation
        origin = typing.get_origin(annotation)
        if origin is list or annotation is list:
            names.append(name)
            continue
        if origin is typing.Union or str(origin) == "types.UnionType":
            if any(typing.get_origin(a) is list or a is list for a in typing.get_args(annotation)):
                names.append(name)
    return names


def coerce_payload_for_model(payload: Any, response_model: type[BaseModel]) -> dict[str, Any]:
    """Accept a bare JSON array for a model that is just a wrapper around one list.

    Cognee asks for ``EventList`` / ``EventEntityList`` (``{"events": [...]}``)
    and gpt-6.1-sol regularly answers with the array itself, which failed
    every temporal extraction task on 2026-10-26 ("Model output JSON was
    not an object"). When the model has exactly one list-typed field and
    every other field is optional, the array is that field. Anything else
    stays a hard error so a genuinely wrong shape is not papered over.
    """
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, list):
        list_fields = _list_fields(response_model)
        others = [
            name
            for name, field in response_model.model_fields.items()
            if name not in list_fields and field.is_required()
        ]
        if len(list_fields) == 1 and not others:
            return {list_fields[0]: payload}
    raise CogneeOAuthCompatError("Model output JSON was not an object.")


def _prompt_for_response_model(
    text_input: str,
    response_model: type[BaseModel] | type[str],
) -> str:
    if response_model is str:
        return text_input
    schema = response_model.model_json_schema()
    top_level = ", ".join(response_model.model_fields) or "(none)"
    return "\n".join(
        [
            text_input,
            "Return only one JSON object. Do not wrap it in Markdown.",
            f"The top-level value must be an object with the key(s): {top_level}.",
            "JSON schema:",
            json.dumps(schema, separators=(",", ":")),
        ]
    )


def _openai_reasoning_effort(model: str, configured: Any = None) -> str:
    configured = configured or os.environ.get("COGNEE_OPENAI_REASONING_EFFORT")
    if configured in {"minimal", "low", "medium", "high"}:
        return configured
    if model.startswith(_LOW_EFFORT_MODEL_PREFIXES):
        return "low"
    return "minimal"


# Models that reject reasoning effort "minimal" on the Codex ChatGPT backend
# (2026-10-25: gpt-6-luna / gpt-6.1-sol / gpt-5.6-* answer HTTP 400
# "Unsupported value: 'minimal'", supported values low..max). "low" is the
# cheapest level every current model accepts.
_LOW_EFFORT_MODEL_PREFIXES = ("gpt-5.4", "gpt-5.5", "gpt-5.6", "gpt-6", "gpt-daybreak")


def _openai_supports_reasoning(model: str) -> bool:
    return model.startswith(("gpt-5", "gpt-6", "gpt-daybreak", "o1", "o3", "o4"))


def _openai_stream_response_text(response: httpx.Response) -> str | None:
    if response.status_code >= 400:
        raise _openai_http_error(response)
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
        elif event_type == "response.output_item.done" and isinstance(event.get("item"), dict):
            final_text = _openai_response_text(event["item"])
        elif event_type == "response.content_part.done" and isinstance(event.get("part"), dict):
            final_text = _openai_response_text(event["part"])
        elif isinstance(event.get("output_text"), str):
            final_text = event["output_text"]
    if chunks:
        return "".join(chunks)
    if final_text:
        return final_text
    try:
        return _openai_response_payload_text(response)
    except ValueError:
        return None


def _openai_response_payload_text(response: httpx.Response) -> str | None:
    if response.status_code >= 400:
        raise _openai_http_error(response)
    return _openai_response_text(response.json())


def _openai_http_error(response: httpx.Response) -> CogneeOAuthCompatError:
    detail = response.text[:500].replace("\n", " ").strip()
    suffix = f" Body: {detail}" if detail else ""
    return CogneeOAuthCompatError(f"OpenAI OAuth request failed: HTTP {response.status_code}.{suffix}")


def _openai_response_text(payload: dict[str, Any]) -> str | None:
    text = payload.get("output_text")
    if isinstance(text, str) and text.strip():
        return text
    chunks: list[str] = []
    for content in payload.get("content") or []:
        if isinstance(content, dict) and content.get("type") in {"output_text", "text"}:
            if content.get("text"):
                chunks.append(str(content["text"]))
    for item in payload.get("output") or []:
        if not isinstance(item, dict):
            continue
        for content in item.get("content") or []:
            if isinstance(content, dict) and content.get("type") in {"output_text", "text"}:
                if content.get("text"):
                    chunks.append(str(content["text"]))
    return "\n".join(chunks) if chunks else None
