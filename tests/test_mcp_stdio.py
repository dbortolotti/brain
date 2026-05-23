from __future__ import annotations

import pytest

from memory_stack.cfg import Settings
from memory_stack.mcp_stdio import _validate_stdio_launch_auth


def test_stdio_launch_auth_requires_bearer_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("BRAIN_STDIO_BEARER_TOKEN", raising=False)
    monkeypatch.setenv("BRAIN_STDIO_USER_ID", "alice")
    settings = Settings(brain_auth_token="secret", brain_user_id="alice")

    with pytest.raises(RuntimeError, match="BRAIN_STDIO_BEARER_TOKEN is required"):
        _validate_stdio_launch_auth(settings)


def test_stdio_launch_auth_rejects_wrong_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BRAIN_STDIO_BEARER_TOKEN", "wrong")
    monkeypatch.setenv("BRAIN_STDIO_USER_ID", "alice")
    settings = Settings(brain_auth_token="secret", brain_user_id="alice")

    with pytest.raises(RuntimeError, match="does not match BRAIN_AUTH_TOKEN"):
        _validate_stdio_launch_auth(settings)


def test_stdio_launch_auth_requires_explicit_matching_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BRAIN_STDIO_BEARER_TOKEN", "secret")
    monkeypatch.setenv("BRAIN_STDIO_USER_ID", "bob")
    settings = Settings(brain_auth_token="secret", brain_user_id="alice")

    with pytest.raises(RuntimeError, match="must match BRAIN_USER_ID"):
        _validate_stdio_launch_auth(settings)


def test_stdio_launch_auth_accepts_bearer_prefix_and_normalizes_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BRAIN_STDIO_BEARER_TOKEN", "Bearer secret")
    monkeypatch.setenv("BRAIN_STDIO_USER_ID", "Alice Smith")
    settings = Settings(brain_auth_token="secret", brain_user_id="alice_smith")

    scoped_settings = _validate_stdio_launch_auth(settings)

    assert scoped_settings.brain_user_id == "alice_smith"
