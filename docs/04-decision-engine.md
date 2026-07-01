# 04 — Decision Engine

## 4.1 Six-Step Decision Flow

```
Input (all data + client profile)
  │
  ▼
┌─────────────────────────────────────────────┐
│  Step 1: Market Regime Detection             │
│  ─────────────────────────                   │
│  LLM analyzes macro signals → classify state │
│                                             │
│  🟢 Bull (trending up)   → high exposure    │
│  🟡 Range (sideways)     → mean reversion   │
│  🔴 Bear (trending down) → defensive        │
│  🟣 Volatile (high VIX)  → hedge, reduce    │
│  ⚪ Uncertain (mixed)     → cash, wait       │
└─────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────┐
│  Step 2: Strategic Asset Allocation          │
│  ──────────────────────────                  │
│  Decide: Stocks% / Bonds% / Commodities%     │
│                                             │
│  Bull: Stocks 85%, Commodities 10%, Cash 5% │
│  Bear: Stocks 40%, Bonds 30%, Gold 15%...  │
└─────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────┐
│  Step 3: Sector Allocation                   │
│  ──────────────────                          │
│  Assign sector weights based on cycle phase  │
│                                             │
│  Early cycle: Tech, Consumer Disc            │
│  Mid cycle:   Industrials, Energy            │
│  Late cycle:  Healthcare, Utilities          │
│  Recession:   Staples, Healthcare            │
└─────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────┐
│  Step 4: Security Selection                  │
│  ──────────────────                          │
│  Score candidate stocks on 4 dimensions:     │
│                                             │
│  • Technical (40%): RSI, MACD, SMA, Volume  │
│  • Fundamental (30%): PE, Growth, Margin    │
│  • Sentiment (20%): News, Social, Insider   │
│  • Risk (10%): Beta, Volatility, Drawdown   │
│                                             │
│  → Select Top 5-15 holdings                 │
└─────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────┐
│  Step 5: Weighting & Risk Check              │
│  ──────────────────────────                  │
│  1. Weight by score                          │
│  2. Check concentration limits               │
│  3. Calculate Portfolio VaR                  │
│  4. Stress test (if rates +2%?)             │
│  5. Adjust to client risk tolerance          │
└─────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────┐
│  Step 6: Structured Output                   │
│  ────────────────                             │
│  JSON decision with:                          │
│  • market_regime                              │
│  • reasoning                                  │
│  • target_allocation                          │
│  • trades_to_execute                          │
│  • risk_report                                │
│  • benchmark_analysis                         │
└─────────────────────────────────────────────┘
```

## 4.2 Scoring Formula

```
Score = w1 × Technical + w2 × Fundamental + w3 × Sentiment + w4 × Risk

Where:
Technical   = 0.25×RSI_Score + 0.25×MACD_Score + 0.25×SMA_Score + 0.25×Volume_Score
Fundamental = 0.3×PE_Score + 0.3×Growth_Score + 0.2×Margin_Score + 0.2×ROE_Score
Sentiment   = 0.5×News_Score + 0.3×Social_Score + 0.2×Insider_Score
Risk        = 0.4×Beta_Score + 0.3×Volatility_Score + 0.3×Drawdown_Score

Dynamic weights by market regime:
- Bull:   w1=0.4, w2=0.3, w3=0.2, w4=0.1  (momentum-driven)
- Bear:   w1=0.2, w2=0.3, w3=0.1, w4=0.4  (risk-aversion)
- Range:  w1=0.3, w2=0.3, w3=0.2, w4=0.2  (balanced)
- Volatile: w1=0.2, w2=0.2, w3=0.1, w4=0.5 (capital preservation)
```

## 4.3 Prompt Template

### System Prompt (base personality)

```
You are a professional AI portfolio manager named [Manager Name].
Your style: [style description, e.g. "data-driven momentum investor"]

Your mission: Manage client portfolios with the goal of consistently
beating the SPY (S&P 500 ETF) benchmark return.

Core principles:
1. Risk management > return chasing
2. Diversification is the only free lunch
3. Don't predict — weigh probabilities
4. Discipline > gut feeling
5. Every decision must include reasoning

Behavioral constraints:
- No single stock > [max_single_stock]% of portfolio
- No single sector > [max_sector]% of portfolio
- Max drawdown capped at [max_drawdown]%
- No unauthorized leverage or derivatives

Output format: You MUST respond in JSON only:
{
  "action": "rebalance|hold|add|remove",
  "reasoning": "detailed market analysis and decision logic",
  "risk_assessment": "current risk evaluation",
  "target_weights": { "SYMBOL": weight_pct, ... },
  "new_holdings": [ { "symbol": "...", "target_weight": N } ],
  "benchmark_analysis": "SPY comparison analysis"
}
```

### Daily Decision Prompt (injected each cycle)

```
━━━ AI Fund Manager Decision #<ID> ━━━
Time: 2026-07-01 14:30 UTC

━━━ Live Market Data ━━━
SPY: $556.30 (+0.45%) | QQQ: $485.20 (+0.82%)
VIX: 14.32 (+1.2%) | DXY: 105.8 | 10Y Yield: 4.32%
GLD: $2,350 | BTC: $68,450 | WTI: $79.50

━━━ Macro Environment ━━━
CPI MoM: +0.2% (exp +0.3%, below exp ✅)
Fed Funds Rate: 5.25-5.50% (next FOMC: Jul 30)
Non-Farm Payrolls: 272K (exp 185K, above exp ❗)
Unemployment: 4.0%
M2 YoY: +2.1% (liquidity still expanding)

━━━ Sector Rotation ━━━
📈 Leading: Tech (+1.2%), Consumer Disc (+0.8%)
📉 Lagging: Energy (-0.5%), Utilities (-0.3%)
Capital flows: Defensive → Cyclical rotation

━━━ Technical Indicators ━━━
SPY SMA50: $548.20 | SMA200: $532.10 → Golden Cross ✅
RSI(14): 62 (neutral-bullish)
MACD: Positive, momentum up
Put/Call Ratio: 0.85 (bullish bias)

━━━ Market Sentiment ━━━
WSB Hottest: NVDA, TSLA, GME (retail bullish)
Fear & Greed: 72 (Greed)
Insider Trading: Tech insider selling increasing (⚠️)

━━━ RAG Retrieval Results ━━━
📰 "Fed officials hint at possible Sep rate cut" (Bloomberg, 2h ago)
📰 "NVDA CEO sells 50K shares" (SEC Filing, 1d ago)
📰 "AAPL target raised to $250 by JP Morgan" (CNBC, 3h ago)
📈 Similar historical period: Jul 2019 (rate cut expectations + soft landing)
    → SPY next 3 months: +6.2%

━━━ Client Portfolio Status ━━━

Client: [Name] | Risk Score: 68/100 | Style: Moderate-Aggressive

Current Value: $152,430.50 | Cash: $2,430.50 (1.6%)
YTD Return: +13.7% | SPY YTD: +11.2% | Alpha: +2.5%
Max Drawdown: -8.5% | Limit: -25%

Positions:
┌────────┬────────┬────────┬────────┬────────┬────────┐
│ Symbol │ Weight │ Target │ Current│ P&L %  │ Drift  │
├────────┼────────┼────────┼────────┼────────┼────────┤
│ AAPL   │ 25.4%  │ 25.0%  │$198.50 │ +13.2% │ +0.4%  │
│ MSFT   │ 22.1%  │ 20.0%  │$425.30 │ +11.8% │ +2.1%  │
│ AMZN   │ 18.7%  │ 20.0%  │$178.70 │  +2.1% │ -1.3%  │
│ GOOGL  │ 20.3%  │ 20.0%  │$153.20 │  +5.1% │ +0.3%  │
│ NVDA   │ 13.5%  │ 15.0%  │$198.50 │ +76.4% │ -1.5%  │
└────────┴────────┴────────┴────────┴────────┴────────┘

━━━ Previous Decision Review ━━━
7 days ago: "Bullish on AI sector, increase NVDA to 15%"
Result ✅ NVDA +8.2% vs SPY +1.5%
Decision quality: Good (beat benchmark)

━━━ Please make your investment decision for this cycle ━━━
```

## 4.4 Structured Output Parsing

```python
from pydantic import BaseModel
from typing import Literal


class TradeAction(BaseModel):
    symbol: str
    side: Literal["buy", "sell"]
    qty: int
    reason: str


class DecisionOutput(BaseModel):
    """Validated LLM decision output."""

    action: Literal["rebalance", "hold", "add", "remove"]
    reasoning: str
    risk_assessment: str
    target_weights: dict[str, float]
    new_holdings: list[dict] | None = None
    trades_to_execute: list[TradeAction] | None = None
    benchmark_analysis: str

    @validator("target_weights")
    def weights_sum_to_100(cls, v):
        total = sum(v.values())
        if abs(total - 100.0) > 5.0:  # Allow small rounding errors
            raise ValueError(f"Target weights sum to {total:.1f}%, expected ~100%")
        return v

    @validator("trades_to_execute")
    def validate_trades(cls, v, values):
        if v and values.get("action") == "hold":
            raise ValueError("Cannot have trades when action is 'hold'")
        return v
```
