#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[demo-preflight] repo: $ROOT_DIR"

if [[ ! -x ".venv/bin/python" ]]; then
  echo "[demo-preflight] missing .venv (expected .venv/bin/python)" >&2
  exit 1
fi

echo "[demo-preflight] backend tests"
.venv/bin/pytest -q backend/tests

echo "[demo-preflight] frontend lint"
pnpm -C frontend run lint

echo "[demo-preflight] frontend tests"
pnpm -C frontend run test:ci

echo "[demo-preflight] frontend build"
pnpm -C frontend run build

echo "[demo-preflight] anchor tests"
cargo test --manifest-path anchor/programs/ai-coliseum/Cargo.toml

echo "[demo-preflight] OK"
