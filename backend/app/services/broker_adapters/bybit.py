"""Bybit exchange adapter — STUB.

SDK: pybit (unofficial) – https://github.com/bybit-exchange/pybit
    pip install pybit

Supports inverse, linear, and spot products on Bybit.
Testnet available via testnet=True in config.
"""

from __future__ import annotations

from typing import Any

from app.services.broker_adapters.base import BrokerAdapter


class BybitBrokerAdapter(BrokerAdapter):
    """Adapter for Bybit cryptocurrency exchange."""

    broker_type = "bybit"
    broker_name = "Bybit"

    async def test_connection(self) -> bool:
        raise NotImplementedError(
            "Bybit adapter not yet implemented.  Use pybit SDK."
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
