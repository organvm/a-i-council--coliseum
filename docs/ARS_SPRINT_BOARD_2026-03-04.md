# Ars Electronica Sprint Board (March 4, 2026)

Source of truth for the submission sprint.

## Labels (only these 3)

- `Submission Blocker`: Prevents recording, packaging, or truthful submission.
- `Demo Drama`: Increases cinematic impact / legibility of the 3-minute demo.
- `Credibility`: Improves trust, reproducibility, or honest status communication.

## Current Status (2026-02-25)

- Repo checks green locally:
  - `.venv/bin/pytest -q backend/tests`
  - `pnpm -C frontend run lint`
  - `pnpm -C frontend run test:ci`
  - `pnpm -C frontend run build`
  - `cargo test --manifest-path anchor/programs/ai-coliseum/Cargo.toml`
- Director Mode implemented for deterministic capture (`/api/demo/*` + `demo_marker` events).
- Frontend now shows:
  - websocket connection status
  - mode badge (`director`/`autonomous`)
  - cinematic overlays from demo markers
  - live simulated vote visuals
- Remaining user-critical task: record final demo + capture screenshots.

## Active Work Queue

### Submission Blocker

- [ ] Run `scripts/demo_preflight.sh` on the final capture machine/session.
- [ ] Run `scripts/demo_reset.sh` before the final recording session.
- [ ] Run `scripts/demo_start.sh` and confirm backend/frontend logs are healthy.
- [ ] Run `scripts/demo_smoke.py` and verify `demo_marker` + `combat_update|vote_update` arrive.
- [ ] Record final 3-minute 1920x1080 capture.
- [ ] Export fallback video version (secondary encode/container).
- [ ] Capture 4 submission screenshots.

### Demo Drama

- [ ] Rehearse Director Mode timing against actual recording cadence (3 full runs).
- [ ] Select best 4 screenshot moments from `demo_marker` beats (`intro`, `combat`, `vote`, `results`).
- [ ] If needed, tune scenario beat delays only (no feature expansion).
- [ ] Validate UI readability at the actual capture resolution.

### Credibility

- [x] Add `GET /health/ready` and `GET /api/state/bootstrap`.
- [x] Add reproducible demo scripts (`demo_reset`, `demo_start`, `demo_preflight`, `demo_smoke.py`).
- [x] Label demo telemetry as simulated in UI.
- [x] Expose mode badge and on-chain prototype caveat in UI.
- [ ] Prepare short submission system statement (implemented vs prototype vs roadmap).
- [ ] Include reproducibility appendix in submission notes using `docs/DEMO_VALIDATION_LOG.md`.

## Freeze Guardrails (Late-Iteration Mode)

- Soft freeze: end of Day 5
  - only `Submission Blocker` and `Demo Drama`
  - no new architecture work
- Hard freeze: 24h before submission (March 3, 2026 local time)
  - blocker fixes only
  - no new visual experiments unless they solve capture clarity
- Submission lock: March 4, 2026 morning local time
  - package + upload only
