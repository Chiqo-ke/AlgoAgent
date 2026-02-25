# 🚀 TVScraper Quick Start Guide

> **A Python package for scraping real-time and historical market data from TradingView**

## 📦 Installation

### From PyPI (Recommended)
```bash
pip install tvscraper
```

### From Source
```bash
git clone https://github.com/yourusername/tvscraper.git
cd tvscraper
pip install -e .
```

### Verify Installation
```bash
python -c "from tvscraper import Scraper; print('TVScraper installed successfully!')"
```

---

## ⚡ 5-Minute Quick Start

### 1. Basic Stock Data Fetching

```python
from tvscraper import Scraper

# Initialize the scraper
scraper = Scraper()

# Start browser and navigate to TradingView
scraper.init_browser()
scraper.navigate_to_tradingview()

# Fetch current market data for AAPL
scraper.change_symbol("AAPL")
data = scraper.get_market_data()

print(f"Apple Stock Price: ${data['ohlc']['close']:.2f}")
print(f"Volume: {data['volume']:,}")

# Cleanup
scraper.close_browser()
```

### 2. Fetch Historical Data

```python
from tvscraper import Scraper
from datetime import datetime, timedelta

scraper = Scraper()
scraper.init_browser()
scraper.navigate_to_tradingview()

# Fetch last 100 bars of 1-hour data
scraper.change_symbol("MSFT")
scraper.change_timeframe("1h")
historical = scraper.get_historical_data(bars_count=100)

print(f"Fetched {len(historical)} bars of data")
print(historical.head())

# Save to CSV
historical.to_csv("MSFT_1h_data.csv", index=False)

scraper.close_browser()
```

### 3. Add Technical Indicators

```python
from tvscraper import Scraper

scraper = Scraper()
scraper.init_browser()
scraper.navigate_to_tradingview()

scraper.change_symbol("TSLA")
scraper.change_timeframe("5min")

# Add EMA indicators
scraper.add_indicator("EMA", {"length": 20})
scraper.add_indicator("EMA", {"length": 50})

# Fetch data with indicators
data = scraper.get_historical_data(bars_count=200)
print(data[['timestamp', 'close', 'EMA_20', 'EMA_50']].tail())

scraper.close_browser()
```

---

## 🎯 Common Use Cases

### Multi-Symbol Data Collection

```python
from tvscraper import Scraper
import pandas as pd

scraper = Scraper()
scraper.init_browser()
scraper.navigate_to_tradingview()

symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
all_data = {}

for symbol in symbols:
    scraper.change_symbol(symbol)
    data = scraper.get_historical_data(bars_count=50)
    all_data[symbol] = data
    print(f"✓ Fetched {symbol}: {len(data)} bars")

scraper.close_browser()

# Combine all data
combined = pd.concat(all_data, names=['Symbol', 'Index'])
combined.to_csv("multi_symbol_data.csv")
```

### Date Range Historical Data

```python
from tvscraper import Scraper
from datetime import datetime, timedelta

scraper = Scraper()
scraper.init_browser()
scraper.navigate_to_tradingview()

# Fetch data for last 30 days
scraper.change_symbol("BTC/USD")
scraper.change_timeframe("1h")

end_date = datetime.now()
start_date = end_date - timedelta(days=30)

data = scraper.get_historical_data(
    from_date=start_date.strftime("%Y-%m-%d"),
    to_date=end_date.strftime("%Y-%m-%d")
)

print(f"Bitcoin Data: {start_date.date()} to {end_date.date()}")
print(f"Total Bars: {len(data)}")
print(f"Price Change: ${data['close'].iloc[-1] - data['close'].iloc[0]:.2f}")

scraper.close_browser()
```

### Real-Time Monitoring

```python
from tvscraper import Scraper
import time

scraper = Scraper()
scraper.init_browser()
scraper.navigate_to_tradingview()

scraper.change_symbol("SPY")  # S&P 500 ETF
scraper.change_timeframe("1min")

print("Monitoring SPY... (Press Ctrl+C to stop)")

try:
    while True:
        data = scraper.get_market_data()
        print(f"Time: {data['timestamp']} | Price: ${data['ohlc']['close']:.2f} | Vol: {data['volume']:,}")
        time.sleep(10)  # Update every 10 seconds
except KeyboardInterrupt:
    print("\nStopped monitoring")
    scraper.close_browser()
```

### Cryptocurrency Data

```python
from tvscraper import Scraper

scraper = Scraper()
scraper.init_browser()
scraper.navigate_to_tradingview()

# Fetch crypto data
crypto_symbols = ["BTC/USD", "ETH/USD", "BNB/USD", "SOL/USD"]

for symbol in crypto_symbols:
    scraper.change_symbol(symbol)
    data = scraper.get_market_data()
    print(f"{symbol.ljust(10)}: ${data['ohlc']['close']:,.2f}")

scraper.close_browser()
```

---

## 🖥️ Command Line Interface (CLI)

### Basic Usage

```bash
# Fetch 100 bars of AAPL data on 1h timeframe
tvscraper --symbol AAPL --timeframe 1h --bars 100

# With output file
tvscraper --symbol TSLA --timeframe 5min --bars 200 --output tesla_data.csv

# Date range
tvscraper --symbol MSFT --from 2026-01-01 --to 2026-02-08 --output msft_jan.csv

# With indicators
tvscraper --symbol GOOGL --bars 100 --indicator "EMA:20" --indicator "RSI:14"
```

### CLI Options

```
Options:
  --symbol SYMBOL          Stock symbol (e.g., AAPL, BTC/USD)
  --timeframe TIMEFRAME    Timeframe (1min, 5min, 15min, 1h, 4h, 1D, 1W)
  --bars BARS              Number of bars to fetch (default: 100)
  --from FROM_DATE         Start date (YYYY-MM-DD)
  --to TO_DATE             End date (YYYY-MM-DD)
  --indicator INDICATOR    Add indicator (format: "NAME:param1,param2")
  --output OUTPUT          Output CSV file path
  -h, --help               Show help message
```

---

## 📚 API Reference

### Core Methods

#### `init_browser()`
Initialize Chrome browser via MCP.

```python
scraper.init_browser()
```

#### `navigate_to_tradingview(url=None)`
Navigate to TradingView chart.

```python
scraper.navigate_to_tradingview()  # Default URL
scraper.navigate_to_tradingview("https://www.tradingview.com/chart/xyz")
```

#### `change_symbol(symbol)`
Change the chart symbol.

```python
scraper.change_symbol("AAPL")           # Stock
scraper.change_symbol("BTC/USD")        # Crypto
scraper.change_symbol("EURUSD")         # Forex
scraper.change_symbol("GC1!")           # Futures
```

#### `change_timeframe(timeframe)`
Change the chart timeframe.

```python
scraper.change_timeframe("1min")   # 1 minute
scraper.change_timeframe("5min")   # 5 minutes
scraper.change_timeframe("1h")     # 1 hour
scraper.change_timeframe("1D")     # 1 day
scraper.change_timeframe("1W")     # 1 week
```

#### `add_indicator(name, params=None)`
Add technical indicator to chart.

```python
scraper.add_indicator("EMA", {"length": 20})
scraper.add_indicator("RSI", {"length": 14})
scraper.add_indicator("MACD", {"fast": 12, "slow": 26, "signal": 9})
scraper.add_indicator("BB", {"length": 20, "stdDev": 2})  # Bollinger Bands
```

#### `get_market_data()`
Get current market data.

```python
data = scraper.get_market_data()
# Returns: {
#   'timestamp': '2026-02-08 10:30:00',
#   'ohlc': {'open': 150.0, 'high': 152.0, 'low': 149.5, 'close': 151.5},
#   'volume': 1234567
# }
```

#### `get_historical_data(bars_count=100, from_date=None, to_date=None)`
Fetch historical data.

```python
# Last 100 bars
data = scraper.get_historical_data(bars_count=100)

# Date range
data = scraper.get_historical_data(
    from_date="2026-01-01",
    to_date="2026-02-08"
)

# Returns pandas DataFrame
```

#### `close_browser()`
Close browser and cleanup.

```python
scraper.close_browser()
```

---

## 🔧 Configuration

### Custom Initialization

```python
from tvscraper import Scraper

# Initialize with custom settings
scraper = Scraper()
scraper.init_browser()

# Configure browser before navigation
scraper.navigate_to_tradingview("https://www.tradingview.com/chart/custom")
```

### Data Export Options

```python
# Export to CSV
data.to_csv("output.csv", index=False)

# Export to JSON
data.to_json("output.json", orient="records", date_format="iso")

# Export to Excel
data.to_excel("output.xlsx", index=False, sheet_name="Market Data")

# Export to Parquet (efficient for large datasets)
data.to_parquet("output.parquet", index=False)
```

---

## 💡 Best Practices

### 1. Always Use Context Managers (Recommended Pattern)

```python
from tvscraper import Scraper

def fetch_stock_data(symbol, timeframe="1h", bars=100):
    """Fetch stock data with proper cleanup"""
    scraper = Scraper()
    try:
        scraper.init_browser()
        scraper.navigate_to_tradingview()
        scraper.change_symbol(symbol)
        scraper.change_timeframe(timeframe)
        return scraper.get_historical_data(bars_count=bars)
    finally:
        scraper.close_browser()  # Always cleanup

# Usage
data = fetch_stock_data("AAPL", "1h", 200)
```

### 2. Handle Errors Gracefully

```python
from tvscraper import Scraper
import logging

logging.basicConfig(level=logging.INFO)

scraper = Scraper()

try:
    scraper.init_browser()
    scraper.navigate_to_tradingview()
    scraper.change_symbol("AAPL")
    data = scraper.get_historical_data(bars_count=100)
    
except Exception as e:
    logging.error(f"Error fetching data: {e}")
    
finally:
    scraper.close_browser()
```

### 3. Rate Limiting for Multiple Requests

```python
from tvscraper import Scraper
import time

scraper = Scraper()
scraper.init_browser()
scraper.navigate_to_tradingview()

symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]

for symbol in symbols:
    try:
        scraper.change_symbol(symbol)
        data = scraper.get_historical_data(bars_count=100)
        print(f"✓ {symbol}: {len(data)} bars")
        time.sleep(2)  # 2-second delay between requests
    except Exception as e:
        print(f"✗ {symbol}: Failed - {e}")

scraper.close_browser()
```

### 4. Reuse Scraper Instance

```python
# ❌ DON'T: Create new instance for each symbol
for symbol in symbols:
    scraper = Scraper()  # Inefficient
    scraper.init_browser()
    # ... fetch data
    scraper.close_browser()

# ✅ DO: Reuse single instance
scraper = Scraper()
scraper.init_browser()
scraper.navigate_to_tradingview()

for symbol in symbols:
    scraper.change_symbol(symbol)
    # ... fetch data

scraper.close_browser()
```

---

## 🐛 Troubleshooting

### "Module not found" Error

```bash
# Make sure package is installed
pip install tvscraper

# Verify installation
python -c "import tvscraper; print(tvscraper.__version__)"
```

### Browser Initialization Fails

```python
# Check if MCP Chrome is available
scraper = Scraper()
try:
    scraper.init_browser()
    print("Browser initialized successfully")
except Exception as e:
    print(f"Browser init failed: {e}")
```

### Data Not Fetching

```python
# Add delays between operations
scraper.change_symbol("AAPL")
time.sleep(1)  # Wait for chart to load

scraper.change_timeframe("1h")
time.sleep(1)  # Wait for timeframe change

data = scraper.get_historical_data(bars_count=100)
```

### Empty DataFrame Returned

```python
# Verify symbol is valid
scraper.change_symbol("AAPL")  # ✓ Valid
scraper.change_symbol("INVALID123")  # ✗ May return empty data

# Check timeframe
scraper.change_timeframe("1h")  # ✓ Valid
scraper.change_timeframe("invalid")  # ✗ May cause issues
```

---

## 📖 Additional Resources

- **[AGENTS.md](AGENTS.md)** - Integrate with AI agents and web frameworks
- **[INSTALL.md](INSTALL.md)** - Detailed installation instructions
- **[README.md](README.md)** - Full project documentation
- **[GitHub Repository](https://github.com/yourusername/tvscraper)** - Source code and examples

---

## 🆘 Getting Help

- **Issues**: [GitHub Issues](https://github.com/yourusername/tvscraper/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/tvscraper/discussions)
- **Email**: support@yourproject.com

---

## 📝 Quick Reference Cheat Sheet

```python
# Installation
pip install tvscraper

# Basic workflow
from tvscraper import Scraper
scraper = Scraper()
scraper.init_browser()
scraper.navigate_to_tradingview()

# Fetch data
scraper.change_symbol("AAPL")
scraper.change_timeframe("1h")
data = scraper.get_historical_data(bars_count=100)

# Add indicators
scraper.add_indicator("EMA", {"length": 20})
scraper.add_indicator("RSI", {"length": 14})

# Cleanup
scraper.close_browser()

# CLI
tvscraper --symbol AAPL --bars 100 --output data.csv
```

---

## 🎓 Next Steps

1. **Try Examples**: Start with the 5-minute quick start
2. **Explore CLI**: Use command-line interface for quick tasks
3. **Read AGENTS.md**: Learn about advanced integrations
4. **Build Projects**: Create your own trading/analysis tools

---

**Happy Trading! 📈**

*Version 1.0.0 | Last Updated: February 8, 2026*
