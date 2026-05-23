#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tarfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rich.console import Console

from memory_stack.cfg import load_settings
from production_check_utils import command_exists


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
    check_release_metadata(prod_root, current, settings, failures)
    check_runtime_paths(settings, shared_data, failures)
    check_palate_retired(failures)

    pid = None
    if not args.skip_launchd:
        pid = check_launchd(settings.brain_launchd_label, failures)
        if pid:
            local_support_root = Path(f"/var/db/brain-{settings.brain_release_env}")
            check_process_cwd(pid, (prod_root, local_support_root), failures)

    health_payload = check_http(
        f"http://{settings.brain_mcp_host}:{settings.brain_mcp_port}{settings.brain_health_path}",
        "local health",
        failures,
        expect_json_service=True,
    )
    check_health_release(health_payload, settings, failures)
    check_http(
        f"http://{settings.brain_mcp_host}:{settings.brain_mcp_port}/",
        "local Brain dashboard",
        failures,
    )
    check_mcp(settings, failures)
    check_app_mcp(settings, failures)
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


def check_release_metadata(prod_root: Path, current: Path, settings, failures: list[str]) -> None:
    if not current.exists():
        return
    try:
        current_target = current.resolve(strict=True)
    except OSError as exc:
        failures.append(f"current symlink cannot be resolved: {exc}")
        return
    current_sha = current_target.name
    metadata_paths = [
        current_target / "release.json",
        prod_root / "shared" / "release.json",
    ]
    for path in metadata_paths:
        if not path.exists():
            failures.append(f"missing release metadata: {path}")
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            failures.append(f"invalid release metadata JSON at {path}: {exc}")
            continue
        if payload.get("sha") != current_sha:
            failures.append(
                f"release metadata sha mismatch at {path}: {payload.get('sha')} != {current_sha}"
            )
        if payload.get("version") != settings.brain_release_version:
            failures.append(
                "release metadata version mismatch at "
                f"{path}: {payload.get('version')} != {settings.brain_release_version}"
            )
        if payload.get("environment") != settings.brain_release_env:
            failures.append(
                "release metadata environment mismatch at "
                f"{path}: {payload.get('environment')} != {settings.brain_release_env}"
            )
    if settings.brain_release_sha != current_sha:
        failures.append(
            f"BRAIN_RELEASE_SHA does not match current release: {settings.brain_release_sha} != {current_sha}"
        )


def check_health_release(
    payload: dict[str, Any] | None,
    settings,
    failures: list[str],
) -> None:
    if payload is None:
        return
    expected = {
        "release_env": settings.brain_release_env,
        "release_sha": settings.brain_release_sha,
        "release_version": settings.brain_release_version,
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            failures.append(f"local health {key} mismatch: {payload.get(key)} != {value}")


def check_runtime_paths(settings, shared_data: Path, failures: list[str]) -> None:
    local_support_root = Path(f"/var/db/brain-{settings.brain_release_env}")
    shared_paths = {}
    local_or_shared_paths = {
        "BRAIN_DATABASE_URL": sqlite_path(settings.brain_database_url),
        "SYSTEM_ROOT_DIRECTORY": Path(settings.system_root_directory),
        "DATA_ROOT_DIRECTORY": Path(settings.data_root_directory),
    }
    if getattr(settings, "vector_db_provider", "lancedb") == "lancedb":
        shared_paths["VECTOR_DB_URL"] = Path(settings.vector_db_url)

    for label, path in shared_paths.items():
        if not path.is_absolute():
            failures.append(f"{label} is not absolute in production: {path}")
            continue
        try:
            path.resolve().relative_to(shared_data.resolve())
            console.print(f"[green][OK][/green] {label} under shared/data")
        except ValueError:
            failures.append(f"{label} is not under shared/data: {path}")

    for label, path in local_or_shared_paths.items():
        if not path.is_absolute():
            failures.append(f"{label} is not absolute in production: {path}")
            continue
        resolved_path = path.resolve()
        for root, description in (
            (local_support_root, "local support root"),
            (shared_data, "shared/data"),
        ):
            try:
                resolved_path.relative_to(root.resolve())
                console.print(f"[green][OK][/green] {label} under {description}")
                break
            except ValueError:
                continue
        else:
            failures.append(f"{label} is not under local support root or shared/data: {path}")


def check_palate_retired(failures: list[str]) -> None:
    launch_agents = Path.home() / "Library" / "LaunchAgents"
    active_launch_agents = [
        path for path in launch_agents.glob("*palate*") if "retired" not in str(path)
    ]
    if active_launch_agents:
        failures.append(f"active Palate launch agents still present: {active_launch_agents}")

    prod_palate = Path("/Volumes/xpg_usb4/prod/palate")
    if prod_palate.exists():
        failures.append(f"active Palate production path still present: {prod_palate}")

    cloudflared_config = Path.home() / ".cloudflared" / "config.yml"
    if cloudflared_config.exists():
        text = cloudflared_config.read_text(encoding="utf-8")
        if "palate.dceb.net" in text or "/palate" in text:
            failures.append(
                f"Cloudflare tunnel config still contains Palate routes: {cloudflared_config}"
            )

    if command_exists("launchctl"):
        result = subprocess.run(
            ["launchctl", "list"],
            text=True,
            capture_output=True,
            check=False,
        )
        if "palate" in result.stdout.lower():
            failures.append("active launchctl list still contains Palate service labels")


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
        ["launchctl", "print", f"system/{label}"],
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


def parse_launchd_pid(output: str) -> int | None:
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith("pid ="):
            try:
                return int(stripped.split("=", 1)[1].strip())
            except ValueError:
                return None
    return None


def check_process_cwd(pid: int, allowed_roots: tuple[Path, ...], failures: list[str]) -> None:
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
    resolved_cwd = cwd.resolve()
    for root in allowed_roots:
        try:
            resolved_cwd.relative_to(root.resolve())
            console.print(f"[green][OK][/green] process cwd under approved runtime root: {cwd}")
            return
        except ValueError:
            continue
    roots = ", ".join(str(root) for root in allowed_roots)
    failures.append(f"process cwd is not under an approved runtime root ({roots}): {cwd}")


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
    url = (
        f"http://{settings.brain_mcp_host}:{settings.brain_mcp_port}{settings.brain_admin_mcp_path}"
    )
    check_mcp_get(
        settings,
        failures,
        url=url,
        expected_metadata_url=settings.protected_resource_metadata_url_for_path(
            settings.brain_public_admin_mcp_path
        ),
        label="local admin MCP",
    )


def check_app_mcp(settings, failures: list[str]) -> None:
    url = f"http://{settings.brain_mcp_host}:{settings.brain_mcp_port}{settings.brain_mcp_path}"
    check_mcp_get(
        settings,
        failures,
        url=url,
        expected_metadata_url=settings.protected_resource_metadata_url,
        label="local curated MCP",
    )


def check_mcp_get(
    settings,
    failures: list[str],
    *,
    url: str,
    expected_metadata_url: str,
    label: str,
) -> None:
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
        failures.append(f"{label} failed at {url}: {exc}")
        return

    if status != 401:
        failures.append(f"{label} did not fail closed; status={status}")
    challenge = headers.get("www-authenticate", "")
    if "Brain" not in challenge and "brain" not in challenge:
        failures.append(f"{label} auth challenge does not identify Brain: {challenge}")
    if expected_metadata_url not in challenge:
        failures.append(
            f"{label} auth challenge does not advertise Brain protected-resource metadata: "
            f"{challenge}"
        )
    else:
        console.print(f"[green][OK][/green] {label} fails closed with Brain auth metadata")


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
                f"protected-resource metadata resource does not match public MCP URL: {protected}"
            )

    admin_protected = check_http_json(
        f"{base}/.well-known/oauth-protected-resource{settings.brain_public_admin_mcp_path}",
        "local OAuth admin protected-resource metadata",
        failures,
    )
    if admin_protected:
        if admin_protected.get("resource_name") != "Brain":
            failures.append(f"admin protected-resource metadata is not Brain: {admin_protected}")
        if admin_protected.get("resource") != settings.public_admin_mcp_url:
            failures.append(
                "admin protected-resource metadata resource does not match public admin MCP URL: "
                f"{admin_protected}"
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
    if getattr(settings, "db_provider", "sqlite") == "sqlite":
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

    raw_data_entries = payload.get("raw_data")
    if not verified_archive_entries(raw_data_entries):
        failures.append(f"latest backup has no verified raw data archive: {latest}")
    profile_context_path = getattr(settings, "brain_profile_context_path", None)
    if profile_context_path and not raw_archive_contains(
        raw_data_entries,
        Path(profile_context_path),
    ):
        failures.append(
            f"latest backup raw data archive does not include profile context: {latest}"
        )
    if getattr(settings, "vector_db_provider", "lancedb") == "pgvector":
        if not any(
            entry.get("verified") and Path(entry.get("dump", "")).exists()
            for entry in payload.get("pgvector") or []
        ):
            failures.append(f"latest backup has no verified pgvector/Postgres dump: {latest}")
    elif not verified_archive_entries(payload.get("lancedb")):
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


def raw_archive_contains(entries: Any, target: Path) -> bool:
    if not entries:
        return False
    for entry in entries:
        archive = Path(entry.get("archive", ""))
        source = Path(entry.get("source", ""))
        if not archive.exists() or not source:
            continue
        try:
            relative_target = target.relative_to(source)
        except ValueError:
            continue
        expected = f"{source.name}/{relative_target.as_posix()}"
        try:
            with tarfile.open(archive, "r:*") as tar:
                if expected in tar.getnames():
                    return True
        except (OSError, tarfile.TarError):
            continue
    return False


if __name__ == "__main__":
    raise SystemExit(main())
