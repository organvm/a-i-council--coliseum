# Submission Reproducibility Appendix

## Scope

This appendix documents the reproducible local workflow used to validate the demo stack and prepare final capture for the March 4, 2026 submission window.

## Environment

- Repo root: `/Users/4jp/Workspace/organvm-ii-poiesis/a-i-council--coliseum`
- Python virtualenv: `.venv`
- Frontend package manager: `pnpm`

## CI-Parity Validation Commands

Run from repo root:

```bash
.venv/bin/pytest -q backend/tests
pnpm -C frontend run lint
pnpm -C frontend run test:ci
pnpm -C frontend run build
cargo test --manifest-path anchor/programs/ai-coliseum/Cargo.toml
```

Expected outcomes:
- Backend tests pass
- Frontend lint/tests/build pass
- Anchor `cargo test` passes (`test_id ... ok`)
- Known warnings may still appear (documented in `docs/DEMO_VALIDATION_LOG.md`)

## Demo Capture Readiness Workflow

### 1. Preflight (final capture machine/session)

```bash
./scripts/demo_preflight.sh
```

Checks:
- environment/tooling availability
- backend/frontend prerequisites
- capture-related readiness signals

### 2. Reset Runtime State

```bash
./scripts/demo_reset.sh
```

Purpose:
- reset local demo/runtime state before recording
- avoid drift between rehearsal and final capture

### 3. Start the Demo Stack

```bash
./scripts/demo_start.sh
```

Notes:
- defaults to local fallback mode when external model keys are not configured
- Director Mode endpoints remain available for deterministic scenario runs

### 4. Smoke Test APIs + WebSocket + Director Mode

```bash
.venv/bin/python scripts/demo_smoke.py
```

Smoke test checks:
- `/health`
- `/health/ready`
- `/api/state/bootstrap`
- Director Mode scenario start (`/api/demo/scenarios/{name}/start`)
- websocket reception of `system_status`, `demo_marker`, and `combat_update|vote_update`

### 5. Record Final Capture

- Resolution: `1920x1080`
- Duration target: `3 minutes`
- Include the key beats:
  - intro/title
  - live debate/combat
  - vote accumulation
  - result/finalization moment

### 6. Capture Screenshots

Capture at least 4 screenshots covering:
- arena/agents
- combat action
- voting state/results
- overlay/title/system context

## Evidence and Logging

- Record validation outcomes in `/Users/4jp/Workspace/organvm-ii-poiesis/a-i-council--coliseum/docs/DEMO_VALIDATION_LOG.md`
- Keep final capture artifacts under `/Users/4jp/Workspace/organvm-ii-poiesis/a-i-council--coliseum/output/`

## Known Non-Blocking Warnings

- `next build` may emit a Node warning for `--localstorage-file`
- Anchor `cargo test` may emit `unexpected cfg` warnings from macro/toolchain compatibility

These warnings are tracked and do not currently block local validation or demo capture.
