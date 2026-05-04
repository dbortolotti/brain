#!/usr/bin/env bash
set -euo pipefail

APP_NAME="brain"
LABEL="com.brain.mcp"
PROD_ROOT="${BRAIN_PROD_ROOT:-/Volumes/xpg_usb4/prod/brain}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SHA="${GITHUB_SHA:-$(git -C "$REPO_ROOT" rev-parse HEAD)}"
SHORT_SHA="${SHA:0:12}"
RELEASE_DIR="$PROD_ROOT/releases/$SHA"
CURRENT_LINK="$PROD_ROOT/current"
SHARED_DIR="$PROD_ROOT/shared"
SECRETS_DIR="$SHARED_DIR/secrets"
DATA_DIR="$SHARED_DIR/data"
BACKUP_DIR="$SHARED_DIR/backups"
PLIST_SRC="$REPO_ROOT/launchd/com.brain.mcp.plist.template"
PLIST_DST="$HOME/Library/LaunchAgents/$LABEL.plist"

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

ensure_env_var() {
  local key="$1"
  local value="$2"
  local env_file="$SECRETS_DIR/brain.env"
  if ! grep -q "^${key}=" "$env_file"; then
    printf '%s=%s\n' "$key" "$value" >>"$env_file"
  fi
}

log "creating production directories under $PROD_ROOT"
mkdir -p "$PROD_ROOT/releases" "$DATA_DIR" "$BACKUP_DIR" "$SECRETS_DIR" "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"

if [[ ! -f "$SECRETS_DIR/brain.env" ]]; then
  log "creating starter production env at $SECRETS_DIR/brain.env"
  cat >"$SECRETS_DIR/brain.env" <<EOF
PROFILE=gemini
LLM_PROVIDER=gemini
LLM_MODEL=gemini/gemini-3.1-flash-lite-preview
LLM_API_KEY=replace-me
EMBEDDING_PROVIDER=gemini
EMBEDDING_MODEL=gemini/gemini-embedding-001
EMBEDDING_API_KEY=replace-me
EMBEDDING_DIMENSIONS=768
GRAPH_DATABASE_PROVIDER=neo4j
GRAPH_DATABASE_URL=bolt://localhost:7687
GRAPH_DATABASE_NAME=neo4j
GRAPH_DATABASE_USERNAME=neo4j
GRAPH_DATABASE_PASSWORD=change-me
VECTOR_DB_PROVIDER=lancedb
VECTOR_DB_URL=$DATA_DIR/lancedb/cognee.lancedb
DB_PROVIDER=sqlite
DB_NAME=cognee_db
SYSTEM_ROOT_DIRECTORY=$DATA_DIR/system
DATA_ROOT_DIRECTORY=$DATA_DIR/data
BRAIN_MCP_HOST=127.0.0.1
BRAIN_MCP_PORT=8000
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
EOF
  chmod 600 "$SECRETS_DIR/brain.env"
fi

ensure_env_var "BRAIN_AUTH_ENABLED" "true"
ensure_env_var "BRAIN_AUTH_PASSWORD_FILE" "$SECRETS_DIR/brain-auth-password"
ensure_env_var "BRAIN_AUTH_STATE_PATH" "$SECRETS_DIR/brain-oauth.json"
ensure_env_var "BRAIN_AUTH_SCOPES" '"brain.memory.read brain.memory.write"'
ensure_env_var "BRAIN_AUTH_REQUIRE_PKCE" "true"
ensure_env_var "BRAIN_AUTH_ACCESS_TOKEN_SECONDS" "3600"
ensure_env_var "BRAIN_AUTH_REFRESH_TOKEN_SECONDS" "2592000"

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
    --exclude 'eval/results/*.csv' \
    --exclude 'eval/results/raw/*' \
    "$REPO_ROOT/" "$RELEASE_DIR/"
else
  log "release already exists: $RELEASE_DIR"
fi

log "installing dependencies in release"
(
  cd "$RELEASE_DIR"
  uv sync --all-extras
)

log "linking shared mutable state"
mkdir -p "$RELEASE_DIR/.data"
ln -sfn "$DATA_DIR" "$RELEASE_DIR/.data/shared"

log "installing launchd plist"
cp "$PLIST_SRC" "$PLIST_DST"
plutil -lint "$PLIST_DST" >/dev/null

log "updating current symlink"
ln -sfn "$RELEASE_DIR" "$CURRENT_LINK"

if command -v launchctl >/dev/null 2>&1; then
  log "restarting launchd service $LABEL"
  launchctl bootout "gui/$(id -u)" "$PLIST_DST" >/dev/null 2>&1 || true
  launchctl bootstrap "gui/$(id -u)" "$PLIST_DST"
else
  log "launchctl not found; skipping service restart"
fi

log "waiting for local health"
for attempt in {1..30}; do
  if curl -fsS "http://127.0.0.1:8000/healthz" >/dev/null 2>&1; then
    break
  fi
  if [[ "$attempt" == "30" ]]; then
    echo "local health did not become ready" >&2
    exit 1
  fi
  sleep 1
done

log "running production verifier"
export ENV_FILE="$SECRETS_DIR/brain.env"
(
  cd "$RELEASE_DIR"
  uv run python scripts/verify_mcp_production.py --skip-backups
)

log "deployed $APP_NAME $SHA"
