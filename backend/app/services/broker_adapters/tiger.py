"""Tiger Brokers adapter — US, HK, SG & AU markets via Tiger OpenAPI.

Docs: https://www.tigersecurities.com/openapi
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.services.broker_adapters.base import BrokerAdapter

logger = logging.getLogger(__name__)


class TigerBrokerAdapter(BrokerAdapter):
    """Adapter for Tiger Brokers — requires RSA private key for authentication."""

    broker_type = "tiger"
    broker_name = "Tiger Brokers"

    async def test_connection(self) -> bool:
        tiger_id = self.config.get("tiger_id", "")
        account = self.config.get("account", "")
        private_key = self.config.get("private_key", "")
        server_url = self.config.get("server_url", "https://openapi.tigerbrokers.com")

        if not tiger_id or not account or not private_key:
            logger.warning("Tiger %s: missing required config (tiger_id, account, private_key)", self.connection.name)
            return False

        # Ping the Tiger OpenAPI endpoint
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{server_url}/health")
                logger.info("Tiger %s: HTTP %d — %s", self.connection.name, resp.status_code, "OK" if resp.status_code == 200 else "FAIL")
                return resp.status_code == 200
        except httpx.HTTPError as exc:
            logger.warning("Tiger %s: error: %s", self.connection.name, exc)
            return False

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
