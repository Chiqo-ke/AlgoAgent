# Historical Data Fetching Feature

**Date**: February 8, 2026  
**Feature**: Comprehensive Historical OHLCV Data Extraction

---

## 🎉 Overview

Historical data fetching capability has been added to the TradingView Scraper, enabling users to extract OHLCV (Open, High, Low, Close, Volume) data for any time range or specific number of bars.

### Key Principle
**"If no data is available up to the specified date, then the available data should be returned."**

This feature gracefully handles TradingView's data availability limitations and always returns whatever data is accessible.

---

## ✨ Features

### 1. **Flexible Data Retrieval**
- Fetch specific number of bars (e.g., last 100 bars)
- Fetch data within date ranges (e.g., January 2024)
- Fetch all available data (as much as TradingView allows)

### 2. **Graceful Degradation**
- If requested date range isn't fully available, returns available data
- Clear feedback on what was actually retrieved
- No errors when partial data exists

### 3. **Multiple Access Methods**
- Direct TradingView API access (when available)
- Fallback scrollback method
- Sample data generation for testing

---

## 📊 Method Signature

```python
def get_historical_data(
    self, 
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    bars_count: Optional[int] = None
) -> List[Dict]:
    """
    Fetch historical OHLCV data from TradingView chart.
    
    Args:
        from_date: Start date in ISO format (e.g., "2024-01-01")
        to_date: End date in ISO format (e.g., "2024-12-31")
        bars_count: Number of bars to fetch
        
    Returns:
        List of candle dictionaries with OHLCV data
    """
```

---

## 💡 Usage Examples

### Example 1: Fetch Last N Bars
```python
# Get last 100 1-hour candles
scraper.change_symbol("AAPL")
scraper.change_timeframe("1h")
data = scraper.get_historical_data(bars_count=100)

print(f"Fetched {len(data)} bars")
# Output: Fetched 100 bars
```

### Example 2: Specific Date Range
```python
# Get all data for January 2024
data = scraper.get_historical_data(
    from_date="2024-01-01",
    to_date="2024-01-31"
)

# Calculate monthly return
if data:
    start_price = data[0]['open']
    end_price = data[-1]['close']
    return_pct = ((end_price - start_price) / start_price) * 100
    print(f"January return: {return_pct:.2f}%")
```

### Example 3: All Available Data
```python
# Fetch maximum available data
data = scraper.get_historical_data()

print(f"Total bars available: {len(data)}")
print(f"Oldest: {data[0]['timestamp']}")
print(f"Newest: {data[-1]['timestamp']}")
```

### Example 4: Partial Data Handling
```python
# Request data that may not be fully available
data = scraper.get_historical_data(
    from_date="2020-01-01",  # May be too old
    to_date="2024-12-31"
)

# Returns whatever is available
if data:
    print(f"Retrieved {len(data)} bars")
    print(f"Actual range: {data[0]['timestamp']} to {data[-1]['timestamp']}")
else:
    print("No data available for this range")
```

---

## 📁 Data Structure

Each bar in the returned list has this structure:

```python
{
    "timestamp": "2024-01-15T14:00:00Z",  # ISO 8601 format
    "time": 1705327200,                    # Unix timestamp
    "open": 185.50,                        # Opening price
    "high": 186.25,                        # Highest price
    "low": 185.10,                         # Lowest price
    "close": 185.95,                       # Closing price
    "volume": 1250000                      # Trading volume
}
```

---

## 🔧 Implementation Details

### Primary Method: TradingView API Access
```javascript
// Accesses TradingView's internal chart data structures
const widget = window.tvWidget;
const chart = widget.activeChart();
const bars = chart.model().mainSeries().bars();

// Extracts bar data with filtering
for (let i = 0; i < bars.length; i++) {
    const bar = bars.get(i);
    // Filter by date range and count
    // Return formatted data
}
```

### Fallback Method: Scrollback Extraction
```python
# When API access isn't available
# 1. Scroll chart backward
# 2. Extract visible data at each position
# 3. Aggregate results
# 4. Continue until range satisfied
```

---

## 🎯 Real-World Applications

### 1. Backtesting Strategies
```python
# Fetch historical data
data = scraper.get_historical_data(bars_count=500)

# Test SMA crossover strategy
signals = []
for i in range(50, len(data)):
    sma_20 = sum(bar['close'] for bar in data[i-20:i]) / 20
    sma_50 = sum(bar['close'] for bar in data[i-50:i]) / 50
    
    if sma_20 > sma_50:
        signals.append(('BUY', data[i]['timestamp'], data[i]['close']))
```

### 2. Volatility Analysis
```python
data = scraper.get_historical_data(bars_count=100)

# Calculate daily returns
returns = []
for i in range(1, len(data)):
    ret = (data[i]['close'] - data[i-1]['close']) / data[i-1]['close']
    returns.append(ret)

# Calculate volatility
import math
volatility = math.sqrt(sum(r**2 for r in returns) / len(returns))
print(f"Volatility: {volatility * 100:.2f}%")
```

### 3. Pattern Recognition
```python
data = scraper.get_historical_data(bars_count=200)

# Find double bottoms
for i in range(20, len(data) - 20):
    # Check for local minimum
    if (data[i]['low'] < data[i-10]['low'] and 
        data[i]['low'] < data[i+10]['low']):
        print(f"Potential bottom at {data[i]['timestamp']}: ${data[i]['low']}")
```

### 4. Performance Comparison
```python
symbols = ["AAPL", "GOOGL", "MSFT"]
results = {}

for symbol in symbols:
    scraper.change_symbol(symbol)
    data = scraper.get_historical_data(bars_count=30)
    
    if data:
        change = ((data[-1]['close'] - data[0]['open']) / data[0]['open']) * 100
        results[symbol] = change

# Find best performer
best = max(results.items(), key=lambda x: x[1])
print(f"Best: {best[0]} ({best[1]:.2f}%)")
```

---

## 📈 Supported Timeframes

The feature works with all TradingView timeframes:
- **Minutes**: 1m, 3m, 5m, 15m, 30m
- **Hours**: 1h, 2h, 4h, 6h, 12h
- **Days**: 1D, 3D
- **Weeks**: 1W
- **Months**: 1M

**Note**: Amount of available data varies by:
- Timeframe (shorter = more recent data only)
- Symbol type (stocks, forex, crypto have different limits)
- TradingView subscription level (Free, Pro, Premium)

---

## ⚠️ Data Availability Limits

### TradingView Free Account
- **Stocks**: ~6-12 months on daily, ~1-2 months on hourly
- **Forex**: ~1-2 years on daily, ~2-3 months on hourly
- **Crypto**: Varies by exchange, typically 1-2 years

### TradingView Premium Account
- **Stocks**: 10+ years on daily, 6+ months on hourly
- **Forex**: 10+ years on daily, 6+ months on hourly
- **Crypto**: All available history from exchange

### Handling Limitations
```python
# Request may exceed available data
data = scraper.get_historical_data(
    from_date="2010-01-01",  # 14+ years ago
    to_date="2024-12-31"
)

# Returns available data only
if data:
    actual_start = data[0]['timestamp']
    print(f"Requested from 2010, but data starts from {actual_start}")
    # Output: "Requested from 2010, but data starts from 2020-01-01"
```

---

## 📊 Export Formats

Historical data can be exported in multiple formats:

### JSON Export
```python
import json

data = scraper.get_historical_data(bars_count=100)

with open('historical_data.json', 'w') as f:
    json.dump(data, f, indent=2)
```

### CSV Export
```python
import csv

data = scraper.get_historical_data(bars_count=100)

with open('historical_data.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
```

### Pandas DataFrame
```python
import pandas as pd

data = scraper.get_historical_data(bars_count=100)
df = pd.DataFrame(data)

# Convert timestamp to datetime
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Set as index
df.set_index('timestamp', inplace=True)

# Save to Excel
df.to_excel('historical_data.xlsx')
```

---

## 🧪 Testing Examples

8 comprehensive examples are provided in [examples/historical_data.py](../examples/historical_data.py):

1. **Fetch Last N Bars** - Basic usage with bar count
2. **Fetch Date Range** - Specific date range requests
3. **Export Historical Data** - JSON, CSV, Excel exports
4. **Calculate Indicators** - SMA calculation & crossover detection
5. **Compare Symbols** - Multi-symbol performance analysis
6. **Volatility Analysis** - Statistical analysis of returns
7. **Daily Snapshots** - Automated data collection
8. **All Available Data** - Maximum data retrieval

Run examples:
```bash
# Interactive menu
python examples/historical_data.py

# Specific example
python examples/historical_data.py 4  # Calculate indicators
python examples/historical_data.py 6  # Volatility analysis
```

---

## 🚀 Performance Considerations

### Optimization Tips

1. **Use Appropriate Timeframe**
   - Higher timeframes = more historical data available
   - Lower timeframes = less data but more detail

2. **Batch Symbol Requests**
   ```python
   symbols = ["AAPL", "GOOGL", "MSFT"]
   all_data = {}
   
   for symbol in symbols:
       scraper.change_symbol(symbol)
       time.sleep(1)  # Allow chart to load
       all_data[symbol] = scraper.get_historical_data(bars_count=100)
   ```

3. **Cache Results**
   ```python
   import json
   from datetime import datetime
   
   # Save to cache
   cache_file = f"cache_{symbol}_{datetime.now().date()}.json"
   with open(cache_file, 'w') as f:
       json.dump(data, f)
   
   # Load from cache on subsequent runs
   ```

---

## 🔮 Future Enhancements

Planned improvements:
- [ ] Real-time streaming updates
- [ ] Incremental data updates
- [ ] Built-in caching mechanism
- [ ] Progress callbacks for large requests
- [ ] Parallel multi-symbol fetching
- [ ] Automatic retry on failures
- [ ] Data quality validation
- [ ] Gap detection and handling

---

## ✅ Summary

### What's Delivered

| Feature | Status | Description |
|---------|--------|-------------|
| Bars Count Fetch | ✅ Complete | Fetch specific number of bars |
| Date Range Fetch | ✅ Complete | Fetch data between dates |
| All Data Fetch | ✅ Complete | Fetch maximum available  |
| Partial Data Handling | ✅ Complete | Returns available data gracefully |
| Multiple Formats | ✅ Complete | JSON, CSV, Excel support |
| Examples | ✅ Complete | 8 comprehensive examples |
| Documentation | ✅ Complete | Full guides and references |

### Key Benefits

✅ **Flexibility** - Multiple ways to specify data range  
✅ **Reliability** - Graceful handling of unavailable data  
✅ **Compatibility** - Works with all timeframes and symbols  
✅ **Usability** - Simple, intuitive API  
✅ **Extensibility** - Easy to integrate into trading strategies  

---

**Historical data fetching is fully implemented and ready for use!** 🎉

Use it for backtesting, analysis, research, and strategy development.
