"""Interactive Brokers (IBKR) adapter — STUB.

SDK: ib_insync (unofficial, well-maintained) – https://github.com/erdewit/ib_insync
    pip install ib_insync

Requires either:
  - IB Gateway running locally (for paper/live)
  - IB API (TWS) running locally
  - IBKR Web API (Client Portal Gateway)

Connection config should provide:
    host (default: 127.0.0.1)
    port (default: 7497 for TWS live, 7496 for IB Gateway paper)
    client_id (integer, unique per connection)
"""

from __future__ import annotations

from typing import Any

from app.services.broker_adapters.base import BrokerAdapter


class InteractiveBrokersAdapter(BrokerAdapter):
    """Adapter for Interactive Brokers — global multi-asset brokerage."""

    broker_type = "interactive_brokers"
    broker_name = "Interactive Brokers (IBKR)"

    async def test_connection(self) -> bool:
        raise NotImplementedError(
            "IBKR adapter not yet implemented.  Use ib_insync SDK."
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
