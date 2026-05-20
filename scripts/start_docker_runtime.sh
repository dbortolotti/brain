#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOCAL_SUPPORT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_SUFFIX="${LOCAL_SUPPORT_DIR##*/brain-}"
ENV_FILE="${ENV_FILE:-$LOCAL_SUPPORT_DIR/secrets/brain.env}"

log() {
  printf '[brain-docker-runtime] %s\n' "$*"
}

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

BRAIN_DOCKER_HOST_USER="${BRAIN_DOCKER_HOST_USER:-oric}"
DOCKER_BIN="${DOCKER_BIN:-}"
COLIMA_BIN="${COLIMA_BIN:-}"
COLIMA_PROFILE="${BRAIN_COLIMA_PROFILE:-default}"
COLIMA_LAUNCH_AGENT_LABEL="${BRAIN_COLIMA_LAUNCH_AGENT_LABEL:-homebrew.mxcl.colima}"
COLIMA_START_ARGS="${BRAIN_COLIMA_START_ARGS:-start --runtime docker}"
USER_HOME="$(dscl . -read "/Users/$BRAIN_DOCKER_HOST_USER" NFSHomeDirectory 2>/dev/null | awk '{print $2}')"
USER_HOME="${USER_HOME:-/Users/$BRAIN_DOCKER_HOST_USER}"
DOCKER_HOST="${DOCKER_HOST:-unix://$USER_HOME/.colima/$COLIMA_PROFILE/docker.sock}"
export DOCKER_HOST

if [[ -z "$DOCKER_BIN" ]]; then
  for candidate in /opt/homebrew/bin/docker /usr/local/bin/docker docker; do
    if command -v "$candidate" >/dev/null 2>&1; then
      DOCKER_BIN="$(command -v "$candidate")"
      break
    fi
  done
fi
if [[ -z "$COLIMA_BIN" ]]; then
  for candidate in /opt/homebrew/bin/colima /usr/local/bin/colima colima; do
    if command -v "$candidate" >/dev/null 2>&1; then
      COLIMA_BIN="$(command -v "$candidate")"
      break
    fi
  done
fi

if [[ -z "$DOCKER_BIN" || ! -x "$DOCKER_BIN" ]]; then
  log "docker command is not installed"
  exit 1
fi
if "$DOCKER_BIN" info >/dev/null 2>&1; then
  log "$ENV_SUFFIX Docker is already ready at $DOCKER_HOST"
  exit 0
fi

if [[ -z "$COLIMA_BIN" || ! -x "$COLIMA_BIN" ]]; then
  log "colima command is not installed"
  exit 1
fi

uid="$(id -u "$BRAIN_DOCKER_HOST_USER" 2>/dev/null || true)"
if [[ -z "$uid" ]]; then
  log "docker host user $BRAIN_DOCKER_HOST_USER does not exist"
  exit 1
fi

agent_plist="$USER_HOME/Library/LaunchAgents/$COLIMA_LAUNCH_AGENT_LABEL.plist"
if [[ -f "$agent_plist" ]] && /bin/launchctl print "gui/$uid" >/dev/null 2>&1; then
  log "kickstarting $COLIMA_LAUNCH_AGENT_LABEL in gui/$uid"
  /bin/launchctl asuser "$uid" /bin/launchctl bootstrap "gui/$uid" "$agent_plist" >/dev/null 2>&1 || true
  /bin/launchctl asuser "$uid" /bin/launchctl enable "gui/$uid/$COLIMA_LAUNCH_AGENT_LABEL" >/dev/null 2>&1 || true
  /bin/launchctl asuser "$uid" /bin/launchctl kickstart -k "gui/$uid/$COLIMA_LAUNCH_AGENT_LABEL" >/dev/null 2>&1 || true
fi

for _attempt in $(seq 1 24); do
  if "$DOCKER_BIN" info >/dev/null 2>&1; then
    log "$ENV_SUFFIX Docker is ready at $DOCKER_HOST"
    exit 0
  fi
  sleep 5
done

log "starting Colima as $BRAIN_DOCKER_HOST_USER"
/usr/bin/su -l "$BRAIN_DOCKER_HOST_USER" -c \
  "export PATH=/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin; $COLIMA_BIN $COLIMA_START_ARGS"

for _attempt in $(seq 1 60); do
  if "$DOCKER_BIN" info >/dev/null 2>&1; then
    log "$ENV_SUFFIX Docker is ready at $DOCKER_HOST"
    exit 0
  fi
  sleep 5
done

log "$ENV_SUFFIX Docker did not become ready at $DOCKER_HOST"
exit 1
