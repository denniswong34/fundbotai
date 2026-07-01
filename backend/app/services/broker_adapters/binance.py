"""Binance broker adapter — spot & futures crypto trading via CCXT or REST.

API docs: https://binance-docs.github.io/apidocs/
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.services.broker_adapters.base import BrokerAdapter

logger = logging.getLogger(__name__)


class BinanceBrokerAdapter(BrokerAdapter):
    """Adapter for Binance cryptocurrency exchange."""

    broker_type = "binance"
    broker_name = "Binance"

    async def test_connection(self) -> bool:
        api_key = self.config.get("api_key", "")
        api_secret = self.config.get("api_secret", "")
        testnet = self.config.get("testnet", True)

        if not api_key or not api_secret:
            logger.warning("Binance %s: missing api_key or api_secret", self.connection.name)
            return False

        base_url = "https://testnet.binance.vision" if testnet else "https://api.binance.com"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Ping endpoint is unauthenticated
                resp = await client.get(f"{base_url}/api/v3/ping")
                ok = resp.status_code == 200
                logger.info("Binance %s: HTTP %d — %s", self.connection.name, resp.status_code, "OK" if ok else "FAIL")
                return ok
        except httpx.HTTPError as exc:
            logger.warning("Binance %s: error: %s", self.connection.name, exc)
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
