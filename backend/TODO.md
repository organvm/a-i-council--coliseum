# Backend TODO

## Completed in MVP Stabilization

- [x] Rebuilt `Agent` into one coherent implementation.
- [x] Rebuilt `SystemOrchestrator` with explicit runtime initialization.
- [x] Standardized orchestrator public contract:
  - [x] `add_agent`
  - [x] `remove_agent`
  - [x] `get_agent`
  - [x] `list_agents`
  - [x] `start` / `stop`
  - [x] `broadcast_event`
  - [x] `register_agent` alias retained
- [x] Made OpenAI dependency optional in NLP module with deterministic fallback behavior.
- [x] Fixed `clear_old_events` cutoff math using `timedelta`.
- [x] Aligned API routers to orchestrator-backed in-memory flows.
- [x] Implemented in-memory voting session lifecycle APIs.
- [x] Kept blockchain write endpoints explicitly `501`.
- [x] Added contract-based test coverage for agents, orchestrator, events, voting, API integration, and lifespan.
- [x] Added compile gate and test/bootstrap updates for CI.

## Deferred (Roadmap)

- [ ] Replace in-memory state with durable persistence for events, votes, and user progression.
- [ ] Add robust auth/authz and abuse controls for voting endpoints.
- [ ] Implement blockchain write paths after secure key-management and signing model is approved.
- [ ] Add websocket-based realtime updates for voting and event streams.
- [ ] Expand event source adapters beyond manual/API ingestion.
- [ ] Add observability and production-grade metrics/alerts.

