# 03 — LLM Inputs & RAG Architecture

## 3.1 Three-Layer Data Architecture

```
┌────────────────────────────────────────────────────────────┐
│                    LLM Fund Manager                         │
│                                                             │
│  ┌─────────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Context Window  │  │  RAG Retrieval│  │  Real-time API  │  │
│  │  (Always Injected)│  │  (On-Demand) │  │  (Every Cycle) │  │
│  ├─────────────────┤  ├──────────────┤  ├───────────────┤  │
│  │ • Client profile │  │ • News       │  │ • Live prices  │  │
│  │ • Portfolio state│  │ • Earnings   │  │ • VIX          │  │
│  │ • Positions      │  │ • Analyst    │  │ • FX rates     │  │
│  │ • Risk limits    │  │   reports    │  │ • Sector flows │  │
│  │ • Last decision  │  │ • Macro DB   │  │ • Order status │  │
│  └─────────────────┘  └──────────────┘  └───────────────┘  │
└────────────────────────────────────────────────────────────┘
```

## 3.2 Complete Data Input Catalog

### A. Macroeconomic Indicators

| Data | Update Frequency | Source | Purpose |
|---|---|---|---|
| Fed Funds Rate | Every 6 weeks (FOMC) | FRED API | Rate direction, cost of capital |
| CPI / Core CPI | Monthly | BLS | Inflation trend |
| PPI | Monthly | BLS | Production cost pressure |
| Non-Farm Payrolls | Monthly | BLS | Labor market health |
| Unemployment Rate | Monthly | BLS | Economic cycle position |
| GDP Growth | Quarterly | BEA | Economic growth momentum |
| 10Y-2Y Treasury Spread | Daily | Treasury | Recession warning |
| US Dollar Index (DXY) | Real-time | Forex | USD strength |
| VIX | Real-time | CBOE | Market fear/greed |
| M2 Money Supply | Monthly | FRED | Market liquidity |

### B. Technical Indicators

| Indicator | Period | Purpose |
|---|---|---|
| S&P 500 (SPY) | 1d/1w/1m/1y | Primary benchmark |
| NASDAQ (QQQ) | 1d/1w/1m | Growth stock gauge |
| Russell 2000 (IWM) | 1d/1w/1m | Small-cap health |
| SMA 50/200 | Cross-period | Trend direction (golden/death cross) |
| RSI (14) | Cross-period | Overbought/oversold |
| MACD | Cross-period | Momentum turning points |
| Bollinger Bands | Cross-period | Volatility channel |
| Put/Call Ratio | Daily | Market sentiment |
| Advance/Decline Line | Daily | Market breadth |

### C. Commodities & Hedge Assets

| Asset | Purpose |
|---|---|
| Gold (GLD/XAU) | Hedge, inflation hedge |
| Silver (SLV/XAG) | Industrial + hedge |
| Crude Oil (WTI/CL) | Inflation input, energy cost |
| Copper (HG) | Economic leading indicator |
| Bitcoin (BTC) | Digital gold, risk appetite |
| US Treasuries (TLT) | Risk-off, rate sensitivity |

### D. Market Sentiment

| Source | Type | Tool |
|---|---|---|
| Reddit WallStreetBets | Retail sentiment | Reddit API + NLP |
| Twitter/X Financial Tweets | Social sentiment | Twitter API v2 |
| CNN Fear & Greed Index | Composite sentiment | Web scrape |
| AAII Sentiment Survey | Retail survey | AAII API |
| Insider Trading | Corporate insider | SEC EDGAR |
| Short Interest | Short data | Financial Modeling Prep |
| Options Flow | Large options | MarketBeat / Barchart |

### E. Sector Rotation Data

```
Sector Rotation Matrix:

  Capital flows →  Leading sector  →  Momentum sector →  Lagging sector
  ─────────────────────────────────────────────────────────────────────
  Early Cycle  │  Tech, Consumer Disc│  Financials, Industrials│  Energy, Materials
  Mid Cycle    │  Financials, Indust.│  Energy, Materials      │  Tech
  Late Cycle   │  Energy, Materials  │  Healthcare, Utilities  │  Financials
  Recession    │  Healthcare, Util.  │  Consumer Staples       │  All risk assets
```

**Sector ETFs tracked daily:**

| Ticker | Sector |
|---|---|
| XLK | Technology |
| XLF | Financials |
| XLV | Healthcare |
| XLE | Energy |
| XLI | Industrials |
| XLP | Consumer Staples |
| XLY | Consumer Discretionary |
| XLU | Utilities |
| XLB | Materials |
| XLRE | Real Estate |

### F. Portfolio-Specific Data

```json
{
  "portfolio_id": 1,
  "total_value": 152430.50,
  "cash": 2430.50,
  "positions": [
    {"symbol": "AAPL", "shares": 50, "avg_cost": 175.30, "current": 198.50, "weight": 25.4},
    {"symbol": "MSFT", "shares": 30, "avg_cost": 380.20, "current": 425.30, "weight": 22.1},
    {"symbol": "AMZN", "shares": 40, "avg_cost": 175.00, "current": 178.70, "weight": 18.7}
  ],
  "performance": {
    "day_pnl": 1230.50,
    "week_pnl": 4500.00,
    "month_pnl": -2300.00,
    "total_pnl": 18350.00,
    "total_return_pct": 13.7,
    "max_drawdown": 8.5,
    "sharpe_ratio": 1.32,
    "var_95": 3200.00
  },
  "benchmark_comparison": {
    "spy_return_pct": 11.2,
    "portfolio_return_pct": 13.7,
    "alpha": 2.5,
    "beta": 1.15,
    "tracking_error": 5.2
  }
}
```

## 3.3 RAG Pipeline Architecture

```
                    RAG Pipeline

Data Ingestion Layer
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ News API │ │SEC EDGAR│ │FRED API │ │ Reddit   │
└────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
     │            │            │            │
     ▼            ▼            ▼            ▼
┌──────────────────────────────────────────────────────┐
│                 ETL Pipeline (Cron / Airflow)         │
│  • Clean  • Normalize  • Chunk  • Embed              │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│              Vector Database (Qdrant / PGVector)      │
│  Collections: news, earnings, macro, sentiment        │
│  Embedding Model: text-embedding-3-large / BGE-M3    │
└──────────────────────┬───────────────────────────────┘
                       │
Retrieval Layer        │
┌──────────────────────▼───────────────────────────────┐
│  RAG Retrieval Strategies                             │
│                                                       │
│  1. Structured Query:                                  │
│     "最近 Fed 會議對利率的指引是什麼？"                   │
│     → Search macro collection for latest FOMC minutes │
│                                                       │
│  2. Time-Aware Retrieval:                              │
│     "AAPL 上季財報的 EPS 和 Revenue 是多少？"            │
│     → Search earnings collection for AAPL latest 10-Q │
│                                                       │
│  3. Sentiment Retrieval:                               │
│     "市場目前對 NVDA 的看法如何？"                       │
│     → Search sentiment collection for recent NVDA     │
│                                                       │
│  4. Similar Event Retrieval:                           │
│     "歷史上類似宏觀環境時，市場如何表現？"                │
│     → Search for similar macro regimes in history     │
└──────────────────────────┬────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────┐
│  Result Compression & Reranking                       │
│  • Cohere Rerank / BGE-Reranker                      │
│  • Top-K = 5-10 most relevant                         │
│  • Recency-weighted scoring                           │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│  Final Prompt Assembly                                 │
│                                                       │
│  System Prompt (personality + rules)                  │
│  + Client Profile (risk score + constraints)          │
│  + Portfolio State (holdings + performance)           │
│  + RAG Results (news + macro + sentiment context)     │
│  + Real-time Data (quotes + VIX + FX)                 │
│  + Risk Limits (max drawdown, concentration)          │
│  + Previous Decisions (last action + outcome)         │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
              ┌──────────────────────┐
              │   LLM Inference      │
              │  (opencode-go API)   │
              └──────────────────────┘
```

## 3.4 LLM Gateway Implementation

```python
class LLMGateway:
    """
    OpenAI-compatible API wrapper for the opencode-go gateway.

    Allows routing to different LLM models through a single endpoint.
    """

    def __init__(self, api_base: str, api_key: str):
        self.api_base = api_base
        self.api_key = api_key
        self.client = OpenAI(
            base_url=api_base,
            api_key=api_key,
        )

    async def generate_decision(
        self,
        model: str,            # e.g. "deepseek-v4-flash", "gpt-4o"
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> dict:
        """
        Call LLM and parse structured decision output.
        Uses response_format to enforce JSON output.
        """
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        return json.loads(raw)

    async def generate_with_fallback(
        self,
        primary_model: str,
        fallback_model: str,
        messages: list[dict],
    ) -> dict:
        """
        Try primary model first, fall back if it fails.
        """
        try:
            return await self.generate_decision(primary_model, messages)
        except Exception as e:
            logger.warning(f"Primary model {primary_model} failed: {e}")
            return await self.generate_decision(fallback_model, messages)
```
