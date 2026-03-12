"""
End-to-end test for the live trading session API.
Tests: login -> save broker credential -> start session (dry_run) -> stop session
"""
import requests
import json

BASE = "http://localhost:8000"

# ─── Step 1: Login ───────────────────────────────────────────────────────────
print("=== Step 1: Login ===")
resp = requests.post(f"{BASE}/api/auth/login/", json={"username": "algotrader", "password": "LiveTest@2026"})
print(f"Status: {resp.status_code}")
if resp.status_code != 200:
    print("ERROR:", resp.text)
    exit(1)
token = resp.json()["tokens"]["access"]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
print("Token obtained OK")

# ─── Step 2: Save FBS broker credentials ─────────────────────────────────────
print("\n=== Step 2: Save Broker Credentials ===")
cred_payload = {
    "label": "FBS Demo Account",
    "mt5_login": 102641850,
    "mt5_password": "U-Ea6.cs",
    "mt5_server": "FBS-Demo",
    "is_default": True
}
resp = requests.post(f"{BASE}/api/trading/credentials/", json=cred_payload, headers=headers)
print(f"Status: {resp.status_code}")
if resp.status_code == 201:
    cred = resp.json()
    cred_id = cred["id"]
    print(f"Credential saved: id={cred_id}, label={cred['label']}, server={cred['mt5_server']}, login={cred['mt5_login']}")
else:
    # Any non-201 (duplicate, error, etc.) → fetch existing list
    print(f"Create returned {resp.status_code}, fetching existing credentials...")
    resp2 = requests.get(f"{BASE}/api/trading/credentials/", headers=headers)
    if resp2.status_code != 200:
        print("ERROR fetching credentials:", resp2.text)
        exit(1)
    creds = resp2.json()
    creds_list = creds.get("results", creds) if isinstance(creds, dict) else creds
    if not creds_list:
        print("ERROR: No credentials found. Create failed:", resp.text)
        exit(1)
    cred_id = creds_list[0]["id"]
    print(f"Using existing credential id={cred_id}, label={creds_list[0]['label']}")

# ─── Step 3: List credentials ─────────────────────────────────────────────────
print("\n=== Step 3: List Credentials ===")
resp = requests.get(f"{BASE}/api/trading/credentials/", headers=headers)
print(f"Status: {resp.status_code}")
data = resp.json()
creds_list = data.get("results", data)
for c in creds_list:
    print(f"  id={c['id']} label={c['label']} server={c['mt5_server']} login={c['mt5_login']} default={c['is_default']}")

# ─── Step 4: Start live session using saved credential ───────────────────────
print("\n=== Step 4: Start Live Session (dry_run=True) ===")
session_payload = {
    "strategy_id": 133,  # most recent strategy with code
    "credential_id": cred_id,
    "symbols": ["EURUSD"],
    "timeframe": "1h",
    "dry_run": True,
    "risk_pct": "1.00"
}
resp = requests.post(f"{BASE}/api/trading/sessions/", json=session_payload, headers=headers)
print(f"Status: {resp.status_code}")
print(json.dumps(resp.json(), indent=2))

if resp.status_code == 201:
    session_id = resp.json()["id"]
    session_pid = resp.json().get("pid")
    print(f"\nSession started: id={session_id}, pid={session_pid}, status={resp.json()['status']}")

    # ─── Step 5: Stop live session ────────────────────────────────────────────
    print("\n=== Step 5: Stop Live Session ===")
    import time
    time.sleep(3)  # Let it run a moment
    resp = requests.post(f"{BASE}/api/trading/sessions/{session_id}/stop/", headers=headers)
    print(f"Status: {resp.status_code}")
    print(json.dumps(resp.json(), indent=2))
else:
    print("Session did not start – see error above")
