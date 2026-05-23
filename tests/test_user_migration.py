from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import migrate_default_user_to_daniele
import migrate_auth_user_passwords
import migrate_user_scoped_data
from memory_stack.brain_store import BrainStore
from memory_stack.cfg import Settings
from memory_stack.oauth import ensure_auth_password, load_auth_users, verify_password
from memory_stack.profile_context import list_profile_context, remember_profile_context


def test_auth_users_file_is_required_when_configured(tmp_path: Path) -> None:
    settings = Settings(
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


def test_migrate_auth_user_passwords_rewrites_legacy_passwords(
    tmp_path: Path,
    monkeypatch,
) -> None:
    env_file = tmp_path / "brain.env"
    auth_password_file = tmp_path / "brain-auth-password"
    auth_users_file = tmp_path / "brain-auth-users.json"
    auth_password_file.write_text("fallback-pass\n", encoding="utf-8")
    auth_users_file.write_text(
        json.dumps([{"id": "daniele", "password": "pass-a", "display_name": "Daniele"}]),
        encoding="utf-8",
    )
    env_file.write_text(
        "\n".join(
            [
                f"BRAIN_AUTH_PASSWORD_FILE={auth_password_file}",
                f"BRAIN_AUTH_USERS_FILE={auth_users_file}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        sys,
        "argv",
        ["migrate_auth_user_passwords.py", "--env-file", str(env_file), "--check"],
    )
    assert migrate_auth_user_passwords.main() == 1

    monkeypatch.setattr(
        sys,
        "argv",
        ["migrate_auth_user_passwords.py", "--env-file", str(env_file)],
    )
    assert migrate_auth_user_passwords.main() == 0

    stored = json.loads(auth_users_file.read_text(encoding="utf-8"))
    assert stored[0]["password_scheme"] == "argon2id"
    assert "password" not in stored[0]
    assert stored[0]["password_hash"].startswith("$argon2id$")
    assert verify_password("pass-a", stored[0])

    monkeypatch.setattr(
        sys,
        "argv",
        ["migrate_auth_user_passwords.py", "--env-file", str(env_file), "--check"],
    )
    assert migrate_auth_user_passwords.main() == 0


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
    BrainStore(settings).create_external_receipt(
        surface="test",
        tool_name="brain_remember",
        action="remember",
        status="synced",
        summary="Default-scoped Cognee receipt should move.",
        cognee_dataset="memory",
        cognee_reference="cognee-default",
        metadata_json={"semantic_store": "cognee"},
    )
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
    assert [
        receipt["summary"]
        for receipt in BrainStore(daniele_settings).list_external_receipts()
    ] == ["Default-scoped Cognee receipt should move."]
    assert BrainStore(default_settings).list_external_receipts() == []
    assert list_profile_context(daniele_settings)
    assert list_profile_context(default_settings) == []

    users = json.loads(auth_users_file.read_text(encoding="utf-8"))
    assert {record["id"]: record["superuser"] for record in users} == {
        "daniele": False,
        "default": True,
    }
    daniele_user = next(record for record in users if record["id"] == "daniele")
    root_user = next(record for record in users if record["id"] == "default")
    assert "password" not in daniele_user
    assert "password" not in root_user
    assert verify_password("daniele-pass", daniele_user)
    assert verify_password(root_password_path.read_text(encoding="utf-8").strip(), root_user)
    state = json.loads(oauth_state_path.read_text(encoding="utf-8"))
    assert state["clients"] == {"client": {"client_id": "client"}}
    assert state["access_tokens"] == {}
    assert state["refresh_tokens"] == {}


def test_migrate_user_scoped_data_only_moves_database_rows(
    tmp_path: Path,
    monkeypatch,
) -> None:
    env_file = tmp_path / "brain.env"
    db_path = tmp_path / "brain.db"
    profile_context_path = tmp_path / "profile_context.json"
    profile_context_path.write_text("[]\n", encoding="utf-8")
    env_file.write_text(
        "\n".join(
            [
                f"BRAIN_DATABASE_URL=sqlite:///{db_path}",
                f"BRAIN_PROFILE_CONTEXT_PATH={profile_context_path}",
                "BRAIN_USER_ID=default",
                "BRAIN_OWNER_NAME=Daniele",
                "BRAIN_OWNER_FULL_NAME=Daniele Bortolotti",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    default_settings = Settings(
        brain_database_url=f"sqlite:///{db_path}",
        brain_profile_context_path=str(profile_context_path),
        brain_user_id="default",
        brain_owner_name="Daniele",
        brain_owner_full_name="Daniele Bortolotti",
    )
    daniele_settings = Settings(
        brain_database_url=f"sqlite:///{db_path}",
        brain_profile_context_path=str(profile_context_path),
        brain_user_id="daniele",
        brain_owner_name="Daniele",
        brain_owner_full_name="Daniele Bortolotti",
    )
    BrainStore(default_settings).create_external_receipt(
        surface="test",
        tool_name="brain_remember",
        action="remember",
        status="synced",
        summary="Default-scoped receipt should move.",
        cognee_dataset="memory",
        cognee_reference="cognee-default",
        metadata_json={"semantic_store": "cognee"},
    )
    BrainStore(daniele_settings).create_external_receipt(
        surface="test",
        tool_name="brain_remember",
        action="remember",
        status="synced",
        summary="Daniele-scoped receipt should stay.",
        cognee_dataset="memory",
        cognee_reference="cognee-daniele",
        metadata_json={"semantic_store": "cognee"},
    )
    BrainStore(default_settings).create_context_record(
        kind="bias",
        statement="Default-scoped bias should move.",
        scope="response_style",
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "migrate_user_scoped_data.py",
            "--env-file",
            str(env_file),
            "--env",
            "prod",
            "--from-user",
            "default",
            "--to-user",
            "daniele",
            "--allow-target-existing",
            "--apply",
        ],
    )
    assert migrate_user_scoped_data.main() == 0

    assert BrainStore(default_settings).list_external_receipts() == []
    assert BrainStore(default_settings).list_context_records(kind="bias") == []
    daniele_receipts = BrainStore(daniele_settings).list_external_receipts()
    summaries = {receipt["summary"] for receipt in daniele_receipts}
    assert summaries == {
        "Default-scoped receipt should move.",
        "Daniele-scoped receipt should stay.",
    }
    assert [
        record["statement"]
        for record in BrainStore(daniele_settings).list_context_records(kind="bias")
    ] == ["Default-scoped bias should move."]
    assert profile_context_path.read_text(encoding="utf-8") == "[]\n"
