# Interactive Backtest Workflow

## Visual Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER STARTS BACKTEST                          │
│  (Double-click .bat file OR run Python script)                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   STEP 1: SYMBOL SELECTION                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Enter stock symbol (e.g., AAPL, MSFT, GOOGL): AAPL       │  │
│  │ ✓ Selected symbol: AAPL                                  │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  STEP 2: DATE RANGE SELECTION                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ From (start date): 2024-01-01                            │  │
│  │ ✓ Start date: 2024-01-01                                 │  │
│  │                                                           │  │
│  │ To (end date): 2024-10-22                                │  │
│  │ ✓ End date: 2024-10-22                                   │  │
│  │                                                           │  │
│  │ 📅 Backtest period: 295 days                             │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  [Validation: Format check, future date check, logical order]    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                STEP 3: INTERVAL SELECTION (Full Mode)            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Select interval (1-5):                                    │  │
│  │   1. 1d  - Daily                                          │  │
│  │   2. 1h  - Hourly                                         │  │
│  │   3. 30m - 30 minutes                                     │  │
│  │   4. 15m - 15 minutes                                     │  │
│  │   5. 5m  - 5 minutes                                      │  │
│  │                                                           │  │
│  │ Selection: 1                                              │  │
│  │ ✓ Selected interval: 1d                                   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  (Quick Mode: Auto-uses 1d)                                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                STEP 4: DATA FETCHING (Data Module)               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ from Data.data_fetcher import DataFetcher                 │  │
│  │                                                           │  │
│  │ df = DataFetcher().fetch_data_by_date_range(              │  │
│  │     ticker = "AAPL",                                      │  │
│  │     start_date = "2024-01-01",                            │  │
│  │     end_date = "2024-10-22",                              │  │
│  │     interval = "1d"                                       │  │
│  │ )                                                         │  │
│  │                                                           │  │
│  │ ✓ Data fetched: 207 bars                                 │  │
│  │   Columns: [Open, High, Low, Close, Volume]              │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  [Data validation, cleaning, format conversion]                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│            STEP 5: CONFIGURATION (Full Mode Optional)            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Use default configuration? (Y/n): Y                       │  │
│  │                                                           │  │
│  │ ✓ Configuration set:                                      │  │
│  │   Starting Cash: $100,000.00                              │  │
│  │   Fee: $0.0 + 0.100%                                      │  │
│  │   Slippage: 0.0100%                                       │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  (Quick Mode: Auto-uses defaults)                                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                STEP 6: BROKER INITIALIZATION                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ from Backtest.sim_broker import SimBroker                 │  │
│  │ from Backtest.config import BacktestConfig                │  │
│  │                                                           │  │
│  │ broker = SimBroker(config)                                │  │
│  │                                                           │  │
│  │ ✓ SimBroker initialized (API v3.0.0)                      │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                STEP 7: STRATEGY INITIALIZATION                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ strategy = SimpleMAStrategy(                              │  │
│  │     broker = broker,                                      │  │
│  │     fast_period = 10,                                     │  │
│  │     slow_period = 30,                                     │  │
│  │     size = 100                                            │  │
│  │ )                                                         │  │
│  │                                                           │  │
│  │ ✓ Strategy initialized                                    │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  STEP 8: BACKTEST SIMULATION                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Simulating 207 bars...                                    │  │
│  │                                                           │  │
│  │ For each bar:                                             │  │
│  │   1. strategy.on_bar(timestamp, market_data)              │  │
│  │   2. broker.step_to(timestamp, market_data)               │  │
│  │                                                           │  │
│  │ Progress: [██████████████████████] 100%                   │  │
│  │                                                           │  │
│  │ ✓ Simulation complete!                                    │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                 STEP 9: METRICS COMPUTATION                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ metrics = broker.compute_metrics()                        │  │
│  │                                                           │  │
│  │ Computing:                                                │  │
│  │   - Total Return & Net Profit                             │  │
│  │   - Win Rate & Profit Factor                              │  │
│  │   - Sharpe, Sortino, Calmar Ratios                        │  │
│  │   - Max Drawdown & Recovery Factor                        │  │
│  │   - Trade Statistics                                      │  │
│  │                                                           │  │
│  │ ✓ Metrics computed                                        │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  STEP 10: RESULTS DISPLAY                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ ══════════════════════════════════════════════════════   │  │
│  │ BACKTEST RESULTS                                          │  │
│  │ ══════════════════════════════════════════════════════   │  │
│  │ Period: 2024-01-02 to 2024-10-22                         │  │
│  │ Duration: 294 days                                        │  │
│  │                                                           │  │
│  │ Starting Capital: $100,000.00                             │  │
│  │ Final Equity: $105,234.56                                 │  │
│  │ Net Profit: $5,234.56 (5.23%)                             │  │
│  │                                                           │  │
│  │ Total Trades: 12                                          │  │
│  │ Win Rate: 58.3%                                           │  │
│  │                                                           │  │
│  │ Sharpe Ratio: 1.45                                        │  │
│  │ Max Drawdown: $2,345.67 (2.35%)                           │  │
│  │ ══════════════════════════════════════════════════════   │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  STEP 11: SAVE RESULTS                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Save results to files? (Y/n): Y                           │  │
│  │                                                           │  │
│  │ Saving to: Backtest/results/                              │  │
│  │                                                           │  │
│  │ ✓ Trades saved to:                                        │  │
│  │   AAPL_trades_20241022_153045.csv                         │  │
│  │                                                           │  │
│  │ ✓ Metrics saved to:                                       │  │
│  │   AAPL_metrics_20241022_153045.json                       │  │
│  │                                                           │  │
│  │ ✓ All results saved successfully!                         │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     BACKTEST COMPLETE                            │
│              Thank you for using Interactive Backtest!           │
└─────────────────────────────────────────────────────────────────┘
```

## Data Module Integration Detail

```
┌─────────────────────────────────────────────────────────────────┐
│                    Data Module Integration                       │
└─────────────────────────────────────────────────────────────────┘

User Input                Data Module                  Backtest
    │                         │                            │
    │  Symbol + Dates         │                            │
    ├────────────────────────►│                            │
    │                         │                            │
    │                    DataFetcher                       │
    │                         │                            │
    │              fetch_data_by_date_range()              │
    │                         │                            │
    │                         │  Yahoo Finance API         │
    │                         ├──────────────►┐            │
    │                         │               │            │
    │                         │◄──────────────┘            │
    │                         │  Raw OHLCV Data            │
    │                         │                            │
    │                    Data Cleaning                     │
    │                    - Flatten columns                 │
    │                    - DateTime index                  │
    │                    - Remove NaN                      │
    │                    - Sort by date                    │
    │                         │                            │
    │                    Validated DataFrame               │
    │                         ├────────────────────────────►│
    │                         │                            │
    │                         │              Convert to Broker Format
    │                         │                            │
    │                         │              SimBroker Backtest
    │                         │                            │
    │◄────────────────────────┴────────────────────────────┤
    │                                                       │
    │                    Results Display                    │
    │                    & File Export                      │
    │                                                       │
    └───────────────────────────────────────────────────────┘
```

## File Organization

```
AlgoAgent/
│
├── Data/                           # Data Module
│   ├── data_fetcher.py             # ◄── FETCHES DATA
│   ├── indicator_calculator.py
│   └── ...
│
└── Backtest/                       # Backtest Module
    │
    ├── interactive_backtest_runner.py   # ◄── MAIN SCRIPT (Full)
    ├── quick_interactive_backtest.py    # ◄── MAIN SCRIPT (Quick)
    │
    ├── run_interactive_backtest.bat     # ◄── WINDOWS LAUNCHER
    ├── run_quick_backtest.bat           # ◄── WINDOWS LAUNCHER
    │
    ├── sim_broker.py                    # ◄── BROKER SIMULATOR
    ├── config.py                        # ◄── CONFIGURATION
    ├── example_strategy.py              # ◄── EXAMPLE STRATEGY
    │
    ├── test_interactive_backtest.py     # Testing
    ├── validate_setup.py                # Setup Validation
    │
    ├── INTERACTIVE_BACKTEST_README.md   # Documentation
    ├── SETUP_GUIDE.md                   # Setup Instructions
    ├── IMPLEMENTATION_SUMMARY.md        # This Summary
    │
    └── results/                         # ◄── OUTPUT DIRECTORY
        ├── AAPL_trades_*.csv
        ├── AAPL_metrics_*.json
        ├── MSFT_trades_*.csv
        └── MSFT_metrics_*.json
```

## Comparison: Before vs After

### BEFORE (Hardcoded)
```python
# In example_strategy.py - run_backtest()
ticker = "AAPL"                    # ◄── HARDCODED
period = "1y"                      # ◄── HARDCODED
interval = "1d"                    # ◄── HARDCODED

df = generate_sample_data(         # ◄── FAKE DATA
    symbol="AAPL",
    days=365
)
```

### AFTER (Interactive)
```python
# User enters at runtime
symbol = get_user_symbol()         # ◄── USER INPUT: "AAPL"
start_date = get_user_date()       # ◄── USER INPUT: "2024-01-01"
end_date = get_user_date()         # ◄── USER INPUT: "2024-10-22"
interval = get_user_interval()     # ◄── USER INPUT: "1d"

df = fetch_data_for_backtest(      # ◄── REAL DATA from Yahoo Finance
    symbol=symbol,
    start_date=start_date,
    end_date=end_date,
    interval=interval
)
```

## Usage Modes Comparison

### Full Interactive Mode
```
✓ Symbol selection
✓ Date range selection  
✓ Interval selection
✓ Configuration customization
✓ Strategy parameter tuning
✓ Save option

Recommended for: Detailed testing, custom configurations
```

### Quick Mode
```
✓ Symbol selection
✓ Date range selection
✗ Uses default interval (1d)
✗ Uses default configuration
✗ Uses default strategy params
✓ Auto-saves

Recommended for: Fast testing, standard configurations
```

## Integration Points

```
┌────────────────┐
│ User Interface │ ◄── Command line prompts
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  Validation    │ ◄── Date format, logic checks
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  Data Module   │ ◄── DataFetcher.fetch_data_by_date_range()
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ Data Cleaning  │ ◄── Format, validate, convert
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  Config Setup  │ ◄── BacktestConfig initialization
└───────┬────────┘
        │
        ▼
┌────────────────┐
│   SimBroker    │ ◄── Broker initialization
└───────┬────────┘
        │
        ▼
┌────────────────┐
│   Strategy     │ ◄── Strategy initialization
└───────┬────────┘
        │
        ▼
┌────────────────┐
│   Simulation   │ ◄── Bar-by-bar execution
└───────┬────────┘
        │
        ▼
┌────────────────┐
│    Metrics     │ ◄── Performance calculation
└───────┬────────┘
        │
        ▼
┌────────────────┐
│    Results     │ ◄── Display & Export
└────────────────┘
```
