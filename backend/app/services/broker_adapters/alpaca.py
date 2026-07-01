"""Alpaca broker adapter — commission-free US stock & crypto via REST API.

API docs: https://docs.alpaca.markets/reference
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.services.broker_adapters.base import BrokerAdapter

logger = logging.getLogger(__name__)


class AlpacaBrokerAdapter(BrokerAdapter):
    """Adapter for Alpaca Markets — US stocks & crypto trading."""

    broker_type = "alpaca"
    broker_name = "Alpaca"

    async def test_connection(self) -> bool:
        api_key = self.config.get("api_key", "")
        api_secret = self.config.get("api_secret", "")
        paper = self.config.get("paper_trading", True)

        if not api_key or not api_secret:
            logger.warning("Alpaca %s: missing api_key or api_secret", self.connection.name)
            return False

        base_url = "https://paper-api.alpaca.markets" if paper else "https://api.alpaca.markets"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{base_url}/v2/account",
                    headers={
                        "APCA-API-KEY-ID": api_key,
                        "APCA-API-SECRET-KEY": api_secret,
                    },
                )
                ok = resp.status_code == 200
                logger.info("Alpaca %s: HTTP %d — %s", self.connection.name, resp.status_code, "OK" if ok else "FAIL")
                return ok
        except httpx.HTTPError as exc:
            logger.warning("Alpaca %s: connection error: %s", self.connection.name, exc)
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
