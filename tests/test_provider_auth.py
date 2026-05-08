from __future__ import annotations

import base64
import json
import threading
import time
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

import memory_stack.brain_cli as brain_cli
from memory_stack.brain_cli import app
from memory_stack.config import Settings
from memory_stack import provider_auth
from memory_stack.provider_auth import (
    OpenAICodexCredential,
    ProviderAuthError,
    build_openai_codex_authorize_url,
    generate_pkce_pair,
    get_openai_codex_profile,
    list_openai_codex_profiles,
    parse_authorization_response,
    refresh_openai_codex_profile,
    resolve_openai_text_bearer,
    upsert_openai_codex_profile,
)


runner = CliRunner()


def test_pkce_generation_and_authorize_url() -> None:
    pkce = generate_pkce_pair()
    url = build_openai_codex_authorize_url(state="state-1", challenge=pkce.challenge)

    assert pkce.verifier
    assert pkce.challenge
    assert "client_id=app_EMoamEEZ73f0CkXaXp7hrann" in url
    assert "code_challenge_method=S256" in url
    assert "state=state-1" in url


def test_parse_authorization_response_validates_state() -> None:
    code = parse_authorization_response(
        "http://127.0.0.1:1455/auth/callback?code=abc&state=expected",
        expected_state="expected",
    )

    assert code == "abc"
    with pytest.raises(ProviderAuthError, match="state mismatch"):
        parse_authorization_response(
            "http://127.0.0.1:1455/auth/callback?code=abc&state=wrong",
            expected_state="expected",
        )


def test_auth_store_round_trips_profile(tmp_path: Path) -> None:
    settings = auth_settings(tmp_path)
    credential = OpenAICodexCredential(
        access="access-token",
        refresh="refresh-token",
        expires=int(time.time() * 1000) + 60_000,
        account_id="acct",
    )

    upsert_openai_codex_profile(settings, credential)

    loaded = get_openai_codex_profile(settings)
    assert loaded == credential
    assert list_openai_codex_profiles(settings)[0]["profile"] == "default"
    mode = (tmp_path / "profiles.json").stat().st_mode & 0o777
    assert mode == 0o600


def test_invalid_auth_store_json_fails_closed(tmp_path: Path) -> None:
    settings = auth_settings(tmp_path)
    (tmp_path / "profiles.json").write_text("{bad", encoding="utf-8")

    with pytest.raises(ProviderAuthError, match="Invalid provider auth store JSON"):
        get_openai_codex_profile(settings)


def test_refresh_serializes_and_reuses_written_token(tmp_path: Path, monkeypatch) -> None:
    settings = auth_settings(tmp_path)
    upsert_openai_codex_profile(
        settings,
        OpenAICodexCredential(
            access="expired",
            refresh="refresh",
            expires=int(time.time() * 1000) - 60_000,
        ),
    )
    calls = {"count": 0}

    def fake_exchange(refresh_token: str) -> OpenAICodexCredential:
        calls["count"] += 1
        time.sleep(0.05)
        assert refresh_token == "refresh"
        return OpenAICodexCredential(
            access="fresh",
            refresh="next-refresh",
            expires=int(time.time() * 1000) + 600_000,
        )

    monkeypatch.setattr(provider_auth, "exchange_refresh_token", fake_exchange)
    results: list[str] = []
    threads = [
        threading.Thread(target=lambda: results.append(refresh_openai_codex_profile(settings).access))
        for _ in range(2)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert calls["count"] == 1
    assert results == ["fresh", "fresh"]


def test_resolve_openai_text_bearer_refreshes_near_expiry_token(
    tmp_path: Path,
    monkeypatch,
) -> None:
    settings = auth_settings(tmp_path, openai_api_key="sk-should-not-be-used")
    upsert_openai_codex_profile(
        settings,
        OpenAICodexCredential(
            access="near-expiry-access",
            refresh="near-expiry-refresh",
            expires=int(time.time() * 1000) + 30_000,
        ),
    )

    def fake_exchange(refresh_token: str) -> OpenAICodexCredential:
        assert refresh_token == "near-expiry-refresh"
        return OpenAICodexCredential(
            access="fresh-short-lived-access",
            refresh="fresh-refresh",
            expires=int(time.time() * 1000) + 600_000,
        )

    monkeypatch.setattr(provider_auth, "exchange_refresh_token", fake_exchange)

    assert resolve_openai_text_bearer(settings) == "fresh-short-lived-access"
    stored = get_openai_codex_profile(settings)
    assert stored is not None
    assert stored.access == "fresh-short-lived-access"


def test_oauth_mode_does_not_fallback_to_openai_api_key_when_profile_missing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    settings = auth_settings(tmp_path, openai_api_key="sk-should-not-be-used")
    empty_codex_home = tmp_path / "empty-codex"
    empty_codex_home.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(empty_codex_home))

    with pytest.raises(ProviderAuthError, match="credentials are missing"):
        resolve_openai_text_bearer(settings)


def test_oauth_mode_never_reads_or_bootstraps_codex_cli_auth(
    tmp_path: Path,
    monkeypatch,
) -> None:
    codex_home = tmp_path / "codex"
    codex_home.mkdir()
    (codex_home / "auth.json").write_text(
        json.dumps(
            {
                "tokens": {
                    "access_token": jwt({"exp": int(time.time()) + 3600}),
                    "refresh_token": "external-refresh",
                    "account_id": "external",
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("CODEX_HOME", str(codex_home))
    settings = auth_settings(tmp_path, openai_api_key="sk-should-not-be-used")

    with pytest.raises(ProviderAuthError, match="credentials are missing"):
        resolve_openai_text_bearer(settings)
    assert get_openai_codex_profile(settings) is None


def test_api_key_mode_is_explicit(tmp_path: Path) -> None:
    settings = auth_settings(tmp_path, openai_auth_mode="api_key", openai_api_key="sk-test")

    assert resolve_openai_text_bearer(settings) == "sk-test"


def test_cli_status_reports_oauth_and_embedding_status(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                f"BRAIN_PROVIDER_AUTH_PROFILES_PATH={tmp_path / 'profiles.json'}",
                f"BRAIN_PROVIDER_AUTH_STATE_DIR={tmp_path / 'state'}",
                "OPENAI_AUTH_MODE=oauth",
                "OPENAI_API_KEY=sk-embedding",
            ]
        ),
        encoding="utf-8",
    )
    settings = auth_settings(tmp_path, openai_api_key="sk-embedding")
    upsert_openai_codex_profile(
        settings,
        OpenAICodexCredential(
            access="local-access",
            refresh="local-refresh",
            expires=int(time.time() * 1000) + 600_000,
        ),
    )

    result = runner.invoke(
        app,
        ["models", "auth", "status", "--provider", "openai-codex", "--env-file", str(env_file)],
    )

    assert result.exit_code == 0
    assert "openai text: OAuth profile default" in result.output
    assert "openai embedding: OPENAI_API_KEY configured" in result.output


def test_cli_list_reports_profiles(tmp_path: Path) -> None:
    env_file = write_auth_env(tmp_path)
    settings = auth_settings(tmp_path)
    upsert_openai_codex_profile(
        settings,
        OpenAICodexCredential(
            access="local-access",
            refresh="local-refresh",
            expires=int(time.time() * 1000) + 600_000,
        ),
    )

    result = runner.invoke(
        app,
        ["models", "auth", "list", "--provider", "openai-codex", "--env-file", str(env_file)],
    )

    assert result.exit_code == 0
    assert "OpenAI Codex OAuth Profiles" in result.output
    assert "default" in result.output
    assert "usable" in result.output


def test_cli_login_uses_auth_flow(tmp_path: Path, monkeypatch) -> None:
    env_file = write_auth_env(tmp_path)

    def fake_login(settings: Settings, *, manual: bool, timeout_seconds: int) -> OpenAICodexCredential:
        assert manual is True
        assert timeout_seconds == 7
        credential = OpenAICodexCredential(
            access="login-access",
            refresh="login-refresh",
            expires=int(time.time() * 1000) + 600_000,
        )
        upsert_openai_codex_profile(settings, credential)
        return credential

    monkeypatch.setattr(brain_cli, "login_openai_codex", fake_login)

    result = runner.invoke(
        app,
        [
            "models",
            "auth",
            "login",
            "--provider",
            "openai-codex",
            "--env-file",
            str(env_file),
            "--manual",
            "--timeout-seconds",
            "7",
        ],
    )

    assert result.exit_code == 0
    assert "Stored OpenAI Codex OAuth profile 'default'" in result.output
    assert get_openai_codex_profile(auth_settings(tmp_path)).access == "login-access"  # type: ignore[union-attr]


def test_cli_refresh_uses_token_sink_refresh(tmp_path: Path, monkeypatch) -> None:
    env_file = write_auth_env(tmp_path)

    def fake_refresh(settings: Settings) -> OpenAICodexCredential:
        credential = OpenAICodexCredential(
            access="fresh-access",
            refresh="fresh-refresh",
            expires=int(time.time() * 1000) + 600_000,
        )
        upsert_openai_codex_profile(settings, credential)
        return credential

    monkeypatch.setattr(brain_cli, "refresh_openai_codex_profile", fake_refresh)

    result = runner.invoke(
        app,
        ["models", "auth", "refresh", "--provider", "openai-codex", "--env-file", str(env_file)],
    )

    assert result.exit_code == 0
    assert "Refreshed OpenAI Codex OAuth profile 'default'" in result.output
    assert get_openai_codex_profile(auth_settings(tmp_path)).access == "fresh-access"  # type: ignore[union-attr]


def auth_settings(tmp_path: Path, **kwargs: Any) -> Settings:
    return Settings(
        brain_provider_auth_profiles_path=str(tmp_path / "profiles.json"),
        brain_provider_auth_state_dir=str(tmp_path / "state"),
        **kwargs,
    )


def write_auth_env(tmp_path: Path) -> Path:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                f"BRAIN_PROVIDER_AUTH_PROFILES_PATH={tmp_path / 'profiles.json'}",
                f"BRAIN_PROVIDER_AUTH_STATE_DIR={tmp_path / 'state'}",
                "OPENAI_AUTH_MODE=oauth",
                "OPENAI_API_KEY=sk-embedding",
            ]
        ),
        encoding="utf-8",
    )
    return env_file


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
