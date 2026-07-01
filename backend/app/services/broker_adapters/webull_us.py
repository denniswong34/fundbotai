"""Webull US broker adapter.

Supports two authentication methods:
  - **OAuth** (App Key + App Secret) — for automated API trading
  - **Direct Login** (Account ID + Trade PIN) — for managed trading
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.services.broker_adapters.base import BrokerAdapter

logger = logging.getLogger(__name__)


class WebullUsBrokerAdapter(BrokerAdapter):
    """Adapter for Webull US — stocks, ETFs & options."""

    broker_type = "webull_us"
    broker_name = "Webull US"

    async def test_connection(self) -> bool:
        server_url = self.config.get("server_url", "https://api.webull.com")
        app_key = self.config.get("app_key", "")
        app_secret = self.config.get("app_secret", "")
        account_id = self.config.get("account_id", "")
        trade_pin = self.config.get("trade_pin", "")

        has_oauth = bool(app_key and app_secret)
        has_direct = bool(account_id and trade_pin)
        if not has_oauth and not has_direct:
            logger.warning("Webull US %s: no credentials configured", self.connection.name)
            return False

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{server_url}/ping")
                logger.info("Webull US %s: responded HTTP %d", self.connection.name, resp.status_code)
                return True
        except (httpx.TimeoutException, httpx.ConnectError):
            logger.warning("Webull US %s: unreachable", self.connection.name)
            return False
        except Exception as exc:
            logger.warning("Webull US %s: error %s", self.connection.name, exc)
            return False

    async def get_positions(self) -> list[dict[str, Any]]:
        raise NotImplementedError("Webull US positions not yet implemented")

    async def get_account_summary(self) -> dict[str, Any]:
        raise NotImplementedError("Webull US account summary not yet implemented")

    async def place_order(self, order: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Webull US order placement not yet implemented")

    async def get_order_status(self, broker_order_id: str) -> dict[str, Any]:
        raise NotImplementedError("Webull US order status not yet implemented")

    async def cancel_order(self, broker_order_id: str) -> dict[str, Any]:
        raise NotImplementedError("Webull US order cancellation not yet implemented")

    async def get_market_hours(self) -> dict[str, Any]:
        raise NotImplementedError("Webull US market hours not yet implemented")
