#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: run_launchd_service.sh mcp|ui|maintenance|log-rotation" >&2
  exit 2
fi

SERVICE="$1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOCAL_SUPPORT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_SUFFIX="${LOCAL_SUPPORT_DIR##*/brain-}"
ENV_FILE="${ENV_FILE:-$LOCAL_SUPPORT_DIR/secrets/brain.env}"
PYTHON="$LOCAL_SUPPORT_DIR/current-venv/bin/python"

log() {
  printf '[brain-service] %s\n' "$*"
}

until [[ -x "$PYTHON" && -f "$ENV_FILE" && -d "/Volumes/xpg_usb4/$ENV_SUFFIX/brain/current" ]]; do
  sleep 5
done

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

DB_PORT="${DB_PORT:-${VECTOR_DB_PORT:-15432}}"
BRAIN_NEO4J_BOLT_PORT="${BRAIN_NEO4J_BOLT_PORT:-17687}"

wait_for_tcp() {
  local host="$1"
  local port="$2"
  local label="$3"

  until "$PYTHON" - "$host" "$port" <<'PY' >/dev/null 2>&1
import socket
import sys

host = sys.argv[1]
port = int(sys.argv[2])
with socket.create_connection((host, port), timeout=2):
    pass
PY
  do
    log "waiting for $label on $host:$port"
    sleep 2
  done
}

wait_for_tcp "127.0.0.1" "$DB_PORT" "Postgres"
wait_for_tcp "127.0.0.1" "$BRAIN_NEO4J_BOLT_PORT" "Neo4j Bolt"

unset PYTHONHOME PYTHONPATH
cd "$LOCAL_SUPPORT_DIR"

case "$SERVICE" in
  mcp)
    exec "$PYTHON" -m memory_stack.mcp_server
    ;;
  ui)
    exec "$PYTHON" -m memory_stack.ui_service
    ;;
  maintenance)
    exec "$PYTHON" "$LOCAL_SUPPORT_DIR/scripts/nightly_maintenance.py" \
      --env "$ENV_SUFFIX" \
      --env-file "$ENV_FILE"
    ;;
  log-rotation)
    exec "$PYTHON" "$LOCAL_SUPPORT_DIR/scripts/rotate_launchd_logs.py" \
      --env "$ENV_SUFFIX" \
      --log-dir "$LOCAL_SUPPORT_DIR/logs/launchd" \
      --archive-dir "/Volumes/xpg_usb4/$ENV_SUFFIX/brain/shared/logs/launchd/archive" \
      --retention-days 30
    ;;
  *)
    echo "unknown launchd service: $SERVICE" >&2
    exit 2
    ;;
esac
