# Demo Validation Log

This file records validated local commands and notable warnings for the Ars Electronica submission sprint.

## 2026-02-25 (Codex implementation pass)

Environment:
- Repo root: `/Users/4jp/Workspace/organvm-ii-poiesis/a-i-council--coliseum`
- Local venv present: `.venv`

Validated commands:

```bash
.venv/bin/pytest -q backend/tests
pnpm -C frontend run lint
pnpm -C frontend run test:ci
pnpm -C frontend run build
cargo test --manifest-path anchor/programs/ai-coliseum/Cargo.toml
```

Observed outcomes:
- Backend tests: pass (`36 passed`)
- Frontend lint: pass
- Frontend tests: pass (`2 passed`)
- Frontend build: pass
- Anchor tests: pass (`test_id ... ok`)

Known warnings (non-blocking, tracked):
- `next build`: Node warning about `--localstorage-file` path.
- `cargo test` (Anchor): `unexpected cfg` macro/toolchain warnings.

New demo workflow assets validated:
- Director Mode scenario file exists:
  - `backend/demo/scenarios/ars_submission_showcase.json`
- Demo APIs compiled + covered by integration tests:
  - `/health/ready`
  - `/api/state/bootstrap`
  - `/api/demo/scenarios`
  - `/api/demo/scenarios/{name}/start`
- Demo scripts created:
  - `scripts/demo_reset.sh`
  - `scripts/demo_start.sh`
  - `scripts/demo_preflight.sh`
  - `scripts/demo_smoke.py`

Smoke validation (local runtime):
- Started backend with Director Mode enabled on a temporary port and external LLM keys disabled.
- Ran:

```bash
.venv/bin/python scripts/demo_smoke.py \
  --api-url http://127.0.0.1:8010 \
  --ws-url ws://127.0.0.1:8010/ws \
  --speed-multiplier 8 \
  --startup-timeout 30 \
  --ws-timeout 20
```

- Result: `PASS`
  - observed websocket `system_status`
  - observed websocket `demo_marker`
  - observed websocket `combat_update`

Notes:
- In this Codex tool environment, background processes launched from one-off shell commands may be cleaned up when the shell exits.
- `scripts/demo_start.sh` is still the intended user workflow for a normal terminal session.

## Final Capture Session (fill in)

Use this section during the real recording session.

- Date/time:
- Machine:
- Resolution:
- `scripts/demo_preflight.sh` result:
- `scripts/demo_smoke.py` result:
- Chosen video file:
- Fallback export file:
- Screenshot files:
- Notes:

## 2026-02-25 (Platform Convergence + Runtime WS pass)

Purpose:
- Validate persisted read-path convergence for events/voting plus runtime (non-Director) `event_update` / `vote_update` websocket emissions after backend/frontend changes.

Validated commands:

```bash
.venv/bin/pytest -q backend/tests
pnpm -C frontend run lint
pnpm -C frontend run test:ci
pnpm -C frontend run build
cargo test --manifest-path anchor/programs/ai-coliseum/Cargo.toml
OPENAI_API_KEY='' ANTHROPIC_API_KEY='' DEMO_DIRECTOR_ENABLED=true .venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8011
.venv/bin/python scripts/demo_smoke.py --api-url http://127.0.0.1:8011 --ws-url ws://127.0.0.1:8011/ws --speed-multiplier 8 --startup-timeout 30 --ws-timeout 20
```

Observed outcomes:
- Backend tests: pass (`44 passed`)
- Frontend lint: pass
- Frontend tests: pass (`3 passed`)
- Frontend build: pass
- Anchor tests: pass (`test_id ... ok`)
- Demo smoke: pass
  - observed websocket `system_status`
  - observed websocket `combat_update`
  - observed websocket `demo_marker`

Notes:
- Temporary smoke backend was run on port `8011`.
- `next build` still emits the known Node warning for `--localstorage-file`.
- Anchor `cargo test` still emits known `unexpected cfg` warnings from macro/toolchain compatibility.
