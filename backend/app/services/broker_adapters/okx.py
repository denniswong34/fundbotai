"""OKX broker adapter — spot, margin, futures & perpetual swaps via REST.

API docs: https://www.okx.com/docs-v5/
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.services.broker_adapters.base import BrokerAdapter

logger = logging.getLogger(__name__)


class OkxBrokerAdapter(BrokerAdapter):
    """Adapter for OKX cryptocurrency exchange."""

    broker_type = "okx"
    broker_name = "OKX"

    async def test_connection(self) -> bool:
        api_key = self.config.get("api_key", "")
        api_secret = self.config.get("api_secret", "")
        passphrase = self.config.get("passphrase", "")
        testnet = self.config.get("testnet", False)

        if not api_key or not api_secret or not passphrase:
            logger.warning("OKX %s: missing api_key, api_secret or passphrase", self.connection.name)
            return False

        base_url = "https://www.okx.com" if not testnet else "https://testnet.okx.com"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Public endpoint — no auth required
                resp = await client.get(f"{base_url}/api/v5/public/time")
                ok = resp.status_code == 200
                logger.info("OKX %s: HTTP %d — %s", self.connection.name, resp.status_code, "OK" if ok else "FAIL")
                return ok
        except httpx.HTTPError as exc:
            logger.warning("OKX %s: error: %s", self.connection.name, exc)
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
