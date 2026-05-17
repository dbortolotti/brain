from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import migrate_default_user_to_daniele
from memory_stack.brain_service import RecallRequest, RememberRequest, recall, remember
from memory_stack.cfg import Settings
from memory_stack.oauth import ensure_auth_password, load_auth_users
from memory_stack.profile_context import list_profile_context, remember_profile_context


def test_auth_users_file_is_required_when_configured(tmp_path: Path) -> None:
    settings = Settings(
        brain_auth_enabled=True,
        brain_auth_password_file=str(tmp_path / "brain-auth-password"),
        brain_auth_users_file=str(tmp_path / "missing-users.json"),
    )

    password = ensure_auth_password(settings)

    try:
        load_auth_users(settings, default_password=password)
    except FileNotFoundError as exc:
        assert "missing-users.json" in str(exc)
    else:
        raise AssertionError("missing BRAIN_AUTH_USERS_FILE should fail closed")


def test_migrate_default_user_to_daniele_moves_data_and_creates_root_registry(
    tmp_path: Path,
    monkeypatch,
) -> None:
    env_file = tmp_path / "brain.env"
    db_path = tmp_path / "brain.db"
    auth_password_file = tmp_path / "brain-auth-password"
    auth_users_file = tmp_path / "brain-auth-users.json"
    profile_context_path = tmp_path / "profile_context.json"
    oauth_state_path = tmp_path / "brain-oauth.json"
    root_password_path = tmp_path / "brain-auth-root-password"
    auth_password_file.write_text("daniele-pass\n", encoding="utf-8")
    profile_context_path.write_text("[]\n", encoding="utf-8")
    oauth_state_path.write_text(
        json.dumps(
            {
                "clients": {"client": {"client_id": "client"}},
                "pending_authorizations": {"pending": {}},
                "authorization_codes": {"code": {}},
                "access_tokens": {"access": {"user_id": "default"}},
                "refresh_tokens": {"refresh": {"user_id": "default"}},
            }
        ),
        encoding="utf-8",
    )
    env_file.write_text(
        "\n".join(
            [
                f"BRAIN_DATABASE_URL=sqlite:///{db_path}",
                f"BRAIN_AUTH_PASSWORD_FILE={auth_password_file}",
                f"BRAIN_AUTH_USERS_FILE={auth_users_file}",
                f"BRAIN_AUTH_STATE_PATH={oauth_state_path}",
                f"BRAIN_PROFILE_CONTEXT_PATH={profile_context_path}",
                "BRAIN_USER_ID=default",
                "BRAIN_OWNER_NAME=Daniele",
                "BRAIN_OWNER_FULL_NAME=Daniele Bortolotti",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("ENV_FILE", str(env_file))

    settings = Settings(
        brain_database_url=f"sqlite:///{db_path}",
        brain_auth_password_file=str(auth_password_file),
        brain_auth_users_file=str(auth_users_file),
        brain_auth_state_path=str(oauth_state_path),
        brain_profile_context_path=str(profile_context_path),
        brain_user_id="default",
        brain_owner_name="Daniele",
        brain_owner_full_name="Daniele Bortolotti",
    )
    remember(RememberRequest(input="Daniele likes user migrations."), settings)
    remember_profile_context(settings, statement="Daniele works with Brain.", scope="work")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "migrate_default_user_to_daniele.py",
            "--apply",
            "--root-password-file",
            str(root_password_path),
        ],
    )
    assert migrate_default_user_to_daniele.main() == 0

    daniele_settings = Settings(
        brain_database_url=f"sqlite:///{db_path}",
        brain_profile_context_path=str(profile_context_path),
        brain_user_id="daniele",
    )
    default_settings = Settings(
        brain_database_url=f"sqlite:///{db_path}",
        brain_profile_context_path=str(profile_context_path),
        brain_user_id="default",
    )
    assert recall(RecallRequest(query="user migrations"), daniele_settings).facts
    assert recall(RecallRequest(query="user migrations"), default_settings).facts == []
    assert list_profile_context(daniele_settings)
    assert list_profile_context(default_settings) == []

    users = json.loads(auth_users_file.read_text(encoding="utf-8"))
    assert {record["id"]: record["superuser"] for record in users} == {
        "daniele": False,
        "default": True,
    }
    assert next(record for record in users if record["id"] == "daniele")["password"] == "daniele-pass"
    assert next(record for record in users if record["id"] == "default")["password"] == root_password_path.read_text(
        encoding="utf-8"
    ).strip()
    state = json.loads(oauth_state_path.read_text(encoding="utf-8"))
    assert state["clients"] == {"client": {"client_id": "client"}}
    assert state["access_tokens"] == {}
    assert state["refresh_tokens"] == {}
