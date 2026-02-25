"""
Basic usage example for TradingView Scraper
"""

from tvscraper import TradingViewScraper, IndicatorManager
import time


def main():
    print("=" * 60)
    print("TradingView Scraper - Basic Usage Example")
    print("=" * 60)
    
    # Initialize scraper
    print("\n1. Initializing scraper...")
    scraper = TradingViewScraper()
    
    # List available indicators  
    print("\n2. Available indicators:")
    indicators = IndicatorManager.list_indicators()
    print(f"   {', '.join(indicators)}")
    
    # Change symbol
    print("\n3. Changing symbol to AAPL...")
    if scraper.set_symbol("AAPL"):
        scraper.wait_for_data_load()
    
    # Change timeframe
    print("\n4. Setting timeframe to 1 hour...")
    if scraper.set_timeframe("1h"):
        time.sleep(1)
    
    # Add first indicator
    print("\n5. Adding EMA(9) indicator...")
    if scraper.add_indicator("EMA", {"length": 9}):
        time.sleep(1)
    
    # Add second indicator
    print("\n6. Adding RSI(14) indicator...")
    if scraper.add_indicator("RSI", {"length": 14}):
        time.sleep(1)
    
    # Get current price
    print("\n7. Getting current price...")
    current_price = scraper.get_current_price()
    if current_price:
        print(f"   Current Price Data:")
        print(f"   - Open:   {current_price.get('open')}")
        print(f"   - High:   {current_price.get('high')}")
        print(f"   - Low:    {current_price.get('low')}")
        print(f"   - Close:  {current_price.get('close')}")
    
    # Get market data
    print("\n8. Extracting market data...")
    market_data = scraper.get_market_data(bars=100)
    if market_data:
        print(f"   Symbol: {market_data.get('symbol')}")
        print(f"   Timeframe: {market_data.get('timeframe')}")
        print(f"   Active Indicators: {len(market_data.get('indicators', []))}")
    
    # Remove an indicator
    print("\n9. Removing RSI indicator...")
    if scraper.remove_indicator("RSI"):
        time.sleep(1)
    
    # Reset scraper
    print("\n10. Resetting scraper...")
    scraper.reset()
    
    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
