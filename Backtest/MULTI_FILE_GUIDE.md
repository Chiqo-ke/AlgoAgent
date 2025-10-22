# PythonSignalExecutor Multi-File Version - Guide

**Process Multiple CSV Signal Files in One Backtest**

**File:** `PythonSignalExecutor_Multi.mq5`  
**Version:** 3.0  
**Purpose:** Execute signals from multiple Python backtest CSV files in sequence

---

## 🎯 What's New

### Multi-File Processing

Instead of loading a single CSV file:
```mql5
// OLD (v1.0, v2.0)
input string SignalFile = "BT_20241018_120000_XAUUSD_H1_signals.csv";
```

Now you can process entire folders:
```mql5
// NEW (v3.0)
input string FolderPattern = "BT_*.csv";          // Process all files matching pattern
input string SpecificFile = "";                    // Or specify single file
input bool   ProcessAllFiles = true;               // Process all or stop after first
input bool   SortByDate = true;                    // Sort chronologically
```

---

## 📋 Key Features

### 1. **Folder Scanning**
- Automatically finds all CSV files matching pattern
- Supports wildcards: `BT_*.csv`, `XAUUSD_*.csv`, `*_H1_*.csv`
- Lists all found files during initialization

### 2. **Chronological Processing**
- Extracts dates from filenames
- Sorts files by date (optional)
- Processes signals in time sequence

### 3. **Multi-File Statistics**
- Tracks signals per file
- Cumulative performance across all files
- File transition logging

### 4. **Equity Management**
- Option to reset equity between files
- Continuous equity across files
- Initial deposit tracking

### 5. **File Source Tracking**
- Each signal tagged with source filename
- File transition detection
- Per-file progress tracking

---

## 🔧 Input Parameters

### File Settings

| Parameter | Default | Description |
|-----------|---------|-------------|
| `FolderPattern` | `"BT_*.csv"` | Pattern to match files (wildcards supported) |
| `SpecificFile` | `""` | Leave empty for folder scan, or specify single file |
| `ProcessAllFiles` | `true` | Process all matching files vs. first only |
| `SortByDate` | `true` | Sort files chronologically |

### Risk Management

| Parameter | Default | Description |
|-----------|---------|-------------|
| `RiskPercent` | `0.0` | Risk % per trade (0 = use signal lot size) |
| `MaxLotSize` | `10.0` | Maximum lot size limit |
| `ResetEquityBetweenFiles` | `false` | Reset to initial deposit between files |

### Trading Settings

| Parameter | Default | Description |
|-----------|---------|-------------|
| `Slippage` | `10` | Max slippage in points |
| `MagicNumber` | `20251019` | Unique trade identifier |
| `CloseOppositeFirst` | `true` | Close opposite before opening new |

### Logging

| Parameter | Default | Description |
|-----------|---------|-------------|
| `LogVerbose` | `true` | Detailed logging |
| `LogSignalDetails` | `false` | Per-signal details (can be very verbose) |
| `LogFileList` | `true` | Log list of files found |

---

## 📁 Use Cases

### Use Case 1: Multiple Strategies on Same Symbol

**Scenario:** Test 3 different strategies on XAUUSD H1

**Files:**
```
MQL5/Files/
├── BT_20251019_100000_XAUUSD_H1_ma_cross_signals.csv
├── BT_20251019_100500_XAUUSD_H1_rsi_strategy_signals.csv
└── BT_20251019_101000_XAUUSD_H1_breakout_signals.csv
```

**Configuration:**
```mql5
FolderPattern = "BT_*_XAUUSD_H1_*.csv"
ProcessAllFiles = true
SortByDate = true
ResetEquityBetweenFiles = false  // Continuous equity
```

**Result:** All three strategies executed in sequence on same equity curve

---

### Use Case 2: Same Strategy, Different Time Periods

**Scenario:** Test strategy across Q1, Q2, Q3, Q4

**Files:**
```
MQL5/Files/
├── BT_20251019_Q1_2024_signals.csv
├── BT_20251019_Q2_2024_signals.csv
├── BT_20251019_Q3_2024_signals.csv
└── BT_20251019_Q4_2024_signals.csv
```

**Configuration:**
```mql5
FolderPattern = "BT_*_Q*_2024_signals.csv"
ProcessAllFiles = true
SortByDate = true
ResetEquityBetweenFiles = true  // Independent equity per quarter
```

**Result:** Each quarter tested with fresh equity, cumulative statistics

---

### Use Case 3: Walk-Forward Analysis

**Scenario:** Monthly backtests for walk-forward validation

**Files:**
```
MQL5/Files/
├── BT_20250101_XAUUSD_H1_signals.csv  (Jan)
├── BT_20250201_XAUUSD_H1_signals.csv  (Feb)
├── BT_20250301_XAUUSD_H1_signals.csv  (Mar)
└── ... (more months)
```

**Configuration:**
```mql5
FolderPattern = "BT_2025*_XAUUSD_H1_signals.csv"
ProcessAllFiles = true
SortByDate = true
ResetEquityBetweenFiles = false  // Continuous for walk-forward
```

**Result:** Full year tested with proper chronological order

---

### Use Case 4: Multiple Symbols (Advanced)

**Scenario:** Portfolio backtest across multiple symbols

**Files:**
```
MQL5/Files/
├── BT_20251019_XAUUSD_H1_signals.csv
├── BT_20251019_EURUSD_H1_signals.csv
├── BT_20251019_GBPUSD_H1_signals.csv
└── BT_20251019_BTCUSD_H1_signals.csv
```

**Note:** Requires running EA on each symbol separately, or custom multi-symbol logic

---

## 🔍 File Naming Convention

### Standard Format
```
BT_YYYYMMDD_HHMMSS_SYMBOL_TIMEFRAME_signals.csv
```

**Examples:**
- `BT_20251019_143052_XAUUSD_H1_signals.csv`
- `BT_20250115_090000_EURUSD_M15_signals.csv`
- `BT_20241231_235959_BTCUSD_D1_signals.csv`

### Date Extraction

The EA extracts date from filename for sorting:
```mql5
// Pattern: BT_YYYYMMDD_HHMMSS
BT_20251019_143052_... → 2025.10.19 14:30:52
```

**Custom Naming:** If your files don't follow this pattern:
- Files will still be processed
- Sorting may not work correctly
- Set `SortByDate = false`

---

## 📊 Output Logging

### Initialization
```
================================================================
===   PythonSignalExecutor Multi-File EA v3.0 Starting      ===
================================================================
Folder Pattern: BT_*.csv
Process All Files: Yes
Symbol: XAUUSD
Timeframe: H1
================================================================
Scanning folder for files matching: BT_*.csv
Found file: BT_20251019_100000_XAUUSD_H1_signals.csv
Found file: BT_20251019_100500_XAUUSD_H1_signals.csv
Found file: BT_20251019_101000_XAUUSD_H1_signals.csv
Found 3 file(s)
Files sorted by date

--- Loading file 1/3: BT_20251019_100000_XAUUSD_H1_signals.csv ---
Loaded 245 signals from BT_20251019_100000_XAUUSD_H1_signals.csv

--- Loading file 2/3: BT_20251019_100500_XAUUSD_H1_signals.csv ---
Loaded 198 signals from BT_20251019_100500_XAUUSD_H1_signals.csv

--- Loading file 3/3: BT_20251019_101000_XAUUSD_H1_signals.csv ---
Loaded 312 signals from BT_20251019_101000_XAUUSD_H1_signals.csv

================================================================
Successfully loaded 3 file(s) with 755 total signals
Date range: 2024-01-01 00:00 to 2024-12-31 23:00
Signal types: BUY=380 SELL=350 EXIT=25 HOLD=0
================================================================
```

### File Transitions
```
--- Transitioned to file: BT_20251019_100500_XAUUSD_H1_signals.csv ---
```

### Shutdown
```
================================================================
===   PythonSignalExecutor Multi-File EA Stopped            ===
================================================================
Files processed: 3 / 3
Signals processed: 755 / 755
Total trades executed: 730
Signals skipped: 0

--- Performance Summary ---
Initial Deposit: 10000.00
Final Balance: 14532.75
Net Profit: 4532.75
Return: 45.33%
================================================================
```

---

## 🎯 Pattern Matching Examples

### Match All Backtest Files
```mql5
FolderPattern = "BT_*.csv"
```

### Match Specific Symbol
```mql5
FolderPattern = "BT_*_XAUUSD_*.csv"
```

### Match Specific Timeframe
```mql5
FolderPattern = "BT_*_H1_*.csv"
```

### Match Date Range
```mql5
FolderPattern = "BT_202501*_*.csv"  // January 2025
```

### Match Strategy Name
```mql5
FolderPattern = "BT_*_ma_cross_*.csv"
```

### Complex Pattern
```mql5
FolderPattern = "BT_202501*_XAUUSD_H1_*.csv"  // XAUUSD H1 in January 2025
```

---

## ⚙️ Configuration Scenarios

### Scenario A: Continuous Equity (Default)
```mql5
ProcessAllFiles = true
ResetEquityBetweenFiles = false
```
**Effect:** All files processed with continuous equity curve  
**Use For:** Walk-forward, portfolio testing, multi-period analysis

### Scenario B: Independent Tests
```mql5
ProcessAllFiles = true
ResetEquityBetweenFiles = true
```
**Effect:** Each file starts with initial deposit  
**Use For:** Comparing strategies, quarterly analysis

### Scenario C: Single File Only
```mql5
SpecificFile = "BT_20251019_143052_XAUUSD_H1_signals.csv"
```
**Effect:** Only specified file processed  
**Use For:** Testing specific strategy

### Scenario D: First Match Only
```mql5
FolderPattern = "BT_*.csv"
ProcessAllFiles = false
```
**Effect:** Only first matching file processed  
**Use For:** Quick testing

---

## 🚀 Installation & Usage

### 1. Generate Multiple Signal Files (Python)

```python
# Generate signals for Q1
broker1 = SimBroker(config, enable_mt5_export=True, 
                    mt5_symbol="XAUUSD", mt5_timeframe="H1")
# ... run backtest ...
broker1.export_mt5_signals(format="csv")  # Creates BT_..._Q1_signals.csv

# Generate signals for Q2
broker2 = SimBroker(config, enable_mt5_export=True,
                    mt5_symbol="XAUUSD", mt5_timeframe="H1")
# ... run backtest ...
broker2.export_mt5_signals(format="csv")  # Creates BT_..._Q2_signals.csv

# etc.
```

### 2. Copy All Files to MT5

```
Copy all CSV files to:
C:\Users\[User]\AppData\Roaming\MetaQuotes\Terminal\[ID]\MQL5\Files\
```

### 3. Compile EA

```
1. Copy PythonSignalExecutor_Multi.mq5 to MT5 Experts folder
2. Open in MetaEditor (F4)
3. Compile (F7)
4. Verify: 0 errors, 0 warnings
```

### 4. Configure Strategy Tester

```
Expert: PythonSignalExecutor_Multi
Symbol: XAUUSD (or your symbol)
Period: H1 (or your timeframe)
Date Range: Cover all your signal files

Inputs:
  FolderPattern: "BT_*.csv" (or your pattern)
  ProcessAllFiles: true
  SortByDate: true
```

### 5. Run and Monitor

- Press F5 to start
- Check Journal for file loading
- Watch for file transitions
- Review cumulative results

---

## ✅ Advantages

| Feature | Single File (v2.0) | Multi-File (v3.0) |
|---------|-------------------|-------------------|
| **File Loading** | Manual | Automatic scan |
| **Multiple Strategies** | Run separately | Combined in one test |
| **Time Periods** | One period | Multiple periods |
| **Statistics** | Per file | Cumulative |
| **Workflow** | Multiple runs | Single run |
| **Comparison** | Manual | Automatic |
| **Walk-Forward** | Manual process | Automatic |
| **Portfolio Testing** | Not supported | Supported |

---

## 🎓 Best Practices

### 1. File Organization
```
MQL5/Files/
├── strategies/
│   ├── BT_*_ma_cross_*.csv
│   ├── BT_*_rsi_*.csv
│   └── BT_*_breakout_*.csv
└── periods/
    ├── BT_*_Q1_*.csv
    ├── BT_*_Q2_*.csv
    └── BT_*_Q3_*.csv
```

### 2. Naming Consistency
- Use consistent date format: `YYYYMMDD_HHMMSS`
- Include symbol and timeframe in filename
- Add strategy name or identifier
- Use descriptive suffixes

### 3. Testing Workflow
1. Generate all signal files in Python
2. Copy to MT5 Files directory
3. Run multi-file EA with appropriate pattern
4. Review cumulative results
5. Export detailed report

### 4. Performance
- For many files (50+), set `LogSignalDetails = false`
- Use `LogVerbose = false` for production runs
- Keep `LogFileList = true` to verify files loaded

---

## 🔍 Troubleshooting

### No Files Found
```
ERROR: No files found matching pattern: BT_*.csv
```
**Solution:**
- Verify files are in `MQL5/Files/` directory
- Check pattern syntax (use wildcards correctly)
- Ensure files have `.csv` extension

### Files Not in Order
```
--- Transitioned to file: BT_20251019_... (wrong order)
```
**Solution:**
- Set `SortByDate = true`
- Verify filename format: `BT_YYYYMMDD_HHMMSS_...`
- Check dates extracted correctly in Journal

### Mixed Symbol Signals
```
WARNING: Signal symbol (EURUSD) differs from EA symbol (XAUUSD)
```
**Solution:**
- Use symbol-specific pattern: `"BT_*_XAUUSD_*.csv"`
- Run EA on correct symbol
- Separate files by symbol

### Memory Issues (Many Files)
```
ERROR: Cannot allocate memory
```
**Solution:**
- Process files in smaller batches
- Reduce number of files
- Increase MT5 memory limits

---

## 📚 Related Documentation

- **Single File Version:** `PythonSignalExecutor_v2.mq5`
- **Setup Guide:** `MQL5_SETUP_GUIDE.md`
- **Code Specification:** `MQL5_CODE_SPECIFICATION.md`
- **Python Integration:** `MT5_INTEGRATION_GUIDE.md`

---

## 🎯 Summary

**PythonSignalExecutor_Multi v3.0** enables:
- ✅ Automatic folder scanning
- ✅ Multi-file processing in one run
- ✅ Chronological ordering
- ✅ Cumulative statistics
- ✅ Walk-forward testing
- ✅ Portfolio analysis
- ✅ Strategy comparison
- ✅ Time-period segmentation

**Perfect for:** Walk-forward analysis, portfolio testing, multi-strategy backtesting, and comprehensive performance evaluation across multiple signal files.

---

**Ready to test multiple strategies in one run!** 🚀
