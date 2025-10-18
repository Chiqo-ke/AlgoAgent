# MT5 Integration Quick Reference

## 5-Minute Setup

### 1. Enable Export (Python)
```python
broker = SimBroker(
    config=config,
    enable_mt5_export=True,
    mt5_symbol="XAUUSD",
    mt5_timeframe="H1"
)

# After backtest
broker.export_mt5_signals(format="both")
```

### 2. Copy Files
```
Signal CSV → C:\Users\[User]\AppData\Roaming\MetaQuotes\Terminal\[ID]\MQL5\Files\
EA File    → C:\Users\[User]\AppData\Roaming\MetaQuotes\Terminal\[ID]\MQL5\Experts\
```

### 3. MT5 Strategy Tester
- **EA**: PythonSignalExecutor
- **Symbol**: XAUUSD
- **Period**: H1
- **Model**: Every tick based on real ticks
- **SignalFile**: your_signal_file.csv

### 4. Run & Compare
Monitor Journal tab → Review Report → Compare with Python results

## Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| "Cannot open file" | Verify file in MQL5/Files/ directory |
| No trades execute | Check timestamp alignment |
| Wrong lot size | Verify conversion: 100 oz = 1.0 lot (XAUUSD) |
| P&L differs 5-10% | Normal (slippage + spread) |
| P&L differs >20% | Check data source consistency |

## Lot Size Conversions

| Symbol | Contract Size | Python → MT5 |
|--------|---------------|--------------|
| XAUUSD | 100 oz/lot | 100 → 1.00 lot |
| XAGUSD | 5000 oz/lot | 5000 → 1.00 lot |
| EURUSD | 100k/lot | 100000 → 1.00 lot |
| BTCUSD | 1 BTC/lot | 1 → 1.00 lot |

## Signal Types

| Signal | Action |
|--------|--------|
| BUY | Open long position |
| SELL | Open short position |
| EXIT | Close current position |
| HOLD | No action (can omit) |

## File Formats

### CSV (Recommended)
```csv
Timestamp,Symbol,Signal,LotSize,StopLoss,TakeProfit,SignalID,Metadata
2024-01-15T09:00:00+00:00,XAUUSD,BUY,0.10,1950.00,1990.00,SIG-001,{}
```

### JSON (Richer)
```json
{
  "backtest_id": "BT_001",
  "symbol": "XAUUSD",
  "timeframe": "H1",
  "signals": [...]
}
```

## Expected Differences

✓ **Normal (Accept)**
- P&L differs by 5-15% (more realistic in MT5)
- Win rate differs by 2-5%
- 1-2 missed trades due to margin

⚠ **Investigate**
- Execution rate < 90%
- P&L differs > 20%
- Win rate differs > 10%
- Many missed trades

## Quick Commands

### Python
```python
# Export signals
from Backtest.sim_broker import SimBroker

broker = SimBroker(enable_mt5_export=True)
# ... run backtest ...
broker.export_mt5_signals()

# Validate data
from Backtest.mt5_connector import MT5Connector

connector = MT5Connector()
connector.connect()
info = connector.get_symbol_info("XAUUSD")
connector.disconnect()

# Reconcile
from Backtest.mt5_reconciliation import MT5Reconciliation

reconciler = MT5Reconciliation()
reconciler.load_python_signals(signals_path)
reconciler.load_python_trades(trades_path)
reconciler.compare_metrics(python_metrics, mt5_metrics)
```

### MQL5 EA Settings
```
SignalFile    = "BT_20241018_XAUUSD_H1_signals.csv"
RiskPercent   = 0              // Use signal lot sizes
Slippage      = 10             // Points
LogVerbose    = true           // Enable logging
MagicNumber   = 20241018       // Unique ID
```

## Validation Checklist

Before MT5 Backtest:
- [ ] Signal file exists in MQL5/Files/
- [ ] EA compiled without errors
- [ ] Symbol and timeframe match
- [ ] Date range matches Python backtest
- [ ] Data source is consistent

After MT5 Backtest:
- [ ] Check execution rate (aim for >95%)
- [ ] Compare total trades
- [ ] Review P&L difference (5-15% normal)
- [ ] Check max drawdown
- [ ] Investigate any anomalies

## Key Functions

### SignalExporter
```python
exporter = SignalExporter(output_dir, backtest_id, symbol, timeframe)
exporter.add_signal(signal, stop_loss, take_profit)
exporter.export_csv()
exporter.validate_signals()
```

### MT5Connector
```python
connector = MT5Connector()
connector.connect()
df = connector.get_historical_data(symbol, timeframe, start, end)
info = connector.get_symbol_info(symbol)
connector.disconnect()
```

### SimBroker (Extended)
```python
broker = SimBroker(
    config=config,
    enable_mt5_export=True,
    mt5_symbol="XAUUSD",
    mt5_timeframe="H1"
)
broker.export_mt5_signals(format="both")
summary = broker.get_mt5_export_summary()
```

## Troubleshooting Flow

```
Issue?
  │
  ├─ Signals not loading?
  │    → Check file path
  │    → Check filename in EA settings
  │    → Verify CSV format
  │
  ├─ No trades executing?
  │    → Check Journal tab for errors
  │    → Verify timestamp format
  │    → Check date range overlap
  │
  ├─ Wrong lot sizes?
  │    → Check LOT_SIZE_CONVERSIONS
  │    → Verify symbol contract size
  │    → Test with fixed lot size
  │
  └─ Results don't match?
       → Check data source consistency
       → Verify commission settings
       → Review slippage model
       → Compare trade-by-trade
```

## Performance Tips

1. **Fast Iteration**: Test with 1-week period first
2. **Model Selection**: "Open prices only" for quick tests
3. **Signal Optimization**: Omit HOLD signals to reduce file size
4. **Data Management**: Use same data source for both systems
5. **Logging**: Enable verbose mode during development

## Resources

- Full Guide: `MT5_INTEGRATION_GUIDE.md`
- Example: `example_mt5_integration.py`
- EA Source: `PythonSignalExecutor.mq5`
- MT5 Python API: https://www.mql5.com/en/docs/python_metatrader5

## Support Workflow

1. Check this quick reference
2. Review full integration guide
3. Run example script
4. Check EA Journal logs
5. Validate signal file format
6. Compare with working example

---

**Remember**: MT5 results will differ from Python (more realistic). Expect 5-15% P&L difference due to slippage, spread, and execution constraints. This is a feature, not a bug!
