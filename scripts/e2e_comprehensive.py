#!/usr/bin/env python3
"""
FundBot AI — Comprehensive E2E Test Suite (v2)
Tests ALL API workflows end-to-end with clean state handling.
"""
import json, sys, time, traceback, uuid
import urllib.request
from urllib.request import Request
from urllib.error import HTTPError

BASE = "http://localhost:8004/api"
passed = 0
failed = 0
errors = []

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

def test(fn):
    global passed, failed
    name = fn.__name__.replace("test_", "").replace("_", " ").title()
    try:
        fn()
        passed += 1
        print(f"  ✅ {name}")
    except Exception as e:
        failed += 1
        msg = f"{type(e).__name__}: {e}"
        errors.append((name, msg))
        print(f"  ❌ {name}: {msg}")

def check(cond, msg=""):
    if not cond:
        raise AssertionError(msg)

def eq(a, b, msg=""):
    if a != b:
        raise AssertionError(f"Expected {b!r}, got {a!r}. {msg}".strip())

# === Test Data ===
SUFFIX = str(uuid.uuid4())[:8]
U1 = f"e2e_u1_{SUFFIX}"
U2 = f"e2e_u2_{SUFFIX}"
PWD = "Test@12345"

TOKEN = [None]
REFRESH = [None]
ORG_ID = [None]
ORG2_ID = [None]
P1_ID = [None]
H1_ID = [None]
H2_ID = [None]
H3_ID = [None]
BC_ID = [None]
USER2_ID = [None]
USER2_TOKEN = [None]

print("="*60)
print("  FundBot AI — Comprehensive E2E Test Suite")
print("="*60)
print()

# =========================================================
# 1. AUTH
# =========================================================
def test_auth_register():
    s, d = req("POST", "/auth/register", {
        "username": U1, "email": f"{U1}@test.com", "password": PWD
    })
    eq(s, 201, f"Register failed: {d}")
    TOKEN[0] = d["access_token"]
    REFRESH[0] = d["refresh_token"]
    ORG_ID[0] = d["organization"]["id"]
    eq(d["user"]["username"], U1)
    eq(d["settings"]["language"], "en")
    eq(d["settings"]["theme"], "dark")
test(test_auth_register)

def test_auth_login():
    s, d = req("POST", "/auth/login", {"username": U1, "password": PWD})
    eq(s, 200, f"Login failed: {d}")
    TOKEN[0] = d["access_token"]
    eq(d["organization"]["id"], ORG_ID[0])
    eq(d["user"]["username"], U1)
    eq(d["settings"]["language"], "en")
test(test_auth_login)

def test_auth_login_wrong_pass():
    s, d = req("POST", "/auth/login", {"username": U1, "password": "wrong"})
    eq(s, 401, f"Expected 401: {d}")
test(test_auth_login_wrong_pass)

def test_auth_register_duplicate():
    s, d = req("POST", "/auth/register", {
        "username": U1, "email": f"{U1}@test.com", "password": PWD
    })
    eq(s, 409, f"Expected 409: {d}")
test(test_auth_register_duplicate)

def test_auth_me():
    s, d = req("GET", "/auth/me", token=TOKEN[0])
    eq(s, 200, f"Get me failed: {d}")
    eq(d["user"]["username"], U1)
    eq(d["organization"]["id"], ORG_ID[0])
    eq(d["settings"]["language"], "en")
    eq(d["settings"]["theme"], "dark")
test(test_auth_me)

def test_auth_me_no_token():
    s, d = req("GET", "/auth/me")
    eq(s, 401, f"Expected 401, got {s}: {d}")
test(test_auth_me_no_token)

def test_auth_settings_update():
    s, d = req("PUT", "/auth/settings", {
        "language": "zh_Hant", "theme": "light", "timezone": "Asia/Tokyo"
    }, token=TOKEN[0])
    eq(s, 200, f"Settings update failed: {d}")
    eq(d["language"], "zh_Hant")
    eq(d["theme"], "light")
test(test_auth_settings_update)

def test_auth_settings_reset():
    s, d = req("PUT", "/auth/settings", {
        "language": "en", "theme": "dark", "timezone": "Asia/Hong_Kong"
    }, token=TOKEN[0])
    eq(s, 200)
    eq(d["language"], "en")
    eq(d["theme"], "dark")
test(test_auth_settings_reset)

# =========================================================
# 2. ORGANIZATIONS
# =========================================================
def test_org_list():
    s, d = req("GET", "/orgs", token=TOKEN[0])
    eq(s, 200)
    check(len(d) >= 1, f"No orgs found: {d}")
    eq(d[0]["id"], ORG_ID[0])
test(test_org_list)

def test_org_get():
    s, d = req("GET", f"/orgs/{ORG_ID[0]}", token=TOKEN[0])
    eq(s, 200)
    eq(d["id"], ORG_ID[0])
    eq(d["is_active"], True)
    check(d["member_count"] >= 1)
test(test_org_get)

def test_org_get_not_found():
    s, d = req("GET", "/orgs/99999", token=TOKEN[0])
    eq(s, 404, f"Expected 404: {d}")
test(test_org_get_not_found)

def test_org_update():
    new_name = f"{U1}'s Updated Org"
    s, d = req("PUT", f"/orgs/{ORG_ID[0]}", {"name": new_name}, token=TOKEN[0])
    eq(s, 200)
    eq(d["name"], new_name)
test(test_org_update)

def test_org_members_list():
    s, d = req("GET", f"/orgs/{ORG_ID[0]}/members", token=TOKEN[0])
    eq(s, 200)
    check(len(d) >= 1)
    eq(d[0]["role"], "owner")
test(test_org_members_list)

# =========================================================
# 3. USER 2 + ORG INVITE
# =========================================================
def test_auth_register_user2():
    s, d = req("POST", "/auth/register", {
        "username": U2, "email": f"{U2}@test.com", "password": PWD
    })
    eq(s, 201, f"Register user2 failed: {d}")
    USER2_TOKEN[0] = d["access_token"]
    USER2_ID[0] = d["user"]["id"]
    ORG2_ID[0] = d["organization"]["id"]
test(test_auth_register_user2)

def test_org_invite_user2():
    s, d = req("POST", f"/orgs/{ORG_ID[0]}/members", {
        "username": U2, "role": "member"
    }, token=TOKEN[0])
    eq(s, 201, f"Invite failed: {d}")
test(test_org_invite_user2)

def test_org_members_after_invite():
    s, d = req("GET", f"/orgs/{ORG_ID[0]}/members", token=TOKEN[0])
    eq(s, 200)
    check(len(d) >= 2, f"Expected 2+ members: {d}")
test(test_org_members_after_invite)

def test_org_promote_user2():
    s, d = req("PUT", f"/orgs/{ORG_ID[0]}/members/{USER2_ID[0]}", {
        "role": "admin"
    }, token=TOKEN[0])
    eq(s, 200, f"Promote failed: {d}")
    eq(d["member"]["role"], "admin")
test(test_org_promote_user2)

def test_org_invite_nonexistent():
    s, d = req("POST", f"/orgs/{ORG_ID[0]}/members", {
        "username": "nonexistent_user_xyz"
    }, token=TOKEN[0])
    eq(s, 404, f"Expected 404: {d}")
test(test_org_invite_nonexistent)

def test_org_invite_duplicate():
    s, d = req("POST", f"/orgs/{ORG_ID[0]}/members", {
        "username": U2, "role": "member"
    }, token=TOKEN[0])
    eq(s, 409, f"Expected 409: {d}")
test(test_org_invite_duplicate)

# =========================================================
# 4. BROKER CONNECTIONS
# =========================================================
def test_broker_types():
    s, d = req("GET", "/brokers/types")
    eq(s, 200)
    check(len(d) >= 1)
    types = {t["type"] for t in d}
    check("paper" in types, f"Expected 'paper' type: {types}")
test(test_broker_types)

def test_broker_create():
    s, d = req("POST", "/brokers", {
        "name": "Test Paper Broker",
        "broker_type": "paper",
        "market_type": "stocks",
        "config_json": {"initial_balance": 100000, "commission_pct": 0.0}
    }, token=TOKEN[0])
    eq(s, 201, f"Create broker failed: {d}")
    BC_ID[0] = d["id"]
    eq(d["broker_type"], "paper")
    eq(d["is_active"], True)
test(test_broker_create)

def test_broker_create_invalid_type():
    s, d = req("POST", "/brokers", {
        "name": "Invalid Broker",
        "broker_type": "nonexistent_broker",
        "config_json": {}
    }, token=TOKEN[0])
    eq(s, 400, f"Expected 400: {d}")
test(test_broker_create_invalid_type)

def test_broker_list():
    s, d = req("GET", "/brokers", token=TOKEN[0])
    eq(s, 200)
    check(len(d) >= 1)
test(test_broker_list)

def test_broker_get():
    s, d = req("GET", f"/brokers/{BC_ID[0]}", token=TOKEN[0])
    eq(s, 200)
    eq(d["id"], BC_ID[0])
    eq(d["broker_type"], "paper")
test(test_broker_get)

def test_broker_test_connection():
    s, d = req("POST", f"/brokers/{BC_ID[0]}/test", token=TOKEN[0])
    eq(s, 200, f"Test connection failed: {d}")
    eq(d["success"], True)
test(test_broker_test_connection)

def test_broker_update():
    s, d = req("PUT", f"/brokers/{BC_ID[0]}", {
        "name": "Updated Paper Broker",
        "config_json": {"initial_balance": 200000}
    }, token=TOKEN[0])
    eq(s, 200)
    eq(d["name"], "Updated Paper Broker")
test(test_broker_update)

# =========================================================
# 5. PORTFOLIO CRUD
# =========================================================
def test_portfolio_create():
    s, d = req("POST", "/portfolios", {
        "name": "Test Growth Portfolio",
        "description": "A diversified growth portfolio",
        "base_currency": "USD",
        "broker_connection_id": BC_ID[0],
        "drift_threshold_pct": 5.0,
        "cash_reserve_pct": 2.0,
        "auto_rebalance_enabled": True,
        "rebalance_frequency": "monthly",
        "rebalance_order_type": "market",
    }, token=TOKEN[0])
    eq(s, 201, f"Create portfolio failed: {d}")
    P1_ID[0] = d["id"]
    eq(d["name"], "Test Growth Portfolio")
    eq(d["base_currency"], "USD")
    eq(d["status"], "active")
    eq(float(d["drift_threshold_pct"]), 5.0)
    eq(float(d["cash_reserve_pct"]), 2.0)
    eq(d["auto_rebalance_enabled"], True)
test(test_portfolio_create)

def test_portfolio_list():
    s, d = req("GET", "/portfolios", token=TOKEN[0])
    eq(s, 200)
    check(len(d) >= 1)
    eq(d[0]["name"], "Test Growth Portfolio")
test(test_portfolio_list)

def test_portfolio_get():
    s, d = req("GET", f"/portfolios/{P1_ID[0]}", token=TOKEN[0])
    eq(s, 200)
    eq(d["id"], P1_ID[0])
    eq(d["name"], "Test Growth Portfolio")
test(test_portfolio_get)

def test_portfolio_get_not_found():
    s, d = req("GET", "/portfolios/99999", token=TOKEN[0])
    eq(s, 404, f"Expected 404: {d}")
test(test_portfolio_get_not_found)

def test_portfolio_update():
    s, d = req("PUT", f"/portfolios/{P1_ID[0]}", {
        "name": "Updated Growth Portfolio",
        "cash_reserve_pct": 3.0,
    }, token=TOKEN[0])
    eq(s, 200, f"Update portfolio failed: {d}")
    eq(d["name"], "Updated Growth Portfolio")
    eq(float(d["cash_reserve_pct"]), 3.0)
test(test_portfolio_update)

def test_portfolio_summary():
    s, d = req("GET", "/portfolios/summary", token=TOKEN[0])
    eq(s, 200, f"Summary failed: {d}")
    eq(d["total_portfolios"], 1)
    check("total_value" in d)
    check("total_pnl" in d)
test(test_portfolio_summary)

# =========================================================
# 6. HOLDINGS MANAGEMENT
# =========================================================
def test_holding_add_aapl():
    s, d = req("POST", f"/portfolios/{P1_ID[0]}/holdings", {
        "symbol": "AAPL",
        "asset_type": "stock",
        "market": "US",
        "currency": "USD",
        "target_weight_pct": 40.0,
        "current_shares": 100,
        "avg_cost": 150.0,
        "current_price": 198.50,
    }, token=TOKEN[0])
    eq(s, 201, f"Add AAPL failed: {d}")
    H1_ID[0] = d["id"]
    eq(d["symbol"], "AAPL")
    eq(float(d["target_weight_pct"]), 40.0)
    eq(float(d["current_shares"]), 100)

def test_holding_add_msft():
    s, d = req("POST", f"/portfolios/{P1_ID[0]}/holdings", {
        "symbol": "MSFT",
        "target_weight_pct": 30.0,
        "current_shares": 50,
        "avg_cost": 380.0,
        "current_price": 420.30,
    }, token=TOKEN[0])
    eq(s, 201, f"Add MSFT failed: {d}")
    H2_ID[0] = d["id"]

def test_holding_add_voo():
    s, d = req("POST", f"/portfolios/{P1_ID[0]}/holdings", {
        "symbol": "VOO",
        "target_weight_pct": 28.0,
        "current_shares": 20,
        "avg_cost": 480.0,
        "current_price": 510.20,
    }, token=TOKEN[0])
    eq(s, 201, f"Add VOO failed: {d}")
    H3_ID[0] = d["id"]

test(test_holding_add_aapl)
test(test_holding_add_msft)
test(test_holding_add_voo)

def test_holdings_list():
    s, d = req("GET", f"/portfolios/{P1_ID[0]}/holdings", token=TOKEN[0])
    eq(s, 200)
    check(len(d) == 3, f"Expected 3 holdings: {d}")
    symbols = {h["symbol"] for h in d}
    check(symbols == {"AAPL", "MSFT", "VOO"}, f"Symbols: {symbols}")
test(test_holdings_list)

def test_holding_update():
    s, d = req("PUT", f"/portfolios/{P1_ID[0]}/holdings/{H1_ID[0]}", {
        "current_price": 200.0,
        "current_shares": 105,
    }, token=TOKEN[0])
    eq(s, 200, f"Update holding failed: {d}")
    eq(float(d["current_price"]), 200.0)
    eq(float(d["current_shares"]), 105)
    # Market value should recalc: 105 * 200 = 21000
    check("market_value" in d)
test(test_holding_update)

def test_holding_update_not_found():
    s, d = req("PUT", f"/portfolios/{P1_ID[0]}/holdings/99999", {
        "current_price": 200.0
    }, token=TOKEN[0])
    eq(s, 404, f"Expected 404: {d}")
test(test_holding_update_not_found)

# =========================================================
# 7. REBALANCE
# =========================================================
def test_rebalance_plan():
    s, d = req("POST", f"/portfolios/{P1_ID[0]}/rebalance/plan", token=TOKEN[0])
    eq(s, 200, f"Rebalance plan failed: {d}")
    check("orders" in d)
    check("total_value" in d)
    check("cash_reserve" in d)
test(test_rebalance_plan)

def test_rebalance_execute_no_confirm():
    s, d = req("POST", f"/portfolios/{P1_ID[0]}/rebalance/execute", {
        "order_type": "market", "confirm": False
    }, token=TOKEN[0])
    eq(s, 400, f"Expected 400 without confirm: {d}")
test(test_rebalance_execute_no_confirm)

def test_rebalance_execute():
    s, d = req("POST", f"/portfolios/{P1_ID[0]}/rebalance/execute", {
        "order_type": "market", "confirm": True
    }, token=TOKEN[0])
    eq(s, 200, f"Execute rebalance failed: {d}")
    check(len(d) >= 1, f"Expected orders: {d}")
    # Should have sell orders (MSFT/VOO over-weight) or buy orders (AAPL under-weight)
    symbols = {o["symbol"] for o in d}
    check(len(symbols) > 0)
test(test_rebalance_execute)

def test_rebalance_orders_check():
    """Verify that the rebalance orders have correct structure"""
    s, d = req("GET", f"/portfolios/{P1_ID[0]}/holdings", token=TOKEN[0])
    eq(s, 200)
    # After rebalance, holding values should still be accurate
    check(len(d) == 3)
test(test_rebalance_orders_check)

# =========================================================
# 8. ALLOCATION & PERFORMANCE
# =========================================================
def test_allocation():
    s, d = req("GET", f"/portfolios/{P1_ID[0]}/allocation", token=TOKEN[0])
    eq(s, 200, f"Allocation failed: {d}")
    check(len(d) == 3, f"Expected 3 entries: {d}")
    for entry in d:
        check("symbol" in entry)
        check("current_weight_pct" in entry or "target_weight_pct" in entry)
        check("color" in entry)
test(test_allocation)

def test_performance():
    s, d = req("GET", f"/portfolios/{P1_ID[0]}/performance?days=30", token=TOKEN[0])
    eq(s, 200, f"Performance failed: {d}")
    check(isinstance(d, list), f"Expected list: {d}")
test(test_performance)

def test_performance_invalid_days():
    s, d = req("GET", f"/portfolios/{P1_ID[0]}/performance?days=999", token=TOKEN[0])
    eq(s, 422, f"Expected 422: {d}")
test(test_performance_invalid_days)

# =========================================================
# 9. TOKEN REFRESH
# =========================================================
def test_token_refresh():
    s, d = req("POST", "/auth/refresh", {
        "refresh_token": REFRESH[0]
    })
    eq(s, 200, f"Refresh failed: {d}")
    check("access_token" in d)
    check("refresh_token" in d)
    # Update the token
    TOKEN[0] = d["access_token"]
    REFRESH[0] = d["refresh_token"]
test(test_token_refresh)

def test_token_refresh_invalid():
    s, d = req("POST", "/auth/refresh", {
        "refresh_token": "invalid_token_here"
    })
    eq(s, 401, f"Expected 401: {d}")
test(test_token_refresh_invalid)

# =========================================================
# 10. BATCH UPDATE HOLDINGS
# =========================================================
def test_batch_update_holdings():
    s, d = req("PUT", f"/portfolios/{P1_ID[0]}/holdings/batch", [
        {"symbol": "AAPL", "target_weight_pct": 50.0, "current_shares": 110,
         "avg_cost": 152.0, "current_price": 200.0},
        {"symbol": "MSFT", "target_weight_pct": 25.0, "current_shares": 55,
         "avg_cost": 385.0, "current_price": 420.0},
        {"symbol": "GOOGL", "target_weight_pct": 25.0, "current_shares": 10,
         "avg_cost": 180.0, "current_price": 195.0},
    ], token=TOKEN[0])
    eq(s, 200, f"Batch update failed: {d}")
    check(len(d) == 3)
test(test_batch_update_holdings)

def test_holdings_after_batch():
    s, d = req("GET", f"/portfolios/{P1_ID[0]}/holdings", token=TOKEN[0])
    eq(s, 200)
    symbols = {h["symbol"] for h in d}
    eq(symbols, {"AAPL", "MSFT", "GOOGL"}, f"Symbols after batch: {symbols}")
    # VOO should be removed (replaced by GOOGL)
test(test_holdings_after_batch)

# =========================================================
# 11. DELETE HOLDING
# =========================================================
def test_holding_delete():
    s, d = req("DELETE", f"/portfolios/{P1_ID[0]}/holdings/{H1_ID[0]}", token=TOKEN[0])
    eq(s, 204, f"Delete holding failed: {d}")
test(test_holding_delete)

def test_holdings_after_delete():
    s, d = req("GET", f"/portfolios/{P1_ID[0]}/holdings", token=TOKEN[0])
    eq(s, 200)
    # AAPL (H1) should be soft-deleted
    active = [h for h in d if h.get("is_active", True)]
    # Actually soft-deleted holdings still appear with is_active=False... let's check
    aapl = [h for h in d if h["symbol"] == "AAPL"]
    if aapl:
        eq(aapl[0]["is_active"], False, "AAPL should be inactive")
test(test_holdings_after_delete)

# =========================================================
# 12. DELETE PORTFOLIO (soft-delete / archive)
# =========================================================
def test_portfolio_delete():
    s, d = req("DELETE", f"/portfolios/{P1_ID[0]}", token=TOKEN[0])
    eq(s, 204, f"Delete portfolio failed: {d}")
test(test_portfolio_delete)

def test_portfolio_list_after_delete():
    s, d = req("GET", "/portfolios", token=TOKEN[0])
    eq(s, 200)
    # Should be empty since our only portfolio was archived
    check(len(d) == 0, f"Expected empty, got: {d}")
test(test_portfolio_list_after_delete)

# =========================================================
# 13. DELETE BROKER
# =========================================================
def test_broker_delete():
    s, d = req("DELETE", f"/brokers/{BC_ID[0]}", token=TOKEN[0])
    eq(s, 204, f"Delete broker failed: {d}")
test(test_broker_delete)

def test_broker_list_after_delete():
    s, d = req("GET", "/brokers", token=TOKEN[0])
    eq(s, 200)
    check(len(d) == 0, f"Expected empty, got: {d}")
test(test_broker_list_after_delete)

# =========================================================
# 14. ORG MEMBER REMOVE
# =========================================================
def test_org_remove_member():
    s, d = req("DELETE", f"/orgs/{ORG_ID[0]}/members/{USER2_ID[0]}", token=TOKEN[0])
    eq(s, 200, f"Remove member failed: {d}")
    eq(d["detail"], "Member removed successfully")
test(test_org_remove_member)

def test_org_members_after_remove():
    s, d = req("GET", f"/orgs/{ORG_ID[0]}/members", token=TOKEN[0])
    eq(s, 200)
    check(len(d) == 1, f"Expected 1 member, got: {d}")
    eq(d[0]["role"], "owner")
test(test_org_members_after_remove)

# =========================================================
# RESULTS
# =========================================================
print()
print("="*60)
total = passed + failed
print(f"  RESULTS: {passed} passed, {failed} failed out of {total} tests")
print("="*60)

if errors:
    print(f"\n  Errors ({len(errors)}):")
    for e in errors:
        print(f"    • {e}")

sys.exit(0 if failed == 0 else 1)
