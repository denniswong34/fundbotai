"""Webull Hong Kong broker adapter — STUB.

SDK: webull (unofficial) – https://github.com/tedchou12/webull
    pip install webull

For HK-specific endpoints the ``region_id`` config field may be required.
"""

from __future__ import annotations

from typing import Any

from app.services.broker_adapters.base import BrokerAdapter


class WebullHkBrokerAdapter(BrokerAdapter):
    """Adapter for Webull Hong Kong — stocks & ETFs traded on HKEX."""

    broker_type = "webull_hk"
    broker_name = "Webull Hong Kong"

    async def test_connection(self) -> bool:
        raise NotImplementedError(
            "Webull HK adapter not yet implemented.  Use the webull SDK."
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
