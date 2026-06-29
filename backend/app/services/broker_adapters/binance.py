"""Binance exchange adapter — STUB.

SDK: python-binance (unofficial) – https://github.com/sammchardy/python-binance
    pip install python-binance

Supports both spot and futures trading with testnet option.
"""

from __future__ import annotations

from typing import Any

from app.services.broker_adapters.base import BrokerAdapter


class BinanceBrokerAdapter(BrokerAdapter):
    """Adapter for Binance cryptocurrency exchange."""

    broker_type = "binance"
    broker_name = "Binance"

    async def test_connection(self) -> bool:
        raise NotImplementedError(
            "Binance adapter not yet implemented.  Use python-binance SDK."
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
