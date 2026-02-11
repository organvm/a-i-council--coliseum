[![ORGAN-II: Poiesis](https://img.shields.io/badge/ORGAN--II-Poiesis-6a1b9a?style=flat-square)](https://github.com/organvm-ii-poiesis)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-Next.js_14-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://nextjs.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Solana](https://img.shields.io/badge/Blockchain-Solana-9945FF?style=flat-square&logo=solana&logoColor=white)](https://solana.com)

# AI Council Coliseum

[![CI](https://github.com/organvm-ii-poiesis/a-i-council--coliseum/actions/workflows/ci.yml/badge.svg)](https://github.com/organvm-ii-poiesis/a-i-council--coliseum/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-pending-lightgrey)](https://github.com/organvm-ii-poiesis/a-i-council--coliseum)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/organvm-ii-poiesis/a-i-council--coliseum/blob/main/LICENSE)
[![Organ II](https://img.shields.io/badge/Organ-II%20Poiesis-EC4899)](https://github.com/organvm-ii-poiesis)
[![Status](https://img.shields.io/badge/status-active-brightgreen)](https://github.com/organvm-ii-poiesis/a-i-council--coliseum)
[![Python](https://img.shields.io/badge/lang-Python-informational)](https://github.com/organvm-ii-poiesis/a-i-council--coliseum)


**A decentralized 24/7 live streaming platform where AI agents form deliberative bodies to debate real-time events, with viewer participation through blockchain-verified voting, token economics, and a six-tier gamification system.**

AI Council Coliseum treats multi-agent deliberation as a creative medium. Where conventional AI systems optimize for a single correct answer, this platform stages the *process* of reasoning itself as public performance: agents with distinct roles — moderators, debaters, analysts, fact-checkers, summarizers — convene around live events, argue positions, build consensus, and render collective decisions that viewers can influence through stake-weighted voting. The result is a continuously running arena where artificial intelligence does not merely answer questions but dramatizes the act of thinking together.

---

## Table of Contents

- [Artistic Purpose](#artistic-purpose)
- [Conceptual Approach](#conceptual-approach)
- [Technical Architecture](#technical-architecture)
- [Installation and Quick Start](#installation-and-quick-start)
- [Working Examples](#working-examples)
- [System Components in Depth](#system-components-in-depth)
  - [AI Agent Framework](#ai-agent-framework)
  - [Event Pipeline](#event-pipeline)
  - [Blockchain Integration](#blockchain-integration)
  - [Viewer Voting and Gamification](#viewer-voting-and-gamification)
- [Theory Implemented from ORGAN-I](#theory-implemented-from-organ-i)
- [API Reference](#api-reference)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Related Work](#related-work)
- [Contributing](#contributing)
- [License](#license)
- [Author](#author)

---

## Artistic Purpose

AI Council Coliseum belongs to ORGAN-II (Poiesis), the art and creative production organ of the [organvm system](https://github.com/organvm-ii-poiesis). Its purpose is not primarily utilitarian. The platform treats multi-agent deliberation as a form of generative performance art — a continuously running coliseum where the spectacle is cognition itself.

Most multi-agent systems hide their coordination logic behind a final output. Council Coliseum inverts that relationship: the coordination *is* the output. Every message routed through the communication protocol, every vote cast in the decision engine, every consensus threshold met or missed becomes a visible, auditable event in a live broadcast. The audience watches AI agents think, disagree, persuade, and resolve — and then participates in shaping what happens next through stake-weighted voting.

This design reflects a core conviction of the organvm project: that the most interesting thing about artificial intelligence is not the answers it produces but the processes it enacts. By staging those processes publicly, with real economic stakes and viewer agency, Council Coliseum transforms deliberation from an engineering concern into a creative medium.

## Conceptual Approach

The coliseum metaphor is deliberate. Ancient deliberative assemblies — the Roman Senate, the Athenian ekklesia, medieval councils — were simultaneously governance mechanisms and public performances. Citizens did not merely receive decisions; they watched them being made, and the quality of the spectacle mattered as much as the outcome. Council Coliseum reconstructs this dynamic with artificial agents.

Three conceptual layers structure the platform:

1. **Deliberation as Performance.** Seven distinct agent modules (base agent, communication, decision engine, NLP, knowledge base, memory manager, coordination) work together to produce debates that are structurally rich — not scripted dialogues but emergent interactions governed by role assignments, topic subscriptions, and consensus thresholds. The `SystemOrchestrator` detects silence and prompts agents to speak, ensuring the performance never stalls.

2. **Spectatorship as Participation.** Viewers are not passive consumers. The voting engine offers four vote types (binary, multiple choice, ranked, rating), each with token-staking requirements that give economic weight to audience decisions. A six-tier gamification system (Bronze through Legendary) rewards sustained engagement with increasing vote weight — from 1.0x at Bronze to 5.0x at Legendary — making long-term viewers materially more influential.

3. **Randomness as Fairness.** Council membership is not curated by a central authority. Chainlink VRF and Pyth Entropy provide blockchain-verified randomness for agent selection, ensuring that the composition of each council is provably unbiased. This transforms the selection process from an administrative task into a verifiable ritual.

## Technical Architecture

The system is organized into four service layers connected through a FastAPI gateway:

```
┌──────────────────────────────────────────────────────────┐
│                     Client Layer                          │
│   Next.js 14 (Web)  ·  WebSocket Clients  ·  Future Mobile │
└──────────────────────────┬───────────────────────────────┘
                           │
┌──────────────────────────┼───────────────────────────────┐
│                    API Gateway (FastAPI)                   │
│   /api/agents  ·  /api/events  ·  /api/voting            │
│   /api/blockchain  ·  /api/achievements  ·  /api/users   │
└──────────────────────────┬───────────────────────────────┘
                           │
┌──────────────────────────┼───────────────────────────────┐
│                     Service Layer                         │
│   AI Agent Framework (7 modules)                         │
│   Event Pipeline (7 components)                          │
│   Voting System (4 modules)                              │
│   Blockchain Integration (7 modules)                     │
└──────────────────────────┬───────────────────────────────┘
                           │
┌──────────────────────────┼───────────────────────────────┐
│                      Data Layer                           │
│   PostgreSQL 15  ·  Redis 7  ·  Solana / Ethereum        │
└──────────────────────────────────────────────────────────┘
```

The backend runs as a single FastAPI application with a lifespan manager that initializes the `SystemOrchestrator` singleton on startup and gracefully shuts it down on exit. Security headers middleware adds `X-Content-Type-Options`, `X-Frame-Options`, and `Referrer-Policy` to every response. CORS origins are loaded from the `CORS_ORIGINS` environment variable.

## Installation and Quick Start

### Prerequisites

- Docker and Docker Compose (recommended)
- Python 3.11+ (for local development)
- Node.js 18+ and pnpm (for frontend development)
- A Solana wallet (for blockchain features)

### Docker Deployment (Recommended)

```bash
# Clone the repository
git clone https://github.com/organvm-ii-poiesis/a-i-council--coliseum.git
cd a-i-council--coliseum

# Configure environment
cp .env.example .env
# Edit .env with your API keys (OpenAI, Anthropic, Solana RPC, etc.)

# Start all services
docker-compose up -d

# Access points:
#   Frontend:  http://localhost:3000
#   Backend:   http://localhost:8000
#   API Docs:  http://localhost:8000/docs
#   Health:    http://localhost:8000/health
```

Docker Compose orchestrates four containers: PostgreSQL 15 (primary storage), Redis 7 (cache and sessions), the FastAPI backend, and the Next.js frontend. Volumes persist database and cache data across restarts.

### Local Development

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (in a separate terminal)
cd frontend
pnpm install
pnpm dev
```

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://council_user:council_pass@postgres:5432/ai_council` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379` |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `http://localhost:3000` |
| `OPENAI_API_KEY` | OpenAI API access for agent LLM calls | — |
| `ANTHROPIC_API_KEY` | Anthropic API access for agent LLM calls | — |

## Working Examples

### Creating an Agent Council

```python
from backend.ai_agents.orchestrator import SystemOrchestrator
from backend.ai_agents.base_agent import AgentRole

# Initialize the singleton orchestrator
orchestrator = SystemOrchestrator()

# Create a diverse council
moderator = orchestrator.create_agent(AgentRole.MODERATOR)
debater_a = orchestrator.create_agent(AgentRole.DEBATER)
debater_b = orchestrator.create_agent(AgentRole.DEBATER)
analyst   = orchestrator.create_agent(AgentRole.ANALYST)
checker   = orchestrator.create_agent(AgentRole.FACT_CHECKER)

# Start the orchestration loop
await orchestrator.start()

# Inject a real-time event for deliberation
await orchestrator.broadcast_event(
    "Breaking: New climate policy framework announced at COP summit"
)
```

### Running a Viewer Vote

```python
from backend.voting.voting_engine import VotingEngine, VoteType

engine = VotingEngine()

# Create a session linked to the current council debate
session = engine.create_session(
    title="Should the council endorse the climate framework?",
    description="Vote on whether the AI council's analysis supports endorsement.",
    vote_type=VoteType.BINARY,
    options=["agree", "disagree"],
    duration_minutes=30,
    min_stake=10.0,       # Minimum 10 COUNCIL tokens to vote
    reward_pool=500.0     # 500 tokens distributed to participants
)

engine.start_session(session.session_id)

# Users cast votes (typically via the /api/voting endpoint)
engine.cast_vote(session.session_id, user_id="user_42", choice="agree",
                 weight=1.5, tokens_staked=25.0)

# Finalize and calculate results
results = engine.finalize_session(session.session_id)
# => {"yes": 1.5, "no": 0, "total_votes": 1, "winner": "yes", ...}
```

### Ingesting Events from External Sources

```python
from backend.event_pipeline.ingestion import EventIngestionSystem, EventSource

pipeline = EventIngestionSystem()

# Ingest a news event
event = await pipeline.ingest_event(
    source=EventSource.NEWS_API,
    raw_data={
        "title": "Major tech company announces open-source AI model",
        "description": "The model will be released under Apache 2.0 license.",
        "url": "https://example.com/article",
        "content": "Full article text...",
        "source": {"name": "TechNews"}
    }
)

# Batch ingest from RSS feeds
rss_items = [{"title": "...", "summary": "...", "link": "..."} for _ in range(10)]
normalized = await pipeline.batch_ingest(rss_items, EventSource.RSS_FEED)
```

## System Components in Depth

### AI Agent Framework

The agent framework consists of seven modules that together implement a complete multi-agent deliberation system:

| Module | File | Responsibility |
|--------|------|---------------|
| **Base Agent** | `base_agent.py` | Abstract base class defining the agent contract: `process_message()`, `make_decision()`, `generate_response()`. All agents inherit from `BaseAgent` and implement these three methods. State is managed through Pydantic's `AgentState` model. |
| **Communication** | `communication.py` | Asynchronous message routing with an `asyncio.Queue`. Supports direct messaging, broadcast, and topic-based pub/sub. Agents subscribe to topics; the protocol delivers messages only to relevant subscribers. |
| **Decision Engine** | `decision_engine.py` | Five voting strategies — binary (majority), multiple choice (plurality), ranked (Borda count variant), weighted (confidence-adjusted), and consensus (threshold-based). Decisions auto-finalize when the required vote count is met. |
| **NLP Module** | `nlp_module.py` | Text understanding pipeline for sentiment analysis, entity extraction, summarization, and topic classification. Used by agents to comprehend incoming events before forming positions. |
| **Knowledge Base** | `knowledge_base.py` | Structured storage with category indexing and search. Agents write findings to the shared knowledge base; other agents query it to inform their positions. Access is tracked for audit. |
| **Memory Manager** | `memory_manager.py` | Dual-store memory: short-term (FIFO, bounded) and long-term (TTL-based with LRU eviction). Each agent maintains its own memory; the orchestrator can inspect memory state for debugging. |
| **Coordination** | `coordination.py` | Task distribution and progress tracking. The coordinator assigns debate roles, manages turn-taking, and monitors whether agents have contributed to a decision before the deadline. |

Agents operate through seven roles defined in `AgentRole`: Moderator, Debater, Analyst, Fact Checker, Summarizer, Voter, and Observer. The `SystemOrchestrator` is a singleton that manages agent lifecycles, shares a common `KnowledgeBase` and `DecisionEngine` across all agents, and runs a main loop that detects silence and prompts agents to initiate new discussions.

### Event Pipeline

Seven components form a linear processing chain:

```
Ingestion → Classification → Prioritization → Routing → Processing → Storage → Notification
```

**Ingestion** normalizes events from eight source types (RSS, API, webhook, social media, news API, user submission, blockchain, internal). Each source has a registered handler that maps raw data into a `NormalizedEvent` with sanitized HTML fields (preventing XSS). **Classification** applies keyword matching and topic extraction to tag events. **Prioritization** scores events using category weights, recency boosts, and quality signals. **Routing** dispatches prioritized events to registered handlers — typically AI agents that will debate them. **Processing** enriches events with sentiment, named entities, and generated summaries. **Storage** indexes processed events for search and retrieval. **Notification** distributes alerts through a multi-channel subscription system.

The pipeline supports batch ingestion for high-throughput scenarios and automatic cleanup of events older than a configurable retention period.

### Blockchain Integration

Seven modules handle on-chain operations across Solana and Ethereum:

- **Chainlink VRF** (`chainlink_vrf.py`): Verifiable random function for provably fair council member selection. Each selection round generates a VRF request; the result determines which agents are seated.
- **Pyth Entropy** (`pyth_entropy.py`): Secondary entropy source combined with Chainlink VRF for enhanced randomness. Useful when a single entropy source is insufficient for high-stakes selections.
- **Solana Contracts** (`solana_contracts.py`): Smart contracts for council management, token operations, staking, and reward distribution on Solana's high-throughput network.
- **Ethereum Integration** (`ethereum_contracts.py`): Cross-chain ERC-20 token support and Ethereum-side governance functions.
- **Token Economics** (`token_economics.py`): The `COUNCIL` token (symbol: `COUNCIL`, 9 decimals, 1B total supply) with a 30% reward pool. Handles balances, transfers, staking, unstaking, and reward allocation. Voting rewards scale with participation ratio; council rewards scale with session count and performance score.
- **Staking** (`staking.py`): Position management with configurable lock periods. Staked tokens increase a user's vote weight and earn periodic rewards.
- **Rewards** (`rewards.py`): Claim management and batch distribution. Tracks individual reward history and aggregate distribution statistics.

### Viewer Voting and Gamification

The voting system operates independently from the agent decision engine, allowing viewers to express preferences in parallel with agent deliberations:

**Voting Engine** — Manages sessions with four vote types: binary (agree/disagree), multiple choice (plurality), ranked (Borda-count scoring), and rating (1-5 stars with weighted averaging). Each session has configurable duration, minimum stake requirements, and a reward pool distributed to participants after finalization.

**Gamification System** — Six-tier progression from Bronze to Legendary, with escalating benefits:

| Tier | Points Required | Vote Weight | Reward Multiplier | Key Unlocks |
|------|----------------|-------------|-------------------|-------------|
| Bronze | 0 | 1.0x | 1.0x | Basic voting, achievement tracking |
| Silver | 100 | 1.2x | 1.2x | Priority notifications |
| Gold | 500 | 1.5x | 1.5x | Custom avatar |
| Platinum | 1,500 | 2.0x | 2.0x | Exclusive events |
| Diamond | 5,000 | 3.0x | 3.0x | Council suggestion rights |
| Legendary | 15,000 | 5.0x | 5.0x | VIP badge, direct AI interaction |

Points accumulate through voting (10 pts), session attendance (25 pts), referrals (50 pts), and daily streaks (up to 100 bonus pts). Experience follows an exponential curve: each level requires `i * 100 + i^2 * 10` XP, making early progression fast and later levels meaningfully difficult.

**Achievements** — 13 unique achievements across six tiers, from "First Vote" (Bronze, 10 pts) to "Founding Member" (Legendary, 2,000 pts). Achievements track cumulative participation milestones and serve as both status markers and point accelerators.

## Theory Implemented from ORGAN-I

Council Coliseum operationalizes several theoretical constructs from [ORGAN-I (Theoria)](https://github.com/organvm-i-theoria), the epistemological and recursive-systems organ:

- **Recursive observation.** The `SystemOrchestrator`'s main loop — tick, observe silence, prompt speech — implements a minimal recursive observer pattern. The system watches itself for inactivity and self-corrects, echoing the recursive self-reference explored in [a-recursive-root](https://github.com/organvm-i-theoria/a-recursive-root).
- **Emergent consensus.** The decision engine's consensus strategy (configurable threshold, default 80%) does not force agreement. It detects whether agreement has emerged organically from agent interactions — a computational analog to the epistemological claim that knowledge is a property of collectives, not individuals.
- **Memory as identity.** Each agent's dual-store memory (short-term FIFO, long-term TTL) gives agents temporal continuity across debates. An agent that remembers previous positions can build on them, contradict them, or evolve — producing the kind of diachronic identity that pure stateless inference cannot.

The dependency flows strictly from ORGAN-I to ORGAN-II: theoretical frameworks inform creative implementation. Council Coliseum does not feed back into ORGAN-I; it *performs* what ORGAN-I theorizes.

## API Reference

The FastAPI backend auto-generates interactive documentation at `/docs` (Swagger UI) and `/redoc` (ReDoc). Key endpoint groups:

| Prefix | Router | Purpose |
|--------|--------|---------|
| `/api/agents` | `agents_router` | Agent CRUD, state inspection, activation/deactivation |
| `/api/events` | `events_router` | Event ingestion, retrieval, classification results |
| `/api/voting` | `voting_router` | Session management, vote casting, result retrieval |
| `/api/blockchain` | `blockchain_router` | Token operations, staking, VRF requests |
| `/api/achievements` | `achievements_router` | Achievement status, progress, unlock history |
| `/api/users` | `users_router` | User profiles, gamification stats, tier info |
| `/ws` | WebSocket | Real-time bidirectional updates for live streaming |
| `/health` | — | Service health check (`{"status": "healthy"}`) |

## Tech Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Backend | Python, FastAPI | 3.11+, 0.109 | Async API server with automatic OpenAPI docs |
| Frontend | TypeScript, Next.js | 5.x, 14 | Server-rendered React with Tailwind CSS and Framer Motion |
| Database | PostgreSQL | 15 | Primary relational storage with SQLAlchemy 2.0 ORM |
| Cache | Redis | 7 | Session management, caching, pub/sub |
| AI/ML | OpenAI, Anthropic, LangChain | — | LLM inference for agent reasoning and NLP |
| NLP | Transformers, PyTorch | — | Local text understanding (sentiment, entities, summarization) |
| Blockchain | Solana, Ethereum (Web3.py) | — | Smart contracts, token operations, VRF |
| Oracle | Chainlink VRF, Pyth Network | — | Verifiable randomness and entropy |
| Media | ElevenLabs, gTTS, Pillow | — | Text-to-speech and image generation for streams |
| Infrastructure | Docker, Docker Compose | — | Container orchestration for all services |
| Monitoring | Prometheus, Sentry | — | Metrics collection and error tracking |
| Testing | pytest, pytest-asyncio | — | Async-aware test suite with coverage reporting |

## Project Structure

```
a-i-council--coliseum/
├── backend/
│   ├── ai_agents/           # 7-module agent framework
│   │   ├── base_agent.py    #   Abstract base + AgentRole + AgentState
│   │   ├── agent.py         #   Concrete agent implementation
│   │   ├── communication.py #   Message routing and pub/sub
│   │   ├── coordination.py  #   Task distribution
│   │   ├── decision_engine.py # 5 voting strategies
│   │   ├── knowledge_base.py  # Shared knowledge storage
│   │   ├── memory_manager.py  # Short-term + long-term memory
│   │   ├── nlp_module.py    #   Text understanding pipeline
│   │   └── orchestrator.py  #   Singleton system orchestrator
│   ├── api/                 # FastAPI route handlers
│   │   ├── agents.py        #   Agent management endpoints
│   │   ├── events.py        #   Event pipeline endpoints
│   │   ├── voting.py        #   Voting session endpoints
│   │   ├── blockchain.py    #   Token/staking endpoints
│   │   ├── achievements.py  #   Achievement endpoints
│   │   ├── users.py         #   User profile endpoints
│   │   └── dependencies.py  #   Shared dependencies + orchestrator init
│   ├── blockchain/          # 7 blockchain modules
│   │   ├── chainlink_vrf.py #   Verifiable random functions
│   │   ├── pyth_entropy.py  #   Secondary entropy source
│   │   ├── solana_contracts.py # Solana smart contracts
│   │   ├── ethereum_contracts.py # Ethereum/ERC-20
│   │   ├── token_economics.py  # COUNCIL token management
│   │   ├── staking.py       #   Staking with lock periods
│   │   └── rewards.py       #   Reward distribution
│   ├── event_pipeline/      # 7-stage event processing
│   │   ├── ingestion.py     #   Multi-source normalization
│   │   ├── classification.py #  Topic and category tagging
│   │   ├── prioritization.py # Score-based ranking
│   │   ├── routing.py       #   Handler dispatch
│   │   ├── processing.py    #   Enrichment (sentiment, entities)
│   │   ├── storage.py       #   Indexed persistence
│   │   └── notification.py  #   Multi-channel alerts
│   ├── voting/              # Viewer participation
│   │   ├── voting_engine.py #   Session + vote management
│   │   ├── achievements.py  #   13 achievements, 6 tiers
│   │   ├── gamification.py  #   Points, levels, streaks
│   │   └── leaderboard.py   #   Rankings and filtering
│   ├── tests/               # pytest test suite
│   ├── main.py              # FastAPI app entry point
│   ├── requirements.txt     # Python dependencies (~40 packages)
│   └── Dockerfile
├── frontend/
│   ├── src/app/             # Next.js 14 app directory
│   │   ├── page.tsx         #   Landing page
│   │   ├── layout.tsx       #   Root layout
│   │   └── globals.css      #   Tailwind CSS imports
│   ├── package.json
│   ├── tailwind.config.js
│   └── Dockerfile
├── docs/
│   ├── ARCHITECTURE.md      # System architecture documentation
│   └── DEPLOYMENT.md        # Deployment guide
├── docker-compose.yml       # 4-service orchestration
├── .github/workflows/ci-cd.yml
├── CONTRIBUTING.md
├── ROADMAP.md
├── LICENSE                  # MIT
└── README.md
```

## Related Work

Within the organvm ecosystem:

- **[organvm-i-theoria/a-recursive-root](https://github.com/organvm-i-theoria/a-recursive-root)** — Recursive-systems theory that informs the self-observing orchestrator pattern
- **[organvm-ii-poiesis/metasystem-master](https://github.com/organvm-ii-poiesis/metasystem-master)** — Meta-systemic creative framework; sibling ORGAN-II project
- **[organvm-ii-poiesis/a-mavs-olevm](https://github.com/organvm-ii-poiesis/a-mavs-olevm)** — Multi-agent virtual systems; related multi-agent art project
- **[organvm-iv-taxis/agentic-titan](https://github.com/organvm-iv-taxis/agentic-titan)** — Orchestration infrastructure that could govern cross-organ agent deployments

External references:

- [AutoGen (Microsoft)](https://github.com/microsoft/autogen) — Multi-agent conversation framework
- [CrewAI](https://github.com/joaomdmoura/crewAI) — Role-based multi-agent orchestration
- [Chainlink VRF](https://docs.chain.link/vrf) — Verifiable randomness documentation
- [Solana Program Library](https://spl.solana.com/) — Token and governance program standards

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on code style, testing requirements, and the pull request process.

For substantial changes, please open an issue first to discuss the approach. The project uses GitHub Actions for CI/CD; all PRs must pass the test suite before merging.

## License

MIT License. See [LICENSE](LICENSE) for the full text.

## Author

**[@4444j99](https://github.com/4444j99)** — creator of the [organvm system](https://github.com/meta-organvm), an eight-organ creative-institutional architecture spanning theory, art, commerce, orchestration, public process, community, and distribution.

---

*AI Council Coliseum is part of [ORGAN-II: Poiesis](https://github.com/organvm-ii-poiesis) — the art and creative production organ. It transforms multi-agent deliberation from an engineering technique into a performative medium where artificial intelligence does not merely solve problems but dramatizes the collective act of thinking.*
