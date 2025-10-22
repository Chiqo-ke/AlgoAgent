# PythonSignalExecutor v2.0 - Release Notes

**Complete MQL5 Expert Advisor for Python Backtest Signal Execution**

**File:** `PythonSignalExecutor_v2.mq5`  
**Version:** 2.0  
**Lines:** ~750 lines  
**Status:** Production Ready ✅

---

## 🎯 What's New in v2.0

### Enhanced Features

1. **Improved Input Parameters**
   - Grouped parameters for better UX
   - Added `MaxLotSize` safety limit
   - Added `CloseOppositeFirst` toggle

2. **Better Error Handling**
   - Comprehensive error messages
   - Detailed return code descriptions
   - Graceful fallback for order types

3. **Advanced Risk Management**
   - Risk-based position sizing option
   - Symbol specification validation
   - Lot size normalization

4. **Comprehensive Logging**
   - Startup banner with configuration
   - Per-signal execution details
   - Statistics summary on exit
   - Trade execution confirmations

5. **Robust CSV Parsing**
   - ISO 8601 timestamp parsing
   - Empty line handling
   - Invalid data skipping
   - Line number tracking

6. **Position Management**
   - Multiple order filling types (FOK/IOC/RETURN)
   - Opposite position closing
   - Position profit tracking

---

## 📋 Key Features

### Input Parameters

```mql5
// File Settings
SignalFile = "BT_20241018_120000_XAUUSD_H1_signals.csv"

// Risk Management
RiskPercent = 0.0          // 0 = use signal lot size
MaxLotSize = 10.0          // Safety limit

// Trading Settings
Slippage = 10              // Max slippage in points
MagicNumber = 20241019     // Unique trade identifier
CloseOppositeFirst = true  // Close opposite before opening

// Logging
LogVerbose = true          // Detailed logs
LogSignalDetails = true    // Per-signal details
```

### Signal Processing

**Supported Signal Types:**
- `BUY` - Opens long position (closes short first if exists)
- `SELL` - Opens short position (closes long first if exists)
- `EXIT` - Closes any open position
- `HOLD` - No action (maintains current state)

**Execution Timing:**
- Signals execute on **bar open** only
- Not tick-based (prevents multiple executions)
- Aligns with Python bar close → MT5 bar open

### CSV Format Support

**Expected Format:**
```csv
timestamp,symbol,signal,lot_size,stop_loss,take_profit,signal_id,metadata
2024-01-15T09:00:00+00:00,XAUUSD,BUY,0.10,1950.50,1980.00,sig-abc123,"{""key"":""val""}"
```

**Parsing Features:**
- ISO 8601 timestamp with timezone (`+00:00` or `Z`)
- Automatic timestamp normalization
- Skips invalid/malformed lines
- Counts and reports skipped signals

### Position Management

**Logic:**
1. One position maximum per symbol
2. Opposite positions closed before opening new
3. SL/TP from signal (0 = none)
4. Multiple filling modes (FOK → IOC → RETURN)
5. Price normalization to symbol digits

### Error Handling

**Critical Errors (Aborts):**
- File not found
- Invalid CSV format
- No signals loaded
- Invalid parameters

**Recoverable Errors (Continues):**
- Symbol mismatch (logs warning)
- Invalid lot size (skips signal)
- Order execution failure (logs error)
- Past signals (logs warning)

**Validation:**
- Input parameter validation
- CSV header validation
- Signal data validation
- Lot size normalization
- Price level validation

---

## 🔧 Technical Implementation

### Core Functions

| Function | Purpose | Lines |
|----------|---------|-------|
| `OnInit()` | Initialize EA, load signals | ~80 |
| `OnTick()` | Process new bars | ~20 |
| `LoadSignalFile()` | Parse CSV file | ~80 |
| `ParseISO8601Timestamp()` | Parse timestamp | ~10 |
| `ValidateSignal()` | Validate signal data | ~25 |
| `ProcessSignalsForBar()` | Find and execute signals | ~30 |
| `ExecuteSignal()` | Execute trading signal | ~70 |
| `CalculateLotSize()` | Calculate position size | ~50 |
| `OpenPosition()` | Open new position | ~60 |
| `ClosePosition()` | Close existing position | ~60 |
| `NormalizePrice()` | Normalize to symbol digits | ~5 |
| `GetDeinitReasonText()` | Deinit reason description | ~15 |
| `GetRetcodeDescription()` | Trade error description | ~40 |

### Data Structures

```mql5
struct SignalData
{
   datetime timestamp;      // Bar open time
   string   symbol;         // Trading symbol
   string   signal;         // BUY/SELL/EXIT/HOLD
   double   lot_size;       // Lot size
   double   stop_loss;      // SL price (0=none)
   double   take_profit;    // TP price (0=none)
   string   signal_id;      // Unique ID
   string   metadata;       // JSON metadata
};
```

### Global Variables

```mql5
SignalData signals[];           // All loaded signals
int        totalSignals = 0;    // Total count
int        currentSignalIndex = 0; // Current position
bool       fileLoaded = false;  // Load status
datetime   lastBarTime = 0;     // Last processed bar
int        tradesExecuted = 0;  // Trade counter
int        signalsProcessed = 0; // Signal counter

// Statistics
int buySignals, sellSignals, exitSignals, holdSignals, skippedSignals;
```

---

## 📊 Logging Output

### Initialization
```
================================================================
===       PythonSignalExecutor EA v2.0 Starting             ===
================================================================
Signal File: BT_20241018_120000_XAUUSD_H1_signals.csv
Symbol: XAUUSD
Timeframe: H1
Risk Percent: 0.0%
Magic Number: 20241019
================================================================
Loading signal file: BT_20241018_120000_XAUUSD_H1_signals.csv
CSV Header validated: timestamp,symbol,signal,lot_size,...
Loaded 245 valid signals
================================================================
Successfully loaded 245 signals
Date range: 2024-01-01 00:00 to 2024-03-31 23:00
Signal types: BUY=120 SELL=115 EXIT=10 HOLD=0
================================================================
```

### Signal Execution
```
--- Processing Signal ---
Time: 2024-01-15 09:00:00
Symbol: XAUUSD
Signal: BUY
Lot Size: 0.10
Stop Loss: 1950.50000
Take Profit: 1980.00000
ID: sig-abc123

✓ LONG position opened: 0.10 lots at 1975.25 | Ticket: 123456789
  Stop Loss: 1950.50000
  Take Profit: 1980.00000
```

### Position Close
```
✓ LONG position closed: 0.10 lots at 1982.50 | Profit: 72.50 | Ticket: 123456789
```

### Shutdown
```
================================================================
===       PythonSignalExecutor EA Stopped                   ===
================================================================
Deinit reason: 0 - Expert Advisor terminated
Signals processed: 245 / 245
Trades executed: 235
Signals skipped: 0
================================================================
```

---

## 🚀 Installation & Usage

### 1. Copy File to MT5

**Location:**
```
C:\Users\[YourUsername]\AppData\Roaming\MetaQuotes\Terminal\[ID]\MQL5\Experts\
```

### 2. Compile in MetaEditor

1. Press **F4** to open MetaEditor
2. Open `PythonSignalExecutor_v2.mq5`
3. Press **F7** to compile
4. Check for `0 errors, 0 warnings`

### 3. Copy Signal File

**From:**
```
AlgoAgent\Backtest\mt5_signals\BT_YYYYMMDD_HHMMSS_XAUUSD_H1_signals.csv
```

**To:**
```
C:\Users\[YourUsername]\AppData\Roaming\MetaQuotes\Terminal\[ID]\MQL5\Files\
```

### 4. Configure Strategy Tester

**Settings:**
- Expert: `PythonSignalExecutor_v2`
- Symbol: Match your signal file (e.g., `XAUUSD`)
- Period: Match your signal file (e.g., `H1`)
- Dates: Match your backtest range
- Deposit: Match your Python config

**Inputs:**
- SignalFile: Exact filename with `.csv`
- RiskPercent: `0.0` (use signal sizes)
- LogVerbose: `true` (for debugging)

### 5. Run Test

- Press **F5** to start
- Monitor **Journal** tab for logs
- Review **Results** tab for performance
- Export report: Right-click → Save as HTML

---

## ✅ Compatibility with Python

### Python Side (SimBroker)

```python
from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig

# Initialize with MT5 export
broker = SimBroker(
    config=BacktestConfig(start_cash=10000),
    enable_mt5_export=True,
    mt5_symbol="XAUUSD",
    mt5_timeframe="H1"
)

# Run backtest...
# Submit signals...

# Export to MT5
broker.export_mt5_signals(format="csv")
```

### MQL5 Side (This EA)

```
1. Loads CSV file
2. Parses ISO 8601 timestamps
3. Executes on bar open
4. Uses exact lot sizes (if RiskPercent=0)
5. Applies SL/TP from signals
6. Logs all actions
7. Produces comparable results
```

### Data Flow

```
Python Strategy → SimBroker → CSV Export → MT5 Files → EA → Execution → Results
```

---

## 🔍 Validation & Testing

### Expected Results

**Matching Metrics (±tolerance):**
- ✅ Trade count: Exact match (or 98%+)
- ✅ Net profit: ±5% (due to spreads/slippage)
- ✅ Win rate: ±2%
- ✅ Max drawdown: ±3%
- ✅ Trade timestamps: Exact match

### Troubleshooting

**Issue: No signals executed**
- Check symbol matches
- Check timeframe matches
- Check date range includes signals
- Verify signal file in MQL5/Files/

**Issue: Different trade count**
- Compare timestamps in Journal
- Check for symbol mismatches
- Verify lot sizes are valid
- Review skipped signal warnings

**Issue: Different profit**
- Normal: ±5% due to spreads
- Check spread settings in tester
- Compare individual trades
- Verify SL/TP execution

---

## 📈 Performance Optimization

### Best Practices

1. **Use RiskPercent=0** for exact validation
2. **Enable LogVerbose** during testing
3. **Disable LogVerbose** for speed optimization
4. **Use "Every tick" model** for accuracy
5. **Match deposit** with Python config

### Speed Optimization

**For large signal files:**
- Set `LogSignalDetails=false`
- Set `LogVerbose=false`
- Use visual mode only when needed
- Process in chunks if > 10,000 signals

---

## 🎯 Advantages Over v1.0

| Feature | v1.0 | v2.0 |
|---------|------|------|
| Input grouping | ❌ | ✅ |
| Risk-based sizing | ❌ | ✅ |
| Max lot limit | ❌ | ✅ |
| Multiple fill modes | ❌ | ✅ |
| Comprehensive logging | ⚠️ | ✅ |
| Error descriptions | Basic | Detailed |
| Statistics tracking | Basic | Comprehensive |
| Parameter validation | Basic | Complete |
| Code documentation | ⚠️ | ✅ |
| Lines of code | 390 | 750 |

---

## 📚 Documentation References

- **Setup Guide:** `MQL5_SETUP_GUIDE.md`
- **Code Specification:** `MQL5_CODE_SPECIFICATION.md`
- **Integration Guide:** `MT5_INTEGRATION_GUIDE.md`
- **Quick Reference:** `MT5_QUICK_REFERENCE.md`

---

## 🔗 MQL5 Documentation Used

Based on official MQL5 documentation from https://www.mql5.com/en/docs:

- **Trade Functions:** `OrderSend()`, `PositionSelect()`, `PositionGetInteger()`
- **File Operations:** `FileOpen()`, `FileClose()`, `FileReadString()`, `FileIsEnding()`
- **String Functions:** `StringToTime()`, `StringReplace()`, `StringToDouble()`
- **Math Functions:** `MathFloor()`, `NormalizeDouble()`
- **Symbol Info:** `SymbolInfoDouble()` for specifications
- **Account Info:** `AccountInfoDouble()` for balance

---

## ✅ Code Quality

- ✅ Strict mode enabled (`#property strict`)
- ✅ All functions documented with headers
- ✅ Consistent naming conventions
- ✅ Error handling on all critical operations
- ✅ Input validation
- ✅ Memory management (ZeroMemory)
- ✅ No magic numbers (all configurable)
- ✅ Clear separation of concerns
- ✅ Comprehensive logging
- ✅ Production-ready error messages

---

## 🎓 Learning Resources

**To understand this code:**
1. Read `MQL5_CODE_SPECIFICATION.md` for requirements
2. Review official MQL5 docs for functions used
3. Study `LoadSignalFile()` for CSV parsing
4. Understand `ProcessSignalsForBar()` for timing
5. Review `ExecuteSignal()` for position logic

**To modify this code:**
1. Keep the core signal processing logic
2. Modify risk management in `CalculateLotSize()`
3. Add custom filters in `ExecuteSignal()`
4. Enhance logging in `OnTick()` or `ExecuteSignal()`
5. Add custom statistics in `OnDeinit()`

---

**Status:** Ready for production use! ✅  
**Tested:** Compatible with Python SimBroker export format  
**Maintained:** Version 2.0 - October 19, 2025
