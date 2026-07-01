"""Portfolio management service — all business logic for portfolio CRUD, holdings, rebalancing, sync, and performance."""

import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_DOWN
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
from app.services.market_config import get_lot_size, get_min_units, round_to_lot

logger = logging.getLogger(__name__)


class PortfolioError(Exception):
    pass


class PortfolioNotFound(PortfolioError):
    pass


class HoldingNotFound(PortfolioError):
    pass


class InsufficientCapitalError(PortfolioError):
    """Raised when a holding's target weight is too small to buy even 1 lot."""
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
        market = data.get("market", "US")
        symbol = data["symbol"].upper()
        lot_size = data.get("lot_size")
        if lot_size is None:
            lot_size = get_lot_size(market, symbol)
        holding = PortfolioHolding(
            portfolio_id=portfolio_id,
            symbol=symbol,
            asset_type=data.get("asset_type", "stock"),
            market=market,
            currency=data.get("currency", "USD"),
            lot_size=lot_size,
            target_weight_pct=Decimal(str(data["target_weight_pct"])),
            current_shares=Decimal(str(data.get("current_shares", 0))),
            avg_cost=Decimal(str(data.get("avg_cost", 0))),
            current_price=Decimal(str(data.get("current_price", 0))),
            notes=data.get("notes"),
        )
        # Validate minimum purchase unit before saving
        await self._validate_minimum_unit(
            portfolio_id, holding.target_weight_pct,
            holding.current_price, lot_size,
            holding.symbol, market
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
                       "market_value", "unrealized_pnl", "unrealized_pnl_pct", "lot_size",
                       "notes", "is_active"):
            if field in data and data[field] is not None:
                if field in ("target_weight_pct", "current_shares", "avg_cost",
                             "current_price", "market_value", "unrealized_pnl", "unrealized_pnl_pct"):
                    setattr(holding, field, Decimal(str(data[field])))
                else:
                    setattr(holding, field, data[field])

        # Recalc if price or shares changed
        if "current_price" in data or "current_shares" in data or "avg_cost" in data:
            self._recalc_holding_values(holding)

        # Validate minimum unit when target weight or price changes
        if "target_weight_pct" in data or "current_price" in data:
            tw = Decimal(str(data.get("target_weight_pct", holding.target_weight_pct or 0)))
            price = Decimal(str(data.get("current_price", holding.current_price or 0)))
            ls = int(data.get("lot_size", holding.lot_size or 1))
            await self._validate_minimum_unit(
                holding.portfolio_id, tw, price, ls,
                holding.symbol, holding.market
            )

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
                market = hd.get("market", "US")
                lot_size = hd.get("lot_size")
                if lot_size is None:
                    lot_size = get_lot_size(market, symbol)
                new_h = PortfolioHolding(
                    portfolio_id=portfolio_id,
                    symbol=symbol,
                    asset_type=hd.get("asset_type", "stock"),
                    market=market,
                    currency=hd.get("currency", "USD"),
                    lot_size=lot_size,
                    target_weight_pct=Decimal(str(hd["target_weight_pct"])),
                    current_shares=Decimal(str(hd.get("current_shares", 0))),
                    avg_cost=Decimal(str(hd.get("avg_cost", 0))),
                    current_price=Decimal(str(hd.get("current_price", 0))),
                    notes=hd.get("notes"),
                )
                self._recalc_holding_values(new_h)
                # Validate minimum unit for new holdings
                tw = Decimal(str(hd["target_weight_pct"]))
                price = Decimal(str(hd.get("current_price", 0)))
                lot_sz = int(lot_size or 1)
                await self._validate_minimum_unit(
                    portfolio_id, tw, price, lot_sz, symbol, market
                )
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

    async def _validate_minimum_unit(
        self, portfolio_id: int, target_weight_pct: Decimal,
        current_price: Decimal, lot_size: int,
        symbol: str, market: str
    ) -> None:
        """Validate that the target weight can buy at least 1 lot.

        Raises InsufficientCapitalError with a helpful message if not.
        """
        if current_price is None or current_price <= 0 or lot_size <= 0:
            return  # Can't validate without price

        result = await self.db.execute(
            select(Portfolio).where(Portfolio.id == portfolio_id)
        )
        portfolio = result.scalar_one_or_none()
        if portfolio is None:
            return

        total_value = portfolio.total_value or Decimal("0")
        if total_value == 0:
            holdings = await self.get_holdings(portfolio_id)
            total_value = sum(h.market_value or Decimal("0") for h in holdings)
        if total_value <= 0:
            return  # No portfolio value yet, can't validate

        target_value = _round2(total_value * target_weight_pct / Decimal("100"))
        min_needed = _round2(current_price * Decimal(str(lot_size)))

        if target_value < min_needed:
            min_pct = (min_needed / total_value * Decimal("100")).quantize(Decimal("0.01"))
            raise InsufficientCapitalError(
                f"{symbol}: Minimum {lot_size} share(s) required (${float(min_needed):,.2f}). "
                f"With {market} lot rules, you need at least {min_pct}% of "
                f"${float(total_value):,.2f} total capital (currently {target_weight_pct}%). "
                f"Increase the target weight or reduce total portfolio holdings."
            )

    # ── Rebalance ───────────────────────────────────────────

    async def calculate_rebalance_plan(
        self, portfolio_id: int, org_id: int = None
    ) -> dict:
        """Calculate a rebalance plan (preview) for a portfolio.

        Shares are rounded to valid lot sizes per market rules:
        - US: 1 share
        - HK: lot_size varies per stock (default 100)
        - CN: 100 shares
        - JP: 100 shares
        - CRYPTO: varies per symbol (e.g. BTC=0.00001)

        Orders where the calculated quantity is less than the minimum
        tradable unit are skipped (not enough capital).
        Sells always round *up* to the nearest whole lot to avoid
        leaving fractional/incomplete positions.
        """
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

            # ── Lot-aware quantity calculation ──────────────
            lot_size = h.lot_size or 1
            market = h.market or "US"
            min_units = get_min_units(market, h.symbol)

            # Raw number of shares before lot rounding
            raw_shares = abs(diff_value) / price if price > 0 else Decimal("0")

            if market.upper() == "CRYPTO":
                # Crypto: round down to minimum unit increment
                if min_units > 0 and raw_shares > 0:
                    valid_shares = (raw_shares / min_units).quantize(Decimal("1"), rounding=ROUND_DOWN) * min_units
                else:
                    valid_shares = raw_shares
            else:
                # Integer-lot markets: round to nearest whole lot
                # Buys: round down (floor) — don't exceed available capital
                # Sells: round up (ceil) — must clear the full position
                if side == "sell":
                    valid_shares = round_to_lot(raw_shares, lot_size, round_down=False)
                else:
                    valid_shares = round_to_lot(raw_shares, lot_size, round_down=True)

            # Re-calculate actual value using rounded shares
            valid_value = _round2(valid_shares * price)

            # Skip if the rounded quantity is less than the minimum tradable unit
            if valid_shares < min_units:
                logger.debug(
                    f"Skipping {h.symbol}: rounded {valid_shares} < min_units {min_units} "
                    f"(raw={raw_shares}, lot_size={lot_size})"
                )
                continue

            # Skip if the rounded shares haven't changed from current holdings
            current_shares = h.current_shares or Decimal("0")
            if side == "buy" and valid_shares <= current_shares:
                continue
            if side == "sell" and valid_shares <= Decimal("0"):
                continue

            orders.append({
                "symbol": h.symbol,
                "market": market,
                "side": side,
                "current_weight_pct": current_weight_pct,
                "target_weight_pct": _pct(normalized_weight / Decimal("100")),
                "current_value": current_value,
                "target_value": target_value,
                "diff_value": valid_value,
                "diff_shares": valid_shares,
                "estimated_price": price,
                "lot_size": lot_size,
                "min_units": min_units,
            })
            total_cost += valid_value

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
        """Execute a rebalance: submit orders to the broker, then store results.

        For each order in the calculated plan:
          1. If a broker is linked, submit via the broker adapter's place_order()
          2. Store the result (broker_order_id, status, etc.) in the local DB
          3. If no broker or broker submission fails, store as PENDING for manual handling

        Uses lot-aware share quantities from the calculated plan.
        Orders whose rounded quantity is below the minimum tradable unit
        are silently skipped.
        """
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

        # Resolve broker adapter if linked
        broker_adapter = None
        if portfolio.broker_connection_id:
            try:
                from sqlalchemy import select
                from app.models.broker_connection import BrokerConnection
                result = await self.db.execute(
                    select(BrokerConnection).where(
                        BrokerConnection.id == portfolio.broker_connection_id,
                        BrokerConnection.is_active == True,
                    )
                )
                conn = result.scalar_one_or_none()
                if conn:
                    from app.services.broker_service import resolve_adapter
                    broker_adapter = await resolve_adapter(conn)
                    # Ensure connected
                    if not await broker_adapter.test_connection():
                        logger.warning("Portfolio %d: broker %s not reachable, orders will be PENDING", portfolio_id, conn.name)
                        broker_adapter = None
            except Exception as e:
                logger.warning("Portfolio %d: broker resolve error: %s", portfolio_id, e)

        # Sells first, then buys
        sell_orders_nested = [o for o in plan["orders"] if o["side"] == "sell"]
        buy_orders_nested = [o for o in plan["orders"] if o["side"] == "buy"]

        for idx, order in enumerate(sell_orders_nested + buy_orders_nested):
            # Safety check: skip if rounded shares < min units
            min_units = order.get("min_units", Decimal("1"))
            if order["diff_shares"] < min_units:
                logger.info(
                    f"Skipping order for {order['symbol']}: "
                    f"{order['diff_shares']} < min_units {min_units}"
                )
                continue

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

            # Submit to broker if adapter available
            if broker_adapter:
                try:
                    broker_order = {
                        "symbol": order["symbol"],
                        "side": order["side"].upper(),
                        "type": order_type,
                        "qty": int(order["diff_shares"]),
                        "time_in_force": "DAY",
                    }
                    if limit_price:
                        broker_order["price"] = float(limit_price)

                    broker_result = await broker_adapter.place_order(broker_order)
                    # Extract broker order ID
                    broker_order_id = (
                        broker_result.get("broker_order_id")
                        or broker_result.get("order_id")
                        or broker_result.get("client_order_id")
                        or broker_result.get("data", {}).get("order_id")
                        or broker_result.get("data", {}).get("client_order_id")
                    )
                    if broker_order_id:
                        db_order.broker_order_id = broker_order_id
                        db_order.status = OrderStatus.SUBMITTED
                        logger.info("Portfolio %d: submitted %s %s -> broker_id=%s",
                                    portfolio_id, order["side"], order["symbol"], broker_order_id)
                    else:
                        # Order submitted but no ID returned - check for errors
                        error_msg = broker_result.get("msg", broker_result.get("message", str(broker_result)[:200]))
                        if "success" in broker_result and not broker_result["success"]:
                            db_order.error_message = error_msg
                        logger.warning("Portfolio %d: %s %s broker result: %s",
                                       portfolio_id, order["side"], order["symbol"], error_msg)
                except Exception as e:
                    db_order.error_message = f"Broker submit error: {e}"
                    logger.error("Portfolio %d: %s %s submit failed: %s",
                                 portfolio_id, order["side"], order["symbol"], e)

            self.db.add(db_order)
            created_orders.append(db_order)

        # Update portfolio stats
        portfolio.last_rebalanced_at = datetime.now(timezone.utc)
        await self._recalc_portfolio_stats(portfolio_id)

        await self.db.commit()
        for o in created_orders:
            await self.db.refresh(o)
        return created_orders

    # ── Rebalance Orders ─────────────────────────────────────

    async def get_rebalance_orders(
        self, portfolio_id: int, org_id: int
    ) -> list[PortfolioRebalanceOrder]:
        """Get all rebalance orders for a portfolio, most recent first.

        If the portfolio has a linked broker, also sync order statuses
        from the broker's API to keep local records up to date.
        """
        # First, try to sync statuses from broker
        try:
            result = await self.db.execute(
                select(Portfolio).where(
                    Portfolio.id == portfolio_id,
                    Portfolio.org_id == org_id,
                )
            )
            portfolio = result.scalar_one_or_none()
            if portfolio and portfolio.broker_connection_id:
                await self._sync_order_statuses_from_broker(portfolio)
        except Exception as e:
            logger.warning("Portfolio %d: broker order sync failed: %s", portfolio_id, e)

        # Now fetch from local DB
        result = await self.db.execute(
            select(PortfolioRebalanceOrder)
            .where(
                PortfolioRebalanceOrder.portfolio_id == portfolio_id,
                PortfolioRebalanceOrder.org_id == org_id,
            )
            .order_by(PortfolioRebalanceOrder.created_at.desc())
        )
        return list(result.scalars().all())

    async def _sync_order_statuses_from_broker(
        self, portfolio: Portfolio
    ) -> None:
        """Update local rebalance order statuses from the broker's API."""
        if not portfolio.broker_connection_id:
            return
        try:
            from app.models.broker_connection import BrokerConnection
            result = await self.db.execute(
                select(BrokerConnection).where(
                    BrokerConnection.id == portfolio.broker_connection_id,
                    BrokerConnection.is_active == True,
                )
            )
            conn = result.scalar_one_or_none()
            if not conn:
                return
            from app.services.broker_service import resolve_adapter
            adapter = await resolve_adapter(conn)
            if not await adapter.test_connection():
                return

            # Get open orders from broker
            try:
                open_orders = await adapter.get_open_orders()
            except (AttributeError, NotImplementedError):
                open_orders = []
            # Get order history from broker
            try:
                history = await adapter.get_order_history()
            except (AttributeError, NotImplementedError):
                history = []

            all_broker_orders = {}
            for o in (open_orders or []) + (history or []):
                oid = o.get("order_id") or o.get("client_order_id")
                if oid:
                    all_broker_orders[oid] = o

            if not all_broker_orders:
                return

            # Find matching local orders by broker_order_id
            broker_ids = list(all_broker_orders.keys())
            result = await self.db.execute(
                select(PortfolioRebalanceOrder).where(
                    PortfolioRebalanceOrder.broker_order_id.in_(broker_ids),
                )
            )
            local_orders = list(result.scalars().all())

            for local in local_orders:
                broker_data = all_broker_orders.get(local.broker_order_id)
                if not broker_data:
                    continue
                broker_status = (broker_data.get("status") or "").lower()
                # Map broker status to local OrderStatus
                status_map = {
                    "new": OrderStatus.PENDING,
                    "submitted": OrderStatus.SUBMITTED,
                    "partiallyfilled": OrderStatus.PARTIALLY_FILLED,
                    "filled": OrderStatus.FILLED,
                    "cancelled": OrderStatus.CANCELLED,
                    "canceled": OrderStatus.CANCELLED,
                    "rejected": OrderStatus.REJECTED,
                    "failed": OrderStatus.FAILED,
                }
                new_status = status_map.get(broker_status.replace(" ", ""))
                if new_status and new_status != local.status:
                    local.status = new_status
                # Update fill info
                filled = broker_data.get("filled_quantity") or broker_data.get("filled_qty")
                if filled:
                    local.filled_qty = Decimal(str(filled))
                avg_price = broker_data.get("avg_price") or broker_data.get("avg_fill_price")
                if avg_price:
                    local.avg_fill_price = Decimal(str(avg_price))
            if local_orders:
                await self.db.commit()
                logger.info("Portfolio %d: synced %d order statuses from broker", portfolio.id, len(local_orders))

        except Exception as e:
            logger.warning("Portfolio %d: broker sync error: %s", portfolio.id, e)

    # ── Bulk Order Actions ────────────────────────────────────

    async def cancel_orders(
        self, portfolio_id: int, order_ids: list[int], org_id: int
    ) -> dict:
        """Cancel one or more open orders.

        For each order:
          1. If a broker is linked and the order has a broker_order_id,
             request cancellation via the broker adapter.
          2. Update local DB status to CANCELLED.

        Returns a summary dict with success/failure counts.
        """
        result = await self.db.execute(
            select(PortfolioRebalanceOrder).where(
                PortfolioRebalanceOrder.id.in_(order_ids),
                PortfolioRebalanceOrder.portfolio_id == portfolio_id,
                PortfolioRebalanceOrder.org_id == org_id,
            )
        )
        orders = list(result.scalars().all())
        if not orders:
            return {"success": 0, "failed": 0, "errors": ["No orders found"]}

        # Resolve broker adapter if linked
        broker_adapter = await self._resolve_portfolio_broker(portfolio_id, org_id)

        succeeded = 0
        failed = 0
        errors = []

        for order in orders:
            if order.status in (OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED):
                errors.append(f"Order {order.id} ({order.symbol}): already {order.status.value}")
                failed += 1
                continue

            if broker_adapter and order.broker_order_id:
                try:
                    broker_result = await broker_adapter.cancel_order(order.broker_order_id)
                    if broker_result.get("success", True):
                        order.status = OrderStatus.CANCELLED
                        succeeded += 1
                    else:
                        # Broker cancel failed — still mark as cancelled locally
                        order.status = OrderStatus.CANCELLED
                        order.error_message = f"Broker cancel returned: {broker_result.get('msg', 'unknown')}"
                        succeeded += 1  # Local state is correct even if broker was flaky
                except Exception as e:
                    order.status = OrderStatus.CANCELLED
                    order.error_message = f"Cancel error: {e}"
                    succeeded += 1  # Force-cancelled locally
            else:
                # No broker: just update local status
                order.status = OrderStatus.CANCELLED
                succeeded += 1

        await self.db.commit()
        return {"success": succeeded, "failed": failed, "errors": errors if errors else None}

    async def replace_order(
        self, portfolio_id: int, order_id: int, org_id: int,
        new_order_type: str = "market", new_limit_price: Decimal = None,
    ) -> PortfolioRebalanceOrder:
        """Replace (cancel + replace) an existing open order.

        1. Cancel the old order at the broker (if linked + has broker_order_id).
        2. Place a new order with the updated type/price.
        3. Update the original order's status to CANCELLED.
        4. Create a new PortfolioRebalanceOrder record for the replacement.

        Returns the *new* order record.
        """
        result = await self.db.execute(
            select(PortfolioRebalanceOrder).where(
                PortfolioRebalanceOrder.id == order_id,
                PortfolioRebalanceOrder.portfolio_id == portfolio_id,
                PortfolioRebalanceOrder.org_id == org_id,
            )
        )
        old_order = result.scalar_one_or_none()
        if old_order is None:
            raise PortfolioNotFound(f"Order {order_id} not found")

        if old_order.status in (OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED):
            raise PortfolioError(
                f"Order {order_id} ({old_order.symbol}): cannot replace a {old_order.status.value} order"
            )

        broker_adapter = await self._resolve_portfolio_broker(portfolio_id, org_id)

        # 1. Cancel the old order at broker
        if broker_adapter and old_order.broker_order_id:
            try:
                cancel_result = await broker_adapter.cancel_order(old_order.broker_order_id)
                if not cancel_result.get("success", True):
                    logger.warning("Order %d: broker cancel returned: %s",
                                   order_id, cancel_result.get("msg", "unknown"))
            except Exception as e:
                logger.warning("Order %d: broker cancel error: %s", order_id, e)

        old_order.status = OrderStatus.CANCELLED
        old_order.error_message = f"Replaced by new order"

        # 2. Place the new order
        ot = OrderType(new_order_type) if new_order_type in ("market", "limit") else OrderType.MARKET
        new_qty = old_order.target_qty
        new_value = old_order.target_value
        limit_price = None

        if ot == OrderType.LIMIT:
            limit_price = new_limit_price or old_order.limit_price or old_order.target_value / old_order.target_qty if old_order.target_qty > 0 else None

        # Build the new order payload for the broker
        broker_order_payload = {
            "symbol": old_order.symbol,
            "side": old_order.side.value.upper(),
            "type": ot.value,
            "qty": int(old_order.target_qty),
            "time_in_force": "DAY",
        }
        if limit_price:
            broker_order_payload["price"] = float(limit_price)

        new_db_order = PortfolioRebalanceOrder(
            portfolio_id=portfolio_id,
            user_id=old_order.user_id,
            org_id=org_id,
            rebalance_group_id=old_order.rebalance_group_id,
            sequence=old_order.sequence,
            symbol=old_order.symbol,
            side=old_order.side,
            order_type=ot,
            target_qty=new_qty,
            target_value=new_value,
            limit_price=limit_price,
            status=OrderStatus.PENDING,
        )

        # Submit to broker if adapter available
        if broker_adapter:
            try:
                broker_result = await broker_adapter.place_order(broker_order_payload)
                broker_order_id = (
                    broker_result.get("broker_order_id")
                    or broker_result.get("order_id")
                    or broker_result.get("client_order_id")
                    or broker_result.get("data", {}).get("order_id")
                )
                if broker_order_id:
                    new_db_order.broker_order_id = broker_order_id
                    new_db_order.status = OrderStatus.SUBMITTED
            except Exception as e:
                new_db_order.error_message = f"Replace submit error: {e}"

        self.db.add(new_db_order)
        await self.db.commit()
        await self.db.refresh(new_db_order)
        return new_db_order

    async def delete_orders(
        self, portfolio_id: int, order_ids: list[int], org_id: int
    ) -> dict:
        """Hard-delete order records from the local DB.

        Any order can be deleted — it is purely a local DB cleanup operation.
        For orders still open at the broker, cancel them first via the
        bulk-cancel endpoint to keep the broker in sync.
        """
        result = await self.db.execute(
            select(PortfolioRebalanceOrder).where(
                PortfolioRebalanceOrder.id.in_(order_ids),
                PortfolioRebalanceOrder.portfolio_id == portfolio_id,
                PortfolioRebalanceOrder.org_id == org_id,
            )
        )
        orders = list(result.scalars().all())
        if not orders:
            return {"success": 0, "failed": 0, "errors": ["No orders found"]}

        succeeded = 0
        errors = []

        for order in orders:
            await self.db.delete(order)
            succeeded += 1

        await self.db.commit()
        return {"success": succeeded, "failed": 0, "errors": errors if errors else None}

    async def _resolve_portfolio_broker(
        self, portfolio_id: int, org_id: int
    ):
        """Resolve the broker adapter for a portfolio, or None."""
        result = await self.db.execute(
            select(Portfolio).where(
                Portfolio.id == portfolio_id,
                Portfolio.org_id == org_id,
            )
        )
        portfolio = result.scalar_one_or_none()
        if not portfolio or not portfolio.broker_connection_id:
            return None
        result = await self.db.execute(
            select(BrokerConnection).where(
                BrokerConnection.id == portfolio.broker_connection_id,
                BrokerConnection.is_active == True,
            )
        )
        conn = result.scalar_one_or_none()
        if not conn:
            return None
        try:
            from app.services.broker_service import resolve_adapter
            adapter = await resolve_adapter(conn)
            if await adapter.test_connection():
                return adapter
        except Exception as e:
            logger.warning("Portfolio %d: broker resolve error: %s", portfolio_id, e)
        return None

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

        # Record a performance snapshot whenever stats are recalculated
        await self._record_performance_snapshot(portfolio_id)

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
        if not snapshots:
            # Fallback: create a single data point from current portfolio values
            result2 = await self.db.execute(
                select(Portfolio).where(Portfolio.id == portfolio_id)
            )
            pf = result2.scalar_one_or_none()
            if pf:
                snapshots = [PortfolioPerformanceSnapshot(
                    portfolio_id=portfolio_id,
                    org_id=pf.org_id,
                    snapshot_date=datetime.now(timezone.utc),
                    total_value=pf.total_value or Decimal("0"),
                    total_pnl=pf.total_pnl or Decimal("0"),
                    total_return_pct=pf.total_pnl_pct or Decimal("0"),
                    daily_pnl=Decimal("0"),
                    daily_return_pct=Decimal("0"),
                )]

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

    # ── Broker Orders & Trades ───────────────────────────────

    async def get_broker_open_orders(
        self, portfolio_id: int, org_id: int
    ) -> list[dict]:
        """Fetch live open orders from the broker linked to this portfolio.

        Returns a normalized list of open orders.
        Returns empty list if no broker is linked or the adapter doesn't
        implement get_open_orders().
        """
        adapter = await self._resolve_portfolio_broker(portfolio_id, org_id)
        if not adapter:
            return []
        try:
            if not hasattr(adapter, "get_open_orders"):
                return []
            orders = await adapter.get_open_orders()
            return self._normalize_broker_orders(orders or [])
        except (AttributeError, NotImplementedError):
            return []
        except Exception as e:
            logger.warning("Portfolio %d: get_open_orders failed: %s", portfolio_id, e)
            return []

    async def get_broker_trades(
        self, portfolio_id: int, org_id: int
    ) -> list[dict]:
        """Fetch trade history from the broker linked to this portfolio.

        Returns a normalized list of filled/completed trades.
        Returns empty list if no broker is linked or the adapter doesn't
        implement get_order_history().
        """
        adapter = await self._resolve_portfolio_broker(portfolio_id, org_id)
        if not adapter:
            return []
        try:
            if not hasattr(adapter, "get_order_history"):
                return []
            history = await adapter.get_order_history()
            normalized = self._normalize_broker_orders(history or [])
            # Only return filled/completed trades
            return [t for t in normalized if t.get("status") in ("filled", "completed", "Filled", "Completed")]
        except (AttributeError, NotImplementedError):
            return []
        except Exception as e:
            logger.warning("Portfolio %d: get_order_history failed: %s", portfolio_id, e)
            return []

    @staticmethod
    def _normalize_broker_orders(orders: list[dict]) -> list[dict]:
        """Normalize broker-specific order formats into a standard shape.

        Handles both the Webull HK format and Paper adapter format.
        """
        normalized = []
        for o in orders:
            normalized.append({
                "id": o.get("id") or o.get("order_id") or o.get("broker_order_id", ""),
                "symbol": o.get("symbol", "").upper(),
                "side": (o.get("side") or "buy").lower(),
                "order_type": (o.get("order_type") or o.get("type") or "market").lower(),
                "qty": float(o.get("qty") or o.get("quantity") or o.get("target_qty") or 0),
                "filled_qty": float(o.get("filled_qty") or o.get("filled_quantity") or 0),
                "price": float(o.get("price") or o.get("limit_price") or 0),
                "avg_fill_price": float(o.get("avg_fill_price") or o.get("avg_price") or 0),
                "status": (o.get("status") or "unknown").lower(),
                "broker_order_id": o.get("order_id") or o.get("broker_order_id") or o.get("client_order_id", ""),
                "created_at": o.get("created_at") or o.get("create_time") or "",
                "source": "broker",
            })
        return normalized
