"""Portfolio management service — all business logic for portfolio CRUD, holdings, rebalancing, sync, and performance."""

import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portfolio import (
    Portfolio,
    PortfolioHolding,
    PortfolioRebalanceOrder,
    PortfolioPerformanceSnapshot,
    PortfolioStatus,
    OrderSide,
    OrderStatus,
    RebalanceMethod,
    OrderType,
)
from app.models.broker_connection import BrokerConnection
from app.services.broker_service import resolve_adapter, get_active_connections

logger = logging.getLogger(__name__)


class PortfolioError(Exception):
    pass


class PortfolioNotFound(PortfolioError):
    pass


class HoldingNotFound(PortfolioError):
    pass


# ── Helper ──────────────────────────────────────────────────


def _round2(val: Decimal) -> Decimal:
    return Decimal(str(val)).quantize(Decimal("0.01"))


def _round4(val: Decimal) -> Decimal:
    return Decimal(str(val)).quantize(Decimal("0.0001"))


def _pct(val: Decimal) -> Decimal:
    """Convert a weight fraction to percentage with 4 decimal places."""
    return _round4(val * Decimal("100"))


# ── Portfolio Manager ───────────────────────────────────────


class PortfolioManager:
    """Central service for all portfolio management operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Portfolio CRUD ──────────────────────────────────────

    async def create_portfolio(
        self, org_id: int, user_id: int, data: dict
    ) -> Portfolio:
        """Create a new portfolio."""
        portfolio = Portfolio(
            user_id=user_id,
            org_id=org_id,
            name=data["name"],
            description=data.get("description"),
            base_currency=data.get("base_currency", "USD"),
            broker_connection_id=data.get("broker_connection_id"),
            broker_sub_account_id=data.get("broker_sub_account_id"),
            rebalance_method=data.get("rebalance_method", RebalanceMethod.WEIGHT_ONLY),
            rebalance_order_type=data.get("rebalance_order_type", OrderType.MARKET),
            drift_threshold_pct=Decimal(str(data.get("drift_threshold_pct", 5.00))),
            cash_reserve_pct=Decimal(str(data.get("cash_reserve_pct", 0.00))),
            auto_rebalance_enabled=bool(data.get("auto_rebalance_enabled", False)),
            rebalance_frequency=data.get("rebalance_frequency", "drift_only"),
        )
        self.db.add(portfolio)
        await self.db.commit()
        await self.db.refresh(portfolio)
        logger.info(f"Portfolio created: id={portfolio.id}, name={portfolio.name}")
        return portfolio

    async def get_portfolios(self, org_id: int, user_id: int) -> list[Portfolio]:
        """Get all portfolios for an org (optionally filtered by user)."""
        query = select(Portfolio).where(
            Portfolio.org_id == org_id,
            Portfolio.status != PortfolioStatus.ARCHIVED,
        )
        result = await self.db.execute(query.order_by(Portfolio.updated_at.desc()))
        return list(result.scalars().all())

    async def get_portfolio(self, org_id: int, portfolio_id: int) -> Portfolio:
        """Get a single portfolio by id, scoped to org."""
        result = await self.db.execute(
            select(Portfolio).where(
                Portfolio.id == portfolio_id,
                Portfolio.org_id == org_id,
            )
        )
        portfolio = result.scalar_one_or_none()
        if portfolio is None:
            raise PortfolioNotFound(f"Portfolio {portfolio_id} not found")
        return portfolio

    async def update_portfolio(
        self, org_id: int, portfolio_id: int, data: dict
    ) -> Portfolio:
        """Update portfolio fields."""
        portfolio = await self.get_portfolio(org_id, portfolio_id)

        for field in (
            "name", "description", "base_currency", "broker_connection_id",
            "broker_sub_account_id", "status", "rebalance_method", "rebalance_order_type",
            "rebalance_frequency",
        ):
            if field in data:
                setattr(portfolio, field, data[field])

        for num_field in ("drift_threshold_pct", "cash_reserve_pct"):
            if num_field in data and data[num_field] is not None:
                setattr(portfolio, num_field, Decimal(str(data[num_field])))

        if "auto_rebalance_enabled" in data:
            portfolio.auto_rebalance_enabled = bool(data["auto_rebalance_enabled"])

        await self.db.commit()
        await self.db.refresh(portfolio)
        return portfolio

    async def delete_portfolio(self, org_id: int, portfolio_id: int) -> bool:
        """Soft-delete (archive) a portfolio."""
        portfolio = await self.get_portfolio(org_id, portfolio_id)
        portfolio.status = PortfolioStatus.ARCHIVED
        await self.db.commit()
        return True

    # ── Holdings CRUD ───────────────────────────────────────

    async def get_holdings(self, portfolio_id: int) -> list[PortfolioHolding]:
        """Get all active holdings for a portfolio."""
        result = await self.db.execute(
            select(PortfolioHolding).where(
                PortfolioHolding.portfolio_id == portfolio_id,
                PortfolioHolding.is_active == True,
            )
        )
        return list(result.scalars().all())

    async def add_holding(
        self, portfolio_id: int, data: dict
    ) -> PortfolioHolding:
        """Add a new holding to a portfolio."""
        holding = PortfolioHolding(
            portfolio_id=portfolio_id,
            symbol=data["symbol"].upper(),
            asset_type=data.get("asset_type", "stock"),
            market=data.get("market", "US"),
            currency=data.get("currency", "USD"),
            target_weight_pct=Decimal(str(data["target_weight_pct"])),
            current_shares=Decimal(str(data.get("current_shares", 0))),
            avg_cost=Decimal(str(data.get("avg_cost", 0))),
            current_price=Decimal(str(data.get("current_price", 0))),
            notes=data.get("notes"),
        )
        self._recalc_holding_values(holding)
        self.db.add(holding)
        await self.db.commit()
        await self.db.refresh(holding)
        return holding

    async def update_holding(
        self, holding_id: int, data: dict
    ) -> PortfolioHolding:
        """Update a holding."""
        result = await self.db.execute(
            select(PortfolioHolding).where(PortfolioHolding.id == holding_id)
        )
        holding = result.scalar_one_or_none()
        if holding is None:
            raise HoldingNotFound(f"Holding {holding_id} not found")

        for field in ("target_weight_pct", "current_shares", "avg_cost", "current_price",
                       "market_value", "unrealized_pnl", "unrealized_pnl_pct", "notes", "is_active"):
            if field in data and data[field] is not None:
                if field in ("target_weight_pct", "current_shares", "avg_cost",
                             "current_price", "market_value", "unrealized_pnl", "unrealized_pnl_pct"):
                    setattr(holding, field, Decimal(str(data[field])))
                else:
                    setattr(holding, field, data[field])

        # Recalc if price or shares changed
        if "current_price" in data or "current_shares" in data or "avg_cost" in data:
            self._recalc_holding_values(holding)

        await self.db.commit()
        await self.db.refresh(holding)
        return holding

    async def remove_holding(self, holding_id: int) -> bool:
        """Soft-delete a holding."""
        result = await self.db.execute(
            select(PortfolioHolding).where(PortfolioHolding.id == holding_id)
        )
        holding = result.scalar_one_or_none()
        if holding is None:
            raise HoldingNotFound(f"Holding {holding_id} not found")
        holding.is_active = False
        await self.db.commit()
        return True

    async def batch_update_holdings(
        self, portfolio_id: int, holdings_data: list[dict]
    ) -> list[PortfolioHolding]:
        """Replace all active holdings with a new set (create/update/remove as needed)."""
        existing = await self.get_holdings(portfolio_id)
        existing_map = {h.symbol: h for h in existing}
        incoming_symbols = {h["symbol"].upper() for h in holdings_data}

        # Deactivate removed holdings
        for h in existing:
            if h.symbol not in incoming_symbols:
                h.is_active = False

        # Create or update
        updated = []
        for hd in holdings_data:
            symbol = hd["symbol"].upper()
            if symbol in existing_map:
                h = existing_map[symbol]
                for field in ("target_weight_pct", "current_shares", "avg_cost",
                              "current_price", "notes"):
                    if field in hd and hd[field] is not None:
                        if field in ("target_weight_pct", "current_shares", "avg_cost", "current_price"):
                            setattr(h, field, Decimal(str(hd[field])))
                        else:
                            setattr(h, field, hd[field])
                h.is_active = True
                self._recalc_holding_values(h)
                updated.append(h)
            else:
                new_h = PortfolioHolding(
                    portfolio_id=portfolio_id,
                    symbol=symbol,
                    asset_type=hd.get("asset_type", "stock"),
                    market=hd.get("market", "US"),
                    currency=hd.get("currency", "USD"),
                    target_weight_pct=Decimal(str(hd["target_weight_pct"])),
                    current_shares=Decimal(str(hd.get("current_shares", 0))),
                    avg_cost=Decimal(str(hd.get("avg_cost", 0))),
                    current_price=Decimal(str(hd.get("current_price", 0))),
                    notes=hd.get("notes"),
                )
                self._recalc_holding_values(new_h)
                self.db.add(new_h)
                updated.append(new_h)

        await self.db.commit()
        for h in updated:
            await self.db.refresh(h)
        return updated

    # ── Holdings calculations ───────────────────────────────

    def _recalc_holding_values(self, holding: PortfolioHolding) -> None:
        """Recalculate market_value, unrealized_pnl, unrealized_pnl_pct for a holding."""
        shares = holding.current_shares or Decimal("0")
        price = holding.current_price or Decimal("0")
        cost = holding.avg_cost or Decimal("0")

        holding.market_value = _round2(shares * price)
        holding.unrealized_pnl = _round2(shares * (price - cost))
        if cost > 0 and shares > 0:
            holding.unrealized_pnl_pct = _pct((price - cost) / cost)
        else:
            holding.unrealized_pnl_pct = Decimal("0")

    # ── Rebalance ───────────────────────────────────────────

    async def calculate_rebalance_plan(
        self, portfolio_id: int, org_id: int = None
    ) -> dict:
        """Calculate a rebalance plan (preview) for a portfolio."""
        if org_id:
            portfolio = await self.get_portfolio(org_id, portfolio_id)
        else:
            # Fallback: get by id only (used when org check already done by caller)
            result = await self.db.execute(
                select(Portfolio).where(Portfolio.id == portfolio_id)
            )
            portfolio = result.scalar_one_or_none()
            if portfolio is None:
                raise PortfolioNotFound(f"Portfolio {portfolio_id} not found")

        holdings = await self.get_holdings(portfolio_id)

        total_value = portfolio.total_value or Decimal("0")
        if total_value == 0:
            total_value = sum(h.market_value or Decimal("0") for h in holdings)
            if total_value == 0:
                total_value = portfolio.total_capital or Decimal("100000")

        cash_reserve_pct = portfolio.cash_reserve_pct or Decimal("0")
        cash_reserve = _round2(total_value * cash_reserve_pct / Decimal("100"))
        investable_value = total_value - cash_reserve

        orders = []
        total_cost = Decimal("0")

        # Normalize weights
        total_weight = sum(h.target_weight_pct or Decimal("0") for h in holdings)
        if total_weight == 0:
            total_weight = Decimal("100")

        for h in holdings:
            tw_pct = h.target_weight_pct or Decimal("0")
            normalized_weight = tw_pct / total_weight * Decimal("100") if total_weight > 0 else Decimal("0")
            current_value = h.market_value or Decimal("0")
            target_value = _round2(investable_value * normalized_weight / Decimal("100"))
            diff_value = target_value - current_value
            current_weight_pct = _pct(current_value / investable_value) if investable_value > 0 else Decimal("0")

            if abs(diff_value) < Decimal("0.01"):
                continue

            side = "buy" if diff_value > 0 else "sell"
            price = h.current_price or Decimal("1")
            diff_shares = _round4(abs(diff_value) / price) if price > 0 else Decimal("0")

            orders.append({
                "symbol": h.symbol,
                "side": side,
                "current_weight_pct": current_weight_pct,
                "target_weight_pct": _pct(normalized_weight / Decimal("100")),
                "current_value": current_value,
                "target_value": target_value,
                "diff_value": abs(diff_value),
                "diff_shares": diff_shares,
                "estimated_price": price,
            })
            total_cost += abs(diff_value)

        return {
            "portfolio_id": portfolio.id,
            "portfolio_name": portfolio.name,
            "total_value": total_value,
            "cash_reserve": cash_reserve,
            "investable_value": investable_value,
            "total_cost_estimate": _round2(total_cost),
            "orders": orders,
        }

    async def execute_rebalance(
        self, portfolio_id: int, user_id: int, order_type: str = "market", org_id: int = None
    ) -> list[PortfolioRebalanceOrder]:
        """Execute a rebalance: create orders with sells first, then buys."""
        if org_id:
            portfolio = await self.get_portfolio(org_id, portfolio_id)
        else:
            result = await self.db.execute(
                select(Portfolio).where(Portfolio.id == portfolio_id)
            )
            portfolio = result.scalar_one_or_none()
            if portfolio is None:
                raise PortfolioNotFound(f"Portfolio {portfolio_id} not found")
        plan = await self.calculate_rebalance_plan(portfolio_id)
        group_id = str(uuid4())
        created_orders = []

        # Sells first
        sell_orders = [o for o in plan["orders"] if o["side"] == "sell"]
        buy_orders = [o for o in plan["orders"] if o["side"] == "buy"]

        for idx, order in enumerate(sell_orders + buy_orders):
            ot = OrderType(order_type) if order_type in ("market", "limit") else OrderType.MARKET
            limit_price = None
            if ot == OrderType.LIMIT:
                tolerance = portfolio.limit_price_tolerance_pct or Decimal("0.50")
                limit_price = order["estimated_price"] * (Decimal("1") + tolerance / Decimal("100"))

            db_order = PortfolioRebalanceOrder(
                portfolio_id=portfolio_id,
                user_id=user_id,
                org_id=portfolio.org_id,
                rebalance_group_id=group_id,
                sequence=idx,
                symbol=order["symbol"],
                side=OrderSide.BUY if order["side"] == "buy" else OrderSide.SELL,
                order_type=ot,
                target_qty=order["diff_shares"],
                target_value=order["diff_value"],
                limit_price=limit_price,
                status=OrderStatus.PENDING,
            )
            self.db.add(db_order)
            created_orders.append(db_order)

        # Update portfolio stats
        portfolio.last_rebalanced_at = datetime.now(timezone.utc)
        await self._recalc_portfolio_stats(portfolio_id)

        await self.db.commit()
        for o in created_orders:
            await self.db.refresh(o)
        return created_orders

    # ── Sync from Broker ────────────────────────────────────

    async def sync_from_broker(self, portfolio_id: int, org_id: int = None) -> dict:
        """Sync current portfolio holdings data from the linked broker connection."""
        if org_id:
            portfolio = await self.get_portfolio(org_id, portfolio_id)
        else:
            result = await self.db.execute(
                select(Portfolio).where(Portfolio.id == portfolio_id)
            )
            portfolio = result.scalar_one_or_none()
            if portfolio is None:
                raise PortfolioNotFound(f"Portfolio {portfolio_id} not found")

        if not portfolio.broker_connection_id:
            # No broker — just recalc from current data
            await self._recalc_portfolio_stats(portfolio_id)
            return {"status": "no_broker", "message": "No broker connection linked"}

        # Get broker connection
        result = await self.db.execute(
            select(BrokerConnection).where(
                BrokerConnection.id == portfolio.broker_connection_id,
                BrokerConnection.is_active == True,
            )
        )
        conn = result.scalar_one_or_none()
        if conn is None:
            return {"status": "error", "message": "Broker connection not found or inactive"}

        try:
            adapter = await resolve_adapter(conn)
            positions = await adapter.get_positions()

            # Update holdings from broker positions
            holdings = await self.get_holdings(portfolio_id)
            holdings_by_symbol = {h.symbol: h for h in holdings}

            for pos in positions:
                symbol = pos.get("symbol", "").upper()
                if symbol in holdings_by_symbol:
                    h = holdings_by_symbol[symbol]
                    h.current_shares = Decimal(str(pos.get("qty", h.current_shares or 0)))
                    h.current_price = Decimal(str(pos.get("current_price", h.current_price or 0)))
                    h.avg_cost = Decimal(str(pos.get("avg_cost", h.avg_cost or 0)))
                    self._recalc_holding_values(h)

            await self._recalc_portfolio_stats(portfolio_id)
            portfolio.last_synced_at = datetime.now(timezone.utc)
            await self.db.commit()

            # Create a performance snapshot
            await self._record_performance_snapshot(portfolio_id)

            return {"status": "success", "positions_synced": len(positions)}

        except Exception as e:
            logger.error(f"Sync failed for portfolio {portfolio_id}: {e}")
            return {"status": "error", "message": str(e)}

    async def _recalc_portfolio_stats(self, portfolio_id: int) -> None:
        """Recalculate aggregated stats on the portfolio from its holdings."""
        result = await self.db.execute(
            select(Portfolio).where(Portfolio.id == portfolio_id)
        )
        portfolio = result.scalar_one_or_none()
        if portfolio is None:
            return

        holdings = await self.get_holdings(portfolio_id)
        total_value = sum(h.market_value or Decimal("0") for h in holdings)
        total_cost = sum((h.avg_cost or Decimal("0")) * (h.current_shares or Decimal("0")) for h in holdings)

        portfolio.total_value = _round2(total_value)
        portfolio.total_cost = _round2(total_cost)
        portfolio.total_pnl = _round2(total_value - total_cost)
        if total_cost > 0:
            portfolio.total_pnl_pct = _pct((total_value - total_cost) / total_cost)
        else:
            portfolio.total_pnl_pct = Decimal("0")

    async def _record_performance_snapshot(self, portfolio_id: int) -> None:
        """Record today's performance snapshot for charting."""
        result = await self.db.execute(
            select(Portfolio).where(Portfolio.id == portfolio_id)
        )
        portfolio = result.scalar_one_or_none()
        if portfolio is None:
            return
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        # Check if snapshot already exists for today
        result = await self.db.execute(
            select(PortfolioPerformanceSnapshot).where(
                PortfolioPerformanceSnapshot.portfolio_id == portfolio_id,
                PortfolioPerformanceSnapshot.snapshot_date >= today,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.total_value = portfolio.total_value
            existing.total_pnl = portfolio.total_pnl
            existing.total_return_pct = portfolio.total_pnl_pct
            return

        # Get yesterday's snapshot for daily P&L
        yesterday = today - timedelta(days=1)
        result = await self.db.execute(
            select(PortfolioPerformanceSnapshot).where(
                PortfolioPerformanceSnapshot.portfolio_id == portfolio_id,
                PortfolioPerformanceSnapshot.snapshot_date >= yesterday,
                PortfolioPerformanceSnapshot.snapshot_date < today,
            )
            .order_by(PortfolioPerformanceSnapshot.snapshot_date.desc())
            .limit(1)
        )
        prev = result.scalar_one_or_none()
        prev_value = prev.total_value if prev else portfolio.total_value

        daily_pnl = (portfolio.total_value or Decimal("0")) - prev_value
        daily_return_pct = _pct(daily_pnl / prev_value) if prev_value > 0 else Decimal("0")

        snapshot = PortfolioPerformanceSnapshot(
            portfolio_id=portfolio_id,
            org_id=portfolio.org_id,
            snapshot_date=today,
            total_value=portfolio.total_value or Decimal("0"),
            total_pnl=portfolio.total_pnl or Decimal("0"),
            total_return_pct=portfolio.total_pnl_pct or Decimal("0"),
            daily_pnl=daily_pnl,
            daily_return_pct=daily_return_pct,
        )
        self.db.add(snapshot)

    # ── Performance ─────────────────────────────────────────

    async def get_performance(self, portfolio_id: int, days: int = 30) -> list[dict]:
        """Get performance snapshot data for charting."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.db.execute(
            select(PortfolioPerformanceSnapshot)
            .where(
                PortfolioPerformanceSnapshot.portfolio_id == portfolio_id,
                PortfolioPerformanceSnapshot.snapshot_date >= cutoff,
            )
            .order_by(PortfolioPerformanceSnapshot.snapshot_date.asc())
        )
        snapshots = result.scalars().all()
        return [
            {
                "date": s.snapshot_date.strftime("%Y-%m-%d") if s.snapshot_date else "",
                "total_value": s.total_value,
                "daily_pnl": s.daily_pnl,
                "daily_return_pct": s.daily_return_pct,
                "total_pnl": s.total_pnl,
                "total_return_pct": s.total_return_pct,
            }
            for s in snapshots
        ]

    async def get_allocation(self, portfolio_id: int) -> list[dict]:
        """Get current allocation vs target for pie chart."""
        holdings = await self.get_holdings(portfolio_id)
        total_value = sum(h.market_value or Decimal("0") for h in holdings)
        if total_value == 0:
            total_value = Decimal("1")  # avoid div by zero

        colors = [
            "#4CAF50", "#2196F3", "#FF9800", "#E91E63", "#9C27B0",
            "#00BCD4", "#FF5722", "#607D8B", "#795548", "#CDDC39",
        ]

        data = []
        for i, h in enumerate(holdings):
            cw_pct = _pct((h.market_value or Decimal("0")) / total_value)
            tw_pct = h.target_weight_pct or Decimal("0")
            drift = cw_pct - tw_pct
            data.append({
                "symbol": h.symbol,
                "current_weight_pct": cw_pct,
                "target_weight_pct": tw_pct,
                "market_value": h.market_value or Decimal("0"),
                "drift_pct": drift,
                "color": colors[i % len(colors)],
            })

        return data

    async def get_summary(self, org_id: int) -> dict:
        """Get aggregate summary of all portfolios for an org."""
        portfolios = await self.get_portfolios(org_id, 0)
        total_value = sum(p.total_value or Decimal("0") for p in portfolios)
        total_pnl = sum(p.total_pnl or Decimal("0") for p in portfolios)
        active_count = sum(1 for p in portfolios if p.status == PortfolioStatus.ACTIVE)

        total_pnl_pct = Decimal("0")
        total_cost = sum(p.total_cost or Decimal("0") for p in portfolios)
        if total_cost > 0:
            total_pnl_pct = _pct(total_pnl / total_cost)

        return {
            "total_portfolios": len(portfolios),
            "total_value": _round2(total_value),
            "total_pnl": _round2(total_pnl),
            "total_pnl_pct": total_pnl_pct,
            "active_count": active_count,
        }
