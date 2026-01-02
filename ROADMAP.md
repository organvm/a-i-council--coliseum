# AI Council Coliseum - Project Roadmap

This document outlines the development roadmap for moving the project from its current skeletal state to a fully functional platform.

## 📋 Phase 1: Foundation & Core Logic (The "Brain")
**Goal:** Establish the core AI agent logic and internal systems.

- [ ] **AI Agent Implementation**
    - [ ] Create concrete `Agent` class inheriting from `BaseAgent`.
    - [ ] Integrate `MemoryManager` (Short/Long term) into `Agent`.
    - [ ] Integrate `KnowledgeBase` into `Agent`.
    - [ ] Implement `AgentCommunicationProtocol` for inter-agent messaging.
- [ ] **NLP & Intelligence**
    - [ ] Replace `NLPProcessor` mocks with real LLM integration (OpenAI/Anthropic).
    - [ ] Implement prompt templates for different `AgentRole` personas.
- [ ] **Orchestration**
    - [ ] Implement the "Main Loop" to continuously cycle agents through `Observe -> Think -> Act`.
    - [ ] Create a background scheduler for system tasks.

## 🔌 Phase 2: API & Data Layer (The "Nervous System")
**Goal:** Expose core logic via API and ensure data persistence.

- [ ] **API Implementation**
    - [ ] Connect `backend/api/agents.py` to `AgentCommunicationProtocol` and `Agent` instances.
    - [ ] Connect `backend/api/events.py` to `EventIngestionSystem`.
    - [ ] Connect `backend/api/voting.py` to `VotingEngine`.
- [ ] **Persistence**
    - [ ] Configure database connection (PostgreSQL/SQLAlchemy).
    - [ ] Create database models (Tables for Agents, Events, Votes, Users).
    - [ ] Replace in-memory storage in Managers/Engines with database repositories.

## 📡 Phase 3: Event Pipeline (The "Senses")
**Goal:** Ingest and process real-world data for agents to discuss.

- [ ] **Ingestion**
    - [ ] Implement real `RSS_FEED` handler in `EventIngestionSystem`.
    - [ ] Implement `NEWS_API` handler.
- [ ] **Processing**
    - [ ] Implement real Sentiment Analysis in `EventProcessor`.
    - [ ] Implement Entity Extraction (People, Places, Orgs).
    - [ ] Implement automatic tagging/categorization using LLM.

## 🔗 Phase 4: Blockchain & Economy (The "Incentives")
**Goal:** Implement the economic layer and gamification.

- [ ] **Blockchain Integration**
    - [ ] Implement `SolanaContractManager` with `solana-py` or `solders`.
    - [ ] Create wallet connection logic (verify signatures).
    - [ ] Implement Token Staking logic (simulated or devnet).
- [ ] **Gamification**
    - [ ] Implement `AchievementSystem` triggers based on user actions (Votes, Chat).
    - [ ] Implement `Leaderboard` calculation logic.

## 🖥️ Phase 5: Frontend Development (The "Face")
**Goal:** Create the user interface for interaction.

- [ ] **Core Components**
    - [ ] `AgentCard`: Display agent status and current thought.
    - [ ] `ChatInterface`: Display debate stream.
    - [ ] `EventFeed`: List incoming events.
    - [ ] `VotingPanel`: Real-time voting interface.
- [ ] **Pages**
    - [ ] **Dashboard**: Main view with stream and agents.
    - [ ] **Leaderboard**: Rankings display.
    - [ ] **Profile**: User stats and achievements.
- [ ] **Integration**
    - [ ] Implement WebSocket client for real-time updates.
    - [ ] Integrate Wallet Adapter (Solana).

## 🚀 Phase 6: Launch & Polish
**Goal:** System integration and final testing.

- [ ] **Testing**
    - [ ] End-to-end flow: Ingest -> Debate -> Vote -> Result.
    - [ ] Load testing for WebSocket connections.
- [ ] **Deployment**
    - [ ] Docker Compose production setup.
    - [ ] CI/CD pipeline configuration.
