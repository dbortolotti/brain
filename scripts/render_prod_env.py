#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shlex
from pathlib import Path


PROD_ROOT = Path(os.getenv("BRAIN_PROD_ROOT", "/Volumes/xpg_usb4/prod/brain"))
SHARED_DIR = PROD_ROOT / "shared"
SECRETS_DIR = SHARED_DIR / "secrets"
DATA_DIR = SHARED_DIR / "data"
BACKUP_DIR = SHARED_DIR / "backups"
LOG_DIR = SHARED_DIR / "logs"
CURRENT_LINK = PROD_ROOT / "current"


SECRET_KEYS = {
    "LLM_API_KEY",
    "EMBEDDING_API_KEY",
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "ANTHROPIC_API_KEY",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "AWS_BEARER_TOKEN_BEDROCK",
    "GROQ_API_KEY",
    "VOYAGE_API_KEY",
    "GRAPH_DATABASE_PASSWORD",
    "BRAIN_AUTH_TOKEN",
    "BRAIN_SLACK_SIGNING_SECRET",
    "BRAIN_SLACK_BOT_TOKEN",
}


ORDERED_KEYS = [
    "PROFILE",
    "LLM_PROVIDER",
    "LLM_MODEL",
    "LLM_API_KEY",
    "LLM_ENDPOINT",
    "LLM_TEMPERATURE",
    "LLM_MAX_TOKENS",
    "EMBEDDING_PROVIDER",
    "EMBEDDING_MODEL",
    "EMBEDDING_API_KEY",
    "EMBEDDING_DIMENSIONS",
    "OPENAI_API_KEY",
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
    "BRAIN_SLACK_RULES_PATH",
    "BRAIN_SLACK_AUTO_COMMIT_HIGH_CONFIDENCE",
]


DEFAULTS = {
    "PROFILE": "openai",
    "LLM_PROVIDER": "openai",
    "LLM_MODEL": "gpt-5.4-mini",
    "LLM_TEMPERATURE": "0.0",
    "LLM_MAX_TOKENS": "8192",
    "EMBEDDING_PROVIDER": "openai",
    "EMBEDDING_MODEL": "text-embedding-3-small",
    "EMBEDDING_DIMENSIONS": "1536",
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
    "BRAIN_SLACK_RULES_PATH": str(CURRENT_LINK / "config" / "slack_memory_agent_rules.md"),
    "BRAIN_SLACK_AUTO_COMMIT_HIGH_CONFIDENCE": "false",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(SECRETS_DIR / "brain.env"))
    parser.add_argument("--auth-password-file", default=str(SECRETS_DIR / "brain-auth-password"))
    parser.add_argument("--no-preserve-existing", action="store_true")
    args = parser.parse_args()

    output = Path(args.output)
    auth_password_file = Path(args.auth_password_file)
    output.parent.mkdir(parents=True, exist_ok=True)

    existing = {} if args.no_preserve_existing else parse_env_file(output)
    rendered = render_values(existing)
    write_env_file(output, rendered)
    maybe_write_auth_password(auth_password_file)

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


def render_values(existing: dict[str, str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for key in ORDERED_KEYS:
        if key in os.environ and os.environ[key] != "":
            values[key] = os.environ[key]
        elif key in existing:
            values[key] = existing[key]
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


def maybe_write_auth_password(path: Path) -> None:
    password = os.getenv("BRAIN_AUTH_PASSWORD")
    if not password:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(password.rstrip("\n") + "\n", encoding="utf-8")
    path.chmod(0o600)


if __name__ == "__main__":
    raise SystemExit(main())
