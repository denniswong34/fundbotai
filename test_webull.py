#!/usr/bin/env python3
"""Test Webull HK adapter via the FundBotAI API."""
import httpx
import json

BASE = "http://localhost:8004/api"

def login():
    resp = httpx.post(f"{BASE}/auth/login", json={"username": "demo", "password": "Demo@2024!"})
    resp.raise_for_status()
    return resp.json()["access_token"]

def main():
    token = login()
    headers = {"Authorization": f"Bearer {token}"}

    print("=== Brokers ===")
    resp = httpx.get(f"{BASE}/brokers", headers=headers)
    for b in resp.json():
        print(f"  ID:{b['id']} {b['broker_type']} '{b['name']}' connected={b.get('is_connected')}")

    print("\n=== Test Webull HK UAT (ID:22) ===")
    resp = httpx.post(f"{BASE}/brokers/22/test", headers=headers, timeout=30)
    print(f"  Status: {resp.status_code}")
    print(f"  Response: {json.dumps(resp.json(), indent=2)[:500]}")

    print("\n=== Test Webull HK Live (ID:21) ===")
    resp = httpx.post(f"{BASE}/brokers/21/test", headers=headers, timeout=30)
    print(f"  Status: {resp.status_code}")
    print(f"  Response: {json.dumps(resp.json(), indent=2)[:500]}")

    print("\n=== Account Summary (Webull HK UAT) ===")
    resp = httpx.get(f"{BASE}/brokers/22/account", headers=headers, timeout=30)
    print(f"  Status: {resp.status_code}")
    print(f"  Response: {json.dumps(resp.json(), indent=2)[:500]}")

    print("\n=== Positions (Webull HK UAT) ===")
    resp = httpx.get(f"{BASE}/brokers/22/positions", headers=headers, timeout=30)
    print(f"  Status: {resp.status_code}")
    print(f"  Response: {json.dumps(resp.json(), indent=2)[:500]}")

if __name__ == "__main__":
    main()
