#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rich.console import Console

from memory_stack.cfg import load_settings


console = Console()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backup-dir", default=None)
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--skip-google-drive", action="store_true")
    args = parser.parse_args()

    settings = load_settings()
    backup_root = Path(args.backup_dir or settings.brain_backup_dir)
    data_root = Path(args.data_dir or settings.shared_data_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = backup_root / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "timestamp": timestamp,
        "backup_dir": str(run_dir),
        "data_root": str(data_root),
        "sqlite": [],
        "lancedb": [],
        "raw_data": [],
        "secrets": [],
        "neo4j": [],
        "google_drive": None,
        "blockers": [],
    }

    backup_sqlite(data_root, run_dir, manifest)
    backup_raw_data(Path(settings.data_root_directory), run_dir, manifest)
    backup_lancedb(settings.vector_db_url, data_root, run_dir, manifest)
    backup_secrets(settings, run_dir, manifest)
    backup_neo4j(settings, data_root, run_dir, manifest)

    manifest_path = run_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    console.print(f"[green][OK][/green] wrote manifest {manifest_path}")

    google_enabled = settings.brain_google_drive_backup_enabled and not args.skip_google_drive
    if google_enabled:
        verify_google_drive_upload(settings, run_dir, manifest)
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    elif settings.brain_google_drive_backup_enabled:
        manifest["google_drive"] = {"skipped": True}
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    console.print(f"[green][OK][/green] backup complete: {run_dir}")
    return 0


def backup_sqlite(data_root: Path, run_dir: Path, manifest: dict[str, Any]) -> None:
    candidates = find_sqlite_databases(data_root)
    if not candidates:
        manifest["blockers"].append("No SQLite files found under shared/data.")
        console.print("[yellow][WARN][/yellow] no SQLite files found")
        return

    sqlite_dir = run_dir / "sqlite"
    sqlite_dir.mkdir(exist_ok=True)
    for source in candidates:
        target = sqlite_dir / backup_filename(data_root, source)
        with sqlite3.connect(source) as src, sqlite3.connect(target) as dst:
            src.backup(dst)
        integrity = sqlite_integrity_check(target)
        manifest["sqlite"].append(
            {"source": str(source), "backup": str(target), "integrity_check": integrity}
        )
        if integrity != "ok":
            raise RuntimeError(f"SQLite integrity check failed for {target}: {integrity}")
        console.print(f"[green][OK][/green] SQLite backup {target}")


def find_sqlite_databases(data_root: Path) -> list[Path]:
    candidates = {
        path
        for pattern in ("*.sqlite", "*.sqlite3", "*.db")
        for path in data_root.rglob(pattern)
        if path.is_file()
    }
    candidates.update(
        path
        for path in (data_root / "system" / "databases").glob("*")
        if path.is_file()
    )
    return sorted(path for path in candidates if is_sqlite_database(path))


def is_sqlite_database(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            return handle.read(16) == b"SQLite format 3\0"
    except OSError:
        return False


def sqlite_integrity_check(path: Path) -> str:
    with sqlite3.connect(path) as conn:
        row = conn.execute("PRAGMA integrity_check").fetchone()
    return str(row[0]) if row else "missing"


def backup_raw_data(data_dir: Path, run_dir: Path, manifest: dict[str, Any]) -> None:
    if not data_dir.exists():
        manifest["blockers"].append(f"DATA_ROOT_DIRECTORY missing: {data_dir}")
        console.print(f"[yellow][WARN][/yellow] DATA_ROOT_DIRECTORY missing: {data_dir}")
        return

    archive_dir = run_dir / "raw_data"
    archive_dir.mkdir(exist_ok=True)
    archive = archive_dir / f"{data_dir.name}.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(data_dir, arcname=data_dir.name)
    manifest["raw_data"].append({"source": str(data_dir), "archive": str(archive)})
    console.print(f"[green][OK][/green] raw data archive {archive}")


def backup_lancedb(
    vector_db_url: str,
    data_root: Path,
    run_dir: Path,
    manifest: dict[str, Any],
) -> None:
    candidates: list[Path] = []
    configured = Path(vector_db_url)
    if not configured.is_absolute():
        configured = data_root / configured
    if configured.exists():
        candidates.append(configured)
    candidates.extend(path for path in data_root.rglob("*lancedb*") if path.exists())

    unique_candidates = []
    for path in candidates:
        if path not in unique_candidates:
            unique_candidates.append(path)

    if not unique_candidates:
        manifest["blockers"].append("No LanceDB path found under shared/data.")
        console.print("[yellow][WARN][/yellow] no LanceDB path found")
        return

    archive_dir = run_dir / "lancedb"
    archive_dir.mkdir(exist_ok=True)
    for source in unique_candidates:
        archive = archive_dir / f"{source.name}.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(source, arcname=source.name)
        manifest["lancedb"].append({"source": str(source), "archive": str(archive)})
        console.print(f"[green][OK][/green] LanceDB archive {archive}")


def backup_secrets(settings, run_dir: Path, manifest: dict[str, Any]) -> None:
    secret_paths = {
        Path(value).expanduser()
        for value in (
            os.getenv("ENV_FILE"),
            settings.brain_auth_password_file,
            settings.brain_auth_state_path,
        )
        if value
    }
    secret_paths = {path for path in secret_paths if str(path) and path.exists()}
    if not secret_paths:
        manifest["blockers"].append("No production secret files found to back up.")
        console.print("[yellow][WARN][/yellow] no secret files found")
        return

    archive_dir = run_dir / "secrets"
    archive_dir.mkdir(exist_ok=True)
    archive = archive_dir / "secrets.tar.gz"
    common_root = Path(os.path.commonpath([str(path.parent) for path in secret_paths]))
    with tarfile.open(archive, "w:gz") as tar:
        for source in sorted(secret_paths):
            tar.add(source, arcname=str(source.relative_to(common_root)))
    archive.chmod(0o600)
    manifest["secrets"].append(
        {
            "sources": [str(path) for path in sorted(secret_paths)],
            "archive": str(archive),
        }
    )
    console.print(f"[green][OK][/green] secrets archive {archive}")


def backup_neo4j(settings, data_root: Path, run_dir: Path, manifest: dict[str, Any]) -> None:
    graph_counts = neo4j_graph_counts(settings)
    if graph_counts is not None:
        counts_path = run_dir / "neo4j-counts.json"
        counts_path.write_text(json.dumps(graph_counts, indent=2), encoding="utf-8")
        manifest["neo4j"].append(
            {"method": "cypher_count_check", "counts": graph_counts, "verified": True}
        )

    if not settings.brain_neo4j_dump_enabled:
        if graph_counts and (graph_counts.get("nodes", 0) or graph_counts.get("relationships", 0)):
            manifest["blockers"].append(
                "Neo4j contains graph data but dump is not enabled. Set "
                "BRAIN_NEO4J_DUMP_ENABLED=true and run a consistent dump."
            )
            archive_neo4j_raw(data_root, run_dir, manifest)
            console.print("[yellow][WARN][/yellow] Neo4j dump missing for non-empty graph")
        else:
            console.print("[green][OK][/green] Neo4j graph is empty; dump not required")
        return

    if not shutil.which("docker"):
        dump_with_neo4j_admin(settings, run_dir, manifest)
        return

    dump_dir = run_dir / "neo4j"
    dump_dir.mkdir(exist_ok=True)
    dump_path = dump_dir / "neo4j.dump"
    mounted_dump = data_root / "neo4j" / "neo4j.dump"
    if mounted_dump.exists():
        mounted_dump.unlink()

    result = subprocess.run(
        [
            "docker",
            "exec",
            "neo4j-cognee",
            "neo4j-admin",
            "database",
            "dump",
            "neo4j",
            "--to-path=/data",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0 and mounted_dump.exists():
        shutil.copy2(mounted_dump, dump_path)

    manifest["neo4j"].append(
        {
            "method": "docker-neo4j-admin",
            "dump": str(dump_path),
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "verified": result.returncode == 0 and dump_path.exists(),
        }
    )
    if result.returncode != 0:
        raise RuntimeError(f"Neo4j dump failed: {result.stderr.strip()}")


def dump_with_neo4j_admin(settings, run_dir: Path, manifest: dict[str, Any]) -> None:
    if not shutil.which("neo4j-admin"):
        raise RuntimeError(
            "BRAIN_NEO4J_DUMP_ENABLED=true but neither docker nor neo4j-admin is available."
        )

    restart_after_dump = False
    if settings.brain_neo4j_stop_for_dump and neo4j_launchd_running(settings):
        console.print("[yellow][WARN][/yellow] stopping Neo4j for consistent dump")
        stop_neo4j_service(settings)
        restart_after_dump = True

    dump_dir = run_dir / "neo4j"
    dump_dir.mkdir(exist_ok=True)
    try:
        result = subprocess.run(
            [
                "neo4j-admin",
                "database",
                "dump",
                settings.graph_database_name,
                f"--to-path={dump_dir}",
                "--overwrite-destination=true",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        dump_path = dump_dir / f"{settings.graph_database_name}.dump"
        manifest["neo4j"].append(
            {
                "method": "neo4j-admin",
                "dump": str(dump_path),
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "verified": result.returncode == 0 and dump_path.exists(),
            }
        )
        if result.returncode != 0:
            hint = ""
            if "database is in use" in result.stderr.lower() and not settings.brain_neo4j_stop_for_dump:
                hint = " Set BRAIN_NEO4J_STOP_FOR_DUMP=true to stop Neo4j during backups."
            raise RuntimeError(f"Neo4j dump failed: {result.stderr.strip()}{hint}")
    finally:
        if restart_after_dump:
            start_neo4j_service(settings)
            wait_for_neo4j(settings)


def neo4j_graph_counts(settings) -> dict[str, int] | None:
    if not shutil.which("cypher-shell"):
        return None
    result = subprocess.run(
        [
            "cypher-shell",
            "--format",
            "plain",
            "-a",
            settings.graph_database_url.replace("bolt://localhost", "bolt://127.0.0.1"),
            "-u",
            settings.graph_database_username,
            "-p",
            settings.graph_database_password,
            "-d",
            settings.graph_database_name,
            "MATCH (n) WITH count(n) AS nodes OPTIONAL MATCH ()-[r]->() "
            "RETURN nodes, count(r) AS relationships;",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if len(lines) < 2:
        return None
    values = [value.strip() for value in lines[-1].split(",")]
    if len(values) != 2:
        return None
    return {"nodes": int(values[0]), "relationships": int(values[1])}


def neo4j_launchd_running(settings) -> bool:
    if not shutil.which("launchctl"):
        return False
    result = subprocess.run(
        ["launchctl", "print", f"gui/{os.getuid()}/{settings.brain_neo4j_launchd_label}"],
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0 and "state = running" in result.stdout


def stop_neo4j_service(settings) -> None:
    if shutil.which("brew"):
        result = subprocess.run(
            ["brew", "services", "stop", settings.brain_neo4j_brew_service],
            text=True,
            capture_output=True,
            check=False,
        )
    else:
        result = subprocess.run(
            [
                "launchctl",
                "bootout",
                f"gui/{os.getuid()}",
                f"{Path.home()}/Library/LaunchAgents/{settings.brain_neo4j_launchd_label}.plist",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to stop Neo4j service: {result.stderr.strip()}")
    wait_for_neo4j_stopped(settings)


def start_neo4j_service(settings) -> None:
    if shutil.which("brew"):
        result = subprocess.run(
            ["brew", "services", "start", settings.brain_neo4j_brew_service],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0 and "Bootstrap failed" in result.stderr:
            subprocess.run(
                [
                    "launchctl",
                    "bootout",
                    f"gui/{os.getuid()}",
                    f"{Path.home()}/Library/LaunchAgents/{settings.brain_neo4j_launchd_label}.plist",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            result = subprocess.run(
                ["brew", "services", "start", settings.brain_neo4j_brew_service],
                text=True,
                capture_output=True,
                check=False,
            )
    else:
        result = subprocess.run(
            [
                "launchctl",
                "bootstrap",
                f"gui/{os.getuid()}",
                f"{Path.home()}/Library/LaunchAgents/{settings.brain_neo4j_launchd_label}.plist",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to start Neo4j service: {result.stderr.strip()}")


def wait_for_neo4j_stopped(settings, attempts: int = 45) -> None:
    for _ in range(attempts):
        if (
            not neo4j_launchd_running(settings)
            and not neo4j_bolt_listening(settings)
            and not neo4j_process_running()
        ):
            return
        time.sleep(1)
    raise RuntimeError("Neo4j did not stop before the dump window.")


def neo4j_bolt_listening(settings) -> bool:
    if not shutil.which("lsof"):
        return False
    port = str(settings.graph_database_url).rsplit(":", maxsplit=1)[-1] or "7687"
    result = subprocess.run(
        ["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN"],
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def neo4j_process_running() -> bool:
    result = subprocess.run(
        ["pgrep", "-f", "org.neo4j.server.Neo4jCommunity"],
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def wait_for_neo4j(settings, attempts: int = 45) -> None:
    if not shutil.which("cypher-shell"):
        return
    for _ in range(attempts):
        result = subprocess.run(
            [
                "cypher-shell",
                "-a",
                settings.graph_database_url,
                "-u",
                settings.graph_database_username,
                "-p",
                settings.graph_database_password,
                "RETURN 1;",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            return
        time.sleep(1)
    raise RuntimeError("Neo4j did not become ready after restart.")


def archive_neo4j_raw(data_root: Path, run_dir: Path, manifest: dict[str, Any]) -> None:
    neo4j_dir = data_root / "neo4j"
    if not neo4j_dir.exists():
        return
    archive_dir = run_dir / "neo4j"
    archive_dir.mkdir(exist_ok=True)
    archive = archive_dir / "neo4j-raw-live.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(neo4j_dir, arcname=neo4j_dir.name)
    manifest["neo4j"].append(
        {
            "method": "raw_live_archive",
            "archive": str(archive),
            "verified": False,
            "note": "Raw live Neo4j archive is a fallback only; use a dump for consistency.",
        }
    )


def backup_filename(root: Path, source: Path) -> str:
    try:
        relative = source.relative_to(root)
    except ValueError:
        relative = Path(source.name)
    return "__".join(relative.parts)


def verify_google_drive_upload(settings, run_dir: Path, manifest: dict[str, Any]) -> None:
    local_mount = settings.brain_google_drive_local_path or os.getenv(
        "BRAIN_GOOGLE_DRIVE_LOCAL_PATH"
    )
    if local_mount:
        target = Path(local_mount) / settings.brain_google_drive_folder
        target.mkdir(parents=True, exist_ok=True)
        copied = target / run_dir.name
        if copied.exists():
            shutil.rmtree(copied)
        shutil.copytree(run_dir, copied)
        if not (copied / "manifest.json").exists():
            raise RuntimeError(f"Google Drive local copy missing manifest: {copied}")
        manifest["google_drive"] = {"method": "local_path", "path": str(copied), "verified": True}
        console.print(f"[green][OK][/green] verified Google Drive local path {copied}")
        return

    if not shutil.which("rclone"):
        raise RuntimeError(
            "Google Drive backup is enabled but rclone is not installed and "
            "BRAIN_GOOGLE_DRIVE_LOCAL_PATH is not set."
        )

    remote = f"{settings.brain_google_drive_remote}:{settings.brain_google_drive_folder}/{run_dir.name}"
    subprocess.run(["rclone", "copy", str(run_dir), remote], check=True)
    listing = subprocess.run(
        ["rclone", "lsf", remote],
        text=True,
        capture_output=True,
        check=True,
    ).stdout
    if "manifest.json" not in listing:
        raise RuntimeError(f"Google Drive upload verification failed for {remote}")
    manifest["google_drive"] = {"method": "rclone", "remote": remote, "verified": True}
    console.print(f"[green][OK][/green] verified Google Drive upload {remote}")


if __name__ == "__main__":
    raise SystemExit(main())
