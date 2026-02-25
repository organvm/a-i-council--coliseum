# Quickstart

## 1) Run with Docker Compose (recommended)

```bash
git clone https://github.com/ivviiviivvi/a-i-council--coliseum.git
cd a-i-council--coliseum
cp .env.example .env
BACKEND_PORT=18000 docker compose up -d
```

Check health:

```bash
curl http://localhost:18000/health
```

Open:

- API docs: `http://localhost:18000/docs`
- Frontend: `http://localhost:3000`

Stop:

```bash
BACKEND_PORT=18000 docker compose down
```

## 2) Run backend locally (no Docker)

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements-test.txt
# runtime-only installs use backend/requirements.txt
uvicorn backend.main:app --reload
```

Backend:

- `http://localhost:8000/health`
- `http://localhost:8000/docs`

## 3) Run frontend locally

```bash
cd frontend
pnpm install --frozen-lockfile
pnpm run dev
```

Frontend:

- `http://localhost:3000`

## 4) MVP smoke checks

```bash
curl http://localhost:8000/api/agents
curl http://localhost:8000/api/events
curl http://localhost:8000/api/voting/sessions
```

## 5) Validation commands

```bash
python -m compileall backend
python -m pytest -q backend/tests
cd frontend && pnpm run lint && pnpm run build
```
