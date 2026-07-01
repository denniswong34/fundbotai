# 07 — Risk Management

## 7.1 Risk Framework Overview

```
Risk Management Hierarchy
═══════════════════════════

Level 1: Hard Limits (enforced by code, cannot be overridden)
├── Max single stock concentration (%)
├── Max sector exposure (%)
├── Max leverage ratio
├── Margin call prevention
└── Regulatory compliance (pattern day trading, etc.)

Level 2: Soft Limits (configurable per client, LLM-aware)
├── Max drawdown (%)
├── Value at Risk (VaR 95%)
├── Portfolio beta range
├── Minimum diversification (# holdings)
├── Turnover limits
└── Cash reserve minimum (%)

Level 3: Warning Signals (monitoring, non-blocking)
├── Insider selling alerts
├── Sector overheating (RSI > 75)
├── Market breadth divergence
├── VIX term structure inversion
└── Correlation regime shift
```

## 7.2 Risk Metrics Calculation

### Value at Risk (VaR)

```python
def calculate_var(
    positions: list[Position],
    confidence: float = 0.95,
    horizon_days: int = 1,
    historical_days: int = 252
) -> dict:
    """
    Calculate VaR using historical simulation method.

    Returns:
    {
        "var_95": -3240.50,        # Dollar amount at risk
        "var_95_pct": -2.13,       # Percentage at risk
        "conditional_var": -4500.20, # Expected shortfall
        "correction_factor": 1.15  # Adjusted for portfolio concentration
    }
    """
    # Get historical returns for each position
    portfolio_returns = []
    for pos in positions:
        hist = get_historical_returns(pos.symbol, historical_days)
        weighted = hist * (pos.weight / 100)
        portfolio_returns.append(weighted)

    # Sum to portfolio-level returns
    total_returns = sum(portfolio_returns)

    # Sort returns and find the VaR percentile
    sorted_returns = sorted(total_returns)
    var_index = int(len(sorted_returns) * (1 - confidence))
    var_value = sorted_returns[var_index]

    # Calculate Conditional VaR (Expected Shortfall)
    tail_returns = sorted_returns[:var_index]
    cvar = sum(tail_returns) / len(tail_returns) if tail_returns else var_value

    # Get the current portfolio value
    portfolio_value = sum(p.market_value for p in positions)

    return {
        "var_95": round(var_value, 2),
        "var_95_pct": round(var_value / portfolio_value * 100, 2) if portfolio_value else 0,
        "conditional_var": round(cvar, 2),
    }
```

### Maximum Drawdown

```python
def calculate_max_drawdown(equity_curve: list[float]) -> dict:
    """
    Calculate maximum drawdown and current drawdown from peak.

    Returns:
    {
        "max_drawdown_pct": 18.5,
        "current_drawdown_pct": 5.2,
        "peak_value": 152430.50,
        "current_value": 144520.30,
        "days_since_peak": 45
    }
    """
    peak = equity_curve[0]
    max_dd = 0
    peak_index = 0

    for i, value in enumerate(equity_curve):
        if value > peak:
            peak = value
            peak_index = i
        dd = (peak - value) / peak * 100
        max_dd = max(max_dd, dd)

    current_value = equity_curve[-1]
    current_dd = (peak - current_value) / peak * 100

    return {
        "max_drawdown_pct": round(max_dd, 2),
        "current_drawdown_pct": round(current_dd, 2),
        "peak_value": round(peak, 2),
        "current_value": round(current_value, 2),
        "days_since_peak": len(equity_curve) - peak_index - 1,
    }
```

### Sharpe Ratio

```python
def calculate_sharpe(
    returns: list[float],
    risk_free_rate: float = 0.05  # Current 5% risk-free rate
) -> float:
    """
    Calculate annualized Sharpe ratio.
    Sharpe = (Portfolio Return - Risk-Free Rate) / Portfolio Volatility
    """
    avg_return = statistics.mean(returns)
    volatility = statistics.stdev(returns)

    # Annualize (assuming daily returns)
    annualized_return = avg_return * 252
    annualized_vol = volatility * math.sqrt(252)

    if annualized_vol == 0:
        return 0

    return round((annualized_return - risk_free_rate) / annualized_vol, 2)
```

### Additional Risk Metrics

```python
def calculate_risk_metrics(portfolio: Portfolio) -> dict:
    """Comprehensive risk assessment for a portfolio."""

    positions = portfolio.positions
    values = [p.market_value for p in positions]
    weights = [p.weight / 100 for p in positions]
    total = sum(values)

    # Concentration metrics
    herfindahl = sum(w ** 2 for w in weights)
    effective_n = 1 / herfindahl if herfindahl > 0 else 0

    # Beta (relative to SPY)
    portfolio_beta = sum(p.beta * w for p, w in zip(positions, weights))

    # Correlation matrix (simplified — average pairwise correlation)
    pairwise_correlations = []
    for i in range(len(positions)):
        for j in range(i + 1, len(positions)):
            corr = get_correlation(positions[i].symbol, positions[j].symbol)
            pairwise_correlations.append(corr)
    avg_correlation = statistics.mean(pairwise_correlations) if pairwise_correlations else 0

    return {
        "concentration": {
            "herfindahl_index": round(herfindahl, 4),
            "effective_holdings": round(effective_n, 1),
            "largest_weight_pct": round(max(weights) * 100, 2),
        },
        "systematic_risk": {
            "portfolio_beta": round(portfolio_beta, 3),
            "avg_correlation": round(avg_correlation, 3),
        },
        "diversification_ratio": round(1 / (1 + avg_correlation * (effective_n - 1)), 3)
            if effective_n > 1 else 1,
    }
```

## 7.3 Risk Limit Enforcement

```python
class RiskEnforcer:
    """
    Validates LLM decisions against risk limits before execution.
    Runs after LLM proposes trades but before execution.
    """

    def __init__(self, client_constraints: dict):
        self.constraints = client_constraints

    async def validate_decision(
        self,
        portfolio: Portfolio,
        proposed_weights: dict[str, float],
    ) -> tuple[bool, list[str]]:
        """
        Validates a proposed allocation against all risk limits.
        Returns (is_safe, list_of_warnings).
        """
        warnings = []

        # 1. Concentration check
        for symbol, weight in proposed_weights.items():
            max_single = self.constraints.get("max_single_stock_pct", 15)
            if weight > max_single:
                warnings.append(
                    f"{symbol}: {weight:.1f}% exceeds max single stock limit of {max_single}%"
                )

        # 2. Sector exposure check
        sector_exposure = self._calculate_sector_exposure(proposed_weights)
        for sector, exposure in sector_exposure.items():
            max_sector = self.constraints.get("max_sector_exposure_pct", 40)
            if exposure > max_sector:
                warnings.append(
                    f"{sector}: {exposure:.1f}% exceeds max sector limit of {max_sector}%"
                )

        # 3. Max drawdown check
        current_dd = calculate_max_drawdown(
            await get_equity_curve(portfolio.id)
        )["current_drawdown_pct"]
        max_dd = self.constraints.get("max_drawdown_pct", 25)

        if current_dd > max_dd:
            warnings.append(
                f"Current drawdown {current_dd:.1f}% exceeds max {max_dd}%. "
                f"Recommend reducing risk."
            )

        # 4. VaR check
        var = calculate_var(await self._positions_from_weights(proposed_weights))
        var_limit = self.constraints.get("var_95_limit_pct", 5)
        if var["var_95_pct"] > var_limit:
            warnings.append(
                f"VaR(95%) {var['var_95_pct']:.2f}% exceeds limit of {var_limit}%"
            )

        # 5. Leverage check
        total_weight = sum(proposed_weights.values())
        if total_weight > 100:
            if not self.constraints.get("leverage_allowed", False):
                warnings.append(
                    f"Total weight {total_weight:.1f}% > 100%. Leverage not permitted."
                )

        # 6. Diversification check
        min_holdings = self.constraints.get("min_holdings", 3)
        if len(proposed_weights) < min_holdings:
            warnings.append(
                f"Only {len(proposed_weights)} holdings, minimum is {min_holdings}"
            )

        is_safe = len(warnings) == 0

        if is_safe:
            logger.info("Risk check PASSED — all constraints satisfied")
        else:
            for w in warnings:
                logger.warning(f"Risk check WARNING: {w}")

        return is_safe, warnings

    def _calculate_sector_exposure(
        self, weights: dict[str, float]
    ) -> dict[str, float]:
        """Aggregate weights by sector."""
        sector_map = get_sector_mapping()
        exposure = {}
        for symbol, weight in weights.items():
            sector = sector_map.get(symbol, "Unknown")
            exposure[sector] = exposure.get(sector, 0) + weight
        return exposure
```

## 7.4 Stress Testing Scenarios

```python
STRESS_SCENARIOS = {
    "rate_hike_100bp": {
        "description": "Unexpected 100bp Fed rate hike",
        "impact": {
            "Tech": -0.08,     # -8%
            "Financials": +0.03,
            "RealEstate": -0.12,
            "Bonds": -0.05,
            "Gold": +0.02,
        }
    },
    "market_crash_2008": {
        "description": "2008-style financial crisis (-40% equities)",
        "impact": {
            "Tech": -0.45,
            "Financials": -0.55,
            "Energy": -0.50,
            "Consumer": -0.35,
            "Gold": +0.10,
            "Bonds": +0.15,
        }
    },
    "inflation_spike": {
        "description": "CPI jumps to 6%, stagflation fears",
        "impact": {
            "Tech": -0.15,
            "Energy": +0.12,
            "Materials": +0.08,
            "ConsumerStaples": +0.05,
            "Gold": +0.15,
            "Bonds": -0.10,
        }
    },
    "tech_bubble_burst": {
        "description": "Tech sector correction -30%",
        "impact": {
            "Tech": -0.30,
            "ConsumerDisc": -0.15,
            "Other": -0.05,
            "Gold": +0.08,
            "Bonds": +0.10,
        }
    },
}
```
