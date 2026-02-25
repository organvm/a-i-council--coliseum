# Ars Electronica Submission Sprint

**Deadline:** March 4, 2026 (Prix Ars Electronica Interactive Art+)
**Current Date:** February 24, 2026
**Remaining Days:** 8

## Issue Categorization & Assignment

| ID | Title | Priority | Owner | Deadline | Status |
|---|---|---|---|---|---|
| #156 | Fix stale venv and verify backend starts | **High (P0)** | Gemini CLI | Feb 24 | ✅ Resolved |
| #157 | Create demo seed script with philosophical agents | **High (P1)** | Gemini CLI | Feb 24 | ✅ Resolved |
| #158 | Wire autonomous demo loop | **High (P1)** | Gemini CLI | Feb 25 | ✅ Resolved |
| #159 | Fix frontend WebSocket handling and wire BattleScene | **High (P2)** | Gemini CLI | Feb 25 | ✅ Resolved |
| #160 | Visual polish for demo video recording | **Medium (P3)** | Gemini CLI | Feb 26 | ✅ Resolved |
| #161 | Record 3-minute demo video and capture screenshots | **Medium (P4)** | User | Feb 27 | ⏳ Ready for User |

## Dependency Map
- **#156** ✅
- **#157** ✅
- **#158** ✅
- **#159** ✅
- **#160** ✅
- **#161** ⏳

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
