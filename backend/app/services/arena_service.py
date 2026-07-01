"""Arena Service — AI Manager lifecycle, decision execution, and LLM integration."""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_manager import AiManager, AiDecisionLog
from app.models.portfolio import Portfolio, PortfolioPerformanceSnapshot
from app.services.portfolio_service import PortfolioManager

logger = logging.getLogger(__name__)


class ArenaError(Exception):
    pass


class AiManagerNotFound(ArenaError):
    pass


class LLMGateway:
    """
    OpenAI-compatible API wrapper for the opencode-go gateway.
    Allows routing to different LLM models through a single endpoint.

    In Phase 1, this returns a simulated decision for testing.
    Phase 2+ will connect to real opencode-go API.
    """

    def __init__(self, api_base: str = None, api_key: str = None):
        self.api_base = api_base or "http://localhost:8080/v1"
        self.api_key = api_key or ""
        self._mock_mode = True  # Phase 1: simulated decisions

    async def generate_decision(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> dict:
        """
        Generate an investment decision from the LLM.

        Phase 1: Returns simulated decision (no real LLM call yet).
        Phase 2+: Calls opencode-go /v1/chat/completions.
        """
        if self._mock_mode:
            return self._mock_decision()

        # Future: real API call
        # response = await self._call_opencode_api(model, messages, temperature, max_tokens)
        # return json.loads(response.choices[0].message.content)
        return self._mock_decision()

    def _mock_decision(self) -> dict:
        """Return a plausible simulated decision for Phase 1 testing."""
        return {
            "action": "rebalance",
            "reasoning": (
                "Market conditions appear favorable with stable VIX and positive momentum. "
                "Technology sector continues to lead, suggesting maintaining overweight position. "
                "However, insider selling activity warrants slight profit-taking in high-flyers. "
                "Recommend rebalancing to lock gains while maintaining growth exposure."
            ),
            "risk_assessment": {
                "level": "moderate",
                "primary_risk": "sector_concentration",
                "details": "Tech-heavy portfolio but VIX at 14 suggests calm markets",
                "var_95_estimate": 3.5,
                "concentration_risk": "tech_overweight"
            },
            "target_weights": {
                "AAPL": 25.0,
                "MSFT": 22.0,
                "AMZN": 18.0,
                "GOOGL": 18.0,
                "NVDA": 12.0,
                "CASH": 5.0,
            },
            "benchmark_analysis": {
                "spy_ytd": 11.2,
                "portfolio_ytd": 13.7,
                "alpha": 2.5,
                "assessment": "Portfolio maintains outperformance trajectory",
                "expected_spy_return_next_month": 1.5,
                "expected_portfolio_return_next_month": 2.1
            },
            "trades_to_execute": [
                {"symbol": "NVDA", "side": "sell", "qty": 2,
                 "reason": "Lock profits after strong run; insider selling signal"},
                {"symbol": "AAPL", "side": "buy", "qty": 3,
                 "reason": "Analyst upgrade, rate-cut beneficiary"},
            ],
        }


class ArenaService:
    """
    Central service for AI Manager operations:
    - CRUD for AI Managers
    - Triggering AI decisions
    - Performance tracking and leaderboard
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm_gateway = LLMGateway()
        self.portfolio_manager = PortfolioManager(db)

    # ── AI Manager CRUD ──────────────────────────────────────

    async def create_manager(self, org_id: int, user_id: int, data: dict) -> AiManager:
        """Create a new AI Manager."""
        manager = AiManager(
            org_id=org_id,
            user_id=user_id,
            name=data["name"],
            description=data.get("description"),
            model_provider=data.get("model_provider", "opencode-go"),
            model_name=data["model_name"],
            api_base_url=data.get("api_base_url"),
            system_prompt=data.get("system_prompt"),
            temperature=data.get("temperature", 0.70),
            max_tokens=data.get("max_tokens", 4000),
            assigned_portfolio_id=data.get("assigned_portfolio_id"),
            run_frequency=data.get("run_frequency", "daily"),
            auto_run_enabled=bool(data.get("auto_run_enabled", False)),
            is_active=bool(data.get("is_active", True)),
        )
        # If assigned to a portfolio, auto-create a portfolio if none provided
        self.db.add(manager)
        await self.db.commit()
        await self.db.refresh(manager)
        logger.info(f"AI Manager created: id={manager.id}, name={manager.name}, model={manager.model_name}")
        return manager

    async def get_managers(self, org_id: int) -> list[AiManager]:
        """Get all AI managers for an organization."""
        result = await self.db.execute(
            select(AiManager)
            .where(AiManager.org_id == org_id)
            .order_by(AiManager.is_active.desc(), AiManager.name.asc())
        )
        return list(result.scalars().all())

    async def get_manager(self, org_id: int, manager_id: int) -> AiManager:
        """Get a single AI manager."""
        result = await self.db.execute(
            select(AiManager).where(
                AiManager.id == manager_id,
                AiManager.org_id == org_id,
            )
        )
        manager = result.scalar_one_or_none()
        if manager is None:
            raise AiManagerNotFound(f"AI Manager {manager_id} not found")
        return manager

    async def update_manager(self, org_id: int, manager_id: int, data: dict) -> AiManager:
        """Update an AI manager's configuration."""
        manager = await self.get_manager(org_id, manager_id)

        for field in ("name", "description", "model_provider", "model_name",
                       "api_base_url", "system_prompt", "run_frequency",):
            if field in data and data[field] is not None:
                setattr(manager, field, data[field])

        for num_field in ("temperature", "max_tokens"):
            if num_field in data and data[num_field] is not None:
                setattr(manager, num_field, float(data[num_field]))

        for bool_field in ("auto_run_enabled", "is_active"):
            if bool_field in data and data[bool_field] is not None:
                setattr(manager, bool_field, bool(data[bool_field]))

        if "assigned_portfolio_id" in data:
            manager.assigned_portfolio_id = data["assigned_portfolio_id"]

        await self.db.commit()
        await self.db.refresh(manager)
        return manager

    async def delete_manager(self, org_id: int, manager_id: int) -> bool:
        """Delete an AI manager."""
        manager = await self.get_manager(org_id, manager_id)
        manager.is_active = False
        await self.db.commit()
        return True

    # ── Decision Execution ──────────────────────────────────

    async def trigger_decision(
        self,
        org_id: int,
        manager_id: int,
        trigger_source: str = "manual",
    ) -> dict:
        """
        Trigger an AI fund manager decision cycle.

        1. Gather portfolio state + market data
        2. Assemble the prompt
        3. Call LLM via gateway
        4. Parse the structured decision
        5. Log everything (no automatic execution in Phase 1)
        6. Return the decision for review
        """
        manager = await self.get_manager(org_id, manager_id)

        # 1. Gather context
        portfolio_state = {}
        portfolio = None
        if manager.assigned_portfolio_id:
            try:
                result = await self.db.execute(
                    select(Portfolio).where(
                        Portfolio.id == manager.assigned_portfolio_id,
                        Portfolio.org_id == org_id,
                    )
                )
                portfolio = result.scalar_one_or_none()
                if portfolio:
                    portfolio_state = {
                        "id": portfolio.id,
                        "name": portfolio.name,
                        "total_value": float(portfolio.total_value or 0),
                        "total_pnl": float(portfolio.total_pnl or 0),
                        "total_pnl_pct": float(portfolio.total_pnl_pct or 0),
                        "last_rebalanced_at": str(portfolio.last_rebalanced_at) if portfolio.last_rebalanced_at else None,
                    }
            except Exception as e:
                logger.warning(f"Manager {manager_id}: failed to load portfolio state: {e}")

        # 2. Assemble prompt
        system_prompt = manager.system_prompt or self._default_system_prompt(manager.name)
        user_prompt = self._build_decision_prompt(manager, portfolio_state)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # 3. Call LLM
        raw_decision = await self.llm_gateway.generate_decision(
            model=manager.model_name,
            messages=messages,
            temperature=float(manager.temperature),
            max_tokens=manager.max_tokens,
        )

        # 4. Parse
        decision_json = json.dumps(raw_decision)

        # 5. Log the decision
        snapshot_before = None
        if portfolio:
            holdings = await self.portfolio_manager.get_holdings(manager.assigned_portfolio_id)
            snapshot_before = {
                "holdings": [
                    {"symbol": h.symbol, "shares": float(h.current_shares or 0),
                     "price": float(h.current_price or 0),
                     "weight": float(h.target_weight_pct or 0)}
                    for h in holdings
                ],
                "total_value": float(portfolio.total_value or 0),
            }

        decision_log = AiDecisionLog(
            ai_manager_id=manager_id,
            portfolio_id=manager.assigned_portfolio_id,
            org_id=org_id,
            user_id=manager.user_id,
            triggered_at=datetime.now(timezone.utc),
            market_regime=raw_decision.get("market_regime", "unknown"),
            trigger_source=trigger_source,
            data_snapshot={"state": "mock_phase1", "note": "Real-time market data TBD Phase 3"},
            rag_results_used=[],
            prompt_sent=user_prompt,
            raw_response=decision_json,
            parsed_decision=raw_decision,
            reasoning=raw_decision.get("reasoning", ""),
            risk_assessment=raw_decision.get("risk_assessment", {}),
            benchmark_analysis=raw_decision.get("benchmark_analysis", {}),
            portfolio_snapshot_before=snapshot_before,
            orders_created=0,
            execution_status="pending_review",
        )
        self.db.add(decision_log)

        # Update manager stats
        manager.last_decision_at = datetime.now(timezone.utc)
        manager.decisions_count = (manager.decisions_count or 0) + 1

        await self.db.commit()
        await self.db.refresh(decision_log)

        logger.info(f"Manager {manager_id} decision triggered: log_id={decision_log.id}")
        return {
            "status": "success",
            "decision_log_id": decision_log.id,
            "decision": raw_decision,
            "note": "Phase 1: simulated decision. Real LLM integration in Phase 3.",
        }

    # ── Decision History ─────────────────────────────────────

    async def get_decision_logs(
        self, org_id: int, manager_id: int, limit: int = 20
    ) -> list[AiDecisionLog]:
        """Get decision history for a specific AI manager."""
        result = await self.db.execute(
            select(AiDecisionLog)
            .where(
                AiDecisionLog.ai_manager_id == manager_id,
                AiDecisionLog.org_id == org_id,
            )
            .order_by(AiDecisionLog.triggered_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_decision_log(
        self, org_id: int, log_id: int
    ) -> AiDecisionLog:
        """Get a single decision log entry."""
        result = await self.db.execute(
            select(AiDecisionLog).where(
                AiDecisionLog.id == log_id,
                AiDecisionLog.org_id == org_id,
            )
        )
        log = result.scalar_one_or_none()
        if log is None:
            raise AiManagerNotFound(f"Decision log {log_id} not found")
        return log

    # ── Leaderboard ──────────────────────────────────────────

    async def get_leaderboard(self, org_id: int) -> dict:
        """Get ranked AI managers with performance metrics."""
        managers = await self.get_managers(org_id)
        active_only = [m for m in managers if m.is_active or True]  # Show all in list

        entries = []
        for m in active_only:
            # Calculate metrics from performance snapshots
            alpha_pct = 0.0
            max_dd_pct = 0.0
            volatility_pct = 0.0
            ai_score = 0.0

            if m.total_return_pct:
                # Mock SPY for now — real benchmark comparison in Phase 3
                spy_return = float(m.total_return_pct) - 2.5  # Assume alpha ~2.5%
                alpha_pct = max(float(m.total_return_pct) - spy_return, 0)
                # Simplified AI score: combination of return, sharpe, win_rate
                score = (
                    min(max(float(m.total_return_pct) * 2, 0), 30) +  # Return: up to 30 pts
                    min(max(float(m.sharpe_ratio or 0) * 20, 0), 30) +  # Sharpe: up to 30 pts
                    min(max(float(m.win_rate or 0) * 0.3, 0), 20) +  # Win rate: up to 20 pts
                    10  # Base participation
                )
                ai_score = round(score, 1)

            entries.append({
                "id": m.id,
                "name": m.name,
                "model_name": m.model_name,
                "portfolio_id": m.assigned_portfolio_id,
                "total_return_pct": float(m.total_return_pct or 0),
                "alpha_pct": alpha_pct,
                "sharpe_ratio": float(m.sharpe_ratio or 0),
                "max_drawdown_pct": max_dd_pct,
                "ai_score": ai_score,
                "volatility_pct": volatility_pct,
                "total_trades": m.total_trades or 0,
                "decisions_count": m.decisions_count or 0,
                "last_decision_at": m.last_decision_at,
                "is_active": m.is_active,
            })

        # Sort by AI score descending
        entries.sort(key=lambda e: e["ai_score"], reverse=True)

        # Assign ranks
        for i, e in enumerate(entries):
            e["rank"] = i + 1
            e["medal"] = ["🥇", "🥈", "🥉"][i] if i < 3 else f"#{i+1}"

        return {
            "entries": entries,
            "total_count": len(entries),
            "updated_at": datetime.now(timezone.utc),
        }

    async def get_comparison_chart(self, org_id: int) -> dict:
        """Get multi-series comparison chart data across all active managers."""
        managers = await self.get_managers(org_id)
        active = [m for m in managers if m.is_active]
        colors = ["#4CAF50", "#2196F3", "#FF9800", "#E91E63", "#9C27B0",
                   "#00BCD4", "#FF5722", "#607D8B", "#795548", "#CDDC39"]

        series = []
        for i, m in enumerate(active[:10]):  # Max 10 series
            # Get performance snapshots for this manager's portfolio
            chart_data = []
            if m.assigned_portfolio_id:
                try:
                    snapshots = await self._get_portfolio_snapshots(m.assigned_portfolio_id)
                    chart_data = [
                        {"date": s["date"], "value": s["value"]}
                        for s in snapshots
                    ]
                except Exception as e:
                    logger.warning(f"Failed to load chart data for manager {m.id}: {e}")

            series.append({
                "manager_id": m.id,
                "manager_name": m.name,
                "model_name": m.model_name,
                "color": colors[i % len(colors)],
                "data": chart_data if chart_data else self._mock_chart_data(),
            })

        return {
            "series": series,
            "benchmark_series": None,  # SPY comparison in Phase 3
        }

    async def _get_portfolio_snapshots(self, portfolio_id: int) -> list[dict]:
        """Get performance snapshot dates and values."""
        result = await self.db.execute(
            select(PortfolioPerformanceSnapshot)
            .where(PortfolioPerformanceSnapshot.portfolio_id == portfolio_id)
            .order_by(PortfolioPerformanceSnapshot.snapshot_date.asc())
        )
        snapshots = list(result.scalars().all())
        return [
            {
                "date": s.snapshot_date.strftime("%Y-%m-%d") if s.snapshot_date else "",
                "value": float(s.total_value or 0),
            }
            for s in snapshots
        ]

    def _mock_chart_data(self) -> list[dict]:
        """Generate mock chart data for Phase 1 testing."""
        import random
        data = []
        base = 100000.0
        for day in range(30):
            date = (datetime.now(timezone.utc) - timedelta(days=29 - day)).strftime("%Y-%m-%d")
            base += base * random.uniform(-0.02, 0.03)
            data.append({"date": date, "value": round(base, 2)})
        return data

    # ── Prompt Templates ─────────────────────────────────────

    @staticmethod
    def _default_system_prompt(manager_name: str) -> str:
        return (
            f"You are {manager_name}, a professional AI portfolio manager. "
            "Your mission is to manage client portfolios with the goal of "
            "consistently beating the SPY (S&P 500 ETF) benchmark return.\n\n"
            "Core principles:\n"
            "1. Risk management > return chasing\n"
            "2. Diversification is the only free lunch\n"
            "3. Don't predict — weigh probabilities\n"
            "4. Discipline > gut feeling\n"
            "5. Every decision must include reasoning\n\n"
            "Output format: You MUST respond in JSON only with fields:\n"
            "action, reasoning, risk_assessment, target_weights, benchmark_analysis"
        )

    def _build_decision_prompt(
        self, manager: AiManager, portfolio_state: dict
    ) -> str:
        """Build the user prompt with portfolio context."""
        prompt = "━━━ AI Fund Manager Decision Cycle ━━━\n\n"
        prompt += f"Manager: {manager.name}\n"
        prompt += f"Model: {manager.model_name}\n"
        prompt += f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n"

        if portfolio_state:
            prompt += "━━━ Portfolio Status ━━━\n"
            prompt += f"Portfolio: {portfolio_state.get('name', 'N/A')}\n"
            prompt += f"Total Value: ${portfolio_state.get('total_value', 0):,.2f}\n"
            prompt += f"Total P&L: ${portfolio_state.get('total_pnl', 0):,.2f} "
            prompt += f"({portfolio_state.get('total_pnl_pct', 0):.2f}%)\n"
            if portfolio_state.get("last_rebalanced_at"):
                prompt += f"Last Rebalanced: {portfolio_state['last_rebalanced_at']}\n"

        prompt += "\n━━━ Market Context (Phase 1 — Simulated) ━━━\n"
        prompt += "SPY: $556.30 (+0.45%) | VIX: 14.32\n"
        prompt += "Market regime: Bullish with caution signals\n\n"
        prompt += "Based on the above, what investment decision do you recommend?\n"
        prompt += "Respond in JSON format with: action, reasoning, risk_assessment, "
        prompt += "target_weights, benchmark_analysis, trades_to_execute"

        return prompt
