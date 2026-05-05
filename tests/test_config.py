from __future__ import annotations

import pytest

from memory_stack.config import Settings, normalize_path, runtime_env


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
