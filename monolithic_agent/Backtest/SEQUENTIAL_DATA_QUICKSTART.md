# Sequential Data Ingestion - Quick Start Guide

## Overview

The backtest system now supports **two data ingestion modes**:

1. **STREAMING MODE** (Default) - Sequential row-by-row processing
2. **BATCH MODE** - Bulk data processing

## Quick Commands

### Check Current Mode
```bash
python set_mode.py info
```

### Switch Modes
```bash
# Enable streaming mode (sequential)
python set_mode.py streaming
# OR
set_streaming_mode.bat

# Enable batch mode (bulk)
python set_mode.py batch
# OR
set_batch_mode.bat
```

## For Strategy Developers

### Using Streaming Mode (Recommended)

```python
from Backtest.data_loader import load_market_data

# Get streaming generator
data_stream = load_market_data(
    ticker="AAPL",
    indicators={'RSI': {'timeperiod': 14}, 'SMA': {'timeperiod': 20}},
    period='6mo',
    interval='1d',
    stream=True  # ✅ Enable streaming
)

# Process row-by-row
for timestamp, market_data, progress_pct in data_stream:
    strategy.on_bar(timestamp, market_data)
    broker.step_to(timestamp, market_data)
    
    # Progress tracking is automatic
    if int(progress_pct) % 10 == 0:
        print(f"Progress: {progress_pct:.1f}%")
```

### Using Batch Mode

```python
from Backtest.data_loader import load_market_data

# Load all data at once
df, metadata = load_market_data(
    ticker="AAPL",
    indicators={'RSI': {'timeperiod': 14}},
    period='6mo',
    interval='1d',
    stream=False  # Batch mode
)

# Manual iteration
for timestamp, row in df.iterrows():
    market_data = {
        'AAPL': {
            'open': row['Open'],
            'high': row['High'],
            'low': row['Low'],
            'close': row['Close'],
            'volume': row['Volume'],
            **{col.lower(): row[col] for col in df.columns 
               if col.lower() not in ['open', 'high', 'low', 'close', 'volume']}
        }
    }
    strategy.on_bar(timestamp, market_data)
    broker.step_to(timestamp, market_data)
```

## Mode Comparison

| Feature | Streaming Mode | Batch Mode |
|---------|---------------|------------|
| **Processing** | Row-by-row sequential | Bulk all-at-once |
| **Look-ahead bias** | ✅ Prevented | ⚠️ Possible |
| **Real-time simulation** | ✅ Yes | ❌ No |
| **Performance** | Slightly slower | Faster |
| **Progress tracking** | ✅ Automatic | Manual |
| **Data format** | Pre-formatted dict | Manual formatting needed |
| **Use case** | Production-like testing | Rapid prototyping |

## When to Use Each Mode

### Use STREAMING MODE when:
- ✅ Default choice for most strategies
- ✅ Need strict sequential processing
- ✅ Want to prevent look-ahead bias
- ✅ Simulating real-time trading behavior
- ✅ Testing production-like scenarios

### Use BATCH MODE when:
- ⚡ Rapid prototyping and testing
- ⚡ Need to perform vectorized calculations
- ⚡ Performance is critical
- ⚡ Debugging with full data visibility

## Testing

Run the test suite to verify both modes work correctly:

```bash
cd c:\Users\nyaga\Documents\AlgoAgent\Backtest
python test_streaming_mode.py
```

This will:
1. Test streaming mode with sequential processing
2. Test batch mode with bulk processing
3. Compare results (should be identical)
4. Verify no look-ahead bias in streaming mode

## Files Modified/Created

### Core Implementation
- ✅ `data_loader.py` - Added `stream` parameter and `_stream_data()` generator
- ✅ `pattern_logger.py` - Fixed empty log file handling
- ✅ `signal_logger.py` - Fixed empty signal file handling

### Configuration
- ✅ `sequential_config.py` - Central configuration for mode management
- ✅ `set_mode.py` - CLI tool for switching modes

### User Tools
- ✅ `set_streaming_mode.bat` - Quick switch to streaming mode
- ✅ `set_batch_mode.bat` - Quick switch to batch mode

### Documentation
- ✅ `SYSTEM_PROMPT.md` - Updated with both mode patterns
- ✅ `SEQUENTIAL_DATA_QUICKSTART.md` - This file

### Testing
- ✅ `test_streaming_mode.py` - Comprehensive test suite

## Example Output

### Streaming Mode
```
🔄 Loading data in STREAMING mode (sequential)...
✓ Data stream initialized
✓ Processing bars sequentially...

  Progress: 20.0% (100 bars)
  Progress: 40.0% (200 bars)
  Progress: 60.0% (300 bars)
  Progress: 80.0% (400 bars)
  Progress: 100.0% (500 bars)

✓ Completed: Processed 500 bars sequentially
```

### Batch Mode
```
⚡ Loading data in BATCH mode...
✓ Loaded 500 bars
✓ Columns: ['Open', 'High', 'Low', 'Close', 'Volume', 'RSI_14']
✓ Processing bars...

  Progress: 20.0%
  Progress: 40.0%
  Progress: 60.0%
  Progress: 80.0%

✓ Completed: Processed 500 bars
```

## Integration with AI Agent

The AI agent will automatically check `sequential_config.py` to determine which mode to use when generating strategy code. The default is **STREAMING MODE** for realistic backtesting.

To change the default:
```bash
python set_mode.py streaming  # Set to streaming
python set_mode.py batch      # Set to batch
```

## Support

For issues or questions:
1. Check `python set_mode.py info` for current configuration
2. Run `python test_streaming_mode.py` to verify implementation
3. Review `SYSTEM_PROMPT.md` for code generation patterns

---

**Created:** 2025-11-03  
**Version:** 1.0.0  
**Status:** ✅ Tested and Verified
