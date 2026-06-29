"""Base broker adapter — abstract interface all broker adapters implement."""

from __future__ import annotations

import abc
from typing import Any

from app.models.broker_connection import BrokerConnection


class BrokerAdapter(abc.ABC):
    """Abstract base class for all broker adapters.

    Every real-broker adapter (Futu, Webull, IBKR, Alpaca, Binance, etc.)
    must subclass this and implement all abstract methods.
    """

    broker_type: str = ""  # Override in subclasses to match BROKER_TYPES key
    broker_name: str = ""  # Human-readable name for the adapter

    def __init__(self, connection: BrokerConnection) -> None:
        self.connection = connection
        self.config = connection.config_json or {}

    # ── Connection lifecycle ─────────────────────────────────

    @abc.abstractmethod
    async def test_connection(self) -> bool:
        """Validate that the broker API credentials work and the endpoint is reachable."""

    # ── Account & positions ──────────────────────────────────

    @abc.abstractmethod
    async def get_positions(self) -> list[dict[str, Any]]:
        """Return current open positions.

        Each position dict should contain at minimum:
            symbol, qty, market_value, cost_basis, unrealized_pl, currency
        """

    @abc.abstractmethod
    async def get_account_summary(self) -> dict[str, Any]:
        """Return account-level summary.

        Should include at minimum:
            total_equity, cash_balance, buying_power, currency
        """

    # ── Order management ─────────────────────────────────────

    @abc.abstractmethod
    async def place_order(self, order: dict[str, Any]) -> dict[str, Any]:
        """Submit an order to the broker.

        ``order`` keys (caller-provided):
            symbol, side (buy/sell), type (market/limit/stop), qty, price (if limit),
            time_in_force (day/gtc/ioc), reduce_only (optional, crypto)

        Returns at minimum:
            broker_order_id, status, filled_qty, avg_fill_price
        """

    @abc.abstractmethod
    async def get_order_status(self, broker_order_id: str) -> dict[str, Any]:
        """Query the current status of a previously submitted order.

        Returns at minimum:
            broker_order_id, status, filled_qty, avg_fill_price
        """

    @abc.abstractmethod
    async def cancel_order(self, broker_order_id: str) -> dict[str, Any]:
        """Request cancellation of an open order.

        Returns at minimum:
            broker_order_id, status (cancelled / cancel_rejected)
        """

    # ── Market data ──────────────────────────────────────────

    @abc.abstractmethod
    async def get_market_hours(self) -> dict[str, Any]:
        """Return market open/close times for the relevant exchange(s).

        Should include at minimum:
            is_open, market_open (datetime str), market_close (datetime str),
            timezone
        """
