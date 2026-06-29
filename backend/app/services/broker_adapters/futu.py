"""Futu (Futu Holdings Ltd / Futubull) broker adapter — STUB.

SDK: futupy (unofficial) or the official Futu OpenAPI (Protobuf-based).
    https://github.com/FutuAPI/py-futu-api
    pip install futu-api

For production use with Futu OpenD:
  1. Run Futu OpenD locally or on a VPN-accessible host.
  2. Configure API_HOST / API_PORT in connection config_json.
  3. Provide unlock_password for trade operations.
"""

from __future__ import annotations

from typing import Any

from app.services.broker_adapters.base import BrokerAdapter


class FutuBrokerAdapter(BrokerAdapter):
    """Adapter for Futu (Futubull / 富途牛牛) — Hong Kong & US broker."""

    broker_type = "futu"
    broker_name = "Futu (Futubull)"

    async def test_connection(self) -> bool:
        raise NotImplementedError(
            "Futu adapter not yet implemented.  Use futu-api SDK + OpenD."
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
