from __future__ import annotations

import pytest

from memory_stack.config import Settings, normalize_path, runtime_env


PROVIDER_ENV_VARS = (
    "LLM_API_KEY",
    "EMBEDDING_API_KEY",
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "ANTHROPIC_API_KEY",
    "GROQ_API_KEY",
)


def clear_provider_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in PROVIDER_ENV_VARS:
        monkeypatch.delenv(key, raising=False)


def test_normalize_path() -> None:
    assert normalize_path("mcp") == "/mcp"
    assert normalize_path("/mcp/") == "/mcp"


def test_local_profile_rejects_cloud_provider() -> None:
    with pytest.raises(ValueError):
        Settings(
            profile="local",
            llm_provider="openai",
            llm_model="gpt-5.4-mini",
            llm_api_key="sk-test",
            embedding_provider="fastembed",
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            embedding_dimensions=384,
        )


def test_openai_provider_key_reuses_key_for_llm_and_embeddings(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_provider_env(monkeypatch)
    env_file = tmp_path / ".env.openai"
    env_file.write_text(
        "\n".join(
            [
                "PROFILE=openai",
                "LLM_PROVIDER=openai",
                "LLM_MODEL=gpt-5.4-mini",
                "OPENAI_API_KEY=sk-provider",
                "EMBEDDING_PROVIDER=openai",
                "EMBEDDING_MODEL=text-embedding-3-small",
                "EMBEDDING_DIMENSIONS=1536",
            ]
        ),
        encoding="utf-8",
    )

    settings = Settings(_env_file=str(env_file))
    env = runtime_env(settings)

    assert settings.llm_api_key == "sk-provider"
    assert settings.embedding_api_key == "sk-provider"
    assert env["LLM_API_KEY"] == "sk-provider"
    assert env["EMBEDDING_API_KEY"] == "sk-provider"
    assert env["OPENAI_API_KEY"] == "sk-provider"


def test_role_api_keys_override_provider_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_provider_env(monkeypatch)
    settings = Settings(
        profile="openai",
        llm_provider="openai",
        llm_model="gpt-5.4-mini",
        llm_api_key="sk-llm-role",
        openai_api_key="sk-provider",
        embedding_provider="openai",
        embedding_model="text-embedding-3-small",
        embedding_api_key="sk-embedding-role",
        embedding_dimensions=1536,
    )

    assert settings.llm_api_key == "sk-llm-role"
    assert settings.embedding_api_key == "sk-embedding-role"
    assert runtime_env(settings)["OPENAI_API_KEY"] == "sk-provider"


def test_gemini_provider_can_use_google_api_key_alias(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_provider_env(monkeypatch)
    env_file = tmp_path / ".env.gemini"
    env_file.write_text(
        "\n".join(
            [
                "PROFILE=gemini",
                "LLM_PROVIDER=gemini",
                "LLM_MODEL=gemini/gemini-3.1-flash-lite-preview",
                "GOOGLE_API_KEY=AIza-provider",
                "EMBEDDING_PROVIDER=gemini",
                "EMBEDDING_MODEL=gemini/gemini-embedding-001",
                "EMBEDDING_DIMENSIONS=768",
            ]
        ),
        encoding="utf-8",
    )

    settings = Settings(_env_file=str(env_file))
    env = runtime_env(settings)

    assert settings.llm_api_key == "AIza-provider"
    assert settings.embedding_api_key == "AIza-provider"
    assert env["GEMINI_API_KEY"] == "AIza-provider"
    assert env["GOOGLE_API_KEY"] == "AIza-provider"


def test_provider_key_lookup_supports_non_active_benchmark_providers(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_provider_env(monkeypatch)
    env_file = tmp_path / ".env.benchmark"
    env_file.write_text(
        "\n".join(
            [
                "PROFILE=gemini",
                "LLM_PROVIDER=gemini",
                "LLM_MODEL=gemini/gemini-3.1-flash-lite-preview",
                "GEMINI_API_KEY=AIza-provider",
                "EMBEDDING_PROVIDER=gemini",
                "EMBEDDING_MODEL=gemini/gemini-embedding-001",
                "EMBEDDING_DIMENSIONS=768",
                "GROQ_API_KEY=gsk-provider",
                "ANTHROPIC_API_KEY=sk-ant-provider",
            ]
        ),
        encoding="utf-8",
    )

    settings = Settings(_env_file=str(env_file))

    assert settings.provider_api_key("groq:llama-3.1-8b-instant") == "gsk-provider"
    assert settings.provider_api_key("anthropic/claude-sonnet-4.6") == "sk-ant-provider"


def test_public_mcp_url() -> None:
    settings = Settings(
        brain_public_base_url="https://brain.dceb.net/",
        brain_public_mcp_path="mcp",
    )
    assert settings.public_mcp_url == "https://brain.dceb.net/mcp"


def test_public_ui_urls() -> None:
    settings = Settings(
        brain_public_base_url="https://brain.dceb.net/",
        brain_public_ui_path="ui",
        brain_public_ui_api_path="ui-api",
    )
    assert settings.public_ui_url == "https://brain.dceb.net/ui"
    assert settings.public_ui_api_url == "https://brain.dceb.net/ui-api"


def test_slack_agent_settings_are_exported() -> None:
    settings = Settings(
        brain_slack_agent_enabled=True,
        brain_slack_agent_port=8003,
        brain_slack_allowed_team_ids="T1,T2",
        brain_slack_allowed_channel_ids="C1",
        brain_slack_allowed_user_ids="U1",
        brain_slack_admin_user_ids="UADMIN",
        brain_slack_signing_secret="secret",
        brain_slack_bot_token="xoxb-test",
    )
    env = runtime_env(settings)

    assert settings.brain_slack_allowed_team_id_list == ["T1", "T2"]
    assert settings.brain_slack_admin_user_id_list == ["UADMIN"]
    assert env["BRAIN_SLACK_AGENT_ENABLED"] == "true"
    assert env["BRAIN_SLACK_AGENT_PORT"] == "8003"
    assert env["BRAIN_SLACK_SIGNING_SECRET"] == "secret"
    assert env["BRAIN_SLACK_BOT_TOKEN"] == "xoxb-test"
