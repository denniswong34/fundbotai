"""Tiger Brokers adapter — STUB.

SDK: tiger-api (official) – https://github.com/tigerbrokers/tiger-openapi-python
    pip install tigerapi

Requires Tiger OpenAPI account with:
    - tiger_id
    - account (sub-account)
    - private_key (RSA key for signing)
"""

from __future__ import annotations

from typing import Any

from app.services.broker_adapters.base import BrokerAdapter


class TigerBrokerAdapter(BrokerAdapter):
    """Adapter for Tiger Brokers — US, HK, SG, & AU markets."""

    broker_type = "tiger"
    broker_name = "Tiger Brokers"

    async def test_connection(self) -> bool:
        raise NotImplementedError(
            "Tiger Brokers adapter not yet implemented.  Use tigerapi SDK."
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
