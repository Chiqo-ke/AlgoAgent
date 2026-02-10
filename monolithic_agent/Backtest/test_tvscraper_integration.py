"""
Test TVscraper Integration - Historical Data Fetch with Indicators

This script simulates a generated bot fetching historical data through the 
data_loader module, which will use TVscraper as fallback when yfinance fails.

Test Parameters:
- Symbol: MSFT
- Period: 1 month (1mo)
- Interval: 1 hour (1h)
- Indicators: EMA 50, EMA 70
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import os

# Configure Django settings before any imports that might need it
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoagent_api.settings_local')

# Add parent to path
BACKTEST_DIR = Path(__file__).parent
MONOLITHIC_DIR = BACKTEST_DIR.parent
sys.path.insert(0, str(MONOLITHIC_DIR))

print("=" * 80)
print("TVscraper Integration Test - MSFT 1h Data with EMA Indicators")
print("=" * 80)
print(f"\nTest Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Import data loader
print("\n[1/5] Importing data loader...")
try:
    # Import directly from module file to avoid Django initialization
    import importlib.util
    spec = importlib.util.spec_from_file_location("data_loader", BACKTEST_DIR / "data_loader.py")
    data_loader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(data_loader)
    
    load_market_data = data_loader.load_market_data
    TV_SCRAPER_AVAILABLE = data_loader.TV_SCRAPER_AVAILABLE
    DATA_FETCHER_AVAILABLE = data_loader.DATA_FETCHER_AVAILABLE
    
    print("   ✅ Data loader imported successfully")
    print(f"   - yfinance available: {DATA_FETCHER_AVAILABLE}")
    print(f"   - TVscraper available: {TV_SCRAPER_AVAILABLE}")
except Exception as e:
    print(f"   ❌ Failed to import data loader: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test parameters
SYMBOL = "MSFT"
PERIOD = "1mo"
INTERVAL = "1h"
INDICATORS = {
    'EMA': [
        {'timeperiod': 50},
        {'timeperiod': 70}
    ]
}

print(f"\n[2/5] Fetching data for {SYMBOL}...")
print(f"   Period: {PERIOD}")
print(f"   Interval: {INTERVAL}")
print(f"   Indicators: EMA 50, EMA 70")

try:
    # This will use yfinance first, then fall back to TVscraper if it fails
    data_stream = load_market_data(
        ticker=SYMBOL,
        period=PERIOD,
        interval=INTERVAL,
        indicators=INDICATORS,
        stream=False  # Get DataFrame directly for testing
    )
    
    # Check if we got a tuple (df, metadata) or generator
    if isinstance(data_stream, tuple):
        df, metadata = data_stream
        print(f"   ✅ Data fetched successfully!")
        print(f"   - Source: {metadata.get('source', 'unknown')}")
        print(f"   - Rows: {len(df)}")
        print(f"   - Date range: {df.index.min()} to {df.index.max()}")
        print(f"   - Columns: {list(df.columns)}")
    else:
        df = data_stream
        print(f"   ✅ Data fetched successfully!")
        print(f"   - Rows: {len(df)}")
        print(f"   - Date range: {df.index.min()} to {df.index.max()}")
        print(f"   - Columns: {list(df.columns)}")
        
except Exception as e:
    print(f"   ❌ Failed to fetch data: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Validate data
print(f"\n[3/5] Validating data...")
required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
indicator_cols = ['EMA_50', 'EMA_70']

missing_ohlcv = [col for col in required_cols if col not in df.columns]
missing_indicators = [col for col in indicator_cols if col not in df.columns]

if missing_ohlcv:
    print(f"   ⚠️  Missing OHLCV columns: {missing_ohlcv}")
else:
    print(f"   ✅ All OHLCV columns present")

if missing_indicators:
    print(f"   ⚠️  Missing indicator columns: {missing_indicators}")
    print(f"   Available columns: {list(df.columns)}")
else:
    print(f"   ✅ All indicator columns present")

# Check for valid data
if df.isnull().sum().sum() > 0:
    print(f"   ⚠️  Found {df.isnull().sum().sum()} null values")
else:
    print(f"   ✅ No null values in data")

# Display sample data
print(f"\n[4/5] Sample data (first 5 rows):")
print(df.head().to_string())

# Save data to Data folder
print(f"\n[5/5] Saving data to Data folder...")
DATA_DIR = MONOLITHIC_DIR / "Data" / "historical"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Create filename with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"{SYMBOL}_{INTERVAL}_{PERIOD}_{timestamp}.csv"
filepath = DATA_DIR / filename

try:
    # Save to CSV
    df.to_csv(filepath)
    print(f"   ✅ Data saved to: {filepath}")
    print(f"   - File size: {filepath.stat().st_size / 1024:.2f} KB")
    
    # Also save metadata file
    metadata_file = DATA_DIR / f"{SYMBOL}_{INTERVAL}_{PERIOD}_{timestamp}_metadata.txt"
    with open(metadata_file, 'w') as f:
        f.write(f"Symbol: {SYMBOL}\n")
        f.write(f"Period: {PERIOD}\n")
        f.write(f"Interval: {INTERVAL}\n")
        f.write(f"Indicators: EMA 50, EMA 70\n")
        f.write(f"Rows: {len(df)}\n")
        f.write(f"Date Range: {df.index.min()} to {df.index.max()}\n")
        f.write(f"Data Source: {metadata.get('source', 'unknown') if isinstance(data_stream, tuple) else 'data_loader'}\n")
        f.write(f"Fetched: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"\nColumns:\n")
        for col in df.columns:
            f.write(f"  - {col}\n")
    
    print(f"   ✅ Metadata saved to: {metadata_file}")
    
except Exception as e:
    print(f"   ❌ Failed to save data: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Summary
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print(f"✅ Symbol: {SYMBOL}")
print(f"✅ Data Points: {len(df)}")
print(f"✅ Timeframe: {INTERVAL}")
print(f"✅ Period: {PERIOD}")
print(f"✅ Indicators: EMA 50, EMA 70")
print(f"✅ Data saved to: {DATA_DIR}")
print(f"✅ Files created:")
print(f"   - {filename}")
print(f"   - {filename.replace('.csv', '_metadata.txt')}")

# Validation checks
validation_passed = True
if missing_ohlcv:
    print(f"\n⚠️  WARNING: Missing OHLCV columns")
    validation_passed = False
if missing_indicators:
    print(f"\n⚠️  WARNING: Missing indicator columns")
    validation_passed = False
if df.isnull().sum().sum() > 0:
    print(f"\n⚠️  WARNING: Found null values in data")
    validation_passed = False

if validation_passed:
    print(f"\n✅ ALL VALIDATION CHECKS PASSED")
    print(f"\n🎉 TVscraper integration is working correctly!")
else:
    print(f"\n⚠️  Some validation checks failed - review above")

print(f"\nTest Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
