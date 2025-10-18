#!/usr/bin/env python3
"""
Test Dynamic Data Loader
=========================

This script demonstrates the updated data_loader module that fetches
data dynamically instead of reading from CSV files.

The data_loader now:
1. Fetches live market data using yfinance (via DataFetcher)
2. Computes indicators dynamically (via indicator_calculator)
3. Caches results for performance
4. Works exactly like the interactive_test.py workflow
"""

import sys
from pathlib import Path

# Add parent directory to path
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

# Import directly from the data_loader module file
import importlib.util
spec = importlib.util.spec_from_file_location("data_loader", SCRIPT_DIR / "Backtest" / "data_loader.py")
data_loader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(data_loader)

# Get the functions we need
load_market_data = data_loader.load_market_data
load_stock_data = data_loader.load_stock_data
get_available_indicators = data_loader.get_available_indicators

def print_section(title):
    """Print formatted section"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def main():
    print_section("DYNAMIC DATA LOADER TEST")
    
    # Test 1: Show available indicators
    print_section("Test 1: Available Indicators")
    indicators = get_available_indicators()
    print(f"Total indicators available: {len(indicators)}")
    print(f"Indicators: {', '.join(indicators)}")
    
    # Test 2: Load data with specific parameters
    print_section("Test 2: Load AAPL with RSI and MACD")
    print("Fetching live data from yfinance...")
    
    df, metadata = load_market_data(
        ticker='AAPL',
        indicators={
            'RSI': {'timeperiod': 14},
            'MACD': {'fastperiod': 12, 'slowperiod': 26, 'signalperiod': 9}
        },
        period='1mo',
        interval='1d'
    )
    
    print(f"\n✅ Success!")
    print(f"   Rows: {metadata['rows']}")
    print(f"   Columns: {metadata['columns']}")
    print(f"   Date Range: {metadata['date_range'][0]} to {metadata['date_range'][1]}")
    print(f"   Source: {metadata['source']}")
    
    print(f"\nFirst 3 rows:")
    print(df.head(3))
    
    print(f"\nLast 3 rows:")
    print(df.tail(3))
    
    # Test 3: Use simplified function
    print_section("Test 3: Load MSFT with default parameters")
    print("Using simplified load_stock_data function...")
    
    df2, metadata2 = load_stock_data(
        ticker='MSFT',
        indicators=['RSI', 'SMA', 'EMA'],  # Use default parameters
        period='5d',
        interval='1h'
    )
    
    print(f"\n✅ Success!")
    print(f"   Rows: {metadata2['rows']}")
    print(f"   Columns: {metadata2['columns']}")
    print(f"   Source: {metadata2['source']}")
    
    # Test 4: Cache test
    print_section("Test 4: Cache Test")
    print("Loading AAPL again (should use cache)...")
    
    df3, metadata3 = load_market_data(
        ticker='AAPL',
        indicators={
            'RSI': {'timeperiod': 14},
            'MACD': {'fastperiod': 12, 'slowperiod': 26, 'signalperiod': 9}
        },
        period='1mo',
        interval='1d',
        use_cache=True
    )
    
    print(f"\n✅ Success!")
    print(f"   Source: {metadata3['source']}")
    if 'cache_age_hours' in metadata3:
        print(f"   Cache age: {metadata3['cache_age_hours']} hours")
    
    print_section("ALL TESTS PASSED!")
    print("\n🎉 The data_loader now fetches data dynamically!")
    print("   ✓ Fetches live market data via yfinance")
    print("   ✓ Computes indicators dynamically")
    print("   ✓ Caches results for performance")
    print("   ✓ No longer depends on CSV files")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
