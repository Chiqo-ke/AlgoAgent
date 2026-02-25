"""
Test Script: Fetch Multiple Symbols with EMA Indicators
=======================================================
Fetches MSFT, AAPL, and TSLA with EMA 20 and 50 on 5-minute timeframe.
Saves data to CSV files in DataTV folder.

PREREQUISITES:
- TradingView must be open in Chrome browser
- MCP Chrome server must be running
"""

import sys
import os
import time
from pathlib import Path

# Add parent directory to path to import tvscraper
sys.path.insert(0, str(Path(__file__).parent))

from tvscraper.mcp_scraper import MCPTradingViewScraper


def main():
    """Main test function."""
    print("=" * 70)
    print("TradingView Multi-Symbol Data Fetcher")
    print("=" * 70)
    print()
    print("⚠️  PREREQUISITES:")
    print("   1. TradingView must be open in Chrome")
    print("   2. MCP Chrome server must be running")
    print()
    
    # Configuration
    symbols = ["MSFT", "AAPL", "TSLA"]
    timeframe = "5"  # 5 minutes
    indicators = [
        {"name": "EMA", "length": 20},
        {"name": "EMA", "length": 50}
    ]
    
    # Create DataTV folder if it doesn't exist
    data_folder = Path(__file__).parent / "DataTV"
    data_folder.mkdir(exist_ok=True)
    print(f"✓ Data folder created: {data_folder}")
    print()
    
    # Initialize scraper
    print("Initializing TradingView scraper...")
    scraper = MCPTradingViewScraper()
    print("✓ Scraper initialized")
    print()
    
    try:
        for i, symbol in enumerate(symbols, 1):
            print(f"[{i}/{len(symbols)}] Processing {symbol}")
            print("-" * 50)
            
            try:
                # Change symbol
                print(f"  → Changing to {symbol}...")
                scraper.change_symbol(symbol)
                time.sleep(3)  # Wait for symbol to load
                print(f"  ✓ Symbol changed to {symbol}")
                
                # Change timeframe
                print(f"  → Setting timeframe to {timeframe} minutes...")
                scraper.change_timeframe(timeframe)
                time.sleep(2)  # Wait for timeframe to change
                print(f"  ✓ Timeframe set to {timeframe}m")
                
                # Remove existing indicators (clean slate)
                print("  → Clearing existing indicators...")
                try:
                    # Try to remove any existing indicators
                    for _ in range(5):  # Max 5 attempts
                        try:
                            scraper.remove_indicator("EMA")
                        except:
                            break
                    time.sleep(1)
                except:
                    pass
                
                # Add EMA 20
                print("  → Adding EMA 20...")
                scraper.add_indicator("EMA")
                time.sleep(2)
                scraper.configure_indicator("EMA", {"length": 20})
                time.sleep(2)
                print("  ✓ EMA 20 added")
                
                # Add EMA 50
                print("  → Adding EMA 50...")
                scraper.add_indicator("EMA")
                time.sleep(2)
                scraper.configure_indicator("EMA", {"length": 50})
                time.sleep(2)
                print("  ✓ EMA 50 added")
                
                # Fetch current market data
                print("  → Fetching market data...")
                data = scraper.get_market_data()
                
                if data:
                    print(f"  ✓ Data fetched successfully")
                    print(f"    - Price: ${data.get('price', 'N/A')}")
                    print(f"    - Volume: {data.get('volume', 'N/A')}")
                    
                    # Check for EMA values
                    indicators_data = data.get('indicators', {})
                    if indicators_data:
                        print(f"    - Indicators found: {len(indicators_data)}")
                        for ind_name, ind_value in indicators_data.items():
                            print(f"      • {ind_name}: {ind_value}")
                    
                    # Save to CSV
                    csv_filename = data_folder / f"{symbol}_5m_ema.csv"
                    print(f"  → Saving to CSV: {csv_filename.name}...")
                    
                    scraper.save_data(data, str(csv_filename), 'csv')
                    print(f"  ✓ Data saved to {csv_filename}")
                else:
                    print("  ✗ Failed to fetch data")
                
                print()
                
            except Exception as e:
                print(f"  ✗ Error processing {symbol}: {e}")
                print()
                continue
        
        # Summary
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        
        # List all created files
        csv_files = list(data_folder.glob("*.csv"))
        if csv_files:
            print(f"✓ Successfully created {len(csv_files)} CSV files:")
            for csv_file in csv_files:
                file_size = csv_file.stat().st_size
                print(f"  • {csv_file.name} ({file_size:,} bytes)")
        else:
            print("✗ No CSV files were created")
        
        print()
        print(f"Data folder location: {data_folder.absolute()}")
        print()
        
    except Exception as e:
        print(f"✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
