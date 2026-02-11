# Roadmap

## Current Baseline (MVP Stabilization Complete)

- Backend runtime compiles and starts cleanly.
- Core APIs operate with in-memory state.
- CI gates compile + backend tests + frontend lint/build.
- Docker compose backend entrypoint aligned to `backend.main:app`.

## Next Milestones

## Phase A: Persistence and Data Contracts

- Add DB-backed repositories for:
  - events
  - voting sessions and votes
  - user progression and achievements
- Keep API contracts stable while replacing in-memory internals.
- Add migration tooling and seed strategy.

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

