#!/usr/bin/env bash
set -euo pipefail

REMOTE="${BRAIN_CLOUD_REMOTE:-brain@159.195.79.79}"
SSH_KEY="${BRAIN_CLOUD_SSH_KEY:-$HOME/.ssh/id_ed25519}"
SOURCE_ROOT=""
RENDERED_ENV_FILE=""
RENDERED_AUTH_PASSWORD_FILE=""

usage() {
  cat <<EOF
Usage: $0 [--source-root PATH] [--rendered-env PATH] [--rendered-auth-password PATH]

Packages the current checkout, uploads it to $REMOTE, and runs the Linux
installer with sudo. Override target with BRAIN_CLOUD_REMOTE.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source-root)
      SOURCE_ROOT="$2"
      shift 2
      ;;
    --rendered-env)
      RENDERED_ENV_FILE="$2"
      shift 2
      ;;
    --rendered-auth-password)
      RENDERED_AUTH_PASSWORD_FILE="$2"
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

REPO_ROOT="$(cd "${SOURCE_ROOT:-$(dirname "${BASH_SOURCE[0]}")/..}" && pwd)"
SHA="${GITHUB_SHA:-$(git -C "$REPO_ROOT" rev-parse HEAD)}"
SHORT_SHA="${SHA:0:12}"
REMOTE_DIR="${BRAIN_CLOUD_REMOTE_DIR:-/home/brain/deploy/brain-deploy-$SHORT_SHA}"
LOCAL_TAR="$(mktemp "${TMPDIR:-/tmp}/brain-src.XXXXXX.tar.gz")"

cleanup() {
  rm -f "$LOCAL_TAR"
}
trap cleanup EXIT

log() {
  printf '[cloud-upload] %s\n' "$*"
}

log "packaging $SHORT_SHA from $REPO_ROOT"
COPYFILE_DISABLE=1 tar --no-xattrs -czf "$LOCAL_TAR" \
  --exclude '.git' \
  --exclude '.env' \
  --exclude '.data' \
  --exclude '.venv' \
  --exclude '.DS_Store' \
  --exclude '._*' \
  --exclude '__MACOSX' \
  --exclude '__pycache__' \
  --exclude '.pytest_cache' \
  --exclude '.ruff_cache' \
  -C "$(dirname "$REPO_ROOT")" "$(basename "$REPO_ROOT")"

ssh_args=(-i "$SSH_KEY" -o BatchMode=yes)
scp_args=(-i "$SSH_KEY" -o BatchMode=yes)

log "uploading release package to $REMOTE"
ssh "${ssh_args[@]}" "$REMOTE" "rm -rf '$REMOTE_DIR' && mkdir -p '$REMOTE_DIR'"
scp "${scp_args[@]}" "$LOCAL_TAR" "$REMOTE:$REMOTE_DIR/source.tar.gz"
scp "${scp_args[@]}" "$REPO_ROOT/scripts/install-cloud-linux-production.sh" "$REMOTE:$REMOTE_DIR/install-cloud-linux-production.sh"

remote_args=(--source-tar "$REMOTE_DIR/source.tar.gz")
if [[ -n "$RENDERED_ENV_FILE" ]]; then
  scp "${scp_args[@]}" "$RENDERED_ENV_FILE" "$REMOTE:$REMOTE_DIR/brain.env"
  remote_args+=(--rendered-env "$REMOTE_DIR/brain.env")
  if [[ -f "$RENDERED_ENV_FILE.last-deployed" ]]; then
    scp "${scp_args[@]}" "$RENDERED_ENV_FILE.last-deployed" "$REMOTE:$REMOTE_DIR/brain.env.last-deployed"
    remote_args+=(--rendered-env-base "$REMOTE_DIR/brain.env.last-deployed")
  fi
fi
if [[ -n "$RENDERED_AUTH_PASSWORD_FILE" ]]; then
  scp "${scp_args[@]}" "$RENDERED_AUTH_PASSWORD_FILE" "$REMOTE:$REMOTE_DIR/brain-auth-password"
  remote_args+=(--rendered-auth-password "$REMOTE_DIR/brain-auth-password")
  if [[ -f "$RENDERED_AUTH_PASSWORD_FILE.last-deployed" ]]; then
    scp "${scp_args[@]}" "$RENDERED_AUTH_PASSWORD_FILE.last-deployed" "$REMOTE:$REMOTE_DIR/brain-auth-password.last-deployed"
    remote_args+=(--rendered-auth-password-base "$REMOTE_DIR/brain-auth-password.last-deployed")
  fi
fi

log "running remote installer on $REMOTE"
remote_cmd="chmod +x '$REMOTE_DIR/install-cloud-linux-production.sh' && sudo -n env GITHUB_SHA='$SHA' BRAIN_RELEASE_SHA='${BRAIN_RELEASE_SHA:-$SHA}' BRAIN_RELEASE_VERSION='${BRAIN_RELEASE_VERSION:-prod-$SHORT_SHA}' BRAIN_DEPLOY_ENV='${BRAIN_DEPLOY_ENV:-prod}' '$REMOTE_DIR/install-cloud-linux-production.sh'"
for arg in "${remote_args[@]}"; do
  printf -v quoted_arg '%q' "$arg"
  remote_cmd+=" $quoted_arg"
done
ssh "${ssh_args[@]}" "$REMOTE" "$remote_cmd"
