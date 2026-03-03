# 📊 Data Export Guide

Complete guide to saving TradingView market data in multiple formats.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Export Formats](#export-formats)
3. [File Paths](#file-paths)
4. [Append Mode](#append-mode)
5. [Examples](#examples)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

```python
from demo import CompleteTVScraper

scraper = CompleteTVScraper()
data = scraper.extract_market_data()

# Save as JSON (simplest)
scraper.save_data(data, format='json')
```

---

## Export Formats

### 📄 JSON Format

**Pros:**
- Preserves nested structure
- Supports all data types
- Easy to append as array
- Human-readable

**Example:**
```python
# Default auto-generated path
filepath = scraper.save_data(data, format='json')
# Creates: exports/tv_EURUSD_20260208_143052.json

# Custom path
filepath = scraper.save_data(
    data,
    filepath='C:/my_data/eurusd.json',
    format='json'
)
```

**Output:**
```json
{
  "symbol": "EURUSD",
  "timeframe": "1 hour",
  "timestamp": "2026-02-08T14:30:52.123Z",
  "ohlc": {
    "open": 1.18208,
    "high": 1.18225,
    "low": 1.18124,
    "close": 1.18133
  },
  "volume": 9140,
  "change": {
    "absolute": -0.00076,
    "percent": -0.06
  },
  "indicators": []
}
```

**Append Mode:**
```python
# Append to existing JSON (creates array)
scraper.save_data(data, filepath='data.json', format='json', append=True)
```

Creates:
```json
[
  {...},  // First entry
  {...}   // Second entry (appended)
]
```

---

### 📊 CSV Format

**Pros:**
- Flat structure for analysis
- Easy import to Excel/Pandas
- Great for time-series data
- Space-efficient

**Example:**
```python
filepath = scraper.save_data(data, format='csv')
# Creates: exports/tv_EURUSD_20260208_143052.csv
```

**Output:**
```csv
symbol,timeframe,timestamp,ohlc_open,ohlc_high,ohlc_low,ohlc_close,volume,change_absolute,change_percent
EURUSD,1 hour,2026-02-08T14:30:52.123Z,1.18208,1.18225,1.18124,1.18133,9140,-0.00076,-0.06
```

**Features:**
- Nested dicts flattened with underscore: `ohlc_open`, `ohlc_high`
- Headers automatically included
- Append mode adds rows without duplicating headers

---

### 📈 Excel Format (XLSX)

**Pros:**
- Opens directly in Excel
- Preserves data types
- Professional presentation
- No flattening needed

**Requirements:**
```bash
pip install pandas openpyxl
```

**Example:**
```python
filepath = scraper.save_data(data, format='xlsx')
# Creates: exports/tv_EURUSD_20260208_143052.xlsx
```

**Features:**
- Uses pandas DataFrame
- Automatic type detection
- Formatted columns
- Ready for charting

**Note:** Excel format does NOT support append mode (would overwrite file).

---

## File Paths

### Auto-Generated Paths (Default)

If you omit the `filepath` parameter, paths are auto-generated:

```python
scraper.save_data(data, format='json')
# Creates: exports/tv_EURUSD_20260208_143052.json
```

**Pattern:**
```
exports/tv_{SYMBOL}_{YYYYMMDD}_{HHMMSS}.{format}
```

**Benefits:**
- No path conflicts
- Organized by symbol and time
- Automatic `exports/` folder creation

### Custom Paths

```python
# Absolute path
scraper.save_data(data, filepath='C:/data/my_file.json', format='json')

# Relative path (from project root)
scraper.save_data(data, filepath='my_data/eurusd.csv', format='csv')

# Organized structure
scraper.save_data(
    data, 
    filepath=f'exports/{symbol}/{timeframe}/{date}.json',
    format='json'
)
```

**Auto-Directory Creation:**
- All parent directories created automatically
- No need for manual `os.makedirs()`
- Safe for nested paths

---

## Append Mode

Perfect for collecting time-series data without overwriting.

### CSV Append

```python
csv_file = 'continuous_data.csv'

for i in range(100):
    data = scraper.extract_market_data()
    
    # First write creates file, rest append
    scraper.save_data(
        data,
        filepath=csv_file,
        format='csv',
        append=(i > 0)
    )
    
    time.sleep(60)  # Collect every minute
```

**Result:**
```csv
symbol,timeframe,timestamp,ohlc_close,...
EURUSD,1 hour,2026-02-08T14:00:00Z,1.18133,...
EURUSD,1 hour,2026-02-08T14:01:00Z,1.18145,...
EURUSD,1 hour,2026-02-08T14:02:00Z,1.18152,...
```

### JSON Append

```python
json_file = 'market_history.json'

for i in range(10):
    data = scraper.extract_market_data()
    scraper.save_data(data, filepath=json_file, format='json', append=True)
```

**Result:**
```json
[
  {"symbol": "EURUSD", "timestamp": "...", ...},
  {"symbol": "EURUSD", "timestamp": "...", ...},
  {"symbol": "EURUSD", "timestamp": "...", ...}
]
```

---

## Examples

### Example 1: Single Export

```python
# Get data once and save
data = scraper.extract_market_data()
filepath = scraper.save_data(data, format='json')
print(f"Saved to: {filepath}")
```

### Example 2: Multi-Format Export

```python
# Save in all formats
data = scraper.extract_market_data()

json_path = scraper.save_data(data, format='json')
csv_path = scraper.save_data(data, format='csv')
xlsx_path = scraper.save_data(data, format='xlsx')

print("Data saved in 3 formats!")
```

### Example 3: Time-Series Collection

```python
import time

csv_file = 'eurusd_5min.csv'

# Collect data every 5 minutes for 1 hour
for i in range(12):
    data = scraper.extract_market_data()
    scraper.save_data(
        data,
        filepath=csv_file,
        format='csv',
        append=(i > 0)
    )
    print(f"✅ Data point {i+1}/12 saved")
    time.sleep(300)  # 5 minutes

print(f"Complete dataset: {csv_file}")
```

### Example 4: Multi-Timeframe Archive

```python
import time

timeframes = ['1m', '5m', '30m', '1h']

for tf in timeframes:
    scraper.change_timeframe(tf)
    time.sleep(2)
    
    data = scraper.extract_market_data()
    filepath = f'exports/EURUSD_{tf}.json'
    scraper.save_data(data, filepath=filepath, format='json')
    
    print(f"✅ {tf} data saved")
```

### Example 5: Organized by Date

```python
from datetime import datetime

# Get data
data = scraper.extract_market_data()

# Create organized structure
symbol = data['symbol']
date = datetime.now().strftime('%Y-%m-%d')
hour = datetime.now().strftime('%H')

# Save: exports/2026-02-08/EURUSD/hour_14.json
filepath = f'exports/{date}/{symbol}/hour_{hour}.json'
scraper.save_data(data, filepath=filepath, format='json')
```

### Example 6: Custom Data Structure

```python
# Extract raw data
raw_data = scraper.extract_market_data()

# Create custom structure
custom = {
    "metadata": {
        "symbol": raw_data['symbol'],
        "collected_at": raw_data['timestamp']
    },
    "prices": raw_data['ohlc'],
    "volume": raw_data['volume']
}

# Save custom structure
scraper.save_data(custom, filepath='custom_data.json', format='json')
```

---

## Best Practices

### ✅ DO

1. **Use append mode for time-series**
   ```python
   scraper.save_data(data, filepath='series.csv', format='csv', append=True)
   ```

2. **Let auto-generation handle paths initially**
   ```python
   filepath = scraper.save_data(data, format='json')
   ```

3. **Check returned filepath**
   ```python
   saved_path = scraper.save_data(data, format='csv')
   print(f"Data saved to: {saved_path}")
   ```

4. **Use JSON for complex nested data**
   ```json
   {"ohlc": {"open": 1.18, ...}, "indicators": [...]}
   ```

5. **Use CSV for flat time-series analysis**
   ```csv
   timestamp,open,high,low,close
   ```

### ❌ DON'T

1. **Don't use Excel append mode** (not supported)
   ```python
   # ❌ This will overwrite!
   scraper.save_data(data, format='xlsx', append=True)
   ```

2. **Don't forget error handling**
   ```python
   ✅ try:
       scraper.save_data(data, format='xlsx')
   except ImportError:
       print("Install pandas first!")
   ```

3. **Don't mix formats in append mode**
   ```python
   # ❌ Don't append JSON to CSV file
   scraper.save_data(data, filepath='data.csv', format='json')
   ```

4. **Don't use spaces in filenames**
   ```python
   ❌ filepath = 'my data.json'  # Bad
   ✅ filepath = 'my_data.json'  # Good
   ```

---

## Troubleshooting

### Issue: "No such file or directory"

**Cause:** Parent directories don't exist.

**Solution:** Auto-created! This shouldn't happen, but if it does:
```python
from pathlib import Path
Path('my/deep/path').mkdir(parents=True, exist_ok=True)
```

### Issue: "ModuleNotFoundError: No module named 'pandas'"

**Cause:** Excel export requires pandas.

**Solution:**
```bash
pip install pandas openpyxl
```

### Issue: CSV file has duplicate headers

**Cause:** Not using append mode correctly.

**Solution:**
```python
# First write (creates file with header)
scraper.save_data(data, filepath='data.csv', format='csv', append=False)

# Subsequent writes (append without header)
scraper.save_data(data, filepath='data.csv', format='csv', append=True)
```

### Issue: JSON file not an array when appending

**Cause:** First write needs `append=False`, subsequent need `append=True`.

**Solution:**
```python
# First
scraper.save_data(data, filepath='data.json', format='json', append=False)
# Creates: {...}

# Convert to array for appending
scraper.save_data(data, filepath='data.json', format='json', append=True)
# Now: [{...}, {...}]
```

### Issue: File encoding issues with special characters

**Solution:** All files saved with UTF-8 encoding by default.

---

## Advanced Usage

### Memory-Efficient Large Dataset Collection

```python
import time

csv_file = 'large_dataset.csv'

# Collect 1000 data points
for i in range(1000):
    data = scraper.extract_market_data()
    
    # Write immediately, don't store in memory
    scraper.save_data(
        data,
        filepath=csv_file,
        format='csv',
        append=(i > 0)
    )
    
    if i % 100 == 0:
        print(f"Progress: {i}/1000")
    
    time.sleep(5)
```

### Automatic Backup

```python
from datetime import datetime

data = scraper.extract_market_data()

# Save to primary location
scraper.save_data(data, filepath='current_data.json', format='json')

# Automatic timestamped backup
backup_path = f'backups/backup_{datetime.now():%Y%m%d_%H%M%S}.json'
scraper.save_data(data, filepath=backup_path, format='json')
```

### Export with Validation

```python
def save_with_validation(scraper, data, filepath, format='json'):
    """Save data and validate file was created."""
    from pathlib import Path
    
    saved_path = scraper.save_data(data, filepath=filepath, format=format)
    
    if Path(saved_path).exists():
        file_size = Path(saved_path).stat().st_size
        print(f"✅ Saved: {saved_path} ({file_size} bytes)")
        return True
    else:
        print(f"❌ Failed to save: {saved_path}")
        return False

# Usage
save_with_validation(scraper, data, 'my_data.json', format='json')
```

---

## API Reference

### `save_data(data, filepath=None, format='json', append=False)`

**Parameters:**

- **data** (dict): Market data dictionary to save
- **filepath** (str, optional): Path where to save file
  - If `None`: Auto-generates `exports/tv_{symbol}_{timestamp}.{format}`
  - Supports absolute and relative paths
  - Parent directories created automatically
- **format** (str): Export format
  - `'json'`: JSON format (default)
  - `'csv'`: CSV format  
  - `'xlsx'` or `'excel'`: Excel format (requires pandas)
- **append** (bool): Whether to append to existing file
  - `False`: Create new file or overwrite (default)
  - `True`: Append to existing file (JSON as array, CSV as rows)
  - Not supported for Excel format

**Returns:**
- **str**: Absolute path to saved file

**Raises:**
- **ImportError**: If pandas/openpyxl not installed (Excel format only)
- **ValueError**: If format not recognized

**Examples:**
```python
# Auto-generated path
path = scraper.save_data(data, format='json')

# Custom path
path = scraper.save_data(data, filepath='C:/data/file.csv', format='csv')

# Append mode
path = scraper.save_data(data, filepath='series.csv', format='csv', append=True)
```

---

**For more examples, see:** `examples/export_data.py`

**Happy exporting! 📊✨**
