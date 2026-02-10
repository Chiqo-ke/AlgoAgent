"""
Standalone TVscraper Test - No Django Dependencies
=================================================

Tests TVscraper directly to fetch MSFT 1h data without going through
the full data_loader integration (which has Django dependencies).

Goal: Fetch 1 month of MSFT 1h data and save to Data folder.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json

# Set console encoding to UTF-8 to avoid emoji issues
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Get paths
SCRIPT_DIR = Path(__file__).parent
BACKTEST_DIR = SCRIPT_DIR
DATA_DIR = BACKTEST_DIR.parent / "Data" / "historical"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Add TVscraper to path
TVSCRAPER_PATH = Path(__file__).parent.parent.parent.parent / "TVscraper"
sys.path.insert(0, str(TVSCRAPER_PATH))

print("=" * 80)
print("TVscraper Standalone Test - MSFT 1h Data")
print("=" * 80)
print(f"\nTest Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Test parameters
TICKER = "MSFT"
PERIOD = "1mo"
INTERVAL = "1h"
BARS_COUNT = 720  # ~1 month of hourly data

print(f"\nTest Parameters:")
print(f"  - Ticker: {TICKER}")
print(f"  - Period: {PERIOD}")
print(f"  - Interval: {INTERVAL}")
print(f"  - Bars: {BARS_COUNT}")
print(f"  - Save to: {DATA_DIR}")

# Step 1: Import TVscraper
print("\n[1/4] Importing TVscraper...")
try:
    from tvscraper.mcp_scraper import MCPTradingViewScraper
    print("   [OK] TVscraper imported successfully")
except ImportError as e:
    print(f"   [FAIL] Failed to import TVscraper: {e}")
    sys.exit(1)

# Step 2: Initialize scraper
print("\n[2/4] Initializing scraper...")
try:
    scraper = MCPTradingViewScraper()
    print("   [OK] Scraper initialized")
    
    # Initialize browser
    if not scraper.init_browser():
        raise RuntimeError("Failed to initialize browser")
    print("   [OK] Browser initialized")
    
    # Navigate to TradingView
    if not scraper.navigate_to_tradingview():
        raise RuntimeError("Failed to navigate to TradingView")
    print("   [OK] Navigated to TradingView")
    
except Exception as e:
    print(f"   [FAIL] Initialization failed: {e}")
    sys.exit(1)

# Step 3: Fetch data
print(f"\n[3/4] Fetching {BARS_COUNT} bars of {TICKER} {INTERVAL} data...")
try:
    # Set symbol
    scraper.change_symbol(TICKER)
    print(f"   [OK] Symbol set to {TICKER}")
    
    # Set timeframe (1h)
    scraper.change_timeframe("1h")
    print(f"   [OK] Timeframe set to 1h")
    
    # Fetch historical data
    historical_data = scraper.get_historical_data(bars_count=BARS_COUNT)
    
    if not historical_data:
        raise ValueError(f"No data returned for {TICKER}")
    
    print(f"   [OK] Fetched {len(historical_data)} bars")
    
    # Show sample
    if len(historical_data) > 0:
        first_bar = historical_data[0]
        last_bar = historical_data[-1]
        print(f"\n   Sample Data:")
        print(f"     First bar: {first_bar.get('timestamp', 'N/A')}")
        print(f"       Open:  ${first_bar.get('open', 'N/A')}")
        print(f"       Close: ${first_bar.get('close', 'N/A')}")
        print(f"     Last bar: {last_bar.get('timestamp', 'N/A')}")
        print(f"       Open:  ${last_bar.get('open', 'N/A')}")
        print(f"       Close: ${last_bar.get('close', 'N/A')}")
    
except Exception as e:
    print(f"   [FAIL] Data fetch failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 4: Save data
print(f"\n[4/4] Saving data to {DATA_DIR}...")
try:
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save as JSON
    json_file = DATA_DIR / f"{TICKER}_{INTERVAL}_{PERIOD}_{timestamp}.json"
    with open(json_file, 'w') as f:
        json.dump(historical_data, f, indent=2)
    print(f"   [OK] Saved JSON: {json_file.name}")
    
    # Save as CSV (convert to simple format)
    csv_file = DATA_DIR / f"{TICKER}_{INTERVAL}_{PERIOD}_{timestamp}.csv"
    with open(csv_file, 'w') as f:
        # Header
        f.write("timestamp,Open,High,Low,Close,Volume\n")
        # Data rows
        for bar in historical_data:
            f.write(f"{bar.get('timestamp', '')},{bar.get('open', 0)},{bar.get('high', 0)},{bar.get('low', 0)},{bar.get('close', 0)},{bar.get('volume', 0)}\n")
    print(f"   [OK] Saved CSV: {csv_file.name}")
    
    # Save metadata
    metadata_file = DATA_DIR / f"{TICKER}_{INTERVAL}_{PERIOD}_{timestamp}_metadata.txt"
    with open(metadata_file, 'w') as f:
        f.write(f"TVscraper Fetch Metadata\n")
        f.write(f"========================\n")
        f.write(f"Ticker: {TICKER}\n")
        f.write(f"Interval: {INTERVAL}\n")
        f.write(f"Period: {PERIOD}\n")
        f.write(f"Bars Requested: {BARS_COUNT}\n")
        f.write(f"Bars Received: {len(historical_data)}\n")
        f.write(f"Data Source: TVscraper (TradingView)\n")
        f.write(f"Fetch Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        if len(historical_data) > 0:
            f.write(f"\nFirst Timestamp: {historical_data[0].get('timestamp', 'N/A')}\n")
            f.write(f"Last Timestamp: {historical_data[-1].get('timestamp', 'N/A')}\n")
    print(f"   [OK] Saved metadata: {metadata_file.name}")
    
    print(f"\n" + "=" * 80)
    print("TEST PASSED")
    print("=" * 80)
    print(f"\nFiles saved to: {DATA_DIR}")
    print(f"  - {json_file.name}")
    print(f"  - {csv_file.name}")
    print(f"  - {metadata_file.name}")
    print(f"\nTotal bars: {len(historical_data)}")
    
except Exception as e:
    print(f"   [FAIL] Save failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
