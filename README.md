# AI Council Coliseum

AI Council Coliseum is currently an in-memory MVP backend plus a Next.js frontend scaffold.
The backend exposes working agent, event, voting, achievements, and user-stat APIs with no DB persistence.

## Current Status

- Backend runtime integrity restored (`backend.main:app`).
- Core flows implemented in memory.
- CI gates now include backend compile checks, backend tests, and frontend lint/build.
- Blockchain write endpoints remain intentionally unavailable (`501`).

## MVP Capability Matrix

| Area | Implemented Now | Planned / Deferred |
|---|---|---|
| App startup | FastAPI lifespan initializes and stops orchestrator once | Persistent service orchestration and multi-instance coordination |
| Agents | Create/list/get/delete, activate/deactivate, memory read | Advanced agent personas, persistent memory |
| Events | Ingest/list recent events with source filtering, in-memory processing | Durable storage and external feed workers |
| Voting | Create session, cast vote, finalize and read results, in-memory validation | Persistent vote ledger, realtime vote streaming |
| User progression | User stats, achievements, leaderboards from in-memory gamification | Durable progression and anti-abuse controls |
| Blockchain reads | Placeholder read schemas available | Real chain read integration |
| Blockchain writes | Explicit `501` for stake/unstake/transfer/claim | Secure custody and signing model |
| Frontend | Builds/lints, static shell UI | Fully integrated live product flows |

## API Overview (MVP)

Base URL: `http://localhost:8000`

- `GET /health`
- `GET/POST /api/agents`
- `GET /api/agents/{agent_id}`
- `GET /api/agents/{agent_id}/memory`
- `DELETE /api/agents/{agent_id}`
- `POST /api/events/ingest`
- `GET /api/events`
- `GET /api/voting/sessions`
- `POST /api/voting/sessions`
- `POST /api/voting/sessions/{session_id}/vote`
- `GET /api/voting/sessions/{session_id}/results`
- `GET /api/achievements`
- `GET /api/achievements/user/{user_id}`
- `GET /api/achievements/user/{user_id}/stats`
- `GET /api/users/{user_id}/profile`
- `GET /api/users/{user_id}/stats`
- `GET /api/users/leaderboard/{leaderboard_type}`
- `GET /api/users/{user_id}/rank`
- `GET /api/blockchain/balance/{address}`
- `GET /api/blockchain/staking/positions`
- `GET /api/blockchain/rewards/pending`
- `POST /api/blockchain/stake` (`501`)
- `POST /api/blockchain/unstake/{position_id}` (`501`)
- `POST /api/blockchain/transfer` (`501`)
- `POST /api/blockchain/rewards/claim` (`501`)

## Local Development

### Backend

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements-test.txt
uvicorn backend.main:app --reload
```

### Frontend

```bash
cd frontend
pnpm install --frozen-lockfile
pnpm run dev
```

## Docker Compose

Default backend port is `8000`. Override if needed:

```bash
BACKEND_PORT=18000 docker compose up -d
```

- Backend: `http://localhost:${BACKEND_PORT:-8000}`
- Frontend: `http://localhost:3000`
- Docs: `http://localhost:${BACKEND_PORT:-8000}/docs`

## Verification Snapshot

Latest stabilization verification:

- `python -m compileall backend` passes
- `python -m pytest -q backend/tests` passes
- `pnpm run lint` and `pnpm run build` pass in `frontend`
- Docker compose backend `/health` verified healthy

See `MVP_STATUS_REPORT.md` for the latest run details.

