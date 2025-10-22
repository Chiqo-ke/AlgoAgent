# Signal Path Configuration - Quick Reference

**Status:** ✅ Configured and Verified  
**Date:** October 19, 2025

---

## 📍 Signal Location

**All signals are now saved to:**
```
C:\Users\nyaga\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\signals\
```

---

## 🔧 What Changed

### Python Code
- **File:** `Backtest/sim_broker.py`
- **Change:** Signals now export directly to MT5 Experts/signals folder
- **No action needed:** Automatic when you use `enable_mt5_export=True`

### MQL5 Code
- **File:** `Backtest/PythonSignalExecutor_Multi.mq5`
- **Change:** Added `SignalsFolder` parameter (default: `"Experts/signals/"`)
- **Action:** Recompile EA in MetaEditor

---

## ✅ Verification Results

```
✓ Directory exists
✓ Directory is writable
✓ MT5 Terminal found
✓ Configuration updated
```

---

## 🚀 Quick Start

### 1. Python - Generate Signals

```python
from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig

config = BacktestConfig()
broker = SimBroker(
    config,
    enable_mt5_export=True,
    mt5_symbol="XAUUSD",
    mt5_timeframe="H1"
)

# Run your strategy...
# Signals automatically saved to Experts/signals/
```

### 2. MQL5 - Load Signals

**In Strategy Tester:**
```
Expert: PythonSignalExecutor_Multi
Inputs:
  SignalsFolder = "Experts/signals/"
  FolderPattern = "BT_*.csv"
  ProcessAllFiles = true
```

**That's it!** No manual file copying needed.

---

## 📋 File Locations

| Item | Location |
|------|----------|
| **Signal Files** | `Terminal/.../MQL5/Experts/signals/*.csv` |
| **Python Code** | `c:\Users\nyaga\Documents\AlgoAgent\Backtest\sim_broker.py` |
| **MQL5 EA** | `Terminal/.../MQL5/Experts\PythonSignalExecutor_Multi.mq5` |
| **Verification Script** | `c:\Users\nyaga\Documents\AlgoAgent\Backtest\verify_signals_setup.py` |

---

## 🔍 Test Setup

**Run verification script:**
```powershell
python "c:\Users\nyaga\Documents\AlgoAgent\Backtest\verify_signals_setup.py"
```

**Expected output:**
```
✓ Directory exists
✓ Directory is writable
✓ MT5 Terminal found
✓ Setup Verification PASSED
```

---

## 📚 Documentation

- **Detailed Guide:** `SIGNAL_PATH_UPDATE.md`
- **Multi-File Usage:** `MULTI_FILE_GUIDE.md`
- **Complete Setup:** `MQL5_SETUP_GUIDE.md`

---

## ⚡ Benefits

1. **No Manual Steps** - Python writes directly to MT5 folder
2. **Immediate Access** - MQL5 reads from same location
3. **Better Organization** - Dedicated signals folder
4. **Multiple Files** - Scan entire folder with pattern matching

---

**Configuration complete! Ready to backtest.** 🎯
