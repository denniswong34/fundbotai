# 09 — Implementation Roadmap

## Phase Overview

| Phase | Content | Est. Hours | Dependencies |
|---|---|---|---|
| **P1** | AiManager model + CRUD API + DB migration | 4h | None |
| **P2** | Arena frontend page (leaderboard + cards) | 8h | P1 |
| **P3** | LLM Gateway + decision engine | 8h | P1 |
| **P4** | Decision scheduling (cron/APScheduler) | 4h | P3 |
| **P5** | Client questionnaire + risk profiling | 4h | P1 |
| **P6** | RAG pipeline (ETL + vector DB) | 12h | P3 |
| **P7** | Data source integration (macro, sentiment) | 8h | P6 |
| **P8** | Performance evaluation + leaderboard logic | 4h | P4 |
| **P9** | Client reports + notifications | 4h | P8 |
| **P10**| Auto-rebalance + risk enforcement | 4h | P3 |

**Total: ~60 hours** (deliverable across 4-6 weeks)

---

## P1 — AiManager Model + CRUD API (4h)

### Backend

**New files:**
- `backend/app/models/ai_manager.py` — AiManager + AiDecisionLog models
- `backend/app/services/arena_service.py` — ArenaService class
- `backend/app/routers/ai_managers.py` — CRUD + decision trigger
- `backend/app/schemas/ai_manager.py` — Pydantic schemas

**Database migration:**
```sql
CREATE TABLE ai_managers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    org_id INT NOT NULL,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    model_provider VARCHAR(50) DEFAULT 'opencode-go',
    model_name VARCHAR(100) NOT NULL,
    api_base_url VARCHAR(255),
    system_prompt TEXT,
    temperature DECIMAL(3,2) DEFAULT 0.70,
    max_tokens INT DEFAULT 4000,
    assigned_portfolio_id INT,
    is_active BOOLEAN DEFAULT TRUE,
    total_return_pct DECIMAL(7,4) DEFAULT 0,
    sharpe_ratio DECIMAL(7,4) DEFAULT 0,
    win_rate DECIMAL(5,2) DEFAULT 0,
    total_trades INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (org_id) REFERENCES organizations(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (assigned_portfolio_id) REFERENCES portfolios(id)
);

CREATE TABLE ai_decision_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ai_manager_id INT NOT NULL,
    portfolio_id INT,
    triggered_at DATETIME NOT NULL,
    market_regime VARCHAR(20),
    data_snapshot JSON,
    rag_results_used JSON,
    prompt_sent TEXT,
    raw_response TEXT,
    parsed_decision JSON,
    reasoning TEXT,
    risk_assessment JSON,
    benchmark_analysis JSON,
    portfolio_snapshot_before JSON,
    portfolio_snapshot_after JSON,
    orders_created INT DEFAULT 0,
    execution_status VARCHAR(20) DEFAULT 'pending',
    execution_error TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ai_manager_id) REFERENCES ai_managers(id),
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id)
);
```

### API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/ai-managers` | List AI managers |
| `POST` | `/api/ai-managers` | Create AI manager |
| `GET` | `/api/ai-managers/{id}` | Get details |
| `PUT` | `/api/ai-managers/{id}` | Update config |
| `DELETE` | `/api/ai-managers/{id}` | Remove |
| `POST` | `/api/ai-managers/{id}/trigger` | Manually trigger AI decision |
| `GET` | `/api/ai-managers/{id}/decisions` | Decision history |
| `GET` | `/api/ai-managers/leaderboard` | Performance ranking |
| `GET` | `/api/ai-managers/comparison-data` | Multi-series chart data |

---

## P2 — Arena Frontend Page (8h)

### New Files
- `frontend/src/views/arena/AiArenaPage.vue` — Main arena view
- `frontend/src/views/arena/AiManagerDetailPage.vue` — Detail view
- `frontend/src/components/arena/LeaderboardTable.vue` — Ranked table
- `frontend/src/components/arena/ComparisonChart.vue` — Multi-line ECharts
- `frontend/src/components/arena/AiManagerCard.vue` — Manager card
- `frontend/src/components/arena/AddAiManagerDialog.vue` — Create/edit dialog
- `frontend/src/components/arena/AiDecisionLog.vue` — Decision timeline
- `frontend/src/stores/arenaStore.js` — Arena state management
- `frontend/src/services/arenaApi.js` — Arena API service

### Route
```javascript
{
    path: '/arena',
    name: 'AiArena',
    component: AiArenaPage,
    meta: { requiresAuth: true },
}
```

### Frontend Layout

```
┌──────────────────────────────────────────────────────────────┐
│  🏆 AI Manager Arena                                        │
│  [Add AI Manager] [Run All] [Schedule Auto-Run]              │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  LEADERBOARD:                                                 │
│  ┌──────┬────────────┬──────────────┬───────┬──────┬──────┐  │
│  │ Rank │ AI Manager │ Model        │ Return│Sharpe│Score │  │
│  ├──────┼────────────┼──────────────┼───────┼──────┼──────┤  │
│  │ 🥇 1 │ DeepSeek   │ ds-v4-flash  │+18.2% │ 1.52 │ 85.3 │  │
│  │ 🥈 2 │ GPT-4o     │ gpt-4o       │+12.7% │ 1.23 │ 72.1 │  │
│  │ 🥉 3 │ Claude     │ claude-4     │ +8.5% │ 0.95 │ 61.8 │  │
│  │   4  │ Gemini     │ gemini-2.5   │ +5.1% │ 0.72 │ 50.4 │  │
│  └──────┴────────────┴──────────────┴───────┴──────┴──────┘  │
│                                                               │
│  COMPARISON CHART (multi-line equity curves):                  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  $180K ┤  ┌──DeepSeek──┐                               │  │
│  │  $170K ┤ ╱             ╲ GPT-4o                        │  │
│  │  $160K ┤╱               ╲───┐                          │  │
│  │  $150K ┤                  └──╲──Claude──┐              │  │
│  │  $140K ┤                      └─────────╲──Gemini──┐   │  │
│  │        └─────────────────────────────────────────────┘  │
│  │         Jun 1    Jun 8   Jun 15   Jun 22   Jun 29       │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

---

## P3 — LLM Gateway + Decision Engine (8h)

### New Files
- `backend/app/services/llm_gateway.py` — OpenAI-compatible wrapper
- `backend/app/services/decision_engine.py` — Decision generation + parsing

### Core Implementation

```python
class DecisionEngine:
    """
    Orchestrates the full AI decision cycle:
    1. Gather portfolio state + market data
    2. Retrieve RAG context
    3. Assemble prompt
    4. Call LLM via gateway
    5. Parse structured output
    6. Validate against risk limits
    7. Execute trades via PortfolioManager
    8. Log everything
    """

    async def run_decision_cycle(
        self, ai_manager_id: int
    ) -> dict:
        manager = await self._get_manager(ai_manager_id)
        portfolio = await self._get_portfolio(manager.assigned_portfolio_id)

        # 1. Gather data
        portfolio_state = await self._get_portfolio_state(portfolio)
        market_data = await self.data_cache.get_market_context()
        rag_context = await self.vector_retriever.query(
            query="recent market news and analysis",
            top_k=5,
        )

        # 2. Assemble prompt
        prompt = self._assemble_prompt(
            manager=manager,
            portfolio_state=portfolio_state,
            market_data=market_data,
            rag_context=rag_context,
        )

        # 3. Call LLM
        decision = await self.llm_gateway.generate_decision(
            model=manager.model_name,
            messages=[
                {"role": "system", "content": manager.system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=manager.temperature,
        )

        # 4. Parse & validate
        validated = DecisionOutput(**decision)
        is_safe, warnings = await self.risk_enforcer.validate_decision(
            portfolio, validated.target_weights
        )

        if not is_safe:
            logger.warning(f"Decision rejected by risk enforcer: {warnings}")
            return {"status": "rejected", "warnings": warnings}

        # 5. Execute trades
        if validated.action != "hold":
            orders = await self.portfolio_manager.execute_rebalance(
                portfolio.id, validated.target_weights
            )

        # 6. Log
        decision_log = AiDecisionLog(
            ai_manager_id=ai_manager_id,
            portfolio_id=portfolio.id,
            triggered_at=datetime.now(timezone.utc),
            market_regime=...,  # from market classifier
            data_snapshot=market_data,
            rag_results_used=rag_context,
            prompt_sent=prompt,
            raw_response=json.dumps(decision),
            parsed_decision=json.dumps(validated.dict()),
            ...
        )
        self.db.add(decision_log)
        await self.db.commit()

        return {"status": "executed", "orders_created": len(orders)}
```

---

## P4 — Decision Scheduling (4h)

```python
# Using APScheduler for scheduled AI decisions

async def setup_decision_scheduler():
    scheduler = AsyncIOScheduler()

    # Get all active AI managers with auto-run enabled
    managers = await db.execute(
        select(AiManager).where(
            AiManager.is_active == True,
            AiManager.auto_run_enabled == True,
        )
    )

    for manager in managers.scalars().all():
        # Schedule based on frequency
        if manager.run_frequency == "daily":
            scheduler.add_job(
                run_ai_decision,
                trigger="cron",
                hour=14,  # After market close
                minute=30,
                args=[manager.id],
                id=f"ai_decision_{manager.id}",
                replace_existing=True,
            )
        elif manager.run_frequency == "weekly":
            scheduler.add_job(
                run_ai_decision,
                trigger="cron",
                day_of_week="fri",
                hour=16,
                args=[manager.id],
            )

    scheduler.start()
```

---

## P5 — Client Questionnaire + Risk Profiling (4h)

### Files
- `frontend/src/components/arena/QuestionnaireWizard.vue` — Multi-step form
- `backend/app/routers/questionnaire.py` — Submit + generate profile
- `backend/app/services/risk_profiler.py` — Scoring logic

### Flow
```
1. User fills 20-question form (4 sections, 5 questions each)
2. POST /api/questionnaire/submit
3. Backend calculates risk_score (0-100)
4. LLM generates human-readable client profile
5. Profile stored in database, linked to user
6. Portfolio created with constraints from profile
7. AI Manager assigned to manage the portfolio
```

---

## P6 — RAG Pipeline (12h)

### Components

| Component | Tech | Hours |
|---|---|---|
| Vector DB setup (PGVector on MariaDB or Qdrant Docker) | PostgreSQL / Qdrant | 2h |
| Embedding service (OpenAI / BGE) | sentence-transformers | 2h |
| News ETL (fetch → chunk → embed → store) | Custom cron | 3h |
| SEC Filings ETL | sec-edgar-api | 2h |
| Macro data ETL | FRED API | 1h |
| RAG retrieval service | pgvector similarity search | 2h |

---

## P7-P10 — Remaining Phases

### P7: Data Source Integration (8h)
- Financial Modeling Prep API integration (quotes, fundamentals)
- Yahoo Finance historical data
- Reddit/Twitter sentiment pipeline
- FRED macro indicator pipeline

### P8: Performance Evaluation (4h)
- PerformanceCalculator integration
- Leaderboard computation on schedule
- Comparison chart data endpoint

### P9: Client Reports (4h)
- Weekly AI manager report generation
- Email/notification delivery
- Performance dashboard

### P10: Auto-Rebalance + Risk Enforcer (4h)
- Cron-based auto-trigger
- Risk limit hard enforcement
- Override/circuit-breaker for extreme decisions

---

## Risk & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| LLM hallucinates data | Medium | High | Validate all LLM outputs with structured parsing |
| API rate limits | High | Medium | Implement queue + backoff; cache aggressively |
| Vector DB too slow | Low | Medium | Use Redis for real-time; vector DB for background |
| LLM cost too high | Medium | Medium | Cache similar queries; use cheaper models for simple tasks |
| Market regime misclassification | Medium | High | Ensemble approach; don't rely on single LLM |
| User trust issues | Medium | High | Transparent decision logs; paper-trading first |
