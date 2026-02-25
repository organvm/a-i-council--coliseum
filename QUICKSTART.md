# Quickstart

## 1) Run with Docker Compose (recommended)

```bash
git clone https://github.com/ivviiviivvi/a-i-council--coliseum.git
cd a-i-council--coliseum
cp .env.example .env
# Required outside local/dev defaults:
# export JWT_SECRET_KEY="$(openssl rand -hex 32)"
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
# For non-dev environments set a real JWT secret:
# export APP_ENV=production
# export JWT_SECRET_KEY="replace-with-long-random-secret"
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
pytest -q backend/tests
pnpm -C frontend run lint
pnpm -C frontend run test:ci
pnpm -C frontend run build
cargo test --manifest-path anchor/programs/ai-coliseum/Cargo.toml
```

## 6) Notes on feature maturity

- Backend and frontend MVP loops are runnable locally today.
- The Solana Anchor program is an active prototype; use the `cargo test` command above to verify current contract compile/runtime status.
- Some governance/economy behaviors are represented in application logic before full on-chain enforcement is complete.

## 7) Anchor program ID / keypair workflow (for deployment readiness)

When `solana-keygen` is available, generate a dedicated program keypair and sync the pubkey into both `anchor/Anchor.toml` and the Anchor program `declare_id!`:

```bash
./scripts/generate-anchor-program-keypair.sh --apply
```

Notes:

- This creates `anchor/target/deploy/ai_coliseum-keypair.json` by default.
- The keypair JSON must **not** be committed.
- Use `--force` to regenerate/overwrite, or `--keypair <path>` to write elsewhere.
