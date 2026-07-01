#!/usr/bin/env python3
"""Quick Webull HK sandbox endpoint discovery."""
import asyncio, json, sys, urllib.parse
sys.path.insert(0, "backend")

import httpx
from webull.core.auth.composer import default_signature_composer as sc
from webull.core.auth.algorithm import sha_hmac1
import webull.core.headers as hd
from webull.core.utils.common import get_iso_8601_date, get_uuid, json_dumps_compact, md5_hex

HOST = "api.sandbox.webull.hk"
APP_KEY = "409b24511e9a1df887a1e0f76e4cefb0"

class Explorer:
    def __init__(self):
        self.token = None

    def _sign(self, uri_path, body_params=None, query_params=None):
        sign_headers = {
            hd.APP_KEY: APP_KEY,
            hd.TIMESTAMP: get_iso_8601_date(),
            hd.SIGN_VERSION: sha_hmac1.get_signer_version(),
            hd.SIGN_ALGORITHM: sha_hmac1.get_signer_name(),
            hd.NONCE: get_uuid(),
        }
        sign_lower = {k.lower(): v for k, v in sign_headers.items()}
        sign_lower["host"] = HOST
        if query_params:
            for k, v in query_params.items():
                kl = k.lower()
                existing = sign_lower.get(kl)
                if existing is not None:
                    sign_lower[kl] = f"{existing}&{v}"
                else:
                    sign_lower[kl] = str(v)
        body_str = json_dumps_compact(body_params) if body_params is not None else ""
        body_md5 = md5_hex(body_str).upper() if body_params is not None else None
        sig_path = "/" + uri_path.lstrip("/")
        string_to_sign = sc._build_sign_string(sign_lower, sig_path, body_md5)
        app_secret = self._get_secret()
        signature = sc._gen_signature(string_to_sign, app_secret, sha_hmac1)
        headers = {
            "Content-Type": "application/json",
            "x-app-key": APP_KEY,
            "x-timestamp": sign_headers[hd.TIMESTAMP],
            "x-signature-version": sign_headers[hd.SIGN_VERSION],
            "x-signature-algorithm": sign_headers[hd.SIGN_ALGORITHM],
            "x-signature-nonce": sign_headers[hd.NONCE],
            "x-signature": signature,
        }
        if self.token:
            headers["x-access-token"] = self.token
        return headers, body_str

    def _get_secret(self):
        return "9e16899c947a9da0fc07e549f6c3e62c"

    async def get_token(self):
        app_secret = self._get_secret()
        headers, body = self._sign("openapi/auth/token/create", {
            "app_key": APP_KEY, "app_secret": app_secret, "grant_type": "client_credentials"
        })
        async with httpx.AsyncClient() as c:
            r = await c.post(f"https://{HOST}/openapi/auth/token/create", headers=headers, content=body)
        if r.status_code == 200:
            d = r.json().get("data", r.json())
            self.token = d.get("access_token") or d.get("token")
            print(f"Token: {self.token[:30]}...")
        else:
            print(f"Token fail: HTTP {r.status_code}: {r.text[:200]}")

    async def hit(self, method, path, body=None, query=None, label=None):
        headers, body_str = self._sign(path, body_params=body, query_params=query)
        url = f"https://{HOST}/{path.lstrip('/')}"
        if query and method == "GET":
            url += "?" + urllib.parse.urlencode(query, doseq=True)
        async with httpx.AsyncClient() as c:
            r = await c.request(method, url, headers=headers, content=body_str)
        tag = label or path
        try:
            data = r.json()
            preview = json.dumps(data, indent=2)[:400]
            print(f"\n  {'='*60}")
            print(f"  [{tag}] HTTP {r.status_code}")
            print(f"  {preview}")
        except:
            print(f"\n  [{tag}] HTTP {r.status_code} (non-JSON)")
            print(f"  {r.text[:200]}")

async def main():
    e = Explorer()
    await e.get_token()
    if not e.token:
        return

    await e.hit("GET", "openapi/account/list", label="Account List")
    await e.hit("GET", "openapi/asset/position", label="Positions")
    await e.hit("GET", "openapi/asset/history", label="Position History")
    await e.hit("GET", "openapi/trade/account", label="Trade Account")
    await e.hit("GET", "openapi/user/info", label="User Info")
    await e.hit("GET", "openapi/market/snapshot", label="Market Snapshot")
    await e.hit("GET", "openapi/market/quote", query={"symbol":"0700.HK"}, label="Quote 0700.HK")
    await e.hit("GET", "openapi/market/history", query={"symbol":"0700.HK"}, label="History 0700.HK")
    await e.hit("POST", "openapi/order/place", body={"symbol":"0700.HK","side":"BUY","order_type":"LIMIT","qty":100,"price":"380.00","time_in_force":"DAY"}, label="Place Order")
    await e.hit("GET", "openapi/order/list", label="Order List")
    await e.hit("GET", "openapi/order/detail", query={"order_id":"test"}, label="Order Detail")

asyncio.run(main())
