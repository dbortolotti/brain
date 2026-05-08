from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest

from memory_stack.config import Settings

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
        llm_model="openai/gpt-5.4-mini",
        openai_api_key="sk-provider",
        embedding_provider="openai",
        embedding_model="text-embedding-3-small",
        embedding_dimensions=1536,
    )

    probes = live_model_smoke.active_probes(settings)

    assert [(probe.kind, probe.provider, probe.model) for probe in probes] == [
        ("llm", "openai", "gpt-5.4-mini"),
        ("embedding", "openai", "text-embedding-3-small"),
    ]


def test_core_scope_maps_aliases_and_excludes_judges_by_default() -> None:
    registry = {
        "providers": {
            "anthropic": {
                "type": "llm",
                "models": [
                    {
                        "id": "claude-haiku-4-5-20251001",
                        "alias": "claude-haiku-4-5",
                        "enabled_by_default": True,
                        "roles": ["conflict_classifier"],
                    },
                    {
                        "id": "claude-sonnet-4-6",
                        "alias": "claude-sonnet-4-6",
                        "enabled_by_default": True,
                        "roles": ["eval_judge"],
                        "judge_only": True,
                    },
                ],
            }
        },
        "core_eval_matrix": {
            "conflict_classifier": ["anthropic:claude-haiku-4-5"],
            "eval_judge": ["anthropic:claude-sonnet-4-6"],
        },
    }

    probes = live_model_smoke.core_registry_probes(
        registry,
        roles=set(),
        include_judge=False,
    )

    assert [(probe.provider, probe.model, probe.roles) for probe in probes] == [
        (
            "anthropic",
            "claude-haiku-4-5-20251001",
            ("conflict_classifier",),
        )
    ]


def test_all_registry_shortcut_selects_every_declared_model() -> None:
    registry = live_model_smoke.load_registry(live_model_smoke.REGISTRY_PATH)

    parser = live_model_smoke.build_parser()
    args = live_model_smoke.normalize_args(parser.parse_args(["--all-registry"]))
    probes = live_model_smoke.select_probes(
        Settings(),
        registry,
        scope=args.scope,
        roles=set(args.role or []),
        include_judge=args.include_judge,
    )

    expected = set()
    for provider, config in (registry.get("providers") or {}).items():
        provider_type = str(config.get("type", "llm"))
        for model in config.get("models") or []:
            if model.get("skip_reason"):
                continue
            if provider == "embeddings":
                expected_provider = live_model_smoke.normalize_provider(str(model["provider"]))
                kind = "embedding"
            else:
                expected_provider = live_model_smoke.normalize_provider(provider)
                kind = provider_type
            expected.add((kind, expected_provider, str(model["id"])))

    actual = {(probe.kind, probe.provider, probe.model) for probe in probes}
    assert args.scope == "all"
    assert args.include_judge is True
    assert actual == expected
    assert any(probe.judge_only for probe in probes)
    assert ("llm", "openai", "gpt-5.5") in actual
    assert ("embedding", "voyage", "voyage-4-large") in actual
    assert ("llm", "aws-bedrock", "mistral.mistral-large-3-675b-instruct") not in actual


def test_openai_active_probe_makes_live_style_calls_without_leaking_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_provider_env(monkeypatch)
    settings = Settings(
        profile="openai",
        openai_auth_mode="api_key",
        llm_provider="openai",
        llm_model="gpt-5.4-mini",
        openai_api_key="sk-provider-secret",
        embedding_provider="openai",
        embedding_model="text-embedding-3-small",
        embedding_dimensions=1536,
    )
    seen_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_paths.append(request.url.path)
        assert request.headers["authorization"] == "Bearer sk-provider-secret"
        if request.url.path == "/v1/responses":
            return httpx.Response(200, json={"id": "resp_123", "output": []})
        if request.url.path == "/v1/embeddings":
            return httpx.Response(200, json={"data": [{"embedding": [0.1, 0.2]}]})
        return httpx.Response(404, json={"error": {"message": "not found"}})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    probes = live_model_smoke.active_probes(settings)

    results = live_model_smoke.run_probes(
        settings,
        probes,
        client=client,
        skip_missing_keys=False,
    )

    assert [result.status for result in results] == ["ok", "ok"]
    assert seen_paths == ["/v1/responses", "/v1/embeddings"]
    assert "sk-provider-secret" not in "\n".join(result.detail for result in results)


def test_missing_key_fails_by_default_and_can_skip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_provider_env(monkeypatch)
    settings = Settings(
        profile="openai",
        llm_provider="openai",
        llm_model="gpt-5.4-mini",
        embedding_provider="openai",
        embedding_model="text-embedding-3-small",
        embedding_dimensions=1536,
    )
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


def test_openai_oauth_text_smoke_does_not_require_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_provider_env(monkeypatch)
    settings = Settings(
        profile="openai",
        openai_auth_mode="oauth",
        llm_provider="openai",
        llm_model="gpt-5.4-mini",
        embedding_provider="openai",
        embedding_model="text-embedding-3-small",
        embedding_dimensions=1536,
    )

    assert (
        live_model_smoke.missing_credential(
            settings,
            live_model_smoke.Probe(
                provider="openai",
                model="gpt-5.4-mini",
                kind="llm",
                label="openai:gpt-5.4-mini",
            ),
        )
        is None
    )
    assert live_model_smoke.missing_credential(
        settings,
        live_model_smoke.Probe(
            provider="openai",
            model="text-embedding-3-small",
            kind="embedding",
            label="openai:text-embedding-3-small",
        ),
    ) == "missing OPENAI_API_KEY for OpenAI embeddings"


def test_openrouter_probe_uses_api_model_and_quantization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_provider_env(monkeypatch)
    settings = Settings(
        profile="openai",
        llm_provider="openai",
        llm_model="gpt-5.4-mini",
        openai_api_key="sk-provider",
        openrouter_api_key="sk-or-provider",
        embedding_provider="openai",
        embedding_model="text-embedding-3-small",
        embedding_dimensions=1536,
    )
    seen_json: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v1/chat/completions":
            seen_json.append(__import__("json").loads(request.content.decode("utf-8")))
            return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})
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
            "messages": [{"role": "user", "content": "Reply with exactly: ok"}],
            "max_tokens": live_model_smoke.SMOKE_MAX_TOKENS,
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
        llm_model="gpt-5.4-mini",
        openai_api_key="sk-provider",
        gemini_api_key="AIza-provider",
        embedding_provider="openai",
        embedding_model="text-embedding-3-small",
        embedding_dimensions=1536,
    )
    seen_json: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith(":generateContent"):
            seen_json.append(__import__("json").loads(request.content.decode("utf-8")))
            return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": "ok"}]}}]})
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
    assert seen_json == [
        {
            "contents": [{"parts": [{"text": "Reply with exactly: ok"}]}],
            "generationConfig": {"maxOutputTokens": live_model_smoke.SMOKE_MAX_TOKENS, "temperature": 0, "thinkingConfig": {"thinkingLevel": "high"}},
        }
    ]
