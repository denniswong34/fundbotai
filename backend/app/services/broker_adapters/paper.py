"""Paper trading broker adapter — fully simulated trading environment."""

from __future__ import annotations

import random
import string
from datetime import datetime, timezone
from typing import Any

from app.models.broker_connection import BrokerConnection
from app.services.broker_adapters.base import BrokerAdapter


def _random_id(prefix: str = "paper") -> str:
    """Generate a unique paper-order/position ID."""
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{prefix}_{suffix}"


class PaperBrokerAdapter(BrokerAdapter):
    """Simulated broker adapter for testing strategies without real money.

    Maintains in-memory positions and order history keyed by connection
    (identified by connection.id).  Balances start at ``initial_balance``
    from the connection config and change with each simulated fill.
    """

    broker_type = "paper"
    broker_name = "Paper Trading"

    # Class-level stores keyed by connection id — shared across adapter
    # instances for the same connection within the same process.
    _positions: dict[int, list[dict[str, Any]]] = {}
    _orders: dict[int, list[dict[str, Any]]] = {}
    _balances: dict[int, float] = {}

    # ── Helpers ──────────────────────────────────────────────────────

    def _get_balance(self) -> float:
        return self._balances.setdefault(
            self.connection.id,
            float(self.config.get("initial_balance", 100_000)),
        )

    def _set_balance(self, value: float) -> None:
        self._balances[self.connection.id] = value

    def _get_positions(self) -> list[dict[str, Any]]:
        return self._positions.setdefault(self.connection.id, [])

    def _get_orders(self) -> list[dict[str, Any]]:
        return self._orders.setdefault(self.connection.id, [])

    def _commission(self, qty: float, price: float) -> float:
        pct = float(self.config.get("commission_pct", 0.0))
        return round(qty * price * pct, 2)

    # ── Interface implementation ─────────────────────────────────────

    async def test_connection(self) -> bool:
        return True

    async def get_positions(self) -> list[dict[str, Any]]:
        return list(self._get_positions())

    async def get_account_summary(self) -> dict[str, Any]:
        positions = self._get_positions()
        pos_value = sum(
            p.get("market_value", 0.0) for p in positions
        )
        cash = self._get_balance()
        equity = cash + pos_value
        return {
            "total_equity": round(equity, 2),
            "cash_balance": round(cash, 2),
            "buying_power": round(cash, 2),
            "position_market_value": round(pos_value, 2),
            "currency": "USD",
            "unrealized_pl": round(
                sum(p.get("unrealized_pl", 0.0) for p in positions), 2
            ),
        }

    async def place_order(self, order: dict[str, Any]) -> dict[str, Any]:
        symbol = order.get("symbol", "UNKNOWN")
        side = order.get("side", "buy")
        qty = float(order.get("qty", 0))
        price = float(order.get("price", 0) or order.get("limit_price", 0) or 0)
        order_type = order.get("type", "market")

        # Simulate fill mechanics
        fill_price = price if price > 0 else round(random.uniform(10, 500), 2)
        filled_qty = qty
        commission = self._commission(filled_qty, fill_price)
        order_id = _random_id("paper")

        now = datetime.now(timezone.utc).isoformat()

        # Adjust cash balance
        total_cost = filled_qty * fill_price + commission
        if side == "buy":
            self._set_balance(self._get_balance() - total_cost)
        else:
            self._set_balance(self._get_balance() + total_cost)

        # Update positions
        positions = self._get_positions()
        existing = next((p for p in positions if p["symbol"] == symbol), None)
        if existing:
            if side == "buy":
                avg_new = (
                    existing["cost_basis"] * existing["qty"]
                    + fill_price * filled_qty
                ) / (existing["qty"] + filled_qty)
                existing["qty"] += filled_qty
                existing["cost_basis"] = round(avg_new, 4)
            else:  # sell
                existing["qty"] -= filled_qty
                if existing["qty"] <= 0:
                    positions.remove(existing)
            existing["market_value"] = round(existing["qty"] * fill_price, 2)
            existing["unrealized_pl"] = round(
                existing["market_value"] - existing["cost_basis"] * existing["qty"], 2
            )
        elif side == "buy":
            positions.append({
                "symbol": symbol,
                "qty": filled_qty,
                "cost_basis": round(fill_price, 4),
                "market_value": round(filled_qty * fill_price, 2),
                "unrealized_pl": 0.0,
                "currency": "USD",
            })

        # Record order in history
        order_record: dict[str, Any] = {
            "broker_order_id": order_id,
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "qty": filled_qty,
            "price": fill_price,
            "status": "filled",
            "filled_qty": filled_qty,
            "avg_fill_price": fill_price,
            "commission": commission,
            "created_at": now,
            "updated_at": now,
        }
        self._get_orders().append(order_record)

        return order_record

    async def get_order_status(self, broker_order_id: str) -> dict[str, Any]:
        orders = self._get_orders()
        for o in orders:
            if o["broker_order_id"] == broker_order_id:
                return o
        return {"broker_order_id": broker_order_id, "status": "not_found"}

    async def cancel_order(self, broker_order_id: str) -> dict[str, Any]:
        orders = self._get_orders()
        for o in orders:
            if o["broker_order_id"] == broker_order_id:
                o["status"] = "cancelled"
                o["updated_at"] = datetime.now(timezone.utc).isoformat()
                return o
        return {"broker_order_id": broker_order_id, "status": "not_found"}

    async def get_market_hours(self) -> dict[str, Any]:
        return {
            "exchange": "SIMULATED",
            "is_open": True,
            "market_open": "09:30",
            "market_close": "16:00",
            "timezone": "America/New_York",
            "note": "Paper trading — market always open",
        }
