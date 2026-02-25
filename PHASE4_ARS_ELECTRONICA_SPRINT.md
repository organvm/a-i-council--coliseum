# Ars Electronica Submission Sprint

**Deadline:** March 4, 2026 (Prix Ars Electronica Interactive Art+)
**Current Date:** February 25, 2026
**Remaining Days:** 7

## Issue Categorization & Assignment

| ID | Title | Priority | Owner | Deadline | Status |
|---|---|---|---|---|---|
| #156 | Fix stale venv and verify backend starts | **High (P0)** | Gemini CLI | Feb 24 | ✅ Resolved |
| #157 | Create demo seed script with philosophical agents | **High (P1)** | Gemini CLI | Feb 24 | ✅ Resolved |
| #158 | Wire autonomous demo loop | **High (P1)** | Gemini CLI | Feb 25 | ✅ Resolved |
| #159 | Fix frontend WebSocket handling and wire BattleScene | **High (P2)** | Gemini CLI | Feb 25 | ✅ Resolved |
| #160 | Visual polish for demo video recording | **Medium (P3)** | Gemini CLI | Feb 26 | ✅ Resolved |
| #161 | Record 3-minute demo video and capture screenshots | **Medium (P4)** | User | Feb 27 | ⏳ Ready for User |
| #162 | Add Director Mode deterministic demo sequence + demo markers | **High (P1)** | Codex | Feb 25 | ✅ Resolved |
| #163 | Add demo readiness APIs/scripts (`/health/ready`, bootstrap, preflight/smoke) | **High (P1)** | Codex | Feb 25 | ✅ Resolved |
| #164 | Frontend demo overlays, WS reconnect status, simulated vote visuals | **High (P2)** | Codex | Feb 25 | ✅ Resolved |

## Dependency Map
- **#156** ✅
- **#157** ✅
- **#158** ✅
- **#159** ✅
- **#160** ✅
- **#161** ⏳
- **#162** ✅
- **#163** ✅
- **#164** ✅

## Verification Summary

### P0: #156 - Environment Fix ✅
- `.venv/` recreated and deps installed.
- `pytest` passes 28/28 tests.
- Backend starts cleanly with SQLite.

### P1: #157 - Seed Data ✅
- `backend/scripts/seed_demo.py` updated with lowercase roles.
- Database seeded successfully. 48 agents available.

### P1: #158 - Autonomous Loop ✅
- Interval reduced to 15s.
- `AutonomousArenaWorker` successfully injects random topics from `SIMULATED_NEWS`.
- Combat sessions auto-trigger and progress.

### P2: #159 - Frontend Wiring ✅
- Consolidated WebSocket logic: single root connection in `page.tsx` updates global store.
- `Arena3D` and `BattleScene` react to `latestCombatEvent` from store.
- Fixed missing font error.

### P3: #160 - Visual Polish ✅
- Agent avatars now use role-based 3D geometries (Sphere, Octahedron, Dodecahedron).
- `BattleScene` features a pulsing red border/glow and scale effect during active combat.
- Battle logs are rendered in real-time with auto-scroll.

### P4: #161 - Demo Recording ⏳
- **Instructions for User:**
  1. Start the system: `source .venv/bin/activate && export PYTHONPATH=$PYTHONPATH:. && uvicorn backend.main:app & cd frontend && pnpm run dev`
  2. Open `http://localhost:3000` in a clean browser window (1920x1080).
  3. Wait for the autonomous loop to kick in (approx 15-20s).
  4. Record for 3 minutes, ensuring you capture:
     - The event ticker scrolling.
     - Agents debating in the chat stream.
     - 3D Arena attack animations.
     - BattleScene HP bars and combat logs.
  5. Take 4 high-res screenshots of the key components.

### P1: #162 - Director Mode Deterministic Sequence ✅
- Added Director Mode scenario runner with JSON beat sequencing in `backend/demo/director.py`.
- Added default capture scenario: `backend/demo/scenarios/ars_submission_showcase.json`.
- Emits explicit websocket `demo_marker` events for title/topic/combat/results moments.

### P1: #163 - Demo Readiness APIs + Scripts ✅
- Added `GET /health/ready` readiness endpoint.
- Added `GET /api/state/bootstrap` frontend hydration snapshot.
- Added demo API controls under `/api/demo/*` (list/status/start/reset).
- Added scripts:
  - `scripts/demo_reset.sh`
  - `scripts/demo_start.sh`
  - `scripts/demo_preflight.sh`
  - `scripts/demo_smoke.py`
- Demo startup scripts now default to local fallback mode (external LLM calls disabled unless explicitly allowed).
- Knowledge-base embedding calls now no-op without API keys to avoid demo-time 401 spam.

### P2: #164 - Frontend Demo Overlay / Reliability ✅
- Added websocket reconnect status badge and mode badge (`director` / `autonomous`) in the main header.
- Added cinematic `DemoOverlay` for `demo_marker` events.
- Added typed handling for websocket `demo_marker`, `vote_update`, and `system_status`.
- Voting panel now renders live simulated audience updates and finalized result snapshots.
- BattleScene readability improved with timestamped logs + impact overlays.

## Known Warnings (Non-Blocking, Tracked)

- Frontend `next build` emits Node warning: ``--localstorage-file`` provided without valid path.
- Anchor `cargo test` emits `unexpected cfg` warnings from macro/toolchain compatibility, but tests pass.
