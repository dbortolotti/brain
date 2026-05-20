#!/usr/bin/env bash
set -euo pipefail

APP_NAME="brain"
DEPLOY_ENV="${BRAIN_DEPLOY_ENV:-prod}"
if [[ "$DEPLOY_ENV" != "prod" && "$DEPLOY_ENV" != "staging" && "$DEPLOY_ENV" != "qa" ]]; then
  printf 'BRAIN_DEPLOY_ENV must be prod, staging, or qa, got: %s\n' "$DEPLOY_ENV" >&2
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
DEFAULT_SERVICE_USER="oric_prod"
if [[ "$DEPLOY_ENV" == "qa" ]]; then
  DEFAULT_PUBLIC_BASE_URL="https://brain-qa.dceb.net"
  DEFAULT_MCP_PORT="18200"
  DEFAULT_UI_PROXY_PORT="18202"
  DEFAULT_UI_FRONTEND_PORT="13200"
  DEFAULT_UI_BACKEND_PORT="18201"
  DEFAULT_SLACK_AGENT_PORT="18203"
  DEFAULT_DB_PORT="17432"
  DEFAULT_NEO4J_HTTP_PORT="19474"
  DEFAULT_NEO4J_BOLT_PORT="19687"
  DEFAULT_GOOGLE_DRIVE_BACKUP_ENABLED="false"
  DEFAULT_SERVICE_USER="oric"
fi
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
  DEFAULT_SERVICE_USER="oric_staging"
fi
LABEL="${BRAIN_LAUNCHD_LABEL:-com.brain.$ENV_SUFFIX.mcp}"
UI_LABEL="${BRAIN_UI_LAUNCHD_LABEL:-com.brain.$ENV_SUFFIX.ui}"
SLACK_LABEL="${BRAIN_SLACK_AGENT_LAUNCHD_LABEL:-com.brain.$ENV_SUFFIX.slack-agent}"
DOCKER_RUNTIME_LABEL="${BRAIN_DOCKER_RUNTIME_LAUNCHD_LABEL:-com.brain.$ENV_SUFFIX.docker-runtime}"
DATABASES_LABEL="${BRAIN_DATABASES_LAUNCHD_LABEL:-com.brain.$ENV_SUFFIX.databases}"
MAINTENANCE_LABEL="${BRAIN_MAINTENANCE_LAUNCHD_LABEL:-com.brain.$ENV_SUFFIX.maintenance}"
LOG_ROTATION_LABEL="${BRAIN_LOG_ROTATION_LAUNCHD_LABEL:-com.brain.$ENV_SUFFIX.log-rotation}"
LEGACY_AGENT_MEMORY_LABEL="${BRAIN_AGENT_MEMORY_LAUNCHD_LABEL:-com.brain.$ENV_SUFFIX.agent-memory}"
LEGACY_BACKUP_LABEL="${BRAIN_BACKUP_LAUNCHD_LABEL:-com.brain.$ENV_SUFFIX.backup}"
PROD_ROOT="${BRAIN_PROD_ROOT:-$DEFAULT_ROOT}"
BRAIN_SERVICE_USER="${BRAIN_SERVICE_USER:-$DEFAULT_SERVICE_USER}"
BRAIN_DEPLOY_USER="${BRAIN_DEPLOY_USER:-${SUDO_USER:-${LOGNAME:-oric}}}"
BRAIN_DEPLOY_PYTHON="${BRAIN_DEPLOY_PYTHON:-3.12}"
DEFAULT_REFRESH_RELEASE="false"
if [[ ( "$DEPLOY_ENV" == "qa" || "$DEPLOY_ENV" == "staging" ) && -z "${GITHUB_ACTIONS:-}" ]]; then
  DEFAULT_REFRESH_RELEASE="true"
fi
BRAIN_REFRESH_RELEASE="${BRAIN_REFRESH_RELEASE:-$DEFAULT_REFRESH_RELEASE}"
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
BRAIN_DOCKER_HOST_USER="${BRAIN_DOCKER_HOST_USER:-${SUDO_USER:-${LOGNAME:-}}}"
BRAIN_NEO4J_CONTAINER_USER="${BRAIN_NEO4J_CONTAINER_USER:-}"
POSTGRES_CONTAINER_UID="${BRAIN_POSTGRES_CONTAINER_UID:-999}"
POSTGRES_CONTAINER_GID="${BRAIN_POSTGRES_CONTAINER_GID:-999}"
NEO4J_CONTAINER_UID="${BRAIN_NEO4J_CONTAINER_UID:-7474}"
NEO4J_CONTAINER_GID="${BRAIN_NEO4J_CONTAINER_GID:-7474}"
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
DOCKER_DIR="$SHARED_DIR/docker"
POSTGRES_DOCKER_DIR="$DOCKER_DIR/postgres"
POSTGRES_DATA_DIR="$POSTGRES_DOCKER_DIR/data"
NEO4J_DOCKER_DIR="$DOCKER_DIR/neo4j"
NEO4J_DATA_DIR="$NEO4J_DOCKER_DIR/data"
NEO4J_LOGS_DIR="$NEO4J_DOCKER_DIR/logs"
NEO4J_IMPORT_DIR="$NEO4J_DOCKER_DIR/import"
NEO4J_PLUGINS_DIR="$NEO4J_DOCKER_DIR/plugins"
DATABASE_URL="sqlite:///$DATA_DIR/brain/brain.db"
LOCAL_SUPPORT_DIR="/var/db/brain-$ENV_SUFFIX"
LOCAL_CACHE_DIR="$LOCAL_SUPPORT_DIR/cache"
LOCAL_SYSTEM_DIR="$LOCAL_SUPPORT_DIR/system"
LOCAL_DATA_DIR="$LOCAL_SUPPORT_DIR/data"
LOCAL_UI_CACHE_DIR="$LOCAL_SUPPORT_DIR/ui-cache"
LOCAL_REQUEST_LOG_DIR="$LOCAL_SUPPORT_DIR/logs/requests"
LOCAL_ROUTING_LOG_DIR="$LOCAL_SUPPORT_DIR/logs/routing"
UV_CACHE_DIR="$LOCAL_SUPPORT_DIR/uv-cache"
UV_PYTHON_INSTALL_DIR="$LOCAL_SUPPORT_DIR/python"
LOCAL_VENVS_DIR="$LOCAL_SUPPORT_DIR/venvs"
LOCAL_VENV_DIR="$LOCAL_VENVS_DIR/$SHA"
LOCAL_CURRENT_VENV_LINK="$LOCAL_SUPPORT_DIR/current-venv"
LOCAL_SECRETS_DIR="$LOCAL_SUPPORT_DIR/secrets"
LOCAL_ENV_FILE="$LOCAL_SECRETS_DIR/brain.env"
LOCAL_SCRIPTS_DIR="$LOCAL_SUPPORT_DIR/scripts"
LOCAL_CFG_DIR="$LOCAL_SUPPORT_DIR/cfg"
LOCAL_DEPLOYMENT_DIR="$LOCAL_SUPPORT_DIR/deployment"
LAUNCHD_LOG_DIR="$LOCAL_SUPPORT_DIR/logs/launchd"
LEGACY_LAUNCH_AGENT_DIR="${BRAIN_LEGACY_LAUNCH_AGENT_DIR:-/Users/$BRAIN_DEPLOY_USER/Library/LaunchAgents}"
PLIST_SRC="$DEPLOYMENT_CONFIG_DIR/launchd/com.brain.mcp.plist.template"
PLIST_DST="/Library/LaunchDaemons/$LABEL.plist"
UI_PLIST_SRC="$DEPLOYMENT_CONFIG_DIR/launchd/com.brain.ui.plist.template"
UI_PLIST_DST="/Library/LaunchDaemons/$UI_LABEL.plist"
SLACK_PLIST_SRC="$DEPLOYMENT_CONFIG_DIR/launchd/com.brain.slack-agent.plist.template"
SLACK_PLIST_DST="/Library/LaunchDaemons/$SLACK_LABEL.plist"
DOCKER_RUNTIME_PLIST_SRC="$DEPLOYMENT_CONFIG_DIR/launchd/com.brain.docker-runtime.plist.template"
DOCKER_RUNTIME_PLIST_DST="/Library/LaunchDaemons/$DOCKER_RUNTIME_LABEL.plist"
DATABASES_PLIST_SRC="$DEPLOYMENT_CONFIG_DIR/launchd/com.brain.databases.plist.template"
DATABASES_PLIST_DST="/Library/LaunchDaemons/$DATABASES_LABEL.plist"
MAINTENANCE_PLIST_SRC="$DEPLOYMENT_CONFIG_DIR/launchd/com.brain.maintenance.plist.template"
MAINTENANCE_PLIST_DST="/Library/LaunchDaemons/$MAINTENANCE_LABEL.plist"
LOG_ROTATION_PLIST_SRC="$DEPLOYMENT_CONFIG_DIR/launchd/com.brain.log-rotation.plist.template"
LOG_ROTATION_PLIST_DST="/Library/LaunchDaemons/$LOG_ROTATION_LABEL.plist"
LEGACY_AGENT_MEMORY_PLIST_DST="/Library/LaunchDaemons/$LEGACY_AGENT_MEMORY_LABEL.plist"
LEGACY_BACKUP_PLIST_DST="/Library/LaunchDaemons/$LEGACY_BACKUP_LABEL.plist"
NEWSYSLOG_SRC="$DEPLOYMENT_CONFIG_DIR/newsyslog/brain.conf"
NEWSYSLOG_DST="/etc/newsyslog.d/brain.conf"
BRAIN_SOURCE_ROOT=""
BRAIN_RENDERED_ENV_FILE=""
BRAIN_RENDERED_AUTH_PASSWORD_FILE=""
ORIGINAL_ARGS=("$@")
SHOW_USAGE="false"

usage() {
  cat <<EOF
Usage: BRAIN_DEPLOY_ENV=prod|staging|qa $0

Deploy Brain to $PROD_ROOT, install LaunchDaemons, and restart the $DEPLOY_ENV services.

Environment:
  BRAIN_DEPLOY_ENV             prod, staging, or qa (default: prod)
  BRAIN_SERVICE_USER           macOS service user (default: $DEFAULT_SERVICE_USER)
  BRAIN_DOCKER_HOST_USER       macOS user running Docker Desktop (default: $BRAIN_DOCKER_HOST_USER)
  BRAIN_NEO4J_CONTAINER_USER   uid:gid for Neo4j Docker process (default: Docker host user)
  BRAIN_DEPLOY_PYTHON          Python version uv should install/use (default: $BRAIN_DEPLOY_PYTHON)
  BRAIN_REFRESH_RELEASE        refresh an existing release directory (default: $BRAIN_REFRESH_RELEASE)

Options:
  --source-root PATH             deploy code from PATH instead of this script's checkout
  --rendered-env PATH            import a pre-rendered brain.env before deploy
  --rendered-auth-password PATH  import a pre-rendered brain-auth-password before deploy
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      SHOW_USAGE="true"
      shift
      ;;
    --source-root)
      if [[ $# -lt 2 ]]; then
        echo "--source-root requires a path" >&2
        exit 2
      fi
      BRAIN_SOURCE_ROOT="$2"
      shift 2
      ;;
    --rendered-env)
      if [[ $# -lt 2 ]]; then
        echo "--rendered-env requires a path" >&2
        exit 2
      fi
      BRAIN_RENDERED_ENV_FILE="$2"
      shift 2
      ;;
    --rendered-auth-password)
      if [[ $# -lt 2 ]]; then
        echo "--rendered-auth-password requires a path" >&2
        exit 2
      fi
      BRAIN_RENDERED_AUTH_PASSWORD_FILE="$2"
      shift 2
      ;;
    *)
      printf 'unknown argument: %s\n\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ "$SHOW_USAGE" == "true" ]]; then
  usage
  exit 0
fi

if [[ -n "$BRAIN_SOURCE_ROOT" ]]; then
  BRAIN_SOURCE_ROOT="$(cd "$BRAIN_SOURCE_ROOT" && pwd)"
  if [[ "$BRAIN_SOURCE_ROOT" != "$REPO_ROOT" && "${BRAIN_DEPLOY_DELEGATED:-false}" != "true" ]]; then
    exec env BRAIN_DEPLOY_DELEGATED=true "$BRAIN_SOURCE_ROOT/scripts/deploy-local-production.sh" "${ORIGINAL_ARGS[@]}"
  fi
fi

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

run_privileged() {
  if [[ "$(id -u)" == "0" ]]; then
    "$@"
    return
  fi
  sudo "$@"
}

require_privileged_access() {
  if [[ "$(id -u)" == "0" ]]; then
    return
  fi
  if ! command -v sudo >/dev/null 2>&1; then
    echo "sudo is required to install LaunchDaemons and set $BRAIN_SERVICE_USER ownership" >&2
    exit 1
  fi
  if ! sudo -n true >/dev/null 2>&1; then
    echo "passwordless sudo is required for non-interactive deploys that install LaunchDaemons" >&2
    exit 1
  fi
}

ensure_service_user() {
  if ! id -u "$BRAIN_SERVICE_USER" >/dev/null 2>&1; then
    cat >&2 <<EOF
service user $BRAIN_SERVICE_USER does not exist.
Create it before deploying, for example as a hidden standard macOS user, then rerun:
  BRAIN_DEPLOY_ENV=$DEPLOY_ENV ./scripts/deploy-local-production.sh
EOF
    exit 1
  fi
}

resolve_docker_runtime_user() {
  if [[ -n "$BRAIN_NEO4J_CONTAINER_USER" ]]; then
    return
  fi
  if [[ -n "$BRAIN_DOCKER_HOST_USER" ]] && id -u "$BRAIN_DOCKER_HOST_USER" >/dev/null 2>&1; then
    BRAIN_NEO4J_CONTAINER_USER="$(id -u "$BRAIN_DOCKER_HOST_USER"):$(id -g "$BRAIN_DOCKER_HOST_USER")"
  else
    BRAIN_NEO4J_CONTAINER_USER="$NEO4J_CONTAINER_UID:$NEO4J_CONTAINER_GID"
  fi
}

grant_docker_host_acl() {
  local path="$1"

  if [[ -z "$BRAIN_DOCKER_HOST_USER" || "$BRAIN_DOCKER_HOST_USER" == "root" ]]; then
    return
  fi
  if ! id -u "$BRAIN_DOCKER_HOST_USER" >/dev/null 2>&1; then
    log "docker host user $BRAIN_DOCKER_HOST_USER does not exist; skipping Docker bind-mount ACL"
    return
  fi
  if [[ ! -e "$path" ]]; then
    return
  fi

  local acl
  acl="$BRAIN_DOCKER_HOST_USER allow read,write,execute,append,readattr,writeattr,readextattr,writeextattr,readsecurity,writesecurity,chown,file_inherit,directory_inherit,list,add_file,search,delete,add_subdirectory,delete_child"
  run_privileged chmod -R -a "$acl" "$path" >/dev/null 2>&1 || true
  run_privileged chmod -R +a "$acl" "$path"
}

container_bind_mount_permissions_need_repair() {
  local path uid gid

  for path in "$POSTGRES_DATA_DIR" "$NEO4J_DATA_DIR"; do
    [[ -e "$path" ]] || return 0
  done

  uid="$(stat -f '%u' "$POSTGRES_DATA_DIR" 2>/dev/null || true)"
  gid="$(stat -f '%g' "$POSTGRES_DATA_DIR" 2>/dev/null || true)"
  if [[ "$uid" != "$POSTGRES_CONTAINER_UID" || "$gid" != "$POSTGRES_CONTAINER_GID" ]]; then
    return 0
  fi

  uid="$(stat -f '%u' "$NEO4J_DATA_DIR" 2>/dev/null || true)"
  gid="$(stat -f '%g' "$NEO4J_DATA_DIR" 2>/dev/null || true)"
  if [[ "$uid" != "$NEO4J_CONTAINER_UID" || "$gid" != "$NEO4J_CONTAINER_GID" ]]; then
    return 0
  fi

  return 1
}

stop_data_containers_for_permission_repair() {
  (
    cd "$RELEASE_DIR"
    GRAPH_DATABASE_PASSWORD="${GRAPH_DATABASE_PASSWORD:-change-me}" \
      DB_NAME="${DB_NAME:-cognee_db}" \
      DB_USERNAME="${DB_USERNAME:-cognee}" \
      DB_PASSWORD="${DB_PASSWORD:-cognee}" \
      DB_PORT="${DB_PORT:-$DEFAULT_DB_PORT}" \
      BRAIN_PROD_ROOT="$PROD_ROOT" \
      BRAIN_DOCKER_PROJECT="$BRAIN_DOCKER_PROJECT" \
      BRAIN_POSTGRES_CONTAINER="$BRAIN_POSTGRES_CONTAINER" \
      BRAIN_NEO4J_CONTAINER="$BRAIN_NEO4J_CONTAINER" \
      BRAIN_NEO4J_CONTAINER_USER="$BRAIN_NEO4J_CONTAINER_USER" \
      BRAIN_NEO4J_HTTP_PORT="$BRAIN_NEO4J_HTTP_PORT" \
      BRAIN_NEO4J_BOLT_PORT="$BRAIN_NEO4J_BOLT_PORT" \
      docker compose -p "$BRAIN_DOCKER_PROJECT" -f deployment/docker-compose.prod.yml stop postgres neo4j >/dev/null 2>&1 || true
  )
}

prepare_container_bind_mounts() {
  log "preparing $DEPLOY_ENV Docker bind mounts"
  run_privileged mkdir -p \
    "$POSTGRES_DATA_DIR" \
    "$NEO4J_DATA_DIR"
  run_privileged chown "$BRAIN_SERVICE_USER:staff" "$DOCKER_DIR" "$POSTGRES_DOCKER_DIR" "$NEO4J_DOCKER_DIR"
  run_privileged chmod 755 "$DOCKER_DIR" "$POSTGRES_DOCKER_DIR" "$NEO4J_DOCKER_DIR"

  if container_bind_mount_permissions_need_repair; then
    log "repairing $DEPLOY_ENV Docker bind-mount ownership for container users"
    stop_data_containers_for_permission_repair
    run_privileged chown -R "$POSTGRES_CONTAINER_UID:$POSTGRES_CONTAINER_GID" "$POSTGRES_DATA_DIR"
    run_privileged chown -R "$NEO4J_CONTAINER_UID:$NEO4J_CONTAINER_GID" "$NEO4J_DATA_DIR"
  fi

  run_privileged chmod -R u+rwX,go-rwx "$POSTGRES_DATA_DIR"
  run_privileged chmod -R u+rwX,go+rX "$NEO4J_DATA_DIR"
  grant_docker_host_acl "$POSTGRES_DATA_DIR"
  grant_docker_host_acl "$NEO4J_DATA_DIR"
}

clear_mutable_data_provenance() {
  if ! command -v xattr >/dev/null 2>&1; then
    return
  fi
  if [[ ! -d "$DATA_DIR" ]]; then
    return
  fi
  log "clearing macOS provenance xattrs from $DEPLOY_ENV mutable data"
  run_privileged xattr -dr com.apple.provenance "$DATA_DIR" >/dev/null 2>&1 || true
}

apply_runtime_permissions() {
  local phase="${1:-final}"

  log "setting $DEPLOY_ENV ownership to $BRAIN_SERVICE_USER"
  if is_true "${BRAIN_FULL_CHOWN:-false}"; then
    run_privileged chown -R "$BRAIN_SERVICE_USER:staff" "$PROD_ROOT" "$LOCAL_SUPPORT_DIR"
  else
    run_privileged chown "$BRAIN_SERVICE_USER:staff" \
      "$PROD_ROOT" \
      "$PROD_ROOT/releases" \
      "$SHARED_DIR" \
      "$DATA_DIR" \
      "$DATA_DIR/brain" \
      "$BACKUP_DIR" \
      "$LOG_DIR" \
      "$LOCAL_SUPPORT_DIR" \
      "$LOCAL_CACHE_DIR" \
      "$LOCAL_SYSTEM_DIR" \
      "$LOCAL_DATA_DIR" \
      "$LOCAL_UI_CACHE_DIR" \
      "$LOCAL_REQUEST_LOG_DIR" \
      "$LOCAL_ROUTING_LOG_DIR" \
      "$UV_CACHE_DIR" \
      "$UV_PYTHON_INSTALL_DIR" \
      "$LOCAL_VENVS_DIR" \
      "$LOCAL_SECRETS_DIR" \
      "$LOCAL_SCRIPTS_DIR" \
      "$LOCAL_CFG_DIR" \
      "$LOCAL_DEPLOYMENT_DIR" \
      "$LAUNCHD_LOG_DIR"
    run_privileged chown -R "$BRAIN_SERVICE_USER:staff" "$SECRETS_DIR" "$LOCAL_SECRETS_DIR" "$LAUNCHD_LOG_DIR" "$LOCAL_REQUEST_LOG_DIR" "$LOCAL_ROUTING_LOG_DIR"
    if [[ -f "$LOCAL_SUPPORT_DIR/run-cognee-ui-production.sh" ]]; then
      run_privileged chown "$BRAIN_SERVICE_USER:staff" "$LOCAL_SUPPORT_DIR/run-cognee-ui-production.sh"
    fi
    if [[ "$phase" == "final" && -d "$LOCAL_SCRIPTS_DIR" ]]; then
      run_privileged chown -R "$BRAIN_SERVICE_USER:staff" "$LOCAL_SCRIPTS_DIR"
    fi
    if [[ "$phase" == "final" && -d "$LOCAL_CFG_DIR" ]]; then
      run_privileged chown -R "$BRAIN_SERVICE_USER:staff" "$LOCAL_CFG_DIR"
    fi
    if [[ "$phase" == "final" && -d "$LOCAL_DEPLOYMENT_DIR" ]]; then
      run_privileged chown -R "$BRAIN_SERVICE_USER:staff" "$LOCAL_DEPLOYMENT_DIR"
    fi
    if [[ "$phase" == "final" && -d "$DATA_DIR/brain" ]]; then
      run_privileged chown -R "$BRAIN_SERVICE_USER:staff" "$DATA_DIR/brain"
    fi
    if [[ "$phase" == "final" && -d "$RELEASE_DIR" ]]; then
      run_privileged chown -R "$BRAIN_SERVICE_USER:staff" "$RELEASE_DIR"
    fi
    if [[ "$phase" == "final" && -d "$LOCAL_VENV_DIR" ]]; then
      run_privileged chown -R "$BRAIN_SERVICE_USER:staff" "$LOCAL_VENV_DIR"
    fi
    if [[ "$phase" == "final" && -d "$UV_PYTHON_INSTALL_DIR" ]]; then
      run_privileged chown -R "$BRAIN_SERVICE_USER:staff" "$UV_PYTHON_INSTALL_DIR"
      run_privileged find "$UV_PYTHON_INSTALL_DIR" -type l -exec chown -h "$BRAIN_SERVICE_USER:staff" {} +
    fi
  fi
  run_privileged chmod 755 "$PROD_ROOT" "$PROD_ROOT/releases" "$SHARED_DIR" "$DATA_DIR" "$DATA_DIR/brain" "$BACKUP_DIR" "$LOG_DIR" "$LAUNCHD_LOG_DIR" "$LOCAL_SUPPORT_DIR" "$LOCAL_CACHE_DIR" "$LOCAL_SYSTEM_DIR" "$LOCAL_DATA_DIR" "$LOCAL_UI_CACHE_DIR" "$LOCAL_REQUEST_LOG_DIR" "$LOCAL_ROUTING_LOG_DIR" "$UV_CACHE_DIR" "$UV_PYTHON_INSTALL_DIR" "$LOCAL_VENVS_DIR" "$LOCAL_SCRIPTS_DIR" "$LOCAL_CFG_DIR" "$LOCAL_DEPLOYMENT_DIR"
  if [[ -d "$LOCAL_VENV_DIR" ]]; then
    run_privileged chmod 755 "$LOCAL_VENV_DIR"
  fi
  if [[ "$phase" == "final" && -d "$UV_PYTHON_INSTALL_DIR" ]]; then
    run_privileged find "$UV_PYTHON_INSTALL_DIR" -type d -exec chmod 755 {} +
    run_privileged find "$UV_PYTHON_INSTALL_DIR" -type f -exec chmod u=rwX,go=rX {} +
    run_privileged find "$UV_PYTHON_INSTALL_DIR" -type l -exec chmod -h 755 {} + >/dev/null 2>&1 || true
  fi
  if [[ "$phase" == "final" && -d "$DATA_DIR/brain" ]]; then
    run_privileged chmod -R u+rwX,go+rX "$DATA_DIR/brain"
  fi
  if [[ "$phase" == "final" && -d "$RELEASE_DIR" ]]; then
    run_privileged find "$RELEASE_DIR" -type d -exec chmod 755 {} +
    run_privileged find "$RELEASE_DIR" -type f -exec chmod u=rw,go=r {} +
    run_privileged find "$RELEASE_DIR" -path '*/bin/*' -type f -exec chmod u=rwx,go=rx {} + >/dev/null 2>&1 || true
    run_privileged chmod +x "$RELEASE_DIR/scripts/"*.sh >/dev/null 2>&1 || true
  fi
  run_privileged chmod 700 "$SECRETS_DIR"
  run_privileged find "$SECRETS_DIR" -type d -exec chmod 700 {} +
  run_privileged find "$SECRETS_DIR" -type f -exec chmod 600 {} +
  run_privileged chmod 700 "$LOCAL_SECRETS_DIR"
  run_privileged find "$LOCAL_SECRETS_DIR" -type d -exec chmod 700 {} +
  run_privileged find "$LOCAL_SECRETS_DIR" -type f -exec chmod 600 {} +
  run_privileged chown -h "$BRAIN_SERVICE_USER:staff" "$CURRENT_LINK" >/dev/null 2>&1 || true
  run_privileged chown -h "$BRAIN_SERVICE_USER:staff" "$LOCAL_CURRENT_VENV_LINK" >/dev/null 2>&1 || true
}

run_in_release_env() {
  (
    cd "$RELEASE_DIR"
    ENV_FILE="$LOCAL_ENV_FILE" \
      HOME="$LOCAL_SUPPORT_DIR" \
      XDG_CACHE_HOME="$LOCAL_CACHE_DIR" \
      UV_CACHE_DIR="$UV_CACHE_DIR" \
      UV_PYTHON_INSTALL_DIR="$UV_PYTHON_INSTALL_DIR" \
      UV_PROJECT_ENVIRONMENT="$LOCAL_VENV_DIR" \
      UV_LINK_MODE=copy \
      BRAIN_CONFIG_DIR="$LOCAL_CFG_DIR" \
      BRAIN_PROVIDER_AUTH_PROFILES_PATH="$LOCAL_SECRETS_DIR/provider-auth-profiles.json" \
      BRAIN_PROVIDER_AUTH_STATE_DIR="$LOCAL_SECRETS_DIR/provider-auth-state" \
      BRAIN_AUTH_PASSWORD_FILE="$LOCAL_SECRETS_DIR/brain-auth-password" \
      BRAIN_AUTH_USERS_FILE="$LOCAL_SECRETS_DIR/brain-auth-users.json" \
      BRAIN_AUTH_STATE_PATH="$LOCAL_SECRETS_DIR/brain-oauth.json" \
      SYSTEM_ROOT_DIRECTORY="$LOCAL_SYSTEM_DIR" \
      DATA_ROOT_DIRECTORY="$LOCAL_DATA_DIR" \
      BRAIN_REQUEST_LOG_PATH="$LOCAL_REQUEST_LOG_DIR/{date}.jsonl" \
      BRAIN_ROUTING_LOG_PATH="$LOCAL_ROUTING_LOG_DIR/{date}.jsonl" \
      BRAIN_UI_CACHE_DIR="$LOCAL_UI_CACHE_DIR" \
      "$@"
  )
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

host = sys.argv[1]
port = int(sys.argv[2])
with socket.create_connection((host, port), timeout=2):
    pass
PY
    then
      return 0
    fi
    sleep 2
  done

  echo "$label did not become ready on $host:$port" >&2
  return 1
}

sync_runtime_secrets() {
  log "syncing runtime secrets to $LOCAL_SECRETS_DIR"
  run_privileged mkdir -p "$LOCAL_SECRETS_DIR"
  rsync -a --delete "$SECRETS_DIR/" "$LOCAL_SECRETS_DIR/"
  python3 - "$LOCAL_ENV_FILE" "$SECRETS_DIR" "$LOCAL_SECRETS_DIR" "$LOCAL_SUPPORT_DIR" <<'PY'
from pathlib import Path
import sys

env_file, source_secrets, local_secrets, local_support = sys.argv[1:]
path = Path(env_file)
lines = path.read_text(encoding="utf-8").splitlines()
text = "\n".join(lines) + "\n"
text = text.replace(source_secrets, local_secrets)
lines = text.splitlines()
overrides = {
    "SYSTEM_ROOT_DIRECTORY": f"{local_support}/system",
    "DATA_ROOT_DIRECTORY": f"{local_support}/data",
    "BRAIN_DATABASE_URL": f"sqlite:///{local_support}/data/brain/brain.db",
    "BRAIN_PROFILE_CONTEXT_PATH": f"{local_support}/data/brain/profile_context.json",
    "BRAIN_REQUEST_LOG_PATH": f"{local_support}/logs/requests/{{date}}.jsonl",
    "BRAIN_ROUTING_LOG_PATH": f"{local_support}/logs/routing/{{date}}.jsonl",
    "BRAIN_UI_CACHE_DIR": f"{local_support}/ui-cache",
}
for key, value in overrides.items():
    line = f"{key}={value}"
    for index, existing in enumerate(lines):
        if existing.startswith(f"{key}="):
            lines[index] = line
            break
    else:
        lines.append(line)
text = "\n".join(lines) + "\n"
path.write_text(text, encoding="utf-8")
PY
  run_privileged chown -R "$BRAIN_SERVICE_USER:staff" "$LOCAL_SECRETS_DIR"
  run_privileged chmod 700 "$LOCAL_SECRETS_DIR"
  run_privileged find "$LOCAL_SECRETS_DIR" -type d -exec chmod 700 {} +
  run_privileged find "$LOCAL_SECRETS_DIR" -type f -exec chmod 600 {} +
}

rewrite_local_runtime_config() {
  python3 - "$LOCAL_CFG_DIR" "$PROD_ROOT" "$LOCAL_SUPPORT_DIR" "$SECRETS_DIR" "$LOCAL_SECRETS_DIR" <<'PY'
from pathlib import Path
import sys

cfg_dir, root, local_support, source_secrets, local_secrets = sys.argv[1:]
replacements = {
    source_secrets: local_secrets,
    f"{root}/shared/data/system": f"{local_support}/system",
    f"{root}/shared/data/data": f"{local_support}/data",
    f"sqlite:///{root}/shared/data/brain/brain.db": f"sqlite:///{local_support}/data/brain/brain.db",
    f"{root}/shared/data/brain/brain.db": f"{local_support}/data/brain/brain.db",
    f"{root}/shared/data/brain/profile_context.json": f"{local_support}/data/brain/profile_context.json",
    f"{root}/shared/logs/requests": f"{local_support}/logs/requests",
    f"{root}/shared/logs/routing": f"{local_support}/logs/routing",
}
for path in Path(cfg_dir).glob("*.yaml"):
    text = path.read_text(encoding="utf-8")
    updated = text
    for old, new in replacements.items():
        updated = updated.replace(old, new)
    if updated != text:
        path.write_text(updated, encoding="utf-8")
PY
}

import_rendered_config() {
  local source_base

  if [[ -n "$BRAIN_RENDERED_ENV_FILE" ]]; then
    if [[ ! -f "$BRAIN_RENDERED_ENV_FILE" ]]; then
      echo "rendered env file not found: $BRAIN_RENDERED_ENV_FILE" >&2
      exit 2
    fi
    log "importing rendered $DEPLOY_ENV env from $BRAIN_RENDERED_ENV_FILE"
    run_privileged cp "$BRAIN_RENDERED_ENV_FILE" "$SECRETS_DIR/brain.env"
    source_base="$BRAIN_RENDERED_ENV_FILE.last-deployed"
    if [[ -f "$source_base" ]]; then
      run_privileged cp "$source_base" "$SECRETS_DIR/brain.env.last-deployed"
    fi
  fi

  if [[ -n "$BRAIN_RENDERED_AUTH_PASSWORD_FILE" ]]; then
    if [[ ! -f "$BRAIN_RENDERED_AUTH_PASSWORD_FILE" ]]; then
      echo "rendered auth password file not found: $BRAIN_RENDERED_AUTH_PASSWORD_FILE" >&2
      exit 2
    fi
    log "importing rendered $DEPLOY_ENV auth password"
    run_privileged cp "$BRAIN_RENDERED_AUTH_PASSWORD_FILE" "$SECRETS_DIR/brain-auth-password"
    source_base="$BRAIN_RENDERED_AUTH_PASSWORD_FILE.last-deployed"
    if [[ -f "$source_base" ]]; then
      run_privileged cp "$source_base" "$SECRETS_DIR/brain-auth-password.last-deployed"
    fi
  fi

  if [[ -n "$BRAIN_RENDERED_ENV_FILE$BRAIN_RENDERED_AUTH_PASSWORD_FILE" ]]; then
    run_privileged chown -R "$BRAIN_SERVICE_USER:staff" "$SECRETS_DIR"
    run_privileged chmod 700 "$SECRETS_DIR"
    run_privileged find "$SECRETS_DIR" -type d -exec chmod 700 {} +
    run_privileged find "$SECRETS_DIR" -type f -exec chmod 600 {} +
  fi
}

bootstrap_local_runtime_data() {
  log "bootstrapping $DEPLOY_ENV Cognee runtime data under $LOCAL_SUPPORT_DIR"
  run_privileged mkdir -p "$LOCAL_SYSTEM_DIR" "$LOCAL_DATA_DIR" "$LOCAL_DATA_DIR/brain"
  if [[ -d "$DATA_DIR/system" ]] && [[ -z "$(find "$LOCAL_SYSTEM_DIR" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
    rsync -rt --ignore-existing --no-owner --no-group --no-perms "$DATA_DIR/system/" "$LOCAL_SYSTEM_DIR/"
  fi
  if [[ -d "$DATA_DIR/data" ]] && [[ -z "$(find "$LOCAL_DATA_DIR" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
    rsync -rt --ignore-existing --no-owner --no-group --no-perms "$DATA_DIR/data/" "$LOCAL_DATA_DIR/"
  fi
  if [[ -d "$DATA_DIR/brain" ]]; then
    if [[ -f "$DATA_DIR/brain/brain.db" ]] && [[ ! -f "$LOCAL_DATA_DIR/brain/brain.db" ]]; then
      rsync -t --no-owner --no-group --no-perms "$DATA_DIR/brain/brain.db" "$LOCAL_DATA_DIR/brain/brain.db"
    fi
    find "$DATA_DIR/brain" -maxdepth 1 -type f -name 'profile_context*.json' -print0 |
      while IFS= read -r -d '' profile_context_file; do
        local target="$LOCAL_DATA_DIR/brain/$(basename "$profile_context_file")"
        if [[ ! -f "$target" ]]; then
          rsync -t --no-owner --no-group --no-perms "$profile_context_file" "$target"
        fi
      done
  fi
  run_privileged chown -R "$BRAIN_SERVICE_USER:staff" "$LOCAL_SYSTEM_DIR" "$LOCAL_DATA_DIR"
  run_privileged chmod -R u+rwX,go+rX "$LOCAL_SYSTEM_DIR" "$LOCAL_DATA_DIR"
}

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

enable_launch_daemon() {
  local label="$1"
  local plist="$2"

  run_privileged chown root:wheel "$plist"
  run_privileged chmod 644 "$plist"
  run_privileged launchctl enable "system/$label" >/dev/null 2>&1 || true
  run_privileged launchctl bootout system "$plist" >/dev/null 2>&1 || true
  if ! run_privileged launchctl bootstrap system "$plist"; then
    if run_privileged launchctl print "system/$label" >/dev/null 2>&1; then
      log "launchd job $label is loaded after bootstrap warning"
    else
      return 1
    fi
  fi
}

retire_legacy_launch_agents() {
  if [[ -z "$BRAIN_DEPLOY_USER" ]] || ! id -u "$BRAIN_DEPLOY_USER" >/dev/null 2>&1; then
    log "deploy user $BRAIN_DEPLOY_USER not found; skipping legacy LaunchAgent retirement"
    return
  fi
  if [[ ! -d "$LEGACY_LAUNCH_AGENT_DIR" ]]; then
    return
  fi

  local deploy_uid retired_dir timestamp labels label plist target
  deploy_uid="$(id -u "$BRAIN_DEPLOY_USER")"
  retired_dir="$LEGACY_LAUNCH_AGENT_DIR/retired"
  timestamp="$(date +%Y%m%d%H%M%S)"
  labels=(
    "$LABEL"
    "$UI_LABEL"
    "$SLACK_LABEL"
    "$DOCKER_RUNTIME_LABEL"
    "$DATABASES_LABEL"
    "$MAINTENANCE_LABEL"
    "$LOG_ROTATION_LABEL"
    "$LEGACY_AGENT_MEMORY_LABEL"
    "$LEGACY_BACKUP_LABEL"
  )

  for label in "${labels[@]}"; do
    plist="$LEGACY_LAUNCH_AGENT_DIR/$label.plist"
    run_privileged launchctl bootout "gui/$deploy_uid" "$plist" >/dev/null 2>&1 || true
    run_privileged launchctl bootout "gui/$deploy_uid/$label" >/dev/null 2>&1 || true
    run_privileged launchctl disable "gui/$deploy_uid/$label" >/dev/null 2>&1 || true
    if [[ -f "$plist" ]]; then
      log "retiring legacy LaunchAgent $label"
      run_privileged mkdir -p "$retired_dir"
      target="$retired_dir/$label.$timestamp.plist"
      run_privileged mv "$plist" "$target"
      run_privileged chown "$BRAIN_DEPLOY_USER:staff" "$target" >/dev/null 2>&1 || true
    fi
  done
  run_privileged chown "$BRAIN_DEPLOY_USER:staff" "$retired_dir" >/dev/null 2>&1 || true
}

disable_launch_daemon() {
  local label="$1"
  local plist="$2"

  run_privileged launchctl bootout system "$plist" >/dev/null 2>&1 || true
  run_privileged launchctl disable "system/$label" >/dev/null 2>&1 || true
  run_privileged rm -f "$plist"
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
  run_privileged cp "$NEWSYSLOG_SRC" "$NEWSYSLOG_DST"
  run_privileged chmod 644 "$NEWSYSLOG_DST"
  log "installed newsyslog config at $NEWSYSLOG_DST"
}

render_plist() {
  local src="$1"
  local dst="$2"
  python3 - "$src" "$dst" "$DEPLOY_ENV" "$PROD_ROOT" "$BRAIN_PUBLIC_BASE_URL" \
    "$BRAIN_MCP_PORT" "$BRAIN_UI_PROXY_PORT" "$BRAIN_UI_FRONTEND_PORT" \
    "$BRAIN_UI_BACKEND_PORT" "$BRAIN_SLACK_AGENT_PORT" "$BRAIN_SERVICE_USER" "$LAUNCHD_LOG_DIR" "$LOCAL_SUPPORT_DIR" <<'PY'
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
    service_user,
    launchd_log_dir,
    local_support_dir,
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
    "oric_prod": service_user,
    "/Users/oric/Library/Logs": launchd_log_dir,
    "/var/db/brain-prod": local_support_dir,
    "/var/db/brain-prod/python": f"{local_support_dir}/python",
    "--env prod": f"--env {deploy_env}",
}
if deploy_env != "prod":
    replacements.update(
        {
            "brain-ui.": f"brain-{deploy_env}-ui.",
            "brain-slack-agent.": f"brain-{deploy_env}-slack-agent.",
            "brain-docker-runtime.": f"brain-{deploy_env}-docker-runtime.",
            "brain-databases.": f"brain-{deploy_env}-databases.",
            "brain-maintenance.": f"brain-{deploy_env}-maintenance.",
            "brain-log-rotation.": f"brain-{deploy_env}-log-rotation.",
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
require_privileged_access
if [[ "$(id -u)" != "0" ]]; then
  log "re-executing deploy as root so LaunchDaemons and $BRAIN_SERVICE_USER ownership can be managed"
  exec sudo -E "$0" "$@"
fi
ensure_service_user
resolve_docker_runtime_user
run_privileged mkdir -p "$PROD_ROOT/releases" "$DATA_DIR" "$DATA_DIR/brain" "$BACKUP_DIR" "$SECRETS_DIR" "$LOG_DIR" "$LAUNCHD_LOG_DIR" "$LOCAL_SUPPORT_DIR" "$LOCAL_CACHE_DIR" "$LOCAL_SYSTEM_DIR" "$LOCAL_DATA_DIR" "$LOCAL_UI_CACHE_DIR" "$LOCAL_REQUEST_LOG_DIR" "$LOCAL_ROUTING_LOG_DIR" "$UV_CACHE_DIR" "$UV_PYTHON_INSTALL_DIR" "$LOCAL_VENVS_DIR" "$LOCAL_SECRETS_DIR" "$LOCAL_SCRIPTS_DIR" "$LOCAL_CFG_DIR" "$LOCAL_DEPLOYMENT_DIR" /Library/LaunchDaemons
apply_runtime_permissions bootstrap
import_rendered_config
clear_mutable_data_provenance

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
BRAIN_OPENAI_APPS_CHALLENGE_TOKEN=
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
ensure_env_var "BRAIN_OPENAI_APPS_CHALLENGE_TOKEN" ""
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
set_env_var "BRAIN_DOCKER_PROJECT" "$BRAIN_DOCKER_PROJECT"
set_env_var "BRAIN_DOCKER_HOST_USER" "$BRAIN_DOCKER_HOST_USER"
set_env_var "BRAIN_POSTGRES_CONTAINER" "$BRAIN_POSTGRES_CONTAINER"
set_env_var "BRAIN_NEO4J_CONTAINER" "$BRAIN_NEO4J_CONTAINER"
set_env_var "BRAIN_NEO4J_CONTAINER_USER" "$BRAIN_NEO4J_CONTAINER_USER"
set_env_var "BRAIN_NEO4J_HTTP_PORT" "$BRAIN_NEO4J_HTTP_PORT"
set_env_var "BRAIN_NEO4J_BOLT_PORT" "$BRAIN_NEO4J_BOLT_PORT"
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

sync_runtime_secrets
bootstrap_local_runtime_data

if [[ -d "$RELEASE_DIR" ]] && is_true "$BRAIN_REFRESH_RELEASE"; then
  log "refreshing existing release $SHORT_SHA"
  rm -rf "$RELEASE_DIR"
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
rsync -a --delete "$RELEASE_DIR/cfg/" "$LOCAL_CFG_DIR/"
rewrite_local_runtime_config
rsync -a --delete "$RELEASE_DIR/deployment/" "$LOCAL_DEPLOYMENT_DIR/"
run_in_release_env uv sync --all-extras --no-editable --reinstall-package memory-stack --python "$BRAIN_DEPLOY_PYTHON"
chmod +x "$RELEASE_DIR/scripts/run-cognee-ui-production.sh"
rsync -a --delete "$RELEASE_DIR/scripts/" "$LOCAL_SCRIPTS_DIR/"
chmod +x "$LOCAL_SCRIPTS_DIR/"*.py >/dev/null 2>&1 || true
chmod +x "$LOCAL_SCRIPTS_DIR/"*.sh >/dev/null 2>&1 || true
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

prepare_container_bind_mounts

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
    BRAIN_NEO4J_CONTAINER_USER="$BRAIN_NEO4J_CONTAINER_USER" \
    BRAIN_NEO4J_HTTP_PORT="$BRAIN_NEO4J_HTTP_PORT" \
    BRAIN_NEO4J_BOLT_PORT="$BRAIN_NEO4J_BOLT_PORT" \
    docker compose -p "$BRAIN_DOCKER_PROJECT" -f deployment/docker-compose.prod.yml up -d postgres neo4j
)
wait_for_tcp "127.0.0.1" "${DB_PORT:-$DEFAULT_DB_PORT}" "$DEPLOY_ENV Postgres"
wait_for_tcp "127.0.0.1" "$BRAIN_NEO4J_BOLT_PORT" "$DEPLOY_ENV Neo4j Bolt"

log "running Brain database migrations"
run_in_release_env "$LOCAL_VENV_DIR/bin/alembic" upgrade head

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
  run_in_release_env "$LOCAL_VENV_DIR/bin/python" scripts/live_model_smoke.py "${smoke_args[@]}"
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
render_plist "$DOCKER_RUNTIME_PLIST_SRC" "$DOCKER_RUNTIME_PLIST_DST"
plutil -lint "$DOCKER_RUNTIME_PLIST_DST" >/dev/null
render_plist "$DATABASES_PLIST_SRC" "$DATABASES_PLIST_DST"
plutil -lint "$DATABASES_PLIST_DST" >/dev/null
render_plist "$MAINTENANCE_PLIST_SRC" "$MAINTENANCE_PLIST_DST"
plutil -lint "$MAINTENANCE_PLIST_DST" >/dev/null
render_plist "$LOG_ROTATION_PLIST_SRC" "$LOG_ROTATION_PLIST_DST"
plutil -lint "$LOG_ROTATION_PLIST_DST" >/dev/null
if [[ "$DEPLOY_ENV" == "prod" ]]; then
  install_newsyslog_config
else
  log "skipping system newsyslog config for $DEPLOY_ENV"
fi

log "updating current symlink"
write_release_metadata "$RELEASE_DIR/release.json"
write_release_metadata "$SHARED_DIR/release.json"
printf '%s\n' "$RELEASE_VERSION" >"$SHARED_DIR/current-version"
ln -sfn "$LOCAL_VENV_DIR" "$LOCAL_CURRENT_VENV_LINK"
ln -sfn "$RELEASE_DIR" "$CURRENT_LINK"
launchd_log_stems=(brain-$DEPLOY_ENV brain-$DEPLOY_ENV-ui brain-$DEPLOY_ENV-slack-agent brain-$DEPLOY_ENV-docker-runtime brain-$DEPLOY_ENV-databases brain-$DEPLOY_ENV-maintenance brain-$DEPLOY_ENV-log-rotation)
if [[ "$DEPLOY_ENV" == "prod" ]]; then
  launchd_log_stems=(brain-prod brain-ui brain-slack-agent brain-docker-runtime brain-databases brain-maintenance brain-log-rotation)
fi
for stem in "${launchd_log_stems[@]}"; do
  touch "$LAUNCHD_LOG_DIR/$stem.out.log" "$LAUNCHD_LOG_DIR/$stem.err.log"
done
apply_runtime_permissions final

if command -v launchctl >/dev/null 2>&1; then
  retire_legacy_launch_agents
  log "restarting launchd service $DOCKER_RUNTIME_LABEL"
  enable_launch_daemon "$DOCKER_RUNTIME_LABEL" "$DOCKER_RUNTIME_PLIST_DST"
  log "restarting launchd service $DATABASES_LABEL"
  enable_launch_daemon "$DATABASES_LABEL" "$DATABASES_PLIST_DST"
  log "restarting launchd service $LABEL"
  enable_launch_daemon "$LABEL" "$PLIST_DST"
  log "restarting launchd service $UI_LABEL"
  enable_launch_daemon "$UI_LABEL" "$UI_PLIST_DST"
  log "restarting launchd service $SLACK_LABEL"
  enable_launch_daemon "$SLACK_LABEL" "$SLACK_PLIST_DST"
  log "reloading launchd job $MAINTENANCE_LABEL"
  enable_launch_daemon "$MAINTENANCE_LABEL" "$MAINTENANCE_PLIST_DST"
  log "reloading launchd job $LOG_ROTATION_LABEL"
  enable_launch_daemon "$LOG_ROTATION_LABEL" "$LOG_ROTATION_PLIST_DST"
  log "removing legacy launchd jobs $LEGACY_AGENT_MEMORY_LABEL and $LEGACY_BACKUP_LABEL"
  disable_launch_daemon "$LEGACY_AGENT_MEMORY_LABEL" "$LEGACY_AGENT_MEMORY_PLIST_DST"
  disable_launch_daemon "$LEGACY_BACKUP_LABEL" "$LEGACY_BACKUP_PLIST_DST"
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
run_in_release_env "$LOCAL_VENV_DIR/bin/python" scripts/verify_mcp_production.py --skip-backups
run_in_release_env "$LOCAL_VENV_DIR/bin/python" scripts/verify_cognee_ui_production.py
run_in_release_env "$LOCAL_VENV_DIR/bin/python" scripts/verify_slack_agent.py

log "deployed $APP_NAME $RELEASE_VERSION ($SHA)"
