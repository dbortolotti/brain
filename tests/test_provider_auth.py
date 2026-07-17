from __future__ import annotations

import base64
import json
import threading
import time
import urllib.parse
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

import memory_stack.brain_cli as brain_cli
from memory_stack.brain_cli import app
from memory_stack.cfg import Settings
from memory_stack import provider_auth
from memory_stack.provider_auth import (
    OpenAICodexCredential,
    ProviderAuthError,
    build_openai_codex_authorize_url,
    exchange_authorization_code,
    generate_pkce_pair,
    get_codex_cli_access_token,
    get_openai_codex_profile,
    list_openai_codex_profiles,
    openai_embeddings_base_url,
    parse_authorization_response,
    refresh_openai_codex_profile,
    resolve_openai_text_bearer,
    upsert_openai_codex_profile,
)


runner = CliRunner()


def test_pkce_generation_and_authorize_url() -> None:
    pkce = generate_pkce_pair()
    url = build_openai_codex_authorize_url(state="state-1", challenge=pkce.challenge)
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)

    assert pkce.verifier
    assert pkce.challenge
    assert (parsed.scheme, parsed.netloc, parsed.path) == (
        "https",
        "auth.openai.com",
        "/oauth/authorize",
    )
    assert query == {
        "response_type": ["code"],
        "client_id": ["app_EMoamEEZ73f0CkXaXp7hrann"],
        "redirect_uri": ["http://localhost:1455/auth/callback"],
        "scope": [
            "openid profile email offline_access "
            "api.connectors.read api.connectors.invoke"
        ],
        "code_challenge": [pkce.challenge],
        "code_challenge_method": ["S256"],
        "id_token_add_organizations": ["true"],
        "codex_cli_simplified_flow": ["true"],
        "originator": ["codex_cli_rs"],
        "state": ["state-1"],
    }


def test_parse_authorization_response_validates_state() -> None:
    code = parse_authorization_response(
        "http://localhost:1455/auth/callback?code=abc&state=expected",
        expected_state="expected",
    )

    assert code == "abc"
    with pytest.raises(ProviderAuthError, match="state mismatch"):
        parse_authorization_response(
            "http://localhost:1455/auth/callback?code=abc&state=wrong",
            expected_state="expected",
        )


def test_exchange_authorization_code_uses_selected_redirect(monkeypatch) -> None:
    request: dict[str, Any] = {}

    def fake_post(url: str, *, data: dict[str, str], timeout: int):
        request.update(url=url, data=data, timeout=timeout)
        return provider_auth.httpx.Response(
            200,
            json={
                "access_token": "access-token",
                "refresh_token": "refresh-token",
                "expires_in": 3600,
            },
        )

    monkeypatch.setattr(provider_auth.httpx, "post", fake_post)

    credential = exchange_authorization_code(
        "authorization-code",
        "verifier",
        redirect_uri="http://localhost:1457/auth/callback",
    )

    assert credential.access == "access-token"
    assert request["url"] == provider_auth.OPENAI_CODEX_TOKEN_URL
    assert request["timeout"] == 60
    assert request["data"]["redirect_uri"] == "http://localhost:1457/auth/callback"


def test_local_browser_callback_falls_back_to_allowlisted_port(monkeypatch) -> None:
    attempted_ports: list[int] = []
    opened_urls: list[str] = []

    class FakeServer:
        def handle_request(self) -> None:
            return

        def server_close(self) -> None:
            return

    def fake_server(address: tuple[str, int], _handler):
        attempted_ports.append(address[1])
        if address[1] == 1455:
            raise OSError("port in use")
        return FakeServer()

    monkeypatch.setattr(provider_auth.http.server, "ThreadingHTTPServer", fake_server)
    monkeypatch.setattr(provider_auth.webbrowser, "open", opened_urls.append)

    code, redirect_uri = provider_auth.try_local_browser_callback(
        expected_state="state-1",
        challenge="challenge-1",
        timeout_seconds=0,
    )

    assert code is None
    assert redirect_uri == "http://localhost:1457/auth/callback"
    assert attempted_ports == [1455, 1457]
    query = urllib.parse.parse_qs(urllib.parse.urlparse(opened_urls[0]).query)
    assert query["redirect_uri"] == ["http://localhost:1457/auth/callback"]


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


def test_resolve_openai_text_bearer_prefers_usable_codex_cli_before_local_refresh(
    tmp_path: Path,
    monkeypatch,
) -> None:
    codex_home = tmp_path / "codex"
    codex_home.mkdir()
    cli_access = jwt({"exp": int(time.time()) + 3600})
    (codex_home / "auth.json").write_text(
        json.dumps({"tokens": {"access_token": cli_access, "refresh_token": "external-refresh"}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("CODEX_HOME", str(codex_home))
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
        raise AssertionError(f"Brain OAuth profile must not refresh before usable Codex CLI token: {refresh_token}")

    monkeypatch.setattr(provider_auth, "exchange_refresh_token", fake_exchange)

    assert resolve_openai_text_bearer(settings) == cli_access
    stored = get_openai_codex_profile(settings)
    assert stored is not None
    assert stored.access == "near-expiry-access"


def test_resolve_openai_text_bearer_refreshes_near_expiry_local_token_when_codex_unavailable(
    tmp_path: Path,
    monkeypatch,
) -> None:
    empty_codex_home = tmp_path / "empty-codex"
    empty_codex_home.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(empty_codex_home))
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


def test_oauth_mode_uses_usable_codex_cli_access_token_without_bootstrapping(
    tmp_path: Path,
    monkeypatch,
) -> None:
    codex_home = tmp_path / "codex"
    codex_home.mkdir()
    access = jwt({"exp": int(time.time()) + 3600})
    (codex_home / "auth.json").write_text(
        json.dumps(
            {
                "tokens": {
                    "access_token": access,
                    "refresh_token": "external-refresh",
                    "account_id": "external",
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("CODEX_HOME", str(codex_home))
    settings = auth_settings(tmp_path, openai_api_key="sk-should-not-be-used")

    assert resolve_openai_text_bearer(settings) == access
    assert get_openai_codex_profile(settings) is None


def test_oauth_mode_does_not_refresh_expired_codex_cli_token(
    tmp_path: Path,
    monkeypatch,
) -> None:
    codex_home = tmp_path / "codex"
    codex_home.mkdir()
    (codex_home / "auth.json").write_text(
        json.dumps(
            {
                "tokens": {
                    "access_token": jwt({"exp": int(time.time()) - 60}),
                    "refresh_token": "external-refresh",
                    "account_id": "external",
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("CODEX_HOME", str(codex_home))

    def fake_exchange(refresh_token: str) -> OpenAICodexCredential:
        raise AssertionError(f"Codex CLI refresh token must not be refreshed: {refresh_token}")

    monkeypatch.setattr(provider_auth, "exchange_refresh_token", fake_exchange)
    settings = auth_settings(tmp_path, openai_api_key="sk-should-not-be-used")

    with pytest.raises(ProviderAuthError, match="credentials are missing"):
        resolve_openai_text_bearer(settings)
    assert get_openai_codex_profile(settings) is None


def test_expired_codex_cli_token_falls_back_to_refreshing_local_profile(
    tmp_path: Path,
    monkeypatch,
) -> None:
    codex_home = tmp_path / "codex"
    codex_home.mkdir()
    (codex_home / "auth.json").write_text(
        json.dumps({"tokens": {"access_token": jwt({"exp": int(time.time()) - 60}), "refresh_token": "external-refresh"}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("CODEX_HOME", str(codex_home))
    settings = auth_settings(tmp_path, openai_api_key="sk-should-not-be-used")
    upsert_openai_codex_profile(
        settings,
        OpenAICodexCredential(
            access="expired-local",
            refresh="local-refresh",
            expires=int(time.time() * 1000) - 60_000,
        ),
    )

    def fake_exchange(refresh_token: str) -> OpenAICodexCredential:
        assert refresh_token == "local-refresh"
        return OpenAICodexCredential(
            access="fresh-local",
            refresh="next-local-refresh",
            expires=int(time.time() * 1000) + 600_000,
        )

    monkeypatch.setattr(provider_auth, "exchange_refresh_token", fake_exchange)

    assert resolve_openai_text_bearer(settings) == "fresh-local"


def test_codex_cli_access_token_requires_unexpired_jwt(tmp_path: Path, monkeypatch) -> None:
    codex_home = tmp_path / "codex"
    codex_home.mkdir()
    (codex_home / "auth.json").write_text(
        json.dumps({"tokens": {"access_token": "not-a-jwt", "refresh_token": "external-refresh"}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("CODEX_HOME", str(codex_home))

    assert get_codex_cli_access_token() is None


def test_api_key_mode_is_explicit(tmp_path: Path) -> None:
    settings = auth_settings(tmp_path, openai_auth_mode="api_key", openai_api_key="sk-test")

    assert resolve_openai_text_bearer(settings) == "sk-test"


def test_oauth_mode_uses_token_sink_client_file(tmp_path: Path, monkeypatch) -> None:
    empty_codex_home = tmp_path / "empty-codex"
    empty_codex_home.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(empty_codex_home))
    token_file = tmp_path / "client_token"
    token_file.write_text("sink-client-token\n", encoding="utf-8")
    settings = auth_settings(
        tmp_path,
        openai_auth_mode="oauth",
        openai_codex_base_url="http://127.0.0.1:11434/v1",
        openai_token_sink_client_token_file=str(token_file),
    )

    assert resolve_openai_text_bearer(settings) == "sink-client-token"
    assert openai_embeddings_base_url(settings) == "http://127.0.0.1:11434/v1"


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
    assert "openai embedding: OAuth profile default" in result.output


def test_cli_status_reports_token_sink_client(tmp_path: Path) -> None:
    token_file = tmp_path / "client_token"
    token_file.write_text("sink-client-token\n", encoding="utf-8")
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                f"BRAIN_PROVIDER_AUTH_PROFILES_PATH={tmp_path / 'profiles.json'}",
                f"BRAIN_PROVIDER_AUTH_STATE_DIR={tmp_path / 'state'}",
                "OPENAI_AUTH_MODE=oauth",
                "OPENAI_CODEX_BASE_URL=http://127.0.0.1:11434/v1",
                f"OPENAI_TOKEN_SINK_CLIENT_TOKEN_FILE={token_file}",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["models", "auth", "status", "--provider", "openai-codex", "--env-file", str(env_file)],
    )

    assert result.exit_code == 0
    assert "openai text: token sink client configured" in result.output
    assert "openai embedding: token sink client configured" in result.output
    assert "sink-client-token" not in result.output


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
