#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DEMO_DB="${DEMO_DB:-$ROOT_DIR/coliseum_demo.db}"

echo "[demo-reset] root: $ROOT_DIR"
echo "[demo-reset] demo db: $DEMO_DB"

rm -f "$DEMO_DB"

if [[ ! -x ".venv/bin/python" ]]; then
  echo "[demo-reset] missing .venv (expected .venv/bin/python)" >&2
  exit 1
fi

export DATABASE_URL="sqlite+aiosqlite:///$DEMO_DB"
export APP_ENV="${APP_ENV:-development}"
export PYTHONPATH="$ROOT_DIR${PYTHONPATH:+:$PYTHONPATH}"

echo "[demo-reset] seeding demo database"
.venv/bin/python -m backend.scripts.seed_demo

echo "[demo-reset] done"
