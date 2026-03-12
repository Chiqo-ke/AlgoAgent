#!/usr/bin/env python3
"""Test Live Data Fetching API Endpoints"""

import requests
import json
from pprint import pprint

BASE_URL = "http://localhost:8000"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzczMjI4Mzk2LCJpYXQiOjE3NzMyMjQ3OTYsImp0aSI6ImMzZGE2MzU3NjE4ZDQxMmJhZGFjOWIwODZhNzI5OWI4IiwidXNlcl9pZCI6IjEiLCJpc3MiOiJhbGdvYWdlbnQtYXBpIn0.wQSKo0bqoJJfuFP5rA80vdv4u2KGEa0v6kDRdnLAZMI"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("\n" + "="*80)
print("LIVE DATA FETCHING API - ENDPOINT TESTS")
print("="*80)

# ============================================================================
# TEST 1: POST /api/live/data/refresh/ - On-Demand Data Fetch
# ============================================================================
print("\n[TEST 1] POST /api/live/data/refresh/ - On-Demand Refresh")
print("-" * 80)

refresh_payload = {
    "symbol": "EURUSD",
    "exchange": "FX",
    "interval": "1h",
    "n_bars": 500
}

print(f"Request: {BASE_URL}/api/live/data/refresh/")
print(f"Payload: {json.dumps(refresh_payload, indent=2)}")
print()

try:
    response = requests.post(
        f"{BASE_URL}/api/live/data/refresh/",
        json=refresh_payload,
        headers=headers,
        timeout=30
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    pprint(response.json(), width=100)
    test1_result = response.json()
except Exception as e:
    print(f"❌ ERROR: {e}")
    test1_result = None

# ============================================================================
# TEST 2: GET /api/live/data/status/ - Check Warehouse Freshness
# ============================================================================
print("\n" + "="*80)
print("[TEST 2] GET /api/live/data/status/ - Check Warehouse Freshness")
print("-" * 80)

status_url = f"{BASE_URL}/api/live/data/status/?symbol=EURUSD&interval=1h"
print(f"Request: {status_url}")
print()

try:
    response = requests.get(status_url, headers=headers, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    pprint(response.json(), width=100)
    test2_result = response.json()
except Exception as e:
    print(f"❌ ERROR: {e}")
    test2_result = None

# ============================================================================
# TEST 3: POST /api/live/scheduler/activate/ - Activate Scheduled Refresh
# ============================================================================
print("\n" + "="*80)
print("[TEST 3] POST /api/live/scheduler/activate/ - Activate Scheduled Refresh")
print("-" * 80)

activate_payload = {
    "symbol": "EURUSD",
    "exchange": "FX",
    "interval": "1h",
    "n_bars": 500
}

print(f"Request: {BASE_URL}/api/live/scheduler/activate/")
print(f"Payload: {json.dumps(activate_payload, indent=2)}")
print()

try:
    response = requests.post(
        f"{BASE_URL}/api/live/scheduler/activate/",
        json=activate_payload,
        headers=headers,
        timeout=30
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    pprint(response.json(), width=100)
    test3_result = response.json()
except Exception as e:
    print(f"❌ ERROR: {e}")
    test3_result = None

# ============================================================================
# TEST 4: GET /api/live/scheduler/jobs/ - List Active Jobs
# ============================================================================
print("\n" + "="*80)
print("[TEST 4] GET /api/live/scheduler/jobs/ - List Active Jobs")
print("-" * 80)

jobs_url = f"{BASE_URL}/api/live/scheduler/jobs/"
print(f"Request: {jobs_url}")
print()

try:
    response = requests.get(jobs_url, headers=headers, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    pprint(response.json(), width=100)
    test4_result = response.json()
except Exception as e:
    print(f"❌ ERROR: {e}")
    test4_result = None

# ============================================================================
# TEST 5: POST /api/live/scheduler/deactivate/ - Deactivate Scheduled Refresh
# ============================================================================
print("\n" + "="*80)
print("[TEST 5] POST /api/live/scheduler/deactivate/ - Deactivate Scheduled Refresh")
print("-" * 80)

deactivate_payload = {
    "symbol": "EURUSD",
    "exchange": "FX",
    "interval": "1h"
}

print(f"Request: {BASE_URL}/api/live/scheduler/deactivate/")
print(f"Payload: {json.dumps(deactivate_payload, indent=2)}")
print()

try:
    response = requests.post(
        f"{BASE_URL}/api/live/scheduler/deactivate/",
        json=deactivate_payload,
        headers=headers,
        timeout=30
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    pprint(response.json(), width=100)
    test5_result = response.json()
except Exception as e:
    print(f"❌ ERROR: {e}")
    test5_result = None

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

tests = [
    ("1. POST /api/live/data/refresh/", test1_result),
    ("2. GET /api/live/data/status/", test2_result),
    ("3. POST /api/live/scheduler/activate/", test3_result),
    ("4. GET /api/live/scheduler/jobs/", test4_result),
    ("5. POST /api/live/scheduler/deactivate/", test5_result),
]

for test_name, result in tests:
    if result and "error" not in str(result).lower():
        print(f"✅ {test_name}")
    else:
        print(f"❌ {test_name}")

print("\n" + "="*80)
print("Tests completed!")
print("="*80)
