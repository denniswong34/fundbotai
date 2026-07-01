"""Broker service — broker adapter resolution, connection management, and broker type registry.

Adapters are loaded dynamically from ``app.services.broker_adapters`` via the
``load_adapter_class()`` function in that package.  New broker types can be
added by:
  1) Creating a new module in ``broker_adapters/`` with a ``BrokerAdapter`` subclass.
  2) Adding the broker type key to ``BROKER_TYPES`` below.
  3) Mapping the key in ``broker_adapters/__init__.py``'s ``_ADAPTER_MODULES`` dict.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.broker_connection import BrokerConnection
from app.services.broker_adapters.base import BrokerAdapter
from app.services.broker_adapters.paper import PaperBrokerAdapter
from app.services.broker_adapters import load_adapter_class

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════
# Broker Type Registry
# ══════════════════════════════════════════════════════════════════════

BROKER_TYPES: dict[str, dict[str, Any]] = {
    # ── Simulated ────────────────────────────────────────────
    "paper": {
        "type": "paper",
        "name": "Paper Trading",
        "description": "Simulated trading environment for testing strategies without real money",
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
    # ── Futu / Futubull ──────────────────────────────────────
    "futu": {
        "type": "futu",
        "name": "Futu (Futubull)",
        "description": "Futu Holdings Ltd — HK, US & China A-share trading via Futu OpenAPI",
        "markets": ["stocks"],
        "config_schema": {
            "type": "object",
            "properties": {
                "api_host": {"type": "string", "title": "OpenD Host", "default": "127.0.0.1"},
                "api_port": {"type": "integer", "title": "OpenD Port", "default": 11111},
                "unlock_password": {"type": "string", "title": "Unlock Password", "format": "password"},
                "market": {
                    "type": "string",
                    "title": "Market",
                    "enum": ["HK", "US", "CN"],
                    "default": "HK",
                },
            },
            "required": ["unlock_password"],
        },
    },
    # ── Webull Hong Kong ─────────────────────────────────────
    "webull_hk": {
        "type": "webull_hk",
        "name": "Webull Hong Kong",
        "description": "Webull Securities Limited — HKEX stocks & ETFs. Supports OAuth (App Key/Secret) for API trading or direct login (Account/PIN).",
        "markets": ["stocks"],
        "config_schema": {
            "type": "object",
            "properties": {
                "app_key": {"type": "string", "title": "App Key", "description": "OAuth App Key from Webull Open Platform"},
                "app_secret": {"type": "string", "title": "App Secret", "format": "password", "description": "OAuth App Secret from Webull Open Platform"},
                "account_id": {"type": "string", "title": "Account ID", "description": "Your Webull account number (for direct login)"},
                "trade_pin": {"type": "string", "title": "Trade PIN", "format": "password", "description": "6-digit trading PIN (for direct login)"},
                "region_id": {"type": "string", "title": "Region", "default": "hk"},
                "server_url": {"type": "string", "title": "Server URL", "default": "https://api.sandbox.webull.hk", "description": "API base URL. Sandbox: https://api.sandbox.webull.hk, Production: https://api.webull.hk"},
            },
            "required": [],
        },
    },
    # ── Webull US ────────────────────────────────────────────
    "webull_us": {
        "type": "webull_us",
        "name": "Webull US",
        "description": "Webull Financial LLC — US stocks, ETFs & options. Supports OAuth (App Key/Secret) for API trading or direct login (Account/PIN).",
        "markets": ["stocks"],
        "config_schema": {
            "type": "object",
            "properties": {
                "app_key": {"type": "string", "title": "App Key", "description": "OAuth App Key from Webull Open Platform"},
                "app_secret": {"type": "string", "title": "App Secret", "format": "password"},
                "account_id": {"type": "string", "title": "Account ID"},
                "trade_pin": {"type": "string", "title": "Trade PIN", "format": "password"},
                "region_id": {"type": "string", "title": "Region", "default": "us"},
                "server_url": {"type": "string", "title": "Server URL", "default": "https://api.webull.com", "description": "API base URL"},
            },
            "required": [],
        },
    },
    # ── Moomoo ───────────────────────────────────────────────
    "moomoo": {
        "type": "moomoo",
        "name": "Moomoo",
        "description": "Moomoo Securities — US & SG markets (backed by Futu OpenAPI)",
        "markets": ["stocks"],
        "config_schema": {
            "type": "object",
            "properties": {
                "api_host": {"type": "string", "title": "OpenD Host", "default": "127.0.0.1"},
                "api_port": {"type": "integer", "title": "OpenD Port", "default": 11111},
                "unlock_password": {"type": "string", "title": "Unlock Password", "format": "password"},
                "market": {
                    "type": "string",
                    "title": "Market",
                    "enum": ["US", "SG"],
                    "default": "US",
                },
            },
            "required": ["unlock_password"],
        },
    },
    # ── Tiger Brokers ────────────────────────────────────────
    "tiger": {
        "type": "tiger",
        "name": "Tiger Brokers",
        "description": "Tiger Brokers — US, HK, SG & AU markets via Tiger OpenAPI",
        "markets": ["stocks"],
        "config_schema": {
            "type": "object",
            "properties": {
                "tiger_id": {"type": "string", "title": "Tiger ID"},
                "account": {"type": "string", "title": "Account Number"},
                "private_key": {"type": "string", "title": "RSA Private Key", "format": "password"},
                "server_url": {
                    "type": "string",
                    "title": "Server URL",
                    "default": "https://openapi.tigerbrokers.com",
                },
            },
            "required": ["tiger_id", "account", "private_key"],
        },
    },
    # ── Interactive Brokers ──────────────────────────────────
    "interactive_brokers": {
        "type": "interactive_brokers",
        "name": "Interactive Brokers (IBKR)",
        "description": "Interactive Brokers — global multi-asset brokerage (stocks, futures, forex, options)",
        "markets": ["stocks"],
        "config_schema": {
            "type": "object",
            "properties": {
                "host": {"type": "string", "title": "Host", "default": "127.0.0.1"},
                "port": {
                    "type": "integer",
                    "title": "Port",
                    "description": "7497 (TWS live), 7496 (IB Gateway paper), 5000 (Client Portal)",
                    "default": 7497,
                },
                "client_id": {"type": "integer", "title": "Client ID", "default": 1},
                "account_id": {"type": "string", "title": "Account ID (optional)"},
                "read_only": {"type": "boolean", "title": "Read Only", "default": False},
            },
            "required": [],
        },
    },
    # ── Alpaca ───────────────────────────────────────────────
    "alpaca": {
        "type": "alpaca",
        "name": "Alpaca",
        "description": "Alpaca Markets — commission-free US stock & crypto trading via REST API",
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
    # ── Binance ──────────────────────────────────────────────
    "binance": {
        "type": "binance",
        "name": "Binance",
        "description": "Binance cryptocurrency exchange — spot & futures trading",
        "markets": ["crypto"],
        "config_schema": {
            "type": "object",
            "properties": {
                "api_key": {"type": "string", "title": "API Key"},
                "api_secret": {"type": "string", "title": "API Secret", "format": "password"},
                "testnet": {"type": "boolean", "title": "Use Testnet", "default": True},
                "futures": {"type": "boolean", "title": "Futures Trading", "default": False},
            },
            "required": ["api_key", "api_secret"],
        },
    },
    # ── Bybit ────────────────────────────────────────────────
    "bybit": {
        "type": "bybit",
        "name": "Bybit",
        "description": "Bybit cryptocurrency exchange — spot, inverse & linear derivatives",
        "markets": ["crypto"],
        "config_schema": {
            "type": "object",
            "properties": {
                "api_key": {"type": "string", "title": "API Key"},
                "api_secret": {"type": "string", "title": "API Secret", "format": "password"},
                "testnet": {"type": "boolean", "title": "Use Testnet", "default": True},
                "category": {
                    "type": "string",
                    "title": "Category",
                    "enum": ["spot", "linear", "inverse", "option"],
                    "default": "spot",
                },
            },
            "required": ["api_key", "api_secret"],
        },
    },
    # ── OKX ──────────────────────────────────────────────────
    "okx": {
        "type": "okx",
        "name": "OKX",
        "description": "OKX cryptocurrency exchange — spot, margin, futures & perpetual swaps",
        "markets": ["crypto"],
        "config_schema": {
            "type": "object",
            "properties": {
                "api_key": {"type": "string", "title": "API Key"},
                "api_secret": {"type": "string", "title": "API Secret", "format": "password"},
                "passphrase": {"type": "string", "title": "Passphrase", "format": "password"},
                "testnet": {"type": "boolean", "title": "Use Testnet", "default": False},
            },
            "required": ["api_key", "api_secret", "passphrase"],
        },
    },
}


def get_broker_types() -> list[dict[str, Any]]:
    """Return the list of available broker types from the registry."""
    return list(BROKER_TYPES.values())


def get_broker_type(type_key: str) -> dict[str, Any] | None:
    """Get a specific broker type definition."""
    return BROKER_TYPES.get(type_key)


# ══════════════════════════════════════════════════════════════════════
# Adapter Registry & Resolution
# ══════════════════════════════════════════════════════════════════════

# Static fallback — paper is always available.
_ADAPTER_REGISTRY: dict[str, type[BrokerAdapter]] = {
    "paper": PaperBrokerAdapter,
}


def register_adapter(broker_type: str, adapter_class: type[BrokerAdapter]) -> None:
    """Register a broker adapter class for a given broker type."""
    _ADAPTER_REGISTRY[broker_type] = adapter_class


def _ensure_registry_populated() -> None:
    """Lazily load all available adapter classes into the registry.

    Called once on first ``resolve_adapter`` invocation.
    """
    if len(_ADAPTER_REGISTRY) > 1:
        return  # already populated
    for bt in BROKER_TYPES:
        if bt in _ADAPTER_REGISTRY:
            continue
        cls = load_adapter_class(bt)
        if cls is not None:
            _ADAPTER_REGISTRY[bt] = cls
            logger.debug("Registered adapter %s for broker_type=%s", cls.__name__, bt)


async def resolve_adapter(connection: BrokerConnection) -> BrokerAdapter:
    """Get the appropriate broker adapter for a connection.

    Adapters are auto-discovered on first call via dynamic module loading.
    Falls back to ``PaperBrokerAdapter`` if none found.
    """
    _ensure_registry_populated()
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
