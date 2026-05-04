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
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rich.console import Console

from memory_stack.config import load_settings


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
        "neo4j": [],
        "google_drive": None,
        "blockers": [],
    }

    backup_sqlite(data_root, run_dir, manifest)
    backup_lancedb(settings.vector_db_url, data_root, run_dir, manifest)
    backup_neo4j(run_dir, manifest)

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
    candidates = sorted(
        {
            path
            for pattern in ("*.sqlite", "*.sqlite3", "*.db")
            for path in data_root.rglob(pattern)
            if path.is_file()
        }
    )
    if not candidates:
        manifest["blockers"].append("No SQLite files found under shared/data.")
        console.print("[yellow][WARN][/yellow] no SQLite files found")
        return

    sqlite_dir = run_dir / "sqlite"
    sqlite_dir.mkdir(exist_ok=True)
    for source in candidates:
        target = sqlite_dir / source.name
        with sqlite3.connect(source) as src, sqlite3.connect(target) as dst:
            src.backup(dst)
        integrity = sqlite_integrity_check(target)
        manifest["sqlite"].append(
            {"source": str(source), "backup": str(target), "integrity_check": integrity}
        )
        if integrity != "ok":
            raise RuntimeError(f"SQLite integrity check failed for {target}: {integrity}")
        console.print(f"[green][OK][/green] SQLite backup {target}")


def sqlite_integrity_check(path: Path) -> str:
    with sqlite3.connect(path) as conn:
        row = conn.execute("PRAGMA integrity_check").fetchone()
    return str(row[0]) if row else "missing"


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


def backup_neo4j(run_dir: Path, manifest: dict[str, Any]) -> None:
    if os.getenv("BRAIN_NEO4J_DUMP_ENABLED", "false").lower() not in {"1", "true", "yes"}:
        manifest["blockers"].append(
            "Neo4j dump not enabled. Set BRAIN_NEO4J_DUMP_ENABLED=true after mounting a dump path into the neo4j-cognee container."
        )
        console.print("[yellow][WARN][/yellow] Neo4j dump recorded as explicit blocker")
        return

    if not shutil.which("docker"):
        raise RuntimeError("BRAIN_NEO4J_DUMP_ENABLED=true but docker is not available.")

    dump_name = f"neo4j-{run_dir.name}.dump"
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
    manifest["neo4j"].append(
        {
            "dump": dump_name,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    )
    if result.returncode != 0:
        raise RuntimeError(f"Neo4j dump failed: {result.stderr.strip()}")


def verify_google_drive_upload(settings, run_dir: Path, manifest: dict[str, Any]) -> None:
    local_mount = os.getenv("BRAIN_GOOGLE_DRIVE_LOCAL_PATH")
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
