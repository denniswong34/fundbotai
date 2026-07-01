# 05 — Multi-LLM Ensemble Strategy

## 5.1 Concept: Different LLMs, Different Personalities

Each LLM model has inherent "character" — strengths and weaknesses that can be exploited for portfolio management:

| AI Manager | Model | Style | Best Market | Weakness |
|---|---|---|---|---|
| 🟢 **DeepSeek Trader** | `deepseek-v4-flash` | Data-driven, momentum-following | Trending/bull markets | Can miss reversals |
| 🔵 **GPT-4o Strategist** | `gpt-4o` | Balanced, fundamentals + technicals | Range-bound markets | Slower to react |
| 🟣 **Claude Analyst** | `claude-sonnet-4` | Conservative, quality-first | Bear/high-volatility markets | Misses rallies |
| 🟡 **Gemini Arbitrage** | `gemini-2.5-pro` | Event-driven, news-aware | News-driven markets | Over-trades |

## 5.2 Ensemble Methods

### Method A: Simple Average Ensemble

Each LLM proposes target weights independently. The final allocation is the average.

```
weights = {
    "AAPL": (25.4 + 22.0 + 20.0 + 18.0) / 4 = 21.35%
    "MSFT": (22.1 + 25.0 + 23.0 + 20.0) / 4 = 22.53%
    "AMZN": (18.7 + 15.0 + 20.0 + 25.0) / 4 = 19.68%
    ...
}
```

**Pros:** Simple, uncorrelated errors cancel out
**Cons:** Ignores skill differences

### Method B: Weighted Ensemble (by Track Record)

Each manager's vote is weighted by their historical Sharpe ratio.

```
total_sharpe = 1.52 + 1.23 + 0.95 + 0.72 = 4.42

weights = {
    "DeepSeek": 1.52 / 4.42 = 34.4%
    "GPT-4o":   1.23 / 4.42 = 27.8%
    "Claude":   0.95 / 4.42 = 21.5%
    "Gemini":   0.72 / 4.42 = 16.3%
}

final_AAPL = 25.4×0.344 + 22.0×0.278 + 20.0×0.215 + 18.0×0.163 = 22.1%
```

**Pros:** Rewards proven performers
**Cons:** Past ≠ future; can become concentrated

### Method C: Supervisor LLM (Hierarchical)

A fifth "Supervisor" LLM reviews all proposals and makes the final call.

```
┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐
│ DeepSeek   │  │ GPT-4o     │  │ Claude     │  │ Gemini     │
│ Proposal 1 │  │ Proposal 2 │  │ Proposal 3 │  │ Proposal 4 │
└─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
      └───────────────┴───────────────┴───────────────┘
                                  │
                                  ▼
                        ┌────────────────────┐
                        │  Supervisor LLM     │
                        │  (e.g. GPT-4o with  │
                        │   meta-prompt)      │
                        │                     │
                        │  "Review proposals  │
                        │   and pick the best │
                        │   or create a       │
                        │   consensus plan"   │
                        └────────────────────┘
                                  │
                                  ▼
                        ┌────────────────────┐
                        │  Final Decision     │
                        └────────────────────┘
```

**Pros:** Context-aware selection; can spot errors in other LLMs
**Cons:** More expensive; adds latency

### Method D: Dynamic Selection (Market-Regime Adaptive)

Pick the best-suited manager for the current market conditions.

```python
def select_manager(market_regime: str) -> str:
    """
    Select the best AI manager based on detected market regime.
    """
    selection_map = {
        "bull": "deepseek-v4-flash",    # momentum-following
        "bear": "claude-sonnet-4",      # conservative, defensive
        "range": "gpt-4o",              # balanced, mean-reversion
        "volatile": "claude-sonnet-4",  # risk-aversion
        "uncertain": "gpt-4o",          # balanced judgment
    }
    return selection_map.get(market_regime, "gpt-4o")
```

**Pros:** Optimal model-task fit, cost-efficient
**Cons:** Requires accurate regime detection

## 5.3 Implementation: AiDecisionLog

Every AI decision is recorded for audit and performance tracking:

```json
{
  "id": "dec_20260701_001",
  "ai_manager_id": 1,
  "timestamp": "2026-07-01T14:30:00Z",
  "market_regime": "bull",

  "data_snapshot": {
    "spy": 556.30,
    "vix": 14.32,
    "fed_rate": 5.50,
    "cpi_mom": 0.2,
    "sector_flows": { "tech": "+1.2%", "energy": "-0.5%" }
  },

  "rag_results_used": [
    "Fed officials hint at Sep rate cut (Bloomberg)",
    "NVDA CEO sells 50K shares (SEC)",
    "AAPL target raised to $250 (JP Morgan)"
  ],

  "reasoning": "Fed rate cut expectations rising, liquidity remains loose.\nTech sector capital inflows continue but NVDA insider selling is a warning.\nRecommend slight NVDA reduction to lock profits, increase AAPL and MSFT.",

  "target_allocation": {
    "AAPL": 27.0,
    "MSFT": 24.0,
    "AMZN": 18.0,
    "GOOGL": 18.0,
    "NVDA": 10.0,
    "CASH": 3.0
  },

  "trades_to_execute": [
    {"symbol": "NVDA", "side": "sell", "qty": 2, "reason": "Lock profits, insider selling signal"},
    {"symbol": "AAPL", "side": "buy", "qty": 5, "reason": "Analyst upgrade, rate-cut beneficiary"},
    {"symbol": "MSFT", "side": "buy", "qty": 3, "reason": "AI business growth continues"}
  ],

  "risk_assessment": {
    "var_95": 3500,
    "max_drawdown_estimate": 12.5,
    "concentration_risk": "low",
    "sector_risk": "tech_overweight"
  },

  "benchmark_analysis": {
    "expected_spy_return": "+1.5% (next month)",
    "expected_portfolio_return": "+2.1% (next month)",
    "confidence": "medium_high",
    "alpha_expected": "+0.6%"
  },

  "executed": true,
  "execution_result": {
    "orders_created": 3,
    "total_value_before": 152430.50,
    "total_value_after": 152430.50,
    "cash_used": 1230.50,
    "status": "submitted"
  }
}
```

## 5.4 SQLAlchemy Model

```python
class AiManager(Base):
    """Configuration for an AI fund manager."""
    __tablename__ = "ai_managers"

    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String(100), nullable=False)
    model_provider = Column(String(50), default="opencode-go")
    model_name = Column(String(100), nullable=False)
    api_base_url = Column(String(255))
    system_prompt = Column(Text)
    temperature = Column(DECIMAL(3, 2), default=Decimal("0.7"))
    max_tokens = Column(Integer, default=4000)
    assigned_portfolio_id = Column(Integer, ForeignKey("portfolios.id"))
    is_active = Column(Boolean, default=True)
    total_return_pct = Column(DECIMAL(7, 4), default=Decimal("0"))
    sharpe_ratio = Column(DECIMAL(7, 4), default=Decimal("0"))
    win_rate = Column(DECIMAL(5, 2), default=Decimal("0"))
    total_trades = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class AiDecisionLog(Base):
    """Record of every AI manager decision."""
    __tablename__ = "ai_decision_logs"

    id = Column(Integer, primary_key=True)
    ai_manager_id = Column(Integer, ForeignKey("ai_managers.id"))
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"))
    triggered_at = Column(DateTime, nullable=False)
    market_regime = Column(String(20))
    data_snapshot = Column(JSON)
    rag_results_used = Column(JSON)
    prompt_sent = Column(Text)
    raw_response = Column(Text)
    parsed_decision = Column(JSON)
    reasoning = Column(Text)
    risk_assessment = Column(JSON)
    benchmark_analysis = Column(JSON)
    portfolio_snapshot_before = Column(JSON)
    portfolio_snapshot_after = Column(JSON)
    orders_created = Column(Integer, default=0)
    execution_status = Column(String(20), default="pending")
    execution_error = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
```
