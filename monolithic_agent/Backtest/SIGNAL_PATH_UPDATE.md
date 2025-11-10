# Signal Path Configuration Update

**Date:** October 19, 2025  
**Version:** Python 1.1 / MQL5 3.1

---

## 🎯 Summary

Updated both Python signal export and MQL5 signal reading to use the MT5 **Experts/signals** directory instead of the default Files directory.

**New Signal Path:**
```
C:\Users\nyaga\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\signals\
```

---

## 📝 Changes Made

### 1. Python Code (sim_broker.py)

**Before:**
```python
if enable_mt5_export:
    output_dir = Path("Backtest/mt5_signals")
```

**After:**
```python
if enable_mt5_export:
    # Direct path to MT5 Experts/signals folder
    output_dir = Path(r"C:\Users\nyaga\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\signals")
```

**Location:** `c:\Users\nyaga\Documents\AlgoAgent\Backtest\sim_broker.py` (Line ~80)

---

### 2. MQL5 Code (PythonSignalExecutor_Multi.mq5)

**Added Input Parameter:**
```cpp
input string   SignalsFolder = "Experts/signals/";  // Subfolder within MQL5 folder
```

**Updated Functions:**

#### ScanAndLoadFiles()
```cpp
// Prepend signals folder path to pattern
string fullPattern = SignalsFolder + pattern;
Print("Scanning folder for files matching: ", fullPattern);
```

#### LoadSignalFile()
```cpp
// Prepend signals folder path
string fullPath = SignalsFolder + filename;

// Open file for reading
int fileHandle = FileOpen(fullPath, FILE_READ|FILE_CSV|FILE_ANSI, ',');
```

**Location:** `c:\Users\nyaga\Documents\AlgoAgent\Backtest\PythonSignalExecutor_Multi.mq5`

---

## 🔧 Why This Change?

### 1. **Better Organization**
- Separates signal files from general data files
- Dedicated folder for backtesting signals
- Easier to manage multiple strategies

### 2. **Direct Access**
- Python writes directly to MT5 folder
- No manual file copying needed
- Immediate availability in MT5

### 3. **Flexibility**
- Can change subfolder via input parameter
- Supports different organization schemes
- Easy to switch between directories

---

## 📁 Directory Structure

```
C:\Users\nyaga\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\
│
├── Experts\
│   ├── PythonSignalExecutor_Multi.mq5    ← Your EA
│   └── signals\                           ← NEW: Signal files here
│       ├── BT_20251019_100000_XAUUSD_H1_signals.csv
│       ├── BT_20251019_100500_EURUSD_H1_signals.csv
│       └── BT_20251019_101000_GBPUSD_M15_signals.csv
│
└── Files\                                 ← OLD: No longer used for signals
```

---

## 🚀 Usage

### Python - Generate Signals

```python
from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig

# Initialize with MT5 export enabled
config = BacktestConfig()
broker = SimBroker(
    config,
    enable_mt5_export=True,
    mt5_symbol="XAUUSD",
    mt5_timeframe="H1"
)

# Run your strategy
# ... trading logic ...

# Export signals (automatically saved to Experts/signals/)
signal_files = broker.export_mt5_signals(format="both")
print(f"Signals exported to: {signal_files}")
```

**Output:**
```
Signals exported to:
C:\Users\nyaga\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\signals\BT_20251019_143052_XAUUSD_H1_signals.csv
```

---

### MQL5 - Load Signals

**Option 1: Scan All Files**
```cpp
// Input Parameters
SignalsFolder = "Experts/signals/"    // Where signals are stored
FolderPattern = "BT_*.csv"            // Load all backtest files
ProcessAllFiles = true                 // Process all in sequence
```

**Option 2: Specific File**
```cpp
// Input Parameters
SignalsFolder = "Experts/signals/"
SpecificFile = "BT_20251019_143052_XAUUSD_H1_signals.csv"
```

**Option 3: Filtered Pattern**
```cpp
// Input Parameters
SignalsFolder = "Experts/signals/"
FolderPattern = "BT_*_XAUUSD_H1_*.csv"  // Only XAUUSD H1 files
ProcessAllFiles = true
```

---

## ✅ Verification

### 1. Check Directory Exists

**PowerShell:**
```powershell
Test-Path "C:\Users\nyaga\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\signals"
```

If `False`, create it:
```powershell
New-Item -ItemType Directory -Path "C:\Users\nyaga\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\signals"
```

### 2. Python Export Test

```python
# Quick test script
from pathlib import Path
from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig

config = BacktestConfig()
broker = SimBroker(config, enable_mt5_export=True, mt5_symbol="XAUUSD", mt5_timeframe="H1")

# Check if directory exists
output_dir = Path(r"C:\Users\nyaga\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\signals")
print(f"Directory exists: {output_dir.exists()}")
print(f"Directory path: {output_dir}")
```

### 3. MQL5 Load Test

In MT5 Strategy Tester:
1. Attach **PythonSignalExecutor_Multi** to chart
2. Check **Journal** for startup messages:
   ```
   Signals Folder: Experts/signals/
   Scanning folder for files matching: Experts/signals/BT_*.csv
   Found 3 file(s)
   ```
3. Verify files loaded successfully

---

## 🔍 Troubleshooting

### Issue 1: Directory Not Found

**Error:**
```
ERROR: No files found matching pattern: Experts/signals/BT_*.csv
Make sure signals are in: Terminal\Common\Files\Experts/signals/
```

**Solution:**
1. Verify directory exists:
   ```powershell
   ls "C:\Users\nyaga\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\signals"
   ```
2. Create if missing:
   ```powershell
   mkdir "C:\Users\nyaga\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\signals"
   ```

### Issue 2: Python Permission Error

**Error:**
```python
PermissionError: [WinError 5] Access is denied
```

**Solution:**
Run Python script as administrator or check folder permissions.

### Issue 3: Wrong Terminal ID

**Error:**
Files saved but MT5 can't find them.

**Solution:**
Verify your Terminal ID:
1. In MT5, go to **File → Open Data Folder**
2. Check the path - look for the Terminal ID (long hex string)
3. Update the path in `sim_broker.py` if different

**Example:**
```python
# Your actual Terminal ID might differ
output_dir = Path(r"C:\Users\nyaga\AppData\Roaming\MetaQuotes\Terminal\YOUR_TERMINAL_ID\MQL5\Experts\signals")
```

### Issue 4: Files in Wrong Location

If you previously saved signals to `Backtest/mt5_signals/`:

**Move Files:**
```powershell
# Source
$source = "c:\Users\nyaga\Documents\AlgoAgent\Backtest\mt5_signals\*.csv"

# Destination
$dest = "C:\Users\nyaga\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\signals\"

# Copy
Copy-Item $source $dest -Verbose
```

---

## 📊 Benefits

| Aspect | Before | After |
|--------|--------|-------|
| **Signal Location** | `Backtest/mt5_signals/` | `Terminal/.../MQL5/Experts/signals/` |
| **Manual Copy** | ✗ Required | ✓ Not needed |
| **File Access** | Separate step | Direct |
| **Organization** | Mixed with data | Dedicated folder |
| **Workflow** | Generate → Copy → Test | Generate → Test |
| **Strategy Isolation** | Shared directory | Per-strategy folders possible |

---

## 🎯 Next Steps

### 1. Update Existing Scripts

If you have existing backtesting scripts, they'll automatically use the new path after updating `sim_broker.py`.

### 2. Clean Old Files (Optional)

Old signal files in `Backtest/mt5_signals/` can be deleted or archived:
```powershell
# Archive old files
$archive = "c:\Users\nyaga\Documents\AlgoAgent\Backtest\mt5_signals_archive"
mkdir $archive
Move-Item "c:\Users\nyaga\Documents\AlgoAgent\Backtest\mt5_signals\*.csv" $archive
```

### 3. Test End-to-End

1. Run Python backtest with MT5 export
2. Verify CSV created in `Experts/signals/`
3. Run MQL5 EA in Strategy Tester
4. Compare Python vs MT5 results

---

## 🔗 Related Files

- **Python:** `Backtest/sim_broker.py`
- **MQL5:** `Backtest/PythonSignalExecutor_Multi.mq5`
- **Documentation:** 
  - `MULTI_FILE_GUIDE.md` - Multi-file usage guide
  - `MQL5_SETUP_GUIDE.md` - Complete setup instructions
  - `MQL5_CODE_SPECIFICATION.md` - Technical specification

---

## 📝 Configuration Reference

### Python Configuration

```python
# sim_broker.py (Line ~80)
output_dir = Path(r"C:\Users\nyaga\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\signals")
```

**To Customize:**
- Change path to different MT5 terminal
- Use environment variable for portability
- Support multiple terminals

**Example - Environment Variable:**
```python
import os
terminal_id = os.getenv("MT5_TERMINAL_ID", "D0E8209F77C8CF37AD8BF550E51FF075")
output_dir = Path(rf"C:\Users\nyaga\AppData\Roaming\MetaQuotes\Terminal\{terminal_id}\MQL5\Experts\signals")
```

### MQL5 Configuration

```cpp
// PythonSignalExecutor_Multi.mq5 (Line ~17)
input string SignalsFolder = "Experts/signals/";
```

**To Customize:**
- Change to different subfolder: `"MySignals/"`
- Use root MQL5 folder: `""`
- Organize by strategy: `"Experts/signals/Strategy1/"`

---

## ✨ Summary

**Simple workflow now:**

1. **Python** → Export signals directly to MT5 Experts/signals
2. **MQL5** → Scan Experts/signals and load all matching files
3. **No manual steps** between signal generation and backtesting

**Perfect for:**
- ✅ Rapid strategy iteration
- ✅ Multi-file backtesting
- ✅ Walk-forward analysis
- ✅ Portfolio testing
- ✅ Automated workflows

---

**Updated: October 19, 2025**  
**Status: Ready for Production** ✅
