"""
yfinance Diagnosis Script
========================

Tests yfinance to identify rate limiting or other failures.
"""

import sys
from pathlib import Path
import time
import pandas as pd

# Add parent to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

print("=" * 80)
print("yfinance Diagnosis Test")
print("=" * 80)

# Test 1: Import and version
print("\n[1/6] Testing yfinance import...")
try:
    import yfinance as yf
    print(f"   [OK] yfinance version: {yf.__version__}")
except Exception as e:
    print(f"   [FAIL] Import error: {e}")
    sys.exit(1)

# Test 2: Simple ticker fetch (using Ticker API)
print("\n[2/6] Testing Ticker API for AAPL (5 days)...")
try:
    start_time = time.time()
    ticker = yf.Ticker("AAPL")
    data = ticker.history(period="5d")
    elapsed = time.time() - start_time
    
    if data.empty:
        print(f"   [FAIL] No data returned (empty DataFrame)")
    else:
        print(f"   [OK] Received {len(data)} rows in {elapsed:.2f}s")
        print(f"   Columns: {list(data.columns)}")
        print(f"   Date range: {data.index[0]} to {data.index[-1]}")
        print(f"   Sample row:\n{data.head(1)}")
except Exception as e:
    print(f"   [FAIL] Error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Download API (what DataFetcher uses)
print("\n[3/6] Testing download() API for AAPL (5 days)...")
try:
    start_time = time.time()
    data = yf.download("AAPL", period="5d", interval="1d", progress=False)
    elapsed = time.time() - start_time
    
    if data.empty:
        print(f"   [FAIL] No data returned (empty DataFrame)")
        print(f"   Data type: {type(data)}")
        print(f"   Data shape: {data.shape}")
    else:
        print(f"   [OK] Received {len(data)} rows in {elapsed:.2f}s")
        print(f"   Columns: {list(data.columns)}")
        print(f"   Data type: {type(data)}")
        print(f"   Has MultiIndex: {isinstance(data.columns, pd.MultiIndex)}")
except Exception as e:
    print(f"   [FAIL] Error: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Multiple rapid requests (rate limit test)
print("\n[4/6] Testing rate limiting (5 rapid requests)...")
symbols = ["AAPL", "MSFT", "TSLA", "GOOGL", "AMZN"]
success_count = 0
fail_count = 0

for i, symbol in enumerate(symbols, 1):
    try:
        start_time = time.time()
        data = yf.download(symbol, period="5d", interval="1d", progress=False)
        elapsed = time.time() - start_time
        
        if not data.empty:
            print(f"   [{i}/5] {symbol}: OK ({len(data)} rows, {elapsed:.2f}s)")
            success_count += 1
        else:
            print(f"   [{i}/5] {symbol}: EMPTY")
            fail_count += 1
    except Exception as e:
        print(f"   [{i}/5] {symbol}: ERROR - {e}")
        fail_count += 1
    
    # Small delay to avoid hammering
    time.sleep(0.5)

print(f"\n   Results: {success_count} success, {fail_count} failures")

# Test 5: DataFetcher class (actual implementation)
print("\n[5/6] Testing DataFetcher class...")
try:
    from Data.data_fetcher import DataFetcher
    
    fetcher = DataFetcher()
    start_time = time.time()
    data = fetcher.fetch_historical_data("AAPL", period="1mo", interval="1d")
    elapsed = time.time() - start_time
    
    if data.empty:
        print(f"   [FAIL] DataFetcher returned empty DataFrame")
    else:
        print(f"   [OK] DataFetcher returned {len(data)} rows in {elapsed:.2f}s")
        print(f"   Columns: {list(data.columns)}")
except Exception as e:
    print(f"   [FAIL] DataFetcher error: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Check for proxy/network issues
print("\n[6/6] Checking network connectivity to Yahoo Finance...")
try:
    import requests
    
    # Test basic connectivity to Yahoo Finance
    urls = [
        "https://query1.finance.yahoo.com",
        "https://query2.finance.yahoo.com",
    ]
    
    for url in urls:
        try:
            response = requests.get(url, timeout=5)
            print(f"   {url}: HTTP {response.status_code}")
        except Exception as e:
            print(f"   {url}: ERROR - {e}")
            
except ImportError:
    print("   [SKIP] requests module not available")

print("\n" + "=" * 80)
print("Diagnosis Complete")
print("=" * 80)
