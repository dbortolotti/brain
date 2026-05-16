from __future__ import annotations

import importlib

import pytest

import cfg
from memory_stack import cfg as package_cfg
from memory_stack.cfg import Settings


def test_cfg_defaults_to_dev() -> None:
    values = package_cfg.reload("dev")

    assert package_cfg.active_env() == "dev"
    assert values["CONFIG_ENV"] == "dev"
    assert cfg.get("LLM_MODEL") == "gpt-5.4-mini"
    assert cfg.get("BRAIN_TASTE_LLM_MODEL") == "gpt-5.5"
    assert cfg.get("BRAIN_TASTE_LLM_REASONING_EFFORT") == "medium"
    assert cfg.get("BRAIN_OWNER_FULL_NAME") == "Daniele Bortolotti"
    assert cfg.get("BRAIN_OWNER_NAME") == "Daniele"
    assert cfg.get("BRAIN_PROFILE_CONTEXT_PATH") == "./.data/brain/profile_context.json"
    assert cfg.get("BRAIN_AGENT_MEMORY_SESSION_ID") == "portable_agent_session"
    assert cfg.get("BRAIN_REQUEST_LOG_PATH") == "./.data/logs/requests/{date}.jsonl"
    assert cfg.get("BRAIN_ROUTING_LOG_PATH") == "./.data/logs/routing/{date}.jsonl"
    assert cfg.get("BRAIN_LOG_LEVEL") == "DEBUG"


def test_cfg_uses_prod_only_when_explicit() -> None:
    values = package_cfg.reload("prod")

    assert package_cfg.active_env() == "prod"
    assert values["CONFIG_ENV"] == "prod"
    assert values["BRAIN_LOG_LEVEL"] == "INFO"
    assert values["BRAIN_DATABASE_URL"] == "sqlite:////Volumes/xpg_usb4/prod/brain/shared/data/brain/brain.db"
    assert values["VECTOR_DB_PROVIDER"] == "pgvector"
    assert values["VECTOR_DB_PORT"] == 15432
    assert values["VECTOR_DATASET_DATABASE_HANDLER"] == "pgvector"
    assert values["DB_PROVIDER"] == "postgres"
    assert values["DB_PORT"] == 15432
    assert (
        values["BRAIN_PROFILE_CONTEXT_PATH"]
        == "/Volumes/xpg_usb4/prod/brain/shared/data/brain/profile_context.json"
    )
    assert values["BRAIN_TASTE_CANONICAL_STORE"] == "cognee"
    assert values["BRAIN_REQUEST_LOG_PATH"] == "/Volumes/xpg_usb4/prod/brain/shared/logs/requests/{date}.jsonl"
    assert values["BRAIN_ROUTING_LOG_ENABLED"] is True


def test_cfg_supports_staging_environment() -> None:
    values = package_cfg.reload("staging")

    assert package_cfg.active_env() == "staging"
    assert values["CONFIG_ENV"] == "staging"
    assert values["BRAIN_DATABASE_URL"] == "sqlite:////Volumes/xpg_usb4/staging/brain/shared/data/brain/brain.db"
    assert values["BRAIN_PUBLIC_BASE_URL"] == "https://staging.brain.dceb.net"
    assert values["BRAIN_MCP_PORT"] == 18100
    assert values["VECTOR_DB_PORT"] == 16432
    assert values["DB_PORT"] == 16432
    assert values["BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED"] is False


def test_cfg_rejects_unknown_environment() -> None:
    with pytest.raises(package_cfg.ConfigError, match="Unsupported config environment"):
        package_cfg.reload("qa")


def test_settings_defaults_follow_explicit_config_env(tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("", encoding="utf-8")
    package_cfg.reload("prod")

    settings = Settings(_env_file=str(env_file))

    assert settings.brain_database_url == "sqlite:////Volumes/xpg_usb4/prod/brain/shared/data/brain/brain.db"
    assert settings.vector_db_provider == "pgvector"
    assert settings.vector_db_port == 15432
    assert settings.vector_dataset_database_handler == "pgvector"
    assert settings.db_provider == "postgres"
    assert settings.db_port == 15432
    assert settings.system_root_directory == "/Volumes/xpg_usb4/prod/brain/shared/data/system"
    assert settings.brain_ui_enabled is True
    assert settings.brain_taste_canonical_store == "cognee"
    assert settings.brain_owner_full_name == "Daniele Bortolotti"
    assert settings.brain_owner_name == "Daniele"
    assert (
        settings.brain_profile_context_path
        == "/Volumes/xpg_usb4/prod/brain/shared/data/brain/profile_context.json"
    )
    assert settings.brain_agent_memory_session_id == "portable_agent_session"


def test_load_settings_accepts_explicit_config_env(tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("", encoding="utf-8")
    package_cfg.reload("dev")

    from memory_stack.cfg import load_settings

    settings = load_settings(env_file, config_env="prod")

    assert package_cfg.active_env() == "prod"
    assert settings.brain_database_url == "sqlite:////Volumes/xpg_usb4/prod/brain/shared/data/brain/brain.db"
    assert settings.brain_ui_enabled is True


def test_model_selection_defaults_come_from_cfg() -> None:
    package_cfg.reload("dev")
    model_selection = importlib.import_module("memory_stack.model_selection")

    assert model_selection.DEFAULT_LLM_MODEL == package_cfg.get("LLM_MODEL")
    assert model_selection.DEFAULT_EMBEDDING_MODEL == package_cfg.get("EMBEDDING_MODEL")
