# MT5 Integration Guide

Complete guide for integrating Python-generated signals with MetaTrader5 execution.

## Overview

This integration enables you to:
1. **Develop strategies in Python** - Fast iteration with rich libraries
2. **Export signals to MT5** - Structured signal files
3. **Execute in MT5** - Realistic broker simulation
4. **Validate results** - Compare and reconcile outcomes

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Python Strategy Layer                    │
├─────────────────────────────────────────────────────────────┤
│  • Strategy Logic (indicators, signals)                      │
│  • SimBroker (Python backtest simulation)                    │
│  • SignalExporter (MT5-compatible export)                    │
└────────────────────┬────────────────────────────────────────┘
                     │ CSV/JSON Signal Files
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    MT5 Execution Layer                       │
├─────────────────────────────────────────────────────────────┤
│  • PythonSignalExecutor EA (reads signals)                   │
│  • MT5 Strategy Tester (realistic execution)                 │
│  • Trade History & Reports                                   │
└────────────────────┬────────────────────────────────────────┘
                     │ Execution Results
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Reconciliation Layer                        │
├─────────────────────────────────────────────────────────────┤
│  • Compare signal execution rate                             │
│  • Analyze price differences                                 │
│  • Validate metrics                                          │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

1. **Python Environment**:
   ```bash
   pip install MetaTrader5 pandas numpy
   ```

2. **MetaTrader5 Terminal**:
   - Installed and configured
   - Demo or live account logged in
   - Historical data downloaded for your symbol

### Step 1: Enable MT5 Export in Python

Modify your backtest script to enable signal export:

```python
from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig

# Initialize broker with MT5 export enabled
config = BacktestConfig(start_cash=10000)
broker = SimBroker(
    config=config,
    enable_mt5_export=True,      # Enable export
    mt5_symbol="XAUUSD",         # MT5 symbol name
    mt5_timeframe="H1"           # MT5 timeframe
)

# Run your backtest as normal
# ... strategy logic ...

# Export signals at the end
signal_files = broker.export_mt5_signals(format="both")
print(f"Signals exported to: {signal_files['csv']}")
```

### Step 2: Copy Files to MT5

**Signal File**:
- Copy the generated CSV file to MT5's Files directory
- Path: `C:\Users\[User]\AppData\Roaming\MetaQuotes\Terminal\[ID]\MQL5\Files\`

**Expert Advisor**:
- Copy `PythonSignalExecutor.mq5` to MT5's Experts directory
- Path: `C:\Users\[User]\AppData\Roaming\MetaQuotes\Terminal\[ID]\MQL5\Experts\`
- Compile in MetaEditor (F7)

### Step 3: Configure MT5 Strategy Tester

1. Open Strategy Tester (View → Strategy Tester or Ctrl+R)

2. **General Settings**:
   - Expert Advisor: `PythonSignalExecutor`
   - Symbol: `XAUUSD` (must match your export)
   - Period: `H1` (must match your export)
   - Date Range: Match your Python backtest dates

3. **Model Settings**:
   - Model: `Every tick based on real ticks` (most accurate)
   - Alternatively: `1 minute OHLC` (faster)
   - Optimization: OFF (disable)

4. **EA Parameters** (Inputs tab):
   - `SignalFile`: Filename of your CSV (e.g., `BT_20241018_XAUUSD_H1_signals.csv`)
   - `RiskPercent`: `0` (use signal lot sizes) or `1.0` (risk-based sizing)
   - `Slippage`: `10` points
   - `MagicNumber`: `20241018` (any unique number)

### Step 4: Run Backtest

1. Click **Start** button
2. Monitor the **Journal** tab for EA logs:
   - "Successfully loaded X signals"
   - "Signal Found" messages for each bar
   - Trade execution confirmations

3. Wait for completion
4. Review **Report** tab

### Step 5: Compare Results

```python
from Backtest.mt5_reconciliation import MT5Reconciliation

reconciler = MT5Reconciliation()

# Load data
reconciler.load_python_signals(Path("Backtest/mt5_signals/signals.csv"))
reconciler.load_python_trades(Path("Backtest/results/trades.csv"))

# Compare metrics
python_metrics = {
    'total_trades': 45,
    'total_pnl': 12500.0,
    'win_rate': 0.62,
    'max_drawdown': 0.08
}

mt5_metrics = {
    'total_trades': 44,          # Might differ slightly
    'total_pnl': 12200.0,        # Expect lower (more realistic)
    'win_rate': 0.61,
    'max_drawdown': 0.09
}

comparison = reconciler.compare_metrics(python_metrics, mt5_metrics)
print("Metric Comparison:", comparison)
```

## Signal File Format

### CSV Format (Recommended for MT5)

```csv
Timestamp,Symbol,Signal,LotSize,StopLoss,TakeProfit,SignalID,Metadata
2024-01-15T09:00:00+00:00,XAUUSD,BUY,0.10,1950.00,1990.00,SIG-001,"{""strategy"":""MA_Cross""}"
2024-01-15T10:00:00+00:00,XAUUSD,HOLD,0.00,0.00,0.00,SIG-002,"{}"
2024-01-15T14:00:00+00:00,XAUUSD,EXIT,0.10,0.00,0.00,SIG-003,"{""reason"":""stop_loss""}"
```

**Fields**:
- `Timestamp`: ISO 8601 format with timezone
- `Symbol`: MT5 symbol name (e.g., "XAUUSD")
- `Signal`: BUY, SELL, EXIT, or HOLD
- `LotSize`: MT5 lot size (0.01 = 1 micro lot)
- `StopLoss`: Absolute price (0 = no stop)
- `TakeProfit`: Absolute price (0 = no take profit)
- `SignalID`: Unique identifier for tracking
- `Metadata`: JSON string with additional context

### JSON Format (Richer metadata)

```json
{
  "backtest_id": "BT_20241018_120000",
  "symbol": "XAUUSD",
  "timeframe": "H1",
  "signals": [
    {
      "timestamp": "2024-01-15T09:00:00+00:00",
      "signal": "BUY",
      "lot_size": 0.10,
      "stop_loss": 1950.00,
      "take_profit": 1990.00,
      "signal_id": "SIG-001",
      "metadata": "{\"ma_fast\": 1975.2, \"ma_slow\": 1960.5}"
    }
  ]
}
```

## Lot Size Conversion

Python uses shares/contracts, MT5 uses lots. The SignalExporter automatically converts:

**XAUUSD**:
- 1 lot = 100 oz
- Python size 100 → MT5 lot 1.00
- Python size 10 → MT5 lot 0.10

**Forex (EURUSD)**:
- 1 lot = 100,000 units
- Python size 100000 → MT5 lot 1.00
- Python size 10000 → MT5 lot 0.10

**Customize** in `SignalExporter.LOT_SIZE_CONVERSIONS`.

## Expert Advisor (EA) Logic

The `PythonSignalExecutor.mq5` EA:

1. **OnInit()**: Loads signal CSV file into memory
2. **OnTick()**: Checks for new bar
3. **On new bar**: 
   - Looks up signal for current bar timestamp
   - Executes trading action (BUY/SELL/EXIT)
4. **Position Management**:
   - Closes opposite positions before opening new
   - Applies stop loss and take profit
   - Uses magic number for isolation

**Key Features**:
- Fast signal lookup (array search)
- Timestamp validation
- Verbose logging for debugging
- Error handling for invalid signals

## Data Synchronization

**Critical**: Python and MT5 must use identical historical data.

### Option 1: MT5 as Source of Truth

```python
from Backtest.mt5_connector import MT5Connector

connector = MT5Connector()
connector.connect()

# Download data from MT5
df = connector.get_historical_data(
    symbol="XAUUSD",
    timeframe="H1",
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31)
)

# Save for Python backtest
connector.save_historical_data(
    symbol="XAUUSD",
    timeframe="H1",
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31),
    output_path=Path("Backtest/data/XAUUSD_H1.csv")
)
```

### Option 2: Validate Data Match

```python
# Compare Python data with MT5
comparison = connector.compare_data_with_python(
    symbol="XAUUSD",
    timeframe="H1",
    python_data=your_dataframe,
    tolerance=0.0001  # 0.01% tolerance
)

if comparison['data_consistent']:
    print("✓ Data matches MT5")
else:
    print(f"⚠ Found {comparison['price_mismatches']} price mismatches")
```

## Timestamp Alignment

**MT5 Bar Times**:
- Bar timestamp = bar OPEN time
- Bar closes at next bar's open time

**Example (H1 timeframe)**:
```
Bar timestamp: 2024-01-15 09:00:00
Bar covers:    09:00:00 to 09:59:59
Signal executes at: 09:00:00 (bar open)
```

**Python Strategy**:
- Generate signals at bar close
- Set signal timestamp to NEXT bar's open time
- This ensures MT5 executes on correct bar

```python
# In strategy
current_bar_time = timestamp  # e.g., 09:00:00
# Signal executes at next bar
signal_time = current_bar_time + timedelta(hours=1)  # 10:00:00
```

## Expected Differences

### Normal Discrepancies

1. **Slippage** (5-10 pips):
   - MT5 models realistic slippage
   - Python uses simulated slippage

2. **Spread** (varies):
   - MT5 accounts for bid/ask spread
   - Python may use mid-price

3. **Partial Fills**:
   - MT5 may partially fill large orders
   - Python typically assumes full fills

4. **Order Rejections**:
   - MT5 validates margin requirements
   - Python may allow overleveraged positions

5. **Timing** (1-2 seconds):
   - MT5 simulates execution delay
   - Python is instantaneous

### Investigate If

1. **Execution Rate < 90%**:
   - Check timestamp alignment
   - Verify signal file format
   - Review EA logs for errors

2. **P&L Difference > 15%**:
   - Validate lot size conversion
   - Check for missed trades
   - Review commission settings

3. **Win Rate Difference > 5%**:
   - Compare entry/exit prices
   - Check stop loss execution
   - Validate trade matching

## Troubleshooting

### EA Won't Load Signal File

**Symptom**: "ERROR: Cannot open file"

**Solutions**:
1. Verify file is in `MQL5/Files/` directory
2. Check filename exactly matches EA parameter
3. Ensure CSV format is correct (no BOM, UTF-8)
4. Try shorter filename (no special characters)

### Signals Not Executing

**Symptom**: EA loads signals but no trades execute

**Solutions**:
1. Check timestamp alignment (use `align_timestamp_to_mt5()`)
2. Verify symbol matches (case-sensitive)
3. Review Journal tab for warnings
4. Check if signal times match backtest period

### Price Differences Too Large

**Symptom**: 20%+ P&L difference

**Solutions**:
1. Ensure data source is identical
2. Verify lot size conversion
3. Check commission settings match
4. Review for data gaps or missing bars

### Missing Trades

**Symptom**: MT5 has fewer trades than Python

**Solutions**:
1. Check margin requirements (MT5 may reject)
2. Verify all signals exported (check signal count)
3. Look for gaps in signal file (chronological order)
4. Review EA logs for rejected trades

## Best Practices

### 1. Development Workflow

```
Python Development (Fast iteration)
         ↓
Python Backtest (Quick validation)
         ↓
MT5 Validation (Realistic execution)
         ↓
Reconciliation (Compare results)
         ↓
Live Trading (Deploy if validated)
```

### 2. Signal File Management

- Use consistent naming: `BT_[DATE]_[SYMBOL]_[TF]_signals.csv`
- Keep signal files organized by backtest ID
- Archive after reconciliation
- Version control signal generation code

### 3. Validation Checklist

Before MT5 backtest:
- [ ] Data source validated
- [ ] Timestamps aligned
- [ ] Lot sizes converted
- [ ] Signal file validated (no errors)
- [ ] EA compiled successfully
- [ ] Test with small date range first

### 4. Performance Optimization

For large backtests:
- Use CSV format (faster parsing)
- Omit HOLD signals if possible
- Pre-validate signal file
- Use MT5 "Open prices only" model for quick tests

## API Reference

### Python Classes

#### SignalExporter

```python
from Backtest.signal_exporter import SignalExporter

exporter = SignalExporter(
    output_dir=Path("mt5_signals"),
    backtest_id="BT_001",
    symbol="XAUUSD",
    timeframe="H1"
)

# Add signal
exporter.add_signal(signal, stop_loss=1950.0, take_profit=1990.0)

# Export
csv_path = exporter.export_csv()
json_path = exporter.export_json()

# Validate
warnings = exporter.validate_signals()
```

#### MT5Connector

```python
from Backtest.mt5_connector import MT5Connector

with MT5Connector() as connector:
    # Get data
    df = connector.get_historical_data("XAUUSD", "H1", start, end)
    
    # Get symbol info
    info = connector.get_symbol_info("XAUUSD")
    lot_size = connector.get_lot_size("XAUUSD")
```

#### MT5Reconciliation

```python
from Backtest.mt5_reconciliation import MT5Reconciliation

reconciler = MT5Reconciliation()
reconciler.load_python_signals(signals_path)
reconciler.load_python_trades(trades_path)
reconciler.load_mt5_history("XAUUSD", start, end)

# Compare
reconciler.compare_signals_to_trades()
reconciler.compare_metrics(python_metrics, mt5_metrics)

# Report
reconciler.generate_report(output_path)
```

### MQL5 EA Parameters

```mql5
input string   SignalFile = "signals.csv";     // Signal filename
input double   RiskPercent = 1.0;              // Risk % per trade
input int      Slippage = 10;                  // Max slippage (points)
input bool     LogVerbose = true;              // Verbose logging
input int      MagicNumber = 20241018;         // Unique magic number
```

## References

- [MetaTrader5 Python API](https://www.mql5.com/en/docs/python_metatrader5)
- [MQL5 File Operations](https://www.mql5.com/en/docs/files)
- [MQL5 Trading Functions](https://www.mql5.com/en/docs/trading)
- [Strategy Tester Documentation](https://www.metatrader5.com/en/automated-trading/strategy-tester)

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review EA Journal tab in MT5
3. Validate signal file format
4. Compare with `example_mt5_integration.py`

## License

Part of AlgoAgent project - MIT License
