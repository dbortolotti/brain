#!/usr/bin/env bash
set -euo pipefail

APP_NAME="brain"
DEPLOY_ENV="${BRAIN_DEPLOY_ENV:-prod}"
if [[ "$DEPLOY_ENV" != "prod" && "$DEPLOY_ENV" != "staging" ]]; then
  printf 'BRAIN_DEPLOY_ENV must be prod or staging, got: %s\n' "$DEPLOY_ENV" >&2
  exit 2
fi
ENV_SUFFIX="$DEPLOY_ENV"
DEFAULT_ROOT="/Volumes/xpg_usb4/$DEPLOY_ENV/brain"
DEFAULT_PUBLIC_BASE_URL="https://brain.dceb.net"
DEFAULT_MCP_PORT="18000"
DEFAULT_UI_PROXY_PORT="18002"
DEFAULT_UI_FRONTEND_PORT="13000"
DEFAULT_UI_BACKEND_PORT="18001"
DEFAULT_SLACK_AGENT_PORT="18003"
DEFAULT_DB_PORT="15432"
DEFAULT_NEO4J_HTTP_PORT="17474"
DEFAULT_NEO4J_BOLT_PORT="17687"
DEFAULT_GOOGLE_DRIVE_BACKUP_ENABLED="true"
if [[ "$DEPLOY_ENV" == "staging" ]]; then
  DEFAULT_PUBLIC_BASE_URL="https://brain-staging.dceb.net"
  DEFAULT_MCP_PORT="18100"
  DEFAULT_UI_PROXY_PORT="18102"
  DEFAULT_UI_FRONTEND_PORT="13100"
  DEFAULT_UI_BACKEND_PORT="18101"
  DEFAULT_SLACK_AGENT_PORT="18103"
  DEFAULT_DB_PORT="16432"
  DEFAULT_NEO4J_HTTP_PORT="18474"
  DEFAULT_NEO4J_BOLT_PORT="18687"
  DEFAULT_GOOGLE_DRIVE_BACKUP_ENABLED="false"
fi
LABEL="${BRAIN_LAUNCHD_LABEL:-com.brain.$ENV_SUFFIX.mcp}"
UI_LABEL="${BRAIN_UI_LAUNCHD_LABEL:-com.brain.$ENV_SUFFIX.ui}"
SLACK_LABEL="${BRAIN_SLACK_AGENT_LAUNCHD_LABEL:-com.brain.$ENV_SUFFIX.slack-agent}"
AGENT_MEMORY_LABEL="${BRAIN_AGENT_MEMORY_LAUNCHD_LABEL:-com.brain.$ENV_SUFFIX.agent-memory}"
LOG_ROTATION_LABEL="${BRAIN_LOG_ROTATION_LAUNCHD_LABEL:-com.brain.$ENV_SUFFIX.log-rotation}"
BACKUP_LABEL="${BRAIN_BACKUP_LAUNCHD_LABEL:-com.brain.$ENV_SUFFIX.backup}"
PROD_ROOT="${BRAIN_PROD_ROOT:-$DEFAULT_ROOT}"
BRAIN_PUBLIC_BASE_URL="${BRAIN_PUBLIC_BASE_URL:-$DEFAULT_PUBLIC_BASE_URL}"
BRAIN_MCP_PORT="${BRAIN_MCP_PORT:-$DEFAULT_MCP_PORT}"
BRAIN_UI_PROXY_PORT="${BRAIN_UI_PROXY_PORT:-$DEFAULT_UI_PROXY_PORT}"
BRAIN_UI_FRONTEND_PORT="${BRAIN_UI_FRONTEND_PORT:-$DEFAULT_UI_FRONTEND_PORT}"
BRAIN_UI_BACKEND_PORT="${BRAIN_UI_BACKEND_PORT:-$DEFAULT_UI_BACKEND_PORT}"
BRAIN_SLACK_AGENT_PORT="${BRAIN_SLACK_AGENT_PORT:-$DEFAULT_SLACK_AGENT_PORT}"
DB_PORT="${DB_PORT:-$DEFAULT_DB_PORT}"
VECTOR_DB_PORT="${VECTOR_DB_PORT:-$DB_PORT}"
BRAIN_NEO4J_HTTP_PORT="${BRAIN_NEO4J_HTTP_PORT:-$DEFAULT_NEO4J_HTTP_PORT}"
BRAIN_NEO4J_BOLT_PORT="${BRAIN_NEO4J_BOLT_PORT:-$DEFAULT_NEO4J_BOLT_PORT}"
BRAIN_DOCKER_PROJECT="${BRAIN_DOCKER_PROJECT:-brain-$ENV_SUFFIX}"
BRAIN_POSTGRES_CONTAINER="${BRAIN_POSTGRES_CONTAINER:-brain-$ENV_SUFFIX-postgres}"
BRAIN_NEO4J_CONTAINER="${BRAIN_NEO4J_CONTAINER:-brain-$ENV_SUFFIX-neo4j}"
BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED="${BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED:-$DEFAULT_GOOGLE_DRIVE_BACKUP_ENABLED}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPLOYMENT_CONFIG_DIR="$REPO_ROOT/deployment"
SHA="${GITHUB_SHA:-$(git -C "$REPO_ROOT" rev-parse HEAD)}"
SHORT_SHA="${SHA:0:12}"
FALLBACK_RELEASE_VERSION="$DEPLOY_ENV-$SHORT_SHA"
RELEASE_DIR="$PROD_ROOT/releases/$SHA"
CURRENT_LINK="$PROD_ROOT/current"
SHARED_DIR="$PROD_ROOT/shared"
SECRETS_DIR="$SHARED_DIR/secrets"
DATA_DIR="$SHARED_DIR/data"
BACKUP_DIR="$SHARED_DIR/backups"
LOG_DIR="$SHARED_DIR/logs"
DATABASE_URL="sqlite:///$DATA_DIR/brain/brain.db"
LOCAL_SUPPORT_DIR="$HOME/Library/Application Support/brain-$ENV_SUFFIX"
PLIST_SRC="$DEPLOYMENT_CONFIG_DIR/launchd/com.brain.mcp.plist.template"
PLIST_DST="$HOME/Library/LaunchAgents/$LABEL.plist"
UI_PLIST_SRC="$DEPLOYMENT_CONFIG_DIR/launchd/com.brain.ui.plist.template"
UI_PLIST_DST="$HOME/Library/LaunchAgents/$UI_LABEL.plist"
SLACK_PLIST_SRC="$DEPLOYMENT_CONFIG_DIR/launchd/com.brain.slack-agent.plist.template"
SLACK_PLIST_DST="$HOME/Library/LaunchAgents/$SLACK_LABEL.plist"
AGENT_MEMORY_PLIST_SRC="$DEPLOYMENT_CONFIG_DIR/launchd/com.brain.agent-memory.plist.template"
AGENT_MEMORY_PLIST_DST="$HOME/Library/LaunchAgents/$AGENT_MEMORY_LABEL.plist"
LOG_ROTATION_PLIST_SRC="$DEPLOYMENT_CONFIG_DIR/launchd/com.brain.log-rotation.plist.template"
LOG_ROTATION_PLIST_DST="$HOME/Library/LaunchAgents/$LOG_ROTATION_LABEL.plist"
BACKUP_PLIST_SRC="$DEPLOYMENT_CONFIG_DIR/launchd/com.brain.backup.plist.template"
BACKUP_PLIST_DST="$HOME/Library/LaunchAgents/$BACKUP_LABEL.plist"
NEWSYSLOG_SRC="$DEPLOYMENT_CONFIG_DIR/newsyslog/brain.conf"
NEWSYSLOG_DST="/etc/newsyslog.d/brain.conf"

log() {
  printf '[deploy] %s\n' "$*"
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    printf 'missing required command: %s\n' "$1" >&2
    exit 1
  }
}

require_cmd git
require_cmd rsync
require_cmd uv
require_cmd python3
require_cmd docker

ensure_env_var() {
  local key="$1"
  local value="$2"
  local env_file="$SECRETS_DIR/brain.env"
  if ! grep -q "^${key}=" "$env_file"; then
    printf '%s=%s\n' "$key" "$value" >>"$env_file"
  fi
}

set_env_var() {
  local key="$1"
  local value="$2"
  local env_file="$SECRETS_DIR/brain.env"
  python3 - "$env_file" "$key" "$value" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
key = sys.argv[2]
value = sys.argv[3]
line = f"{key}={value}"
lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
for index, existing in enumerate(lines):
    if existing.startswith(f"{key}="):
        lines[index] = line
        break
else:
    lines.append(line)
path.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY
}

read_env_var() {
  local key="$1"
  local env_file="$SECRETS_DIR/brain.env"
  if [[ ! -f "$env_file" ]]; then
    return 0
  fi
  python3 - "$env_file" "$key" <<'PY'
from pathlib import Path
import shlex
import sys

path = Path(sys.argv[1])
key = sys.argv[2]
for raw in path.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    existing_key, value = line.split("=", 1)
    existing_key = existing_key.removeprefix("export ").strip()
    if existing_key != key:
        continue
    try:
        parsed = shlex.split(value.strip(), comments=False, posix=True)
        print(parsed[0] if parsed else "")
    except ValueError:
        print(value.strip().strip("'\""))
    break
PY
}

write_release_metadata() {
  local path="$1"
  python3 - "$path" "$APP_NAME" "$DEPLOY_ENV" "$RELEASE_VERSION" "$RELEASE_SHA" "$RELEASE_DIR" <<'PY'
from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import sys

path, app, environment, version, sha, release_dir = sys.argv[1:]
payload = {
    "app": app,
    "environment": environment,
    "version": version,
    "sha": sha,
    "release_dir": release_dir,
    "deployed_at": datetime.now(UTC).isoformat(timespec="seconds"),
    "source": "github-actions" if "GITHUB_ACTIONS" in __import__("os").environ else "local",
}
target = Path(path)
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}

enable_launch_agent() {
  local label="$1"
  local plist="$2"
  local domain="gui/$(id -u)"

  launchctl enable "$domain/$label" >/dev/null 2>&1 || true
  launchctl bootout "$domain" "$plist" >/dev/null 2>&1 || true
  launchctl bootstrap "$domain" "$plist"
}

install_newsyslog_config() {
  if [[ ! -f "$NEWSYSLOG_SRC" ]]; then
    log "newsyslog config template not found; skipping"
    return
  fi
  if [[ -w "$(dirname "$NEWSYSLOG_DST")" ]]; then
    cp "$NEWSYSLOG_SRC" "$NEWSYSLOG_DST"
    chmod 644 "$NEWSYSLOG_DST"
    log "installed newsyslog config at $NEWSYSLOG_DST"
    return
  fi
  if command -v sudo >/dev/null 2>&1 && sudo -n true >/dev/null 2>&1; then
    sudo cp "$NEWSYSLOG_SRC" "$NEWSYSLOG_DST"
    sudo chmod 644 "$NEWSYSLOG_DST"
    log "installed newsyslog config at $NEWSYSLOG_DST"
    return
  fi
  log "cannot install $NEWSYSLOG_DST without sudo; launchd logs will not get daily system rotation"
}

render_plist() {
  local src="$1"
  local dst="$2"
  python3 - "$src" "$dst" "$DEPLOY_ENV" "$PROD_ROOT" "$BRAIN_PUBLIC_BASE_URL" \
    "$BRAIN_MCP_PORT" "$BRAIN_UI_PROXY_PORT" "$BRAIN_UI_FRONTEND_PORT" \
    "$BRAIN_UI_BACKEND_PORT" "$BRAIN_SLACK_AGENT_PORT" <<'PY'
from pathlib import Path
import sys

(
    src,
    dst,
    deploy_env,
    root,
    public_base_url,
    mcp_port,
    ui_proxy_port,
    ui_frontend_port,
    ui_backend_port,
    slack_agent_port,
) = sys.argv[1:]
text = Path(src).read_text(encoding="utf-8")
replacements = {
    "com.brain.prod.": f"com.brain.{deploy_env}.",
    "/Volumes/xpg_usb4/prod/brain": root,
    "https://brain.dceb.net": public_base_url,
    "18000": mcp_port,
    "18002": ui_proxy_port,
    "13000": ui_frontend_port,
    "18001": ui_backend_port,
    "18003": slack_agent_port,
    "brain-prod": f"brain-{deploy_env}",
    "--env prod": f"--env {deploy_env}",
}
if deploy_env != "prod":
    replacements.update(
        {
            "brain-ui.": f"brain-{deploy_env}-ui.",
            "brain-slack-agent.": f"brain-{deploy_env}-slack-agent.",
            "brain-agent-memory.": f"brain-{deploy_env}-agent-memory.",
            "brain-log-rotation.": f"brain-{deploy_env}-log-rotation.",
            "brain-backup.": f"brain-{deploy_env}-backup.",
        }
    )
for old, new in replacements.items():
    text = text.replace(old, new)
Path(dst).write_text(text, encoding="utf-8")
PY
}

is_true() {
  case "${1:-}" in
    1|true|TRUE|yes|YES|on|ON)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

log "creating $DEPLOY_ENV directories under $PROD_ROOT"
mkdir -p "$PROD_ROOT/releases" "$DATA_DIR" "$DATA_DIR/brain" "$BACKUP_DIR" "$SECRETS_DIR" "$LOG_DIR" "$HOME/Library/LaunchAgents" "$HOME/Library/Logs" "$LOCAL_SUPPORT_DIR"

if [[ ! -f "$SECRETS_DIR/brain.env" ]]; then
  log "creating starter $DEPLOY_ENV env at $SECRETS_DIR/brain.env"
  cat >"$SECRETS_DIR/brain.env" <<EOF
PROFILE=openai
BRAIN_LLM_ENABLED=false
LLM_PROVIDER=openai
LLM_MODEL=gpt-5.4-mini
LLM_TEMPERATURE=0.0
LLM_MAX_TOKENS=8192
OPENAI_AUTH_MODE=oauth
OPENAI_CODEX_AUTH_PROFILE=default
OPENAI_CODEX_BASE_URL=https://chatgpt.com/backend-api/codex
BRAIN_PROVIDER_AUTH_PROFILES_PATH=$SECRETS_DIR/provider-auth-profiles.json
BRAIN_PROVIDER_AUTH_STATE_DIR=$SECRETS_DIR/provider-auth-state
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_DIMENSIONS=3072
GRAPH_DATABASE_PROVIDER=neo4j
GRAPH_DATABASE_URL=bolt://127.0.0.1:$BRAIN_NEO4J_BOLT_PORT
GRAPH_DATABASE_NAME=neo4j
GRAPH_DATABASE_USERNAME=neo4j
GRAPH_DATABASE_PASSWORD=change-me
VECTOR_DB_PROVIDER=pgvector
VECTOR_DB_URL=
VECTOR_DB_PORT=$VECTOR_DB_PORT
VECTOR_DB_NAME=cognee_vectors
VECTOR_DB_KEY=
VECTOR_DATASET_DATABASE_HANDLER=pgvector
VECTOR_DB_USERNAME=cognee
VECTOR_DB_PASSWORD=cognee
VECTOR_DB_HOST=127.0.0.1
DB_PROVIDER=postgres
DB_NAME=cognee_db
DB_HOST=127.0.0.1
DB_PORT=$DB_PORT
DB_USERNAME=cognee
DB_PASSWORD=cognee
SYSTEM_ROOT_DIRECTORY=$DATA_DIR/system
DATA_ROOT_DIRECTORY=$DATA_DIR/data
BRAIN_DATABASE_URL=$DATABASE_URL
BRAIN_PROD_ROOT=$PROD_ROOT
BRAIN_MCP_HOST=127.0.0.1
BRAIN_MCP_PORT=$BRAIN_MCP_PORT
BRAIN_MCP_PATH=/mcp
BRAIN_ADMIN_MCP_PATH=/admin/mcp
BRAIN_APP_MCP_PATH=/app/mcp
BRAIN_PUBLIC_BASE_URL=$BRAIN_PUBLIC_BASE_URL
BRAIN_PUBLIC_MCP_PATH=/mcp
BRAIN_PUBLIC_ADMIN_MCP_PATH=/admin/mcp
BRAIN_PUBLIC_APP_MCP_PATH=/mcp
BRAIN_BACKUP_DIR=$BACKUP_DIR
BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED=$BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED
BRAIN_GOOGLE_DRIVE_FOLDER=backup/brain
BRAIN_AUTH_ENABLED=true
BRAIN_AUTH_PASSWORD_FILE=$SECRETS_DIR/brain-auth-password
BRAIN_AUTH_USERS_FILE=$SECRETS_DIR/brain-auth-users.json
BRAIN_AUTH_SUPERUSER_IDS=default
BRAIN_AUTH_STATE_PATH=$SECRETS_DIR/brain-oauth.json
BRAIN_AUTH_SCOPES="brain.memory.read brain.memory.write"
BRAIN_AUTH_REQUIRE_PKCE=true
BRAIN_AUTH_ACCESS_TOKEN_SECONDS=3600
BRAIN_AUTH_REFRESH_TOKEN_SECONDS=2592000
BRAIN_USER_ID=default
BRAIN_REQUEST_LOG_ENABLED=true
BRAIN_REQUEST_LOG_PATH=$LOG_DIR/requests/{date}.jsonl
BRAIN_REQUEST_LOG_MAX_BODY_BYTES=8192
BRAIN_REQUEST_LOG_RETENTION_DAYS=30
BRAIN_ROUTING_LOG_ENABLED=true
BRAIN_ROUTING_LOG_PATH=$LOG_DIR/routing/{date}.jsonl
BRAIN_ROUTING_LOG_RETENTION_DAYS=90
BRAIN_TASTE_ENABLED=true
BRAIN_TASTE_LLM_ROUTING_ENABLED=false
BRAIN_TASTE_AUTO_ENRICH_ENABLED=true
BRAIN_TASTE_WEB_ENRICHMENT_ENABLED=true
BRAIN_TASTE_AUTO_WRITE_THRESHOLD=0.95
BRAIN_TASTE_CONFIRMATION_THRESHOLD=0.70
BRAIN_TASTE_OPEN_LOOP_CLOSE_THRESHOLD=0.97
BRAIN_TASTE_OPEN_LOOP_CONFIRMATION_THRESHOLD=0.80
BRAIN_TASTE_PROPOSAL_EXPIRY_HOURS=24
ENABLE_BACKEND_ACCESS_CONTROL=false
BRAIN_UI_ENABLED=true
BRAIN_UI_HOST=127.0.0.1
BRAIN_UI_PROXY_PORT=$BRAIN_UI_PROXY_PORT
BRAIN_UI_FRONTEND_PORT=$BRAIN_UI_FRONTEND_PORT
BRAIN_UI_BACKEND_PORT=$BRAIN_UI_BACKEND_PORT
BRAIN_PUBLIC_UI_PATH=/cognee
BRAIN_PUBLIC_UI_API_PATH=/cognee-api
BRAIN_UI_SESSION_SECONDS=43200
BRAIN_SLACK_AGENT_ENABLED=true
BRAIN_SLACK_AGENT_HOST=127.0.0.1
BRAIN_SLACK_AGENT_PORT=$BRAIN_SLACK_AGENT_PORT
BRAIN_SLACK_SIGNING_SECRET=
BRAIN_SLACK_BOT_TOKEN=
BRAIN_SLACK_ALLOWED_TEAM_IDS=
BRAIN_SLACK_ALLOWED_CHANNEL_IDS=
BRAIN_SLACK_ALLOWED_USER_IDS=
BRAIN_SLACK_ADMIN_USER_IDS=
BRAIN_SLACK_AUTO_COMMIT_HIGH_CONFIDENCE=false
BRAIN_AGENT_MEMORY_SESSION_ID=portable_agent_session
BRAIN_RELEASE_ENV=$DEPLOY_ENV
BRAIN_RELEASE_SHA=$SHA
BRAIN_RELEASE_VERSION=$FALLBACK_RELEASE_VERSION
EOF
  chmod 600 "$SECRETS_DIR/brain.env"
fi

FILE_RELEASE_VERSION="$(read_env_var BRAIN_RELEASE_VERSION)"
FILE_RELEASE_SHA="$(read_env_var BRAIN_RELEASE_SHA)"
RELEASE_SHA="${BRAIN_RELEASE_SHA:-$SHA}"
if [[ -n "${BRAIN_RELEASE_VERSION:-}" ]]; then
  RELEASE_VERSION="$BRAIN_RELEASE_VERSION"
elif [[ "$FILE_RELEASE_SHA" == "$SHA" && -n "$FILE_RELEASE_VERSION" ]]; then
  RELEASE_VERSION="$FILE_RELEASE_VERSION"
else
  RELEASE_VERSION="$FALLBACK_RELEASE_VERSION"
fi
RELEASE_ENV="${BRAIN_RELEASE_ENV:-$DEPLOY_ENV}"
if [[ "$RELEASE_SHA" != "$SHA" ]]; then
  printf 'BRAIN_RELEASE_SHA must match deployed GITHUB_SHA: %s != %s\n' "$RELEASE_SHA" "$SHA" >&2
  exit 2
fi

ensure_env_var "BRAIN_AUTH_ENABLED" "true"
set_env_var "BRAIN_RELEASE_ENV" "$RELEASE_ENV"
set_env_var "BRAIN_RELEASE_SHA" "$RELEASE_SHA"
set_env_var "BRAIN_RELEASE_VERSION" "$RELEASE_VERSION"
ensure_env_var "OPENAI_AUTH_MODE" "oauth"
ensure_env_var "OPENAI_CODEX_AUTH_PROFILE" "default"
ensure_env_var "OPENAI_CODEX_BASE_URL" "https://chatgpt.com/backend-api/codex"
ensure_env_var "BRAIN_PROVIDER_AUTH_PROFILES_PATH" "$SECRETS_DIR/provider-auth-profiles.json"
ensure_env_var "BRAIN_PROVIDER_AUTH_STATE_DIR" "$SECRETS_DIR/provider-auth-state"
ensure_env_var "BRAIN_AUTH_PASSWORD_FILE" "$SECRETS_DIR/brain-auth-password"
ensure_env_var "BRAIN_AUTH_USERS_FILE" "$SECRETS_DIR/brain-auth-users.json"
ensure_env_var "BRAIN_AUTH_SUPERUSER_IDS" "default"
ensure_env_var "BRAIN_AUTH_STATE_PATH" "$SECRETS_DIR/brain-oauth.json"
ensure_env_var "BRAIN_AUTH_SCOPES" '"brain.memory.read brain.memory.write"'
ensure_env_var "BRAIN_AUTH_REQUIRE_PKCE" "true"
ensure_env_var "BRAIN_AUTH_ACCESS_TOKEN_SECONDS" "3600"
ensure_env_var "BRAIN_AUTH_REFRESH_TOKEN_SECONDS" "2592000"
ensure_env_var "BRAIN_USER_ID" "default"
ensure_env_var "BRAIN_REQUEST_LOG_ENABLED" "true"
set_env_var "BRAIN_REQUEST_LOG_PATH" "$LOG_DIR/requests/{date}.jsonl"
set_env_var "BRAIN_REQUEST_LOG_MAX_BODY_BYTES" "8192"
ensure_env_var "BRAIN_REQUEST_LOG_RETENTION_DAYS" "30"
ensure_env_var "BRAIN_ROUTING_LOG_ENABLED" "true"
set_env_var "BRAIN_ROUTING_LOG_PATH" "$LOG_DIR/routing/{date}.jsonl"
ensure_env_var "BRAIN_ROUTING_LOG_RETENTION_DAYS" "90"
ensure_env_var "BRAIN_DATABASE_URL" "$DATABASE_URL"
set_env_var "BRAIN_PROD_ROOT" "$PROD_ROOT"
set_env_var "BRAIN_MCP_PORT" "$BRAIN_MCP_PORT"
set_env_var "BRAIN_MCP_PATH" "/mcp"
set_env_var "BRAIN_ADMIN_MCP_PATH" "/admin/mcp"
set_env_var "BRAIN_APP_MCP_PATH" "/app/mcp"
set_env_var "BRAIN_PUBLIC_BASE_URL" "$BRAIN_PUBLIC_BASE_URL"
set_env_var "BRAIN_PUBLIC_MCP_PATH" "/mcp"
set_env_var "BRAIN_PUBLIC_ADMIN_MCP_PATH" "/admin/mcp"
set_env_var "BRAIN_PUBLIC_APP_MCP_PATH" "/mcp"
set_env_var "BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED" "$BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED"
set_env_var "GRAPH_DATABASE_URL" "bolt://127.0.0.1:$BRAIN_NEO4J_BOLT_PORT"
set_env_var "VECTOR_DB_PROVIDER" "pgvector"
set_env_var "VECTOR_DB_URL" ""
set_env_var "VECTOR_DB_PORT" "$VECTOR_DB_PORT"
set_env_var "VECTOR_DB_NAME" "cognee_vectors"
set_env_var "VECTOR_DB_KEY" ""
set_env_var "VECTOR_DATASET_DATABASE_HANDLER" "pgvector"
set_env_var "VECTOR_DB_USERNAME" "cognee"
set_env_var "VECTOR_DB_PASSWORD" "cognee"
set_env_var "VECTOR_DB_HOST" "127.0.0.1"
set_env_var "DB_PROVIDER" "postgres"
set_env_var "DB_NAME" "cognee_db"
set_env_var "DB_HOST" "127.0.0.1"
set_env_var "DB_PORT" "$DB_PORT"
set_env_var "DB_USERNAME" "cognee"
set_env_var "DB_PASSWORD" "cognee"
ensure_env_var "BRAIN_LLM_ENABLED" "false"
ensure_env_var "BRAIN_TASTE_ENABLED" "true"
ensure_env_var "BRAIN_TASTE_LLM_ROUTING_ENABLED" "false"
ensure_env_var "BRAIN_TASTE_AUTO_ENRICH_ENABLED" "true"
ensure_env_var "BRAIN_TASTE_WEB_ENRICHMENT_ENABLED" "true"
ensure_env_var "BRAIN_TASTE_AUTO_WRITE_THRESHOLD" "0.95"
ensure_env_var "BRAIN_TASTE_CONFIRMATION_THRESHOLD" "0.70"
ensure_env_var "BRAIN_TASTE_OPEN_LOOP_CLOSE_THRESHOLD" "0.97"
ensure_env_var "BRAIN_TASTE_OPEN_LOOP_CONFIRMATION_THRESHOLD" "0.80"
ensure_env_var "BRAIN_TASTE_PROPOSAL_EXPIRY_HOURS" "24"
ensure_env_var "ENABLE_BACKEND_ACCESS_CONTROL" "false"
ensure_env_var "BRAIN_UI_ENABLED" "true"
ensure_env_var "BRAIN_UI_HOST" "127.0.0.1"
set_env_var "BRAIN_UI_PROXY_PORT" "$BRAIN_UI_PROXY_PORT"
set_env_var "BRAIN_UI_FRONTEND_PORT" "$BRAIN_UI_FRONTEND_PORT"
set_env_var "BRAIN_UI_BACKEND_PORT" "$BRAIN_UI_BACKEND_PORT"
set_env_var "BRAIN_PUBLIC_UI_PATH" "/cognee"
set_env_var "BRAIN_PUBLIC_UI_API_PATH" "/cognee-api"
ensure_env_var "BRAIN_UI_SESSION_SECONDS" "43200"
ensure_env_var "BRAIN_SLACK_AGENT_ENABLED" "true"
ensure_env_var "BRAIN_SLACK_AGENT_HOST" "127.0.0.1"
set_env_var "BRAIN_SLACK_AGENT_PORT" "$BRAIN_SLACK_AGENT_PORT"
ensure_env_var "BRAIN_SLACK_SIGNING_SECRET" ""
ensure_env_var "BRAIN_SLACK_BOT_TOKEN" ""
ensure_env_var "BRAIN_SLACK_ALLOWED_TEAM_IDS" ""
ensure_env_var "BRAIN_SLACK_ALLOWED_CHANNEL_IDS" ""
ensure_env_var "BRAIN_SLACK_ALLOWED_USER_IDS" ""
ensure_env_var "BRAIN_SLACK_ADMIN_USER_IDS" ""
ensure_env_var "BRAIN_SLACK_AUTO_COMMIT_HIGH_CONFIDENCE" "false"
ensure_env_var "BRAIN_AGENT_MEMORY_SESSION_ID" "portable_agent_session"

if [[ ! -f "$SECRETS_DIR/brain-auth-password" ]]; then
  log "creating Brain OAuth password at $SECRETS_DIR/brain-auth-password"
  umask 077
  python3 - <<'PY' >"$SECRETS_DIR/brain-auth-password"
import secrets

print(secrets.token_urlsafe(24))
PY
  chmod 600 "$SECRETS_DIR/brain-auth-password"
fi

if [[ ! -f "$SECRETS_DIR/brain-auth-users.json" ]]; then
  log "creating Brain OAuth users registry at $SECRETS_DIR/brain-auth-users.json"
  umask 077
  BRAIN_AUTH_PASSWORD_PATH="$SECRETS_DIR/brain-auth-password" \
  BRAIN_AUTH_ROOT_PASSWORD_PATH="$SECRETS_DIR/brain-auth-root-password" \
  BRAIN_AUTH_USERS_PATH="$SECRETS_DIR/brain-auth-users.json" \
  python3 - <<'PY'
import json
import os
import secrets
from pathlib import Path

auth_password = Path(os.environ["BRAIN_AUTH_PASSWORD_PATH"]).read_text(encoding="utf-8").strip()
root_password_path = Path(os.environ["BRAIN_AUTH_ROOT_PASSWORD_PATH"])
if root_password_path.exists():
    root_password = root_password_path.read_text(encoding="utf-8").strip()
else:
    root_password = secrets.token_urlsafe(32)
    root_password_path.write_text(root_password + "\n", encoding="utf-8")
    root_password_path.chmod(0o600)

users_path = Path(os.environ["BRAIN_AUTH_USERS_PATH"])
users_path.write_text(
    json.dumps(
        [
            {
                "id": "default",
                "password": root_password,
                "display_name": "Root",
                "email": "",
                "superuser": True,
            },
            {
                "id": "daniele",
                "password": auth_password,
                "display_name": "Daniele Bortolotti",
                "email": "",
                "superuser": False,
            },
        ],
        indent=2,
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)
users_path.chmod(0o600)
PY
fi

if [[ ! -d "$RELEASE_DIR" ]]; then
  log "creating release $SHORT_SHA"
  mkdir -p "$RELEASE_DIR"
  rsync -a --delete \
    --exclude '.git' \
    --exclude '.env' \
    --exclude '.data' \
    --exclude '.venv' \
    --exclude '__pycache__' \
    --exclude '.pytest_cache' \
    --exclude '.ruff_cache' \
    "$REPO_ROOT/" "$RELEASE_DIR/"
else
  log "release already exists: $RELEASE_DIR"
fi
rm -f "$RELEASE_DIR/.env"

log "installing dependencies in release"
(
  cd "$RELEASE_DIR"
  uv sync --all-extras
)
chmod +x "$RELEASE_DIR/scripts/run-cognee-ui-production.sh"
cp "$RELEASE_DIR/scripts/run-cognee-ui-production.sh" "$LOCAL_SUPPORT_DIR/run-cognee-ui-production.sh"
chmod +x "$LOCAL_SUPPORT_DIR/run-cognee-ui-production.sh"

log "linking shared mutable state"
mkdir -p "$RELEASE_DIR/.data"
ln -sfn "$DATA_DIR" "$RELEASE_DIR/.data/shared"

export ENV_FILE="$SECRETS_DIR/brain.env"
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

if [[ -z "${GRAPH_DATABASE_PASSWORD:-}" || "$GRAPH_DATABASE_PASSWORD" == "change-me" || "$GRAPH_DATABASE_PASSWORD" == "replace-me" ]]; then
  echo "GRAPH_DATABASE_PASSWORD must be set to a real secret before starting prod Neo4j" >&2
  exit 1
fi

log "starting $DEPLOY_ENV Postgres/pgvector and Neo4j containers"
(
  cd "$RELEASE_DIR"
  GRAPH_DATABASE_PASSWORD="$GRAPH_DATABASE_PASSWORD" \
    DB_NAME="${DB_NAME:-cognee_db}" \
    DB_USERNAME="${DB_USERNAME:-cognee}" \
    DB_PASSWORD="${DB_PASSWORD:-cognee}" \
    DB_PORT="${DB_PORT:-$DEFAULT_DB_PORT}" \
    BRAIN_PROD_ROOT="$PROD_ROOT" \
    BRAIN_DOCKER_PROJECT="$BRAIN_DOCKER_PROJECT" \
    BRAIN_POSTGRES_CONTAINER="$BRAIN_POSTGRES_CONTAINER" \
    BRAIN_NEO4J_CONTAINER="$BRAIN_NEO4J_CONTAINER" \
    BRAIN_NEO4J_HTTP_PORT="$BRAIN_NEO4J_HTTP_PORT" \
    BRAIN_NEO4J_BOLT_PORT="$BRAIN_NEO4J_BOLT_PORT" \
    docker compose -p "$BRAIN_DOCKER_PROJECT" -f deployment/docker-compose.prod.yml up -d postgres neo4j
)

log "running Brain database migrations"
(
  cd "$RELEASE_DIR"
  uv run alembic upgrade head
)

MODEL_SMOKE_SCOPE="${BRAIN_MODEL_SMOKE_SCOPE:-active}"
if [[ "$MODEL_SMOKE_SCOPE" != "none" ]]; then
  log "running pre-promotion live model smoke scope=$MODEL_SMOKE_SCOPE"
  smoke_args=(--scope "$MODEL_SMOKE_SCOPE")
  if is_true "${BRAIN_MODEL_SMOKE_SKIP_MISSING_KEYS:-false}"; then
    smoke_args+=(--skip-missing-keys)
  fi
  if [[ -n "${BRAIN_MODEL_SMOKE_TIMEOUT_SECONDS:-}" ]]; then
    smoke_args+=(--timeout "$BRAIN_MODEL_SMOKE_TIMEOUT_SECONDS")
  fi
  (
    cd "$RELEASE_DIR"
    uv run python scripts/live_model_smoke.py "${smoke_args[@]}"
  )
else
  log "pre-promotion live model smoke disabled"
fi

log "installing launchd plist"
render_plist "$PLIST_SRC" "$PLIST_DST"
plutil -lint "$PLIST_DST" >/dev/null
render_plist "$UI_PLIST_SRC" "$UI_PLIST_DST"
plutil -lint "$UI_PLIST_DST" >/dev/null
render_plist "$SLACK_PLIST_SRC" "$SLACK_PLIST_DST"
plutil -lint "$SLACK_PLIST_DST" >/dev/null
render_plist "$AGENT_MEMORY_PLIST_SRC" "$AGENT_MEMORY_PLIST_DST"
plutil -lint "$AGENT_MEMORY_PLIST_DST" >/dev/null
render_plist "$LOG_ROTATION_PLIST_SRC" "$LOG_ROTATION_PLIST_DST"
plutil -lint "$LOG_ROTATION_PLIST_DST" >/dev/null
render_plist "$BACKUP_PLIST_SRC" "$BACKUP_PLIST_DST"
plutil -lint "$BACKUP_PLIST_DST" >/dev/null
if [[ "$DEPLOY_ENV" == "prod" ]]; then
  install_newsyslog_config
else
  log "skipping system newsyslog config for $DEPLOY_ENV"
fi

log "updating current symlink"
write_release_metadata "$RELEASE_DIR/release.json"
write_release_metadata "$SHARED_DIR/release.json"
printf '%s\n' "$RELEASE_VERSION" >"$SHARED_DIR/current-version"
ln -sfn "$RELEASE_DIR" "$CURRENT_LINK"

if command -v launchctl >/dev/null 2>&1; then
  log "restarting launchd service $LABEL"
  enable_launch_agent "$LABEL" "$PLIST_DST"
  log "restarting launchd service $UI_LABEL"
  enable_launch_agent "$UI_LABEL" "$UI_PLIST_DST"
  log "restarting launchd service $SLACK_LABEL"
  enable_launch_agent "$SLACK_LABEL" "$SLACK_PLIST_DST"
  log "reloading launchd job $AGENT_MEMORY_LABEL"
  enable_launch_agent "$AGENT_MEMORY_LABEL" "$AGENT_MEMORY_PLIST_DST"
  log "reloading launchd job $LOG_ROTATION_LABEL"
  enable_launch_agent "$LOG_ROTATION_LABEL" "$LOG_ROTATION_PLIST_DST"
  log "reloading launchd job $BACKUP_LABEL"
  enable_launch_agent "$BACKUP_LABEL" "$BACKUP_PLIST_DST"
else
  log "launchctl not found; skipping service restart"
fi

log "waiting for local health"
for attempt in {1..30}; do
  if curl -fsS "http://${BRAIN_MCP_HOST:-127.0.0.1}:${BRAIN_MCP_PORT:-18000}/healthz" >/dev/null 2>&1; then
    break
  fi
  if [[ "$attempt" == "30" ]]; then
    echo "local health did not become ready" >&2
    exit 1
  fi
  sleep 1
done

log "waiting for local UI health"
for attempt in {1..120}; do
  if curl -fsS "http://${BRAIN_UI_HOST:-127.0.0.1}:${BRAIN_UI_PROXY_PORT:-18002}/healthz" >/dev/null 2>&1; then
    break
  fi
  if [[ "$attempt" == "120" ]]; then
    echo "local UI health did not become ready" >&2
    exit 1
  fi
  sleep 1
done

log "waiting for local Slack agent health"
for attempt in {1..30}; do
  if curl -fsS "http://${BRAIN_SLACK_AGENT_HOST:-127.0.0.1}:${BRAIN_SLACK_AGENT_PORT:-18003}/slack/healthz" >/dev/null 2>&1; then
    break
  fi
  if [[ "$attempt" == "30" ]]; then
    echo "local Slack agent health did not become ready" >&2
    exit 1
  fi
  sleep 1
done

log "running $DEPLOY_ENV verifier"
(
  cd "$RELEASE_DIR"
  uv run python scripts/verify_mcp_production.py --skip-backups
  uv run python scripts/verify_cognee_ui_production.py
  uv run python scripts/verify_slack_agent.py
)

log "deployed $APP_NAME $RELEASE_VERSION ($SHA)"
