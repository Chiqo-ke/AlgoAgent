# Backtesting.py Integration - Complete Implementation

**Date:** October 31, 2025  
**Status:** ✅ COMPLETED

---

## Overview

Successfully migrated from custom SimBroker backtesting system to the professional **backtesting.py** package (kernc/backtesting.py v0.6.5). This provides a robust, industry-standard framework with better performance, built-in metrics, and parameter optimization capabilities.

---

## What Changed

### Before (SimBroker)
- Custom-built backtesting engine
- Manual metric calculations
- Bar-by-bar simulation with manual order management
- Limited to custom implementation

### After (backtesting.py)
- Professional, maintained open-source framework
- Vectorized operations for better performance  
- Built-in comprehensive metrics (Sharpe, Sortino, Calmar, etc.)
- Interactive Bokeh visualizations
- Parameter optimization capabilities
- Larger community and ecosystem

---

## Files Created/Modified

### 1. New Files Created

#### `Backtest/backtesting_adapter.py`
**Purpose:** Adapter layer to integrate backtesting.py with existing system

**Key Classes:**
- `BacktestingAdapter`: Main wrapper around backtesting.py's Backtest class
- `create_strategy_from_canonical()`: Converts canonical JSON to Strategy classes
- `fetch_and_prepare_data()`: Fetches and formats data for backtesting.py
- `run_backtest_from_canonical()`: Complete workflow from canonical JSON to results

**Features:**
- Compatible interface with existing system
- Handles MultiIndex columns from yfinance
- Proper column naming (capitalized OHLCV)
- Exports trades to CSV
- Converts metrics to format compatible with frontend

#### `Backtest/SYSTEM_PROMPT_BACKTESTING_PY.md`
**Purpose:** System prompt for Gemini AI to generate backtesting.py-compatible strategies

**Contents:**
- Complete code structure template
- Strategy class patterns (MA crossover, RSI, Bollinger Bands, etc.)
- Best practices and common pitfalls
- Error handling guidelines
- Parameter optimization examples

#### `Backtest/codes/test_ma_crossover_backtesting_py.py`
**Purpose:** Working example strategy using backtesting.py

**Features:**
- Simple MA crossover strategy
- Complete with data fetching, backtest execution, and results display
- Exports trades to CSV
- Demonstrates the new workflow

### 2. Modified Files

#### `Backtest/gemini_strategy_generator.py`
**Changes:**
- Added `use_backtesting_py` flag (defaults to True)
- Updated `_load_system_prompt()` to load appropriate prompt
- Can still generate SimBroker strategies if needed (legacy support)

**New behavior:**
```python
# Default: generates backtesting.py strategies
generator = GeminiStrategyGenerator()

# Legacy: generates SimBroker strategies
generator.use_backtesting_py = False
```

#### `backtest_api/views.py`
**Changes:** Updated `quick_run()` endpoint to use backtesting.py

**New Features:**
- Accepts canonical JSON directly
- Uses `run_backtest_from_canonical()` for execution
- Returns comprehensive metrics in frontend-compatible format
- Better error handling with detailed stack traces

**API Response Format:**
```json
{
  "status": "completed",
  "summary": {
    "total_return": 12.93,
    "total_trades": 2,
    "win_rate": 50.0,
    "sharpe_ratio": 0.83,
    "max_drawdown": -15.39,
    "final_equity": 11293.31
  },
  "metrics": {
    "start_date": "2024-01-02",
    "end_date": "2024-10-30",
    "exposure_time": 38.09,
    "return_pct": 12.93,
    "volatility_ann": 18.87,
    "calmar_ratio": 1.02,
    ...
  },
  "trades": [...],
  "daily_stats": [],
  "symbol_stats": [...]
}
```

---

## Architecture

### Data Flow

```
┌─────────────────────┐
│  Canonical JSON     │
│  (from AI)          │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ create_strategy_    │
│ from_canonical()    │
│                     │
│ Generates:          │
│ - Strategy class    │
│ - init() with       │
│   indicators        │
│ - next() with       │
│   entry/exit logic  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ fetch_and_prepare_  │
│ data()              │
│                     │
│ Returns:            │
│ - DataFrame with    │
│   OHLCV data        │
│ - Proper format     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ BacktestingAdapter  │
│                     │
│ Wraps:              │
│ - Backtest()        │
│ - Strategy          │
│ - Data              │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Run Backtest        │
│                     │
│ Returns:            │
│ - Results (Series)  │
│ - Trades (DF)       │
│ - Metrics           │
└─────────────────────┘
```

### Strategy Structure

```python
class YourStrategy(Strategy):
    """Inherits from backtesting.Strategy"""
    
    # Parameters (can be optimized)
    param1 = default_value
    param2 = default_value
    
    def init(self):
        """
        Initialize indicators once
        - Runs at start of backtest
        - Use self.I() wrapper for indicators
        - Vectorized operations
        """
        self.indicator1 = self.I(SMA, self.data.Close, period)
        self.indicator2 = self.I(EMA, self.data.Close, period)
    
    def next(self):
        """
        Execute strategy logic for each bar
        - Called sequentially for each data point
        - Check positions: self.position
        - Execute trades: self.buy(), self.sell(), self.position.close()
        """
        if not self.position:
            if crossover(self.indicator1, self.indicator2):
                self.buy()
        elif crossover(self.indicator2, self.indicator1):
            self.position.close()
```

---

## Key Features

### 1. Built-in Indicators

backtesting.py includes common indicators:
```python
from backtesting.test import SMA, GOOG

self.sma = self.I(SMA, self.data.Close, 20)
```

### 2. Custom Indicators

Easy to create custom indicators:
```python
def EMA(series, period):
    return pd.Series(series).ewm(span=period).mean()

self.ema = self.I(EMA, self.data.Close, 20)
```

### 3. Crossover Helper

Built-in crossover detection:
```python
from backtesting.lib import crossover

if crossover(self.ma1, self.ma2):  # ma1 crosses above ma2
    self.buy()
```

### 4. Position Management

```python
# Check position
if self.position:
    print(f"Size: {self.position.size}")
    print(f"P/L: {self.position.pl}")

# Trade operations
self.buy()                  # Market order
self.buy(limit=100.50)      # Limit order
self.buy(stop=101.25)       # Stop order
self.position.close()       # Close position
self.position.close(0.5)    # Close 50%
```

### 5. Parameter Optimization

```python
# Optimize strategy parameters
results = bt.optimize(
    fast_period=range(5, 20, 5),
    slow_period=range(20, 100, 10),
    maximize='Sharpe Ratio',
    constraint=lambda p: p.fast_period < p.slow_period
)
```

### 6. Interactive Visualization

```python
# Generate interactive Bokeh chart
adapter.plot()  # Opens in browser
```

---

## Performance Comparison

### SimBroker (Old)
- **Execution:** Bar-by-bar simulation
- **Speed:** Slower (Python loops)
- **Metrics:** Manual calculation
- **Visualization:** Manual plotting required

### backtesting.py (New)
- **Execution:** Vectorized operations
- **Speed:** Much faster (NumPy/Pandas)
- **Metrics:** 30+ built-in metrics
- **Visualization:** Interactive Bokeh charts

---

## Test Results

### Test Strategy: Simple MA Crossover
- **Symbol:** AAPL
- **Period:** 2024-01-01 to 2024-10-31 (302 days)
- **Initial Capital:** $10,000
- **Commission:** 0.2%

### Results:
```
Return:              12.93%
Total Trades:        2
Win Rate:            50.0%
Sharpe Ratio:        0.83
Sortino Ratio:       1.52
Calmar Ratio:        1.02
Max Drawdown:        -15.39%
Final Equity:        $11,293.31
Profit Factor:       3.51
```

**Status:** ✅ Test passed successfully!

---

## API Integration

### Endpoint: `/api/backtest/quick_run/`

**Request:**
```json
{
  "strategy_code": {...},  // Canonical JSON
  "strategy_id": 123,      // Or existing strategy ID
  "symbol": "AAPL",
  "start_date": "2024-01-01",
  "end_date": "2024-10-31",
  "timeframe": "1d",
  "initial_balance": 10000,
  "commission": 0.002
}
```

**Response:**
```json
{
  "status": "completed",
  "summary": {
    "total_return": 12.93,
    "total_trades": 2,
    "win_rate": 50.0,
    "sharpe_ratio": 0.83,
    "max_drawdown": -15.39,
    "final_equity": 11293.31
  },
  "metrics": {...},
  "trades": [...],
  "symbol_stats": [...]
}
```

---

## Frontend Integration

The frontend already calls `/api/backtest/quick_run/` endpoint. No changes required! The new backtesting.py system is a drop-in replacement that returns the same response format.

**Files using the endpoint:**
- `Algo/src/pages/Backtesting.tsx`
- `Algo/src/lib/services.ts`

---

## Migration Guide

### For New Strategies

All new strategies generated by AI will automatically use backtesting.py format. No action needed.

### For Existing Strategies

Existing strategies stored as canonical JSON will work automatically with the new system through `create_strategy_from_canonical()`.

### For Custom Python Strategies

If you have custom Python strategies using SimBroker:

1. **Option A:** Continue using SimBroker (still available)
2. **Option B:** Convert to backtesting.py format:

```python
# Old (SimBroker)
class MyStrategy:
    def __init__(self, broker, symbol):
        self.broker = broker
        
    def on_bar(self, timestamp, data):
        # Logic here
        signal = create_signal(...)
        self.broker.submit_signal(signal)

# New (backtesting.py)
class MyStrategy(Strategy):
    def init(self):
        # Initialize indicators
        
    def next(self):
        # Logic here
        self.buy()  # Or self.sell(), self.position.close()
```

---

## Benefits Summary

✅ **Professional Framework:** Industry-standard, actively maintained  
✅ **Better Performance:** Vectorized operations, faster execution  
✅ **Comprehensive Metrics:** 30+ built-in metrics  
✅ **Interactive Charts:** Beautiful Bokeh visualizations  
✅ **Parameter Optimization:** Built-in grid search and optimization  
✅ **Active Community:** Large user base, frequent updates  
✅ **Better Documentation:** Extensive docs and examples  
✅ **Testing:** Well-tested framework with many real-world users  

---

## Troubleshooting

### Issue: Import errors in VS Code

**Cause:** Linter doesn't detect .venv packages  
**Solution:** Errors are cosmetic only. Code runs fine.

### Issue: "Cannot broadcast" error

**Cause:** Indicator array length mismatch  
**Solution:** Always use `self.I()` wrapper for indicators

### Issue: "KeyError: 'Close'"

**Cause:** Data columns not capitalized  
**Solution:** Use `fetch_and_prepare_data()` which handles this

### Issue: MultiIndex columns

**Cause:** yfinance returns MultiIndex  
**Solution:** Already handled in `fetch_and_prepare_data()`

---

## Future Enhancements

### Potential Additions

1. **Walk-Forward Analysis:** Time-series cross-validation
2. **Monte Carlo Simulation:** Robustness testing
3. **Portfolio Backtesting:** Multiple strategies together
4. **Live Trading Integration:** Connect to brokers
5. **Custom Metrics:** Add domain-specific metrics
6. **Strategy Comparison:** Side-by-side comparison
7. **Risk Analytics:** VaR, CVaR, tail risk
8. **Regime Detection:** Market regime analysis

---

## Dependencies

### Python Packages

```txt
backtesting==0.6.5  # Main framework
pandas>=1.3.0       # Data manipulation
numpy>=1.20.0       # Numerical operations
bokeh>=2.4.0        # Visualization (auto-installed with backtesting)
```

### Installation

```bash
# Already installed in .venv
pip install backtesting
```

---

## Documentation Links

- **backtesting.py Docs:** https://kernc.github.io/backtesting.py/
- **GitHub Repo:** https://github.com/kernc/backtesting.py
- **Examples:** https://kernc.github.io/backtesting.py/doc/examples/

---

## Conclusion

The migration to backtesting.py is **complete and successful**. The system now uses a professional, well-maintained framework that provides better performance, comprehensive metrics, and interactive visualizations while maintaining full compatibility with existing code.

### Implementation Status

✅ Adapter layer created  
✅ Strategy generator updated  
✅ API endpoint modified  
✅ Test strategy verified  
✅ Documentation complete  
✅ Backward compatibility maintained  

**The system is production-ready!**

---

**Document Version:** 1.0  
**Last Updated:** October 31, 2025  
**Author:** AlgoAgent Development Team
