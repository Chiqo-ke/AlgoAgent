"""
Test script to fetch MSFT, AAPL, and TSLA data with EMA 20 and 50 indicators
on 5-minute timeframe and save to CSV in DataTV folder.
"""
import sys
import os
import time
from datetime import datetime
from pathlib import Path

# Add the tvscraper module to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tvscraper.mcp_scraper import MCPTradingViewScraper


def main():
    """Fetch stock data with EMA indicators and save to CSV."""
    
    print("=" * 60)
    print("TradingView Stock Data Fetcher")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Configuration
    symbols = ["MSFT", "AAPL", "TSLA"]
    timeframe = "5m"  # 5-minute timeframe
    indicators = [
        {"name": "EMA", "length": 20},
        {"name": "EMA", "length": 50}
    ]
    
    # Create DataTV folder
    output_dir = Path(__file__).parent / "DataTV"
    output_dir.mkdir(exist_ok=True)
    print(f"✓ Output directory: {output_dir}")
    print()
    
    # Initialize scraper
    print("Initializing TradingView Scraper...")
    scraper = MCPTradingViewScraper()
    print("✓ Scraper initialized")
    print()
    
    # Initialize browser
    if not scraper.init_browser():
        print("✗ Failed to initialize browser")
        return
    
    # Navigate to TradingView
    if not scraper.navigate_to_tradingview():
        print("✗ Failed to navigate to TradingView")
        return
    
    print()
    print("NOTE: TradingView should now be open in your browser.")
    print("      The script will now fetch data for MSFT, AAPL, and TSLA...")
    print()
    time.sleep(2)
    
    try:
        # Process each symbol
        for i, symbol in enumerate(symbols, 1):
            print(f"\n[{i}/{len(symbols)}] Processing {symbol}...")
            print("-" * 60)
            
            try:
                # Change symbol
                print(f"  → Changing symbol to {symbol}...")
                scraper.change_symbol(symbol)
                time.sleep(2)
                
                # Change timeframe to 5 minutes
                print(f"  → Setting timeframe to {timeframe} minutes...")
                scraper.change_timeframe(timeframe)
                time.sleep(2)
                
                # Add EMA 20
                print(f"  → Adding EMA 20 indicator...")
                scraper.add_indicator("EMA")
                time.sleep(2)
                
                # Configure EMA 20
                print(f"  → Configuring EMA 20...")
                scraper.configure_indicator("EMA", {"length": 20})
                time.sleep(2)
                
                # Add EMA 50
                print(f"  → Adding EMA 50 indicator...")
                scraper.add_indicator("EMA")
                time.sleep(2)
                
                # Configure EMA 50
                print(f"  → Configuring EMA 50...")
                scraper.configure_indicator("EMA", {"length": 50})
                time.sleep(2)
                
                # Fetch historical data (last 100 bars for 5-minute timeframe)
                print(f"  → Fetching historical data...")
                historical_data = scraper.get_historical_data(bars_count=100)
                
                if historical_data:
                    print(f"  ✓ Retrieved {len(historical_data)} bars")
                    
                    # Get current market data with indicators
                    print(f"  → Fetching current market data with indicators...")
                    market_data = scraper.get_market_data()
                    
                    if market_data:
                        # Save to CSV
                        csv_filename = f"{symbol}_5min_EMA20_EMA50.csv"
                        csv_path = output_dir / csv_filename
                        
                        print(f"  → Saving to CSV: {csv_filename}...")
                        scraper.save_data(
                            data=market_data,
                            filepath=str(csv_path),
                            format='csv'
                        )
                        
                        print(f"  ✓ Saved to: {csv_path}")
                        
                        # Display summary
                        print(f"\n  Summary for {symbol}:")
                        print(f"    • Symbol: {market_data.get('symbol', 'N/A')}")
                        print(f"    • Price: ${market_data.get('price', 'N/A')}")
                        print(f"    • Timeframe: {timeframe} minutes")
                        print(f"    • Indicators: EMA 20, EMA 50")
                        print(f"    • Historical bars: {len(historical_data)}")
                        
                        # Display indicator values if available
                        indicators_data = market_data.get('indicators', {})
                        if indicators_data:
                            print(f"    • Indicator values:")
                            if isinstance(indicators_data, dict):
                                for ind_name, ind_value in indicators_data.items():
                                    if "EMA" in ind_name:
                                        print(f"      - {ind_name}: {ind_value}")
                            elif isinstance(indicators_data, list):
                                for ind in indicators_data:
                                    if isinstance(ind, dict) and "EMA" in str(ind):
                                        print(f"      - {ind}")
                    else:
                        print(f"  ✗ Failed to fetch market data for {symbol}")
                else:
                    print(f"  ✗ Failed to fetch historical data for {symbol}")
                
                # Clean up indicators for next symbol
                if i < len(symbols):
                    print(f"  → Removing indicators for next symbol...")
                    try:
                        scraper.remove_indicator("EMA")
                        time.sleep(1)
                        scraper.remove_indicator("EMA")
                        time.sleep(1)
                    except Exception as e:
                        print(f"  ! Warning: Could not remove indicators: {e}")
                
            except Exception as e:
                print(f"  ✗ Error processing {symbol}: {e}")
                continue
        
        print("\n" + "=" * 60)
        print("COMPLETION SUMMARY")
        print("=" * 60)
        
        # List generated files
        csv_files = list(output_dir.glob("*.csv"))
        print(f"\n✓ Generated {len(csv_files)} CSV file(s):")
        for csv_file in csv_files:
            file_size = csv_file.stat().st_size / 1024  # KB
            print(f"  • {csv_file.name} ({file_size:.2f} KB)")
        
        print(f"\n✓ All files saved to: {output_dir}")
        print(f"✓ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        print("\nCleaning up...")
        try:
            scraper.close_browser()
        except:
            pass
        print("Test completed.")


if __name__ == "__main__":
    print("\nPython environment:")
    print(f"  • Python executable: {sys.executable}")
    print(f"  • Python version: {sys.version.split()[0]}")
    print()
    
    main()
