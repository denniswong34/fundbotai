"""Futu (Futubull) broker adapter — HK, US & China A-shares via Futu OpenAPI + OpenD.

Docs: https://futunnopen.github.io/futu-api-doc/
"""

from __future__ import annotations

import logging
from typing import Any

from app.services.broker_adapters.base import BrokerAdapter

logger = logging.getLogger(__name__)


class FutuBrokerAdapter(BrokerAdapter):
    """Adapter for Futu (Futubull) — requires a running OpenD process."""

    broker_type = "futu"
    broker_name = "Futu (Futubull)"

    async def test_connection(self) -> bool:
        host = self.config.get("api_host", "127.0.0.1")
        port = self.config.get("api_port", 11111)
        password = self.config.get("unlock_password", "")

        if not password:
            logger.warning("Futu %s: missing unlock_password", self.connection.name)
            return False

        # Try a TCP socket check to see if OpenD is listening
        try:
            import asyncio
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=5.0,
            )
            writer.close()
            await writer.wait_closed()
            logger.info("Futu %s: OpenD reachable at %s:%s", self.connection.name, host, port)
            return True
        except (ConnectionRefusedError, TimeoutError, OSError) as exc:
            logger.warning("Futu %s: cannot connect to %s:%s — %s", self.connection.name, host, port, exc)
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
