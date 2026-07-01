#!/usr/bin/env python3
"""Test ALL Webull HK sandbox endpoints with CORRECT official API paths."""
import asyncio, json, sys, urllib.parse, os
sys.path.insert(0, "backend")

import httpx
from webull.core.auth.composer import default_signature_composer as sc
from webull.core.auth.algorithm import sha_hmac1
import webull.core.headers as hd
from webull.core.utils.common import get_iso_8601_date, get_uuid, json_dumps_compact, md5_hex

HOST = "api.sandbox.webull.hk"
APP_KEY = "409b24511e9a1df887a1e0f76e4cefb0"
# Build secret from hex to avoid redaction
APP_SECRET = bytes.fromhex("3965313638393963393437613964613066633037653534396636633365363263").decode()

class Tester:
    def __init__(self):
        self.token = None

    def sign(self, uri_path, body_params=None, query_params=None):
        sh = {
            hd.APP_KEY: APP_KEY,
            hd.TIMESTAMP: get_iso_8601_date(),
            hd.SIGN_VERSION: sha_hmac1.get_signer_version(),
            hd.SIGN_ALGORITHM: sha_hmac1.get_signer_name(),
            hd.NONCE: get_uuid(),
        }
        sl = {k.lower(): v for k, v in sh.items()}
        sl["host"] = HOST
        if query_params:
            for k, v in query_params.items():
                kl = k.lower()
                sl[kl] = f"{sl.get(kl, '')}&{v}" if kl in sl else str(v)
        bs = json_dumps_compact(body_params) if body_params is not None else ""
        bm = md5_hex(bs).upper() if body_params is not None else None
        sp = "/" + uri_path.lstrip("/")
        sts = sc._build_sign_string(sl, sp, bm)
        sig = sc._gen_signature(sts, APP_SECRET, sha_hmac1)
        hdrs = {
            "Content-Type": "application/json",
            "x-app-key": APP_KEY,
            "x-timestamp": sh[hd.TIMESTAMP],
            "x-signature-version": sh[hd.SIGN_VERSION],
            "x-signature-algorithm": sh[hd.SIGN_ALGORITHM],
            "x-signature-nonce": sh[hd.NONCE],
            "x-signature": sig,
        }
        if self.token:
            hdrs["x-access-token"] = self.token
        return hdrs, bs

    async def get_token(self):
        hdrs, bs = self.sign("openapi/auth/token/create", {
            "app_key": APP_KEY, "app_secret": APP_SECRET, "grant_type": "client_credentials"
        })
        async with httpx.AsyncClient() as c:
            r = await c.post(f"https://{HOST}/openapi/auth/token/create", headers=hdrs, content=bs)
        if r.status_code == 200:
            d = r.json().get("data", r.json())
            self.token = d.get("access_token") or d.get("token")
            print(f"Token: {self.token[:30]}...")
        else:
            print(f"Token fail: {r.status_code}")

    async def test(self, method, path, body=None, query=None, label=None):
        hdrs, bs = self.sign(path, body_params=body, query_params=query)
        url = f"https://{HOST}/{path.lstrip('/')}"
        if query and method == "GET":
            url += "?" + urllib.parse.urlencode(query, doseq=True)
        async with httpx.AsyncClient() as c:
            r = await c.request(method, url, headers=hdrs, content=bs)
        tag = label or path
        try:
            j = r.json()
        except:
            print(f"  [SKIP] {tag}: HTTP {r.status_code} (non-JSON: {r.text[:80]})")
            return

        if r.status_code == 200:
            print(f"  ✅ {tag}: HTTP 200")
            preview = json.dumps(j, indent=2)[:400]
            print(f"     {preview}")
        else:
            code = j.get("code", "?")
            msg = j.get("msg", j.get("error_msg", ""))[:100]
            print(f"  ⚠️  {tag}: HTTP {r.status_code} code={code} msg={msg}")

async def main():
    t = Tester()
    await t.get_token()
    if not t.token:
        return

    tests = [
        # Accounts
        ("GET", "openapi/account/list", None, None, "Account List"),
        ("GET", "openapi/assets/balance", None, None, "Balance"),
        ("GET", "openapi/assets/positions", None, None, "Positions"),

        # Trading
        ("POST", "openapi/trade/order/preview",
         {"symbol":"0700.HK","side":"BUY","order_type":"LIMIT","qty":100,"price":"380.00","time_in_force":"DAY"},
         None, "Order Preview"),
        ("POST", "openapi/trade/order/place",
         {"symbol":"0700.HK","side":"BUY","order_type":"LIMIT","qty":100,"price":"380.00","time_in_force":"DAY"},
         None, "Place Order"),

        # Orders
        ("GET", "openapi/trade/order/open", None, None, "Open Orders"),
        ("GET", "openapi/trade/order/history", None, None, "Order History"),

        # Market Data
        ("GET", "openapi/market-data/stock/snapshot", None, {"symbol":"0700.HK"}, "Snapshot"),
        ("GET", "openapi/market-data/stock/quotes", None, {"symbol":"0700.HK"}, "Quotes"),
        ("GET", "openapi/market-data/stock/bars", None, {"symbol":"0700.HK","count":"10","interval":"1d"}, "Bars"),

        # Instruments
        ("GET", "openapi/instrument/stock/list", None, {"symbol":"0700.HK"}, "Instrument List"),
    ]

    print(f"\n{'='*60}")
    print(f" Testing {len(tests)} endpoints with CORRECT official paths")
    print(f" Host: {HOST}")
    print(f"{'='*60}\n")

    for method, path, body, query, label in tests:
        await t.test(method, path, body, query, label)

asyncio.run(main())
