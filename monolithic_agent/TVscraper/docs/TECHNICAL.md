# TradingView Scraper - Technical Documentation

## Architecture

The TVscraper is built using Chrome DevTools Protocol (CDP) to interact with TradingView charts. It does NOT use web scraping or HTTP requests, but instead controls the browser directly.

### Key Components

1. **scraper.py**: Main scraper class with high-level API
2. **indicators.py**: Indicator definitions and parameter validation
3. **utils.py**: Helper functions for data parsing and formatting
4. **live_scraper.py**: Live implementation with MCP integration

## How It Works

### Page Structure Analysis

TradingView uses a complex React-based UI. Key elements identified:

```
Root (uid=1_0)
├── Symbol Button (uid=1_2) - "EURUSD"
├── Timeframe Buttons
│   ├── 1m (uid=1_5)
│   ├── 3m (uid=1_6)
│   ├── 5m (uid=1_7)
│   ├── 30m (uid=1_8)
│   └── 1h (uid=1_9)
├── Indicators Button (uid=1_12)
└── Chart Region (uid=1_55)
    ├── OHLC Legend
    │   ├── O: 1.18208 (uid=1_64, 1_65)
    │   ├── H: 1.18225 (uid=1_66, 1_67)
    │   ├── L: 1.18124 (uid=1_68, 1_69)
    │   └── C: 1.18133 (uid=1_70, 1_71)
    ├── Indicator Legends
    │   ├── EMA(9) (uid=1_81-1_87)
    │   ├── Volume (uid=1_88-1_93)
    │   └── BB(20) (uid=1_94-1_102)
    └── Chart Canvas (uid=1_103)
```

### Data Extraction Strategy

1. **Snapshot Method**: Take accessibility tree snapshot to find elements
2. **Click Interaction**: Use UIDs to click buttons and change settings
3. **JavaScript Execution**: Inject scripts to extract chart data
4. **Network Monitoring**: Monitor WebSocket/API calls for raw data

### TradingView Internal Data

TradingView stores chart data in internal JavaScript objects. Key paths:

```javascript
// Chart data (requires reverse engineering)
window.tvWidget.chart()
window.tvWidget.activeChart()

// Symbol info
window.tvWidget.chart().symbol()

// Timeframe
window.tvWidget.chart().resolution()

// Price data
window.tvWidget.chart().getAllStudies()
window.tvWidget.chart().getSeries()
```

## API Usage

### Basic Usage

```python
from tvscraper import TradingViewScraper

scraper = TradingViewScraper()

# Change symbol
scraper.set_symbol("BTCUSD")

# Set timeframe  
scraper.set_timeframe("1h")

# Add indicators (max 2)
scraper.add_indicator("EMA", {"length": 20})
scraper.add_indicator("RSI", {"length": 14})

# Get data
data = scraper.get_market_data(bars=100)
```

### Advanced Usage

```python
from tvscraper import TradingViewScraper, IndicatorManager

# List available indicators
indicators = IndicatorManager.list_indicators()

# Validate parameters
is_valid = IndicatorManager.validate_parameters("MACD", {
    "fast_length": 12,
    "slow_length": 26,
    "signal_length": 9
})

# Get current OHLC
scraper = TradingViewScraper()
ohlc = scraper.get_current_price()
print(f"Current Close: {ohlc['close']}")
```

## MCP Integration

The scraper uses Model Context Protocol (MCP) Chrome DevTools integration:

### Required MCP Tools

1. `mcp_io_github_chr_take_snapshot` - Get page structure
2. `mcp_io_github_chr_click` - Click elements
3. `mcp_io_github_chr_fill` - Fill input fields
4. `mcp_io_github_chr_evaluate_script` - Execute JavaScript
5. `mcp_io_github_chr_list_network_requests` - Monitor data requests

### Example MCP Calls

```python
# Take snapshot
snapshot = mcp.take_snapshot()

# Click symbol button (uid=1_2)
mcp.click(uid="1_2")

# Execute script
result = mcp.evaluate_script("""
    () => {
        return window.tvWidget.chart().symbol();
    }
""")
```

## Data Format

### Market Data Response

```json
{
    "symbol": "EURUSD",
    "timeframe": "1h",
    "ohlc": {
        "open": 1.18208,
        "high": 1.18225,
        "low": 1.18124,
        "close": 1.18133,
        "volume": 9140,
        "timestamp": 1707436800
    },
    "indicators": {
        "EMA(9)": {
            "value": 1.18133,
            "visible": true
        },
        "RSI(14)": {
            "value": 52.3,
            "visible": true
        }
    },
    "bars": [
        {
            "time": 1707436800,
            "open": 1.18200,
            "high": 1.18250,
            "low": 1.18100,
            "close": 1.18133,
            "volume": 9140
        }
        // ... more bars
    ]
}
```

## Limitations

1. **Maximum 2 Indicators**: Designed for focused analysis
2. **Manual Login Required**: User must log in to TradingView manually
3. **Browser Dependency**: Requires active Chrome session
4. **Rate Limiting**: Respects TradingView's usage limits
5. **Data Availability**: Limited to what's visible on the chart

## Troubleshooting

### Scraper Not Finding Elements

```python
# Take a fresh snapshot to get updated UIDs
scraper._take_snapshot()
```

### Data Extraction Fails

```python
# Wait longer for data to load
scraper.wait_for_data_load(timeout=15)
```

### Indicator Not Adding

```python
# Check if max indicators reached
if len(scraper.active_indicators) >= 2:
    scraper.remove_indicator("EMA")
    scraper.add_indicator("MACD")
```

## Privacy & Ethics

- This tool is for personal use and research
- Respect TradingView's Terms of Service
- Do not overload their servers
- Implement appropriate rate limiting
- Use for educational purposes

## Future Enhancements

- [ ] Support for more simultaneous indicators
- [ ] Historical data extraction
- [ ] Multiple timeframe analysis
- [ ] Alert monitoring
- [ ] Symbol watchlist scraping
- [ ] Drawing tools extraction
- [ ] Save/load chart layouts
