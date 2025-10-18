# MQL5 Setup Guide - Step by Step

**Complete setup procedure for executing Python backtest signals in MetaTrader 5**

**Version:** 1.0.0  
**Last Updated:** October 19, 2025  
**Status:** Production Ready ✅

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Step 1: Run Python Backtest with Signal Export](#step-1-run-python-backtest-with-signal-export)
4. [Step 2: Locate and Verify Signal Files](#step-2-locate-and-verify-signal-files)
5. [Step 3: Install Expert Advisor in MT5](#step-3-install-expert-advisor-in-mt5)
6. [Step 4: Copy Signal File to MT5](#step-4-copy-signal-file-to-mt5)
7. [Step 5: Configure Expert Advisor](#step-5-configure-expert-advisor)
8. [Step 6: Run Strategy Tester](#step-6-run-strategy-tester)
9. [Step 7: Compare Results (Reconciliation)](#step-7-compare-results-reconciliation)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

This guide walks you through the complete process of:
1. Running a Python backtest with your updated `SimBroker`
2. Exporting signals to MT5-compatible format
3. Setting up MetaTrader 5 to execute those signals
4. Validating that MT5 execution matches Python results

**Data Flow:**
```
Python Strategy
    ↓
SimBroker (with enable_mt5_export=True)
    ↓
CSV Signal File (XAUUSD_signals.csv)
    ↓
MT5 Strategy Tester
    ↓
MT5 Execution Results
    ↓
Reconciliation Report
```

---

## 🔧 Prerequisites

### Required Software
- ✅ **Python 3.8+** with packages:
  - `pandas`
  - `numpy`
  - `MetaTrader5` (optional, for reconciliation)
  
- ✅ **MetaTrader 5** Terminal (Desktop application)
  - Download: https://www.metatrader5.com/en/download

### Required Files
- ✅ `sim_broker.py` - Your updated backtesting engine
- ✅ `signal_exporter.py` - Signal export module
- ✅ `PythonSignalExecutor.mq5` - MT5 Expert Advisor
- ✅ Your strategy file (e.g., `my_strategy.py`)

### What You Need to Know
- 📝 Your trading symbol in MT5 format (e.g., `XAUUSD`, `EURUSD`)
- 📝 Your timeframe (e.g., `H1`, `H4`, `D1`)
- 📝 Date range for backtesting

---

## Step 1: Run Python Backtest with Signal Export

### 1.1 Update Your Strategy Code

Add MT5 export to your existing strategy:

```python
from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig
from datetime import datetime

# Configure backtest
config = BacktestConfig(
    start_cash=10000,
    commission=0.0,
    slippage=0.0
)

# Initialize broker WITH MT5 EXPORT ENABLED
broker = SimBroker(
    config=config,
    enable_mt5_export=True,        # ← ENABLE THIS
    mt5_symbol="XAUUSD",           # ← Your MT5 symbol
    mt5_timeframe="H1"             # ← Your timeframe
)

# Your strategy logic here
# ... (submit signals as usual)

# After backtest completes, export signals
output_path = broker.export_mt5_signals(format="csv")  # or "json"
print(f"✅ Signals exported to: {output_path}")

# Get export summary
summary = broker.get_mt5_export_summary()
print(f"Total signals: {summary['total_signals']}")
print(f"BUY signals: {summary['signal_types']['BUY']}")
print(f"SELL signals: {summary['signal_types']['SELL']}")
print(f"File location: {summary['file_path']}")
```

### 1.2 Run Your Backtest

```powershell
# Navigate to your project directory
cd C:\Users\nyaga\Documents\AlgoAgent

# Run your strategy
python Backtest\my_strategy.py
```

### 1.3 What Gets Created

The backtest will create a signal file:

**File naming pattern:**
```
BT_YYYYMMDD_HHMMSS_SYMBOL_TIMEFRAME_signals.csv
```

**Example:**
```
BT_20251019_143052_XAUUSD_H1_signals.csv
```

**Location:**
```
AlgoAgent/
└── Backtest/
    └── mt5_signals/
        └── BT_20251019_143052_XAUUSD_H1_signals.csv  ← Your file here
```

---

## Step 2: Locate and Verify Signal Files

### 2.1 Find Your Signal File

```powershell
# Check the mt5_signals directory
dir Backtest\mt5_signals\
```

You should see your CSV file listed.

### 2.2 Verify File Format

Open the CSV file in a text editor or Excel. It should look like this:

**CSV Structure:**
```csv
timestamp,symbol,signal,lot_size,stop_loss,take_profit,signal_id,metadata
2024-01-15T09:00:00+00:00,XAUUSD,BUY,0.10,1950.50,1980.00,sig-abc123,"{""strategy_id"":""ma_cross""}"
2024-01-15T13:00:00+00:00,XAUUSD,EXIT,0.00,0.00,0.00,sig-def456,"{""action"":""EXIT""}"
2024-01-15T17:00:00+00:00,XAUUSD,SELL,0.10,2020.00,1990.00,sig-ghi789,"{""strategy_id"":""ma_cross""}"
```

**Column Definitions:**

| Column | Description | Format | Example |
|--------|-------------|--------|---------|
| `timestamp` | Signal time (UTC) | ISO 8601 | `2024-01-15T09:00:00+00:00` |
| `symbol` | MT5 symbol name | String | `XAUUSD` |
| `signal` | Signal type | BUY/SELL/EXIT/HOLD | `BUY` |
| `lot_size` | Position size in lots | Float | `0.10` |
| `stop_loss` | Stop loss price (0=none) | Float | `1950.50` |
| `take_profit` | Take profit price (0=none) | Float | `1980.00` |
| `signal_id` | Unique identifier | String | `sig-abc123` |
| `metadata` | Additional info | JSON string | `{...}` |

### 2.3 Important Notes

**✅ Lot Size Conversion**
Your Python backtest uses shares/contracts, but MT5 uses lots. The conversion is automatic:

| Symbol | Shares per Lot | Example |
|--------|---------------|---------|
| XAUUSD | 100 oz | 100 oz → 1.0 lot |
| XAGUSD | 5,000 oz | 5,000 oz → 1.0 lot |
| EURUSD | 100,000 units | 100,000 → 1.0 lot |
| BTCUSD | 1 BTC | 1 BTC → 1.0 lot |

**✅ Timestamp Format**
- Always UTC timezone
- ISO 8601 format: `YYYY-MM-DDTHH:MM:SS+00:00`
- MT5 will parse this automatically

---

## Step 3: Install Expert Advisor in MT5

### 3.1 Locate the EA File

The Expert Advisor is here:
```
AlgoAgent/
└── Backtest/
    └── PythonSignalExecutor.mq5  ← This file
```

### 3.2 Copy EA to MT5 Directory

**Windows Path:**
```
C:\Users\[YourUsername]\AppData\Roaming\MetaQuotes\Terminal\[TerminalID]\MQL5\Experts\
```

**Steps:**
1. Open MT5
2. Click **File → Open Data Folder**
3. Navigate to `MQL5\Experts\`
4. Copy `PythonSignalExecutor.mq5` to this folder

### 3.3 Compile the EA

1. In MT5, press **F4** to open MetaEditor
2. In the **Navigator** panel, find **Experts → PythonSignalExecutor**
3. Double-click to open the file
4. Click **Compile** button (or press F7)
5. Check **Errors** tab - should show `0 error(s), 0 warning(s)`

**✅ Success:** You'll see `PythonSignalExecutor.ex5` created in the same folder

---

## Step 4: Copy Signal File to MT5

### 4.1 Locate MT5 Files Directory

**Windows Path:**
```
C:\Users\[YourUsername]\AppData\Roaming\MetaQuotes\Terminal\[TerminalID]\MQL5\Files\
```

**Quick Method:**
1. In MT5, press **F4** (MetaEditor)
2. Click **File → Open Data Folder**
3. Navigate to `MQL5\Files\`

### 4.2 Copy Your Signal File

Copy your CSV file from:
```
AlgoAgent\Backtest\mt5_signals\BT_20251019_143052_XAUUSD_H1_signals.csv
```

To:
```
C:\Users\[YourUsername]\AppData\Roaming\MetaQuotes\Terminal\[TerminalID]\MQL5\Files\
```

**📝 Note the filename** - you'll need it in the next step!

Example: `BT_20251019_143052_XAUUSD_H1_signals.csv`

---

## Step 5: Configure Expert Advisor

### 5.1 Open Strategy Tester

1. In MT5, press **Ctrl+R** (or View → Strategy Tester)
2. The Strategy Tester panel appears at the bottom

### 5.2 Configure Settings

**Settings Tab:**

| Setting | Value | Description |
|---------|-------|-------------|
| **Expert Advisor** | `PythonSignalExecutor` | Select from dropdown |
| **Symbol** | `XAUUSD` | Must match your signal file |
| **Period** | `H1` | Must match your signal file |
| **Date** | Custom range | Match your backtest dates |
| **Deposit** | `10000` | Match your Python config |
| **Leverage** | `1:100` | Standard or as needed |
| **Optimization** | Disabled | Not needed for validation |

**Example Configuration:**
```
Expert:     PythonSignalExecutor
Symbol:     XAUUSD
Period:     H1
Date From:  2024-01-01
Date To:    2024-03-31
Deposit:    10000 USD
```

### 5.3 Configure EA Input Parameters

Click **Expert properties** button, then **Inputs** tab:

| Parameter | Value | Description |
|-----------|-------|-------------|
| **SignalFile** | `BT_20251019_143052_XAUUSD_H1_signals.csv` | Your signal file name |
| **RiskPercent** | `0.0` | 0 = use signal lot size exactly |
| **Slippage** | `10` | Max slippage in points |
| **LogVerbose** | `true` | Enable detailed logging |
| **MagicNumber** | `20251019` | Unique identifier |

**⚠️ IMPORTANT:** 
- `SignalFile` must be **exact filename** (with .csv extension)
- `RiskPercent = 0.0` means use exact lot sizes from signal file
- Set `RiskPercent > 0` to override with risk-based sizing

### 5.4 Configure Testing Settings

**Testing Tab:**
- ✅ **Model:** Every tick (most accurate)
- ✅ **Optimization:** Disabled
- ✅ **Visual mode:** Optional (slower but shows execution)

---

## Step 6: Run Strategy Tester

### 6.1 Start the Test

Click **Start** button (or press **F5**)

### 6.2 Monitor Progress

**Backtest Tab** shows:
- Current progress (0-100%)
- Bars processed
- Current date/time

**Journal Tab** shows:
- EA initialization
- Signal file loading
- Signal processing logs

**Expected Journal Output:**
```
=== PythonSignalExecutor EA Starting ===
Signal File: BT_20251019_143052_XAUUSD_H1_signals.csv
Symbol: XAUUSD
Timeframe: H1
Successfully loaded 245 signals
Date range: 2024-01-01 00:00 to 2024-03-31 23:00

Processing signal at 2024-01-15 09:00:00
Signal: BUY
Lot Size: 0.10
Stop Loss: 1950.50
Take Profit: 1980.00
ID: sig-abc123

Opening LONG position: 0.10 lots at 1975.25
Position opened successfully, Ticket: 123456789

...

=== PythonSignalExecutor EA Stopped ===
Signals processed: 245 / 245
```

### 6.3 Review Results

**Results Tab** shows:
- Total Net Profit
- Balance curve
- Equity curve
- Drawdown
- Total trades
- Win rate
- Profit factor

**Graph Tab** shows:
- Visual balance/equity curves
- Drawdown graph

### 6.4 Export MT5 Results

1. **Right-click** on results
2. Select **Report → Save as HTML**
3. Save to: `AlgoAgent\Backtest\results\mt5_report.html`

**Also export detailed trades:**
1. Go to **Account History** tab
2. Right-click → **Report → Save as HTML**
3. Save to: `AlgoAgent\Backtest\results\mt5_trades.html`

---

## Step 7: Compare Results (Reconciliation)

### 7.1 Run Reconciliation Script

Use the MT5 reconciliation tool to compare Python vs MT5:

```python
from Backtest.mt5_reconciliation import MT5Reconciliation
from datetime import datetime

# Initialize reconciliation
reconcile = MT5Reconciliation(
    python_signal_file="Backtest/mt5_signals/BT_20251019_143052_XAUUSD_H1_signals.csv",
    python_trades_file="Backtest/results/trades.csv",
    python_metrics_file="Backtest/results/metrics.json"
)

# Compare results (requires MT5 connection)
report = reconcile.compare_all(
    symbol="XAUUSD",
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 3, 31),
    magic_number=20251019
)

# Generate report
reconcile.generate_report("Backtest/results/reconciliation_report.txt")
```

### 7.2 What Gets Compared

| Metric | Source 1 | Source 2 | Acceptable Difference |
|--------|----------|----------|----------------------|
| **Total Trades** | Python | MT5 | Must match exactly |
| **Net Profit** | Python | MT5 | ±2% (slippage/spreads) |
| **Win Rate** | Python | MT5 | ±1% |
| **Sharpe Ratio** | Python | MT5 | ±5% |
| **Max Drawdown** | Python | MT5 | ±3% |
| **Trade Timestamps** | Python | MT5 | Must match (±1 bar) |

### 7.3 Interpret Results

**✅ Perfect Match:**
```
Signal Comparison: 245/245 matched (100.0%)
Trade Count: Python=245, MT5=245 (Match!)
Net Profit: Python=$5,432.10, MT5=$5,401.25 (Diff: -0.57%)
Status: PASS ✓
```

**⚠️ Acceptable Variance:**
```
Signal Comparison: 245/245 matched (100.0%)
Trade Count: Python=245, MT5=243 (98.4% match)
Net Profit: Python=$5,432.10, MT5=$5,289.50 (Diff: -2.63%)
Status: PASS (within tolerance)
Reason: 2 trades not executed due to spread widening
```

**❌ Issue Found:**
```
Signal Comparison: 245/198 matched (80.8%)
Trade Count: Python=245, MT5=198
Status: FAIL ✗
Reason: Signal file may have wrong timestamp format
```

---

## 🔍 Troubleshooting

### Issue 1: EA Won't Load Signal File

**Error:**
```
ERROR: Failed to load signal file: BT_20251019_143052_XAUUSD_H1_signals.csv
```

**Solutions:**
- ✅ Verify file is in `MQL5\Files\` directory (not in subdirectory)
- ✅ Check filename is **exact** (case-sensitive on some systems)
- ✅ Ensure file has `.csv` extension
- ✅ Verify file is not open in Excel or another program
- ✅ Check file permissions (not read-only)

### Issue 2: No Signals Executed

**Symptoms:**
- EA loads successfully
- No trades opened
- Journal shows: "Processing signal..." but no execution

**Solutions:**
- ✅ Verify **symbol** in EA settings matches signal file (`XAUUSD`)
- ✅ Verify **timeframe** matches (`H1`)
- ✅ Check date range includes signal timestamps
- ✅ Ensure signal timestamps are in **UTC** format
- ✅ Verify lot sizes are valid (>= 0.01 for most brokers)

### Issue 3: Wrong Lot Sizes

**Symptoms:**
- Positions opened with incorrect sizes
- Risk too high or too low

**Solutions:**
- ✅ Check `RiskPercent` parameter (set to 0.0 to use signal sizes)
- ✅ Verify lot size conversion in signal file
- ✅ Check broker's minimum/maximum lot size
- ✅ Verify your Python strategy is using correct symbol

**Lot Size Check:**
```python
# In your Python code
from Backtest.signal_exporter import SignalExporter

exporter = SignalExporter(
    output_dir="Backtest/mt5_signals",
    backtest_id="test",
    symbol="XAUUSD",  # ← Must match MT5 symbol
    timeframe="H1"
)

# Check conversion
print(f"Shares per lot: {exporter.shares_per_lot}")
# XAUUSD should show: 100
```

### Issue 4: Timestamp Mismatch

**Symptoms:**
- Signals load but execute at wrong times
- Trades don't match Python backtest

**Solutions:**
- ✅ Verify timestamps in CSV are **UTC** (not local time)
- ✅ Check ISO 8601 format: `2024-01-15T09:00:00+00:00`
- ✅ Ensure MT5 timezone is configured correctly
- ✅ Verify broker's trading hours match your data

**Time Zone Check:**
```python
# In signal_exporter.py, timestamps are automatically converted to UTC
from datetime import timezone

timestamp_str = signal.timestamp.replace(tzinfo=timezone.utc).isoformat()
# Output: 2024-01-15T09:00:00+00:00
```

### Issue 5: Different Results Between Python and MT5

**Acceptable Differences:**
- ✅ Slippage (MT5 simulates realistic execution)
- ✅ Spreads (MT5 uses actual broker spreads)
- ✅ Partial fills (MT5 may not fill full size at market)

**Unacceptable Differences:**
- ❌ Missing trades (>5% difference)
- ❌ Wrong direction (BUY vs SELL)
- ❌ Large profit discrepancy (>10%)

**Investigation Steps:**
1. Check **Journal** tab for errors
2. Compare trade-by-trade (use HTML reports)
3. Verify symbol specifications (spread, lot size, etc.)
4. Check if broker has restrictions (hedging, FIFO, etc.)

### Issue 6: File Format Errors

**Error:**
```
ERROR: Invalid CSV format
```

**Solutions:**
- ✅ Verify CSV uses commas (`,`) as delimiter
- ✅ Check for header row: `timestamp,symbol,signal,lot_size,...`
- ✅ Ensure no extra spaces in headers
- ✅ Verify no blank lines in file
- ✅ Check for special characters in metadata JSON

**Manual CSV Validation:**
```powershell
# View first few lines
Get-Content Backtest\mt5_signals\BT_20251019_143052_XAUUSD_H1_signals.csv -Head 5
```

---

## 📊 Complete Workflow Example

Here's a complete end-to-end example:

### Python Strategy File: `test_mt5_strategy.py`

```python
import sys
from pathlib import Path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig
from Backtest.data_loader import DataLoader
from Backtest.canonical_schema import create_signal, OrderSide, OrderAction, OrderType
from datetime import datetime

def main():
    print("=== Starting MT5 Integration Test ===")
    
    # 1. Configure backtest
    config = BacktestConfig(
        start_cash=10000,
        commission=0.0,
        slippage=0.0
    )
    
    # 2. Initialize broker with MT5 export
    broker = SimBroker(
        config=config,
        enable_mt5_export=True,
        mt5_symbol="XAUUSD",
        mt5_timeframe="H1"
    )
    
    # 3. Load data
    loader = DataLoader()
    data = loader.load_csv("Backtest/data/XAUUSD_H1.csv")
    
    # 4. Simple strategy: Buy on first bar, exit on last bar
    timestamps = sorted(data.keys())
    
    # Entry signal
    entry_signal = create_signal(
        timestamp=timestamps[10],
        symbol="XAUUSD",
        side=OrderSide.BUY,
        action=OrderAction.ENTRY,
        order_type=OrderType.MARKET,
        size=100,  # 100 oz = 1.0 lot
        strategy_id="test_strategy"
    )
    broker.submit_signal(entry_signal.to_dict())
    broker.step_to(timestamps[10], {"XAUUSD": data[timestamps[10]]})
    
    # Exit signal
    exit_signal = create_signal(
        timestamp=timestamps[-10],
        symbol="XAUUSD",
        side=OrderSide.SELL,
        action=OrderAction.EXIT,
        order_type=OrderType.MARKET,
        size=0,
        strategy_id="test_strategy"
    )
    broker.submit_signal(exit_signal.to_dict())
    broker.step_to(timestamps[-10], {"XAUUSD": data[timestamps[-10]]})
    
    # 5. Export signals
    signal_file = broker.export_mt5_signals(format="csv")
    print(f"\n✅ Signals exported to: {signal_file}")
    
    # 6. Get summary
    summary = broker.get_mt5_export_summary()
    print(f"\nExport Summary:")
    print(f"  Total Signals: {summary['total_signals']}")
    print(f"  File: {summary['file_path']}")
    
    # 7. Export trades and metrics
    broker.export_trades("Backtest/results/test_trades.csv")
    metrics = broker.compute_metrics()
    print(f"\nPython Results:")
    print(f"  Net Profit: ${metrics['net_profit']:.2f}")
    print(f"  Total Trades: {metrics['total_trades']}")
    
    print("\n=== Next Steps ===")
    print("1. Copy signal file to MT5 Files directory")
    print(f"   From: {signal_file}")
    print("   To: C:\\Users\\[YourUsername]\\AppData\\Roaming\\MetaQuotes\\Terminal\\[ID]\\MQL5\\Files\\")
    print("2. Run MT5 Strategy Tester with PythonSignalExecutor EA")
    print("3. Compare results using mt5_reconciliation.py")

if __name__ == "__main__":
    main()
```

### Run the Test

```powershell
cd C:\Users\nyaga\Documents\AlgoAgent
python Backtest\test_mt5_strategy.py
```

### Expected Output

```
=== Starting MT5 Integration Test ===

✅ Signals exported to: Backtest\mt5_signals\BT_20251019_150530_XAUUSD_H1_signals.csv

Export Summary:
  Total Signals: 2
  File: Backtest\mt5_signals\BT_20251019_150530_XAUUSD_H1_signals.csv

Python Results:
  Net Profit: $127.50
  Total Trades: 1

=== Next Steps ===
1. Copy signal file to MT5 Files directory
   From: Backtest\mt5_signals\BT_20251019_150530_XAUUSD_H1_signals.csv
   To: C:\Users\[YourUsername]\AppData\Roaming\MetaQuotes\Terminal\[ID]\MQL5\Files\
2. Run MT5 Strategy Tester with PythonSignalExecutor EA
3. Compare results using mt5_reconciliation.py
```

---

## 📋 Quick Reference Checklist

### Before Running MT5 Test:

- [ ] Python backtest completed successfully
- [ ] Signal file exported to `mt5_signals/` directory
- [ ] Signal file format verified (CSV with correct columns)
- [ ] `PythonSignalExecutor.mq5` copied to MT5 Experts folder
- [ ] EA compiled successfully (no errors)
- [ ] Signal file copied to MT5 Files folder
- [ ] Signal filename noted (exact name with .csv)

### MT5 Configuration:

- [ ] Expert Advisor: `PythonSignalExecutor` selected
- [ ] Symbol matches signal file (e.g., `XAUUSD`)
- [ ] Timeframe matches signal file (e.g., `H1`)
- [ ] Date range includes all signal dates
- [ ] Input parameter `SignalFile` set to exact filename
- [ ] Input parameter `RiskPercent` set to `0.0` (use signal sizes)
- [ ] Testing model set to "Every tick"

### After MT5 Test:

- [ ] All signals loaded successfully (check Journal)
- [ ] Trades executed (check Results tab)
- [ ] Results exported to HTML
- [ ] Reconciliation script run
- [ ] Results match within acceptable tolerance

---

## 🎯 Summary

### What This Setup Does:

1. **Python Side:**
   - Your strategy runs normally with `SimBroker`
   - Signal export is enabled with `enable_mt5_export=True`
   - Signals automatically converted to MT5 format
   - CSV file created with lot sizes, timestamps, SL/TP

2. **MT5 Side:**
   - Expert Advisor reads CSV signal file
   - Signals executed in Strategy Tester
   - Realistic execution with spreads, slippage
   - Full MT5 reporting and analysis

3. **Validation:**
   - Compare Python vs MT5 results
   - Verify trade count, profit, timing
   - Identify execution differences
   - Ensure strategy works in live-like conditions

### Key Files:

| File | Location | Purpose |
|------|----------|---------|
| `sim_broker.py` | `Backtest/` | Main backtesting engine |
| `signal_exporter.py` | `Backtest/` | Export module |
| `PythonSignalExecutor.mq5` | `Backtest/` → `MT5/Experts/` | MT5 EA |
| `*_signals.csv` | `Backtest/mt5_signals/` → `MT5/Files/` | Signal data |
| `trades.csv` | `Backtest/results/` | Python results |
| `mt5_report.html` | `Backtest/results/` | MT5 results |

---

## 📚 Additional Resources

- **SimBroker API:** See `API_REFERENCE.md`
- **Complete MT5 Guide:** See `MT5_INTEGRATION_GUIDE.md`
- **Quick Reference:** See `MT5_QUICK_REFERENCE.md`
- **Example Code:** See `example_mt5_integration.py`
- **MQL5 Documentation:** https://www.mql5.com/en/docs
- **MT5 Python API:** https://www.mql5.com/en/docs/python_metatrader5

---

## ✅ Success Criteria

You'll know the setup is working when:

1. ✅ Python backtest creates signal CSV file
2. ✅ MT5 EA loads signal file without errors
3. ✅ MT5 executes all signals (or >95% with valid reasons for skips)
4. ✅ Trade count matches between Python and MT5
5. ✅ Profit difference is <5% (due to spreads/slippage)
6. ✅ Reconciliation report shows "PASS" status

---

**Questions? Issues?** Check `TROUBLESHOOTING` section above or review `MT5_INTEGRATION_GUIDE.md` for detailed explanations.

**Ready to go?** Start with Step 1! 🚀
