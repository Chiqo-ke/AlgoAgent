"""
Historical Data Fetching Examples

This module demonstrates how to fetch and work with historical OHLCV data
from TradingView charts.

Features:
- Fetch specific number of bars
- Fetch data within date ranges
- Export historical data to CSV/JSON/Excel
- Analyze historical price patterns
- Compare multiple symbols historically
"""

import time
from datetime import datetime, timedelta


def example_1_fetch_last_n_bars():
    """Example: Fetch last N bars of data."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Fetch Last N Bars")
    print("="*70 + "\n")
    
    from tvscraper.mcp_scraper import MCPTradingViewScraper
    
    scraper = MCPTradingViewScraper()
    
    # Set up chart
    scraper.change_symbol("AAPL")
    scraper.change_timeframe("1h")
    
    # Fetch last 100 bars
    print("Fetching last 100 hourly bars for AAPL...\n")
    historical_data = scraper.get_historical_data(bars_count=100)
    
    print(f"\n✅ Fetched {len(historical_data)} bars")
    
    # Show first few bars
    print("\nFirst 3 bars:")
    for i, bar in enumerate(historical_data[:3]):
        print(f"\n  Bar {i+1}:")
        print(f"    Time: {bar['timestamp']}")
        print(f"    Open: ${bar['open']:.2f}")
        print(f"    High: ${bar['high']:.2f}")
        print(f"    Low: ${bar['low']:.2f}")
        print(f"    Close: ${bar['close']:.2f}")
        print(f"    Volume: {bar['volume']:,}")
    
    # Show last bar (most recent)
    print("\nMost recent bar:")
    last_bar = historical_data[-1]
    print(f"    Time: {last_bar['timestamp']}")
    print(f"    Close: ${last_bar['close']:.2f}")
    print(f"    Volume: {last_bar['volume']:,}")


def example_2_fetch_date_range():
    """Example: Fetch data for specific date range."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Fetch Specific Date Range")
    print("="*70 + "\n")
    
    from tvscraper.mcp_scraper import MCPTradingViewScraper
    
    scraper = MCPTradingViewScraper()
    
    # Set up chart
    scraper.change_symbol("BTCUSD")
    scraper.change_timeframe("1h")
    
    # Fetch data for January 2024
    print("Fetching BTCUSD data for January 2024...\n")
    historical_data = scraper.get_historical_data(
        from_date="2024-01-01",
        to_date="2024-01-31"
    )
    
    print(f"\n✅ Fetched {len(historical_data)} bars")
    
    if historical_data:
        print(f"Date range: {historical_data[0]['timestamp']} to {historical_data[-1]['timestamp']}")
        
        # Calculate statistics
        closes = [bar['close'] for bar in historical_data]
        highs = [bar['high'] for bar in historical_data]
        lows = [bar['low'] for bar in historical_data]
        
        print(f"\nJanuary 2024 Statistics:")
        print(f"  High: ${max(highs):,.2f}")
        print(f"  Low: ${min(lows):,.2f}")
        print(f"  Open: ${historical_data[0]['open']:,.2f}")
        print(f"  Close: ${historical_data[-1]['close']:,.2f}")
        print(f"  Change: ${historical_data[-1]['close'] - historical_data[0]['open']:,.2f}")


def example_3_export_historical_data():
    """Example: Export historical data to various formats."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Export Historical Data")
    print("="*70 + "\n")
    
    from tvscraper.mcp_scraper import MCPTradingViewScraper
    import json
    import csv
    
    scraper = MCPTradingViewScraper()
    
    # Fetch data
    scraper.change_symbol("EURUSD")
    scraper.change_timeframe("5m")
    
    print("Fetching last 200 bars of 5-minute EURUSD data...\n")
    historical_data = scraper.get_historical_data(bars_count=200)
    
    # Export to JSON
    json_file = "eurusd_historical.json"
    with open(json_file, 'w') as f:
        json.dump(historical_data, f, indent=2)
    print(f"✅ Exported to JSON: {json_file}")
    
    # Export to CSV
    csv_file = "eurusd_historical.csv"
    with open(csv_file, 'w', newline='') as f:
        if historical_data:
            writer = csv.DictWriter(f, fieldnames=historical_data[0].keys())
            writer.writeheader()
            writer.writerows(historical_data)
    print(f"✅ Exported to CSV: {csv_file}")
    
    # Export to Excel (optional, requires openpyxl)
    try:
        import pandas as pd
        df = pd.DataFrame(historical_data)
        excel_file = "eurusd_historical.xlsx"
        df.to_excel(excel_file, index=False)
        print(f"✅ Exported to Excel: {excel_file}")
    except ImportError:
        print("⚠️  Excel export requires pandas and openpyxl")


def example_4_calculate_indicators():
    """Example: Calculate technical indicators from historical data."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Calculate Indicators from Historical Data")
    print("="*70 + "\n")
    
    from tvscraper.mcp_scraper import MCPTradingViewScraper
    
    scraper = MCPTradingViewScraper()
    
    # Fetch data
    scraper.change_symbol("AAPL")
    scraper.change_timeframe("1h")
    
    print("Fetching AAPL hourly data...\n")
    historical_data = scraper.get_historical_data(bars_count=50)
    
    # Calculate simple moving average (SMA)
    def calculate_sma(data, period=20):
        """Calculate Simple Moving Average."""
        if len(data) < period:
            return []
        
        sma_values = []
        for i in range(period - 1, len(data)):
            window = data[i - period + 1:i + 1]
            avg = sum(bar['close'] for bar in window) / period
            sma_values.append({
                'timestamp': data[i]['timestamp'],
                'sma': avg,
                'close': data[i]['close']
            })
        
        return sma_values
    
    # Calculate SMA(20)
    sma_data = calculate_sma(historical_data, period=20)
    
    print(f"✅ Calculated SMA(20) for {len(sma_data)} points")
    print("\nLast 5 SMA values:")
    for item in sma_data[-5:]:
        print(f"  {item['timestamp'][:19]}: Close=${item['close']:.2f}, SMA(20)=${item['sma']:.2f}")
    
    # Identify crossovers
    print("\nLooking for price/SMA crossovers...")
    crossovers = []
    for i in range(1, len(sma_data)):
        prev = sma_data[i-1]
        curr = sma_data[i]
        
        # Bullish crossover (price crosses above SMA)
        if prev['close'] < prev['sma'] and curr['close'] > curr['sma']:
            crossovers.append({'time': curr['timestamp'], 'type': 'Bullish', 'price': curr['close']})
        
        # Bearish crossover (price crosses below SMA)
        elif prev['close'] > prev['sma'] and curr['close'] < curr['sma']:
            crossovers.append({'time': curr['timestamp'], 'type': 'Bearish', 'price': curr['close']})
    
    print(f"Found {len(crossovers)} crossovers:")
    for cross in crossovers[-3:]:
        print(f"  {cross['type']}: {cross['time'][:19]} at ${cross['price']:.2f}")


def example_5_compare_multiple_symbols():
    """Example: Compare historical performance of multiple symbols."""
    print("\n" + "="*70)
    print("EXAMPLE 5: Compare Multiple Symbols")
    print("="*70 + "\n")
    
    from tvscraper.mcp_scraper import MCPTradingViewScraper
    
    scraper = MCPTradingViewScraper()
    
    symbols = ["AAPL", "GOOGL", "MSFT", "AMZN"]
    results = {}
    
    # Fetch last 30 days for each symbol
    from_date = (datetime.now() - timedelta(days=30)).isoformat()[:10]
    to_date = datetime.now().isoformat()[:10]
    
    print(f"Comparing symbols from {from_date} to {to_date}\n")
    
    for symbol in symbols:
        print(f"Processing {symbol}...")
        scraper.change_symbol(symbol)
        time.sleep(1)
        
        data = scraper.get_historical_data(
            from_date=from_date,
            to_date=to_date
        )
        
        if data:
            start_price = data[0]['close']
            end_price = data[-1]['close']
            change = ((end_price - start_price) / start_price) * 100
            
            results[symbol] = {
                'start': start_price,
                'end': end_price,
                'change_pct': change,
                'bars': len(data)
            }
    
    # Display results
    print("\n" + "="*50)
    print("30-Day Performance Comparison")
    print("="*50)
    
    # Sort by performance
    sorted_results = sorted(results.items(), key=lambda x: x[1]['change_pct'], reverse=True)
    
    for symbol, stats in sorted_results:
        print(f"\n{symbol}:")
        print(f"  Start: ${stats['start']:.2f}")
        print(f"  End: ${stats['end']:.2f}")
        print(f"  Change: {stats['change_pct']:+.2f}%")
        print(f"  Bars: {stats['bars']}")
    
    # Find best and worst
    best = sorted_results[0]
    worst = sorted_results[-1]
    
    print(f"\n🏆 Best performer: {best[0]} ({best[1]['change_pct']:+.2f}%)")
    print(f"📉 Worst performer: {worst[0]} ({worst[1]['change_pct']:+.2f}%)")


def example_6_volatility_analysis():
    """Example: Analyze price volatility from historical data."""
    print("\n" + "="*70)
    print("EXAMPLE 6: Volatility Analysis")
    print("="*70 + "\n")
    
    from tvscraper.mcp_scraper import MCPTradingViewScraper
    import math
    
    scraper = MCPTradingViewScraper()
    
    # Fetch data
    scraper.change_symbol("BTCUSD")
    scraper.change_timeframe("1h")
    
    print("Analyzing Bitcoin volatility...\n")
    historical_data = scraper.get_historical_data(bars_count=100)
    
    # Calculate returns
    returns = []
    for i in range(1, len(historical_data)):
        prev_close = historical_data[i-1]['close']
        curr_close = historical_data[i]['close']
        ret = (curr_close - prev_close) / prev_close
        returns.append(ret)
    
    # Calculate statistics
    mean_return = sum(returns) / len(returns)
    variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
    std_dev = math.sqrt(variance)
    
    # Annualized volatility (for hourly data: sqrt(24*365))
    annualized_volatility = std_dev * math.sqrt(24 * 365) * 100
    
    print("Volatility Statistics (last 100 hours):")
    print(f"  Mean Return: {mean_return * 100:.4f}%")
    print(f"  Std Deviation: {std_dev * 100:.4f}%")
    print(f"  Annualized Volatility: {annualized_volatility:.2f}%")
    
    # Find largest moves
    returns_indexed = [(i, r) for i, r in enumerate(returns)]
    returns_indexed.sort(key=lambda x: abs(x[1]), reverse=True)
    
    print("\nTop 5 largest price moves:")
    for i, (idx, ret) in enumerate(returns_indexed[:5], 1):
        bar = historical_data[idx + 1]
        direction = "📈" if ret > 0 else "📉"
        print(f"  {i}. {direction} {ret * 100:+.2f}% at {bar['timestamp'][:19]}")


def example_7_save_daily_snapshots():
    """Example: Save daily historical snapshots for backtesting."""
    print("\n" + "="*70)
    print("EXAMPLE 7: Daily Snapshot Collection")
    print("="*70 + "\n")
    
    from tvscraper.mcp_scraper import MCPTradingViewScraper
    import json
    from datetime import datetime
    
    scraper = MCPTradingViewScraper()
    
    # Configure
    symbol = "SPY"  # S&P 500 ETF
    scraper.change_symbol(symbol)
    scraper.change_timeframe("1h")
    
    print(f"Collecting daily snapshot for {symbol}...\n")
    
    # Fetch last 24 hours (24 bars on 1h timeframe)
    historical_data = scraper.get_historical_data(bars_count=24)
    
    # Create snapshot structure
    snapshot = {
        "symbol": symbol,
        "timeframe": "1h",
        "snapshot_date": datetime.now().isoformat(),
        "bars_count": len(historical_data),
        "data": historical_data,
        "summary": {
            "first": historical_data[0] if historical_data else None,
            "last": historical_data[-1] if historical_data else None,
            "high": max(bar['high'] for bar in historical_data) if historical_data else 0,
            "low": min(bar['low'] for bar in historical_data) if historical_data else 0
        }
    }
    
    # Save to file
    filename = f"{symbol}_snapshot_{datetime.now().strftime('%Y%m%d')}.json"
    with open(filename, 'w') as f:
        json.dump(snapshot, f, indent=2)
    
    print(f"✅ Snapshot saved: {filename}")
    print(f"\nSnapshot summary:")
    print(f"  Bars: {snapshot['bars_count']}")
    print(f"  24h High: ${snapshot['summary']['high']:.2f}")
    print(f"  24h Low: ${snapshot['summary']['low']:.2f}")
    
    if snapshot['summary']['first'] and snapshot['summary']['last']:
        change = snapshot['summary']['last']['close'] - snapshot['summary']['first']['open']
        change_pct = (change / snapshot['summary']['first']['open']) * 100
        print(f"  24h Change: ${change:.2f} ({change_pct:+.2f}%)")


def example_8_all_available_data():
    """Example: Fetch all available historical data."""
    print("\n" + "="*70)
    print("EXAMPLE 8: Fetch All Available Data")
    print("="*70 + "\n")
    
    from tvscraper.mcp_scraper import MCPTradingViewScraper
    
    scraper = MCPTradingViewScraper()
    
    # Set up
    scraper.change_symbol("TSLA")
    scraper.change_timeframe("1h")
    
    print("Fetching ALL available TSLA hourly data...")
    print("(Limited by TradingView subscription and symbol)\n")
    
    # Fetch without specifying date range or count
    # This will get as much as TradingView allows
    historical_data = scraper.get_historical_data()
    
    print(f"\n✅ Fetched {len(historical_data)} total bars")
    
    if historical_data:
        first_bar = historical_data[0]
        last_bar = historical_data[-1]
        
        print(f"\nData range:")
        print(f"  Oldest: {first_bar['timestamp']}")
        print(f"  Newest: {last_bar['timestamp']}")
        
        # Calculate time span
        from datetime import datetime
        start_dt = datetime.fromisoformat(first_bar['timestamp'].replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(last_bar['timestamp'].replace('Z', '+00:00'))
        days = (end_dt - start_dt).days
        
        print(f"  Span: {days} days")
        
        print(f"\nPrice range:")
        all_highs = [bar['high'] for bar in historical_data]
        all_lows = [bar['low'] for bar in historical_data]
        print(f"  All-time high: ${max(all_highs):.2f}")
        print(f"  All-time low: ${min(all_lows):.2f}")


# Menu system
def show_menu():
    """Display example menu."""
    print("\n" + "="*70)
    print(" "*15 + "HISTORICAL DATA EXAMPLES")
    print("="*70)
    print("\n1. Fetch Last N Bars")
    print("2. Fetch Specific Date Range")
    print("3. Export Historical Data")
    print("4. Calculate Technical Indicators")
    print("5. Compare Multiple Symbols")
    print("6. Volatility Analysis")
    print("7. Save Daily Snapshots")
    print("8. Fetch All Available Data")
    print("0. Exit")
    print("\n" + "="*70)


if __name__ == "__main__":
    import sys
    
    examples = {
        "1": example_1_fetch_last_n_bars,
        "2": example_2_fetch_date_range,
        "3": example_3_export_historical_data,
        "4": example_4_calculate_indicators,
        "5": example_5_compare_multiple_symbols,
        "6": example_6_volatility_analysis,
        "7": example_7_save_daily_snapshots,
        "8": example_8_all_available_data
    }
    
    if len(sys.argv) > 1:
        choice = sys.argv[1]
        if choice in examples:
            examples[choice]()
        else:
            print(f"Unknown example: {choice}")
            print("Valid options: 1-8")
    else:
        # Interactive menu
        while True:
            show_menu()
            choice = input("\nEnter your choice: ").strip()
            
            if choice == "0":
                print("\nGoodbye!")
                break
            elif choice in examples:
                examples[choice]()
            else:
                print("\n❌ Invalid choice. Please try again.")
            
            input("\nPress Enter to continue...")
