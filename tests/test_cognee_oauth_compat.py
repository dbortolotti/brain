from __future__ import annotations

import asyncio
import json
import os
import sys
import types
from typing import Any

import httpx
import pytest
from pydantic import BaseModel

from memory_stack.cognee import oauth_compat
from memory_stack.cognee_adapter import add_text, remember_text
from memory_stack.cfg import Settings


class SampleResponse(BaseModel):
    answer: str


async def _completed_sleep() -> None:
    return None


@pytest.fixture(autouse=True)
def restore_environment() -> None:
    original = dict(os.environ)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(original)


def test_cognee_oauth_environment_exports_llm_key_without_openai_api_key(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_ENDPOINT", raising=False)
    monkeypatch.delenv("EMBEDDING_ENDPOINT", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(oauth_compat, "resolve_openai_text_bearer", lambda settings: "oauth-token")
    settings = auth_settings(tmp_path)

    values = oauth_compat.configure_cognee_oauth_environment(settings)

    assert values["LLM_API_KEY"] == "oauth-token"
    assert values["LLM_ENDPOINT"] == settings.openai_codex_base_url
    assert values["EMBEDDING_PROVIDER"] == "openai"
    assert values["EMBEDDING_MODEL"] == "openai/text-embedding-3-large"
    assert values["EMBEDDING_DIMENSIONS"] == "3072"
    assert values["EMBEDDING_API_KEY"] == "oauth-token"
    assert values["EMBEDDING_ENDPOINT"] == "https://api.openai.com/v1"
    assert "OPENAI_API_KEY" not in values
    assert "OPENAI_API_KEY" not in os.environ


def test_cognee_oauth_environment_points_embeddings_at_token_sink(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(oauth_compat, "resolve_openai_text_bearer", lambda settings: "sink-token")
    settings = auth_settings(
        tmp_path,
        openai_codex_base_url="http://127.0.0.1:11434/v1",
        openai_token_sink_client_token_file="/etc/hermes/token-sink/client_token",
    )

    values = oauth_compat.configure_cognee_oauth_environment(settings)

    assert values["LLM_API_KEY"] == "sink-token"
    assert values["LLM_ENDPOINT"] == "http://127.0.0.1:11434/v1"
    assert values["EMBEDDING_API_KEY"] == "sink-token"
    assert values["EMBEDDING_ENDPOINT"] == "http://127.0.0.1:11434/v1"


def test_cognee_oauth_adapter_calls_codex_responses_endpoint(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(oauth_compat, "resolve_openai_text_bearer", lambda settings: "oauth-token")
    requests: list[dict[str, Any]] = []

    class FakeAsyncClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            del args, kwargs

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, *args: Any) -> None:
            del args

        async def post(self, url: str, *, headers: dict[str, str], json: dict[str, Any]) -> httpx.Response:
            requests.append({"url": url, "headers": headers, "json": json})
            event = {
                "type": "response.output_text.delta",
                "delta": '{"answer":"ok"}',
            }
            return httpx.Response(200, text=f"data: {json_dumps(event)}\n\ndata: [DONE]\n")

    monkeypatch.setattr(oauth_compat.httpx, "AsyncClient", FakeAsyncClient)
    adapter = oauth_compat.CogneeOAuthLLMAdapter(auth_settings(tmp_path))

    result = asyncio.run(
        adapter.acreate_structured_output(
            text_input="question",
            system_prompt="system",
            response_model=SampleResponse,
        )
    )

    assert result.answer == "ok"
    assert requests[0]["url"].endswith("/responses")
    assert requests[0]["headers"]["Authorization"] == "Bearer oauth-token"
    assert requests[0]["json"]["stream"] is True
    assert "JSON schema:" in requests[0]["json"]["input"][0]["content"]


def test_cognee_oauth_adapter_passes_responses_tool_options(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(oauth_compat, "resolve_openai_text_bearer", lambda settings: "oauth-token")
    requests: list[dict[str, Any]] = []

    class FakeAsyncClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            del args, kwargs

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, *args: Any) -> None:
            del args

        async def post(self, url: str, *, headers: dict[str, str], json: dict[str, Any]) -> httpx.Response:
            del url, headers
            requests.append(json)
            event = {
                "type": "response.output_text.delta",
                "delta": '{"answer":"ok"}',
            }
            return httpx.Response(200, text=f"data: {json_dumps(event)}\n\ndata: [DONE]\n")

    monkeypatch.setattr(oauth_compat.httpx, "AsyncClient", FakeAsyncClient)
    adapter = oauth_compat.CogneeOAuthLLMAdapter(auth_settings(tmp_path))

    asyncio.run(
        adapter.acreate_structured_output(
            text_input="question",
            system_prompt="system",
            response_model=SampleResponse,
            tools=[{"type": "web_search"}],
            tool_choice="auto",
            include=["web_search_call.action.sources"],
        )
    )

    assert requests[0]["tools"] == [{"type": "web_search"}]
    assert requests[0]["tool_choice"] == "auto"
    assert requests[0]["include"] == ["web_search_call.action.sources"]


def test_cognee_oauth_adapter_honors_model_and_reasoning_overrides(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(oauth_compat, "resolve_openai_text_bearer", lambda settings: "oauth-token")
    requests: list[dict[str, Any]] = []

    class FakeAsyncClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            del args, kwargs

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, *args: Any) -> None:
            del args

        async def post(self, url: str, *, headers: dict[str, str], json: dict[str, Any]) -> httpx.Response:
            del url, headers
            requests.append(json)
            event = {
                "type": "response.output_text.delta",
                "delta": '{"answer":"ok"}',
            }
            return httpx.Response(200, text=f"data: {json_dumps(event)}\n\ndata: [DONE]\n")

    monkeypatch.setattr(oauth_compat.httpx, "AsyncClient", FakeAsyncClient)
    adapter = oauth_compat.CogneeOAuthLLMAdapter(auth_settings(tmp_path))

    asyncio.run(
        adapter.acreate_structured_output(
            text_input="question",
            system_prompt="system",
            response_model=SampleResponse,
            model="gpt-5.5",
            reasoning_effort="medium",
        )
    )

    assert requests[0]["model"] == "gpt-5.5"
    assert requests[0]["reasoning"] == {"effort": "medium"}


def test_cognee_oauth_adapter_reads_completed_stream_item_text(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(oauth_compat, "resolve_openai_text_bearer", lambda settings: "oauth-token")
    requests: list[dict[str, Any]] = []

    class FakeAsyncClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            del args, kwargs

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, *args: Any) -> None:
            del args

        async def post(self, url: str, *, headers: dict[str, str], json: dict[str, Any]) -> httpx.Response:
            del url, headers
            requests.append(json)
            event = {
                "type": "response.output_item.done",
                "item": {"content": [{"type": "output_text", "text": '{"answer":"done"}'}]},
            }
            return httpx.Response(200, text=f"data: {json_dumps(event)}\n\ndata: [DONE]\n")

    monkeypatch.setattr(oauth_compat.httpx, "AsyncClient", FakeAsyncClient)
    adapter = oauth_compat.CogneeOAuthLLMAdapter(auth_settings(tmp_path))

    result = asyncio.run(
        adapter.acreate_structured_output(
            text_input="question",
            system_prompt="system",
            response_model=SampleResponse,
        )
    )

    assert result.answer == "done"
    assert [request["stream"] for request in requests] == [True]


def test_cognee_oauth_adapter_retries_empty_stream_response(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(oauth_compat, "resolve_openai_text_bearer", lambda settings: "oauth-token")
    monkeypatch.setattr(oauth_compat.asyncio, "sleep", lambda *_args, **_kwargs: _completed_sleep())
    monkeypatch.setattr(oauth_compat.random, "random", lambda: 0)
    requests: list[dict[str, Any]] = []

    class FakeAsyncClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            del args, kwargs

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, *args: Any) -> None:
            del args

        async def post(self, url: str, *, headers: dict[str, str], json: dict[str, Any]) -> httpx.Response:
            del url, headers
            requests.append(json)
            if len(requests) == 1:
                return httpx.Response(200, text="data: [DONE]\n")
            event = {
                "type": "response.output_text.delta",
                "delta": '{"answer":"retry"}',
            }
            return httpx.Response(200, text=f"data: {json_dumps(event)}\n\ndata: [DONE]\n")

    monkeypatch.setattr(oauth_compat.httpx, "AsyncClient", FakeAsyncClient)
    adapter = oauth_compat.CogneeOAuthLLMAdapter(auth_settings(tmp_path))

    result = asyncio.run(
        adapter.acreate_structured_output(
            text_input="question",
            system_prompt="system",
            response_model=SampleResponse,
        )
    )

    assert result.answer == "retry"
    assert len(requests) == 2


def test_cognee_oauth_adapter_retries_transport_errors(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(oauth_compat, "resolve_openai_text_bearer", lambda settings: "oauth-token")
    monkeypatch.setattr(oauth_compat.asyncio, "sleep", lambda *_args, **_kwargs: _completed_sleep())
    monkeypatch.setattr(oauth_compat.random, "random", lambda: 0)
    requests: list[dict[str, Any]] = []

    class FakeAsyncClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            del args, kwargs

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, *args: Any) -> None:
            del args

        async def post(self, url: str, *, headers: dict[str, str], json: dict[str, Any]) -> httpx.Response:
            del url, headers
            requests.append(json)
            if len(requests) == 1:
                raise httpx.RemoteProtocolError("incomplete chunked read")
            event = {
                "type": "response.output_text.delta",
                "delta": '{"answer":"transport-retry"}',
            }
            return httpx.Response(200, text=f"data: {json_dumps(event)}\n\ndata: [DONE]\n")

    monkeypatch.setattr(oauth_compat.httpx, "AsyncClient", FakeAsyncClient)
    adapter = oauth_compat.CogneeOAuthLLMAdapter(auth_settings(tmp_path))

    result = asyncio.run(
        adapter.acreate_structured_output(
            text_input="question",
            system_prompt="system",
            response_model=SampleResponse,
        )
    )

    assert result.answer == "transport-retry"
    assert len(requests) == 2


def test_cognee_oauth_adapter_supports_cognee_string_connection_check(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(oauth_compat, "resolve_openai_text_bearer", lambda settings: "oauth-token")
    requests: list[dict[str, Any]] = []

    class FakeAsyncClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            del args, kwargs

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, *args: Any) -> None:
            del args

        async def post(self, url: str, *, headers: dict[str, str], json: dict[str, Any]) -> httpx.Response:
            requests.append({"url": url, "headers": headers, "json": json})
            event = {
                "type": "response.output_text.delta",
                "delta": "test",
            }
            return httpx.Response(200, text=f"data: {json_dumps(event)}\n\ndata: [DONE]\n")

    monkeypatch.setattr(oauth_compat.httpx, "AsyncClient", FakeAsyncClient)
    adapter = oauth_compat.CogneeOAuthLLMAdapter(auth_settings(tmp_path))

    result = asyncio.run(
        adapter.acreate_structured_output(
            text_input="test",
            system_prompt='Respond to me with the following string: "test"',
            response_model=str,
        )
    )

    assert result == "test"
    assert "JSON schema:" not in requests[0]["json"]["input"][0]["content"]


def test_remember_text_prepares_oauth_runtime_before_cognee_call(tmp_path, monkeypatch) -> None:
    calls: list[str] = []

    class FakeCognee:
        async def remember(self, text: str, **kwargs: Any) -> dict[str, Any]:
            calls.append(text)
            return kwargs

    monkeypatch.setattr(
        "memory_stack.cognee_adapter.prepare_cognee_oauth_runtime",
        lambda settings: calls.append("prepared") or True,
    )
    monkeypatch.setattr("memory_stack.cognee_adapter.import_cognee", lambda: FakeCognee())

    result = asyncio.run(remember_text("hello", dataset_name="memory", settings=auth_settings(tmp_path)))

    assert calls == ["prepared", "hello"]
    assert result["dataset_name"] == "memory"
    assert result["temporal_cognify"] is True


def test_add_text_prepares_oauth_runtime_before_cognee_call(tmp_path, monkeypatch) -> None:
    calls: list[str] = []

    class FakeCognee:
        async def add(self, text: str, **kwargs: Any) -> dict[str, Any]:
            calls.append(text)
            return kwargs

    monkeypatch.setattr(
        "memory_stack.cognee_adapter.prepare_cognee_oauth_runtime",
        lambda settings: calls.append("prepared") or True,
    )
    monkeypatch.setattr("memory_stack.cognee_adapter.import_cognee", lambda: FakeCognee())

    result = asyncio.run(add_text("hello", dataset_name="memory", settings=auth_settings(tmp_path)))

    assert calls == ["prepared", "hello"]
    assert result["dataset_name"] == "memory"


def test_install_cognee_oauth_adapter_patches_cognee_factory(tmp_path, monkeypatch) -> None:
    llm_config_module = types.ModuleType("cognee.infrastructure.llm.config")
    client_module = types.ModuleType(
        "cognee.infrastructure.llm.structured_output_framework.litellm_instructor.llm.get_llm_client"
    )

    def fake_get_llm_config() -> None:
        return None

    def fake_cached_factory() -> None:
        return None

    fake_get_llm_config.cache_clear = lambda: None  # type: ignore[attr-defined]
    fake_cached_factory.cache_clear = lambda: None  # type: ignore[attr-defined]
    llm_config_module.get_llm_config = fake_get_llm_config  # type: ignore[attr-defined]
    client_module._get_llm_client_cached = fake_cached_factory  # type: ignore[attr-defined]
    client_module.get_llm_client = lambda: None  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, llm_config_module.__name__, llm_config_module)
    monkeypatch.setitem(sys.modules, client_module.__name__, client_module)

    assert oauth_compat.install_cognee_oauth_llm_adapter(auth_settings(tmp_path)) is True

    assert isinstance(client_module.get_llm_client(), oauth_compat.CogneeOAuthLLMAdapter)


def auth_settings(tmp_path, **kwargs: Any) -> Settings:
    values = {
        "brain_database_url": f"sqlite:///{tmp_path / 'brain.db'}",
        "brain_provider_auth_profiles_path": str(tmp_path / "profiles.json"),
        "brain_provider_auth_state_dir": str(tmp_path / "state"),
        "openai_auth_mode": "oauth",
        "openai_codex_base_url": "https://chatgpt.com/backend-api/codex",
    }
    values.update(kwargs)
    return Settings(**values)


def json_dumps(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"))
