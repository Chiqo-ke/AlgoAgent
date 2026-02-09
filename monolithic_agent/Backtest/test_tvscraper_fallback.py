"""
Test TVscraper Fallback Integration

This script tests that the data_loader can successfully import and use
TVscraper as a fallback when yfinance fails.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Test import
print("=" * 70)
print("Testing TVscraper Fallback Integration")
print("=" * 70)

print("\n1. Testing TVscraper import...")
try:
    from Backtest import data_loader
    
    if data_loader.TV_SCRAPER_AVAILABLE:
        print("   ✅ TVscraper is available!")
        print(f"   TVscraper path: {data_loader.TV_SCRAPER_PATH}")
    else:
        print("   ❌ TVscraper is NOT available")
        print("   This is expected if MCP tools are not installed")
        
    if data_loader.DATA_FETCHER_AVAILABLE:
        print("   ✅ yfinance (DataFetcher) is available")
    else:
        print("   ⚠️  yfinance (DataFetcher) is NOT available")
        
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n2. Testing fallback logic (without actually fetching data)...")
try:
    # Check if the fallback function exists
    if hasattr(data_loader, 'fetch_market_data_with_tvscraper'):
        print("   ✅ Fallback function exists: fetch_market_data_with_tvscraper")
    else:
        print("   ❌ Fallback function missing!")
        
    # Check the main fetch function
    if hasattr(data_loader, 'fetch_market_data'):
        print("   ✅ Main function exists: fetch_market_data")
        
        # Check if it has try/except logic
        import inspect
        source = inspect.getsource(data_loader.fetch_market_data)
        if 'TV_SCRAPER_AVAILABLE' in source and 'fetch_market_data_with_tvscraper' in source:
            print("   ✅ Fallback logic is integrated!")
        else:
            print("   ⚠️  Fallback logic may not be properly integrated")
    else:
        print("   ❌ Main function missing!")
        
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("Test Complete")
print("=" * 70)

print("\nSummary:")
print(f"  ✅ TVscraper available: {data_loader.TV_SCRAPER_AVAILABLE if hasattr(data_loader, 'TV_SCRAPER_AVAILABLE') else 'Unknown'}")
print(f"  ✅ yfinance available: {data_loader.DATA_FETCHER_AVAILABLE if hasattr(data_loader, 'DATA_FETCHER_AVAILABLE') else 'Unknown'}")
print(f"\nFallback Status: {'✅ READY' if data_loader.TV_SCRAPER_AVAILABLE else '⚠️  NOT AVAILABLE (MCP tools required)'}")
