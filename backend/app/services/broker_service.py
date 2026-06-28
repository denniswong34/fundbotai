"""Broker service — broker adapter resolution, connection management, and broker type registry."""

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.broker_connection import BrokerConnection

logger = logging.getLogger(__name__)

# ── Broker Type Registry ────────────────────────────────────

BROKER_TYPES: dict[str, dict[str, Any]] = {
    "paper": {
        "type": "paper",
        "name": "Paper Trading",
        "description": "Simulated trading environment for testing strategies",
        "markets": ["stocks", "crypto"],
        "config_schema": {
            "type": "object",
            "properties": {
                "initial_balance": {
                    "type": "number",
                    "title": "Initial Balance",
                    "default": 100000,
                },
                "commission_pct": {
                    "type": "number",
                    "title": "Commission %",
                    "default": 0.0,
                },
            },
        },
    },
    "webull": {
        "type": "webull",
        "name": "Webull",
        "description": "Webull trading platform integration",
        "markets": ["stocks"],
        "config_schema": {
            "type": "object",
            "properties": {
                "app_key": {"type": "string", "title": "App Key"},
                "app_secret": {"type": "string", "title": "App Secret", "format": "password"},
                "account_id": {"type": "string", "title": "Account ID"},
            },
            "required": ["app_key", "app_secret"],
        },
    },
    "alpaca": {
        "type": "alpaca",
        "name": "Alpaca",
        "description": "Alpaca trading API (US stocks)",
        "markets": ["stocks"],
        "config_schema": {
            "type": "object",
            "properties": {
                "api_key": {"type": "string", "title": "API Key"},
                "api_secret": {"type": "string", "title": "API Secret", "format": "password"},
                "paper_trading": {"type": "boolean", "title": "Paper Trading", "default": True},
            },
            "required": ["api_key", "api_secret"],
        },
    },
    "binance": {
        "type": "binance",
        "name": "Binance",
        "description": "Binance cryptocurrency exchange",
        "markets": ["crypto"],
        "config_schema": {
            "type": "object",
            "properties": {
                "api_key": {"type": "string", "title": "API Key"},
                "api_secret": {"type": "string", "title": "API Secret", "format": "password"},
                "testnet": {"type": "boolean", "title": "Use Testnet", "default": True},
            },
            "required": ["api_key", "api_secret"],
        },
    },
}


def get_broker_types() -> list[dict[str, Any]]:
    """Return the list of available broker types from the registry."""
    return list(BROKER_TYPES.values())


def get_broker_type(type_key: str) -> dict[str, Any] | None:
    """Get a specific broker type definition."""
    return BROKER_TYPES.get(type_key)


class BrokerAdapter:
    """Base broker adapter interface. Specific brokers extend this."""

    def __init__(self, connection: BrokerConnection):
        self.connection = connection
        self.config = connection.config_json or {}

    async def test_connection(self) -> bool:
        """Test if the broker connection is valid."""
        raise NotImplementedError

    async def get_positions(self) -> list[dict]:
        """Get current positions from the broker."""
        raise NotImplementedError

    async def get_account_summary(self) -> dict:
        """Get account summary (balance, buying power, etc.)."""
        raise NotImplementedError

    async def place_order(self, order: dict) -> dict:
        """Place an order with the broker."""
        raise NotImplementedError

    async def get_order_status(self, broker_order_id: str) -> dict:
        """Check the status of a submitted order."""
        raise NotImplementedError


class PaperBrokerAdapter(BrokerAdapter):
    """Paper trading broker — simulates trading locally."""

    async def test_connection(self) -> bool:
        return True

    async def get_positions(self) -> list[dict]:
        return []

    async def get_account_summary(self) -> dict:
        return {
            "total_equity": self.config.get("initial_balance", 100000),
            "cash_balance": self.config.get("initial_balance", 100000),
            "buying_power": self.config.get("initial_balance", 100000),
        }

    async def place_order(self, order: dict) -> dict:
        commission = float(self.config.get("commission_pct", 0))
        return {
            "broker_order_id": f"paper_{order.get('symbol', 'unknown')}_{id(order)}",
            "status": "filled",
            "filled_qty": order.get("qty", 0),
            "avg_fill_price": order.get("price", 0),
            "commission": commission,
        }

    async def get_order_status(self, broker_order_id: str) -> dict:
        return {"broker_order_id": broker_order_id, "status": "filled"}


_ADAPTER_REGISTRY: dict[str, type[BrokerAdapter]] = {
    "paper": PaperBrokerAdapter,
}


def register_adapter(broker_type: str, adapter_class: type[BrokerAdapter]) -> None:
    """Register a broker adapter class for a given broker type."""
    _ADAPTER_REGISTRY[broker_type] = adapter_class


async def resolve_adapter(connection: BrokerConnection) -> BrokerAdapter:
    """Get the appropriate broker adapter for a connection."""
    adapter_class = _ADAPTER_REGISTRY.get(connection.broker_type, PaperBrokerAdapter)
    return adapter_class(connection)


async def test_connection(connection: BrokerConnection) -> bool:
    """Test a broker connection by resolving its adapter and calling test."""
    try:
        adapter = await resolve_adapter(connection)
        result = await adapter.test_connection()
        return result
    except Exception as e:
        logger.warning(f"Connection test failed for {connection.name}: {e}")
        return False


async def get_active_connections(db: AsyncSession, org_id: int) -> list[BrokerConnection]:
    """Get all active broker connections for an organization."""
    result = await db.execute(
        select(BrokerConnection).where(
            BrokerConnection.org_id == org_id,
            BrokerConnection.is_active == True,
        )
    )
    return list(result.scalars().all())
