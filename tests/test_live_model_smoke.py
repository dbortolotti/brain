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


def test_openai_active_probe_makes_live_style_calls_without_leaking_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_provider_env(monkeypatch)
    settings = Settings(
        profile="openai",
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
