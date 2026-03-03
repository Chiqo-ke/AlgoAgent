"""
Fetch MSFT historical data on 1-hour timeframe for the past month.
Date range: ~January 8, 2026 to February 8, 2026
"""
import sys
import os
from datetime import datetime, timedelta

# Add the tvscraper module to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tvscraper.mcp_scraper import MCPTradingViewScraper


def main():
    """Fetch MSFT 1-hour historical data for past month."""
    
    print("=" * 70)
    print("MSFT Historical Data Fetcher - 1 Hour Timeframe")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Calculate date range (past month)
    today = datetime.now()
    one_month_ago = today - timedelta(days=30)
    
    from_date = one_month_ago.strftime('%Y-%m-%d')
    to_date = today.strftime('%Y-%m-%d')
    
    print(f"Target Date Range:")
    print(f"  From: {from_date}")
    print(f"  To:   {to_date}")
    print(f"  Days: 30")
    print()
    
    # Initialize scraper
    print("Initializing TradingView Scraper...")
    scraper = MCPTradingViewScraper()
    print("✓ Scraper initialized")
    print()
    
    try:
        # Initialize browser
        print("[1/6] Initializing Chrome browser...")
        if not scraper.init_browser():
            print("✗ Failed to initialize browser")
            return
        print()
        
        # Navigate to TradingView
        print("[2/6] Navigating to TradingView...")
        if not scraper.navigate_to_tradingview():
            print("✗ Failed to navigate to TradingView")
            return
        print()
        
        # Change symbol to MSFT
        print("[3/6] Changing symbol to MSFT...")
        if scraper.change_symbol("MSFT"):
            print("✓ Symbol changed to MSFT")
        else:
            print("✗ Failed to change symbol")
            return
        print()
        
        # Change timeframe to 1 hour
        print("[4/6] Setting timeframe to 1 hour...")
        if scraper.change_timeframe("1h"):
            print("✓ Timeframe set to 1 hour")
        else:
            print("✗ Failed to set timeframe")
            return
        print()
        
        # Fetch historical data for the past month
        print("[5/6] Fetching historical data...")
        print(f"  Requesting data from {from_date} to {to_date}")
        
        historical_data = scraper.get_historical_data(
            from_date=from_date,
            to_date=to_date
        )
        
        if historical_data and len(historical_data) > 0:
            print(f"✓ Successfully fetched {len(historical_data)} bars")
            print()
            
            # Display data statistics
            print("Data Summary:")
            print("-" * 70)
            
            first_bar = historical_data[0]
            last_bar = historical_data[-1]
            
            print(f"  Total Bars:    {len(historical_data)}")
            print(f"  First Date:    {first_bar['timestamp']}")
            print(f"  Last Date:     {last_bar['timestamp']}")
            print(f"  First Price:   ${first_bar['open']:.2f}")
            print(f"  Last Price:    ${last_bar['close']:.2f}")
            
            # Calculate price change
            price_change = last_bar['close'] - first_bar['open']
            price_change_pct = (price_change / first_bar['open']) * 100
            
            print(f"  Price Change:  ${price_change:.2f} ({price_change_pct:+.2f}%)")
            
            # Calculate high/low
            all_highs = [bar['high'] for bar in historical_data]
            all_lows = [bar['low'] for bar in historical_data]
            highest = max(all_highs)
            lowest = min(all_lows)
            
            print(f"  Highest:       ${highest:.2f}")
            print(f"  Lowest:        ${lowest:.2f}")
            print(f"  Range:         ${highest - lowest:.2f}")
            
            # Calculate average volume
            avg_volume = sum(bar['volume'] for bar in historical_data) / len(historical_data)
            print(f"  Avg Volume:    {avg_volume:,.0f}")
            print()
            
        else:
            print("✗ No historical data available for this range")
            print("   Note: Data availability depends on TradingView subscription")
            return
        
        # Save to CSV
        print("[6/6] Saving data to CSV...")
        
        output_dir = os.path.join(os.path.dirname(__file__), "DataTV")
        os.makedirs(output_dir, exist_ok=True)
        
        # Create filename with date range
        filename = f"MSFT_1h_{from_date}_to_{to_date}.csv"
        filepath = os.path.join(output_dir, filename)
        
        # Save historical data
        import csv
        
        with open(filepath, 'w', newline='') as f:
            if historical_data:
                fieldnames = historical_data[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(historical_data)
        
        file_size = os.path.getsize(filepath) / 1024  # KB
        
        print(f"✓ Data saved successfully")
        print(f"  File: {filename}")
        print(f"  Path: {filepath}")
        print(f"  Size: {file_size:.2f} KB")
        print(f"  Rows: {len(historical_data) + 1} (including header)")
        print()
        
        # Success summary
        print("=" * 70)
        print("SUCCESS")
        print("=" * 70)
        print(f"✓ Fetched {len(historical_data)} hours of MSFT data")
        print(f"✓ Date range: {first_bar['timestamp']} to {last_bar['timestamp']}")
        print(f"✓ Saved to: {filepath}")
        print()
        print("You can now:")
        print("  • Open the CSV in Excel or any spreadsheet software")
        print("  • Use it for backtesting trading strategies")
        print("  • Analyze price movements and patterns")
        print("  • Calculate technical indicators")
        print()
        
    except Exception as e:
        print(f"\n✗ Error occurred: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        print("Cleaning up...")
        try:
            scraper.close_browser()
        except:
            pass
        
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)


if __name__ == "__main__":
    print("\nPython environment:")
    print(f"  • Python executable: {sys.executable}")
    print(f"  • Python version: {sys.version.split()[0]}")
    print()
    
    main()
