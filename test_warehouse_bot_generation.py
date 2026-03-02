"""
End-to-end test: simulate a frontend user creating a bot via the API,
then inspect the generated script for warehouse-backed data loading.
"""
import requests
import json
import sys
import os
from pathlib import Path

BASE = "http://localhost:8000/api"
CREDS = {"username": "algotrader", "password": "Trading@2024"}

CANONICAL = {
    "strategy_name": "RSI_EMA_Momentum",
    "description": (
        "Momentum strategy using RSI and EMA crossover. "
        "Buy when RSI is below 35 and the 12-period EMA crosses above the 26-period EMA. "
        "Sell when RSI is above 65 or the fast EMA crosses back below the slow EMA."
    ),
    "timeframe": "1h",
    "entry_rules": [
        {
            "description": "RSI(14) crosses below 35 (oversold)",
            "indicator": "RSI",
            "condition": "below",
            "value": 35
        },
        {
            "description": "EMA(12) crosses above EMA(26)",
            "indicator": "EMA_crossover",
            "fast_period": 12,
            "slow_period": 26
        }
    ],
    "exit_rules": [
        {
            "description": "RSI(14) rises above 65 (overbought)",
            "indicator": "RSI",
            "condition": "above",
            "value": 65
        },
        {
            "description": "EMA(12) crosses back below EMA(26)",
            "indicator": "EMA_crossunder",
            "fast_period": 12,
            "slow_period": 26
        }
    ],
    "risk_management": {
        "stop_loss": "1.5% below entry price",
        "take_profit": "3% above entry price",
        "position_sizing": "2% of account equity per trade"
    },
    "indicators": [
        {"name": "RSI", "parameters": {"timeperiod": 14}},
        {"name": "EMA", "parameters": {"periods": [12, 26]}}
    ]
}

GENERATION_PAYLOAD = {
    "canonical_json": CANONICAL,
    "strategy_name": "RSI_EMA_Momentum",
    "ai_provider": "copilot",
    "auto_execute": False,
    "auto_fix": False,
}


def sep(label=""):
    print("\n" + "=" * 60)
    if label:
        print(f"  {label}")
        print("=" * 60)


# ── 1. Login ──────────────────────────────────────────────────
sep("STEP 1: LOGIN")
r = requests.post(f"{BASE}/auth/login/", json=CREDS, timeout=15)
print(f"Status: {r.status_code}")

if r.status_code != 200:
    print("FAIL – login rejected:", r.text[:400])
    sys.exit(1)

login_data = r.json()
token = login_data.get("tokens", {}).get("access") or login_data.get("access")
if not token:
    print("FAIL – no access token in response:", list(login_data.keys()))
    sys.exit(1)

user = login_data.get("user", {})
print(f"OK – logged in as '{user.get('username')}' (id={user.get('id')})")
print(f"Token prefix: {token[:32]}…")

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}",
}

# ── 2. Generate bot script ────────────────────────────────────
sep("STEP 2: GENERATE BOT (generate_strategy_unified)")
print("Payload sent:")
print(json.dumps({k: v for k, v in GENERATION_PAYLOAD.items() if k != "canonical_json"}, indent=2))
print("canonical_json keys:", list(CANONICAL.keys()))

r2 = requests.post(
    f"{BASE}/strategies/api/generate_strategy_unified/",
    headers=HEADERS,
    json=GENERATION_PAYLOAD,
    timeout=120,
)
print(f"\nStatus: {r2.status_code}")

if r2.status_code not in (200, 201):
    print("FAIL – generation rejected:")
    print(r2.text[:800])
    sys.exit(1)

gen = r2.json()
print("Response keys:", list(gen.keys()))
print(f"success      : {gen.get('success')}")
print(f"ai_provider  : {gen.get('ai_provider')}")
print(f"file_name    : {gen.get('file_name')}")
print(f"file_path    : {gen.get('file_path')}")
strategy_id = gen.get("strategy_id")
print(f"strategy_id  : {strategy_id}")

# Error check
if not gen.get("success"):
    print("\nGeneration reported failure:")
    print(gen.get("error", ""))
    print(gen.get("details", ""))
    sys.exit(1)

# ── 3. Read generated file ────────────────────────────────────
sep("STEP 3: INSPECT GENERATED SCRIPT")
file_path = gen.get("file_path")
if not file_path:
    # Fallback: find most-recently modified .py in codes/
    codes_dir = Path(__file__).parent / "monolithic_agent" / "Backtest" / "codes"
    py_files = sorted(codes_dir.glob("*.py"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not py_files:
        print("FAIL – no generated file found and file_path was empty")
        sys.exit(1)
    file_path = str(py_files[0])
    print(f"(file_path missing from response; using newest file: {py_files[0].name})")

gen_file = Path(file_path)
if not gen_file.exists():
    print(f"FAIL – file not found: {file_path}")
    sys.exit(1)

code = gen_file.read_text(encoding="utf-8", errors="replace")
print(f"File: {gen_file.name}  ({len(code)} chars, {code.count(chr(10))} lines)")

# ── 4. Data-loading analysis ──────────────────────────────────
sep("STEP 4: DATA LOADING ANALYSIS")

checks = {
    "imports load_market_data"           : "load_market_data" in code,
    "uses from Backtest.data_loader"     : "Backtest.data_loader" in code or "from Backtest" in code,
    "NO DataFetcher import"              : "DataFetcher" not in code,
    "NO yfinance import"                 : "yfinance" not in code,
    "NO TVscraper import"                : "TVscraper" not in code and "tvscraper" not in code.lower(),
    "NO requests.get/fetch import"       : "requests.get" not in code,
    "uses stream=True OR load_market_data": "stream=True" in code or "load_market_data(" in code,
    "has on_bar method"                  : "def on_bar" in code,
    "has broker.submit_signal"           : "submit_signal" in code,
    "has position tracking"              : "in_position" in code or "position_size" in code,
}

all_ok = True
for description, result in checks.items():
    icon = "[OK]" if result else "[FAIL]"
    if not result:
        all_ok = False
    print(f"  {icon}  {description}")

sep("STEP 5: CODE PREVIEW (first 80 lines)")
lines = code.splitlines()
for i, line in enumerate(lines[:80], 1):
    print(f"{i:3}: {line}")

sep("SUMMARY")
if all_ok:
    print("ALL CHECKS PASSED – generated bot uses warehouse data loading correctly.")
else:
    print("SOME CHECKS FAILED – review items marked [FAIL] above.")

print(f"\nGenerated file: {gen_file}")
print("Done.")
