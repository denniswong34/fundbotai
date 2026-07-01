# 08 — Performance Evaluation

## 8.1 Key Performance Metrics

| Metric | Formula | Target | Frequency |
|---|---|---|---|
| **Total Return** | `(End - Start) / Start × 100` | Beat SPY | Daily |
| **Alpha** | `Portfolio Return - Benchmark Return` | > 0 | Monthly |
| **Beta** | `Cov(Portfolio, SPY) / Var(SPY)` | 0.8 - 1.2 | Monthly |
| **Sharpe Ratio** | `(Return - Rf) / Volatility` | > 1.0 | Monthly |
| **Sortino Ratio** | `(Return - Rf) / Downside Deviation` | > 1.5 | Monthly |
| **Max Drawdown** | `Peak-to-Trough Decline` | < 25% | Rolling |
| **Win Rate** | `Winning trades / Total trades` | > 50% | Monthly |
| **Profit Factor** | `Gross Profit / Gross Loss` | > 1.5 | Monthly |
| **Calmar Ratio** | `Annualized Return / Max Drawdown` | > 1.0 | Monthly |
| **Information Ratio** | `Alpha / Tracking Error` | > 0.5 | Monthly |

## 8.2 Performance Calculation Service

```python
class PerformanceCalculator:
    """
    Calculates comprehensive performance metrics for portfolios
    and AI managers.
    """

    async def calculate_portfolio_metrics(
        self, portfolio_id: int, benchmark_symbol: str = "SPY"
    ) -> dict:
        """Full performance analysis with benchmark comparison."""

        # Get portfolio equity curve
        snapshots = await self.db.execute(
            select(PortfolioPerformanceSnapshot)
            .where(PortfolioPerformanceSnapshot.portfolio_id == portfolio_id)
            .order_by(PortfolioPerformanceSnapshot.snapshot_date.asc())
        )
        equity = list(snapshots.scalars().all())

        if len(equity) < 2:
            return {"error": "Not enough data points"}

        # Get benchmark data (SPY)
        benchmark_data = await self._get_benchmark_data(
            benchmark_symbol,
            equity[0].snapshot_date,
            equity[-1].snapshot_date,
        )

        # Calculate returns
        portfolio_values = [s.total_value for s in equity]
        benchmark_values = [b["close"] for b in benchmark_data]

        portfolio_returns = self._daily_returns(portfolio_values)
        benchmark_returns = self._daily_returns(benchmark_values)

        # Core metrics
        total_return = self._total_return(portfolio_values)
        benchmark_return = self._total_return(benchmark_values)
        alpha = total_return - benchmark_return
        beta = self._beta(portfolio_returns, benchmark_returns)
        tracking_error = self._tracking_error(portfolio_returns, benchmark_returns)
        information_ratio = alpha / tracking_error if tracking_error > 0 else 0

        # Risk metrics
        volatility = statistics.stdev(portfolio_returns) * math.sqrt(252)
        downside_returns = [r for r in portfolio_returns if r < 0]
        downside_dev = statistics.stdev(downside_returns) * math.sqrt(252) if downside_returns else 0
        max_dd = self._max_drawdown(portfolio_values)

        # Risk-adjusted returns
        risk_free = 0.05  # Current 5% risk-free rate
        sharpe = (total_return - risk_free) / volatility if volatility > 0 else 0
        sortino = (total_return - risk_free) / downside_dev if downside_dev > 0 else 0
        calmar = total_return / abs(max_dd) if max_dd != 0 else 0

        return {
            "period": {
                "start": equity[0].snapshot_date.isoformat(),
                "end": equity[-1].snapshot_date.isoformat(),
                "trading_days": len(portfolio_values),
            },
            "returns": {
                "total_return_pct": round(total_return * 100, 2),
                "benchmark_return_pct": round(benchmark_return * 100, 2),
                "alpha_pct": round(alpha * 100, 2),
                "excess_return_pct": round((total_return - benchmark_return) * 100, 2),
            },
            "risk": {
                "volatility_pct": round(volatility * 100, 2),
                "max_drawdown_pct": round(max_dd * 100, 2),
                "var_95_pct": round(self._var(portfolio_returns, 0.95) * 100, 2),
                "downside_deviation_pct": round(downside_dev * 100, 2),
            },
            "risk_adjusted": {
                "sharpe_ratio": round(sharpe, 3),
                "sortino_ratio": round(sortino, 3),
                "calmar_ratio": round(calmar, 3),
                "information_ratio": round(information_ratio, 3),
            },
            "benchmark_comparison": {
                "beta": round(beta, 3),
                "tracking_error_pct": round(tracking_error * 100, 2),
                "correlation": round(self._correlation(portfolio_returns, benchmark_returns), 3),
                "up_capture": round(self._up_capture(portfolio_returns, benchmark_returns), 2),
                "down_capture": round(self._down_capture(portfolio_returns, benchmark_returns), 2),
            },
            "ai_manager_score": self._calculate_ai_score(
                alpha, sharpe, max_dd, win_rate
            ),
        }

    def _daily_returns(self, values: list[float]) -> list[float]:
        return [
            (values[i] - values[i - 1]) / values[i - 1]
            for i in range(1, len(values))
        ]

    def _total_return(self, values: list[float]) -> float:
        return (values[-1] - values[0]) / values[0]

    def _beta(
        self, portfolio_returns: list[float], benchmark_returns: list[float]
    ) -> float:
        cov_matrix = np.cov(portfolio_returns, benchmark_returns)
        covariance = cov_matrix[0, 1]
        variance = cov_matrix[1, 1]
        return covariance / variance if variance > 0 else 1.0

    def _tracking_error(
        self, portfolio_returns: list[float], benchmark_returns: list[float]
    ) -> float:
        diff = [p - b for p, b in zip(portfolio_returns, benchmark_returns)]
        return statistics.stdev(diff)

    def _max_drawdown(self, values: list[float]) -> float:
        peak = values[0]
        max_dd = 0
        for v in values:
            if v > peak:
                peak = v
            dd = (peak - v) / peak
            max_dd = max(max_dd, dd)
        return max_dd

    def _var(self, returns: list[float], confidence: float = 0.95) -> float:
        sorted_returns = sorted(returns)
        index = int(len(sorted_returns) * (1 - confidence))
        return abs(sorted_returns[index])

    def _correlation(self, a: list[float], b: list[float]) -> float:
        return statistics.correlation(a, b) if len(a) > 2 else 0

    def _up_capture(
        self, portfolio_returns: list[float], benchmark_returns: list[float]
    ) -> float:
        """Percentage of benchmark gains captured."""
        up_days = [(p, b) for p, b in zip(portfolio_returns, benchmark_returns) if b > 0]
        if not up_days:
            return 0
        port_up = sum(p for p, _ in up_days) / len(up_days)
        bench_up = sum(b for _, b in up_days) / len(up_days)
        return port_up / bench_up * 100 if bench_up > 0 else 0

    def _down_capture(
        self, portfolio_returns: list[float], benchmark_returns: list[float]
    ) -> float:
        """Percentage of benchmark losses captured (lower is better)."""
        down_days = [(p, b) for p, b in zip(portfolio_returns, benchmark_returns) if b < 0]
        if not down_days:
            return 0
        port_down = sum(p for p, _ in down_days) / len(down_days)
        bench_down = sum(b for _, b in down_days) / len(down_days)
        return port_down / bench_down * 100 if bench_down < 0 else 0

    def _calculate_ai_score(
        self,
        alpha: float,
        sharpe: float,
        max_drawdown: float,
        win_rate: float,
    ) -> float:
        """
        Composite AI Manager Score (0-100).
        Used for the leaderboard ranking.
        """
        alpha_score = min(max((alpha + 0.10) / 0.20 * 30, 0), 30)
        sharpe_score = min(max(sharpe / 2.0 * 30, 0), 30)
        drawdown_score = min(max((1 - abs(max_drawdown) / 0.30) * 20, 0), 20)
        win_rate_score = min(max(win_rate / 0.60 * 20, 0), 20)

        return round(alpha_score + sharpe_score + drawdown_score + win_rate_score, 1)
```

## 8.3 Leaderboard API

```python
@router.get("/api/ai-managers/leaderboard")
async def get_leaderboard(
    org_id: int = Depends(get_current_org),
    sort_by: str = Query("ai_score", enum=["ai_score", "total_return", "sharpe"]),
    db: AsyncSession = Depends(get_db),
):
    """Get all AI managers ranked by performance."""
    result = await db.execute(
        select(AiManager)
        .where(AiManager.org_id == org_id, AiManager.is_active == True)
    )
    managers = list(result.scalars().all())

    entries = []
    for m in managers:
        metrics = await PerformanceCalculator(db).calculate_portfolio_metrics(
            m.assigned_portfolio_id
        )
        entries.append({
            "id": m.id,
            "name": m.name,
            "model_name": m.model_name,
            "portfolio_id": m.assigned_portfolio_id,
            "total_return_pct": metrics["returns"]["total_return_pct"],
            "alpha_pct": metrics["returns"]["alpha_pct"],
            "sharpe_ratio": metrics["risk_adjusted"]["sharpe_ratio"],
            "max_drawdown_pct": metrics["risk"]["max_drawdown_pct"],
            "ai_score": metrics["ai_manager_score"],
            "volatility_pct": metrics["risk"]["volatility_pct"],
            "total_trades": m.total_trades,
            "last_decision_at": ...,  # From AiDecisionLog
        })

    # Sort by selected metric
    entries.sort(key=lambda e: e.get(sort_by, 0), reverse=True)

    # Assign ranks (with medals)
    for i, e in enumerate(entries):
        e["rank"] = i + 1
        e["medal"] = ["🥇", "🥈", "🥉"][i] if i < 3 else f"#{i+1}"

    return entries
```

## 8.4 Client Performance Report (LLM-Generated)

After each decision cycle, the LLM generates a natural-language report:

```
┌─────────────────────────────────────────────────────────┐
│  🏆 DeepSeek Trader — Weekly Report (Jun 28 - Jul 1)    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  📊 Weekly Performance: +2.1% vs SPY +1.5% → 🟢 BEAT    │
│                                                         │
│  📈 YTD: +13.7% vs SPY +11.2% → Alpha +2.5%             │
│                                                         │
│  🔍 Market Analysis:                                     │
│  This week markets rallied on Fed rate cut expectations. │
│  VIX stayed low at 14, indicating stable sentiment.      │
│  Capital rotated from Energy to Tech.                    │
│                                                         │
│  ✅ Trades Executed:                                     │
│  • Jul 1: Sold 2 NVDA @ $198.50 (locked +76% profit)    │
│  • Jul 1: Bought 5 AAPL @ $198.50 (analyst upgrade)     │
│                                                         │
│  ⚠️ Risk Alert:                                          │
│  Tech sector exposure at 62.5% (above 35% soft limit)    │
│  Recommend gradual reduction to diversify                │
│                                                         │
│  🎯 Next Week Outlook:                                   │
│  Watch Jul 5 NFP data. Strong jobs data may delay cuts.  │
│  If NFP > 250K, will shift to more defensive posture     │
└─────────────────────────────────────────────────────────┘
```
