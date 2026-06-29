"""Webull US broker adapter — STUB.

SDK: webull (unofficial) – https://github.com/tedchou12/webull
    pip install webull

Uses the same python-webull library as Webull HK; the US endpoints are
selected via ``region_id`` in the connection config.
"""

from __future__ import annotations

from typing import Any

from app.services.broker_adapters.base import BrokerAdapter


class WebullUsBrokerAdapter(BrokerAdapter):
    """Adapter for Webull US — US stocks, ETFs, options."""

    broker_type = "webull_us"
    broker_name = "Webull US"

    async def test_connection(self) -> bool:
        raise NotImplementedError(
            "Webull US adapter not yet implemented.  Use the webull SDK."
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
