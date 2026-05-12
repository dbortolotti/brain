#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import os
import shlex
import sys
from datetime import UTC, datetime
from pathlib import Path

from memory_stack.model_selection import (
    DEFAULT_EMBEDDING_DIMENSIONS,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_EMBEDDING_PROVIDER,
    DEFAULT_LLM_MODEL,
    DEFAULT_LLM_PROVIDER,
)


PROD_ROOT = Path(os.getenv("BRAIN_PROD_ROOT", "/Volumes/xpg_usb4/prod/brain"))
SHARED_DIR = PROD_ROOT / "shared"
SECRETS_DIR = SHARED_DIR / "secrets"
DATA_DIR = SHARED_DIR / "data"
BACKUP_DIR = SHARED_DIR / "backups"
LOG_DIR = SHARED_DIR / "logs"
CURRENT_LINK = PROD_ROOT / "current"


METADATA_KEYS = {
    "BRAIN_CONFIG_RENDER_SHA",
    "BRAIN_CONFIG_RENDERED_AT",
    "BRAIN_CONFIG_RENDER_SOURCE",
}
REQUIRED_CONFIG_KEYS = {
    "GRAPH_DATABASE_PASSWORD": {
        "",
    },
}
OPENAI_API_KEY_PLACEHOLDERS = {
    "",
    "replace-me",
    "sk-...",
    "...",
}
REQUIRED_EXTERNAL_SECRET_KEYS = {
    "BRAIN_AUTH_PASSWORD": {
        "",
        "replace-me",
        "...",
    },
}


ORDERED_KEYS = [
    "BRAIN_CONFIG_RENDER_SHA",
    "BRAIN_CONFIG_RENDERED_AT",
    "BRAIN_CONFIG_RENDER_SOURCE",
    "PROFILE",
    "LLM_PROVIDER",
    "LLM_MODEL",
    "LLM_API_KEY",
    "LLM_ENDPOINT",
    "LLM_TEMPERATURE",
    "LLM_MAX_TOKENS",
    "OPENAI_AUTH_MODE",
    "OPENAI_CODEX_AUTH_PROFILE",
    "OPENAI_CODEX_BASE_URL",
    "BRAIN_PROVIDER_AUTH_PROFILES_PATH",
    "BRAIN_PROVIDER_AUTH_STATE_DIR",
    "EMBEDDING_PROVIDER",
    "EMBEDDING_MODEL",
    "EMBEDDING_API_KEY",
    "EMBEDDING_DIMENSIONS",
    "OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "ANTHROPIC_API_KEY",
    "AWS_REGION",
    "AWS_DEFAULT_REGION",
    "AWS_PROFILE",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "AWS_BEARER_TOKEN_BEDROCK",
    "GROQ_API_KEY",
    "VOYAGE_API_KEY",
    "GOOGLE_FREE_TIER",
    "GRAPH_DATABASE_PROVIDER",
    "GRAPH_DATABASE_URL",
    "GRAPH_DATABASE_NAME",
    "GRAPH_DATABASE_USERNAME",
    "GRAPH_DATABASE_PASSWORD",
    "VECTOR_DB_PROVIDER",
    "VECTOR_DB_URL",
    "DB_PROVIDER",
    "DB_NAME",
    "SYSTEM_ROOT_DIRECTORY",
    "DATA_ROOT_DIRECTORY",
    "BRAIN_DATABASE_URL",
    "BRAIN_MCP_HOST",
    "BRAIN_MCP_PORT",
    "BRAIN_MCP_PATH",
    "BRAIN_PUBLIC_BASE_URL",
    "BRAIN_PUBLIC_MCP_PATH",
    "BRAIN_BACKUP_DIR",
    "BRAIN_NEO4J_DUMP_ENABLED",
    "BRAIN_NEO4J_STOP_FOR_DUMP",
    "BRAIN_NEO4J_BREW_SERVICE",
    "BRAIN_NEO4J_LAUNCHD_LABEL",
    "BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED",
    "BRAIN_GOOGLE_DRIVE_FOLDER",
    "BRAIN_GOOGLE_DRIVE_LOCAL_PATH",
    "BRAIN_AUTH_ENABLED",
    "BRAIN_AUTH_TOKEN",
    "BRAIN_AUTH_PASSWORD_FILE",
    "BRAIN_AUTH_STATE_PATH",
    "BRAIN_AUTH_SCOPES",
    "BRAIN_AUTH_REQUIRE_PKCE",
    "BRAIN_AUTH_ACCESS_TOKEN_SECONDS",
    "BRAIN_AUTH_REFRESH_TOKEN_SECONDS",
    "BRAIN_REQUEST_LOG_ENABLED",
    "BRAIN_REQUEST_LOG_PATH",
    "BRAIN_REQUEST_LOG_MAX_BODY_BYTES",
    "BRAIN_TASTE_ENABLED",
    "BRAIN_TASTE_LLM_ROUTING_ENABLED",
    "BRAIN_TASTE_AUTO_ENRICH_ENABLED",
    "BRAIN_TASTE_OMDB_API_KEY",
    "BRAIN_TASTE_WEB_ENRICHMENT_ENABLED",
    "BRAIN_TASTE_GOOGLE_PLACES_API_KEY",
    "BRAIN_TASTE_AUTO_WRITE_THRESHOLD",
    "BRAIN_TASTE_CONFIRMATION_THRESHOLD",
    "BRAIN_TASTE_OPEN_LOOP_CLOSE_THRESHOLD",
    "BRAIN_TASTE_OPEN_LOOP_CONFIRMATION_THRESHOLD",
    "BRAIN_TASTE_PROPOSAL_EXPIRY_HOURS",
    "ENABLE_BACKEND_ACCESS_CONTROL",
    "BRAIN_UI_ENABLED",
    "BRAIN_UI_HOST",
    "BRAIN_UI_PROXY_PORT",
    "BRAIN_UI_FRONTEND_PORT",
    "BRAIN_UI_BACKEND_PORT",
    "BRAIN_PUBLIC_UI_PATH",
    "BRAIN_PUBLIC_UI_API_PATH",
    "BRAIN_UI_SESSION_SECONDS",
    "BRAIN_SLACK_AGENT_ENABLED",
    "BRAIN_SLACK_AGENT_HOST",
    "BRAIN_SLACK_AGENT_PORT",
    "BRAIN_SLACK_SIGNING_SECRET",
    "BRAIN_SLACK_BOT_TOKEN",
    "BRAIN_SLACK_ALLOWED_TEAM_IDS",
    "BRAIN_SLACK_ALLOWED_CHANNEL_IDS",
    "BRAIN_SLACK_ALLOWED_USER_IDS",
    "BRAIN_SLACK_ADMIN_USER_IDS",
    "BRAIN_SLACK_AUTO_COMMIT_HIGH_CONFIDENCE",
]


DEFAULTS = {
    "PROFILE": "openai",
    "LLM_PROVIDER": DEFAULT_LLM_PROVIDER,
    "LLM_MODEL": DEFAULT_LLM_MODEL,
    "LLM_TEMPERATURE": "0.0",
    "LLM_MAX_TOKENS": "8192",
    "OPENAI_AUTH_MODE": "oauth",
    "OPENAI_CODEX_AUTH_PROFILE": "default",
    "OPENAI_CODEX_BASE_URL": "https://chatgpt.com/backend-api/codex",
    "BRAIN_PROVIDER_AUTH_PROFILES_PATH": str(SECRETS_DIR / "provider-auth-profiles.json"),
    "BRAIN_PROVIDER_AUTH_STATE_DIR": str(SECRETS_DIR / "provider-auth-state"),
    "EMBEDDING_PROVIDER": DEFAULT_EMBEDDING_PROVIDER,
    "EMBEDDING_MODEL": DEFAULT_EMBEDDING_MODEL,
    "EMBEDDING_DIMENSIONS": str(DEFAULT_EMBEDDING_DIMENSIONS),
    "GRAPH_DATABASE_PROVIDER": "neo4j",
    "GRAPH_DATABASE_URL": "bolt://localhost:7687",
    "GRAPH_DATABASE_NAME": "neo4j",
    "GRAPH_DATABASE_USERNAME": "neo4j",
    "GRAPH_DATABASE_PASSWORD": "change-me",
    "VECTOR_DB_PROVIDER": "lancedb",
    "VECTOR_DB_URL": str(DATA_DIR / "lancedb" / "cognee.lancedb"),
    "DB_PROVIDER": "sqlite",
    "DB_NAME": "cognee_db",
    "SYSTEM_ROOT_DIRECTORY": str(DATA_DIR / "system"),
    "DATA_ROOT_DIRECTORY": str(DATA_DIR / "data"),
    "BRAIN_DATABASE_URL": f"sqlite:///{DATA_DIR / 'brain' / 'brain.db'}",
    "BRAIN_MCP_HOST": "127.0.0.1",
    "BRAIN_MCP_PORT": "8000",
    "BRAIN_MCP_PATH": "/mcp",
    "BRAIN_PUBLIC_BASE_URL": "https://brain.dceb.net",
    "BRAIN_PUBLIC_MCP_PATH": "/mcp",
    "BRAIN_BACKUP_DIR": str(BACKUP_DIR),
    "BRAIN_NEO4J_DUMP_ENABLED": "true",
    "BRAIN_NEO4J_STOP_FOR_DUMP": "true",
    "BRAIN_NEO4J_BREW_SERVICE": "neo4j",
    "BRAIN_NEO4J_LAUNCHD_LABEL": "homebrew.mxcl.neo4j",
    "BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED": "true",
    "BRAIN_GOOGLE_DRIVE_FOLDER": "backup/brain",
    "BRAIN_AUTH_ENABLED": "true",
    "BRAIN_AUTH_PASSWORD_FILE": str(SECRETS_DIR / "brain-auth-password"),
    "BRAIN_AUTH_STATE_PATH": str(SECRETS_DIR / "brain-oauth.json"),
    "BRAIN_AUTH_SCOPES": "brain.memory.read brain.memory.write",
    "BRAIN_AUTH_REQUIRE_PKCE": "true",
    "BRAIN_AUTH_ACCESS_TOKEN_SECONDS": "3600",
    "BRAIN_AUTH_REFRESH_TOKEN_SECONDS": "2592000",
    "BRAIN_REQUEST_LOG_ENABLED": "true",
    "BRAIN_REQUEST_LOG_PATH": str(LOG_DIR / "requests.jsonl"),
    "BRAIN_REQUEST_LOG_MAX_BODY_BYTES": "0",
    "BRAIN_TASTE_ENABLED": "true",
    "BRAIN_TASTE_LLM_ROUTING_ENABLED": "false",
    "BRAIN_TASTE_AUTO_ENRICH_ENABLED": "true",
    "BRAIN_TASTE_WEB_ENRICHMENT_ENABLED": "true",
    "BRAIN_TASTE_AUTO_WRITE_THRESHOLD": "0.95",
    "BRAIN_TASTE_CONFIRMATION_THRESHOLD": "0.70",
    "BRAIN_TASTE_OPEN_LOOP_CLOSE_THRESHOLD": "0.97",
    "BRAIN_TASTE_OPEN_LOOP_CONFIRMATION_THRESHOLD": "0.80",
    "BRAIN_TASTE_PROPOSAL_EXPIRY_HOURS": "24",
    "ENABLE_BACKEND_ACCESS_CONTROL": "false",
    "BRAIN_UI_ENABLED": "true",
    "BRAIN_UI_HOST": "127.0.0.1",
    "BRAIN_UI_PROXY_PORT": "8002",
    "BRAIN_UI_FRONTEND_PORT": "3000",
    "BRAIN_UI_BACKEND_PORT": "8001",
    "BRAIN_PUBLIC_UI_PATH": "/ui",
    "BRAIN_PUBLIC_UI_API_PATH": "/ui-api",
    "BRAIN_UI_SESSION_SECONDS": "43200",
    "BRAIN_SLACK_AGENT_ENABLED": "true",
    "BRAIN_SLACK_AGENT_HOST": "127.0.0.1",
    "BRAIN_SLACK_AGENT_PORT": "8003",
    "BRAIN_SLACK_ALLOWED_TEAM_IDS": "",
    "BRAIN_SLACK_ALLOWED_CHANNEL_IDS": "",
    "BRAIN_SLACK_ALLOWED_USER_IDS": "",
    "BRAIN_SLACK_ADMIN_USER_IDS": "",
    "BRAIN_SLACK_AUTO_COMMIT_HIGH_CONFIDENCE": "false",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(SECRETS_DIR / "brain.env"))
    parser.add_argument("--base-output", default=None)
    parser.add_argument("--auth-password-file", default=str(SECRETS_DIR / "brain-auth-password"))
    parser.add_argument("--auth-password-base-file", default=None)
    parser.add_argument(
        "--force-config-override",
        action="store_true",
        help="Bypass three-way conflict checks and establish a new prod config baseline.",
    )
    args = parser.parse_args()

    output = Path(args.output)
    base_output = Path(args.base_output) if args.base_output else last_deployed_path(output)
    auth_password_file = Path(args.auth_password_file)
    auth_password_base_file = (
        Path(args.auth_password_base_file)
        if args.auth_password_base_file
        else last_deployed_path(auth_password_file)
    )
    output.parent.mkdir(parents=True, exist_ok=True)

    rendered = render_values()
    missing = missing_required_values(rendered)
    if missing:
        print(
            "missing required GitHub Secrets/Vars: " + ", ".join(sorted(missing)),
            file=sys.stderr,
        )
        return 2

    if not args.force_config_override:
        conflicts = config_conflicts(
            proposed=rendered,
            current=parse_env_file(output),
            base=parse_env_file(base_output),
            current_exists=output.exists(),
            base_exists=base_output.exists(),
        )
        auth_password_conflict = external_secret_conflict(
            name="BRAIN_AUTH_PASSWORD",
            proposed=os.environ.get("BRAIN_AUTH_PASSWORD", ""),
            current=read_secret_file(auth_password_file),
            base=read_secret_file(auth_password_base_file),
            current_exists=auth_password_file.exists(),
            base_exists=auth_password_base_file.exists(),
        )
        if auth_password_conflict:
            conflicts.append(auth_password_conflict)
        if conflicts:
            print("production config conflict; propagate prod edits to GitHub first:", file=sys.stderr)
            for key in conflicts:
                print(f"- {key}", file=sys.stderr)
            print("Use --force-config-override only to intentionally re-baseline prod.", file=sys.stderr)
            return 3

    write_env_file(output, rendered)
    write_env_file(base_output, rendered)
    write_secret_file(auth_password_file, os.environ["BRAIN_AUTH_PASSWORD"])
    write_secret_file(auth_password_base_file, os.environ["BRAIN_AUTH_PASSWORD"])
    print(f"wrote {output}")
    return 0


def parse_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.removeprefix("export ").strip()
        value = value.strip()
        try:
            parsed = shlex.split(value, comments=False, posix=True)
            value = parsed[0] if parsed else ""
        except ValueError:
            value = value.strip("'\"")
        values[key] = value
    return values


def render_values() -> dict[str, str]:
    metadata = render_metadata()
    values: dict[str, str] = {}
    for key in ORDERED_KEYS:
        if key in metadata:
            values[key] = metadata[key]
        elif key in os.environ and os.environ[key] != "":
            values[key] = os.environ[key]
        elif key in DEFAULTS:
            values[key] = DEFAULTS[key]
        else:
            values[key] = ""
    return values


def write_env_file(path: Path, values: dict[str, str]) -> None:
    lines = [f"{key}={quote_env(value)}" for key, value in values.items() if value != ""]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    path.chmod(0o600)


def quote_env(value: str) -> str:
    if value == "":
        return ""
    if any(char.isspace() for char in value) or any(char in value for char in "\"'#$`\\"):
        return shlex.quote(value)
    return value


def render_metadata() -> dict[str, str]:
    return {
        "BRAIN_CONFIG_RENDER_SHA": render_sha(),
        "BRAIN_CONFIG_RENDERED_AT": datetime.now(UTC).isoformat(timespec="seconds"),
        "BRAIN_CONFIG_RENDER_SOURCE": (
            "github-actions" if os.getenv("GITHUB_ACTIONS") == "true" else "local"
        ),
    }


def render_sha() -> str:
    if value := os.getenv("GITHUB_SHA"):
        return value
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            encoding="utf-8",
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def missing_required_values(values: dict[str, str]) -> set[str]:
    missing = {
        key
        for key, disallowed_values in REQUIRED_CONFIG_KEYS.items()
        if is_placeholder_value(values.get(key, ""), disallowed_values)
    }
    if values.get("OPENAI_AUTH_MODE") == "api_key" and is_placeholder_value(
        values.get("OPENAI_API_KEY", ""),
        OPENAI_API_KEY_PLACEHOLDERS,
    ):
        missing.add("OPENAI_API_KEY")
    missing.update(
        key
        for key, disallowed_values in REQUIRED_EXTERNAL_SECRET_KEYS.items()
        if is_placeholder_value(os.environ.get(key, ""), disallowed_values)
    )
    return missing


def is_placeholder_value(value: str, disallowed_values: set[str]) -> bool:
    stripped = value.strip()
    return stripped in disallowed_values or stripped.endswith("...")


def config_conflicts(
    *,
    proposed: dict[str, str],
    current: dict[str, str],
    base: dict[str, str],
    current_exists: bool,
    base_exists: bool,
) -> list[str]:
    if current_exists and not base_exists:
        return ["brain.env.last-deployed"]

    conflicts: list[str] = []
    keys = (set(proposed) | set(current) | set(base)) - METADATA_KEYS
    for key in sorted(keys):
        proposed_value = proposed.get(key, "")
        current_value = current.get(key, "")
        base_value = base.get(key, "")
        if proposed_value == current_value or current_value == base_value:
            continue
        conflicts.append(key)
    return conflicts


def external_secret_conflict(
    *,
    name: str,
    proposed: str,
    current: str,
    base: str,
    current_exists: bool,
    base_exists: bool,
) -> str | None:
    if current_exists and not base_exists:
        return f"{name}.last-deployed"
    if proposed == current or current == base:
        return None
    return name


def last_deployed_path(path: Path) -> Path:
    return path.with_name(f"{path.name}.last-deployed")


def read_secret_file(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def write_secret_file(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip("\n") + "\n", encoding="utf-8")
    path.chmod(0o600)


if __name__ == "__main__":
    raise SystemExit(main())
