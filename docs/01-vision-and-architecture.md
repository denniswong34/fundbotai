# 01 — Vision and Architecture

## 1.1 Product Vision

FundBot AI transforms from a portfolio rebalancing tool into a **competitive AI fund manager platform**. Each portfolio is managed by a different LLM "AI Manager" (DeepSeek, GPT-4o, Claude, etc.). Users create, monitor, and compare AI-managed portfolios side-by-side on a live leaderboard.

**Core promise**: Let AI fight AI — the best manager wins.

## 1.2 Key Stakeholders

| Role | Needs |
|---|---|
| **Retail Investor** | Simple way to get AI-managed portfolio that beats SPY |
| **Power User** | Compare multiple AI strategies, switch between managers |
| **Platform Admin** | Monitor AI decision quality, override if needed |
| **Developer** | Add new AI models, custom strategies, data sources |

## 1.3 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                               Frontend (Vue 3 + Vuetify 3)                  │
│  ┌──────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐  │
│  │ Arena     │ │ Portfolio    │ │ Questionnaire│ │ Performance           │  │
│  │ Page      │ │ Page         │ │ (KYC Form)   │ │ Dashboard             │  │
│  │ Leaderboard│ │ Holdings     │ │              │ │ Equity Curves         │  │
│  │ Rankings  │ │ Orders/Trades│ │              │ │ Benchmark Comparison  │  │
│  └──────────┘ └──────────────┘ └──────────────┘ └──────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────────────────┘
                           │ REST API / WebSocket
                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend (Python 3.11)                       │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ ArenaService │  │ Portfolio-   │  │ LLM Gateway  │  │ DataPipeline │   │
│  │              │  │ Manager      │  │ (opencode-go)│  │              │   │
│  │ • Client     │  │ • Portfolio  │  │ • Multi-LLM  │  │ • ETL       │   │
│  │   Profiling  │  │   CRUD       │  │   routing    │  │ • Vector     │   │
│  │ • AI Decision│  │ • Rebalance  │  │ • Fallback   │  │   embedding  │   │
│  │   Engine     │  │ • Order Exec │  │ • Rate limit │  │ • Scheduler  │   │
│  │ • Performance│  │ • Broker Sync│  │ • Structured │  │ • Cache      │   │
│  │   Tracking   │  │              │  │   output     │  │              │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
└──────────────────────────┬──────────────────────────────────────────────────┘
                           │
         ┌─────────────────┼────────────────────┐
         ▼                 ▼                    ▼
┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐
│  MariaDB     │  │  Redis       │  │  Vector Database     │
│  (Primary DB)│  │  (Cache/Q)   │  │  (Qdrant/PGVector)   │
│              │  │              │  │                      │
│ • portfolios │  │ • Live Quotes│  │ • News embeddings    │
│ • orders     │  │ • Sessions   │  │ • Earnings data      │
│ • holdings   │  │ • Rate Limits│  │ • Market analysis    │
│ • ai_managers│  │ • Job Queue  │  │ • Historical patterns│
│ • ai_decisions│  │              │  │                      │
└──────────────┘  └──────────────┘  └─────────────────────┘
```

## 1.4 Component Relationships

```
┌──────────────┐     manages      ┌──────────────┐
│  AiManager   │ ────────────────▶ │   Portfolio   │
│  (LLM Config)│                   │  (Target Wts) │
└──────┬───────┘                   └──────┬───────┘
       │                                  │
       │ generates                        │ contains
       ▼                                  ▼
┌──────────────┐                   ┌──────────────┐
│ AiDecisionLog│                   │  Holdings    │
│ (Decisions)  │                   │  (Positions) │
└──────┬───────┘                   └──────┬───────┘
       │                                  │
       │ triggers                         │ rebalances
       ▼                                  ▼
┌──────────────┐                   ┌──────────────┐
│  Rebalance   │                   │  Orders      │
│  (Execution) │                   │  (Trades)    │
└──────────────┘                   └──────────────┘
```

## 1.5 Data Flow

```
Daily AI Decision Cycle:

  1. Cron trigger → ArenaService
  2. ArenaService loads AiManager config
  3. ArenaService fetches portfolio state + market data
  4. RAG pipeline retrieves relevant context (news, macro, sentiment)
  5. LLM Gateway calls opencode-go with structured prompt
  6. LLM returns JSON decision (target weights, trades, reasoning)
  7. ArenaService parses and validates the decision
  8. Risk checks pass/fail → execute or hold
  9. PortfolioManager executes trades via broker adapter
  10. AiDecisionLog records everything
  11. Performance snapshots updated
```

## 1.6 Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Vue 3 + Vuetify 3 + ECharts + Vite |
| Backend | FastAPI (Python 3.11) + uvicorn |
| Database | MariaDB 10.6+ |
| Cache | Redis (docker) |
| Vector DB | PGVector (PostgreSQL extension) or Qdrant |
| LLM Gateway | opencode-go (OpenAI-compatible) |
| Task Scheduler | APScheduler / cron |
| Data Pipeline | Apache Airflow or custom Python + cron |
| Embeddings | text-embedding-3-small / BGE-M3 |
