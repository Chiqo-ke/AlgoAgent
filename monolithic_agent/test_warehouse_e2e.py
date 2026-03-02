"""
End-to-end test: Simulates a frontend user creating a bot script.
Verifies the generated code loads data from the local warehouse (not yfinance/TVscraper).
"""
import sys
import json
import urllib.request
import urllib.error
import urllib.parse
import os
import re

# --- tee output to log file so we can read progress even while script runs ---
import io

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "e2e_result.txt")

class _Tee:
    def __init__(self, *streams):
        self._streams = streams
    def write(self, data):
        for s in self._streams:
            s.write(data)
            s.flush()
    def flush(self):
        for s in self._streams:
            s.flush()

_log_fh = open(LOG_FILE, "w", encoding="utf-8", buffering=1)
sys.stdout = _Tee(sys.__stdout__, _log_fh)
sys.stderr = _Tee(sys.__stderr__, _log_fh)
# --------------------------------------------------------------------------

BASE_URL = "http://localhost:8000/api"
USERNAME  = "algotrader"
PASSWORD  = "Trading@2024"

PASS = "[PASS]"
FAIL = "[FAIL]"
INFO = "[INFO]"


def post(url, payload, token=None):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"raw": body}


# ─── Step 1: Login ─────────────────────────────────────────────────────────────
print(f"\n{INFO} Step 1 — Login as '{USERNAME}'")
code, resp = post(f"{BASE_URL}/auth/login/", {"username": USERNAME, "password": PASSWORD})
print(f"  HTTP {code}")

if code not in (200, 201):
    print(f"{FAIL} Login failed: {json.dumps(resp, indent=2)[:500]}")
    sys.exit(1)

# Support multiple token response shapes
token = (
    resp.get("access")
    or resp.get("access_token")
    or (resp.get("tokens") or {}).get("access")
)

if not token:
    print(f"{FAIL} Could not find access token in response: {json.dumps(resp, indent=2)[:500]}")
    sys.exit(1)
print(f"{PASS} Logged in. Token: {token[:30]}…")


# ─── Step 2: Generate bot script ───────────────────────────────────────────────
print(f"\n{INFO} Step 2 — Generate EMA Crossover strategy (EURUSD 1h)")

canonical_json = {
    "strategy_name": "EMA Crossover EURUSD",
    "description": "EMA crossover strategy for EURUSD on 1-hour timeframe. Buy when fast EMA crosses above slow EMA, sell when fast EMA crosses below slow EMA.",
    "timeframe": "1h",
    "entry_rules": [
        {"description": "Enter long when 9-period EMA crosses above 21-period EMA"},
        {"description": "Enter short when 9-period EMA crosses below 21-period EMA"}
    ],
    "exit_rules": [
        {"description": "Exit long when 9-period EMA crosses below 21-period EMA"},
        {"description": "Exit short when 9-period EMA crosses above 21-period EMA"}
    ],
    "risk_management": {
        "stop_loss": "1.5% below entry",
        "take_profit": "3% above entry",
        "position_sizing": "1% of portfolio per trade"
    },
    "indicators": [
        {"name": "EMA", "type": "EMA", "period": 9},
        {"name": "EMA", "type": "EMA", "period": 21}
    ]
}

payload = {
    "canonical_json":   canonical_json,
    "strategy_name":    "EMA Crossover EURUSD",
    "ai_provider":      "copilot",
    "auto_execute":     False,
    "auto_fix":         False,
}

code, resp = post(
    f"{BASE_URL}/strategies/api/generate_strategy_unified/",
    payload,
    token=token
)
print(f"  HTTP {code}")

if code not in (200, 201):
    # Server may return generated_code in the 400 body (code-guard rejection)
    inline_code = resp.get("generated_code")
    if inline_code:
        print(f"  NOTE: Server rejected the code ({resp.get('validation_error', resp.get('error'))})")
        print(f"  Auditing the returned generated_code for warehouse compliance …")
        generated_code = inline_code
        file_path = None
    else:
        print(f"[FAIL] Generation failed (no code returned):")
        print(json.dumps(resp, indent=2)[:1000])
        sys.exit(1)
else:
    if not resp.get("success"):
        print(f"[FAIL] Generation failed:")
        print(json.dumps(resp, indent=2)[:1000])
        sys.exit(1)

    print(f"{PASS} Strategy generated.")
    print(f"  ai_provider : {resp.get('ai_provider')}")
    print(f"  file_name   : {resp.get('file_name')}")
    file_path = resp.get("file_path")
    print(f"  file_path   : {file_path}")
    generated_code = None   # will read from disk below


# ─── Step 3: Read generated file ───────────────────────────────────────────────
print(f"\n{INFO} Step 3 — Inspect generated file / returned code")

if generated_code is None:
    if file_path and os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as fh:
            generated_code = fh.read()
        print(f"  Read {len(generated_code)} chars from disk: {file_path}")
    else:
        alt = os.path.join(
            os.path.dirname(__file__), "Backtest", "codes", resp.get("file_name", "")
        )
        if os.path.exists(alt):
            with open(alt, "r", encoding="utf-8") as fh:
                generated_code = fh.read()
            print(f"  Read {len(generated_code)} chars from alt path: {alt}")
        else:
            # Fall back to strategy_code in response body
            generated_code = resp.get("strategy_code", "")
            if generated_code:
                print(f"  Using strategy_code from response body ({len(generated_code)} chars)")
            else:
                print(f"[FAIL] No generated code found anywhere")
                sys.exit(1)

# Print first 60 lines for visual inspection
lines = generated_code.splitlines()
print(f"\n{'─'*60}")
print("  First 60 lines of generated code:")
print(f"{'─'*60}")
for i, line in enumerate(lines[:60], 1):
    print(f"  {i:3d} | {line}")
print(f"{'─'*60}\n")


# ─── Step 4: Audit checks ──────────────────────────────────────────────────────
print(f"{INFO} Step 4 — Warehouse compliance audit")
checks = []

# GOOD patterns (must be present)
good = [
    ("load_market_data imported from Backtest.data_loader",
     r"from\s+Backtest\.data_loader\s+import.*load_market_data"),
    ("load_market_data called",
     r"\bload_market_data\s*\("),
    ("Path setup (3-level parent)",
     r"parent\.parent\.parent|monolithic_agent"),
    ("SimBroker import",
     r"from\s+Backtest\.sim_broker\s+import"),
]

# BAD patterns (must NOT be present)
bad = [
    ("DataFetcher",        r"\bDataFetcher\b"),
    ("yfinance",           r"\byfinance\b"),
    ("TVscraper",          r"\bTVscraper\b"),
    ("import yf",          r"\bimport\s+yf\b"),
    ("requests.get",       r"\brequests\.get\s*\("),
    ("raw data_loader import (no package)",
     r"^from data_loader import|^import data_loader\b"),
]

all_pass = True

print("\n  ✔ REQUIRED patterns:")
for label, pattern in good:
    found = bool(re.search(pattern, generated_code, re.MULTILINE))
    status = PASS if found else FAIL
    print(f"    {status} {label}")
    checks.append(found)

print("\n  ✘ FORBIDDEN patterns (must be absent):")
for label, pattern in bad:
    found = bool(re.search(pattern, generated_code, re.MULTILINE))
    status = FAIL if found else PASS
    print(f"    {status} {label} {'← FOUND!' if found else ''}")
    checks.append(not found)   # pass = NOT found

all_pass = all(checks)

# ─── Summary ───────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
if all_pass:
    print(f"  {PASS} ALL CHECKS PASSED — bot script loads from warehouse correctly")
else:
    passed = sum(checks)
    print(f"  {FAIL} {passed}/{len(checks)} checks passed — review output above")
print(f"{'='*60}\n")

sys.exit(0 if all_pass else 1)
