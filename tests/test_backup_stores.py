from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import tarfile
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
    data_dir = tmp_path / "shared" / "data"
    data_dir.mkdir(parents=True)
    (data_dir / "data").mkdir()
    (data_dir / "data" / "memory.txt").write_text("remember this", encoding="utf-8")
    (data_dir / "brain").mkdir()
    (data_dir / "brain" / "profile_context.json").write_text("[]\n", encoding="utf-8")

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
    with tarfile.open(manifest["raw_data"][0]["archive"], "r:gz") as tar:
        assert "data/brain/profile_context.json" in tar.getnames()
    secrets_archive = Path(manifest["secrets"][0]["archive"])
    assert secrets_archive.exists()
    assert secrets_archive.stat().st_mode & 0o777 == 0o600


def test_backup_neo4j_uses_configured_docker_container(tmp_path, monkeypatch) -> None:
    data_root = tmp_path / "shared" / "data"
    (data_root / "neo4j").mkdir(parents=True)
    run_dir = tmp_path / "backup"
    run_dir.mkdir()
    manifest = {"neo4j": [], "blockers": []}
    settings = SimpleNamespace(
        brain_neo4j_dump_enabled=True,
        brain_neo4j_docker_container="brain-prod-neo4j",
        brain_neo4j_stop_for_dump=False,
    )
    observed_commands: list[list[str]] = []

    monkeypatch.setattr(backup_stores, "neo4j_graph_counts", lambda _settings: None)
    monkeypatch.setattr(backup_stores.shutil, "which", lambda name: "/usr/bin/docker" if name == "docker" else None)

    def fake_run(cmd, **kwargs):
        observed_commands.append(cmd)
        (run_dir / "neo4j").mkdir(exist_ok=True)
        (run_dir / "neo4j" / "neo4j.dump").write_text("dump", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

    monkeypatch.setattr(backup_stores.subprocess, "run", fake_run)

    backup_stores.backup_neo4j(settings, data_root, run_dir, manifest)

    assert observed_commands[0][2] == "brain-prod-neo4j"
    assert manifest["neo4j"][0]["verified"] is True
    assert (run_dir / "neo4j" / "neo4j.dump").exists()


def test_backup_neo4j_stops_docker_container_for_consistent_dump(tmp_path, monkeypatch) -> None:
    data_root = tmp_path / "shared" / "data"
    data_root.mkdir(parents=True)
    docker_data = tmp_path / "shared" / "docker" / "neo4j" / "data"
    docker_data.mkdir(parents=True)
    run_dir = tmp_path / "backup"
    run_dir.mkdir()
    manifest = {"neo4j": [], "blockers": []}
    settings = SimpleNamespace(
        brain_neo4j_dump_enabled=True,
        brain_neo4j_docker_container="brain-prod-neo4j",
        brain_neo4j_stop_for_dump=True,
    )
    observed_commands: list[list[str]] = []

    monkeypatch.setattr(backup_stores, "neo4j_graph_counts", lambda _settings: None)
    monkeypatch.setattr(backup_stores.shutil, "which", lambda name: "/usr/bin/docker" if name == "docker" else None)

    def fake_run(cmd, **kwargs):
        observed_commands.append(cmd)
        if cmd[:2] == ["docker", "inspect"]:
            payload = [
                {
                    "Config": {"Image": "neo4j:5-community"},
                    "Mounts": [{"Destination": "/data", "Source": str(docker_data)}],
                }
            ]
            return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(payload), stderr="")
        if cmd[:2] == ["docker", "run"]:
            (run_dir / "neo4j").mkdir(exist_ok=True)
            (run_dir / "neo4j" / "neo4j.dump").write_text("dump", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

    monkeypatch.setattr(backup_stores.subprocess, "run", fake_run)

    backup_stores.backup_neo4j(settings, data_root, run_dir, manifest)

    assert [cmd[:2] for cmd in observed_commands] == [
        ["docker", "inspect"],
        ["docker", "stop"],
        ["docker", "run"],
        ["docker", "start"],
    ]
    run_command = observed_commands[2]
    assert f"{docker_data}:/data" in run_command
    assert f"{run_dir / 'neo4j'}:/backup" in run_command
    assert manifest["neo4j"][0]["verified"] is True


def test_backup_pgvector_uses_docker_pg_dump(tmp_path, monkeypatch) -> None:
    calls = []

    class Result:
        returncode = 0
        stdout = "pg dump"
        stderr = ""

    def fake_run(command, **kwargs):
        calls.append({"command": command, **kwargs})
        return Result()

    monkeypatch.setattr(backup_stores.shutil, "which", lambda name: "/usr/bin/docker")
    monkeypatch.setattr(backup_stores.subprocess, "run", fake_run)
    settings = SimpleNamespace(db_username="cognee", db_name="cognee_db")
    manifest = {"pgvector": [], "blockers": []}
    run_dir = tmp_path / "backup"
    run_dir.mkdir()

    backup_stores.backup_pgvector(settings, run_dir, manifest)

    assert calls[0]["command"] == [
        "docker",
        "exec",
        "brain-prod-postgres",
        "pg_dump",
        "-U",
        "cognee",
        "-d",
        "cognee_db",
    ]
    assert manifest["pgvector"][0]["verified"] is True
    assert Path(manifest["pgvector"][0]["dump"]).read_text(encoding="utf-8") == "pg dump"


def test_verify_backups_requires_critical_artifacts(tmp_path) -> None:
    backup_dir = tmp_path / "backups"
    run_dir = backup_dir / "20260504_120000"
    for name in ("sqlite", "raw_data", "lancedb", "secrets"):
        (run_dir / name).mkdir(parents=True, exist_ok=True)
    main_db_backup = run_dir / "sqlite" / "system__databases__cognee_db"
    raw_archive = run_dir / "raw_data" / "data.tar.gz"
    lancedb_archive = run_dir / "lancedb" / "cognee.lancedb.tar.gz"
    secrets_archive = run_dir / "secrets" / "secrets.tar.gz"
    for path in (main_db_backup, lancedb_archive, secrets_archive):
        path.write_text("backup", encoding="utf-8")
    profile_context = tmp_path / "prod" / "shared" / "data" / "brain" / "profile_context.json"
    profile_context.parent.mkdir(parents=True)
    profile_context.write_text("[]\n", encoding="utf-8")
    with tarfile.open(raw_archive, "w:gz") as tar:
        tar.add(profile_context.parent.parent, arcname="data")

    manifest = {
        "blockers": [],
        "sqlite": [
            {
                "source": "/prod/shared/data/system/databases/cognee_db",
                "backup": str(main_db_backup),
                "integrity_check": "ok",
            }
        ],
        "raw_data": [
            {
                "source": str(profile_context.parent.parent),
                "archive": str(raw_archive),
            }
        ],
        "lancedb": [{"archive": str(lancedb_archive)}],
        "secrets": [{"archive": str(secrets_archive)}],
        "neo4j": [{"method": "cypher_count_check", "verified": True}],
        "google_drive": {"verified": True},
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    settings = SimpleNamespace(
        system_root_directory="/prod/shared/data/system",
        db_provider="sqlite",
        vector_db_provider="lancedb",
        brain_profile_context_path=str(profile_context),
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
        db_provider="sqlite",
        vector_db_provider="lancedb",
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
    for path in (main_db_backup, lancedb_archive, secrets_archive):
        path.write_text("backup", encoding="utf-8")
    profile_context = tmp_path / "prod" / "shared" / "data" / "brain" / "profile_context.json"
    profile_context.parent.mkdir(parents=True)
    profile_context.write_text("[]\n", encoding="utf-8")
    with tarfile.open(raw_archive, "w:gz") as tar:
        tar.add(profile_context.parent.parent, arcname="data")

    manifest = {
        "blockers": [],
        "sqlite": [
            {
                "source": "/prod/shared/data/system/databases/custom_cognee",
                "backup": str(main_db_backup),
                "integrity_check": "ok",
            }
        ],
        "raw_data": [
            {
                "source": str(profile_context.parent.parent),
                "archive": str(raw_archive),
            }
        ],
        "lancedb": [{"archive": str(lancedb_archive)}],
        "secrets": [{"archive": str(secrets_archive)}],
        "neo4j": [{"method": "cypher_count_check", "verified": True}],
        "google_drive": {"verified": False},
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    settings = SimpleNamespace(
        system_root_directory="/prod/shared/data/system",
        db_name="custom_cognee",
        db_provider="sqlite",
        vector_db_provider="lancedb",
        brain_profile_context_path=str(profile_context),
        brain_google_drive_backup_enabled=False,
    )
    failures: list[str] = []

    verify_mcp_production.check_backups(backup_dir, settings, failures)

    assert failures == []


def test_verify_backups_accepts_pgvector_instead_of_lancedb(tmp_path) -> None:
    backup_dir = tmp_path / "backups"
    run_dir = backup_dir / "20260504_120000"
    for name in ("sqlite", "raw_data", "pgvector", "secrets"):
        (run_dir / name).mkdir(parents=True, exist_ok=True)
    brain_db_backup = run_dir / "sqlite" / "brain__brain.db"
    raw_archive = run_dir / "raw_data" / "data.tar.gz"
    pg_dump = run_dir / "pgvector" / "cognee_db.sql"
    secrets_archive = run_dir / "secrets" / "secrets.tar.gz"
    for path in (brain_db_backup, pg_dump, secrets_archive):
        path.write_text("backup", encoding="utf-8")
    profile_context = tmp_path / "prod" / "shared" / "data" / "brain" / "profile_context.json"
    profile_context.parent.mkdir(parents=True)
    profile_context.write_text("[]\n", encoding="utf-8")
    with tarfile.open(raw_archive, "w:gz") as tar:
        tar.add(profile_context.parent.parent, arcname="data")

    manifest = {
        "blockers": [],
        "sqlite": [
            {
                "source": "/prod/shared/data/brain/brain.db",
                "backup": str(brain_db_backup),
                "integrity_check": "ok",
            }
        ],
        "raw_data": [
            {
                "source": str(profile_context.parent.parent),
                "archive": str(raw_archive),
            }
        ],
        "pgvector": [{"dump": str(pg_dump), "verified": True}],
        "lancedb": [],
        "secrets": [{"archive": str(secrets_archive)}],
        "neo4j": [{"method": "cypher_count_check", "verified": True}],
        "google_drive": {"verified": False},
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    settings = SimpleNamespace(
        system_root_directory="/prod/shared/data/system",
        db_provider="postgres",
        vector_db_provider="pgvector",
        brain_profile_context_path=str(profile_context),
        brain_google_drive_backup_enabled=False,
    )
    failures: list[str] = []

    verify_mcp_production.check_backups(backup_dir, settings, failures)

    assert failures == []


def test_verify_backups_rejects_raw_archive_missing_profile_context(tmp_path) -> None:
    backup_dir = tmp_path / "backups"
    run_dir = backup_dir / "20260504_120000"
    for name in ("sqlite", "raw_data", "pgvector", "secrets"):
        (run_dir / name).mkdir(parents=True, exist_ok=True)
    brain_db_backup = run_dir / "sqlite" / "brain__brain.db"
    raw_archive = run_dir / "raw_data" / "data.tar.gz"
    pg_dump = run_dir / "pgvector" / "cognee_db.sql"
    secrets_archive = run_dir / "secrets" / "secrets.tar.gz"
    for path in (brain_db_backup, pg_dump, secrets_archive):
        path.write_text("backup", encoding="utf-8")
    shared_data = tmp_path / "prod" / "shared" / "data"
    (shared_data / "data").mkdir(parents=True)
    (shared_data / "data" / "memory.txt").write_text("missing profile", encoding="utf-8")
    with tarfile.open(raw_archive, "w:gz") as tar:
        tar.add(shared_data / "data", arcname="data")

    manifest = {
        "blockers": [],
        "sqlite": [
            {
                "source": "/prod/shared/data/brain/brain.db",
                "backup": str(brain_db_backup),
                "integrity_check": "ok",
            }
        ],
        "raw_data": [{"source": str(shared_data), "archive": str(raw_archive)}],
        "pgvector": [{"dump": str(pg_dump), "verified": True}],
        "lancedb": [],
        "secrets": [{"archive": str(secrets_archive)}],
        "neo4j": [{"method": "cypher_count_check", "verified": True}],
        "google_drive": {"verified": False},
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    settings = SimpleNamespace(
        system_root_directory="/prod/shared/data/system",
        db_provider="postgres",
        vector_db_provider="pgvector",
        brain_profile_context_path=str(shared_data / "brain" / "profile_context.json"),
        brain_google_drive_backup_enabled=False,
    )
    failures: list[str] = []

    verify_mcp_production.check_backups(backup_dir, settings, failures)

    assert any("profile context" in failure for failure in failures)
