#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rich.console import Console

from memory_stack.config import load_settings


console = Console()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-launchd", action="store_true")
    parser.add_argument("--skip-backups", action="store_true")
    args = parser.parse_args()

    settings = load_settings()
    failures: list[str] = []

    prod_root = Path(settings.brain_prod_root)
    current = prod_root / "current"
    shared_data = prod_root / "shared" / "data"

    check_path(current, "current symlink", failures)
    check_path(shared_data, "shared/data", failures)
    check_runtime_paths(settings, shared_data, failures)

    pid = None
    if not args.skip_launchd:
        pid = check_launchd(settings.brain_launchd_label, failures)
        if pid:
            check_process_cwd(pid, prod_root, failures)

    check_http(
        f"http://{settings.brain_mcp_host}:{settings.brain_mcp_port}{settings.brain_health_path}",
        "local health",
        failures,
        expect_json_service=True,
    )
    check_mcp(settings, failures)
    if settings.brain_auth_enabled:
        check_oauth_metadata(settings, failures)

    if not args.skip_backups:
        check_backups(Path(settings.brain_backup_dir), settings, failures)

    if failures:
        for failure in failures:
            console.print(f"[red][FAIL][/red] {failure}")
        return 1

    console.print("[green][OK][/green] production verification passed")
    return 0


def check_path(path: Path, label: str, failures: list[str]) -> None:
    if path.exists():
        console.print(f"[green][OK][/green] {label}: {path}")
    else:
        failures.append(f"missing {label}: {path}")


def check_runtime_paths(settings, shared_data: Path, failures: list[str]) -> None:
    paths = {
        "SYSTEM_ROOT_DIRECTORY": Path(settings.system_root_directory),
        "DATA_ROOT_DIRECTORY": Path(settings.data_root_directory),
        "VECTOR_DB_URL": Path(settings.vector_db_url),
        "BRAIN_DATABASE_URL": sqlite_path(settings.brain_database_url),
    }
    for label, path in paths.items():
        if not path.is_absolute():
            failures.append(f"{label} is not absolute in production: {path}")
            continue
        try:
            path.resolve().relative_to(shared_data.resolve())
            console.print(f"[green][OK][/green] {label} under shared/data")
        except ValueError:
            failures.append(f"{label} is not under shared/data: {path}")


def sqlite_path(database_url: str) -> Path:
    prefix = "sqlite:///"
    if database_url.startswith(prefix):
        return Path(database_url.removeprefix(prefix))
    return Path(database_url)


def check_launchd(label: str, failures: list[str]) -> int | None:
    if not command_exists("launchctl"):
        failures.append("launchctl is not available")
        return None
    result = subprocess.run(
        ["launchctl", "print", f"gui/{uid()}/{label}"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        failures.append(f"launchd service not loaded: {label}")
        return None
    pid = parse_launchd_pid(result.stdout)
    if pid:
        console.print(f"[green][OK][/green] launchd service running pid={pid}")
        return pid
    failures.append(f"launchd service loaded but no pid found: {label}")
    return None


def uid() -> str:
    return subprocess.check_output(["id", "-u"], text=True).strip()


def parse_launchd_pid(output: str) -> int | None:
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith("pid ="):
            try:
                return int(stripped.split("=", 1)[1].strip())
            except ValueError:
                return None
    return None


def check_process_cwd(pid: int, prod_root: Path, failures: list[str]) -> None:
    if not command_exists("lsof"):
        failures.append("lsof is not available to inspect process cwd")
        return
    result = subprocess.run(
        ["lsof", "-a", "-p", str(pid), "-d", "cwd", "-Fn"],
        text=True,
        capture_output=True,
        check=False,
    )
    cwd = None
    for line in result.stdout.splitlines():
        if line.startswith("n"):
            cwd = Path(line[1:])
            break
    if cwd is None:
        failures.append(f"could not determine cwd for pid {pid}")
        return
    try:
        cwd.resolve().relative_to(prod_root.resolve())
        console.print(f"[green][OK][/green] process cwd under production: {cwd}")
    except ValueError:
        failures.append(f"process cwd is not under production root: {cwd}")


def check_http(
    url: str,
    label: str,
    failures: list[str],
    *,
    expect_json_service: bool = False,
) -> dict[str, Any] | None:
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            body = response.read().decode("utf-8", errors="replace")
            status = response.status
    except Exception as exc:
        failures.append(f"{label} failed at {url}: {exc}")
        return None
    if status >= 400:
        failures.append(f"{label} returned HTTP {status}: {url}")
        return None
    console.print(f"[green][OK][/green] {label}: {url}")
    if expect_json_service:
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            failures.append(f"{label} did not return JSON")
            return None
        if payload.get("service") != "Brain":
            failures.append(f"{label} service is not Brain: {payload}")
        return payload
    return None


def check_mcp(settings, failures: list[str]) -> None:
    url = f"http://{settings.brain_mcp_host}:{settings.brain_mcp_port}{settings.brain_mcp_path}"
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            body = response.read().decode("utf-8", errors="replace")
            status = response.status
            headers = {key.lower(): value for key, value in response.headers.items()}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        status = exc.code
        headers = {key.lower(): value for key, value in exc.headers.items()}
    except Exception as exc:
        failures.append(f"local MCP failed at {url}: {exc}")
        return

    if settings.brain_auth_enabled:
        if status != 401:
            failures.append(f"auth-enabled MCP did not fail closed; status={status}")
        challenge = headers.get("www-authenticate", "")
        if "Brain" not in challenge and "brain" not in challenge:
            failures.append(f"MCP auth challenge does not identify Brain: {challenge}")
        if settings.protected_resource_metadata_url not in challenge:
            failures.append(
                "MCP auth challenge does not advertise Brain protected-resource metadata: "
                f"{challenge}"
            )
        else:
            console.print("[green][OK][/green] local MCP fails closed with Brain auth metadata")
    elif status >= 400:
        failures.append(f"local MCP returned HTTP {status}: {body[:200]}")
    else:
        if "Brain" not in body and "brain" not in body:
            failures.append("local MCP response does not identify Brain")
        console.print(f"[green][OK][/green] local MCP: {url}")


def check_oauth_metadata(settings, failures: list[str]) -> None:
    base = f"http://{settings.brain_mcp_host}:{settings.brain_mcp_port}"
    protected = check_http_json(
        f"{base}/.well-known/oauth-protected-resource{settings.brain_public_mcp_path}",
        "local OAuth protected-resource metadata",
        failures,
    )
    if protected:
        if protected.get("resource_name") != "Brain":
            failures.append(f"protected-resource metadata is not Brain: {protected}")
        if protected.get("resource") != settings.public_mcp_url:
            failures.append(
                "protected-resource metadata resource does not match public MCP URL: "
                f"{protected}"
            )

    issuer = check_http_json(
        f"{base}/.well-known/oauth-authorization-server",
        "local OAuth authorization-server metadata",
        failures,
    )
    if issuer:
        if issuer.get("service") != "Brain":
            failures.append(f"authorization-server metadata is not Brain: {issuer}")
        if issuer.get("issuer") != settings.brain_public_base_url.rstrip("/"):
            failures.append(f"authorization-server issuer is wrong: {issuer}")


def check_http_json(url: str, label: str, failures: list[str]) -> dict[str, Any] | None:
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            body = response.read().decode("utf-8", errors="replace")
            status = response.status
    except Exception as exc:
        failures.append(f"{label} failed at {url}: {exc}")
        return None
    if status >= 400:
        failures.append(f"{label} returned HTTP {status}: {url}")
        return None
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        failures.append(f"{label} did not return JSON")
        return None
    console.print(f"[green][OK][/green] {label}: {url}")
    return payload


def check_backups(backup_dir: Path, settings, failures: list[str]) -> None:
    if not backup_dir.exists():
        failures.append(f"backup dir missing: {backup_dir}")
        return
    manifests = sorted(backup_dir.glob("*/manifest.json"))
    if not manifests:
        failures.append(f"no backup manifests found in {backup_dir}")
        return
    latest = manifests[-1]
    payload = json.loads(latest.read_text(encoding="utf-8"))
    blockers = payload.get("blockers", [])
    if blockers:
        failures.append(f"latest backup has blockers: {blockers}")

    sqlite_entries = payload.get("sqlite") or []
    if not sqlite_entries:
        failures.append(f"latest backup has no SQLite result: {latest}")
    db_name = getattr(settings, "db_name", "cognee_db")
    main_db = str(Path(settings.system_root_directory) / "databases" / db_name)
    if not any(entry.get("source") == main_db for entry in sqlite_entries):
        failures.append(f"latest backup does not include main Cognee DB: {latest}")
    bad_sqlite = [
        entry
        for entry in sqlite_entries
        if entry.get("integrity_check") != "ok" or not Path(entry.get("backup", "")).exists()
    ]
    if bad_sqlite:
        failures.append(f"latest backup has invalid SQLite entries: {bad_sqlite}")

    if not verified_archive_entries(payload.get("raw_data")):
        failures.append(f"latest backup has no verified raw data archive: {latest}")
    if not verified_archive_entries(payload.get("lancedb")):
        failures.append(f"latest backup has no verified LanceDB archive: {latest}")
    if not verified_archive_entries(payload.get("secrets")):
        failures.append(f"latest backup has no verified secrets archive: {latest}")

    neo4j_entries = payload.get("neo4j") or []
    if not any(entry.get("verified") for entry in neo4j_entries):
        failures.append(f"latest backup has no verified Neo4j check or dump: {latest}")

    if settings.brain_google_drive_backup_enabled:
        google = payload.get("google_drive") or {}
        if not google.get("verified"):
            failures.append(f"latest backup is not verified in Google Drive: {latest}")
    console.print(f"[green][OK][/green] backup manifest present: {latest}")


def verified_archive_entries(entries: Any) -> bool:
    if not entries:
        return False
    for entry in entries:
        archive = entry.get("archive")
        if archive and Path(archive).exists():
            return True
    return False


def command_exists(command: str) -> bool:
    return subprocess.run(["/usr/bin/env", "which", command], capture_output=True).returncode == 0


if __name__ == "__main__":
    raise SystemExit(main())
