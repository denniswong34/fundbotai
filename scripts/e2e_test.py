#!/usr/bin/env python3
"""
FundBot AI — Comprehensive E2E Test Suite

Tests all major API workflows:
1. User Registration & Login
2. Organization Management
3. User Settings
4. Broker Connections CRUD
5. Portfolio CRUD
6. Holdings Management
7. Rebalance Plan & Execute
8. Performance & Allocation
9. Token Refresh
10. Error Handling (edge cases)
"""

import json
import sys
import time
import traceback
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BASE_URL = "http://localhost:8004/api"

passed = 0
failed = 0


def request(method, path, data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    req = Request(url, data=body, headers=headers, method=method)
    try:
        resp = urlopen(req)
        status = resp.status
        raw = resp.read()
        resp_data = json.loads(raw.decode()) if raw else {}
        return status, resp_data
    except HTTPError as e:
        status = e.code
        raw = e.read()
        resp_data = json.loads(raw.decode()) if raw else {}
        return status, resp_data


def test(name, fn):
    global passed, failed
    try:
        fn()
        passed += 1
        print(f"  ✅ {name}")
    except Exception as e:
        failed += 1
        print(f"  ❌ {name}: {e}")
        traceback.print_exc()


def assert_eq(a, b, msg=""):
    if a != b:
        raise AssertionError(f"Expected {b!r}, got {a!r}. {msg}".strip())


def assert_in(key, obj, msg=""):
    if key not in obj:
        raise AssertionError(f"Key '{key}' not in response: {obj}. {msg}".strip())


def assert_type(t, val, msg=""):
    if not isinstance(val, t):
        raise AssertionError(f"Expected type {t.__name__}, got {type(val).__name__}: {val}. {msg}".strip())


# ── User 1: John Doe ──────────────────────────────────
TOKEN = None
REFRESH = None
USER1_ID = None
ORG1_ID = None
SETTINGS = None

# ── User 2: Jane Doe (for org membership testing) ────
TOKEN2 = None
USER2_ID = None
ORG2_ID = None

# ── Test data ─────────────────────────────────────────
P1_ID = None
H1_ID = None
BC_ID = None


# ══════════════════════════════════════════════════════
#  1. AUTH
# ══════════════════════════════════════════════════════

def test_auth_register():
    global TOKEN, REFRESH, USER1_ID, ORG1_ID, SETTINGS
    status, data = request("POST", "/auth/register", {
        "username": "john_doe_e2e",
        "email": "john_e2e@example.com",
        "password": "TestPass123!",
        "display_name": "John Doe"
    })
    assert_eq(status, 201, f"Register failed: {data}")
    assert_in("access_token", data)
    assert_in("refresh_token", data)
    assert_in("user", data)
    assert_in("organization", data)
    assert_in("settings", data)
    TOKEN = data["access_token"]
    REFRESH = data["refresh_token"]
    USER1_ID = data["user"]["id"]
    ORG1_ID = data["organization"]["id"]
    SETTINGS = data["settings"]
    assert_eq(data["user"]["username"], "john_doe_e2e")
    assert_eq(data["organization"]["slug"], "john_doe_e2e")
    assert_eq(data["settings"]["language"], "en")


def test_auth_login():
    status, data = request("POST", "/auth/login", {
        "username": "john_doe_e2e",
        "password": "TestPass123!"
    })
    assert_eq(status, 200, f"Login failed: {data}")
    assert_in("access_token", data)
    assert_in("organization", data)
    assert_eq(data["organization"]["id"], ORG1_ID)


def test_auth_login_wrong_password():
    status, data = request("POST", "/auth/login", {
        "username": "john_doe_e2e",
        "password": "wrongpassword"
    })
    assert_eq(status, 401, f"Expected 401: {data}")


def test_auth_register_duplicate():
    status, data = request("POST", "/auth/register", {
        "username": "john_doe_e2e",
        "email": "john_e2e@example.com",
        "password": "TestPass123!"
    })
    assert_eq(status, 409, f"Expected 409: {data}")


def test_auth_me():
    status, data = request("GET", "/auth/me", token=TOKEN)
    assert_eq(status, 200)
    assert_eq(data["user"]["id"], USER1_ID)
    assert_eq(data["organization"]["id"], ORG1_ID)
    assert_in("settings", data)


def test_auth_me_no_token():
    status, data = request("GET", "/auth/me")
    assert_eq(status, 403, f"Expected 403: {data}")


def test_auth_settings_update():
    global SETTINGS
    status, data = request("PUT", "/auth/settings", {
        "language": "zh_Hant",
        "theme": "light",
        "timezone": "Asia/Hong_Kong"
    }, token=TOKEN)
    assert_eq(status, 200)
    assert_eq(data["language"], "zh_Hant")
    assert_eq(data["theme"], "light")
    assert_eq(data["timezone"], "Asia/Hong_Kong")
    SETTINGS = data


def test_auth_settings_reset():
    global SETTINGS
    status, data = request("PUT", "/auth/settings", {
        "language": "en",
        "theme": "dark",
        "timezone": "UTC"
    }, token=TOKEN)
    assert_eq(status, 200)
    assert_eq(data["language"], "en")
    assert_eq(data["theme"], "dark")
    SETTINGS = data


# ══════════════════════════════════════════════════════
#  2. ORGANIZATIONS
# ══════════════════════════════════════════════════════

def test_org_list():
    status, data = request("GET", "/orgs", token=TOKEN)
    assert_eq(status, 200)
    assert_type(list, data)
    assert len(data) >= 1
    assert_eq(data[0]["id"], ORG1_ID)


def test_org_get():
    status, data = request("GET", f"/orgs/{ORG1_ID}", token=TOKEN)
    assert_eq(status, 200)
    assert_eq(data["id"], ORG1_ID)
    assert_eq(data["slug"], "john_doe_e2e")
    assert_in("member_count", data)
    assert_eq(data["member_count"], 1)


def test_org_get_other_org():
    status, data = request("GET", "/orgs/99999", token=TOKEN)
    assert_eq(status, 404, f"Expected 404: {data}")


def test_org_update():
    status, data = request("PUT", f"/orgs/{ORG1_ID}", {
        "name": "John's Updated Org"
    }, token=TOKEN)
    assert_eq(status, 200)
    assert_eq(data["name"], "John's Updated Org")


def test_org_update_unauthorized():
    # User 2 shouldn't be able to update this org
    status, data = request("PUT", f"/orgs/{ORG1_ID}", {
        "name": "Hacked!"
    }, token=TOKEN2)
    assert_eq(status, 403, f"Expected 403: {data}")


def test_org_members_list():
    status, data = request("GET", f"/orgs/{ORG1_ID}/members", token=TOKEN)
    assert_eq(status, 200)
    assert_type(list, data)
    assert len(data) >= 1
    member = data[0]
    assert_eq(member["user_id"], USER1_ID)
    assert_eq(member["role"], "owner")


# ══════════════════════════════════════════════════════
#  3. USER 2: REGISTER & ORG MEMBERSHIP
# ══════════════════════════════════════════════════════

def test_auth_register_user2():
    global TOKEN2, USER2_ID, ORG2_ID
    status, data = request("POST", "/auth/register", {
        "username": "jane_doe_e2e",
        "email": "jane_e2e@example.com",
        "password": "TestPass456!"
    })
    assert_eq(status, 201, f"Register failed: {data}")
    TOKEN2 = data["access_token"]
    USER2_ID = data["user"]["id"]
    ORG2_ID = data["organization"]["id"]


def test_org_invite_user2():
    status, data = request("POST", f"/orgs/{ORG1_ID}/members", {
        "username": "jane_doe_e2e",
        "role": "member"
    }, token=TOKEN)
    assert_eq(status, 201, f"Invite failed: {data}")


def test_org_members_after_invite():
    status, data = request("GET", f"/orgs/{ORG1_ID}/members", token=TOKEN)
    assert_eq(status, 200)
    assert_type(list, data)
    assert len(data) >= 2
    usernames = [m.get("username") for m in data]
    assert "john_doe_e2e" in usernames
    assert "jane_doe_e2e" in usernames


def test_org_promote_user2():
    status, data = request("PUT", f"/orgs/{ORG1_ID}/members/{USER2_ID}", {
        "role": "admin"
    }, token=TOKEN)
    # Should succeed — owner can promote
    assert_eq(status, 200, f"Promote failed: {data}")


def test_org_invite_nonexistent_user():
    status, data = request("POST", f"/orgs/{ORG1_ID}/members", {
        "username": "nonexistent_user",
        "role": "member"
    }, token=TOKEN)
    assert_eq(status, 404, f"Expected 404: {data}")


def test_org_invite_duplicate():
    status, data = request("POST", f"/orgs/{ORG1_ID}/members", {
        "username": "jane_doe_e2e",
        "role": "member"
    }, token=TOKEN)
    assert_eq(status, 409, f"Expected 409: {data}")


# ══════════════════════════════════════════════════════
#  4. BROKER CONNECTIONS
# ══════════════════════════════════════════════════════

def test_broker_types():
    status, data = request("GET", "/brokers/types", token=TOKEN)
    assert_eq(status, 200)
    assert_type(list, data)
    types = {b["type"] for b in data}
    assert "paper" in types, f"Expected 'paper' in broker types: {types}"
    assert "webull" in types
    assert "alpaca" in types
    assert "binance" in types


def test_broker_create():
    global BC_ID
    status, data = request("POST", "/brokers", {
        "name": "My Paper Broker",
        "broker_type": "paper",
        "market_type": "stocks",
        "config_json": {"initial_balance": 100000, "commission_pct": 0.0}
    }, token=TOKEN)
    assert_eq(status, 201, f"Create broker failed: {data}")
    assert_in("id", data)
    BC_ID = data["id"]
    assert_eq(data["name"], "My Paper Broker")
    assert_eq(data["broker_type"], "paper")
    assert_eq(data["is_active"], True)


def test_broker_create_invalid_type():
    status, data = request("POST", "/brokers", {
        "name": "Bad Broker",
        "broker_type": "nonexistent",
        "config_json": {}
    }, token=TOKEN)
    assert_eq(status, 400, f"Expected 400: {data}")


def test_broker_list():
    status, data = request("GET", "/brokers", token=TOKEN)
    assert_eq(status, 200)
    assert_type(list, data)
    ids = [b["id"] for b in data]
    assert BC_ID in ids, f"Expected broker {BC_ID} in list"


def test_broker_test_connection():
    status, data = request("POST", f"/brokers/{BC_ID}/test", token=TOKEN)
    assert_eq(status, 200)
    assert_eq(data["success"], True)


def test_broker_update():
    status, data = request("PUT", f"/brokers/{BC_ID}", {
        "name": "Paper Broker Updated",
        "config_json": {"initial_balance": 200000}
    }, token=TOKEN)
    assert_eq(status, 200)
    assert_eq(data["name"], "Paper Broker Updated")


# ══════════════════════════════════════════════════════
#  5. PORTFOLIO CRUD
# ══════════════════════════════════════════════════════

def test_portfolio_create():
    global P1_ID
    status, data = request("POST", "/portfolios", {
        "name": "Tech Growth Portfolio",
        "description": "Aggressive tech stock portfolio",
        "base_currency": "USD",
        "broker_connection_id": BC_ID,
        "drift_threshold_pct": 5.0,
        "cash_reserve_pct": 2.0,
        "auto_rebalance_enabled": True,
        "rebalance_frequency": "weekly"
    }, token=TOKEN)
    assert_eq(status, 201, f"Create portfolio failed: {data}")
    assert_in("id", data)
    P1_ID = data["id"]
    assert_eq(data["name"], "Tech Growth Portfolio")
    assert_eq(data["auto_rebalance_enabled"], True)
    assert_eq(data["rebalance_frequency"], "weekly")
    assert_eq(data["status"], "active")


def test_portfolio_list():
    status, data = request("GET", "/portfolios", token=TOKEN)
    assert_eq(status, 200)
    assert_type(list, data)
    ids = [p["id"] for p in data]
    assert P1_ID in ids, f"Expected portfolio {P1_ID} in list"


def test_portfolio_get():
    status, data = request("GET", f"/portfolios/{P1_ID}", token=TOKEN)
    assert_eq(status, 200)
    assert_eq(data["id"], P1_ID)
    assert_eq(data["name"], "Tech Growth Portfolio")
    assert_eq(data["broker_connection_id"], BC_ID)


def test_portfolio_get_not_found():
    status, data = request("GET", "/portfolios/99999", token=TOKEN)
    assert_eq(status, 404, f"Expected 404: {data}")


def test_portfolio_update():
    status, data = request("PUT", f"/portfolios/{P1_ID}", {
        "name": "Tech Growth Portfolio V2",
        "cash_reserve_pct": 3.0,
        "drift_threshold_pct": 3.0
    }, token=TOKEN)
    assert_eq(status, 200)
    assert_eq(data["name"], "Tech Growth Portfolio V2")
    assert_eq(data["drift_threshold_pct"], "3.00")


def test_portfolio_summary():
    status, data = request("GET", "/portfolios/summary", token=TOKEN)
    assert_eq(status, 200)
    assert_in("total_portfolios", data)
    assert_in("total_value", data)
    assert_in("active_count", data)
    assert_eq(data["total_portfolios"], 1)
    assert_eq(data["active_count"], 1)


# ══════════════════════════════════════════════════════
#  6. HOLDINGS
# ══════════════════════════════════════════════════════

def test_holding_add():
    global H1_ID
    status, data = request("POST", f"/portfolios/{P1_ID}/holdings", {
        "symbol": "AAPL",
        "asset_type": "stock",
        "market": "US",
        "currency": "USD",
        "target_weight_pct": 30.0,
        "current_shares": 10,
        "avg_cost": 150.00,
        "current_price": 198.50
    }, token=TOKEN)
    assert_eq(status, 201, f"Add holding failed: {data}")
    assert_in("id", data)
    H1_ID = data["id"]
    assert_eq(data["symbol"], "AAPL")
    assert_eq(data["target_weight_pct"], "30.0000")
    # Market value should be calculated: 10 * 198.50 = 1985.00
    assert_eq(data["market_value"], "1985.00")


def test_holdings_add_msft():
    status, data = request("POST", f"/portfolios/{P1_ID}/holdings", {
        "symbol": "MSFT",
        "target_weight_pct": 20.0,
        "current_shares": 5,
        "avg_cost": 380.00,
        "current_price": 420.30,
        "market": "US",
        "currency": "USD"
    }, token=TOKEN)
    assert_eq(status, 201)
    assert_eq(data["symbol"], "MSFT")
    assert_eq(data["market_value"], "2101.50")  # 5 * 420.30


def test_holdings_add_voo():
    status, data = request("POST", f"/portfolios/{P1_ID}/holdings", {
        "symbol": "VOO",
        "target_weight_pct": 50.0,
        "current_shares": 3,
        "avg_cost": 450.00,
        "current_price": 480.20,
        "market": "US",
        "currency": "USD"
    }, token=TOKEN)
    assert_eq(status, 201)
    assert_eq(data["symbol"], "VOO")


def test_holdings_list():
    status, data = request("GET", f"/portfolios/{P1_ID}/holdings", token=TOKEN)
    assert_eq(status, 200)
    assert_type(list, data)
    assert len(data) == 3
    symbols = {h["symbol"] for h in data}
    assert symbols == {"AAPL", "MSFT", "VOO"}


def test_holding_update():
    global H1_ID
    status, data = request("PUT", f"/portfolios/{P1_ID}/holdings/{H1_ID}", {
        "target_weight_pct": 35.0,
        "current_shares": 12,
        "current_price": 200.00
    }, token=TOKEN)
    assert_eq(status, 200)
    # Recalc: 12 * 200 = 2400
    assert_eq(data["market_value"], "2400.00")


def test_holding_update_not_found():
    status, data = request("PUT", f"/portfolios/{P1_ID}/holdings/99999", {
        "target_weight_pct": 10.0
    }, token=TOKEN)
    assert_eq(status, 404, f"Expected 404: {data}")


# ══════════════════════════════════════════════════════
#  7. REBALANCE
# ══════════════════════════════════════════════════════

def test_rebalance_plan():
    status, data = request("POST", f"/portfolios/{P1_ID}/rebalance/plan", token=TOKEN)
    assert_eq(status, 200, f"Rebalance plan failed: {data}")
    assert_in("orders", data)
    assert_in("total_value", data)
    assert_in("portfolio_id", data)
    assert_eq(data["portfolio_id"], P1_ID)
    # Should have orders since weights don't match
    assert len(data["orders"]) > 0, "Expected at least 1 rebalance order"


def test_rebalance_execute_no_confirm():
    status, data = request("POST", f"/portfolios/{P1_ID}/rebalance/execute",
                           {"order_type": "market", "confirm": False}, token=TOKEN)
    assert_eq(status, 400, f"Expected 400 without confirm: {data}")


def test_rebalance_execute():
    status, data = request("POST", f"/portfolios/{P1_ID}/rebalance/execute",
                           {"order_type": "market", "confirm": True}, token=TOKEN)
    assert_eq(status, 200, f"Execute rebalance failed: {data}")
    assert_type(list, data)
    assert len(data) > 0
    first = data[0]
    assert_in("rebalance_group_id", first)
    assert_in("symbol", first)
    assert_in("side", first)
    assert_in("status", first)
    assert first["status"] == "pending"
    # Verify sell-first, buy-later ordering
    sides = [o["side"] for o in data]
    sell_positions = [i for i, s in enumerate(sides) if s == "sell"]
    buy_positions = [i for i, s in enumerate(sides) if s == "buy"]
    # All sells should come before buys
    if sell_positions and buy_positions:
        assert max(sell_positions) < min(buy_positions), \
            f"Sells should come before buys. Sides: {sides}"


# ══════════════════════════════════════════════════════
#  8. PERFORMANCE & ALLOCATION
# ══════════════════════════════════════════════════════

def test_allocation():
    status, data = request("GET", f"/portfolios/{P1_ID}/allocation", token=TOKEN)
    assert_eq(status, 200)
    assert_type(list, data)
    assert len(data) == 3
    for alloc in data:
        assert_in("symbol", alloc)
        assert_in("current_weight_pct", alloc)
        assert_in("target_weight_pct", alloc)
        assert_in("drift_pct", alloc)
        assert_in("color", alloc)
    # Target weights should add up to ~100%
    target_sum = sum(float(a["target_weight_pct"]) for a in data)
    assert abs(target_sum - 105.0) < 0.01, f"Target weights should sum to ~105: {target_sum}"


def test_performance():
    status, data = request("GET", f"/portfolios/{P1_ID}/performance?days=30", token=TOKEN)
    assert_eq(status, 200)
    assert_type(list, data)


def test_performance_invalid_days():
    status, data = request("GET", f"/portfolios/{P1_ID}/performance?days=999", token=TOKEN)
    assert_eq(status, 422, f"Expected 422: {data}")


# ══════════════════════════════════════════════════════
#  9. TOKEN REFRESH
# ══════════════════════════════════════════════════════

def test_token_refresh():
    global TOKEN, REFRESH
    # Need to decode settings first — can't see .env values
    status, data = request("POST", "/auth/refresh", {
        "refresh_token": REFRESH
    }, token=TOKEN)
    # Refresh endpoint might not require auth header (token in body)
    assert_eq(status, 200, f"Refresh failed: {data}")
    assert_in("access_token", data)
    assert_in("refresh_token", data)
    TOKEN = data["access_token"]  # Use new token going forward
    REFRESH = data["refresh_token"]


# ══════════════════════════════════════════════════════
#  10. CLEANUP & EDGE CASES
# ══════════════════════════════════════════════════════

def test_batch_update_holdings():
    status, data = request("PUT", f"/portfolios/{P1_ID}/holdings/batch", [
        {"symbol": "AAPL", "target_weight_pct": 40.0, "current_shares": 10,
         "current_price": 200.0, "avg_cost": 150.0, "market": "US", "currency": "USD"},
        {"symbol": "GOOGL", "target_weight_pct": 30.0, "current_shares": 5,
         "current_price": 180.0, "avg_cost": 160.0, "market": "US", "currency": "USD"},
        {"symbol": "AMZN", "target_weight_pct": 30.0, "current_shares": 8,
         "current_price": 220.0, "avg_cost": 200.0, "market": "US", "currency": "USD"},
    ], token=TOKEN)
    assert_eq(status, 200, f"Batch update failed: {data}")
    assert_type(list, data)
    assert len(data) == 3
    symbols = {h["symbol"] for h in data}
    assert "GOOGL" in symbols
    assert "AMZN" in symbols
    # MSFT should have been removed (deactivated)
    assert "MSFT" not in symbols, "MSFT should have been removed"


def test_holding_delete():
    # First get all holdings to find one to delete
    status, data = request("GET", f"/portfolios/{P1_ID}/holdings", token=TOKEN)
    assert_eq(status, 200)
    assert len(data) >= 1
    h_id = data[0]["id"]
    status, data = request("DELETE", f"/portfolios/{P1_ID}/holdings/{h_id}", token=TOKEN)
    assert_eq(status, 204, f"Delete holding failed: {data}")
    # Verify it's gone
    status, data = request("GET", f"/portfolios/{P1_ID}/holdings", token=TOKEN)
    assert_eq(status, 200)
    active_ids = [h["id"] for h in data]
    assert h_id not in active_ids, "Holding should not be in active list"


def test_portfolio_delete():
    status, data = request("DELETE", f"/portfolios/{P1_ID}", token=TOKEN)
    assert_eq(status, 204, f"Delete portfolio failed: {data}")
    # Verify it's archived
    status, data = request("GET", f"/portfolios/{P1_ID}", token=TOKEN)
    assert_eq(status, 200)
    assert_eq(data["status"], "archived")


def test_broker_delete():
    status, data = request("DELETE", f"/brokers/{BC_ID}", token=TOKEN)
    assert_eq(status, 204, f"Delete broker failed: {data}")
    status, data = request("GET", "/brokers", token=TOKEN)
    assert_eq(status, 200)
    assert BC_ID not in [b["id"] for b in data], "Broker should be deleted"


def test_org_remove_member():
    status, data = request("DELETE", f"/orgs/{ORG1_ID}/members/{USER2_ID}", token=TOKEN)
    assert_eq(status, 200, f"Remove member failed: {data}")
    # Verify member removed
    status, data = request("GET", f"/orgs/{ORG1_ID}/members", token=TOKEN)
    assert_eq(status, 200)
    assert len([m for m in data if m.get("user_id") == USER2_ID]) == 0


# ══════════════════════════════════════════════════════
#  RUN ALL TESTS
# ══════════════════════════════════════════════════════

ALL_TESTS = [
    # Auth
    ("Register User 1", test_auth_register),
    ("Login", test_auth_login),
    ("Login wrong password", test_auth_login_wrong_password),
    ("Register duplicate user", test_auth_register_duplicate),
    ("Get current user (me)", test_auth_me),
    ("Auth me without token", test_auth_me_no_token),
    ("Update settings", test_auth_settings_update),
    ("Reset settings", test_auth_settings_reset),

    # Org
    ("List organizations", test_org_list),
    ("Get organization", test_org_get),
    ("Get non-existent org", test_org_get_other_org),
    ("Update organization", test_org_update),
    ("List org members", test_org_members_list),

    # User 2
    ("Register User 2", test_auth_register_user2),
    ("Invite User 2 to Org 1", test_org_invite_user2),
    ("Org members after invite", test_org_members_after_invite),
    ("Promote User 2 to admin", test_org_promote_user2),
    ("Invite non-existent user", test_org_invite_nonexistent_user),
    ("Invite duplicate user", test_org_invite_duplicate),

    # Broker
    ("List broker types", test_broker_types),
    ("Create broker connection", test_broker_create),
    ("Create invalid broker type", test_broker_create_invalid_type),
    ("List broker connections", test_broker_list),
    ("Test broker connection", test_broker_test_connection),
    ("Update broker connection", test_broker_update),

    # Portfolio
    ("Create portfolio", test_portfolio_create),
    ("List portfolios", test_portfolio_list),
    ("Get portfolio", test_portfolio_get),
    ("Get non-existent portfolio", test_portfolio_get_not_found),
    ("Update portfolio", test_portfolio_update),
    ("Portfolio summary", test_portfolio_summary),

    # Holdings
    ("Add holding AAPL", test_holding_add),
    ("Add holding MSFT", test_holdings_add_msft),
    ("Add holding VOO", test_holdings_add_voo),
    ("List holdings", test_holdings_list),
    ("Update holding", test_holding_update),
    ("Update non-existent holding", test_holding_update_not_found),

    # Rebalance
    ("Rebalance plan", test_rebalance_plan),
    ("Rebalance execute without confirm", test_rebalance_execute_no_confirm),
    ("Rebalance execute", test_rebalance_execute),

    # Performance & Allocation
    ("Allocation", test_allocation),
    ("Performance", test_performance),
    ("Performance invalid days", test_performance_invalid_days),

    # Token Refresh
    ("Token refresh", test_token_refresh),

    # Cleanup
    ("Batch update holdings", test_batch_update_holdings),
    ("Delete holding", test_holding_delete),
    ("Delete portfolio", test_portfolio_delete),
    ("Delete broker", test_broker_delete),
    ("Remove org member", test_org_remove_member),
]

print(f"\n{'='*60}")
print("  FundBot AI — Comprehensive E2E Test Suite")
print(f"{'='*60}\n")

for name, fn in ALL_TESTS:
    test(name, fn)

print(f"\n{'='*60}")
print(f"  RESULTS: {passed} passed, {failed} failed out of {passed + failed} tests")
print(f"{'='*60}")

if failed > 0:
    sys.exit(1)
else:
    print("\n  🎉 ALL TESTS PASSED!")
    sys.exit(0)
