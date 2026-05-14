from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import backup_stores
import verify_mcp_production
from memory_stack.cfg import Settings
from memory_stack.taste.models import TasteRememberRequest
from memory_stack.taste.service import TasteService


def test_backup_sqlite_includes_cognee_db_without_extension(tmp_path) -> None:
    data_root = tmp_path / "shared" / "data"
    db_path = data_root / "system" / "databases" / "cognee_db"
    db_path.parent.mkdir(parents=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY)")
        conn.execute("INSERT INTO items DEFAULT VALUES")

    manifest = {"sqlite": [], "blockers": []}
    run_dir = tmp_path / "backup"
    run_dir.mkdir()

    backup_stores.backup_sqlite(data_root, run_dir, manifest)

    assert manifest["blockers"] == []
    assert len(manifest["sqlite"]) == 1
    entry = manifest["sqlite"][0]
    assert entry["source"] == str(db_path)
    assert entry["integrity_check"] == "ok"
    assert Path(entry["backup"]).name == "system__databases__cognee_db"


def test_backup_sqlite_includes_brain_taste_tables(tmp_path) -> None:
    data_root = tmp_path / "shared" / "data"
    brain_db = data_root / "brain" / "brain.db"
    brain_db.parent.mkdir(parents=True)
    settings = Settings(brain_database_url=f"sqlite:///{brain_db}")
    TasteService(settings).remember(
        TasteRememberRequest(
            type="wine",
            canonical_name="Backup Wine",
            description="Backup Wine is rated 8/10.",
            rating=8,
            fetch_external_ratings=False,
        )
    )
    proposal = TasteService(settings).create_proposal_from_text("Alex recommended Mystery Thing.")
    TasteService(settings).cancel(proposal["id"])
    manifest = {"sqlite": [], "blockers": []}
    run_dir = tmp_path / "backup"
    run_dir.mkdir()

    backup_stores.backup_sqlite(data_root, run_dir, manifest)

    brain_entry = next(entry for entry in manifest["sqlite"] if entry["source"] == str(brain_db))
    with sqlite3.connect(brain_entry["backup"]) as conn:
        count = conn.execute("SELECT COUNT(*) FROM taste_items").fetchone()[0]
        proposal_status = conn.execute("SELECT status FROM taste_proposals").fetchone()[0]
    assert count == 1
    assert proposal_status == "cancelled"


def test_backup_raw_data_and_secrets_archives(tmp_path, monkeypatch) -> None:
    data_dir = tmp_path / "shared" / "data" / "data"
    data_dir.mkdir(parents=True)
    (data_dir / "memory.txt").write_text("remember this", encoding="utf-8")

    secrets_dir = tmp_path / "shared" / "secrets"
    secrets_dir.mkdir(parents=True)
    env_file = secrets_dir / "brain.env"
    password_file = secrets_dir / "brain-auth-password"
    state_file = secrets_dir / "brain-oauth.json"
    env_file.write_text("PROFILE=openai\n", encoding="utf-8")
    password_file.write_text("secret\n", encoding="utf-8")
    state_file.write_text("{}\n", encoding="utf-8")
    monkeypatch.setenv("ENV_FILE", str(env_file))

    settings = SimpleNamespace(
        brain_auth_password_file=str(password_file),
        brain_auth_state_path=str(state_file),
    )
    manifest = {"raw_data": [], "secrets": [], "blockers": []}
    run_dir = tmp_path / "backup"
    run_dir.mkdir()

    backup_stores.backup_raw_data(data_dir, run_dir, manifest)
    backup_stores.backup_secrets(settings, run_dir, manifest)

    assert Path(manifest["raw_data"][0]["archive"]).exists()
    secrets_archive = Path(manifest["secrets"][0]["archive"])
    assert secrets_archive.exists()
    assert secrets_archive.stat().st_mode & 0o777 == 0o600


def test_verify_backups_requires_critical_artifacts(tmp_path) -> None:
    backup_dir = tmp_path / "backups"
    run_dir = backup_dir / "20260504_120000"
    for name in ("sqlite", "raw_data", "lancedb", "secrets"):
        (run_dir / name).mkdir(parents=True, exist_ok=True)
    main_db_backup = run_dir / "sqlite" / "system__databases__cognee_db"
    raw_archive = run_dir / "raw_data" / "data.tar.gz"
    lancedb_archive = run_dir / "lancedb" / "cognee.lancedb.tar.gz"
    secrets_archive = run_dir / "secrets" / "secrets.tar.gz"
    for path in (main_db_backup, raw_archive, lancedb_archive, secrets_archive):
        path.write_text("backup", encoding="utf-8")

    manifest = {
        "blockers": [],
        "sqlite": [
            {
                "source": "/prod/shared/data/system/databases/cognee_db",
                "backup": str(main_db_backup),
                "integrity_check": "ok",
            }
        ],
        "raw_data": [{"archive": str(raw_archive)}],
        "lancedb": [{"archive": str(lancedb_archive)}],
        "secrets": [{"archive": str(secrets_archive)}],
        "neo4j": [{"method": "cypher_count_check", "verified": True}],
        "google_drive": {"verified": True},
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    settings = SimpleNamespace(
        system_root_directory="/prod/shared/data/system",
        brain_google_drive_backup_enabled=True,
    )
    failures: list[str] = []

    verify_mcp_production.check_backups(backup_dir, settings, failures)

    assert failures == []


def test_verify_backups_rejects_missing_main_cognee_db(tmp_path) -> None:
    backup_dir = tmp_path / "backups"
    run_dir = backup_dir / "20260504_120000"
    run_dir.mkdir(parents=True)
    (run_dir / "manifest.json").write_text(
        json.dumps(
            {
                "blockers": [],
                "sqlite": [],
                "raw_data": [],
                "lancedb": [],
                "secrets": [],
                "neo4j": [],
                "google_drive": {"verified": False},
            }
        ),
        encoding="utf-8",
    )
    settings = SimpleNamespace(
        system_root_directory="/prod/shared/data/system",
        brain_google_drive_backup_enabled=True,
    )
    failures: list[str] = []

    verify_mcp_production.check_backups(backup_dir, settings, failures)

    assert any("main Cognee DB" in failure for failure in failures)


def test_verify_backups_uses_configured_db_name(tmp_path) -> None:
    backup_dir = tmp_path / "backups"
    run_dir = backup_dir / "20260504_120000"
    for name in ("sqlite", "raw_data", "lancedb", "secrets"):
        (run_dir / name).mkdir(parents=True, exist_ok=True)
    main_db_backup = run_dir / "sqlite" / "system__databases__custom_cognee"
    raw_archive = run_dir / "raw_data" / "data.tar.gz"
    lancedb_archive = run_dir / "lancedb" / "cognee.lancedb.tar.gz"
    secrets_archive = run_dir / "secrets" / "secrets.tar.gz"
    for path in (main_db_backup, raw_archive, lancedb_archive, secrets_archive):
        path.write_text("backup", encoding="utf-8")

    manifest = {
        "blockers": [],
        "sqlite": [
            {
                "source": "/prod/shared/data/system/databases/custom_cognee",
                "backup": str(main_db_backup),
                "integrity_check": "ok",
            }
        ],
        "raw_data": [{"archive": str(raw_archive)}],
        "lancedb": [{"archive": str(lancedb_archive)}],
        "secrets": [{"archive": str(secrets_archive)}],
        "neo4j": [{"method": "cypher_count_check", "verified": True}],
        "google_drive": {"verified": False},
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    settings = SimpleNamespace(
        system_root_directory="/prod/shared/data/system",
        db_name="custom_cognee",
        brain_google_drive_backup_enabled=False,
    )
    failures: list[str] = []

    verify_mcp_production.check_backups(backup_dir, settings, failures)

    assert failures == []
