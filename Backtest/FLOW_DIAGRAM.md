# Enhanced Backtesting Flow Diagram

## Overview: Sequential Data Processing with Logging

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ENHANCED BACKTESTING FLOW                         │
└─────────────────────────────────────────────────────────────────────┘

1. INITIALIZATION
   ┌──────────────────┐
   │ Load Data        │
   │ with Indicators  │
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │ Initialize       │
   │ - Broker         │
   │ - Strategy       │
   │ - PatternLogger  │
   │ - SignalLogger   │
   └────────┬─────────┘
            │
            ▼

2. SEQUENTIAL PROCESSING (Row by Row)
   ┌─────────────────────────────────────────────────────────────────┐
   │  FOR EACH ROW in DataFrame:                                     │
   │                                                                  │
   │  ┌───────────────────────────────────────────────────────────┐ │
   │  │ ROW N: timestamp, OHLCV, indicators                       │ │
   │  └───────────────────────────────────────────────────────────┘ │
   │                          │                                       │
   │                          ▼                                       │
   │  ┌───────────────────────────────────────────────────────────┐ │
   │  │ STRATEGY.ON_BAR()                                         │ │
   │  │                                                           │ │
   │  │  Step 1: Extract market_data & indicators                │ │
   │  │          ↓                                                │ │
   │  │  Step 2: Check Entry Pattern                             │ │
   │  │          ├─→ LOG PATTERN (True/False) ─→ pattern_log.csv │ │
   │  │          │                                                │ │
   │  │          └─→ If True & not in position:                  │ │
   │  │               ├─→ LOG SIGNAL ──────────→ signal_log.csv  │ │
   │  │               └─→ Submit to Broker                       │ │
   │  │                                                           │ │
   │  │  Step 3: Check Exit Pattern (if in position)             │ │
   │  │          ├─→ LOG PATTERN (True/False) ─→ pattern_log.csv │ │
   │  │          │                                                │ │
   │  │          └─→ If True:                                    │ │
   │  │               ├─→ LOG SIGNAL ──────────→ signal_log.csv  │ │
   │  │               └─→ Submit to Broker                       │ │
   │  └───────────────────────────────────────────────────────────┘ │
   │                          │                                       │
   │                          ▼                                       │
   │  ┌───────────────────────────────────────────────────────────┐ │
   │  │ BROKER.STEP_TO()                                          │ │
   │  │                                                           │ │
   │  │  - Process pending signals                                │ │
   │  │  - Execute trades                                         │ │
   │  │  - Update positions                                       │ │
   │  │  - Update account state                                   │ │
   │  └───────────────────────────────────────────────────────────┘ │
   │                          │                                       │
   │                          ▼                                       │
   │                    NEXT ROW                                      │
   └─────────────────────────────────────────────────────────────────┘
            │
            ▼

3. FINALIZATION
   ┌──────────────────┐
   │ Strategy.        │
   │ finalize()       │
   │                  │
   │ - Close Pattern  │
   │   Logger         │
   │ - Close Signal   │
   │   Logger         │
   │ - Print          │
   │   Summaries      │
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │ Broker.          │
   │ compute_metrics()│
   │                  │
   │ - Calculate PnL  │
   │ - Win Rate       │
   │ - Drawdown       │
   │ - Sharpe Ratio   │
   │ - etc.           │
   └────────┬─────────┘
            │
            ▼

4. OUTPUT FILES
   ┌──────────────────────────────────────────────────────────────┐
   │ signals/                                                      │
   │                                                              │
   │ ┌─────────────────────────────────────────────────────────┐ │
   │ │ {strategy_id}_patterns_{timestamp}.csv                  │ │
   │ │ ─────────────────────────────────────────────────────── │ │
   │ │ Every row analyzed with True/False pattern detection    │ │
   │ │                                                         │ │
   │ │ timestamp | step_id | pattern_condition | pattern_found│ │
   │ │ ──────────┼─────────┼───────────────────┼──────────────│ │
   │ │ 10:00     | entry   | EMA_30 > EMA_50   | False        │ │
   │ │ 10:01     | entry   | EMA_30 > EMA_50   | False        │ │
   │ │ 10:02     | entry   | EMA_30 > EMA_50   | TRUE ✓       │ │
   │ │ 10:03     | exit    | Stop Loss Hit     | False        │ │
   │ │ ...       | ...     | ...               | ...          │ │
   │ └─────────────────────────────────────────────────────────┘ │
   │                                                              │
   │ ┌─────────────────────────────────────────────────────────┐ │
   │ │ {strategy_id}_signals_{timestamp}.csv                   │ │
   │ │ ─────────────────────────────────────────────────────── │ │
   │ │ All trading signals with full context                   │ │
   │ │                                                         │ │
   │ │ signal_id | timestamp | side | action | size | price   │ │
   │ │ ──────────┼───────────┼──────┼────────┼──────┼────────│ │
   │ │ SIG_001   | 10:02     | BUY  | ENTRY  | 100  | 151.00 │ │
   │ │ SIG_002   | 14:30     | SELL | EXIT   | 100  | 152.50 │ │
   │ │ ...       | ...       | ...  | ...    | ...  | ...    │ │
   │ └─────────────────────────────────────────────────────────┘ │
   │                                                              │
   │ ┌─────────────────────────────────────────────────────────┐ │
   │ │ {strategy_id}_signals_{timestamp}.json                  │ │
   │ │ ─────────────────────────────────────────────────────── │ │
   │ │ Full signal details with nested objects                 │ │
   │ │ - Market data at signal time                            │ │
   │ │ - Indicator values at signal time                       │ │
   │ │ - Strategy state at signal time                         │ │
   │ │ - For programmatic signal replay                        │ │
   │ └─────────────────────────────────────────────────────────┘ │
   └──────────────────────────────────────────────────────────────┘
```

## Key Concepts

### 1. Every Row is Logged
```
Data Row 1 → Check Pattern → Log (False) → No Signal
Data Row 2 → Check Pattern → Log (False) → No Signal
Data Row 3 → Check Pattern → Log (TRUE) → Generate Signal → Log Signal
Data Row 4 → Check Pattern → Log (False) → No Signal
...
```

### 2. Pattern vs Signal Logs

**Pattern Logs** = Every row analyzed
- Shows ALL pattern checks (True/False)
- Helps debug: "Why didn't my strategy enter here?"
- Shows: "Pattern was checked but not found"

**Signal Logs** = Only when signals generated
- Shows ACTUAL trading signals
- Used for trade simulation
- Contains full context for replay

### 3. Data Flow

```
Historical Data (CSV/API)
         ↓
Load with Indicators (EMA, RSI, etc.)
         ↓
DataFrame with OHLCV + Indicators
         ↓
┌─────────────────────────┐
│ Row-by-Row Processing   │
│                         │
│ For each row:           │
│   1. Extract data       │
│   2. Check patterns ────→ LOG (True/False)
│   3. If pattern found   │
│      Generate signal ───→ LOG (Signal Details)
│   4. Execute with broker│
└─────────────────────────┘
         ↓
Pattern Logs + Signal Logs + Trades + Metrics
```

## Logging Decision Tree

```
┌──────────────────────┐
│  Strategy.on_bar()   │
│  (called for row N)  │
└──────────┬───────────┘
           │
           ▼
    ┌─────────────┐
    │ Extract     │
    │ market_data │
    │ & indicators│
    └──────┬──────┘
           │
           ▼
    ┌────────────────────┐
    │ Check Entry Pattern│
    └──────┬─────────────┘
           │
           ├─→ LOG PATTERN ──→ pattern_log.csv
           │    (True or False)
           │
           ▼
    Pattern Found?
           │
       ┌───┴───┐
       │       │
      Yes      No
       │       │
       │       └─→ Continue
       │
       ▼
    Not in Position?
       │
   ┌───┴───┐
   │       │
  Yes      No
   │       │
   │       └─→ Continue
   │
   ▼
┌──────────────────┐
│ Generate Signal  │
├──────────────────┤
│ 1. LOG SIGNAL ───→ signal_log.csv
│                     (Full context)
│ 2. Submit to     │
│    Broker        │
│ 3. Update State  │
└──────────────────┘
```

## Summary Report Example

```
======================================================================
BACKTEST RESULTS
======================================================================
Final Equity: $102,500.00
Net Profit: $2,500.00
Total Trades: 15
Win Rate: 60.0%

======================================================================
PATTERN DETECTION SUMMARY
======================================================================
Total Rows Analyzed: 1,260           ← Every row logged
Patterns Found: 45                    ← True count
Patterns Not Found: 1,215             ← False count
Detection Rate: 3.57%                 ← True / Total

📁 Pattern Log: signals/strategy_001_patterns_20251022.csv

======================================================================
SIGNAL GENERATION SUMMARY
======================================================================
Total Signals: 30                     ← All signals logged
Entry Signals: 15                     ← BUY signals
Exit Signals: 15                      ← SELL signals
Market Orders: 30
Limit Orders: 0
Stop Orders: 0

📁 Signal CSV: signals/strategy_001_signals_20251022.csv
📁 Signal JSON: signals/strategy_001_signals_20251022.json

======================================================================
```

## Use Cases

### 1. Debugging Strategy Logic
```
"Why didn't my strategy enter at time X?"

→ Check pattern_log.csv at time X
→ See pattern_found = False
→ Check indicator_values column
→ Identify: EMA_30 was 149.5, EMA_50 was 150.2
→ Pattern condition not met!
```

### 2. Signal Verification
```
"Did my strategy generate the right signals?"

→ Check signal_log.csv
→ See all signals with reasons
→ Verify: Signal at 10:02 because "EMA crossover"
→ Confirm: Indicator values support the decision
```

### 3. Trade Simulation
```
"Can I test different execution strategies?"

→ Load signal_log.json
→ Replay signals with different parameters
→ Test: Market vs Limit orders
→ Test: Different position sizing
→ Compare results
```

### 4. Performance Attribution
```
"Which patterns generated profitable trades?"

→ Join pattern_log with signal_log with trades
→ Analyze: Which pattern conditions led to wins
→ Optimize: Adjust pattern thresholds
→ Improve: Strategy performance
```
