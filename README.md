# FundBot AI — Unified Fund Management Trading App

> **AI-powered, multi-broker, multi-market unified fund management with automated trading bot.**
> Built with the same architecture and design language as LeanPortal.

## Vision

FundBot AI lets you manage all your investment portfolios across multiple brokers and markets from a single dashboard. Create target-weight portfolios, auto-rebalance with AI-powered trading bots, track performance over time, and get drift alerts — all through a beautiful dark-themed web app and Android companion.

## Key Features

- **AI-Powered Trading Bot** — Auto-manage your funds with intelligent rebalancing
- **Multi-Portfolio Management** — Create multiple named portfolios (e.g. "Retirement", "Growth", "Dividend Income")
- **Multi-Broker Support** — Connect Webull HK, Futu, Tiger Brokers, Interactive Brokers, Alpaca, Paper Trading (more via broker adapter pattern)
- **Multi-Market & Multi-Currency** — US stocks, HK stocks, China A-shares, Japan, Crypto — all currencies normalized
- **Target-Weight Rebalancing** — Set target % for each holding, one-click rebalance, auto-detect drift
- **Auto-Rebalance Cron** — Detects drift > threshold and alerts/executes automatically via trading bot
- **Configurable Trading Bot** — Market or limit orders, cash reserve %, drift threshold, frequency — all configurable
- **Multi-Account Broker Support** — Select sub-account for brokers with multiple accounts (IB, etc.)
- **Performance Tracking** — Daily snapshots, P&L charts, allocation pie charts
- **Dark Theme UI** — Premium glassmorphism design with purple/cyan gradients (same design system as LeanPortal)
- **Android App** — Companion mobile app for portfolio management on the go
- **Webull MCP Server Ready** — AI-assistant integration for natural language trading

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Android App (Flutter)                   │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS + JWT
┌──────────────────────▼──────────────────────────────────┐
│              FundBot AI Backend (FastAPI)                 │
│                                                          │
│  ┌────────────────┐  ┌──────────────────────────────┐   │
│  │ Portfolio Mgr  │  │ Broker Adapter Interface     │   │
│  │ (rebalance)    │  │  ├─ Webull HK                │   │
│  │ (performance)  │  │  ├─ Futu                     │   │
│  │ (trading bot)  │  │  ├─ Tiger                    │   │
│  └────────────────┘  │  ├─ Interactive Brokers      │   │
│                       │  ├─ Alpaca                   │   │
│  ┌────────────────┐  │  ├─ Paper Trading            │   │
│  │ Auth (JWT)     │  │  └─ CCXT (crypto)            │   │
│  └────────────────┘  └──────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                   MariaDB                                │
│  users | broker_connections | portfolios                 │
│  portfolio_holdings | rebalance_orders                   │
│  performance_snapshots | notifications                   │
└─────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy (async), Pydantic v2 |
| **Frontend** | Vue 3 + Composition API, Vuetify 3, Pinia, Vue Router, ECharts |
| **Database** | MariaDB 10.11 |
| **Auth** | JWT (access + refresh tokens), bcrypt |
| **Infra** | Docker Compose, Nginx reverse proxy |
| **Broker APIs** | Webull OpenAPI, Futu OpenD, Tiger OpenAPI, IB API, CCXT |
| **Mobile** | Flutter (Android) |

## Project Structure

```
fundbotai/
├── backend/
│   ├── app/
│   │   ├── models/           # SQLAlchemy models
│   │   ├── routers/          # FastAPI route handlers
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # Business logic
│   │   │   ├── brokers/      # Broker adapters (Webull, Futu, Tiger, IB, etc.)
│   │   │   └── data_providers/ # Market data providers
│   │   ├── middleware/       # Auth middleware
│   │   ├── config.py
│   │   ├── database.py
│   │   └── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/             # Axios API client
│   │   ├── components/      # Reusable Vue components
│   │   ├── pages/           # Page-level components
│   │   ├── router/          # Vue Router config
│   │   ├── services/        # API service modules
│   │   ├── stores/          # Pinia stores
│   │   └── views/           # View pages
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── vite.config.js
├── database/
│   └── init/01_schema.sql   # DB initialization
├── scripts/                 # Utility scripts
├── docs/                    # Documentation
├── docker-compose.yml
└── README.md
```

## Getting Started

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USER/fundbotai.git
cd fundbotai

# 2. Set up environment
cp backend/.env.example backend/.env
# Edit backend/.env with your config

# 3. Start with Docker
docker compose up -d

# 4. Access the app
# Web UI: http://localhost:8081
# API:    http://localhost:8000
# API docs: http://localhost:8000/docs
```

## Design System

FundBot AI uses the same design system as LeanPortal:
- **Dark theme** with purple/cyan gradients
- **Glassmorphism** cards and panels
- **Cyber grid** background animations
- **Professional trading UI** patterns
- **Responsive** — desktop web + mobile web + Android app

## Related Projects

- **[LeanPortal](https://github.com/denniswong34/lean-portal)** — Self-hosted algo trading platform (LEAN Engine + FastAPI + Vue)
- **[FundBot AI](https://github.com/denniswong34/fundbotai)** — AI-Powered Unified Fund Management Trading App
