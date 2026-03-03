"""
Command-line interface for TradingView Scraper.
"""
import sys
import argparse
from .mcp_scraper import MCPTradingViewScraper


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="TradingView Scraper - Automate TradingView chart interactions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch AAPL data
  tvscraper --symbol AAPL --timeframe 1h --bars 100
  
  # Fetch with date range
  tvscraper --symbol MSFT --from 2026-01-01 --to 2026-02-01
  
  # Add indicators
  tvscraper --symbol TSLA --indicator RSI --indicator EMA
        """
    )
    
    parser.add_argument(
        "--symbol", "-s",
        type=str,
        default="AAPL",
        help="Symbol to fetch (default: AAPL)"
    )
    
    parser.add_argument(
        "--timeframe", "-t",
        type=str,
        default="1h",
        choices=["1m", "3m", "5m", "30m", "1h"],
        help="Timeframe (default: 1h)"
    )
    
    parser.add_argument(
        "--bars", "-b",
        type=int,
        help="Number of bars to fetch"
    )
    
    parser.add_argument(
        "--from",
        dest="from_date",
        type=str,
        help="Start date (YYYY-MM-DD)"
    )
    
    parser.add_argument(
        "--to",
        dest="to_date",
        type=str,
        help="End date (YYYY-MM-DD)"
    )
    
    parser.add_argument(
        "--indicator", "-i",
        action="append",
        help="Add indicator (can be used multiple times)"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output file path (CSV format)"
    )
    
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"%(prog)s {MCPTradingViewScraper.__module__}"
    )
    
    args = parser.parse_args()
    
    # Create scraper
    print(f"🚀 TradingView Scraper CLI")
    print(f"   Symbol: {args.symbol}")
    print(f"   Timeframe: {args.timeframe}")
    print()
    
    scraper = MCPTradingViewScraper()
    
    try:
        # Initialize
        print("Initializing browser...")
        scraper.init_browser()
        scraper.navigate_to_tradingview()
        
        # Change symbol
        print(f"Changing symbol to {args.symbol}...")
        scraper.change_symbol(args.symbol)
        
        # Change timeframe
        print(f"Setting timeframe to {args.timeframe}...")
        scraper.change_timeframe(args.timeframe)
        
        # Add indicators
        if args.indicator:
            for indicator in args.indicator:
                print(f"Adding indicator: {indicator}...")
                scraper.add_indicator(indicator)
        
        # Fetch data
        print("Fetching historical data...")
        if args.bars:
            data = scraper.get_historical_data(bars_count=args.bars)
        elif args.from_date or args.to_date:
            data = scraper.get_historical_data(
                from_date=args.from_date,
                to_date=args.to_date
            )
        else:
            data = scraper.get_historical_data(bars_count=100)
        
        if data:
            print(f"✓ Fetched {len(data)} bars")
            
            # Save if output specified
            if args.output:
                import csv
                with open(args.output, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                print(f"✓ Saved to {args.output}")
            else:
                # Print first few rows
                print("\nFirst 5 bars:")
                for bar in data[:5]:
                    print(f"  {bar['timestamp']}: O={bar['open']:.2f} H={bar['high']:.2f} L={bar['low']:.2f} C={bar['close']:.2f}")
        else:
            print("✗ No data fetched")
            return 1
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return 1
    
    finally:
        scraper.close_browser()
    
    print("\n✓ Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
