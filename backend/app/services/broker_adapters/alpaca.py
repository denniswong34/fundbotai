"""Alpaca broker adapter — STUB.

SDK: alpaca-py (official) – https://github.com/alpacahq/alpaca-py
    pip install alpaca-py

Alpaca provides commission-free US stock & crypto trading via REST API.
Supports paper trading (paper=True in config).
"""

from __future__ import annotations

from typing import Any

from app.services.broker_adapters.base import BrokerAdapter


class AlpacaBrokerAdapter(BrokerAdapter):
    """Adapter for Alpaca — US stocks & crypto trading."""

    broker_type = "alpaca"
    broker_name = "Alpaca"

    async def test_connection(self) -> bool:
        raise NotImplementedError(
            "Alpaca adapter not yet implemented.  Use alpaca-py SDK."
        )

    async def get_positions(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    async def get_account_summary(self) -> dict[str, Any]:
        raise NotImplementedError

    async def place_order(self, order: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    async def get_order_status(self, broker_order_id: str) -> dict[str, Any]:
        raise NotImplementedError

    async def cancel_order(self, broker_order_id: str) -> dict[str, Any]:
        raise NotImplementedError

    async def get_market_hours(self) -> dict[str, Any]:
        raise NotImplementedError
