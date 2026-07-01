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

    print("=== Test Webull HK UAT (ID:22) ===")
    resp = httpx.post(f"{BASE}/brokers/22/test", headers=headers, timeout=30)
    print(f"  Status: {resp.status_code}")
    try:
        data = resp.json()
        print(f"  Response: {json.dumps(data, indent=2)[:500]}")
        if not data.get("success"):
            # Check backend logs
            import subprocess
            result = subprocess.run(
                ["journalctl", "_PID=1189208", "--no-pager", "-n", "30"],
                capture_output=True, text=True, timeout=5
            )
            webull_lines = [l for l in result.stdout.split('\n') if 'webull' in l.lower() or 'Webull' in l or '401' in l]
            if webull_lines:
                print(f"\n  Backend logs (Webull-related):")
                for l in webull_lines[-5:]:
                    print(f"    {l}")
    except Exception as e:
        print(f"  Error: {e}")

if __name__ == "__main__":
    main()
