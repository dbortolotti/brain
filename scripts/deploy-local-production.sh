#!/usr/bin/env bash
set -euo pipefail

APP_NAME="brain"
LABEL="com.brain.prod.mcp"
UI_LABEL="com.brain.prod.ui"
SLACK_LABEL="com.brain.prod.slack-agent"
AGENT_MEMORY_LABEL="com.brain.prod.agent-memory"
PROD_ROOT="${BRAIN_PROD_ROOT:-/Volumes/xpg_usb4/prod/brain}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPLOYMENT_CONFIG_DIR="$REPO_ROOT/deployment"
SHA="${GITHUB_SHA:-$(git -C "$REPO_ROOT" rev-parse HEAD)}"
SHORT_SHA="${SHA:0:12}"
RELEASE_DIR="$PROD_ROOT/releases/$SHA"
CURRENT_LINK="$PROD_ROOT/current"
SHARED_DIR="$PROD_ROOT/shared"
SECRETS_DIR="$SHARED_DIR/secrets"
DATA_DIR="$SHARED_DIR/data"
BACKUP_DIR="$SHARED_DIR/backups"
LOG_DIR="$SHARED_DIR/logs"
DATABASE_URL="sqlite:///$DATA_DIR/brain/brain.db"
LOCAL_SUPPORT_DIR="$HOME/Library/Application Support/brain"
PLIST_SRC="$DEPLOYMENT_CONFIG_DIR/launchd/com.brain.mcp.plist.template"
PLIST_DST="$HOME/Library/LaunchAgents/$LABEL.plist"
UI_PLIST_SRC="$DEPLOYMENT_CONFIG_DIR/launchd/com.brain.ui.plist.template"
UI_PLIST_DST="$HOME/Library/LaunchAgents/$UI_LABEL.plist"
SLACK_PLIST_SRC="$DEPLOYMENT_CONFIG_DIR/launchd/com.brain.slack-agent.plist.template"
SLACK_PLIST_DST="$HOME/Library/LaunchAgents/$SLACK_LABEL.plist"
AGENT_MEMORY_PLIST_SRC="$DEPLOYMENT_CONFIG_DIR/launchd/com.brain.agent-memory.plist.template"
AGENT_MEMORY_PLIST_DST="$HOME/Library/LaunchAgents/$AGENT_MEMORY_LABEL.plist"

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

enable_launch_agent() {
  local label="$1"
  local plist="$2"
  local domain="gui/$(id -u)"

  launchctl enable "$domain/$label" >/dev/null 2>&1 || true
  launchctl bootout "$domain" "$plist" >/dev/null 2>&1 || true
  launchctl bootstrap "$domain" "$plist"
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

log "creating production directories under $PROD_ROOT"
mkdir -p "$PROD_ROOT/releases" "$DATA_DIR" "$BACKUP_DIR" "$SECRETS_DIR" "$LOG_DIR" "$HOME/Library/LaunchAgents" "$HOME/Library/Logs" "$LOCAL_SUPPORT_DIR"

if [[ ! -f "$SECRETS_DIR/brain.env" ]]; then
  log "creating starter production env at $SECRETS_DIR/brain.env"
  cat >"$SECRETS_DIR/brain.env" <<EOF
PROFILE=openai
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
GRAPH_DATABASE_URL=bolt://127.0.0.1:17687
GRAPH_DATABASE_NAME=neo4j
GRAPH_DATABASE_USERNAME=neo4j
GRAPH_DATABASE_PASSWORD=change-me
VECTOR_DB_PROVIDER=lancedb
VECTOR_DB_URL=$DATA_DIR/lancedb/cognee.lancedb
DB_PROVIDER=sqlite
DB_NAME=cognee_db
SYSTEM_ROOT_DIRECTORY=$DATA_DIR/system
DATA_ROOT_DIRECTORY=$DATA_DIR/data
BRAIN_DATABASE_URL=$DATABASE_URL
BRAIN_MCP_HOST=127.0.0.1
BRAIN_MCP_PORT=18000
BRAIN_MCP_PATH=/mcp
BRAIN_PUBLIC_BASE_URL=https://brain.dceb.net
BRAIN_PUBLIC_MCP_PATH=/mcp
BRAIN_BACKUP_DIR=$BACKUP_DIR
BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED=true
BRAIN_GOOGLE_DRIVE_FOLDER=backup/brain
BRAIN_AUTH_ENABLED=true
BRAIN_AUTH_PASSWORD_FILE=$SECRETS_DIR/brain-auth-password
BRAIN_AUTH_STATE_PATH=$SECRETS_DIR/brain-oauth.json
BRAIN_AUTH_SCOPES="brain.memory.read brain.memory.write"
BRAIN_AUTH_REQUIRE_PKCE=true
BRAIN_AUTH_ACCESS_TOKEN_SECONDS=3600
BRAIN_AUTH_REFRESH_TOKEN_SECONDS=2592000
BRAIN_REQUEST_LOG_ENABLED=true
BRAIN_REQUEST_LOG_PATH=$LOG_DIR/requests.jsonl
BRAIN_REQUEST_LOG_MAX_BODY_BYTES=0
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
BRAIN_UI_PROXY_PORT=18002
BRAIN_UI_FRONTEND_PORT=13000
BRAIN_UI_BACKEND_PORT=18001
BRAIN_PUBLIC_UI_PATH=/ui
BRAIN_PUBLIC_UI_API_PATH=/ui-api
BRAIN_UI_SESSION_SECONDS=43200
BRAIN_SLACK_AGENT_ENABLED=true
BRAIN_SLACK_AGENT_HOST=127.0.0.1
BRAIN_SLACK_AGENT_PORT=18003
BRAIN_SLACK_SIGNING_SECRET=
BRAIN_SLACK_BOT_TOKEN=
BRAIN_SLACK_ALLOWED_TEAM_IDS=
BRAIN_SLACK_ALLOWED_CHANNEL_IDS=
BRAIN_SLACK_ALLOWED_USER_IDS=
BRAIN_SLACK_ADMIN_USER_IDS=
BRAIN_SLACK_AUTO_COMMIT_HIGH_CONFIDENCE=false
BRAIN_AGENT_MEMORY_SESSION_ID=portable_agent_session
EOF
  chmod 600 "$SECRETS_DIR/brain.env"
fi

ensure_env_var "BRAIN_AUTH_ENABLED" "true"
ensure_env_var "OPENAI_AUTH_MODE" "oauth"
ensure_env_var "OPENAI_CODEX_AUTH_PROFILE" "default"
ensure_env_var "OPENAI_CODEX_BASE_URL" "https://chatgpt.com/backend-api/codex"
ensure_env_var "BRAIN_PROVIDER_AUTH_PROFILES_PATH" "$SECRETS_DIR/provider-auth-profiles.json"
ensure_env_var "BRAIN_PROVIDER_AUTH_STATE_DIR" "$SECRETS_DIR/provider-auth-state"
ensure_env_var "BRAIN_AUTH_PASSWORD_FILE" "$SECRETS_DIR/brain-auth-password"
ensure_env_var "BRAIN_AUTH_STATE_PATH" "$SECRETS_DIR/brain-oauth.json"
ensure_env_var "BRAIN_AUTH_SCOPES" '"brain.memory.read brain.memory.write"'
ensure_env_var "BRAIN_AUTH_REQUIRE_PKCE" "true"
ensure_env_var "BRAIN_AUTH_ACCESS_TOKEN_SECONDS" "3600"
ensure_env_var "BRAIN_AUTH_REFRESH_TOKEN_SECONDS" "2592000"
ensure_env_var "BRAIN_REQUEST_LOG_ENABLED" "true"
ensure_env_var "BRAIN_REQUEST_LOG_PATH" "$LOG_DIR/requests.jsonl"
ensure_env_var "BRAIN_REQUEST_LOG_MAX_BODY_BYTES" "0"
ensure_env_var "BRAIN_DATABASE_URL" "$DATABASE_URL"
set_env_var "BRAIN_MCP_PORT" "18000"
set_env_var "GRAPH_DATABASE_URL" "bolt://127.0.0.1:17687"
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
set_env_var "BRAIN_UI_PROXY_PORT" "18002"
set_env_var "BRAIN_UI_FRONTEND_PORT" "13000"
set_env_var "BRAIN_UI_BACKEND_PORT" "18001"
ensure_env_var "BRAIN_PUBLIC_UI_PATH" "/ui"
ensure_env_var "BRAIN_PUBLIC_UI_API_PATH" "/ui-api"
ensure_env_var "BRAIN_UI_SESSION_SECONDS" "43200"
ensure_env_var "BRAIN_SLACK_AGENT_ENABLED" "true"
ensure_env_var "BRAIN_SLACK_AGENT_HOST" "127.0.0.1"
set_env_var "BRAIN_SLACK_AGENT_PORT" "18003"
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

if [[ ! -d "$RELEASE_DIR" ]]; then
  log "creating release $SHORT_SHA"
  mkdir -p "$RELEASE_DIR"
  rsync -a --delete \
    --exclude '.git' \
    --exclude '.data' \
    --exclude '.venv' \
    --exclude '__pycache__' \
    --exclude '.pytest_cache' \
    --exclude '.ruff_cache' \
    "$REPO_ROOT/" "$RELEASE_DIR/"
else
  log "release already exists: $RELEASE_DIR"
fi

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

log "starting production Neo4j container"
(
  cd "$RELEASE_DIR"
  GRAPH_DATABASE_PASSWORD="$GRAPH_DATABASE_PASSWORD" \
    BRAIN_PROD_ROOT="$PROD_ROOT" \
    docker compose -f deployment/docker-compose.prod.yml up -d neo4j
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
cp "$PLIST_SRC" "$PLIST_DST"
plutil -lint "$PLIST_DST" >/dev/null
cp "$UI_PLIST_SRC" "$UI_PLIST_DST"
plutil -lint "$UI_PLIST_DST" >/dev/null
cp "$SLACK_PLIST_SRC" "$SLACK_PLIST_DST"
plutil -lint "$SLACK_PLIST_DST" >/dev/null
cp "$AGENT_MEMORY_PLIST_SRC" "$AGENT_MEMORY_PLIST_DST"
plutil -lint "$AGENT_MEMORY_PLIST_DST" >/dev/null

log "updating current symlink"
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

log "running production verifier"
(
  cd "$RELEASE_DIR"
  uv run python scripts/verify_mcp_production.py --skip-backups
  uv run python scripts/verify_cognee_ui_production.py
  uv run python scripts/verify_slack_agent.py
)

log "deployed $APP_NAME $SHA"
