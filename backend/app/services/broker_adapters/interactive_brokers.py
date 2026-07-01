"""Interactive Brokers (IBKR) adapter — global multi-asset via TWS/IB Gateway API.

Docs: https://www.interactivebrokers.com/api/doc.html
"""

from __future__ import annotations

import logging
from typing import Any

from app.services.broker_adapters.base import BrokerAdapter

logger = logging.getLogger(__name__)


class InteractiveBrokersBrokerAdapter(BrokerAdapter):
    """Adapter for Interactive Brokers — requires a running TWS or IB Gateway."""

    broker_type = "interactive_brokers"
    broker_name = "Interactive Brokers (IBKR)"

    async def test_connection(self) -> bool:
        host = self.config.get("host", "127.0.0.1")
        port = int(self.config.get("port", 7497))

        # TCP socket check to TWS/IB Gateway
        try:
            import asyncio
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=5.0,
            )
            writer.close()
            await writer.wait_closed()
            logger.info("IBKR %s: TWS/Gateway reachable at %s:%s", self.connection.name, host, port)
            return True
        except (ConnectionRefusedError, TimeoutError, OSError) as exc:
            logger.warning("IBKR %s: cannot connect to %s:%s — %s", self.connection.name, host, port, exc)
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
