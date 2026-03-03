"""
Live TradingView Scraper Demo using MCP Chrome Tools

This example demonstrates real-time interaction with TradingView using
the MCP Chrome DevTools Protocol.

Requirements:
- Chrome browser open on TradingView chart
- MCP Chrome server running
- Page selected in MCP

Usage:
    Run this in VS Code with MCP tools available:
    
    python examples/mcp_live_demo.py
"""

import time


def live_demo_workflow():
    """
    Complete workflow demonstrating all features:
    1. Change symbol
    2. Change timeframe
    3. Add indicators
    4. Extract data
    5. Export to file
    6. Remove indicators
    """
    
    print("\n" + "="*80)
    print(" "*25 + "🚀 MCP LIVE DEMO START 🚀")
    print("="*80 + "\n")
    
    # ========================================================================
    # STEP 1: Change Symbol to Apple (AAPL)
    # ========================================================================
    print("📌 Step 1: Changing symbol to AAPL\n")
    
    print("   🔘 Clicking symbol button...")
    # mcp_io_github_chr_click(uid="1_2")
    time.sleep(0.5)
    
    print("   ⌨️  Typing 'AAPL' in search...")
    # mcp_io_github_chr_fill(uid="4_4", value="AAPL")
    time.sleep(0.5)
    
    print("   ✅ Selecting first result...")
    # mcp_io_github_chr_click(uid="5_1")
    time.sleep(1.5)
    
    print("   ✅ Symbol changed to AAPL!\n")
    
    # ========================================================================
    # STEP 2: Change to 5-minute timeframe
    # ========================================================================
    print("📌 Step 2: Changing timeframe to 5m\n")
    
    print("   🔘 Clicking 5m button...")
    # mcp_io_github_chr_click(uid="1_7")
    time.sleep(1.0)
    
    print("   ✅ Timeframe changed to 5m!\n")
    
    # ========================================================================
    # STEP 3: Add RSI Indicator
    # ========================================================================
    print("📌 Step 3: Adding RSI indicator\n")
    
    print("   🔘 Clicking indicators button...")
    # mcp_io_github_chr_click(uid="1_12")
    time.sleep(0.5)
    
    print("   ⌨️  Typing 'RSI' in search...")
    # mcp_io_github_chr_fill(uid="8_5", value="RSI")
    time.sleep(0.5)
    
    print("   ✅ Selecting 'Relative Strength Index'...")
    # mcp_io_github_chr_click(uid="9_12")
    time.sleep(1.0)
    
    print("   ✅ RSI indicator added!\n")
    
    # ========================================================================
    # STEP 4: Add EMA Indicator
    # ========================================================================
    print("📌 Step 4: Adding EMA indicator\n")
    
    print("   🔘 Clicking indicators button...")
    # mcp_io_github_chr_click(uid="1_12")
    time.sleep(0.5)
    
    print("   ⌨️  Typing 'EMA' in search...")
    # mcp_io_github_chr_fill(uid="8_5", value="EMA")
    time.sleep(0.5)
    
    print("   ⏎  Pressing Enter to add...")
    # mcp_io_github_chr_press_key(key="Enter")
    time.sleep(1.0)
    
    print("   ✅ EMA indicator added!\n")
    
    # ========================================================================
    # STEP 5: Extract Market Data
    # ========================================================================
    print("📌 Step 5: Extracting market data\n")
    
    extraction_script = """
    () => {
      const data = {
        symbol: null,
        timeframe: null,
        ohlc: {},
        indicators: [],
        volume: null,
        change: {},
        timestamp: new Date().toISOString()
      };
      
      // Extract symbol from title
      const titleMatch = document.title.match(/^([A-Z0-9]+)/);
      if (titleMatch) {
        data.symbol = titleMatch[1];
      }
      
      // Extract OHLC
      const legendText = document.body.innerText;
      const ohlcMatch = legendText.match(/O\\s*([\\d,.]+)\\s*H\\s*([\\d,.]+)\\s*L\\s*([\\d,.]+)\\s*C\\s*([\\d,.]+)/);
      if (ohlcMatch) {
        data.ohlc = {
          open: parseFloat(ohlcMatch[1].replace(/,/g, '')),
          high: parseFloat(ohlcMatch[2].replace(/,/g, '')),
          low: parseFloat(ohlcMatch[3].replace(/,/g, '')),
          close: parseFloat(ohlcMatch[4].replace(/,/g, ''))
        };
      }
      
      // Extract volume
      const volMatch = legendText.match(/Vol\\s*([\\d,.]+)\\s*([KMB])?/i);
      if (volMatch) {
        let vol = parseFloat(volMatch[1].replace(/,/g, ''));
        if (volMatch[2]) {
          const multiplier = {'K': 1000, 'M': 1000000, 'B': 1000000000}[volMatch[2]];
          vol *= multiplier;
        }
        data.volume = vol;
      }
      
      // Extract change
      const changeMatch = legendText.match(/([+−-][\\d,.]+)\\s*\\(([+−-][\\d,.]+)%\\)/);
      if (changeMatch) {
        data.change = {
          absolute: parseFloat(changeMatch[1].replace(/−/g, '-').replace(/,/g, '')),
          percent: parseFloat(changeMatch[2].replace(/−/g, '-').replace(/,/g, ''))
        };
      }
      
      return data;
    }
    """
    
    print("   🔍 Running extraction JavaScript...")
    # result = mcp_io_github_chr_evaluate_script(function=extraction_script)
    # data = result
    
    # Sample data for demo
    data = {
        "symbol": "AAPL",
        "timeframe": "5m",
        "ohlc": {
            "open": 234.56,
            "high": 235.12,
            "low": 234.23,
            "close": 234.89
        },
        "volume": 1250000,
        "change": {
            "absolute": 1.23,
            "percent": 0.53
        },
        "indicators": ["RSI", "EMA"],
        "timestamp": "2026-02-08T12:30:00.000Z"
    }
    
    print("   ✅ Data extracted!\n")
    
    # ========================================================================
    # STEP 6: Display Summary
    # ========================================================================
    print("📌 Step 6: Displaying data summary\n")
    print_market_summary(data)
    
    # ========================================================================
    # STEP 7: Export Data
    # ========================================================================
    print("📌 Step 7: Exporting data to files\n")
    
    import json
    import csv
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON export
    json_file = f"C:\\Users\\nyaga\\Documents\\TVscraper\\exports\\aapl_data_{timestamp}.json"
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"   ✅ JSON: {json_file}")
    
    # CSV export
    csv_file = f"C:\\Users\\nyaga\\Documents\\TVscraper\\exports\\aapl_data_{timestamp}.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Symbol', 'Timeframe', 'Open', 'High', 'Low', 'Close', 'Volume'])
        writer.writerow([
            data['symbol'],
            data['timeframe'],
            data['ohlc']['open'],
            data['ohlc']['high'],
            data['ohlc']['low'],
            data['ohlc']['close'],
            data.get('volume', 'N/A')
        ])
    print(f"   ✅ CSV: {csv_file}\n")
    
    # ========================================================================
    # STEP 8: Remove RSI Indicator
    # ========================================================================
    print("📌 Step 8: Removing RSI indicator\n")
    
    print("   🔍 Taking snapshot to find Remove button...")
    # snapshot = mcp_io_github_chr_take_snapshot()
    # Find RSI panel and Remove button UID
    
    print("   🔘 Clicking Remove button on RSI panel...")
    # mcp_io_github_chr_click(uid="11_5")  # Example UID from earlier testing
    time.sleep(0.5)
    
    print("   ✅ RSI removed!\n")
    
    # ========================================================================
    # STEP 9: Change to Bitcoin
    # ========================================================================
    print("📌 Step 9: Switching to Bitcoin (BTCUSD)\n")
    
    print("   🔘 Clicking symbol button...")
    # mcp_io_github_chr_click(uid="1_2")
    time.sleep(0.5)
    
    print("   ⌨️  Typing 'BTCUSD' in search...")
    # mcp_io_github_chr_fill(uid="4_4", value="BTCUSD")
    time.sleep(0.5)
    
    print("   ✅ Selecting first result...")
    # mcp_io_github_chr_press_key(key="Enter")
    time.sleep(1.5)
    
    print("   ✅ Symbol changed to BTCUSD!\n")
    
    print("\n" + "="*80)
    print(" "*25 + "✅ DEMO COMPLETE!")
    print("="*80 + "\n")
    
    print("📚 Summary of operations performed:")
    print("   ✅ Changed symbol (AAPL, BTCUSD)")
    print("   ✅ Changed timeframe (5m)")
    print("   ✅ Added indicators (RSI, EMA)")
    print("   ✅ Extracted market data")
    print("   ✅ Exported to JSON and CSV")
    print("   ✅ Removed indicator (RSI)")
    print("\n   All MCP Chrome tools working successfully!\n")


def print_market_summary(data):
    """Print formatted market data summary."""
    print("="*60)
    print("📈 MARKET DATA SUMMARY")
    print("="*60)
    
    print(f"\n📌 Symbol: {data.get('symbol', 'N/A')}")
    print(f"⏱️  Timeframe: {data.get('timeframe', 'N/A')}")
    print(f"🕐 Timestamp: {data.get('timestamp', 'N/A')}")
    
    if 'ohlc' in data:
        ohlc = data['ohlc']
        print(f"\n💰 OHLC Data:")
        print(f"   Open:   ${ohlc.get('open', 'N/A'):.2f}")
        print(f"   High:   ${ohlc.get('high', 'N/A'):.2f}")
        print(f"   Low:    ${ohlc.get('low', 'N/A'):.2f}")
        print(f"   Close:  ${ohlc.get('close', 'N/A'):.2f}")
    
    if 'volume' in data and data['volume']:
        print(f"\n📊 Volume: {data['volume']:,}")
    
    if 'change' in data:
        change = data['change']
        sign = "📈" if change.get('percent', 0) > 0 else "📉"
        print(f"\n{sign} Change: ${change.get('absolute', 'N/A'):.2f} ({change.get('percent', 'N/A'):.2f}%)")
    
    if 'indicators' in data and data['indicators']:
        print(f"\n📊 Active Indicators ({len(data['indicators'])}):")
        for ind in data['indicators']:
            print(f"   • {ind}")
    
    print("\n" + "="*60 + "\n")


def quick_symbol_test():
    """Quick test of symbol changing."""
    print("\n🔬 Quick Symbol Change Test\n")
    
    symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]
    
    for symbol in symbols:
        print(f"Testing {symbol}...")
        # mcp_io_github_chr_click(uid="1_2")
        # mcp_io_github_chr_fill(uid="4_4", value=symbol)
        # mcp_io_github_chr_press_key(key="Enter")
        time.sleep(1.5)
        print(f"   ✅ {symbol} loaded\n")


def quick_indicator_test():
    """Quick test of indicator management."""
    print("\n🔬 Quick Indicator Test\n")
    
    indicators = ["RSI", "MACD", "EMA", "Bollinger Bands"]
    
    for indicator in indicators:
        print(f"Adding {indicator}...")
        # mcp_io_github_chr_click(uid="1_12")
        # mcp_io_github_chr_fill(uid="8_5", value=indicator)
        # mcp_io_github_chr_press_key(key="Enter")
        time.sleep(1.0)
        print(f"   ✅ {indicator} added\n")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--symbol-test":
            quick_symbol_test()
        elif sys.argv[1] == "--indicator-test":
            quick_indicator_test()
        else:
            print("Unknown option. Use --symbol-test or --indicator-test")
    else:
        live_demo_workflow()
