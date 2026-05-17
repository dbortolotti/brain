#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${BRAIN_RELEASE_DIR:-$(pwd)}"
ENV_FILE="${ENV_FILE:-/Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env}"
FRONTEND_READY=0
BACKEND_READY=0
PROXY_READY=0

log() {
  printf '[brain-ui] %s\n' "$*"
}

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

export BRAIN_UI_ENABLED="${BRAIN_UI_ENABLED:-true}"
export BRAIN_UI_HOST="${BRAIN_UI_HOST:-127.0.0.1}"
export BRAIN_UI_PROXY_PORT="${BRAIN_UI_PROXY_PORT:-18002}"
export BRAIN_UI_FRONTEND_PORT="${BRAIN_UI_FRONTEND_PORT:-13000}"
export BRAIN_UI_BACKEND_PORT="${BRAIN_UI_BACKEND_PORT:-18001}"
export BRAIN_PUBLIC_UI_PATH="${BRAIN_PUBLIC_UI_PATH:-/cognee}"
export BRAIN_PUBLIC_UI_API_PATH="${BRAIN_PUBLIC_UI_API_PATH:-/cognee-api}"
export BRAIN_UI_SESSION_SECONDS="${BRAIN_UI_SESSION_SECONDS:-43200}"
export UI_APP_URL="${BRAIN_PUBLIC_BASE_URL:-https://brain.dceb.net}"
export CORS_ALLOWED_ORIGINS="${BRAIN_PUBLIC_BASE_URL:-https://brain.dceb.net}"
export NEXT_PUBLIC_LOCAL_API_URL="${BRAIN_PUBLIC_BASE_URL:-https://brain.dceb.net}${BRAIN_PUBLIC_UI_API_PATH}"
export NEXT_PUBLIC_IS_CLOUD_ENVIRONMENT=false
export REQUIRE_AUTHENTICATION=false
export ENABLE_BACKEND_ACCESS_CONTROL=false
export HTTP_API_HOST=127.0.0.1
export HTTP_API_PORT="$BRAIN_UI_BACKEND_PORT"
export HOST=127.0.0.1
export PORT="$BRAIN_UI_FRONTEND_PORT"

cleanup() {
  local status=$?
  trap - EXIT INT TERM
  for pid in ${PROXY_PID:-} ${FRONTEND_PID:-} ${BACKEND_PID:-}; do
    if [[ -n "$pid" ]]; then
      kill "$pid" >/dev/null 2>&1 || true
    fi
  done
  wait >/dev/null 2>&1 || true
  exit "$status"
}
trap cleanup EXIT INT TERM

log "preparing Cognee frontend cache"
uv run python - <<'PY'
from cognee.api.v1.ui.ui import download_frontend_assets, find_frontend_path

if not download_frontend_assets(force=False):
    raise SystemExit("failed to download Cognee frontend assets")
if find_frontend_path() is None:
    raise SystemExit("Cognee frontend cache was not found after download")
PY

FRONTEND_DIR="$(uv run python - <<'PY' | tail -n 1
from cognee.api.v1.ui.ui import find_frontend_path

path = find_frontend_path()
if path is None:
    raise SystemExit("Cognee frontend cache was not found")
print(path)
PY
)"

log "installing Cognee frontend dependencies"
(
  cd "$FRONTEND_DIR"
  npm install
)

log "starting Cognee backend on 127.0.0.1:$BRAIN_UI_BACKEND_PORT"
uv run python -m uvicorn cognee.api.client:app \
  --host 127.0.0.1 \
  --port "$BRAIN_UI_BACKEND_PORT" &
BACKEND_PID=$!

log "starting Cognee frontend on 127.0.0.1:$BRAIN_UI_FRONTEND_PORT"
(
  cd "$FRONTEND_DIR"
  npm run dev
) &
FRONTEND_PID=$!

log "starting Brain UI proxy on $BRAIN_UI_HOST:$BRAIN_UI_PROXY_PORT"
uv run python -m uvicorn memory_stack.ui_proxy:app \
  --host "$BRAIN_UI_HOST" \
  --port "$BRAIN_UI_PROXY_PORT" &
PROXY_PID=$!

for attempt in {1..60}; do
  if [[ "$BACKEND_READY" == "0" ]] &&
    curl -fsS "http://127.0.0.1:$BRAIN_UI_BACKEND_PORT/health" >/dev/null 2>&1; then
    BACKEND_READY=1
    log "Cognee backend is ready"
  fi
  if [[ "$FRONTEND_READY" == "0" ]] &&
    curl -fsS "http://127.0.0.1:$BRAIN_UI_FRONTEND_PORT/" >/dev/null 2>&1; then
    FRONTEND_READY=1
    log "Cognee frontend is ready"
  fi
  if [[ "$PROXY_READY" == "0" ]] &&
    curl -fsS "http://$BRAIN_UI_HOST:$BRAIN_UI_PROXY_PORT/healthz" >/dev/null 2>&1; then
    PROXY_READY=1
    log "Brain UI proxy is ready"
  fi
  if [[ "$BACKEND_READY$FRONTEND_READY$PROXY_READY" == "111" ]]; then
    break
  fi
  sleep 1
done

if [[ "$BACKEND_READY$FRONTEND_READY$PROXY_READY" != "111" ]]; then
  log "UI service did not become ready"
  exit 1
fi

wait -n "$BACKEND_PID" "$FRONTEND_PID" "$PROXY_PID"
