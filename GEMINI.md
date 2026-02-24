# AI Council Coliseum - Project Context

Welcome to the AI Council Coliseum project. This document provides the essential context, architectural patterns, and development workflows used in this codebase.

## Project Overview
AI Council Coliseum is a decentralized platform where AI agents debate real-time events. Viewers participate through blockchain-based voting and gamification.

- **Status:** MVP (In-memory backend, Next.js frontend scaffold)
- **Primary Tech Stack:**
  - **Backend:** Python 3.11, FastAPI, Uvicorn, Pytest
  - **Frontend:** Next.js 14, React 18, Tailwind CSS, pnpm, TypeScript, Zustand, Framer Motion
  - **Infrastructure:** Docker Compose
  - **Blockchain:** Solana & Ethereum (Planned integrations, current writes are `501`)

## Architecture
The system is designed with a modular architecture split into several core layers:

1. **API Gateway (FastAPI):** Handles REST and WebSocket endpoints.
2. **Service Layer:**
   - **AI Agent Framework:** 7 modules (Base Agent, Communication, Decision Engine, NLP, Knowledge Base, Memory Manager, Coordination).
   - **Event Pipeline:** 7 components (Ingestion, Classification, Prioritization, Routing, Processing, Storage, Notification).
   - **Voting System:** Voting engine, achievements, gamification, leaderboard.
3. **Data Layer:** Currently in-memory. Roadmap includes PostgreSQL and Redis.

### Core Component: System Orchestrator
The `SystemOrchestrator` (`backend/ai_agents/orchestrator.py`) is the central coordinator that manages agent lifecycles, event ingestion, and voting sessions.

## Building and Running

### Backend
Requires Python 3.11+.
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements-test.txt
# Run the app
uvicorn backend.main:app --reload
```
- API Docs: `http://localhost:8000/docs`

### Frontend
Requires Node.js and pnpm.
```bash
cd frontend
pnpm install --frozen-lockfile
pnpm run dev
```
- App URL: `http://localhost:3000`

### Docker Compose
```bash
docker compose up -d
```
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`

## Development Conventions

- **Python Style:** Follow standard FastAPI/Pydantic patterns. Use async for I/O bound tasks.
- **Frontend Style:** Next.js App Router, functional components, Tailwind CSS for styling.
- **Testing:** 
  - Backend: `pytest` located in `backend/tests/`.
  - Frontend: `lint` and `build` checks.
- **Git Workflow:** Keep changes atomic. Do not commit secrets.

## MVP Capability Matrix
| Area | Status | Note |
|---|---|---|
| Agents | Working | Create/list/get/delete, in-memory memory snapshots |
| Events | Working | Ingest, list, in-memory classification/processing |
| Voting | Working | Session management, weighted voting, results |
| Gamification | Working | Achievements, leaderboards, user stats |
| Blockchain Writes | Unavailable | Returns `501` (Not Implemented) |

## Key Directories
- `backend/ai_agents/`: Core agent logic and orchestrator.
- `backend/api/`: FastAPI route definitions.
- `backend/event_pipeline/`: Event ingestion and processing components.
- `backend/voting/`: Voting engine and gamification logic.
- `frontend/src/app/`: Next.js application structure.
- `docs/`: Architectural documentation and ADRs.

## Roadmap & TODOs
- [ ] Replace in-memory state with durable persistence (PostgreSQL/Redis).
- [ ] Implement robust auth/authz for voting and user management.
- [ ] Integrate real blockchain write paths (Solana/Ethereum).
- [ ] Implement full frontend UI components (Agent views, Chat stream, Voting panel).
- [ ] Add WebSocket real-time updates for live streams.

<!-- ORGANVM:AUTO:START -->
## System Context (auto-generated — do not edit)

**Organ:** ORGAN-II (Art) | **Tier:** standard | **Status:** CANDIDATE
**Org:** `unknown` | **Repo:** `a-i-council--coliseum`

### Edges
- **Consumes** ← `organvm-ii-poiesis/performance-sdk`: unknown
- **Consumes** ← `organvm-ii-poiesis/metasystem-master`: unknown

### Siblings in Art
`core-engine`, `performance-sdk`, `example-generative-music`, `metasystem-master`, `example-choreographic-interface`, `showcase-portfolio`, `archive-past-works`, `case-studies-methodology`, `learning-resources`, `example-generative-visual`, `example-interactive-installation`, `example-ai-collaboration`, `docs`, `a-mavs-olevm`, `.github` ... and 14 more

### Governance
- Consumes Theory (I) concepts, produces artifacts for Commerce (III).

*Last synced: 2026-02-24T12:41:28Z*
<!-- ORGANVM:AUTO:END -->
