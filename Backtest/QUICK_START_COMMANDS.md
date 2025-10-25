# Quick Start Commands

## Prerequisites

```powershell
# Install required packages
pip install yfinance pandas numpy google-generativeai python-dotenv

# Set up Gemini API key
$env:GEMINI_API_KEY = "your-api-key-here"
# OR create .env file with:
# GEMINI_API_KEY=your-api-key-here
```

## Running the Interactive Backtest Runner

### Method 1: Batch File (Recommended)
```powershell
cd c:\Users\nyaga\Documents\AlgoAgent\Backtest
.\run_interactive_backtest.bat
```

### Method 2: Direct Python
```powershell
cd c:\Users\nyaga\Documents\AlgoAgent\Backtest
python interactive_backtest_runner.py
```

### Method 3: Quick Mode (Defaults)
```powershell
cd c:\Users\nyaga\Documents\AlgoAgent\Backtest
.\run_quick_backtest.bat
# OR
python quick_interactive_backtest.py
```

## Validation

```powershell
# Verify setup
cd c:\Users\nyaga\Documents\AlgoAgent\Backtest
python validate_setup.py

# Expected: 14/14 checks pass
```

## Example Session Walkthrough

```powershell
PS C:\Users\nyaga\Documents\AlgoAgent\Backtest> python interactive_backtest_runner.py

╔════════════════════════════════════════════════════════════════╗
║        INTERACTIVE BACKTEST RUNNER v2.0                        ║
║        with Strategy Integration                               ║
╚════════════════════════════════════════════════════════════════╝

─────────────────────────────────────────────────────────────────
 STEP 1: SYMBOL SELECTION
─────────────────────────────────────────────────────────────────
Enter the ticker symbol (e.g., AAPL, MSFT, GOOGL): AAPL
✓ Symbol set to: AAPL

─────────────────────────────────────────────────────────────────
 STEP 2: DATE RANGE
─────────────────────────────────────────────────────────────────
Start Date (YYYY-MM-DD) [2024-01-01]: 2024-01-01
End Date (YYYY-MM-DD) [2024-10-22]: 2024-10-22
✓ Date range: 2024-01-01 to 2024-10-22

─────────────────────────────────────────────────────────────────
 STEP 3: DATA INTERVAL
─────────────────────────────────────────────────────────────────
Select interval:
  1. 1 day
  2. 1 hour
  3. 30 minutes
  4. 15 minutes
  5. 5 minutes
  6. Custom

Enter choice (1-6) [1]: 1
✓ Interval set to: 1d

─────────────────────────────────────────────────────────────────
 STEP 4: FETCH DATA
─────────────────────────────────────────────────────────────────
Fetching data for AAPL (2024-01-01 to 2024-10-22, interval: 1d)...
✓ Fetched 201 rows of data

─────────────────────────────────────────────────────────────────
 STEP 5: BACKTEST CONFIGURATION
─────────────────────────────────────────────────────────────────
Initial capital [100000]: 100000
Trading fee (%) [0.1]: 0.1
Slippage (%) [0.05]: 0.05
✓ Configuration complete

─────────────────────────────────────────────────────────────────
 STEP 6: STRATEGY SELECTION
─────────────────────────────────────────────────────────────────
Select strategy source:
  1. Enter NEW strategy (AI-powered validation & code generation)
  2. Use EXISTING strategy from library
  3. Use EXAMPLE strategy (quick test)

Enter choice (1-3): 1

═════════════════════════════════════════════════════════════════
 ENTER NEW STRATEGY
═════════════════════════════════════════════════════════════════
Describe your strategy in plain English.
You can use multiple lines. Type 'DONE' on a new line when finished.

Strategy text:
> Buy when RSI < 30 and price > 50-day moving average
> Sell when RSI > 70
> Use 14-period RSI
> DONE

✓ Strategy text captured (42 characters)

Validating strategy with AI...
─────────────────────────────────────────────────────────────────
✓ VALIDATION SUCCESSFUL
  • Strategy ID: strat-20241022-165432
  • Title: RSI Mean Reversion
  • Classification: Momentum, Mean Reversion
  • Risk Level: Medium
─────────────────────────────────────────────────────────────────

Generating Python code from canonical strategy...
─────────────────────────────────────────────────────────────────
✓ CODE GENERATED
  • File: Backtest/codes/rsi_mean_reversion_20241022_165432.py
  • JSON: Backtest/codes/rsi_mean_reversion_20241022_165432.json
─────────────────────────────────────────────────────────────────

Loading strategy class...
✓ Strategy loaded: RsiMeanReversion

─────────────────────────────────────────────────────────────────
 STEP 7: STRATEGY PARAMETERS
─────────────────────────────────────────────────────────────────
Found 2 parameters for RsiMeanReversion:

  1. rsi_period (default: 14)
     Enter value [14]: 14
  
  2. rsi_oversold (default: 30)
     Enter value [30]: 30

✓ Parameters configured

─────────────────────────────────────────────────────────────────
 STEP 8: RUN BACKTEST
─────────────────────────────────────────────────────────────────
Running backtest...
  • Processing 201 bars...
  • Strategy: RsiMeanReversion
  • Symbol: AAPL
  • Period: 2024-01-01 to 2024-10-22

[■■■■■■■■■■■■■■■■■■■■] 100%

✓ Backtest complete (5.2 seconds)

─────────────────────────────────────────────────────────────────
 STEP 9: RESULTS
─────────────────────────────────────────────────────────────────

PERFORMANCE METRICS
═══════════════════
  Total Return:       12.45%
  Sharpe Ratio:       1.34
  Max Drawdown:       -5.67%
  Win Rate:           62.50%
  Total Trades:       24
  Avg Trade:          0.52%

FILES SAVED
═══════════
  Trades:  results/AAPL_trades_20241022_165432.csv
  Metrics: results/AAPL_metrics_20241022_165432.json
  Code:    codes/rsi_mean_reversion_20241022_165432.py
  Config:  codes/rsi_mean_reversion_20241022_165432.json

═════════════════════════════════════════════════════════════════
 BACKTEST COMPLETE
═════════════════════════════════════════════════════════════════
```

## Testing Different Strategy Options

### Option 1: New Strategy (AI-Powered)
```powershell
# Full workflow: Text → Validation → Code Generation → Backtest
python interactive_backtest_runner.py

# Select Option 1
# Enter strategy description
# AI validates and generates code
# Code saved to codes/
# Backtest runs automatically
```

### Option 2: Existing Strategy
```powershell
# Use previously generated strategies
python interactive_backtest_runner.py

# Select Option 2
# Choose from codes/ directory:
#   - rsi_mean_reversion_20241022.py
#   - moving_average_crossover_20241021.py
#   - etc.
# Backtest runs with selected strategy
```

### Option 3: Example Strategy
```powershell
# Quick test with built-in SimpleMAStrategy
python interactive_backtest_runner.py

# Select Option 3
# Customize parameters:
#   - short_window (default: 20)
#   - long_window (default: 50)
# Backtest runs immediately
```

## Common Workflows

### Workflow A: Quick Test with Defaults
```powershell
python quick_interactive_backtest.py
# Uses AAPL, last 6 months, 1-day interval, SimpleMAStrategy
```

### Workflow B: New Strategy Development
```powershell
python interactive_backtest_runner.py
# Option 1: Enter new strategy
# Iterate on parameters
# Save successful strategies
```

### Workflow C: Strategy Library Management
```powershell
# List generated strategies
dir codes\*.py

# Rerun existing strategy with different data
python interactive_backtest_runner.py
# Option 2: Select from library
# Change symbol or dates
```

### Workflow D: Batch Testing Multiple Symbols
```powershell
# Test same strategy on different symbols
python interactive_backtest_runner.py  # Run for AAPL
python interactive_backtest_runner.py  # Run for MSFT
python interactive_backtest_runner.py  # Run for GOOGL
# Use Option 2 to select same strategy each time
```

## Troubleshooting Commands

### Check Python Environment
```powershell
python --version
# Should be Python 3.7+
```

### Verify Packages
```powershell
pip list | findstr "yfinance pandas numpy google-generativeai"
```

### Test Data Fetcher
```powershell
cd ..\Data
python -c "from data_fetcher import DataFetcher; df = DataFetcher(); print(df.fetch_data_by_date_range('AAPL', '2024-01-01', '2024-10-22', '1d')); print('Success!')"
```

### Test Strategy Validator
```powershell
cd ..\Strategy
python -c "from strategy_validator import StrategyValidatorBot; bot = StrategyValidatorBot(); print('Success!')"
```

### Check Gemini API Key
```powershell
echo $env:GEMINI_API_KEY
# Should print your API key (not empty)
```

### View Generated Files
```powershell
# List generated strategies
dir codes\*.py

# List backtest results
dir results\*.csv
dir results\*.json
```

### Read Strategy Code
```powershell
# View generated Python code
type codes\rsi_mean_reversion_20241022_165432.py

# View canonical JSON
type codes\rsi_mean_reversion_20241022_165432.json
```

## Development Commands

### Run Tests
```powershell
# Test interactive backtest components
python test_interactive_backtest.py

# Test strategy validation
cd ..\Strategy
python -m pytest tests/

# Test data fetcher
cd ..\Data
python -m pytest tests/
```

### Clean Up Old Results
```powershell
# Remove old backtest results (keep last 10)
python cleanup_old_files.py
```

## Advanced Usage

### Custom Intervals
```powershell
# When prompted for interval, select Option 6 (Custom)
# Enter any valid yfinance interval:
#   - 1m, 2m, 5m, 15m, 30m, 60m, 90m
#   - 1h, 1d, 5d, 1wk, 1mo, 3mo
```

### Multiple Parameter Tests
```powershell
# Test different RSI periods
python interactive_backtest_runner.py
# Use same strategy, different parameters:
#   Run 1: rsi_period=10
#   Run 2: rsi_period=14
#   Run 3: rsi_period=20
# Compare results/ files
```

### Strategy Comparison
```powershell
# Run multiple strategies on same data
python interactive_backtest_runner.py  # Strategy A
python interactive_backtest_runner.py  # Strategy B
python interactive_backtest_runner.py  # Strategy C
# Use same symbol & dates
# Compare metrics JSON files
```

## File Locations

```
Backtest/
├── interactive_backtest_runner.py     # Main runner (v2.0)
├── quick_interactive_backtest.py      # Quick mode
├── run_interactive_backtest.bat       # Windows launcher
├── run_quick_backtest.bat             # Quick launcher
├── validate_setup.py                  # Setup validator
│
├── codes/                             # Generated strategies
│   ├── *.py                           # Python code
│   └── *.json                         # Canonical JSON
│
└── results/                           # Backtest outputs
    ├── *_trades_*.csv                 # Trade logs
    └── *_metrics_*.json               # Performance metrics
```

## Environment Variables

```powershell
# Gemini API Key (required for code generation)
$env:GEMINI_API_KEY = "your-key"

# Optional: Change default symbol
$env:DEFAULT_SYMBOL = "MSFT"

# Optional: Change default capital
$env:DEFAULT_CAPITAL = "50000"
```

## Next Steps

1. **Install dependencies**:
   ```powershell
   pip install yfinance pandas numpy google-generativeai python-dotenv
   ```

2. **Set up Gemini API key**:
   ```powershell
   $env:GEMINI_API_KEY = "your-api-key-here"
   ```

3. **Run validation**:
   ```powershell
   python validate_setup.py
   ```

4. **Start backtesting**:
   ```powershell
   python interactive_backtest_runner.py
   ```

5. **Explore features**:
   - Try all three strategy options
   - Test different symbols and dates
   - Compare strategies
   - Build your strategy library

## Support Documentation

- **Setup**: `SETUP_GUIDE.md`
- **Usage**: `INTERACTIVE_BACKTEST_README.md`
- **Strategy Integration**: `STRATEGY_INTEGRATION_GUIDE.md`
- **Quick Reference**: `QUICK_REFERENCE.md`
- **Flow Diagrams**: `STRATEGY_INTEGRATION_DIAGRAM.md`
- **API Reference**: `API_REFERENCE.md`

## Tips

✓ Start with Option 3 (Example strategy) for quick testing
✓ Use Option 1 (New strategy) when developing new ideas
✓ Use Option 2 (Existing) to reuse successful strategies
✓ Save promising strategies (automatically saved in codes/)
✓ Compare results by running same strategy on different symbols
✓ Use quick mode (`quick_interactive_backtest.py`) for rapid iteration
✓ Check results/ directory for detailed trade logs
✓ Review generated code in codes/ to understand strategy logic

---

**Ready to start? Run this command:**
```powershell
cd c:\Users\nyaga\Documents\AlgoAgent\Backtest
python interactive_backtest_runner.py
```
