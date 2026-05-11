from __future__ import annotations

import base64
import json
import sys
import time
from pathlib import Path
from typing import Any

import httpx
import pytest

from memory_stack.config import Settings
from memory_stack.evals import provider_client
from memory_stack.provider_auth import OpenAICodexCredential, upsert_openai_codex_profile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import live_model_smoke


PROVIDER_ENV_VARS = (
    "LLM_API_KEY",
    "EMBEDDING_API_KEY",
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "ANTHROPIC_API_KEY",
    "AWS_REGION",
    "AWS_DEFAULT_REGION",
    "AWS_PROFILE",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "AWS_BEARER_TOKEN_BEDROCK",
    "GROQ_API_KEY",
    "VOYAGE_API_KEY",
)


def clear_provider_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in PROVIDER_ENV_VARS:
        monkeypatch.delenv(key, raising=False)


def test_active_scope_selects_configured_llm_and_embedding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_provider_env(monkeypatch)
    settings = Settings(
        profile="openai",
        openai_auth_mode="api_key",
        llm_provider="openai",
        llm_model="openai/gpt-5.5",
        openai_api_key="sk-provider",
        embedding_provider="fastembed",
        embedding_model="intfloat/multilingual-e5-large",
        embedding_dimensions=1024,
    )

    probes = live_model_smoke.active_probes(settings)

    assert [(probe.kind, probe.provider, probe.model) for probe in probes] == [
        ("llm", "openai", "gpt-5.5"),
        ("embedding", "fastembed", "intfloat/multilingual-e5-large"),
    ]


def test_fastembed_embedding_probe_runs_locally(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_provider_env(monkeypatch)
    calls: list[tuple[str, str]] = []

    def fake_fastembed_vector(model: str, text: str) -> list[float]:
        calls.append((model, text))
        return [0.1, 0.2]

    monkeypatch.setattr(provider_client, "fastembed_vector", fake_fastembed_vector)
    settings = Settings()
    probe = live_model_smoke.Probe(
        provider="fastembed",
        model="intfloat/multilingual-e5-large",
        kind="embedding",
        label="active:embedding",
    )

    with httpx.Client() as client:
        results = live_model_smoke.run_probes(
            settings,
            [probe],
            client=client,
            skip_missing_keys=False,
        )

    assert results[0].status == "ok"
    assert calls == [("intfloat/multilingual-e5-large", "brain smoke test")]


def test_explicit_smoke_models_are_parsed_without_registry() -> None:
    parser = live_model_smoke.build_parser()
    args = live_model_smoke.normalize_args(
        parser.parse_args(["--models", "openai:gpt-5.5,fastembed:intfloat/multilingual-e5-large"])
    )
    probes = live_model_smoke.select_probes(
        Settings(),
        scope=args.scope,
        model_refs=live_model_smoke.parse_csv_list(args.models),
    )

    actual = {(probe.kind, probe.provider, probe.model) for probe in probes}
    assert actual == {
        ("llm", "openai", "gpt-5.5"),
        ("embedding", "fastembed", "intfloat/multilingual-e5-large"),
    }


def test_openai_active_probe_makes_live_style_calls_without_leaking_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_provider_env(monkeypatch)
    settings = Settings(
        profile="openai",
        openai_auth_mode="api_key",
        llm_provider="openai",
        llm_model="gpt-5.5",
        openai_api_key="sk-provider-secret",
        embedding_provider="fastembed",
        embedding_model="intfloat/multilingual-e5-large",
        embedding_dimensions=1024,
    )
    seen_paths: list[str] = []
    embedding_calls: list[tuple[str, str]] = []

    def fake_fastembed_vector(model: str, text: str) -> list[float]:
        embedding_calls.append((model, text))
        return [0.1, 0.2]

    def handler(request: httpx.Request) -> httpx.Response:
        seen_paths.append(request.url.path)
        assert request.headers["authorization"] == "Bearer sk-provider-secret"
        if request.url.path == "/v1/responses":
            return httpx.Response(200, json={"id": "resp_123", "output_text": '{"ok": true}'})
        return httpx.Response(404, json={"error": {"message": "not found"}})

    monkeypatch.setattr(provider_client, "fastembed_vector", fake_fastembed_vector)
    client = httpx.Client(transport=httpx.MockTransport(handler))
    probes = live_model_smoke.active_probes(settings)

    results = live_model_smoke.run_probes(
        settings,
        probes,
        client=client,
        skip_missing_keys=False,
    )

    assert [result.status for result in results] == ["ok", "ok"]
    assert seen_paths == ["/v1/responses"]
    assert embedding_calls == [("intfloat/multilingual-e5-large", "brain smoke test")]
    assert "sk-provider-secret" not in "\n".join(result.detail for result in results)


def test_missing_key_fails_by_default_and_can_skip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_provider_env(monkeypatch)
    settings = Settings()
    probe = live_model_smoke.Probe(
        provider="groq",
        model="llama-3.1-8b-instant",
        kind="llm",
        label="groq:llama-3.1-8b-instant",
    )
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(500)))

    fail_result = live_model_smoke.run_probes(
        settings,
        [probe],
        client=client,
        skip_missing_keys=False,
    )[0]
    skip_result = live_model_smoke.run_probes(
        settings,
        [probe],
        client=client,
        skip_missing_keys=True,
    )[0]

    assert fail_result.status == "fail"
    assert fail_result.detail == "missing GROQ_API_KEY"
    assert skip_result.status == "skip"
    assert skip_result.detail == "missing GROQ_API_KEY"


def test_openai_oauth_text_smoke_reports_missing_profile_without_api_key(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    clear_provider_env(monkeypatch)
    empty_codex_home = tmp_path / "empty-codex"
    empty_codex_home.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(empty_codex_home))
    settings = Settings(openai_auth_mode="oauth")

    assert live_model_smoke.missing_credential(
        settings,
        live_model_smoke.Probe(
            provider="openai",
            model="gpt-5.5",
            kind="llm",
            label="openai:gpt-5.5",
        ),
    ) == "OpenAI OAuth credentials are missing. Run `brain models auth login --provider openai-codex`."
    assert live_model_smoke.missing_credential(
        settings,
        live_model_smoke.Probe(
            provider="openai",
            model="text-embedding-3-small",
            kind="embedding",
            label="openai:text-embedding-3-small",
        ),
    ) == "missing OPENAI_API_KEY for OpenAI embeddings"


def test_openai_oauth_text_smoke_accepts_codex_cli_token_without_brain_profile(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    clear_provider_env(monkeypatch)
    codex_home = tmp_path / "codex"
    codex_home.mkdir()
    cli_access = jwt({"exp": int(time.time()) + 3600})
    (codex_home / "auth.json").write_text(
        json.dumps({"tokens": {"access_token": cli_access, "refresh_token": "external-refresh"}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("CODEX_HOME", str(codex_home))
    settings = Settings(
        profile="openai",
        openai_auth_mode="oauth",
        llm_provider="openai",
        llm_model="gpt-5.5",
        embedding_provider="fastembed",
        embedding_model="intfloat/multilingual-e5-large",
        embedding_dimensions=1024,
        brain_provider_auth_profiles_path=str(tmp_path / "profiles.json"),
        brain_provider_auth_state_dir=str(tmp_path / "state"),
    )

    assert (
        live_model_smoke.missing_credential(
            settings,
            live_model_smoke.Probe(
                provider="openai",
                model="gpt-5.5",
                kind="llm",
                label="openai:gpt-5.5",
            ),
        )
        is None
    )


def test_openai_oauth_text_smoke_uses_codex_bearer(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    clear_provider_env(monkeypatch)
    empty_codex_home = tmp_path / "empty-codex"
    empty_codex_home.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(empty_codex_home))
    settings = Settings(
        profile="openai",
        openai_auth_mode="oauth",
        llm_provider="openai",
        llm_model="gpt-5.5",
        embedding_provider="fastembed",
        embedding_model="intfloat/multilingual-e5-large",
        embedding_dimensions=1024,
        brain_provider_auth_profiles_path=str(tmp_path / "profiles.json"),
        brain_provider_auth_state_dir=str(tmp_path / "state"),
    )
    upsert_openai_codex_profile(
        settings,
        OpenAICodexCredential(
            access="oauth-access",
            refresh="oauth-refresh",
            expires=int(time.time() * 1000) + 600_000,
        ),
    )
    assert (
        live_model_smoke.missing_credential(
            settings,
            live_model_smoke.Probe(
                provider="openai",
                model="gpt-5.5",
                kind="llm",
                label="openai:gpt-5.5",
            ),
        )
        is None
    )
    seen: list[tuple[str, str]] = []
    seen_json: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((str(request.url), request.headers["authorization"]))
        seen_json.append(json.loads(request.content.decode("utf-8")))
        return httpx.Response(
            200,
            text='data: {"type":"response.completed","response":{"output_text":"{\\"ok\\": true}"}}\n\n',
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    results = live_model_smoke.run_probes(
        settings,
        [
            live_model_smoke.Probe(
                provider="openai",
                model="gpt-5.5",
                kind="llm",
                label="openai:gpt-5.5",
            )
        ],
        client=client,
        skip_missing_keys=False,
    )

    assert [result.status for result in results] == ["ok"]
    assert seen == [
        (
            "https://chatgpt.com/backend-api/codex/responses",
            "Bearer oauth-access",
        )
    ]
    assert len(seen_json) == 1
    assert seen_json[0]["model"] == "gpt-5.5"
    assert seen_json[0]["instructions"].startswith("Return only one JSON object")
    assert seen_json[0]["store"] is False
    assert seen_json[0]["stream"] is True
    assert "Return exactly this JSON object" in seen_json[0]["input"][0]["content"]
    assert "JSON schema" in seen_json[0]["input"][0]["content"]


def test_openrouter_probe_uses_api_model_and_quantization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_provider_env(monkeypatch)
    settings = Settings(
        profile="openai",
        llm_provider="openai",
        llm_model="gpt-5.5",
        openai_api_key="sk-provider",
        openrouter_api_key="sk-or-provider",
        embedding_provider="fastembed",
        embedding_model="intfloat/multilingual-e5-large",
        embedding_dimensions=1024,
    )
    seen_json: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v1/chat/completions":
            seen_json.append(__import__("json").loads(request.content.decode("utf-8")))
            return httpx.Response(200, json={"choices": [{"message": {"content": '{"ok": true}'}}]})
        return httpx.Response(404, json={"error": {"message": "not found"}})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    probe = live_model_smoke.Probe(
        provider="openrouter",
        model="google/gemma-4-31b-it-fp8",
        api_model="google/gemma-4-31b-it",
        kind="llm",
        label="openrouter:google/gemma-4-31b-it-fp8",
        quantizations=("fp8",),
    )

    results = live_model_smoke.run_probes(settings, [probe], client=client, skip_missing_keys=False)

    assert [result.status for result in results] == ["ok"]
    assert seen_json == [
        {
            "model": "google/gemma-4-31b-it",
            "messages": [
                {
                    "role": "user",
                    "content": (
                        'Return exactly this JSON object: {"ok": true}\n'
                        "Return only one JSON object. Do not wrap it in Markdown.\n"
                        'JSON schema:\n{"type":"object","properties":{"ok":{"type":"boolean"}},"required":["ok"],"additionalProperties":false}'
                    ),
                }
            ],
            "max_tokens": provider_client.MAX_OUTPUT_TOKENS,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "provider": {"quantizations": ["fp8"]},
        }
    ]


def test_google_probe_uses_api_model_and_thinking_level(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_provider_env(monkeypatch)
    settings = Settings(
        profile="openai",
        llm_provider="openai",
        llm_model="gpt-5.5",
        openai_api_key="sk-provider",
        gemini_api_key="AIza-provider",
        embedding_provider="fastembed",
        embedding_model="intfloat/multilingual-e5-large",
        embedding_dimensions=1024,
    )
    seen_json: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith(":generateContent"):
            seen_json.append(__import__("json").loads(request.content.decode("utf-8")))
            return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": '{"ok": true}' }]}}]})
        return httpx.Response(404, json={"error": {"message": "not found"}})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    probe = live_model_smoke.Probe(
        provider="google",
        model="gemini-3.1-pro-preview-high",
        api_model="gemini-3.1-pro-preview",
        reasoning_effort="high",
        kind="llm",
        label="google:gemini-3.1-pro-preview-high",
    )

    results = live_model_smoke.run_probes(settings, [probe], client=client, skip_missing_keys=False)

    assert [result.status for result in results] == ["ok"]
    assert len(seen_json) == 1
    assert "Return exactly this JSON object" in seen_json[0]["contents"][0]["parts"][0]["text"]
    assert seen_json[0]["generationConfig"] == {
        "maxOutputTokens": provider_client.MAX_OUTPUT_TOKENS,
        "temperature": 0,
        "responseMimeType": "application/json",
        "thinkingConfig": {"thinkingLevel": "high"},
    }


def jwt(payload: dict[str, Any]) -> str:
    header = {"alg": "none"}
    return ".".join(
        [
            b64(json.dumps(header).encode("utf-8")),
            b64(json.dumps(payload).encode("utf-8")),
            "",
        ]
    )


def b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")
