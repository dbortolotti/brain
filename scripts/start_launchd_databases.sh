#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOCAL_SUPPORT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_SUFFIX="${LOCAL_SUPPORT_DIR##*/brain-}"
ENV_FILE="${ENV_FILE:-$LOCAL_SUPPORT_DIR/secrets/brain.env}"

log() {
  printf '[brain-databases] %s\n' "$*"
}

if [[ ! -f "$ENV_FILE" ]]; then
  log "waiting for env file: $ENV_FILE"
fi
until [[ -f "$ENV_FILE" ]]; do
  sleep 5
done

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

PROD_ROOT="${BRAIN_PROD_ROOT:-/Volumes/xpg_usb4/$ENV_SUFFIX/brain}"
BRAIN_DOCKER_ROOT="${BRAIN_DOCKER_ROOT:-$LOCAL_SUPPORT_DIR/docker}"
CURRENT_LINK="$PROD_ROOT/current"
COMPOSE_FILE="${BRAIN_DOCKER_COMPOSE_FILE:-$LOCAL_SUPPORT_DIR/deployment/docker-compose.prod.yml}"
DB_PORT="${DB_PORT:-${VECTOR_DB_PORT:-15432}}"
BRAIN_NEO4J_BOLT_PORT="${BRAIN_NEO4J_BOLT_PORT:-17687}"
BRAIN_DOCKER_PROJECT="${BRAIN_DOCKER_PROJECT:-brain-$ENV_SUFFIX}"
BRAIN_DOCKER_HOST_USER="${BRAIN_DOCKER_HOST_USER:-oric}"
BRAIN_POSTGRES_CONTAINER="${BRAIN_POSTGRES_CONTAINER:-brain-$ENV_SUFFIX-postgres}"
BRAIN_NEO4J_CONTAINER="${BRAIN_NEO4J_CONTAINER:-brain-$ENV_SUFFIX-neo4j}"
BRAIN_NEO4J_CONTAINER_USER="${BRAIN_NEO4J_CONTAINER_USER:-7474:7474}"
DOCKER_BIN="${DOCKER_BIN:-}"
DOCKER_COMPOSE_BIN="${DOCKER_COMPOSE_BIN:-}"

if [[ -z "${DOCKER_HOST:-}" ]]; then
  for socket in \
    "/Users/$BRAIN_DOCKER_HOST_USER/.colima/default/docker.sock" \
    "/Users/$BRAIN_DOCKER_HOST_USER/.docker/run/docker.sock" \
    "/var/run/docker.sock"; do
    if [[ -S "$socket" ]]; then
      export DOCKER_HOST="unix://$socket"
      break
    fi
  done
fi

if [[ -z "$DOCKER_BIN" ]]; then
  for candidate in /opt/homebrew/bin/docker /usr/local/bin/docker docker; do
    if command -v "$candidate" >/dev/null 2>&1; then
      DOCKER_BIN="$(command -v "$candidate")"
      break
    fi
  done
fi
if [[ -z "$DOCKER_COMPOSE_BIN" ]]; then
  for candidate in /opt/homebrew/bin/docker-compose /usr/local/bin/docker-compose; do
    if command -v "$candidate" >/dev/null 2>&1; then
      DOCKER_COMPOSE_BIN="$(command -v "$candidate")"
      break
    fi
  done
fi

wait_for_tcp() {
  local host="$1"
  local port="$2"
  local label="$3"
  local attempts="${4:-120}"

  for _attempt in $(seq 1 "$attempts"); do
    if /usr/bin/nc -z -G 2 "$host" "$port" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done

  log "$label did not become ready on $host:$port"
  return 1
}

until [[ -d "$CURRENT_LINK" && -f "$COMPOSE_FILE" ]]; do
  log "waiting for release symlink: $CURRENT_LINK"
  sleep 5
done

until [[ -n "$DOCKER_BIN" && -x "$DOCKER_BIN" ]]; do
  log "waiting for docker command"
  sleep 10
done

until "$DOCKER_BIN" info >/dev/null 2>&1; do
  log "waiting for Docker daemon${DOCKER_HOST:+ at $DOCKER_HOST}"
  sleep 10
done

log "starting $ENV_SUFFIX Postgres/pgvector and Neo4j containers"
cd "$CURRENT_LINK"
export GRAPH_DATABASE_PASSWORD="${GRAPH_DATABASE_PASSWORD:-change-me}"
export DB_NAME="${DB_NAME:-cognee_db}"
export DB_USERNAME="${DB_USERNAME:-cognee}"
export DB_PASSWORD="${DB_PASSWORD:-cognee}"
export DB_PORT
export BRAIN_PROD_ROOT="$PROD_ROOT"
export BRAIN_DOCKER_ROOT
export BRAIN_DOCKER_PROJECT
export BRAIN_DOCKER_HOST_USER
export BRAIN_POSTGRES_CONTAINER
export BRAIN_NEO4J_CONTAINER
export BRAIN_NEO4J_CONTAINER_USER
export BRAIN_NEO4J_HTTP_PORT="${BRAIN_NEO4J_HTTP_PORT:-17474}"
export BRAIN_NEO4J_BOLT_PORT

log "using Docker binary: $DOCKER_BIN"
if [[ -n "$DOCKER_COMPOSE_BIN" && -x "$DOCKER_COMPOSE_BIN" ]]; then
  log "using Docker Compose binary: $DOCKER_COMPOSE_BIN"
"$DOCKER_COMPOSE_BIN" -p "$BRAIN_DOCKER_PROJECT" -f "$COMPOSE_FILE" up -d postgres neo4j
else
  "$DOCKER_BIN" compose -p "$BRAIN_DOCKER_PROJECT" -f "$COMPOSE_FILE" up -d postgres neo4j
fi

wait_for_tcp "127.0.0.1" "$DB_PORT" "$ENV_SUFFIX Postgres"
wait_for_tcp "127.0.0.1" "$BRAIN_NEO4J_BOLT_PORT" "$ENV_SUFFIX Neo4j Bolt"
log "$ENV_SUFFIX database containers are ready"
