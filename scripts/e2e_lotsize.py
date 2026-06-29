#!/usr/bin/env python3
"""
Test: Rebalance Engine — Minimum Lot Size & Rounding Edge Cases
"""
import json, uuid, urllib.request
from urllib.request import Request
from urllib.error import HTTPError

BASE = "http://localhost:8004/api"

def req(method, path, data=None, token=None):
    url = f"{BASE}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    r = Request(url, data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r)
        raw = resp.read()
        return resp.status, json.loads(raw.decode()) if raw else {}
    except HTTPError as e:
        raw = e.read()
        return e.code, json.loads(raw.decode()) if raw else {}

# Register fresh user
suff = str(uuid.uuid4())[:8]
s, d = req("POST", "/auth/register", {
    "username": f"lottest_{suff}", "email": f"lot{suff}@t.com", "password": "Test@12345"
})
assert s == 201, f"Register failed: {d}"
tok = d["access_token"]
oid = d["organization"]["id"]

# Create broker
s, d = req("POST", "/brokers", {
    "name": "Paper", "broker_type": "paper",
    "config_json": {"initial_balance": 100000}
}, token=tok)
bc_id = d["id"]

print("="*60)
print("  Lot-Size Rebalance Edge Case Tests")
print("="*60)
print()

tests_passed = 0
tests_failed = 0

def check(desc, status, expected_status, data):
    global tests_passed, tests_failed
    ok = status == expected_status
    if ok:
        tests_passed += 1
        print(f"  ✅ {desc}")
    else:
        tests_failed += 1
        print(f"  ❌ {desc}: Expected {expected_status}, got {status}: {data}")

# === TEST 1: US stock, small portfolio, 5% GOOG at $10k capital ===
print("\n--- US Stock: 1% AAPL of $10k total (can't buy 1 share of GOOG) ---")
s, d = req("POST", "/portfolios", {
    "name": "US Edge Case",
    "broker_connection_id": bc_id,
    "cash_reserve_pct": 0,
}, token=tok)
pid = d["id"]

# Add AAPL as the main holding to establish total_value = $10,000
s, d = req("POST", f"/portfolios/{pid}/holdings", {
    "symbol": "AAPL", "target_weight_pct": 95.0,
    "current_shares": 50, "current_price": 200.0,
    "avg_cost": 190.0, "market": "US",
}, token=tok)
check("Add AAPL (market value $10k)", s, 201, d)

# Total = $10,000 (AAPL 50×200). GOOGL target 5% = $500. $500/$1,680 = 0.29 < 1 share → REJECTED
s, d = req("POST", f"/portfolios/{pid}/holdings", {
    "symbol": "GOOGL", "target_weight_pct": 5.0,
    "current_shares": 0, "current_price": 1680.0,
    "avg_cost": 0, "market": "US",
}, token=tok)
check("Reject GOOGL 5% (< min 1 share)", s, 400, d)
if s == 400:
    check("Error mentions minimum shares", "Minimum 1 share" in str(d.get("detail","")), True, d)

# Now try GOOGL at 17% (just above 16.8% threshold = 1 share)
s, d = req("POST", f"/portfolios/{pid}/holdings", {
    "symbol": "GOOGL", "target_weight_pct": 17.0,
    "current_shares": 0, "current_price": 1680.0,
    "avg_cost": 0, "market": "US",
}, token=tok)
check("Accept GOOGL 17% (can buy 1 share)", s, 201, d)
check("lot_size=1 for US", d.get("lot_size"), 1, d)

# === TEST 2: HK stock, lot size test ===
print("\n--- HK Stock: Tencent 0700 (100 shares/lot) ---")
s, d = req("POST", "/portfolios", {
    "name": "HK Test",
    "broker_connection_id": bc_id,
    "cash_reserve_pct": 0, "base_currency": "HKD",
}, token=tok)
pid2 = d["id"]

# Tencent at 380 HKD, 5% of 100k = 5,000 HKD → 5000/380 = 13.15 shares → round to 0 lots
s, d = req("POST", f"/portfolios/{pid2}/holdings", {
    "symbol": "0700.HK", "target_weight_pct": 5.0,
    "current_shares": 0, "current_price": 380.0, "market": "HK", "currency": "HKD",
    "total_capital": 100000,
}, token=tok)
check("Add Tencent HK", s, 201, d)
check("lot_size=100 (HK lot)", d.get("lot_size"), 100, d)

# === TEST 3: HK stock, sufficient capital for 1 lot ===
print("\n--- HK Stock: Tencent 50% of $200k (enough for 2 lots) ---")
s, d = req("POST", "/portfolios", {
    "name": "HK Sufficient",
    "broker_connection_id": bc_id,
    "cash_reserve_pct": 0, "base_currency": "HKD",
}, token=tok)
pid3 = d["id"]

# Override total_value simulation — add a holding with market value
s, d = req("POST", f"/portfolios/{pid3}/holdings", {
    "symbol": "0700.HK", "target_weight_pct": 50.0,
    "current_shares": 100, "current_price": 380.0,
    "avg_cost": 350.0, "market": "HK", "currency": "HKD",
}, token=tok)
check("Add Tencent 100 shares", s, 201, d)

s, d = req("POST", f"/portfolios/{pid3}/holdings", {
    "symbol": "AAPL", "target_weight_pct": 50.0,
    "current_shares": 50, "current_price": 200.0,
    "avg_cost": 190.0, "market": "US", "currency": "USD",
}, token=tok)
check("Add AAPL 50 shares", s, 201, d)

# Portfolio value: 100*380 + 50*200 = 38,000 + 10,000 = 48,000
# Target: 0700=50%→24,000, AAPL=50%→24,000
# Current: 0700=38,000=SURPLUS, AAPL=10,000=NEED MORE
# Sell 0700: (24000-38000)/380 = -36.84 → round to lot: needs ceil of 36.84/100 = 0.3684→1 lot = 100 shares (sell 100)
# Buy AAPL: (24000-10000)/200 = 70 shares → 70 lots of 1 = 70 shares

s, d = req("POST", f"/portfolios/{pid3}/rebalance/plan", token=tok)
check("HK+US rebalance plan", s, 200, d)
if s == 200:
    ords = d.get("orders", [])
    print(f"    Orders generated: {len(ords)}")
    for o in ords:
        print(f"    {o['side'].upper()} {o['symbol']}: {o.get('diff_shares', '?')} shares @ ${o.get('estimated_price', '?')} "
              f"(lot_size={o.get('lot_size', '?')})")
    check(f"Plan: {len(ords)} orders", len(ords) > 0, True, d)
    # Check 0700 sell: should be in whole lots
    sell_0700 = [o for o in ords if o['symbol'] == '0700.HK' and o['side'] == 'sell']
    if sell_0700:
        qty = float(sell_0700[0]['diff_shares'])
        check(f"0700 sell qty {qty} is multiple of 100", qty % 100 == 0, True, sell_0700[0])

# === TEST 4: Execute rebalance ===
s, d = req("POST", f"/portfolios/{pid3}/rebalance/execute", {
    "order_type": "market", "confirm": True
}, token=tok)
check("Execute rebalance", s, 200, d)
if s == 200:
    check(f"Rebalance: {len(d)} orders created", len(d) > 0, True, d)

# === TEST 5: CN A-share lot size ===
print("\n--- China A-Share: Kweichow Moutai (100 shares/lot) ---")
s, d = req("POST", "/portfolios", {
    "name": "CN Test", "broker_connection_id": bc_id,
    "cash_reserve_pct": 0,
}, token=tok)
pid4 = d["id"]

s, d = req("POST", f"/portfolios/{pid4}/holdings", {
    "symbol": "600519.SH", "target_weight_pct": 100.0,
    "current_shares": 0, "current_price": 1880.0,
    "market": "CN", "currency": "CNY",
}, token=tok)
check("Add Moutai CN", s, 201, d)
check("lot_size=100 (CN A-share)", d.get("lot_size"), 100, d)

# === TEST 6: Broker adapters loaded correctly ===
print("\n--- Broker Adapter Types ---")
s, d = req("GET", "/brokers/types")
check("Broker types loaded", s, 200, d)
if s == 200:
    types = {t["type"] for t in d}
    expected = {"paper", "futu", "webull_hk", "webull_us", "moomoo",
                "tiger", "interactive_brokers", "alpaca", "binance", "bybit", "okx"}
    missing = expected - types
    check(f"All 11 broker types registered (missing: {missing})", len(missing), 0, list(types))

# === SUMMARY ===
print()
print("="*60)
print(f"  RESULTS: {tests_passed} passed, {tests_failed} failed out of {tests_passed + tests_failed}")
print("="*60)
exit(0 if tests_failed == 0 else 1)
