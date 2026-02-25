#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

API_URL="${API_URL:-http://localhost:8000}"
WS_URL="${WS_URL:-ws://localhost:8000/ws}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"
OUTPUT_DIR="${OUTPUT_DIR:-$ROOT_DIR/output/playwright}"
DURATION_SECONDS="${DURATION_SECONDS:-180}"
SCENARIO="${SCENARIO:-ars_submission_showcase}"
SPEED_MULTIPLIER="${SPEED_MULTIPLIER:-1.0}"
WS_TIMEOUT="${WS_TIMEOUT:-20}"
STARTUP_TIMEOUT="${STARTUP_TIMEOUT:-40}"
KEEP_SERVERS="${KEEP_SERVERS:-false}"
PLAYWRIGHT_INSTALL_BROWSER="${PLAYWRIGHT_INSTALL_BROWSER:-true}"
HEADLESS="${HEADLESS:-true}"
FRONTEND_SERVER_MODE="${FRONTEND_SERVER_MODE:-prod}"

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  if [[ "$KEEP_SERVERS" == "true" ]]; then
    echo "[demo-record] KEEP_SERVERS=true; leaving demo services running"
    return
  fi

  for pid in "$FRONTEND_PID" "$BACKEND_PID"; do
    if [[ -n "${pid:-}" ]] && kill -0 "$pid" >/dev/null 2>&1; then
      kill "$pid" >/dev/null 2>&1 || true
    fi
  done
}
trap cleanup EXIT

echo "[demo-record] step 1/5 reset demo state"
"$ROOT_DIR/scripts/demo_reset.sh"

echo "[demo-record] step 2/5 start backend + frontend"
FRONTEND_SERVER_MODE="$FRONTEND_SERVER_MODE" "$ROOT_DIR/scripts/demo_start.sh"

if [[ -f "$ROOT_DIR/logs/demo/backend.pid" ]]; then
  BACKEND_PID="$(cat "$ROOT_DIR/logs/demo/backend.pid")"
fi
if [[ -f "$ROOT_DIR/logs/demo/frontend.pid" ]]; then
  FRONTEND_PID="$(cat "$ROOT_DIR/logs/demo/frontend.pid")"
fi
echo "[demo-record] backend pid: ${BACKEND_PID:-unknown}"
echo "[demo-record] frontend pid: ${FRONTEND_PID:-unknown}"

echo "[demo-record] step 3/5 smoke test"
.venv/bin/python "$ROOT_DIR/scripts/demo_smoke.py" \
  --api-url "$API_URL" \
  --ws-url "$WS_URL" \
  --scenario "$SCENARIO" \
  --ws-timeout "$WS_TIMEOUT" \
  --startup-timeout "$STARTUP_TIMEOUT"

if [[ "$PLAYWRIGHT_INSTALL_BROWSER" == "true" ]]; then
  echo "[demo-record] ensuring Playwright chromium is installed"
  pnpm -C frontend exec playwright install chromium >/dev/null
fi

echo "[demo-record] step 4/5 record ${DURATION_SECONDS}s take"
mkdir -p "$OUTPUT_DIR"
API_URL="$API_URL" \
FRONTEND_URL="$FRONTEND_URL" \
SCENARIO="$SCENARIO" \
DURATION_SECONDS="$DURATION_SECONDS" \
SPEED_MULTIPLIER="$SPEED_MULTIPLIER" \
OUTPUT_DIR="$OUTPUT_DIR" \
HEADLESS="$HEADLESS" \
pnpm -C frontend exec node ../scripts/record_demo_take.mjs

LATEST_WEBM="$(ls -1t "$OUTPUT_DIR"/final-take-*.webm | head -1)"
LATEST_MP4="${LATEST_WEBM%.webm}.mp4"

echo "[demo-record] step 5/5 transcode to mp4"
ffmpeg -y -i "$LATEST_WEBM" \
  -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -movflags +faststart \
  -c:a aac -b:a 128k \
  "$LATEST_MP4" >/dev/null 2>&1

echo "[demo-record] webm: $LATEST_WEBM"
echo "[demo-record] mp4:  $LATEST_MP4"
ffprobe -v error -show_entries stream=width,height:format=duration -of default=noprint_wrappers=1 "$LATEST_MP4"
