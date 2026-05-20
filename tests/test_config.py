from __future__ import annotations

import pytest

from memory_stack.cfg import Settings, normalize_path, runtime_env
from memory_stack.model_selection import DEFAULT_LLM_MODEL


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


def test_normalize_path() -> None:
    assert normalize_path("mcp") == "/mcp"
    assert normalize_path("/mcp/") == "/mcp"


def test_runtime_rejects_non_openai_profile() -> None:
    with pytest.raises(ValueError):
        Settings(
            profile="local",
        )


def test_openai_api_key_is_used_for_fixed_llm_only(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_provider_env(monkeypatch)
    env_file = tmp_path / ".env.openai"
    env_file.write_text(
        "\n".join(
            [
                "PROFILE=openai",
                "OPENAI_AUTH_MODE=api_key",
                "LLM_PROVIDER=openai",
                f"LLM_MODEL={DEFAULT_LLM_MODEL}",
                "OPENAI_API_KEY=sk-provider",
                "EMBEDDING_PROVIDER=openai",
                "EMBEDDING_MODEL=text-embedding-3-large",
                "EMBEDDING_DIMENSIONS=3072",
            ]
        ),
        encoding="utf-8",
    )

    settings = Settings(_env_file=str(env_file))
    env = runtime_env(settings)

    assert settings.llm_api_key == "sk-provider"
    assert settings.embedding_api_key == "sk-provider"
    assert env["LLM_API_KEY"] == "sk-provider"
    assert env["OPENAI_API_KEY"] == "sk-provider"
    assert env["EMBEDDING_API_KEY"] == "sk-provider"


def test_openai_oauth_is_default_and_does_not_export_text_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_provider_env(monkeypatch)
    settings = Settings(
        profile="openai",
        llm_provider="openai",
        llm_model=DEFAULT_LLM_MODEL,
        openai_api_key="sk-provider",
        embedding_provider="openai",
        embedding_model="text-embedding-3-large",
        embedding_dimensions=3072,
        graph_database_provider="ladybug",
    )
    env = runtime_env(settings)

    assert settings.openai_auth_mode == "oauth"
    assert settings.llm_api_key is None
    assert settings.provider_api_key("openai") is None
    assert env["OPENAI_AUTH_MODE"] == "oauth"
    assert "LLM_API_KEY" not in env
    assert "EMBEDDING_API_KEY" not in env
    assert "OPENAI_API_KEY" not in env


def test_openai_profile_exports_fixed_models(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_provider_env(monkeypatch)
    settings = Settings(
        profile="openai",
        llm_provider="openai",
        llm_model=DEFAULT_LLM_MODEL,
        openai_auth_mode="oauth",
        openai_api_key="sk-provider",
        embedding_provider="openai",
        embedding_model="text-embedding-3-large",
        embedding_dimensions=3072,
        graph_database_provider="ladybug",
    )
    env = runtime_env(settings)

    assert settings.llm_api_key is None
    assert settings.embedding_api_key is None
    assert settings.provider_api_key("openai") is None
    assert env["PROFILE"] == "openai"
    assert env["LLM_PROVIDER"] == "openai"
    assert env["EMBEDDING_PROVIDER"] == "openai"
    assert env["EMBEDDING_MODEL"] == "text-embedding-3-large"
    assert env["EMBEDDING_DIMENSIONS"] == "3072"
    assert env["GRAPH_DATABASE_PROVIDER"] == "ladybug"
    assert env["ENABLE_BACKEND_ACCESS_CONTROL"] == "false"
    assert "LLM_API_KEY" not in env
    assert "EMBEDDING_API_KEY" not in env
    assert "OPENAI_API_KEY" not in env


def test_cognee_env_does_not_export_cloud_or_modal_env() -> None:
    env = runtime_env(Settings())

    assert "COGNEE_DISTRIBUTED" not in env
    assert "MODAL_SECRET_NAME" not in env
    assert "BRAIN_COGNEE_EXECUTION_BACKEND" not in env
    assert env["BRAIN_COGNEE_SYNC_ON_INGEST"] == "false"
    assert env["BRAIN_COGNEE_SYNC_ON_INGEST_SWEEP_LIMIT"] == "25"


def test_cognee_uses_postgres_pgvector_by_default() -> None:
    env = runtime_env(Settings())

    assert env["DB_PROVIDER"] == "postgres"
    assert env["DB_HOST"] == "127.0.0.1"
    assert env["DB_PORT"] == "5432"
    assert env["DB_USERNAME"] == "cognee"
    assert env["DB_PASSWORD"] == "cognee"
    assert env["VECTOR_DB_PROVIDER"] == "pgvector"
    assert env["VECTOR_DATASET_DATABASE_HANDLER"] == "pgvector"
    assert env["VECTOR_DB_HOST"] == "127.0.0.1"
    assert env["VECTOR_DB_PORT"] == "5432"
    assert env["VECTOR_DB_USERNAME"] == "cognee"
    assert env["VECTOR_DB_PASSWORD"] == "cognee"


def test_runtime_rejects_non_default_llm_or_embedding() -> None:
    with pytest.raises(ValueError, match="runtime LLM is fixed"):
        Settings(llm_model="gpt-5.5")

    with pytest.raises(ValueError, match="runtime embeddings are fixed"):
        Settings(
            embedding_provider="openai",
            embedding_model="text-embedding-3-small",
            embedding_dimensions=1536,
        )


def test_llm_api_key_overrides_provider_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_provider_env(monkeypatch)
    settings = Settings(
        profile="openai",
        openai_auth_mode="api_key",
        llm_provider="openai",
        llm_model=DEFAULT_LLM_MODEL,
        llm_api_key="sk-llm-role",
        openai_api_key="sk-provider",
        embedding_provider="openai",
        embedding_model="text-embedding-3-large",
        embedding_dimensions=3072,
    )

    assert settings.llm_api_key == "sk-llm-role"
    assert settings.embedding_api_key == "sk-provider"
    assert runtime_env(settings)["OPENAI_API_KEY"] == "sk-provider"


def test_provider_key_lookup_supports_non_active_benchmark_providers(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_provider_env(monkeypatch)
    env_file = tmp_path / ".env.benchmark"
    env_file.write_text(
        "\n".join(
            [
                "PROFILE=openai",
                "LLM_PROVIDER=openai",
                f"LLM_MODEL={DEFAULT_LLM_MODEL}",
                "EMBEDDING_PROVIDER=openai",
                "EMBEDDING_MODEL=text-embedding-3-large",
                "EMBEDDING_DIMENSIONS=3072",
                "GROQ_API_KEY=gsk-provider",
                "ANTHROPIC_API_KEY=sk-ant-provider",
                "VOYAGE_API_KEY=pa-provider",
                "AWS_REGION=eu-west-2",
                "AWS_BEARER_TOKEN_BEDROCK=bedrock-provider",
            ]
        ),
        encoding="utf-8",
    )

    settings = Settings(_env_file=str(env_file))
    env = runtime_env(settings)

    assert settings.provider_api_key("groq:llama-3.1-8b-instant") == "gsk-provider"
    assert settings.provider_api_key("anthropic/claude-sonnet-4.6") == "sk-ant-provider"
    assert settings.provider_api_key("voyage:voyage-4-lite") == "pa-provider"
    assert (
        settings.provider_api_key("aws-bedrock:nvidia.nemotron-super-3-120b")
        == "bedrock-provider"
    )
    assert env["GROQ_API_KEY"] == "gsk-provider"
    assert env["ANTHROPIC_API_KEY"] == "sk-ant-provider"
    assert env["VOYAGE_API_KEY"] == "pa-provider"
    assert env["AWS_REGION"] == "eu-west-2"
    assert env["AWS_BEARER_TOKEN_BEDROCK"] == "bedrock-provider"

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


def test_taste_settings_are_exported() -> None:
    settings = Settings(
        brain_taste_enabled=True,
        brain_taste_omdb_api_key="omdb-key",
        brain_taste_google_places_api_key="places-key",
    )
    env = runtime_env(settings)

    assert env["BRAIN_TASTE_ENABLED"] == "true"
    assert env["BRAIN_TASTE_LLM_ROUTING_ENABLED"] == "false"
    assert env["BRAIN_TASTE_AUTO_ENRICH_ENABLED"] == "true"
    assert env["BRAIN_TASTE_OMDB_API_KEY"] == "omdb-key"
    assert env["BRAIN_TASTE_GOOGLE_PLACES_API_KEY"] == "places-key"
    assert env["BRAIN_TASTE_OPEN_LOOP_CONFIRMATION_THRESHOLD"] == "0.8"
    assert "BRAIN_TASTE_IMPORT_SOURCE_PATH" not in env
