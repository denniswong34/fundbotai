"""Bybit broker adapter — spot, linear & inverse derivatives trading via REST.

API docs: https://bybit-exchange.github.io/docs/
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.services.broker_adapters.base import BrokerAdapter

logger = logging.getLogger(__name__)


class BybitBrokerAdapter(BrokerAdapter):
    """Adapter for Bybit cryptocurrency exchange."""

    broker_type = "bybit"
    broker_name = "Bybit"

    async def test_connection(self) -> bool:
        api_key = self.config.get("api_key", "")
        api_secret = self.config.get("api_secret", "")
        testnet = self.config.get("testnet", True)

        if not api_key or not api_secret:
            logger.warning("Bybit %s: missing api_key or api_secret", self.connection.name)
            return False

        base_url = "https://api-testnet.bybit.com" if testnet else "https://api.bybit.com"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Public market endpoint — no auth required
                resp = await client.get(f"{base_url}/v5/market/time")
                ok = resp.status_code == 200
                logger.info("Bybit %s: HTTP %d — %s", self.connection.name, resp.status_code, "OK" if ok else "FAIL")
                return ok
        except httpx.HTTPError as exc:
            logger.warning("Bybit %s: error: %s", self.connection.name, exc)
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
