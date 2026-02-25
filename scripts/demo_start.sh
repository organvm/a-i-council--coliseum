#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

LOG_DIR="${LOG_DIR:-$ROOT_DIR/logs/demo}"
mkdir -p "$LOG_DIR"

API_URL="${API_URL:-http://localhost:8000}"
WS_URL="${WS_URL:-ws://localhost:8000/ws}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"
DEMO_DB="${DEMO_DB:-$ROOT_DIR/coliseum_demo.db}"
SCENARIO="${SCENARIO:-ars_submission_showcase}"
FRONTEND_SERVER_MODE="${FRONTEND_SERVER_MODE:-dev}"

if [[ ! -x ".venv/bin/uvicorn" ]]; then
  echo "[demo-start] missing .venv (expected .venv/bin/uvicorn)" >&2
  exit 1
fi

echo "[demo-start] logs: $LOG_DIR"
echo "[demo-start] using scenario: $SCENARIO"
echo "[demo-start] frontend server mode: $FRONTEND_SERVER_MODE"

export DATABASE_URL="sqlite+aiosqlite:///$DEMO_DB"
export APP_ENV="${APP_ENV:-development}"
export PYTHONPATH="$ROOT_DIR${PYTHONPATH:+:$PYTHONPATH}"
export DEMO_DIRECTOR_ENABLED="true"
export DEMO_DIRECTOR_AUTOSTART_SCENARIO="${DEMO_DIRECTOR_AUTOSTART_SCENARIO:-$SCENARIO}"
export CORS_ORIGINS="${CORS_ORIGINS:-$FRONTEND_URL}"
export FRONTEND_URL="$FRONTEND_URL"
export NEXT_PUBLIC_CAPTURE_PROFILE="${NEXT_PUBLIC_CAPTURE_PROFILE:-recording}"
export NEXT_PUBLIC_ARENA_3D_MODE="${NEXT_PUBLIC_ARENA_3D_MODE:-auto}"

if [[ "${DEMO_ALLOW_EXTERNAL_LLM:-false}" != "true" ]]; then
  export OPENAI_API_KEY=""
  export ANTHROPIC_API_KEY=""
  echo "[demo-start] external LLM calls disabled (deterministic local fallback mode)"
fi

BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"
FRONTEND_BUILD_LOG="$LOG_DIR/frontend-build.log"

nohup .venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000 >"$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID" > "$LOG_DIR/backend.pid"

if [[ "$FRONTEND_SERVER_MODE" == "prod" ]]; then
  echo "[demo-start] building frontend for production (log: $FRONTEND_BUILD_LOG)"
  env NEXT_PUBLIC_API_URL="$API_URL" NEXT_PUBLIC_WS_URL="$WS_URL" \
    pnpm -C frontend run build >"$FRONTEND_BUILD_LOG" 2>&1
  nohup env NEXT_PUBLIC_API_URL="$API_URL" NEXT_PUBLIC_WS_URL="$WS_URL" \
    pnpm -C frontend exec next start -H 0.0.0.0 -p 3000 >"$FRONTEND_LOG" 2>&1 &
elif [[ "$FRONTEND_SERVER_MODE" == "dev" ]]; then
  nohup env NEXT_PUBLIC_API_URL="$API_URL" NEXT_PUBLIC_WS_URL="$WS_URL" pnpm -C frontend run dev >"$FRONTEND_LOG" 2>&1 &
else
  echo "[demo-start] invalid FRONTEND_SERVER_MODE=$FRONTEND_SERVER_MODE (expected dev|prod)" >&2
  kill "$BACKEND_PID" >/dev/null 2>&1 || true
  exit 1
fi
FRONTEND_PID=$!
echo "$FRONTEND_PID" > "$LOG_DIR/frontend.pid"

echo "[demo-start] backend pid: $BACKEND_PID"
echo "[demo-start] frontend pid: $FRONTEND_PID"
echo "[demo-start] backend log: $BACKEND_LOG"
echo "[demo-start] frontend log: $FRONTEND_LOG"
echo "[demo-start] next step: .venv/bin/python scripts/demo_smoke.py"
