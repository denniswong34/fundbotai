#!/usr/bin/env python3
"""Test min unit validation on add_holding"""
import json, uuid, urllib.request
from urllib.request import Request
from urllib.error import HTTPError

BASE = "http://localhost:8004/api"

def req(method, path, data=None, token=None):
    url = f"{BASE}{path}"
    headers = {"Content-Type": "application/json"}
    if token: headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    try:
        r = Request(url, data=body, headers=headers, method=method)
        resp = urllib.request.urlopen(r)
        raw = resp.read()
        return resp.status, json.loads(raw.decode()) if raw else {}
    except HTTPError as e:
        raw = e.read()
        return e.code, json.loads(raw.decode()) if raw else {}

suff = str(uuid.uuid4())[:8]

# Register
s, d = req("POST", "/auth/register", {
    "username": f"mint_{suff}", "email": f"m{suff}@t.com", "password": "Test12345"
})
assert s == 201, f"Register: {d}"
tok = d["access_token"]

# Create broker
s, d = req("POST", "/brokers", {"name": "Paper", "broker_type": "paper", "config_json": {}}, token=tok)
bc_id = d["id"]

# Create portfolio
s, d = req("POST", "/portfolios", {
    "name": "Min Unit Test", "broker_connection_id": bc_id, "cash_reserve_pct": 0
}, token=tok)
pid = d["id"]

# Add AAPL as main holding → total_value = $10,000
s, d = req("POST", f"/portfolios/{pid}/holdings", {
    "symbol": "AAPL", "target_weight_pct": 95.0,
    "current_shares": 50, "current_price": 200.0,
    "avg_cost": 190.0, "market": "US",
}, token=tok)
assert s == 201, f"AAPL: {d}"
print(f"✅ AAPL added: market_value=$10,000")

# TEST: GOOGL at 1% → 1% of $10k = $100 < $1,680 (1 share)
print("\n--- Test: 1% GOOGL of $10k (should FAIL) ---")
s, d = req("POST", f"/portfolios/{pid}/holdings", {
    "symbol": "GOOGL", "target_weight_pct": 1.0,
    "current_shares": 0, "current_price": 1680.0,
    "avg_cost": 0, "market": "US",
}, token=tok)
if s == 400:
    print(f"✅ REJECTED (400): {d.get('detail', '')}")
elif s == 201:
    print(f"❌ ACCEPTED but should have been rejected")
else:
    print(f"❌ Unexpected status {s}: {d}")

# TEST: GOOGL at 20% → 20% of $10k = $2,000 > $1,680 (1 share, ok)
print("\n--- Test: 20% GOOGL of $10k (should PASS) ---")
s, d = req("POST", f"/portfolios/{pid}/holdings", {
    "symbol": "GOOGL", "target_weight_pct": 20.0,
    "current_shares": 0, "current_price": 1680.0,
    "avg_cost": 0, "market": "US",
}, token=tok)
if s == 201:
    print(f"✅ ACCEPTED: lot_size={d.get('lot_size')}, target={d.get('target_weight_pct')}%")
elif s == 400:
    print(f"❌ REJECTED but should pass: {d.get('detail', '')}")
    print(f"   (20% of $10k = $2,000, need $1,680 for 1 share)")
else:
    print(f"❌ Unexpected status {s}: {d}")

# TEST: HK stock at 0.5% (too small)
print("\n--- Test: 0.5% Tencent HK of $10k (should FAIL, need 100 shares) ---")
s, d = req("POST", f"/portfolios/{pid}/holdings", {
    "symbol": "0700.HK", "target_weight_pct": 0.5,
    "current_shares": 0, "current_price": 380.0,
    "avg_cost": 0, "market": "HK", "currency": "HKD",
}, token=tok)
if s == 400:
    print(f"✅ REJECTED (400): {d.get('detail', '')}")
else:
    print(f"❌ Status {s}: {d}")

# TEST: HK stock at 80% (should pass: 80% of $10k = $8,000 → $8,000/$380 = 21 lots)
print("\n--- Test: 80% Tencent HK of $10k (should PASS) ---")
s, d = req("POST", f"/portfolios/{pid}/holdings", {
    "symbol": "0700.HK", "target_weight_pct": 80.0,
    "current_shares": 0, "current_price": 380.0,
    "avg_cost": 0, "market": "HK", "currency": "HKD",
}, token=tok)
if s == 201:
    print(f"✅ ACCEPTED: lot_size={d.get('lot_size')}")
else:
    print(f"❌ Status {s}: {d}")

print("\n" + "="*60)
print("  Tests complete!")
