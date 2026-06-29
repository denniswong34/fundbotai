"""OKX exchange adapter — STUB.

SDK: okx (official) – https://github.com/okxapi/python-okx
    pip install okx

Supports spot, margin, futures, and perpetual swaps on OKX.
Testnet available by pointing to www.okx.com vs www.okx.com (no separate flag).
"""

from __future__ import annotations

from typing import Any

from app.services.broker_adapters.base import BrokerAdapter


class OkxBrokerAdapter(BrokerAdapter):
    """Adapter for OKX cryptocurrency exchange."""

    broker_type = "okx"
    broker_name = "OKX"

    async def test_connection(self) -> bool:
        raise NotImplementedError(
            "OKX adapter not yet implemented.  Use okx SDK."
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
