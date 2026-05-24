#!/usr/bin/env bash
set -euo pipefail

APP_NAME="brain"
DEPLOY_ENV="${BRAIN_DEPLOY_ENV:-prod}"
if [[ "$DEPLOY_ENV" != "prod" ]]; then
  printf 'cloud Linux deploy currently supports BRAIN_DEPLOY_ENV=prod only, got: %s\n' "$DEPLOY_ENV" >&2
  exit 2
fi

SERVICE_USER="${BRAIN_SERVICE_USER:-brain}"
PROD_ROOT="${BRAIN_PROD_ROOT:-/opt/brain}"
SUPPORT_DIR="${BRAIN_SUPPORT_DIR:-/var/lib/brain}"
SECRETS_DIR="${BRAIN_SECRETS_DIR:-/etc/brain}"
LOG_DIR="${BRAIN_LOG_DIR:-/var/log/brain}"
PUBLIC_BASE_URL="${BRAIN_PUBLIC_BASE_URL:-https://brain.dceb.net}"
BRAIN_MCP_PORT="${BRAIN_MCP_PORT:-18000}"
BRAIN_UI_PROXY_PORT="${BRAIN_UI_PROXY_PORT:-18002}"
BRAIN_UI_FRONTEND_PORT="${BRAIN_UI_FRONTEND_PORT:-13000}"
BRAIN_UI_BACKEND_PORT="${BRAIN_UI_BACKEND_PORT:-18001}"
DB_PORT="${DB_PORT:-15432}"
VECTOR_DB_PORT="${VECTOR_DB_PORT:-$DB_PORT}"
BRAIN_NEO4J_HTTP_PORT="${BRAIN_NEO4J_HTTP_PORT:-17474}"
BRAIN_NEO4J_BOLT_PORT="${BRAIN_NEO4J_BOLT_PORT:-17687}"
BRAIN_DOCKER_PROJECT="${BRAIN_DOCKER_PROJECT:-brain-prod}"
BRAIN_POSTGRES_CONTAINER="${BRAIN_POSTGRES_CONTAINER:-brain-prod-postgres}"
BRAIN_NEO4J_CONTAINER="${BRAIN_NEO4J_CONTAINER:-brain-prod-neo4j}"
BRAIN_NEO4J_CONTAINER_USER="${BRAIN_NEO4J_CONTAINER_USER:-7474:7474}"
BRAIN_DEPLOY_PYTHON="${BRAIN_DEPLOY_PYTHON:-3.12}"
BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED="${BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED:-false}"
BRAIN_MODEL_SMOKE_SCOPE="${BRAIN_MODEL_SMOKE_SCOPE:-none}"

SOURCE_TAR=""
RENDERED_ENV_FILE=""
RENDERED_ENV_BASE_FILE=""
RENDERED_AUTH_PASSWORD_FILE=""
RENDERED_AUTH_PASSWORD_BASE_FILE=""

usage() {
  cat <<EOF
Usage: sudo $0 --source-tar PATH [--rendered-env PATH] [--rendered-env-base PATH] [--rendered-auth-password PATH] [--rendered-auth-password-base PATH]

Installs or updates Brain on a Linux server under the '$SERVICE_USER' user.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source-tar)
      SOURCE_TAR="$2"
      shift 2
      ;;
    --rendered-env)
      RENDERED_ENV_FILE="$2"
      shift 2
      ;;
    --rendered-env-base)
      RENDERED_ENV_BASE_FILE="$2"
      shift 2
      ;;
    --rendered-auth-password)
      RENDERED_AUTH_PASSWORD_FILE="$2"
      shift 2
      ;;
    --rendered-auth-password-base)
      RENDERED_AUTH_PASSWORD_BASE_FILE="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'unknown argument: %s\n\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ "$(id -u)" != "0" ]]; then
  echo "install-cloud-linux-production.sh must run as root" >&2
  exit 1
fi
if [[ -z "$SOURCE_TAR" || ! -f "$SOURCE_TAR" ]]; then
  echo "--source-tar is required and must point to a tarball" >&2
  exit 2
fi

SHA="${GITHUB_SHA:-}"
if [[ -z "$SHA" ]]; then
  SHA="$(tar -tzf "$SOURCE_TAR" | sed -n 's#^\([^/]*\)/.git/.*#\1#p' | head -1 || true)"
fi
if [[ -z "$SHA" || ! "$SHA" =~ ^[0-9a-f]{40}$ ]]; then
  SHA="${BRAIN_RELEASE_SHA:-manual-$(date +%Y%m%d%H%M%S)}"
fi
SHORT_SHA="${SHA:0:12}"
RELEASE_VERSION="${BRAIN_RELEASE_VERSION:-prod-$SHORT_SHA}"
RELEASE_SHA="${BRAIN_RELEASE_SHA:-$SHA}"
RELEASE_DIR="$PROD_ROOT/releases/$SHA"
CURRENT_LINK="$PROD_ROOT/current"
SHARED_DIR="$PROD_ROOT/shared"
DATA_DIR="$SUPPORT_DIR/data"
BACKUP_DIR="$SUPPORT_DIR/backups"
CACHE_DIR="$SUPPORT_DIR/cache"
UI_CACHE_DIR="$SUPPORT_DIR/ui-cache"
SYSTEM_DIR="$SUPPORT_DIR/system"
UV_CACHE_DIR="$SUPPORT_DIR/uv-cache"
UV_PYTHON_INSTALL_DIR="$SUPPORT_DIR/python"
VENV_DIR="$SUPPORT_DIR/venvs/$SHA"
CURRENT_VENV_LINK="$SUPPORT_DIR/current-venv"
CFG_DIR="$SUPPORT_DIR/cfg"
DOCKER_DIR="$SUPPORT_DIR/docker"
ENV_FILE="$SECRETS_DIR/brain.env"
AUTH_PASSWORD_FILE="$SECRETS_DIR/brain-auth-password"
AUTH_USERS_FILE="$SECRETS_DIR/brain-auth-users.json"

log() {
  printf '[cloud-deploy] %s\n' "$*"
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    printf 'missing required command after bootstrap: %s\n' "$1" >&2
    exit 1
  }
}

set_env_var() {
  local key="$1"
  local value="$2"
  python3 - "$ENV_FILE" "$key" "$value" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
key = sys.argv[2]
value = sys.argv[3]
line = f"{key}={value}"
lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
for index, existing in enumerate(lines):
    if existing.startswith(f"{key}=") or existing.startswith(f"export {key}="):
        lines[index] = line
        break
else:
    lines.append(line)
path.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY
}

ensure_env_var() {
  local key="$1"
  local value="$2"
  if ! grep -qE "^(export[[:space:]]+)?${key}=" "$ENV_FILE" 2>/dev/null; then
    printf '%s=%s\n' "$key" "$value" >>"$ENV_FILE"
  fi
}

read_env_var() {
  local key="$1"
  python3 - "$ENV_FILE" "$key" <<'PY'
from pathlib import Path
import shlex
import sys

path = Path(sys.argv[1])
key = sys.argv[2]
if not path.exists():
    raise SystemExit
for raw in path.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    existing_key, value = line.split("=", 1)
    existing_key = existing_key.removeprefix("export ").strip()
    if existing_key == key:
        try:
            parsed = shlex.split(value.strip(), comments=False, posix=True)
            print(parsed[0] if parsed else "")
        except ValueError:
            print(value.strip().strip("'\""))
        break
PY
}

run_as_brain() {
  sudo -u "$SERVICE_USER" -H env \
    ENV_FILE="$ENV_FILE" \
    HOME="$SUPPORT_DIR" \
    XDG_CACHE_HOME="$CACHE_DIR" \
    UV_CACHE_DIR="$UV_CACHE_DIR" \
    UV_PYTHON_INSTALL_DIR="$UV_PYTHON_INSTALL_DIR" \
    UV_PROJECT_ENVIRONMENT="$VENV_DIR" \
    UV_LINK_MODE=copy \
    BRAIN_CONFIG_DIR="$CFG_DIR" \
    SYSTEM_ROOT_DIRECTORY="$SYSTEM_DIR" \
    DATA_ROOT_DIRECTORY="$DATA_DIR" \
    BRAIN_UI_CACHE_DIR="$UI_CACHE_DIR" \
    "$@"
}

wait_for_tcp() {
  local host="$1"
  local port="$2"
  local label="$3"
  local attempts="${4:-60}"
  for _attempt in $(seq 1 "$attempts"); do
    if python3 - "$host" "$port" <<'PY' >/dev/null 2>&1
import socket
import sys
with socket.create_connection((sys.argv[1], int(sys.argv[2])), timeout=2):
    pass
PY
    then
      return 0
    fi
    sleep 2
  done
  printf '%s did not become ready on %s:%s\n' "$label" "$host" "$port" >&2
  return 1
}

write_release_metadata() {
  local path="$1"
  python3 - "$path" "$APP_NAME" "$DEPLOY_ENV" "$RELEASE_VERSION" "$RELEASE_SHA" "$RELEASE_DIR" <<'PY'
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
    "source": "cloud-linux",
}
target = Path(path)
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}

install_packages() {
  export DEBIAN_FRONTEND=noninteractive
  if ! command -v curl >/dev/null 2>&1 || ! command -v rsync >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
    log "installing Debian runtime packages"
    apt-get update
    apt-get install -y ca-certificates curl git rsync python3 python3-venv build-essential npm caddy
  elif ! command -v caddy >/dev/null 2>&1; then
    log "installing Caddy"
    apt-get update
    apt-get install -y caddy
  fi
  if ! command -v docker >/dev/null 2>&1; then
    log "installing Docker packages from Debian"
    apt-get update
    apt-get install -y docker.io docker-compose-plugin
    systemctl enable --now docker
  elif ! docker compose version >/dev/null 2>&1; then
    log "installing Docker Compose plugin"
    apt-get update
    apt-get install -y docker-compose-plugin
  fi
  if ! command -v uv >/dev/null 2>&1; then
    log "installing uv to /usr/local/bin"
    curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh
  fi
}

ensure_user_and_dirs() {
  if ! id "$SERVICE_USER" >/dev/null 2>&1; then
    log "creating Linux service user $SERVICE_USER"
    useradd --system --create-home --home-dir "/home/$SERVICE_USER" --shell /usr/sbin/nologin "$SERVICE_USER"
  fi
  if getent group docker >/dev/null 2>&1; then
    usermod -aG docker "$SERVICE_USER"
  fi
  mkdir -p \
    "$PROD_ROOT/releases" "$SHARED_DIR" "$SECRETS_DIR" "$LOG_DIR/requests" "$LOG_DIR/routing" \
    "$DATA_DIR/brain" "$BACKUP_DIR" "$CACHE_DIR" "$UI_CACHE_DIR" "$SYSTEM_DIR" \
    "$UV_CACHE_DIR" "$UV_PYTHON_INSTALL_DIR" "$SUPPORT_DIR/venvs" "$CFG_DIR" \
    "$DOCKER_DIR/postgres/data" "$DOCKER_DIR/neo4j/data" "$DOCKER_DIR/neo4j/logs" \
    "$DOCKER_DIR/neo4j/import" "$DOCKER_DIR/neo4j/plugins"
  chown -R "$SERVICE_USER:$SERVICE_USER" "$PROD_ROOT" "$SUPPORT_DIR" "$LOG_DIR"
  chown -R "$SERVICE_USER:$SERVICE_USER" "$SECRETS_DIR"
  chmod 755 "$PROD_ROOT" "$PROD_ROOT/releases" "$SUPPORT_DIR" "$DATA_DIR" "$LOG_DIR"
  chmod 700 "$SECRETS_DIR"
}

prepare_env() {
  if [[ -n "$RENDERED_ENV_FILE" ]]; then
    log "importing rendered Brain env"
    install -m 600 -o "$SERVICE_USER" -g "$SERVICE_USER" "$RENDERED_ENV_FILE" "$ENV_FILE"
  elif [[ ! -f "$ENV_FILE" ]]; then
    log "creating starter Brain env at $ENV_FILE"
    install -m 600 -o "$SERVICE_USER" -g "$SERVICE_USER" /dev/null "$ENV_FILE"
  fi

  set_env_var PROFILE openai
  ensure_env_var BRAIN_LLM_ENABLED true
  ensure_env_var LLM_PROVIDER openai
  ensure_env_var LLM_MODEL gpt-5.4-mini
  ensure_env_var OPENAI_AUTH_MODE oauth
  ensure_env_var OPENAI_CODEX_AUTH_PROFILE default
  ensure_env_var OPENAI_CODEX_BASE_URL https://chatgpt.com/backend-api/codex
  ensure_env_var EMBEDDING_PROVIDER openai
  ensure_env_var EMBEDDING_MODEL text-embedding-3-large
  ensure_env_var EMBEDDING_DIMENSIONS 3072
  set_env_var BRAIN_PROD_ROOT "$PROD_ROOT"
  set_env_var BRAIN_RELEASE_ENV "$DEPLOY_ENV"
  set_env_var BRAIN_RELEASE_SHA "$RELEASE_SHA"
  set_env_var BRAIN_RELEASE_VERSION "$RELEASE_VERSION"
  set_env_var BRAIN_DATABASE_URL "sqlite:///$DATA_DIR/brain/brain.db"
  set_env_var SYSTEM_ROOT_DIRECTORY "$SYSTEM_DIR"
  set_env_var DATA_ROOT_DIRECTORY "$DATA_DIR"
  set_env_var BRAIN_BACKUP_DIR "$BACKUP_DIR"
  set_env_var BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED "$BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED"
  set_env_var BRAIN_MCP_HOST 127.0.0.1
  set_env_var BRAIN_MCP_PORT "$BRAIN_MCP_PORT"
  set_env_var BRAIN_MCP_PATH /mcp
  set_env_var BRAIN_ADMIN_MCP_PATH /admin/mcp
  set_env_var BRAIN_APP_MCP_PATH /app/mcp
  set_env_var BRAIN_PUBLIC_BASE_URL "$PUBLIC_BASE_URL"
  set_env_var BRAIN_PUBLIC_MCP_PATH /mcp
  set_env_var BRAIN_PUBLIC_ADMIN_MCP_PATH /admin/mcp
  set_env_var BRAIN_PUBLIC_APP_MCP_PATH /mcp
  set_env_var BRAIN_PROVIDER_AUTH_PROFILES_PATH "$SECRETS_DIR/provider-auth-profiles.json"
  set_env_var BRAIN_PROVIDER_AUTH_STATE_DIR "$SECRETS_DIR/provider-auth-state"
  set_env_var BRAIN_AUTH_PASSWORD_FILE "$AUTH_PASSWORD_FILE"
  set_env_var BRAIN_AUTH_USERS_FILE "$AUTH_USERS_FILE"
  set_env_var BRAIN_AUTH_SUPERUSER_IDS default
  set_env_var BRAIN_AUTH_STATE_PATH "$SECRETS_DIR/brain-oauth.json"
  ensure_env_var BRAIN_AUTH_SCOPES '"brain.memory.read brain.memory.write"'
  ensure_env_var BRAIN_AUTH_REQUIRE_PKCE true
  ensure_env_var BRAIN_AUTH_ACCESS_TOKEN_SECONDS 3600
  ensure_env_var BRAIN_AUTH_REFRESH_TOKEN_SECONDS 2592000
  ensure_env_var BRAIN_USER_ID default
  set_env_var BRAIN_REQUEST_LOG_ENABLED true
  set_env_var BRAIN_REQUEST_LOG_PATH "$LOG_DIR/requests/{date}.jsonl"
  set_env_var BRAIN_ROUTING_LOG_ENABLED true
  set_env_var BRAIN_ROUTING_LOG_PATH "$LOG_DIR/routing/{date}.jsonl"
  set_env_var GRAPH_DATABASE_PROVIDER neo4j
  set_env_var GRAPH_DATABASE_URL "bolt://127.0.0.1:$BRAIN_NEO4J_BOLT_PORT"
  set_env_var GRAPH_DATABASE_NAME neo4j
  set_env_var GRAPH_DATABASE_USERNAME neo4j
  ensure_env_var GRAPH_DATABASE_PASSWORD change-me
  set_env_var VECTOR_DB_PROVIDER pgvector
  set_env_var VECTOR_DB_URL ""
  set_env_var VECTOR_DB_PORT "$VECTOR_DB_PORT"
  set_env_var VECTOR_DB_NAME cognee_vectors
  set_env_var VECTOR_DB_KEY ""
  set_env_var VECTOR_DATASET_DATABASE_HANDLER pgvector
  set_env_var VECTOR_DB_USERNAME cognee
  set_env_var VECTOR_DB_PASSWORD cognee
  set_env_var VECTOR_DB_HOST 127.0.0.1
  set_env_var DB_PROVIDER postgres
  set_env_var DB_NAME cognee_db
  set_env_var DB_HOST 127.0.0.1
  set_env_var DB_PORT "$DB_PORT"
  set_env_var DB_USERNAME cognee
  set_env_var DB_PASSWORD cognee
  set_env_var BRAIN_DOCKER_ROOT "$DOCKER_DIR"
  set_env_var BRAIN_DOCKER_PROJECT "$BRAIN_DOCKER_PROJECT"
  set_env_var BRAIN_POSTGRES_CONTAINER "$BRAIN_POSTGRES_CONTAINER"
  set_env_var BRAIN_NEO4J_CONTAINER "$BRAIN_NEO4J_CONTAINER"
  set_env_var BRAIN_NEO4J_CONTAINER_USER "$BRAIN_NEO4J_CONTAINER_USER"
  set_env_var BRAIN_NEO4J_HTTP_PORT "$BRAIN_NEO4J_HTTP_PORT"
  set_env_var BRAIN_NEO4J_BOLT_PORT "$BRAIN_NEO4J_BOLT_PORT"
  set_env_var BRAIN_UI_ENABLED true
  set_env_var BRAIN_UI_HOST 127.0.0.1
  set_env_var BRAIN_UI_PROXY_PORT "$BRAIN_UI_PROXY_PORT"
  set_env_var BRAIN_UI_FRONTEND_PORT "$BRAIN_UI_FRONTEND_PORT"
  set_env_var BRAIN_UI_BACKEND_PORT "$BRAIN_UI_BACKEND_PORT"
  set_env_var BRAIN_PUBLIC_UI_PATH /cognee
  set_env_var BRAIN_PUBLIC_UI_API_PATH /cognee-api
  ensure_env_var BRAIN_UI_SESSION_SECONDS 43200
  ensure_env_var ENABLE_BACKEND_ACCESS_CONTROL false
  ensure_env_var BRAIN_TASTE_ENABLED true
  ensure_env_var BRAIN_TASTE_LLM_ROUTING_ENABLED false
  ensure_env_var BRAIN_TASTE_AUTO_ENRICH_ENABLED true
  ensure_env_var BRAIN_TASTE_WEB_ENRICHMENT_ENABLED true

  if [[ -z "$(read_env_var BRAIN_AUTH_TOKEN || true)" ]]; then
    set_env_var BRAIN_AUTH_TOKEN "$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
)"
  fi
  if [[ -n "$RENDERED_AUTH_PASSWORD_FILE" ]]; then
    install -m 600 -o "$SERVICE_USER" -g "$SERVICE_USER" "$RENDERED_AUTH_PASSWORD_FILE" "$AUTH_PASSWORD_FILE"
    if [[ -n "$RENDERED_AUTH_PASSWORD_BASE_FILE" ]]; then
      install -m 600 -o "$SERVICE_USER" -g "$SERVICE_USER" "$RENDERED_AUTH_PASSWORD_BASE_FILE" "$AUTH_PASSWORD_FILE.last-deployed"
    else
      install -m 600 -o "$SERVICE_USER" -g "$SERVICE_USER" "$RENDERED_AUTH_PASSWORD_FILE" "$AUTH_PASSWORD_FILE.last-deployed"
    fi
  elif [[ ! -f "$AUTH_PASSWORD_FILE" ]]; then
    python3 - <<'PY' >"$AUTH_PASSWORD_FILE"
import secrets
print(secrets.token_urlsafe(24))
PY
    chown "$SERVICE_USER:$SERVICE_USER" "$AUTH_PASSWORD_FILE"
    chmod 600 "$AUTH_PASSWORD_FILE"
  fi
  if [[ ! -f "$AUTH_USERS_FILE" ]]; then
    BRAIN_AUTH_PASSWORD_PATH="$AUTH_PASSWORD_FILE" BRAIN_AUTH_USERS_PATH="$AUTH_USERS_FILE" python3 - <<'PY'
import json
import os
import secrets
from pathlib import Path

auth_password = Path(os.environ["BRAIN_AUTH_PASSWORD_PATH"]).read_text(encoding="utf-8").strip()
root_password = secrets.token_urlsafe(32)
Path(os.environ["BRAIN_AUTH_USERS_PATH"]).write_text(
    json.dumps(
        [
            {"id": "default", "password": root_password, "display_name": "Root", "email": "", "superuser": True},
            {"id": "daniele", "password": auth_password, "display_name": "Daniele Bortolotti", "email": "", "superuser": False},
        ],
        indent=2,
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)
PY
    chown "$SERVICE_USER:$SERVICE_USER" "$AUTH_USERS_FILE"
    chmod 600 "$AUTH_USERS_FILE"
  fi
  chown -R "$SERVICE_USER:$SERVICE_USER" "$SECRETS_DIR"
  chmod 700 "$SECRETS_DIR"
  find "$SECRETS_DIR" -type f -exec chmod 600 {} +
  if [[ -n "$RENDERED_ENV_FILE" ]]; then
    install -m 600 -o "$SERVICE_USER" -g "$SERVICE_USER" "$ENV_FILE" "$ENV_FILE.last-deployed"
  fi
}

extract_release() {
  if [[ -d "$RELEASE_DIR" && "${BRAIN_REFRESH_RELEASE:-false}" == "true" ]]; then
    rm -rf "$RELEASE_DIR"
  fi
  if [[ ! -d "$RELEASE_DIR" ]]; then
    log "extracting release $SHORT_SHA to $RELEASE_DIR"
    mkdir -p "$RELEASE_DIR"
    tar -xzf "$SOURCE_TAR" --strip-components=1 -C "$RELEASE_DIR"
  else
    log "release already exists: $RELEASE_DIR"
  fi
  rm -f "$RELEASE_DIR/.env"
  chown -R "$SERVICE_USER:$SERVICE_USER" "$RELEASE_DIR"
  chmod +x "$RELEASE_DIR/scripts/"*.sh >/dev/null 2>&1 || true
  mkdir -p "$RELEASE_DIR/.data"
  ln -sfn "$DATA_DIR" "$RELEASE_DIR/.data/shared"
  rsync -a --delete "$RELEASE_DIR/cfg/" "$CFG_DIR/"
  chown -R "$SERVICE_USER:$SERVICE_USER" "$CFG_DIR"
}

install_python_env() {
  log "installing Python dependencies"
  run_as_brain bash -lc "cd '$RELEASE_DIR' && uv sync --all-extras --no-editable --reinstall-package memory-stack --python '$BRAIN_DEPLOY_PYTHON'"
  ln -sfn "$VENV_DIR" "$CURRENT_VENV_LINK"
  chown -h "$SERVICE_USER:$SERVICE_USER" "$CURRENT_VENV_LINK"
}

start_databases() {
  local graph_password
  graph_password="$(read_env_var GRAPH_DATABASE_PASSWORD || true)"
  if [[ -z "$graph_password" || "$graph_password" == "change-me" || "$graph_password" == "replace-me" ]]; then
    echo "GRAPH_DATABASE_PASSWORD must be set to a real secret in $ENV_FILE before starting prod Neo4j" >&2
    exit 1
  fi
  chown -R 999:999 "$DOCKER_DIR/postgres/data"
  chown -R 7474:7474 "$DOCKER_DIR/neo4j/data" "$DOCKER_DIR/neo4j/logs" "$DOCKER_DIR/neo4j/import" "$DOCKER_DIR/neo4j/plugins"
  log "starting Postgres/pgvector and Neo4j containers"
  (
    cd "$RELEASE_DIR/deployment"
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
    docker compose -p "$BRAIN_DOCKER_PROJECT" -f docker-compose.prod.yml up -d postgres neo4j
  )
  wait_for_tcp 127.0.0.1 "$DB_PORT" "Postgres"
  wait_for_tcp 127.0.0.1 "$BRAIN_NEO4J_BOLT_PORT" "Neo4j Bolt"
}

run_migrations_and_smoke() {
  log "running Brain database migrations"
  run_as_brain bash -lc "cd '$RELEASE_DIR' && set -a && source '$ENV_FILE' && set +a && '$VENV_DIR/bin/alembic' upgrade head"
  if [[ "$BRAIN_MODEL_SMOKE_SCOPE" != "none" ]]; then
    log "running live model smoke scope=$BRAIN_MODEL_SMOKE_SCOPE"
    run_as_brain bash -lc "cd '$RELEASE_DIR' && set -a && source '$ENV_FILE' && set +a && '$VENV_DIR/bin/python' scripts/live_model_smoke.py --scope '$BRAIN_MODEL_SMOKE_SCOPE'"
  fi
}

install_systemd_units() {
  log "installing systemd units"
  install -m 644 "$RELEASE_DIR/deployment/systemd/brain-mcp.service.template" /etc/systemd/system/brain-mcp.service
  install -m 644 "$RELEASE_DIR/deployment/systemd/brain-ui.service.template" /etc/systemd/system/brain-ui.service
  install -m 644 "$RELEASE_DIR/deployment/systemd/brain-maintenance.service.template" /etc/systemd/system/brain-maintenance.service
  install -m 644 "$RELEASE_DIR/deployment/systemd/brain-maintenance.timer.template" /etc/systemd/system/brain-maintenance.timer
  systemctl daemon-reload
}

install_caddy_config() {
  log "installing Caddy reverse proxy config for brain.dceb.net"
  install -d -m 755 /etc/caddy/conf.d /var/log/caddy
  install -m 644 "$RELEASE_DIR/deployment/caddy/brain.caddy.template" /etc/caddy/conf.d/brain.caddy
  if [[ ! -f /etc/caddy/Caddyfile ]]; then
    cat >/etc/caddy/Caddyfile <<'EOF'
{
	admin localhost:2019
}

import /etc/caddy/conf.d/*.caddy
EOF
  elif ! grep -q '^import /etc/caddy/conf\.d/\*\.caddy$' /etc/caddy/Caddyfile; then
    printf '\nimport /etc/caddy/conf.d/*.caddy\n' >>/etc/caddy/Caddyfile
  fi
  caddy validate --config /etc/caddy/Caddyfile
  systemctl enable --now caddy
  systemctl reload caddy
}

promote_and_restart() {
  log "promoting release $SHORT_SHA"
  write_release_metadata "$RELEASE_DIR/release.json"
  write_release_metadata "$SHARED_DIR/release.json"
  printf '%s\n' "$RELEASE_VERSION" >"$SHARED_DIR/current-version"
  chown -R "$SERVICE_USER:$SERVICE_USER" "$SHARED_DIR"
  ln -sfn "$RELEASE_DIR" "$CURRENT_LINK"
  chown -h "$SERVICE_USER:$SERVICE_USER" "$CURRENT_LINK"
  systemctl enable --now brain-maintenance.timer
  systemctl restart brain-mcp.service
  systemctl restart brain-ui.service
}

verify_services() {
  log "waiting for Brain health"
  for attempt in $(seq 1 60); do
    if curl -fsS "http://127.0.0.1:$BRAIN_MCP_PORT/healthz" >/dev/null 2>&1; then
      break
    fi
    if [[ "$attempt" == "60" ]]; then
      journalctl -u brain-mcp.service -n 80 --no-pager >&2 || true
      echo "Brain health did not become ready" >&2
      exit 1
    fi
    sleep 2
  done
  log "waiting for Brain UI health"
  for attempt in $(seq 1 120); do
    if curl -fsS "http://127.0.0.1:$BRAIN_UI_PROXY_PORT/healthz" >/dev/null 2>&1; then
      break
    fi
    if [[ "$attempt" == "120" ]]; then
      journalctl -u brain-ui.service -n 120 --no-pager >&2 || true
      echo "Brain UI health did not become ready" >&2
      exit 1
    fi
    sleep 2
  done
  log "deployed $APP_NAME $RELEASE_VERSION ($RELEASE_SHA)"
}

install_packages
require_cmd python3
require_cmd rsync
require_cmd uv
require_cmd docker
ensure_user_and_dirs
prepare_env
extract_release
install_python_env
start_databases
run_migrations_and_smoke
install_systemd_units
install_caddy_config
promote_and_restart
verify_services
