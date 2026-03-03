# TradingView Scraper

A powerful Python tool to automate TradingView chart interactions using Chrome DevTools Protocol (MCP).

## ✨ Features

### Core Functionality
- ✅ **Symbol Changing** - Switch between stocks, forex, crypto, indices
- ✅ **Timeframe Control** - Change chart intervals (1m, 3m, 5m, 30m, 1h, etc.)
- ✅ **Indicator Management** - Add/remove technical indicators (RSI, MACD, EMA, etc.)
- ✅ **Parameter Customization** - Configure indicator parameters (length, source, multipliers)
- ✅ **Dynamic Indicator Removal** - Smart detection and removal of indicators
- ✅ **Historical Data Fetching** - Get OHLCV data for any date range or bar count ⭐ NEW
- ✅ **Data Extraction** - Extract OHLC, volume, price changes, indicator values
- ✅ **Multi-Format Export** - Save data as JSON, CSV, or Excel

### Advanced Features
- 🔄 **Multi-Symbol Analysis** - Automated scanning across multiple securities
- 📊 **Browser Automation** - Direct Chrome DevTools Protocol integration
- 🎯 **Real-Time Data** - Extract live market data from TradingView
- � **Time-Series Analysis** - Fetch and analyze historical candle data ⭐ NEW
- 🔍 **Backtesting Support** - Export historical data for strategy testing ⭐ NEW
- �💾 **Flexible Export** - Append mode, custom filenames, auto-timestamping

## 🚀 Quick Start

### Requirements

- Python 3.8+
- Chrome browser
- MCP Chrome DevTools server (for browser automation)
- TradingView account (free or paid)

### Installation

```bash
# Clone or navigate to project directory
cd TVscraper

# Activate virtual environment (recommended)
# Windows:
& C:\Users\nyaga\Documents\.venv\Scripts\Activate.ps1
# Or create new venv:
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Browser Setup with MCP

The scraper uses MCP (Model Context Protocol) Chrome DevTools for browser automation:

```python
from tvscraper.mcp_scraper import MCPTradingViewScraper

# Initialize scraper
scraper = MCPTradingViewScraper()

# Initialize Chrome browser
scraper.init_browser()

# Navigate to TradingView
scraper.navigate_to_tradingview()

# Now you can interact with the chart
scraper.change_symbol("AAPL")
```

**Test Browser Initialization:**
```bash
# Run browser initialization test
python test_browser_init.py
```

### Basic Usage

```python
from tvscraper.mcp_scraper import MCPTradingViewScraper

# Initialize scraper
scraper = MCPTradingViewScraper()

# Initialize browser and navigate to TradingView
scraper.init_browser()
scraper.navigate_to_tradingview()

# Change symbol to Apple
scraper.change_symbol("AAPL")

# Change to 5-minute chart
scraper.change_timeframe("5m")

# Add RSI indicator with custom parameters ⭐ NEW
scraper.add_indicator("RSI", parameters={"length": 21, "source": "hl2"})

# Add EMA with custom length
scraper.add_indicator("EMA", parameters={"length": 50})

# Extract market data
data = scraper.get_market_data()

# Print summary
scraper.print_summary(data)

# Save data
scraper.save_data(data, format='json')

# Remove an indicator
scraper.remove_indicator("RSI")

# Fetch historical data ⭐ NEW
historical_data = scraper.get_historical_data(bars_count=100)
print(f"Fetched {len(historical_data)} bars")

# Or fetch specific date range ⭐ NEW
historical_data = scraper.get_historical_data(
    from_date="2024-01-01",
    to_date="2024-01-31"
)
```

## 📚 Documentation

### Quick References
- **[MCP Integration Guide](docs/MCP_INTEGRATION_GUIDE.md)** - Complete workflows and troubleshooting
- **[Quick Reference](docs/QUICK_REFERENCE.md)** - Essential MCP tool calls and snippets
- **[Agent Integration Guide](AGENTS.md)** - AI agents & codebase integration patterns ⭐ NEW

### Examples
- **[mcp_live_demo.py](examples/mcp_live_demo.py)** - Complete workflow demonstration
- **[indicator_management.py](examples/indicator_management.py)** - Indicator customization examples
- **[historical_data.py](examples/historical_data.py)** - Historical data fetching & analysis ⭐ NEW
- **[export_data.py](examples/export_data.py)** - Data export examples

## 💡 Use Cases

### 1. Multi-Symbol Analysis
```python
symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]
results = []

for symbol in symbols:
    scraper.change_symbol(symbol)
    data = scraper.get_market_data()
    results.append(data)
    print(f"{symbol}: ${data['ohlc']['close']:.2f}")
```

### 2. Historical Backtesting ⭐ NEW
```python
# Fetch historical data for backtesting
scraper.change_symbol("BTCUSD")
scraper.change_timeframe("1h")

# Get last 1000 hourly bars
historical_data = scraper.get_historical_data(bars_count=1000)

# Calculate moving average crossovers
for i in range(20, len(historical_data)):
    sma_20 = sum(bar['close'] for bar in historical_data[i-20:i]) / 20
    price = historical_data[i]['close']
    
    if price > sma_20:
        print(f"Buy signal at {historical_data[i]['timestamp']}: ${price:.2f}")
```

### 3. Technical Indicator Comparison
```python
# Add multiple indicators
scraper.add_indicator("RSI")
scraper.add_indicator("MACD")
scraper.add_indicator("EMA", {"length": 20})

# Extract all data
data = scraper.get_market_data()

# Export to Excel with all indicators
scraper.save_data(data, format='xlsx')
```

### 4. Time-Series Data Collection
```python
import time

# Set up chart
scraper.change_symbol("BTCUSD")
scraper.change_timeframe("5m")
scraper.add_indicator("RSI")

# Collect data every 5 minutes
while True:
    data = scraper.get_market_data()
    scraper.save_data(data, filepath='btc_5m.csv', format='csv', append=True)
    print(f"Logged: {data['timestamp']}")
    time.sleep(300)  # Wait 5 minutes
```

## 🎯 MCP Tool Integration

This project uses MCP (Model Context Protocol) Chrome tools for browser automation:

### Core MCP Tools Used
- `mcp_io_github_chr_click` - Click UI elements
- `mcp_io_github_chr_fill` - Fill input fields
- `mcp_io_github_chr_press_key` - Keyboard input
- `mcp_io_github_chr_evaluate_script` - Execute JavaScript
- `mcp_io_github_chr_take_snapshot` - Capture UI state

### Element UIDs
| Element | UID | Purpose |
|---------|-----|---------|
| Symbol Button | `1_2` | Open symbol search |
| Symbol Search | `4_4` | Type symbol name |
| Indicators Button | `1_12` | Open indicators dialog |
| Indicator Search | `8_5` | Type indicator name |
| Timeframe 5m | `1_7` | Change to 5-minute chart |
| Timeframe 1h | `1_9` | Change to 1-hour chart |

**See [QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md) for complete UID list**

## 📁 Project Structure

```
TVscraper/
├── tvscraper/
│   ├── __init__.py
│   ├── scraper.py          # Original scraper class
│   ├── mcp_scraper.py      # MCP-integrated scraper ✨ NEW
│   ├── indicators.py       # Indicator management
│   ├── config.py           # Element UID mappings
│   └── utils.py            # Export helpers
├── examples/
│   ├── basic_usage.py      # Simple examples
│   ├── export_data.py      # Export format demos
│   └── mcp_live_demo.py    # Live MCP automation ✨ NEW
├── docs/
│   ├── MCP_INTEGRATION_GUIDE.md  # Complete guide ✨ NEW
│   └── QUICK_REFERENCE.md         # Quick snippets ✨ NEW
├── exports/                # Default export directory
├── tests/
│   └── test_scraper.py     # Unit tests
├── requirements.txt
└── README.md
```

## 💾 Export Formats

### JSON
```json
{
  "symbol": "AAPL",
  "timeframe": "5m",
  "timestamp": "2026-02-08T12:30:00.000Z",
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
  "indicators": ["RSI", "EMA"]
}
```

### CSV
```csv
Symbol,Timeframe,Open,High,Low,Close,Volume,Change,Change%
AAPL,5m,234.56,235.12,234.23,234.89,1250000,1.23,0.53
```

### Excel
Formatted spreadsheet with:
- Headers
- Numeric formatting
- Timestamp columns
- Multi-sheet support (coming soon)

## 🧪 Testing

### Run Framework Demo
```bash
python tvscraper/mcp_scraper.py
```

### Run Live MCP Demo
```bash
# Ensure Chrome is open with TradingView
# MCP server is running
python examples/mcp_live_demo.py
```

### Run Specific Tests
```bash
# Test symbol changing
python examples/mcp_live_demo.py --symbol-test

# Test indicator management
python examples/mcp_live_demo.py --indicator-test
```

## ⚠️ Important Notes

### Prerequisites
- **Manual Login Required**: You must log into TradingView manually in Chrome
- **Chrome DevTools Protocol**: Requires MCP Chrome server for live automation
- **Element UIDs**: May change with TradingView updates - see documentation for updates

### Best Practices
- Add delays between actions (0.5-2.0 seconds)
- Verify actions with snapshots
- Handle errors gracefully
- Respect TradingView's terms of service
- Don't scrape excessively

### Limitations
- Requires browser session (not headless-friendly)
- Element UIDs may change with UI updates
- Some premium TradingView features require subscription
- Network speed affects reliability

## 🔧 Troubleshooting

**Elements Not Found?**
- Take a fresh snapshot to get updated UIDs
- See [MCP_INTEGRATION_GUIDE.md](docs/MCP_INTEGRATION_GUIDE.md#troubleshooting)

**Symbol Not Changing?**
- Increase delay after clicking symbol button
- Verify symbol exists on TradingView
- Check symbol search dialog opened

**Indicators Not Adding?**
- Ensure indicators dialog is visible
- Try pressing Enter instead of clicking
- Close dialog with Escape key after adding

## 📈 Roadmap

- [ ] Support for more timeframes (4h, 1D, 1W)
- [ ] Indicator parameter customization
- [ ] Historical data extraction
- [ ] Multi-chart monitoring
- [ ] Automated alert creation
- [ ] Headless mode support
- [ ] WebSocket real-time streaming

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Update documentation
5. Submit a pull request

## 📄 License

This project is for educational purposes only. Respect TradingView's terms of service.

## 🙏 Acknowledgments

- **TradingView** - Excellent charting platform
- **MCP Chrome Tools** - Chrome DevTools Protocol automation
- **GitHub Copilot** - Development assistance

---

**Current Status**: ✅ All core features implemented and tested  
**Last Updated**: February 8, 2026

---

Made with ❤️ for traders and developers
