# MQL5 Expert Advisor Code Specification

**AI Model Instructions for Generating Compatible MQL5 Code**

**Version:** 1.0.0  
**Last Updated:** October 19, 2025  
**Purpose:** Generate MQL5 Expert Advisor that executes signals from Python backtesting module

---

## 🎯 Objective

Generate an MQL5 Expert Advisor that:
1. Reads CSV signal files exported from Python `SimBroker`
2. Executes signals in MT5 Strategy Tester with exact timing
3. Maintains compatibility with Python signal format
4. Produces comparable results for validation

---

## 📋 Input Data Format Specification

### Signal File Format

**File Type:** CSV (Comma-separated values)  
**Encoding:** UTF-8  
**Location:** MT5 `MQL5/Files/` directory  
**Naming Pattern:** `BT_YYYYMMDD_HHMMSS_SYMBOL_TIMEFRAME_signals.csv`

### CSV Structure

**Header Row (Required):**
```csv
timestamp,symbol,signal,lot_size,stop_loss,take_profit,signal_id,metadata
```

**Data Row Example:**
```csv
2024-01-15T09:00:00+00:00,XAUUSD,BUY,0.10,1950.50,1980.00,sig-abc123,"{""strategy_id"":""ma_cross""}"
```

### Column Specifications

| Column | Data Type | Format | Constraints | Example |
|--------|-----------|--------|-------------|---------|
| `timestamp` | DateTime | ISO 8601 with UTC | `YYYY-MM-DDTHH:MM:SS+00:00` | `2024-01-15T09:00:00+00:00` |
| `symbol` | String | MT5 symbol name | Max 20 chars | `XAUUSD` |
| `signal` | Enum | Signal type | `BUY`, `SELL`, `EXIT`, `HOLD` | `BUY` |
| `lot_size` | Double | Lot size | >= 0.0, precision 2 decimals | `0.10` |
| `stop_loss` | Double | Price level | >= 0.0 (0 = no SL) | `1950.50` |
| `take_profit` | Double | Price level | >= 0.0 (0 = no TP) | `1980.00` |
| `signal_id` | String | Unique identifier | Max 50 chars | `sig-abc123` |
| `metadata` | String | JSON object | Escaped quotes | `"{""key"":""value""}"` |

### Signal Type Definitions

| Signal | Action Required | Position Management |
|--------|----------------|---------------------|
| `BUY` | Open LONG position | Close existing SHORT first |
| `SELL` | Open SHORT position | Close existing LONG first |
| `EXIT` | Close any open position | Close LONG or SHORT |
| `HOLD` | No action | Maintain current state |

### Timestamp Parsing Requirements

**Input Format:** ISO 8601 with timezone offset
- Example: `2024-01-15T09:00:00+00:00`
- Timezone: Always UTC (`+00:00`)

**MQL5 Conversion Required:**
1. Parse ISO 8601 string
2. Convert to `datetime` type
3. Align to bar open time on specified timeframe
4. Handle timezone conversion if broker uses different timezone

**Example Parsing Logic:**
```mql5
datetime ParseISO8601(string timestamp_str)
{
   // Remove timezone suffix (+00:00 or Z)
   StringReplace(timestamp_str, "+00:00", "");
   StringReplace(timestamp_str, "Z", "");
   
   // Parse: "2024-01-15T09:00:00"
   datetime result = StringToTime(timestamp_str);
   return result;
}
```

---

## 🔧 Required MQL5 Components

### 1. Input Parameters

```mql5
input string   SignalFile = "BT_20241018_120000_XAUUSD_H1_signals.csv"; // CSV filename in MQL5/Files/
input double   RiskPercent = 0.0;        // 0 = use signal lot size exactly
input int      Slippage = 10;            // Max slippage in points
input bool     LogVerbose = true;        // Enable detailed logging
input int      MagicNumber = 20241018;   // Unique EA identifier
```

**Parameter Descriptions:**
- `SignalFile`: Exact filename (with .csv extension) in MQL5/Files/ directory
- `RiskPercent`: If 0.0, use exact lot sizes from CSV; if > 0, calculate based on account risk
- `Slippage`: Maximum acceptable slippage in points for order execution
- `LogVerbose`: Enable/disable detailed logging to Journal
- `MagicNumber`: Unique identifier for this EA's trades

### 2. Data Structures

```mql5
// Signal data structure matching CSV format
struct SignalData
{
   datetime timestamp;      // Parsed from ISO 8601
   string   symbol;         // Trading symbol
   string   signal;         // BUY/SELL/EXIT/HOLD
   double   lot_size;       // Position size in lots
   double   stop_loss;      // SL price (0 = none)
   double   take_profit;    // TP price (0 = none)
   string   signal_id;      // Unique identifier
};

// Global storage
SignalData signals[];       // Array of all signals
int signalCount = 0;        // Total signals loaded
int currentSignalIndex = 0; // Current processing index
```

### 3. Core Functions Required

#### A. File Loading Function

**Purpose:** Read and parse CSV file into signal array

**Signature:**
```mql5
bool LoadSignalFile(string filename)
```

**Requirements:**
1. Open file from `MQL5/Files/` directory using `FileOpen()`
2. Read header row and validate column names
3. Parse each data row into `SignalData` structure
4. Store in global `signals[]` array
5. Validate data integrity (timestamps sequential, valid signal types)
6. Return `true` if successful, `false` on error
7. Log total signals loaded and date range

**Error Handling:**
- File not found
- Invalid CSV format
- Malformed timestamps
- Invalid signal types
- Missing required columns

#### B. Signal Processing Function

**Purpose:** Execute signal when bar matches signal timestamp

**Signature:**
```mql5
void ProcessSignalForBar(datetime bar_time)
```

**Requirements:**
1. Find signal(s) matching current bar time
2. Validate signal symbol matches EA symbol
3. Execute signal based on type (BUY/SELL/EXIT/HOLD)
4. Handle position conflicts (close opposite position first)
5. Log execution details
6. Track processed signals to avoid duplicates

**Logic Flow:**
```
1. Search signals[] for timestamp == bar_time
2. If found:
   - Verify symbol matches _Symbol
   - Check signal type
   - Execute corresponding action
   - Increment currentSignalIndex
3. If not found:
   - Continue (no signal for this bar)
```

#### C. Order Execution Functions

**Required Functions:**

```mql5
// Open new position
bool OpenPosition(ENUM_ORDER_TYPE order_type, SignalData &signal)

// Close current position
bool ClosePosition()

// Check if position exists
bool HasPosition()

// Get current position type
ENUM_POSITION_TYPE GetPositionType()
```

**OpenPosition() Requirements:**
1. Calculate lot size (use signal.lot_size if RiskPercent == 0)
2. Get current price (Ask for BUY, Bid for SELL)
3. Set SL/TP from signal (if not 0)
4. Execute order using `OrderSend()`
5. Handle slippage tolerance
6. Log execution result
7. Return success/failure

**ClosePosition() Requirements:**
1. Select position by symbol
2. Get position ticket
3. Determine close price (Bid for LONG, Ask for SHORT)
4. Send close order
5. Log result

### 4. Execution Timing

**Critical Requirement:** Signals must execute on bar open, not on tick

**Implementation:**
```mql5
datetime lastBarTime = 0;

void OnTick()
{
   // Get current bar open time
   datetime currentBarTime = iTime(_Symbol, _Period, 0);
   
   // Check if new bar opened
   if(currentBarTime == lastBarTime)
      return;  // Not a new bar, exit
   
   lastBarTime = currentBarTime;
   
   // Process signal for this bar
   ProcessSignalForBar(currentBarTime);
}
```

**Why This Matters:**
- Python backtest executes on bar close (next bar open)
- MT5 must execute at same bar open to match timing
- Ticks within bar should not trigger multiple executions

---

## 🔄 Signal Execution Logic

### Signal Processing Flow

```
OnTick() called
    ↓
New bar detected?
    ↓ YES
Get bar open time
    ↓
Find signal for this time
    ↓
Signal found?
    ↓ YES
Validate symbol matches
    ↓
Check signal type
    ↓
┌─────────────────┐
│  BUY Signal     │ → Close SHORT (if exists) → Open LONG
│  SELL Signal    │ → Close LONG (if exists) → Open SHORT
│  EXIT Signal    │ → Close any position
│  HOLD Signal    │ → Do nothing
└─────────────────┘
    ↓
Log execution
    ↓
Continue to next bar
```

### Position Management Rules

**Rule 1: One Position at a Time**
- EA maintains maximum one open position
- New signal closes opposite position first

**Rule 2: BUY Signal Logic**
```mql5
if(signal.signal == "BUY")
{
   // Check for existing position
   if(PositionSelect(_Symbol))
   {
      // If SHORT position exists, close it
      if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_SELL)
         ClosePosition();
   }
   
   // Open LONG position (only if no position exists)
   if(!PositionSelect(_Symbol))
      OpenPosition(ORDER_TYPE_BUY, signal);
}
```

**Rule 3: SELL Signal Logic**
```mql5
if(signal.signal == "SELL")
{
   // Check for existing position
   if(PositionSelect(_Symbol))
   {
      // If LONG position exists, close it
      if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY)
         ClosePosition();
   }
   
   // Open SHORT position (only if no position exists)
   if(!PositionSelect(_Symbol))
      OpenPosition(ORDER_TYPE_SELL, signal);
}
```

**Rule 4: EXIT Signal Logic**
```mql5
if(signal.signal == "EXIT")
{
   // Close any position (LONG or SHORT)
   if(PositionSelect(_Symbol))
      ClosePosition();
}
```

**Rule 5: HOLD Signal Logic**
```mql5
if(signal.signal == "HOLD")
{
   // No action - maintain current state
   // Optional: Log for debugging
}
```

---

## 📊 Logging Requirements

### Initialization Logging

**OnInit() must log:**
```
=== PythonSignalExecutor EA Starting ===
Signal File: [filename]
Symbol: [symbol]
Timeframe: [timeframe]
Successfully loaded [N] signals
Date range: [start] to [end]
```

### Execution Logging (if LogVerbose == true)

**For each signal processed:**
```
Processing signal at [timestamp]
Signal: [BUY/SELL/EXIT/HOLD]
Lot Size: [lot_size]
Stop Loss: [stop_loss]
Take Profit: [take_profit]
ID: [signal_id]
```

**For position actions:**
```
Opening LONG position: [lot_size] lots at [price]
Position opened successfully, Ticket: [ticket]

OR

Closing LONG position: [lot_size] lots at [price]
Position closed successfully, Profit: [profit]
```

### Shutdown Logging

**OnDeinit() must log:**
```
=== PythonSignalExecutor EA Stopped ===
Reason: [reason]
Signals processed: [current_index] / [total_count]
```

### Error Logging

**Critical errors:**
- Failed to load signal file
- Invalid signal format
- Order execution failure
- Symbol mismatch
- Invalid lot size

**Format:**
```
ERROR: [description]
Details: [additional context]
```

---

## 🎯 MQL5 Order Execution Specifications

### Order Sending

**Use MqlTradeRequest structure:**
```mql5
MqlTradeRequest request;
MqlTradeResult result;

// Initialize request
ZeroMemory(request);
request.action = TRADE_ACTION_DEAL;
request.symbol = _Symbol;
request.volume = lot_size;              // From signal
request.type = order_type;              // ORDER_TYPE_BUY or ORDER_TYPE_SELL
request.price = price;                  // Ask for BUY, Bid for SELL
request.sl = stop_loss;                 // From signal (0 if none)
request.tp = take_profit;               // From signal (0 if none)
request.deviation = Slippage;           // From input parameter
request.magic = MagicNumber;            // From input parameter
request.comment = "PythonSignal";

// Send order
if(!OrderSend(request, result))
{
   Print("ERROR: Order failed, error code: ", GetLastError());
   return false;
}

return true;
```

### Position Closing

```mql5
// Select position
if(!PositionSelect(_Symbol))
   return false;

long ticket = PositionGetInteger(POSITION_TICKET);
double volume = PositionGetDouble(POSITION_VOLUME);
ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);

// Prepare close request
MqlTradeRequest request;
MqlTradeResult result;
ZeroMemory(request);

request.action = TRADE_ACTION_DEAL;
request.position = ticket;
request.symbol = _Symbol;
request.volume = volume;
request.type = (type == POSITION_TYPE_BUY) ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
request.price = (type == POSITION_TYPE_BUY) ? SymbolInfoDouble(_Symbol, SYMBOL_BID) : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
request.deviation = Slippage;
request.magic = MagicNumber;

// Close position
if(!OrderSend(request, result))
{
   Print("ERROR: Close failed, error code: ", GetLastError());
   return false;
}

return true;
```

---

## 🔍 Validation Requirements

### Pre-execution Validation

**Before executing any signal:**

1. **Symbol Validation**
   ```mql5
   if(signal.symbol != _Symbol)
   {
      Print("WARNING: Signal symbol mismatch");
      return false;
   }
   ```

2. **Lot Size Validation**
   ```mql5
   double min_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double max_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   
   if(signal.lot_size < min_lot || signal.lot_size > max_lot)
   {
      Print("ERROR: Invalid lot size");
      return false;
   }
   ```

3. **Price Validation (for SL/TP)**
   ```mql5
   double current_price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   
   // For BUY: SL < entry < TP
   // For SELL: TP < entry < SL
   // Validate accordingly
   ```

4. **Timestamp Validation**
   ```mql5
   // Ensure timestamp is within backtest range
   if(signal.timestamp < start_date || signal.timestamp > end_date)
   {
      Print("WARNING: Signal outside date range");
      return false;
   }
   ```

---

## 📐 Python Backtest Module Interface

### How Python Generates Signals

**Python Side (SimBroker):**
```python
# User enables MT5 export
broker = SimBroker(
    config=config,
    enable_mt5_export=True,
    mt5_symbol="XAUUSD",
    mt5_timeframe="H1"
)

# Strategy submits signals normally
signal = create_signal(
    timestamp=datetime(2024, 1, 15, 9, 0),
    symbol="XAUUSD",
    side=OrderSide.BUY,
    action=OrderAction.ENTRY,
    order_type=OrderType.MARKET,
    size=100,  # 100 oz
    strategy_id="my_strategy"
)
broker.submit_signal(signal.to_dict())

# After backtest, export to CSV
broker.export_mt5_signals(format="csv")
```

**What Gets Exported:**
- **Timestamp:** Bar close time (when signal generated)
- **Symbol:** MT5-compatible symbol name
- **Signal:** BUY/SELL/EXIT (converted from side+action)
- **Lot Size:** Automatically converted from shares (100 oz → 1.0 lot)
- **SL/TP:** Calculated by strategy (or 0.0 if none)
- **Signal ID:** Unique identifier for tracking
- **Metadata:** JSON with strategy_id, action, order_type

### Lot Size Conversion (Python → MT5)

**Automatic Conversion in `signal_exporter.py`:**

| Symbol | Python Size | Conversion Factor | MT5 Lot Size |
|--------|------------|-------------------|--------------|
| XAUUSD | 100 oz | ÷ 100 | 1.00 lot |
| XAUUSD | 50 oz | ÷ 100 | 0.50 lot |
| XAUUSD | 10 oz | ÷ 100 | 0.10 lot |
| EURUSD | 100,000 units | ÷ 100,000 | 1.00 lot |
| EURUSD | 10,000 units | ÷ 100,000 | 0.10 lot |
| BTCUSD | 1 BTC | ÷ 1 | 1.00 lot |

**MQL5 receives lot sizes directly - no conversion needed**

### Signal Type Conversion

**Python to MQL5 Mapping:**

| Python Side | Action | MT5 Signal |
|-------------|--------|------------|
| `side=BUY`, `action=ENTRY` | Open long | `BUY` |
| `side=SELL`, `action=ENTRY` | Open short | `SELL` |
| `action=EXIT` (any side) | Close position | `EXIT` |
| No signal this bar | Hold | `HOLD` (optional) |

---

## ⚙️ Configuration Matching

### Settings That Must Match

**For accurate comparison between Python and MT5:**

| Setting | Python (config.py) | MT5 Strategy Tester |
|---------|-------------------|---------------------|
| **Initial Capital** | `start_cash=10000` | Deposit: `10000` |
| **Symbol** | `mt5_symbol="XAUUSD"` | Symbol: `XAUUSD` |
| **Timeframe** | `mt5_timeframe="H1"` | Period: `H1` |
| **Commission** | `commission=0.0` | Commission: `0` |
| **Slippage** | `slippage=0.0` | Slippage: `0` (or minimal) |
| **Date Range** | Strategy start/end dates | Date From/To |

### Strategy Tester Settings

**Required settings for validation:**
- **Model:** Every tick (most accurate)
- **Optimization:** Disabled
- **Visualization:** Optional (slower)
- **Forward:** Disabled

---

## 📤 Expected Output Format

### Journal Output Example

```
2024.01.15 09:00:00  PythonSignalExecutor (XAUUSD,H1)  === PythonSignalExecutor EA Starting ===
2024.01.15 09:00:00  PythonSignalExecutor (XAUUSD,H1)  Signal File: BT_20241018_120000_XAUUSD_H1_signals.csv
2024.01.15 09:00:00  PythonSignalExecutor (XAUUSD,H1)  Symbol: XAUUSD
2024.01.15 09:00:00  PythonSignalExecutor (XAUUSD,H1)  Timeframe: H1
2024.01.15 09:00:00  PythonSignalExecutor (XAUUSD,H1)  Successfully loaded 245 signals
2024.01.15 09:00:00  PythonSignalExecutor (XAUUSD,H1)  Date range: 2024-01-01 00:00 to 2024-03-31 23:00
2024.01.15 09:00:00  PythonSignalExecutor (XAUUSD,H1)  Processing signal at 2024-01-15 09:00:00
2024.01.15 09:00:00  PythonSignalExecutor (XAUUSD,H1)  Signal: BUY
2024.01.15 09:00:00  PythonSignalExecutor (XAUUSD,H1)  Opening LONG position: 0.10 lots at 1975.25
2024.01.15 09:00:00  PythonSignalExecutor (XAUUSD,H1)  Position opened successfully, Ticket: 123456789
...
2024.03.31 23:00:00  PythonSignalExecutor (XAUUSD,H1)  === PythonSignalExecutor EA Stopped ===
2024.03.31 23:00:00  PythonSignalExecutor (XAUUSD,H1)  Signals processed: 245 / 245
```

### Results Export

**Must be exportable to HTML report containing:**
- Total trades
- Net profit
- Win rate
- Profit factor
- Maximum drawdown
- All individual trades with timestamps

---

## 🚨 Error Handling Requirements

### Critical Errors (Must Abort)

1. **Signal file not found**
   - Return `INIT_FAILED` from `OnInit()`
   
2. **Invalid CSV format**
   - Log error with line number
   - Return `INIT_FAILED`
   
3. **Empty signal file**
   - Log warning
   - Return `INIT_FAILED`

### Recoverable Errors (Log and Continue)

1. **Symbol mismatch**
   - Log warning
   - Skip signal
   
2. **Invalid lot size**
   - Log warning
   - Skip signal
   
3. **Order execution failure**
   - Log error with code
   - Continue to next signal

### Warnings (Log Only)

1. **Timestamp outside date range**
2. **Duplicate signal timestamp**
3. **HOLD signal encountered**
4. **SL/TP at invalid levels**

---

## ✅ Success Criteria

### The generated MQL5 EA is successful if:

1. ✅ Loads CSV file without errors
2. ✅ Parses all signals correctly
3. ✅ Executes signals at correct bar open times
4. ✅ Opens/closes positions according to signal type
5. ✅ Matches trade count from Python (±2% acceptable)
6. ✅ Matches net profit from Python (±5% acceptable due to spreads)
7. ✅ Logs execution details for debugging
8. ✅ Handles errors gracefully
9. ✅ Completes without crashes
10. ✅ Produces exportable results

---

## 📚 Reference Implementation

### Existing Implementation

**File:** `PythonSignalExecutor.mq5` (in `Backtest/` directory)
**Lines:** 390 lines
**Status:** Production-ready, tested

**Key Features Implemented:**
- CSV parsing with proper ISO 8601 handling
- Bar-aligned execution (not tick-based)
- Position management (one position at a time)
- Stop loss and take profit handling
- Comprehensive logging
- Error handling
- Magic number for trade identification

**AI Model Note:** You can reference this file for implementation patterns, but generate code based on this specification for clarity.

---

## 🎯 Code Generation Checklist

When generating MQL5 code, ensure:

- [ ] `#property strict` directive included
- [ ] All input parameters defined with descriptions
- [ ] `SignalData` struct matches CSV format exactly
- [ ] `OnInit()` loads and validates CSV file
- [ ] `OnTick()` checks for new bar before processing
- [ ] Timestamp parsing handles ISO 8601 with timezone
- [ ] Signal type switch handles BUY/SELL/EXIT/HOLD
- [ ] Position management closes opposite positions first
- [ ] Order execution uses `MqlTradeRequest`
- [ ] Stop loss and take profit are set from signals
- [ ] Magic number tags all trades
- [ ] Logging matches specification
- [ ] Error handling covers all critical cases
- [ ] `OnDeinit()` logs summary statistics
- [ ] Code compiles without errors in MetaEditor
- [ ] Variable naming is clear and consistent

---

## 📝 Example Prompt for AI Code Generation

**Use this prompt with AI models:**

```
Generate an MQL5 Expert Advisor that:

1. Reads CSV signal files with format: timestamp,symbol,signal,lot_size,stop_loss,take_profit,signal_id,metadata
2. Parses ISO 8601 timestamps (YYYY-MM-DDTHH:MM:SS+00:00)
3. Executes signals on bar open (not every tick)
4. Handles signal types: BUY (open long), SELL (open short), EXIT (close position), HOLD (no action)
5. Manages one position at a time (close opposite before opening new)
6. Uses stop loss and take profit from signal (0 = none)
7. Logs all actions to Journal with timestamps
8. Returns INIT_FAILED if file not found or invalid
9. Uses input parameters: SignalFile, RiskPercent, Slippage, LogVerbose, MagicNumber
10. Produces results comparable to Python backtest

Requirements:
- File location: MQL5/Files/ directory
- Execution timing: Bar open only
- Position logic: One position maximum
- Error handling: Log and continue for non-critical errors
- Validation: Check symbol, lot size, prices before execution

Reference the MQL5_CODE_SPECIFICATION.md for complete details.
```

---

## 🔗 Related Files

- **Python Export:** `signal_exporter.py` - Generates CSV files
- **Python Broker:** `sim_broker.py` - Backtest engine with MT5 export
- **Python Reconciliation:** `mt5_reconciliation.py` - Compare results
- **MQL5 Implementation:** `PythonSignalExecutor.mq5` - Reference code
- **Setup Guide:** `MQL5_SETUP_GUIDE.md` - User instructions
- **Integration Guide:** `MT5_INTEGRATION_GUIDE.md` - Complete documentation

---

**This specification ensures any AI-generated MQL5 code will be fully compatible with your Python backtesting module.** 🎯
