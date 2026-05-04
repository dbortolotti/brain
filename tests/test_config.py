from __future__ import annotations

import pytest

from memory_stack.config import Settings, normalize_path


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
