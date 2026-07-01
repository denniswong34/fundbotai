"""Webull Hong Kong broker adapter.

Uses the official Webull Python SDK (v1.1.0) signing algorithm directly
via ``webull.core.auth.composer.default_signature_composer``.

Sandbox: api.sandbox.webull.hk (shared test accounts, no prior application needed)
Production: api.webull.hk

Endpoint reference (from official Webull HK Open API docs https://developer.webull.hk/apis/docs/webull-open-api-reference):

  Auth
    POST /openapi/auth/token/create           — generate access token
    POST /openapi/auth/token/check             — verify token status

  Accounts
    GET  /openapi/account/list                 — list accounts
    GET  /openapi/assets/balance               — account balance details
    GET  /openapi/assets/positions             — positions by account ID

  Trading – Order (Trading API)
    POST /openapi/trade/order/preview          — preview order cost
    POST /openapi/trade/order/place            — place equity/options order
    POST /openapi/trade/order/replace          — modify open order
    POST /openapi/trade/order/cancel           — cancel pending order

  Trading – Order Query (Trading API)
    GET  /openapi/trade/order/open             — pending orders
    GET  /openapi/trade/order/history          — historical orders (7 days)
    GET  /openapi/trade/order/detail           — order details by order ID

  Market Data – Stock (Non-Display Solution)
    GET  /openapi/market-data/stock/tick       — tick-by-tick trade data
    GET  /openapi/market-data/stock/snapshot   — real-time snapshot
    GET  /openapi/market-data/stock/quotes     — bid/ask depth
    GET  /openapi/market-data/stock/bars       — single-symbol OHLCV
    POST /openapi/market-data/stock/batch-bars — batch OHLCV
"""
from __future__ import annotations

import logging
import time
import urllib.parse
from typing import Any

import httpx

from app.services.broker_adapters.base import BrokerAdapter

# Official Webull SDK signing components
from webull.core.auth.composer import default_signature_composer as sc
from webull.core.auth.algorithm import sha_hmac1
import webull.core.headers as hd
from webull.core.utils.common import get_iso_8601_date, get_uuid, json_dumps_compact, md5_hex

logger = logging.getLogger(__name__)

SHARED_TEST_ACCOUNTS = {
    "HK": {
        "app_key": "409b24511e9a1df887a1e0f76e4cefb0",
        "app_secret": "9e16899c947a9da0fc07e549f6c3e62c",
    },
}


def _sign(
    host: str,
    uri_path: str,
    body_params: dict | None = None,
    query_params: dict | None = None,
    app_key: str | None = None,
    app_secret: str | None = None,
) -> tuple[dict[str, str], str]:
    """Build signed headers using the official SDK composer.

    Returns (headers_dict, body_string).
    """
    sign_headers = {
        hd.APP_KEY: app_key,
        hd.TIMESTAMP: get_iso_8601_date(),
        hd.SIGN_VERSION: sha_hmac1.get_signer_version(),
        hd.SIGN_ALGORITHM: sha_hmac1.get_signer_name(),
        hd.NONCE: get_uuid(),
    }

    # Lowercase keys (SDK does this internally)
    sign_headers_lower = {k.lower(): v for k, v in sign_headers.items()}
    sign_headers_lower["host"] = host

    # Merge query params into sign params (per SDK convention)
    if query_params:
        for k, v in query_params.items():
            k_lower = k.lower()
            existing = sign_headers_lower.get(k_lower)
            if existing is not None:
                sign_headers_lower[k_lower] = f"{existing}&{v}"
            else:
                sign_headers_lower[k_lower] = str(v)

    # Build body + MD5
    body_str = json_dumps_compact(body_params) if body_params is not None else ""
    body_md5 = md5_hex(body_str).upper() if body_params is not None else None

    # Build string-to-sign using the SDK's function
    sig_path = "/" + uri_path.lstrip("/")
    string_to_sign = sc._build_sign_string(sign_headers_lower, sig_path, body_md5)

    # Generate signature using the SDK's function
    signature = sc._gen_signature(string_to_sign, app_secret, sha_hmac1)

    headers = {
        "Content-Type": "application/json",
        "x-app-key": app_key,
        "x-timestamp": sign_headers[hd.TIMESTAMP],
        "x-signature-version": sign_headers[hd.SIGN_VERSION],
        "x-signature-algorithm": sign_headers[hd.SIGN_ALGORITHM],
        "x-signature-nonce": sign_headers[hd.NONCE],
        "x-signature": signature,
    }

    return headers, body_str


class WebullHkBrokerAdapter(BrokerAdapter):
    """Adapter for Webull Hong Kong — uses correct official API paths."""

    broker_type = "webull_hk"
    broker_name = "Webull Hong Kong"

    def __init__(self, connection: Any) -> None:
        super().__init__(connection)
        self._token: str | None = None
        self._refresh_token: str | None = None
        self._token_expires_at: float = 0
        self._account_id: str | None = None

    @property
    def _host(self) -> str:
        server_url = self.config.get("server_url", "https://api.sandbox.webull.hk")
        host = server_url.replace("https://", "").replace("http://", "").split("/")[0]
        return host

    async def _get_account_id(self) -> str | None:
        """Get account_id from config or auto-detect from account list."""
        if self._account_id:
            return self._account_id
        # Check if it's in config
        aid = self.config.get("account_id") or self.config.get("sub_account_id")
        if aid:
            self._account_id = aid
            return aid
        # Auto-detect from account list
        try:
            accounts = await self.get_accounts()
            if accounts:
                self._account_id = accounts[0].get("account_id") or accounts[0].get("id")
                logger.info("Webull HK %s: auto-detected account_id=%s", self.connection.name, self._account_id)
                return self._account_id
        except Exception:
            pass
        return None

    def _get_app_credentials(self) -> tuple[str, str]:
        app_key = self.config.get("app_key", "")
        app_secret = self.config.get("app_secret", "")
        if not app_key or not app_secret:
            shared = SHARED_TEST_ACCOUNTS.get("HK", {})
            app_key = shared.get("app_key", "")
            app_secret = shared.get("app_secret", "")
        return app_key, app_secret

    async def _ensure_token(self) -> str | None:
        if self._token and time.time() < self._token_expires_at:
            return self._token

        app_key, app_secret = self._get_app_credentials()
        if not app_key or not app_secret:
            return None

        try:
            headers, body = _sign(
                self._host,
                "openapi/auth/token/create",
                body_params={
                    "app_key": app_key,
                    "app_secret": app_secret,
                    "grant_type": "client_credentials",
                },
                app_key=app_key,
                app_secret=app_secret,
            )
            url = f"https://{self._host}/openapi/auth/token/create"

            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, headers=headers, content=body)

            if resp.status_code == 200:
                data = resp.json()
                payload = data.get("data", data)
                self._token = payload.get("access_token", payload.get("token")) or None
                expires_in = payload.get("expires_in", 7200)
                self._token_expires_at = time.time() + int(expires_in)
                self._refresh_token = payload.get("refresh_token") or None
                logger.info("Webull HK %s: token obtained", self.connection.name)
                return self._token

            logger.warning(
                "Webull HK %s: token request HTTP %d: %s",
                self.connection.name,
                resp.status_code,
                resp.text[:300],
            )
            return None
        except Exception as exc:
            logger.warning("Webull HK %s: token error: %s", self.connection.name, exc)
            return None

    async def _api_request(
        self,
        method: str,
        uri_path: str,
        body_params: dict | None = None,
        query_params: dict | None = None,
        extra_headers: dict | None = None,
    ) -> dict[str, Any]:
        """Make a signed request to the Webull HK API."""
        token = await self._ensure_token()
        if not token:
            return {"code": -1, "msg": "Failed to obtain access token"}

        app_key, app_secret = self._get_app_credentials()
        headers, body = _sign(
            self._host,
            uri_path,
            body_params=body_params,
            query_params=query_params,
            app_key=app_key,
            app_secret=app_secret,
        )
        headers["x-access-token"] = token
        # All Webull HK API endpoints require x-version: v2
        headers["x-version"] = "v2"
        if extra_headers:
            headers.update(extra_headers)

        url = f"https://{self._host}/{uri_path.lstrip('/')}"
        if query_params and method == "GET":
            url += "?" + urllib.parse.urlencode(query_params, doseq=True)

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.request(method, url, headers=headers, content=body)
            try:
                data = resp.json()
                if isinstance(data, dict):
                    data.setdefault("_http_status", resp.status_code)
                    return data
                return {"code": 0, "data": data, "_http_status": resp.status_code, "_is_list": True}
            except ValueError:
                return {"code": -2, "msg": f"Non-JSON: {resp.text[:200]}", "_http_status": resp.status_code}
        except Exception as exc:
            logger.warning("Webull HK %s: API error: %s", self.connection.name, exc)
            return {"code": -1, "msg": str(exc)}

    # ── Interface implementation ─────────────────────────────────

    async def test_connection(self) -> bool:
        app_key, app_secret = self._get_app_credentials()
        if not app_key or not app_secret:
            return False

        try:
            headers, body = _sign(
                self._host,
                "openapi/auth/token/create",
                body_params={
                    "app_key": app_key,
                    "app_secret": app_secret,
                    "grant_type": "client_credentials",
                },
                app_key=app_key,
                app_secret=app_secret,
            )
            url = f"https://{self._host}/openapi/auth/token/create"

            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, headers=headers, content=body)

            if resp.status_code == 200:
                data = resp.json()
                payload = data.get("data", data)
                self._token = payload.get("access_token", payload.get("token")) or None
                expires_in = payload.get("expires_in", 7200)
                self._token_expires_at = time.time() + int(expires_in)
                return self._token is not None

            logger.warning("Webull HK %s: test HTTP %d: %s", self.connection.name, resp.status_code, resp.text[:300])
            return False
        except Exception as exc:
            logger.warning("Webull HK %s: test error: %s", self.connection.name, exc)
            return False

    async def get_account_summary(self) -> dict[str, Any]:
        accounts = await self.get_accounts()
        if isinstance(accounts, list) and accounts:
            return dict(accounts[0])
        return {}

    async def get_accounts(self) -> list[dict[str, Any]]:
        """List all trading accounts."""
        resp = await self._api_request("GET", "openapi/account/list")
        if resp.get("code") == 0:
            data = resp.get("data", [])
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "accounts" in data:
                return data["accounts"]
            return [data] if data else []
        logger.warning("Webull HK %s: accounts: %s", self.connection.name, resp.get("msg", resp))
        return []

    async def get_balance(self) -> dict[str, Any]:
        """Get account balance details. Auto-injects account_id."""
        account_id = await self._get_account_id()
        params = {"account_id": account_id} if account_id else {}
        resp = await self._api_request("GET", "openapi/assets/balance", query_params=params)
        if resp.get("code") == 0 or resp.get("_http_status") == 200:
            return {k: v for k, v in resp.items() if not k.startswith("_")}
        logger.warning("Webull HK %s: balance: %s", self.connection.name, resp.get("msg", resp))
        return {}

    async def get_positions(self) -> list[dict[str, Any]]:
        """Get positions for the account. Auto-injects account_id."""
        account_id = await self._get_account_id()
        params = {"account_id": account_id} if account_id else {}
        resp = await self._api_request("GET", "openapi/assets/positions", query_params=params)
        if resp.get("code") == 0:
            data = resp.get("data", [])
            return data if isinstance(data, list) else [data] if data else []
        logger.warning("Webull HK %s: positions: %s", self.connection.name, resp.get("msg", resp))
        return []

    async def place_order(self, order: dict[str, Any]) -> dict[str, Any]:
        """Place an order. Wraps in new_orders array, auto-adds account_id."""
        account_id = await self._get_account_id()
        
        # Build order payload per Webull HK API spec
        if "account_id" not in order and account_id:
            order["account_id"] = account_id
        
        import uuid
        # If order doesn't have new_orders wrapper, wrap it
        if "new_orders" not in order and "symbol" in order:
            side = order.pop("side", "BUY")
            order_type = order.pop("order_type", order.pop("type", "LMT"))
            symbol = order.pop("symbol")
            qty = order.pop("qty", order.pop("quantity", 1))
            tif = order.pop("time_in_force", "DAY")
            
            new_order = {
                "client_order_id": uuid.uuid4().hex[:32],
                "combo_type": "NORMAL",
                "entrust_type": order_type,
                "instrument_type": order.pop("instrument_type", "EQUITY"),
                "market": order.pop("market", self._detect_market(symbol)),
                "order_type": order_type,
                "side": side,
                "symbol": symbol,
                "quantity": qty,
                "time_in_force": tif,
            }
            # Optional price fields
            price = order.pop("price", order.pop("limit_price", None))
            if price:
                new_order["limit_price"] = str(price)
            stop_price = order.pop("stop_price", None)
            if stop_price:
                new_order["stop_price"] = str(stop_price)
            # Support trading session (US stocks)
            if new_order.get("market") == "US":
                new_order["support_trading_session"] = "ALL"
            
            order["new_orders"] = [new_order]

        # Try preview first
        try:
            preview = await self._api_request("POST", "openapi/trade/order/preview", body_params=order)
            if preview.get("code") != 0:
                logger.debug("Webull HK %s: order preview: %s", self.connection.name, preview.get("msg", preview.get("message", "")))
        except Exception:
            pass

        resp = await self._api_request("POST", "openapi/trade/order/place", body_params=order)
        if resp.get("code") == 0:
            return resp.get("data", resp)
        logger.warning("Webull HK %s: place_order: %s", self.connection.name, resp.get("msg", resp.get("message", str(resp))))
        return {"success": False, "msg": resp.get("msg", resp.get("message", str(resp)))}

    @staticmethod
    def _detect_market(symbol: str) -> str:
        """Detect market code (US/HK/CN) from symbol suffix."""
        category = WebullHkBrokerAdapter._detect_instrument_category(symbol)
        return {"HK_STOCK": "HK", "CN_STOCK": "CN"}.get(category, "US")

    async def get_order_status(self, broker_order_id: str) -> dict[str, Any]:
        resp = await self._api_request("GET", "openapi/trade/order/detail", query_params={"order_id": broker_order_id})
        if resp.get("code") == 0:
            return resp.get("data", resp)
        return {"code": resp.get("code"), "msg": resp.get("msg", "")}

    async def cancel_order(self, broker_order_id: str) -> dict[str, Any]:
        resp = await self._api_request("POST", "openapi/trade/order/cancel", body_params={"order_id": broker_order_id})
        if resp.get("code") == 0:
            return {"success": True, "data": resp.get("data")}
        return {"success": False, "msg": resp.get("msg", str(resp))}

    async def get_open_orders(self) -> list[dict[str, Any]]:
        """Get all open (pending) orders. Auto-injects account_id."""
        account_id = await self._get_account_id()
        params = {"account_id": account_id} if account_id else {}
        resp = await self._api_request("GET", "openapi/trade/order/open", query_params=params)
        if resp.get("code") == 0:
            data = resp.get("data", [])
            return data if isinstance(data, list) else [data] if data else []
        return []

    async def get_order_history(self) -> list[dict[str, Any]]:
        """Get historical orders (past 7 days). Auto-injects account_id."""
        account_id = await self._get_account_id()
        params = {"account_id": account_id} if account_id else {}
        resp = await self._api_request("GET", "openapi/trade/order/history", query_params=params)
        if resp.get("code") == 0:
            data = resp.get("data", [])
            return data if isinstance(data, list) else [data] if data else []
        return []

    async def get_market_quote(self, symbol: str) -> dict[str, Any]:
        """Get bid/ask quotes for a symbol. Requires category, depth, overnight_required."""
        category = self._detect_instrument_category(symbol)
        params = {
            "symbol": symbol,
            "category": category,
            "depth": "1",
            "overnight_required": "false",
        }
        resp = await self._api_request("GET", "openapi/market-data/stock/quotes", query_params=params)
        if resp.get("code") == 0 or resp.get("_http_status") == 200:
            data = resp.get("data", resp)
            if isinstance(data, list) and data:
                return data[0]
            if isinstance(data, dict):
                return {k: v for k, v in data.items() if not k.startswith("_")}
            return data
        return {}

    async def get_market_snapshot(self, symbol: str) -> dict[str, Any]:
        """Get real-time snapshot for a symbol. Uses symbols (plural) param."""
        category = self._detect_instrument_category(symbol)
        params = {
            "symbols": symbol,
            "category": category,
        }
        resp = await self._api_request("GET", "openapi/market-data/stock/snapshot", query_params=params)
        if resp.get("code") == 0:
            data = resp.get("data", [])
            if isinstance(data, list) and data:
                return data[0] if isinstance(data[0], dict) else {}
            return dict(data) if isinstance(data, dict) else {}
        return {}

    async def get_instruments(self, symbols: list[str]) -> list[dict[str, Any]]:
        """Look up instruments by symbol(s). Maximum 100 per query."""
        if not symbols:
            return []
        # Determine category from the first symbol
        category = self._detect_instrument_category(symbols[0])
        params = {
            "symbols": ",".join(symbols),
            "category": category,
        }
        resp = await self._api_request("GET", "openapi/instrument/stock/list", query_params=params)
        if resp.get("code") == 0:
            data = resp.get("data", [])
            return data if isinstance(data, list) else [data] if data else []
        logger.warning("Webull HK %s: instruments: %s", self.connection.name, resp.get("msg", resp))
        return []

    async def get_market_bars(self, symbol: str, timespan: str = "D", count: int = 50) -> list[dict[str, Any]]:
        """Get historical bars for a symbol. timespan: D (daily), M1 (1min), M5, W, M, etc."""
        category = self._detect_instrument_category(symbol)
        params = {
            "symbol": symbol,
            "category": category,
            "timespan": timespan,
            "count": str(count),
            "real_time_required": "false",
        }
        resp = await self._api_request("GET", "openapi/market-data/stock/bars", query_params=params)
        if resp.get("code") == 0:
            data = resp.get("data", [])
            return data if isinstance(data, list) else [data] if data else []
        return []

    async def get_market_hours(self) -> dict[str, Any]:
        """Get market snapshot as proxy for market hours info."""
        resp = await self._api_request("GET", "openapi/market-data/stock/snapshot", query_params={"symbols": "AAPL", "category": "US_STOCK"})
        if resp.get("code") == 0:
            data = resp.get("data", {})
            return dict(data) if isinstance(data, dict) else {}
        return {}

    @staticmethod
    def _detect_instrument_category(symbol: str) -> str:
        """Detect instrument category from symbol suffix."""
        if symbol.endswith(".HK"):
            return "HK_STOCK"
        if symbol.endswith(".SS") or symbol.endswith(".SH"):
            return "CN_STOCK"
        if symbol.endswith(".SZ"):
            return "CN_STOCK"
        return "US_STOCK"
