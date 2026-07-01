"""Moomoo broker adapter — US & SG markets via Futu OpenAPI (same backend as Futu).

Docs: https://www.moomoo.com/download/OpenAPI
"""

from __future__ import annotations

import logging
from typing import Any

from app.services.broker_adapters.base import BrokerAdapter

logger = logging.getLogger(__name__)


class MoomooBrokerAdapter(BrokerAdapter):
    """Adapter for Moomoo — US & SG markets, backed by Futu OpenAPI."""

    broker_type = "moomoo"
    broker_name = "Moomoo"

    async def test_connection(self) -> bool:
        host = self.config.get("api_host", "127.0.0.1")
        port = self.config.get("api_port", 11111)
        password = self.config.get("unlock_password", "")

        if not password:
            logger.warning("Moomoo %s: missing unlock_password", self.connection.name)
            return False

        try:
            import asyncio
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=5.0,
            )
            writer.close()
            await writer.wait_closed()
            logger.info("Moomoo %s: OpenD reachable at %s:%s", self.connection.name, host, port)
            return True
        except (ConnectionRefusedError, TimeoutError, OSError) as exc:
            logger.warning("Moomoo %s: cannot connect to %s:%s — %s", self.connection.name, host, port, exc)
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
