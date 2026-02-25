# Roadmap

## Current Baseline (MVP Stabilization Complete)

- Backend runtime compiles and starts cleanly.
- Core APIs operate with in-memory state.
- CI gates compile + backend tests + frontend lint/build.
- Docker compose backend entrypoint aligned to `backend.main:app`.

## Reality Notes (2026-02-25)

- The runtime is currently **hybrid** rather than purely in-memory:
  - agents/events/votes have DB persistence paths
  - voting sessions are partially persisted/hydrated
  - restart consistency and transactional durability are still incomplete
- Submission sprint enablement now includes:
  - Director Mode scenario runner (`/api/demo/*`)
  - bootstrap/readiness endpoints (`/api/state/bootstrap`, `/health/ready`)
  - demo capture scripts in `scripts/`
- Treat `docs/ARS_SPRINT_BOARD_2026-03-04.md` as the source of truth for March 4 submission work.

## Next Milestones

## Phase A: Persistence and Data Contracts

- Add DB-backed repositories for:
  - events
  - voting sessions and votes
  - user progression and achievements
- Keep API contracts stable while replacing in-memory internals.
- Add migration tooling and seed strategy.
- Close hybrid persistence gaps:
  - vote/session close/finalize durability
  - restart consistency tests
  - DB uniqueness constraints (`session_id`, `user_id`)

## Phase B: Security and Access Control

- Add request authentication for mutating endpoints.
- Add authorization checks for privileged operations.
- Add vote-rate limiting and duplicate-abuse protections.
- Define and implement secure blockchain signing/custody model.

## Phase C: Realtime Product Flows

- Add websocket updates for:
  - event ingestion stream
  - voting session updates
  - leaderboard updates
- Integrate frontend pages to live backend contracts.

## Phase D: Blockchain Execution

- Keep read endpoints stable.
- Move write endpoints (`stake`, `unstake`, `transfer`, `claim`) from `501` to secure execution only after signing model approval.
- Add deterministic integration tests for blockchain adapters.

## Phase E: Production Hardening

- Add observability stack (structured logs, metrics, traces).
- Add load/stress tests for agent orchestration and voting traffic.
- Add deployment playbooks and rollback strategy.
