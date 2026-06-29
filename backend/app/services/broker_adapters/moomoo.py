"""Moomoo (FutuSG / MooMoo) broker adapter — STUB.

SDK: futu-api (same underlying Futu OpenAPI as Futu).
    pip install futu-api

Moomoo is a Futu-backed broker targeting US & SG markets.
Use the same OpenD setup as the Futu adapter.
"""

from __future__ import annotations

from typing import Any

from app.services.broker_adapters.base import BrokerAdapter


class MoomooBrokerAdapter(BrokerAdapter):
    """Adapter for Moomoo — US, SG & HK markets via Futu OpenAPI."""

    broker_type = "moomoo"
    broker_name = "Moomoo"

    async def test_connection(self) -> bool:
        raise NotImplementedError(
            "Moomoo adapter not yet implemented.  Shares the futu-api SDK."
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
