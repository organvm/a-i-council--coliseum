# Backend Implementation Todos

This file tracks granular tasks for the backend development.

## 🧠 AI Agents (`backend/ai_agents/`)

- [x] **Agent Core**
    - [x] Create `Agent` class in `agent.py` (inherits `BaseAgent`).
    - [x] Implement `process_message` handler.
    - [x] Implement `make_decision` logic using `DecisionEngine`.
    - [x] Implement `generate_response` calling `NLPProcessor`.
- [x] **NLP Module** (`nlp_module.py`)
    - [x] Integrate OpenAI API client (or similar).
    - [x] Implement `analyze_sentiment` using LLM or NLTK/TextBlob.
    - [x] Implement `extract_entities` using Spacy or LLM.
    - [x] Implement `summarize` using LLM.
- [x] **Orchestration**
    - [x] Create `SystemOrchestrator` class to manage the lifecycle of all agents.
    - [x] Implement a "Tick" loop (e.g., `asyncio.create_task`) that triggers agents to "perceive" and "act" periodically.

## 🔌 API Layer (`backend/api/`)

- [x] **Dependency Injection**
    - [x] Create a `get_system_instance` dependency to share the active `Orchestrator` and `Engines` across requests.
- [x] **Agents API** (`agents.py`)
    - [x] Implement `GET /` to return real active agents from memory.
    - [x] Implement `POST /` to spawn new agents dynamically.
    - [x] Implement `GET /{id}/memory` to inspect agent state.
- [x] **Events API** (`events.py`)
    - [x] Connect `POST /ingest` to `EventIngestionSystem`.
    - [x] Implement `GET /` with filtering (category, source).
- [ ] **Voting API** (`voting.py`)
    - [ ] Connect `POST /sessions` to `VotingEngine.create_session`.
    - [ ] Connect `POST /vote` to `VotingEngine.cast_vote`.
    - [ ] Implement WebSocket endpoint for real-time vote updates.

## 📡 Event Pipeline (`backend/event_pipeline/`)

- [x] **Ingestion Sources** (`ingestion.py`)
    - [x] Implement `RSSHandler` to parse XML feeds.
    - [x] Implement `NewsAPIHandler` to fetch from external APIs.
- [x] **Processing** (`processing.py`)
    - [ ] Connect `EventProcessor` to `NLPProcessor` for enrichment.
    - [x] Implement `prioritization.py` logic to score events based on keywords/sentiment.

## 🗳️ Voting & Gamification (`backend/voting/`)

- [ ] **Persistence**
    - [ ] Modify `VotingEngine` to save/load sessions from DB.
- [ ] **Achievements** (`achievements.py`)
    - [ ] Create event listeners for: `VoteCast`, `MessageSent`, `SessionWon`.
    - [ ] Implement logic to check criteria and award badges.

## ⛓️ Blockchain (`backend/blockchain/`)

- [ ] **Solana Integration** (`solana_contracts.py`)
    - [ ] Set up `AsyncClient` from `solana.rpc.async_api`.
    - [ ] Implement `verify_wallet_signature` for auth.
    - [ ] Implement `monitor_program` to listen for on-chain events.
- [ ] **Tokenomics**
    - [ ] Implement `calculate_staking_rewards`.

## 💾 Database & Infrastructure

- [ ] **Models**
    - [ ] Create SQLAlchemy models in `backend/database/models.py`.
    - [ ] Set up `alembic` for migrations.
- [ ] **Configuration**
    - [ ] Update `config.py` to read DB credentials from `.env`.
