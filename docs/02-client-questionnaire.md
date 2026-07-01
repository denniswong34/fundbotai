# 02 — Client Questionnaire (KYC)

> Before designing a portfolio, the LLM must understand the client. This is the complete KYC (Know Your Client) questionnaire.

## 2.1 Personal Information

```
┌──────────────────────────────────────────────────────────┐
│  📋 Client Questionnaire — Part 1: Personal Info          │
├──────────────────────────────────────────────────────────┤
│  1. Age Range:                                            │
│     □ 18-25  □ 26-35  □ 36-45  □ 46-55  □ 56-65  □ 65+  │
│                                                          │
│  2. Annual Income (USD):                                   │
│     □ <50K  □ 50-100K  □ 100-250K  □ 250-500K  □ 500K+   │
│                                                          │
│  3. Total Investable Assets (excluding primary residence): │
│     □ <10K  □ 10-50K  □ 50-250K  □ 250K-1M  □ 1M+        │
│                                                          │
│  4. Investment Experience:                                │
│     □ Beginner (<1yr)  □ Novice (1-3yr)                   │
│     □ Intermediate (3-10yr)  □ Advanced (10yr+)           │
│     □ Professional                                        │
│                                                          │
│  5. Monthly Contribution Capacity:                         │
│     □ <500  □ 500-2K  □ 2K-5K  □ 5K-10K  □ 10K+         │
└──────────────────────────────────────────────────────────┘
```

## 2.2 Risk Tolerance

```
┌──────────────────────────────────────────────────────────┐
│  📋 Client Questionnaire — Part 2: Risk Tolerance          │
├──────────────────────────────────────────────────────────┤
│  6. Your primary investment goal is:                      │
│     □ Capital preservation (+2-4% annually)               │
│     □ Steady growth (+5-8% annually)                      │
│     □ Aggressive growth (+8-15% annually)                 │
│     □ High growth (+15%+ annually)                        │
│     □ Beat SPY (+SPY+2-5% annually)                       │
│                                                          │
│  7. Your investment horizon:                              │
│     □ <1 year (short-term)  □ 1-3 years                   │
│     □ 3-5 years  □ 5-10 years  □ 10+ years (retirement)   │
│                                                          │
│  8. If your portfolio dropped 20% in a month, you would:  │
│     □ Sell everything immediately to stop losses          │
│     □ Sell partially to reduce risk                       │
│     □ Hold and wait for recovery                          │
│     □ Buy more to average down                            │
│                                                          │
│  9. Maximum acceptable annual loss:                        │
│     □ <5%  □ 5-10%  □ 10-20%  □ 20-30%  □ 30%+          │
│                                                          │
│  10. Your view on leverage (borrowing to invest):          │
│      □ No leverage acceptable                              │
│      □ Minor leverage OK (<1.2x)                           │
│      □ Moderate leverage OK (1.2-1.5x)                     │
│      □ Higher leverage OK (1.5-2x)                         │
└──────────────────────────────────────────────────────────┘
```

## 2.3 Investment Preferences & Restrictions

```
┌──────────────────────────────────────────────────────────┐
│  📋 Client Questionnaire — Part 3: Preferences            │
├──────────────────────────────────────────────────────────┤
│  11. Preferred markets (multi-select):                    │
│      □ US Stocks  □ HK Stocks  □ China A-Share            │
│      □ Japan  □ Crypto  □ Emerging Markets  □ Europe     │
│                                                          │
│  12. Preferred asset classes (multi-select):               │
│      □ Individual Stocks  □ ETFs  □ Mutual Funds          │
│      □ Bonds  □ Commodities (Gold/Silver)                 │
│      □ Real Estate (REITs)  □ Crypto  □ Cash             │
│                                                          │
│  13. Sector preferences (multi-select):                    │
│      □ Technology  □ Financials  □ Healthcare  □ Energy   │
│      □ Consumer  □ Industrials  □ Utilities  □ Real Estate│
│      □ Materials  □ No preference                         │
│                                                          │
│  14. ESG (Environmental, Social, Governance) preferences:  │
│      □ No special preference                              │
│      □ Avoid fossil fuels/tobacco/weapons                 │
│      □ Only invest in high ESG-rated companies            │
│      □ Actively seek impact investments                   │
│                                                          │
│  15. Any prohibited industries or companies?               │
│      ________________________________________________     │
│                                                          │
│  16. Current portfolio holdings (if any):                  │
│      ________________________________________________     │
└──────────────────────────────────────────────────────────┘
```

## 2.4 Behavioral Finance Assessment

```
┌──────────────────────────────────────────────────────────┐
│  📋 Client Questionnaire — Part 4: Behavioral Finance      │
├──────────────────────────────────────────────────────────┤
│  17. Market suddenly drops 10%. Your first thought:        │
│      □ "Panic — get out now!"                              │
│      □ "Wait for a bounce to sell"                        │
│      □ "This is a buying opportunity"                     │
│      □ "Let me understand what's happening first"         │
│                                                          │
│  18. How often do you check your portfolio?                │
│      □ Multiple times daily  □ Daily  □ Weekly            │
│      □ Monthly  □ Rarely                                  │
│                                                          │
│  19. Your emotional response to market volatility:         │
│      □ Very sensitive — loses sleep                        │
│      □ Somewhat — affects my mood                         │
│      □ Calm — understand it's normal noise                │
│      □ Completely unaffected                              │
│                                                          │
│  20. Trust level in AI portfolio management:               │
│      □ Full trust in AI decisions                          │
│      □ Trust with reservations (want human review)        │
│      □ Skeptical — try small amount first                 │
│      □ Not very trusting — reference only                 │
└──────────────────────────────────────────────────────────┘
```

## 2.5 Generated Client Risk Profile

After the questionnaire, the LLM generates a client risk profile:

```json
{
  "client_profile": {
    "risk_score": 68,
    "risk_tolerance": "moderate_aggressive",
    "investment_horizon": "long_term",
    "preferred_markets": ["US", "HK"],
    "excluded_sectors": ["tobacco", "weapons"],
    "behavioral_bias": ["loss_aversion", "recency_bias"],
    "suggested_benchmark": "SPY",
    "suggested_goal": "beat SPY by 2-3% annually"
  },
  "portfolio_constraints": {
    "max_drawdown_pct": 25,
    "min_cash_pct": 5,
    "max_single_stock_pct": 10,
    "max_sector_exposure_pct": 35,
    "leverage_allowed": false,
    "derivatives_allowed": false,
    "crypto_allowed": true,
    "crypto_max_pct": 10
  }
}
```

## 2.6 API Model for Questionnaire

```python
class QuestionnaireResponse(BaseModel):
    # Personal info
    age_range: str  # "18-25" | "26-35" | ...
    annual_income: str  # "<50K" | "50-100K" | ...
    investable_assets: str
    experience: str
    monthly_contribution: str

    # Risk tolerance
    investment_goal: str
    investment_horizon: str
    crash_response: str  # How they'd react to a 20% drop
    max_acceptable_loss: str
    leverage_view: str

    # Preferences
    preferred_markets: list[str]
    preferred_asset_classes: list[str]
    preferred_sectors: list[str]
    esg_preference: str
    prohibited_industries: str | None
    current_holdings: str | None

    # Behavioral
    market_drop_reaction: str
    check_frequency: str
    volatility_sensitivity: str
    ai_trust_level: str
```

## 2.7 Scoring Formula

```python
def calculate_risk_score(responses: dict) -> int:
    """
    0-100 risk score.
    0 = extremely conservative
    100 = extremely aggressive

    Components:
    - Financial capacity (income, assets, contributions): 30%
    - Risk attitude questions (goal, loss tolerance, leverage): 40%
    - Behavioral assessment (panic reaction, check frequency): 20%
    - Experience level: 10%
    """
    score = 0

    # Financial capacity (0-30)
    assets_map = {"<10K": 2, "10-50K": 6, "50-250K": 12, "250K-1M": 20, "1M+": 30}
    score += assets_map.get(responses.get("investable_assets", "<10K"), 0) * 0.3

    # ... additional scoring logic

    return min(max(score, 0), 100)
```
