#!/usr/bin/env bash
set -euo pipefail

SERVICE_USERS=(oric_prod oric_staging)
PRIMARY_GROUP_ID="20"
HOME_DIR="/var/empty"
SHELL_PATH="/usr/bin/false"

if [[ "$(id -u)" != "0" ]]; then
  exec sudo "$0" "$@"
fi

next_uid() {
  dscl . -list /Users UniqueID |
    awk '$2 >= 550 && $2 < 600 { if ($2 > max) max = $2 } END { print max ? max + 1 : 550 }'
}

ensure_service_user() {
  local username="$1"
  if id -u "$username" >/dev/null 2>&1; then
    printf '[setup] user exists: %s\n' "$username"
    return
  fi

  local uid
  uid="$(next_uid)"
  printf '[setup] creating hidden service user %s uid=%s\n' "$username" "$uid"
  dscl . -create "/Users/$username"
  dscl . -create "/Users/$username" UserShell "$SHELL_PATH"
  dscl . -create "/Users/$username" RealName "Brain service user ($username)"
  dscl . -create "/Users/$username" UniqueID "$uid"
  dscl . -create "/Users/$username" PrimaryGroupID "$PRIMARY_GROUP_ID"
  dscl . -create "/Users/$username" NFSHomeDirectory "$HOME_DIR"
  dscl . -create "/Users/$username" IsHidden 1
  dscl . -passwd "/Users/$username" "*"
}

for username in "${SERVICE_USERS[@]}"; do
  ensure_service_user "$username"
done

printf '[setup] service users ready: %s\n' "${SERVICE_USERS[*]}"
