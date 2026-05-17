#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BRAIN_SUBMISSION_BASE_URL:-https://brain.dceb.net}"
OUT_DIR="${BRAIN_SUBMISSION_SCREENSHOT_DIR:-docs/openai-submission-assets/screenshots}"
CHROME="${CHROME_BIN:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"

if [[ ! -x "$CHROME" ]]; then
  printf 'Chrome binary not found or not executable: %s\n' "$CHROME" >&2
  exit 2
fi

mkdir -p "$OUT_DIR"

capture() {
  local path="$1"
  local filename="$2"
  "$CHROME" \
    --headless=new \
    --disable-gpu \
    --no-first-run \
    --no-default-browser-check \
    --window-size=1440,1100 \
    "--screenshot=$OUT_DIR/$filename" \
    "$BASE_URL$path"
}

capture "/" "01-dashboard-login.png"
capture "/privacy" "02-privacy.png"
capture "/terms" "03-terms.png"
capture "/support" "04-support.png"

printf 'Saved OpenAI submission screenshots to %s\n' "$OUT_DIR"
