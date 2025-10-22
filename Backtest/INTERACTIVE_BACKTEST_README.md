# Interactive Backtest Runner

## Overview

The Interactive Backtest Runner adds human interaction to the backtesting system through command-line prompts. Instead of hardcoding security symbols and date ranges, users can now dynamically specify:

1. **Symbol Selection** - Enter any stock ticker symbol
2. **Date Range** - Specify custom start and end dates
3. **Data Interval** - Choose timeframe (daily, hourly, etc.)
4. **Configuration** - Customize backtest parameters or use defaults

## Features

✅ **Interactive Symbol Entry** - Enter stock symbols via command line  
✅ **Custom Date Ranges** - Specify exact start and end dates (From: {date}, To: {date})  
✅ **Dynamic Data Fetching** - Automatically fetches data from Yahoo Finance using the Data module  
✅ **Date Validation** - Ensures dates are in correct format and logical order  
✅ **Flexible Intervals** - Support for various timeframes (1m, 5m, 15m, 30m, 1h, 1d, etc.)  
✅ **Configuration Options** - Customize fees, slippage, and starting capital  
✅ **Strategy Parameters** - Adjust strategy settings interactively  
✅ **Progress Tracking** - Real-time progress updates during simulation  
✅ **Comprehensive Results** - Detailed metrics and statistics  
✅ **Auto-Save Results** - Exports trades and metrics to files  

## Files Created

### Core Scripts

1. **`interactive_backtest_runner.py`** - Full-featured interactive backtest with all options
2. **`quick_interactive_backtest.py`** - Streamlined version with minimal prompts and defaults
3. **`run_interactive_backtest.bat`** - Windows batch script for full version
4. **`run_quick_backtest.bat`** - Windows batch script for quick version

## Usage

### Method 1: Using Batch Scripts (Easiest)

**Full Interactive Mode:**
```cmd
cd Backtest
run_interactive_backtest.bat
```

**Quick Mode (Minimal Prompts):**
```cmd
cd Backtest
run_quick_backtest.bat
```

### Method 2: Direct Python Execution

**Full Interactive Mode:**
```cmd
cd Backtest
python interactive_backtest_runner.py
```

**Quick Mode:**
```cmd
cd Backtest
python quick_interactive_backtest.py
```

## Interactive Workflow

### Full Interactive Mode

1. **Symbol Selection**
   ```
   Enter stock symbol (e.g., AAPL, MSFT, GOOGL): AAPL
   ```

2. **Date Range Selection**
   ```
   From (start date): 2024-01-01
   To (end date): 2024-12-31
   ```

3. **Interval Selection**
   ```
   Select interval (1-5) or enter custom:
     1. 1d  - Daily
     2. 1h  - Hourly
     3. 30m - 30 minutes
     4. 15m - 15 minutes
     5. 5m  - 5 minutes
   Selection: 1
   ```

4. **Configuration Options**
   ```
   Use default configuration? (Y/n): n
   Starting cash (default $100,000): 50000
   Fee percentage (default 0.100%): 0.1
   ```

5. **Strategy Parameters**
   ```
   Customize strategy parameters? (y/N): y
   Fast MA period (default 10): 10
   Slow MA period (default 30): 50
   Position size (default 100): 100
   ```

6. **Results Display**
   - Comprehensive performance metrics
   - Trade statistics
   - Risk metrics (Sharpe, Sortino, Calmar ratios)
   - Drawdown analysis

7. **Save Results**
   ```
   Save results to files? (Y/n): Y
   ```

### Quick Mode

Simplified workflow with only essential prompts:
1. Enter symbol
2. Enter date range
3. View results (uses defaults for everything else)
4. Auto-saves results

## Examples

### Example 1: Backtest Apple Stock (2024)

```
Symbol: AAPL
From: 2024-01-01
To: 2024-10-22
Interval: 1d (daily)
```

### Example 2: Backtest Microsoft with Custom Range

```
Symbol: MSFT
From: 2023-06-01
To: 2024-06-01
Interval: 1h (hourly)
```

### Example 3: Quick Test on Recent Data

```
Symbol: GOOGL
From: 2024-09-01
To: 2024-10-22
```

## Date Format

All dates must be in **YYYY-MM-DD** format:
- ✅ Valid: `2024-01-01`, `2023-12-31`, `2024-10-22`
- ❌ Invalid: `01/01/2024`, `1-1-2024`, `2024/01/01`

## Data Fetching

The system uses the **Data module's DataFetcher** class:

```python
from Data.data_fetcher import DataFetcher

fetcher = DataFetcher()
df = fetcher.fetch_data_by_date_range(
    ticker=symbol,
    start_date=start_date,
    end_date=end_date,
    interval=interval
)
```

This fetches real-time data from Yahoo Finance with the specified date range.

## Validation

The system includes comprehensive validation:

### Symbol Validation
- Non-empty
- Alphanumeric characters (plus `^` and `.` for special tickers)

### Date Validation
- Correct format (YYYY-MM-DD)
- Not in the future
- End date after start date
- Valid calendar dates

### Data Validation
- Non-empty DataFrame
- Required OHLCV columns present
- No missing data in critical rows

## Output Files

Results are saved with timestamps in the `results/` directory:

```
results/
  ├── AAPL_trades_20241022_153045.csv
  ├── AAPL_metrics_20241022_153045.json
  ├── MSFT_trades_20241022_160215.csv
  └── MSFT_metrics_20241022_160215.json
```

### Trade File Format (CSV)
```csv
entry_time,exit_time,symbol,side,entry_price,exit_price,size,pnl,pnl_pct,commission,slippage
```

### Metrics File Format (JSON)
```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-10-22",
  "total_trades": 45,
  "win_rate": 0.556,
  "net_profit": 12345.67,
  "sharpe_ratio": 1.45,
  ...
}
```

## Integration with Existing System

### Compatible Components

The interactive runner integrates seamlessly with:

- ✅ **Data Module** - Uses `DataFetcher` for data retrieval
- ✅ **SimBroker** - Full broker simulation with all features
- ✅ **BacktestConfig** - All configuration options supported
- ✅ **Strategy Classes** - Works with any strategy implementing `on_bar()`
- ✅ **Metrics Engine** - Complete performance analytics

### Strategy Integration

To use your custom strategy, modify the import section:

```python
# In interactive_backtest_runner.py, replace:
from Backtest.example_strategy import SimpleMAStrategy

# With your strategy:
from Backtest.your_strategy import YourStrategyClass
```

Then update the strategy instantiation:

```python
strategy_params = {
    'param1': value1,
    'param2': value2,
    # Your parameters
}

metrics = run_backtest_simulation(
    broker=broker,
    df=df,
    symbol=symbol,
    strategy_class=YourStrategyClass,
    strategy_params=strategy_params
)
```

## Customization

### Adding New Intervals

Edit the `get_user_interval()` function to add more presets:

```python
intervals = {
    '1': '1d',
    '2': '1h',
    '3': '30m',
    '4': '15m',
    '5': '5m',
    '6': '1wk',  # Add weekly
    '7': '1mo',  # Add monthly
}
```

### Custom Validation Rules

Modify `validate_date()` to add business days validation, holidays, etc.:

```python
def validate_date(date_string: str) -> Tuple[bool, Optional[datetime]]:
    # Add custom validation logic
    # Check if date is a business day
    # Exclude holidays
    # etc.
    pass
```

### Additional User Inputs

Add more prompts in the `main()` function:

```python
def main():
    symbol = get_user_symbol()
    start_date, end_date = get_user_date_range()
    interval = get_user_interval()
    
    # Add your custom prompts
    leverage = get_user_leverage()
    risk_level = get_user_risk_level()
    # etc.
```

## Troubleshooting

### Common Issues

**1. "No data returned" error**
- Check if the symbol is valid
- Verify date range isn't too narrow
- Ensure dates aren't too old (yfinance limits)
- Try a different interval

**2. "Data fetcher not available" error**
- Install yfinance: `pip install yfinance`
- Check Data module is accessible
- Verify imports are working

**3. Python not found (batch scripts)**
- Install Python 3.7+
- Add Python to PATH
- Try running Python scripts directly

**4. Empty DataFrame after fetching**
- Symbol might be delisted
- Date range might be invalid
- Market might be closed for that period

## Requirements

### Python Packages
```
pandas>=1.3.0
numpy>=1.20.0
yfinance>=0.1.70
```

### Module Dependencies
```
Data/
  ├── data_fetcher.py
  └── ...

Backtest/
  ├── sim_broker.py
  ├── config.py
  ├── example_strategy.py
  └── ...
```

## Best Practices

1. **Start with Recent Data** - Use recent dates for initial tests
2. **Use Appropriate Intervals** - Match interval to strategy timeframe
3. **Check Data Quality** - Review fetched data before running full backtest
4. **Save Results** - Always save results for later analysis
5. **Test with Small Capital** - Use realistic starting capital amounts
6. **Include Fees** - Use realistic fee structure for accurate results

## Advanced Usage

### Batch Testing Multiple Symbols

Create a script that calls the runner programmatically:

```python
from interactive_backtest_runner import (
    fetch_data_for_backtest,
    get_realistic_config,
    run_backtest_simulation,
    save_results
)

symbols = ['AAPL', 'MSFT', 'GOOGL']
for symbol in symbols:
    df = fetch_data_for_backtest(symbol, '2024-01-01', '2024-10-22')
    # Run backtest...
```

### Custom Date Range Presets

Add quick presets for common ranges:

```python
def get_preset_range():
    print("Preset ranges:")
    print("  1. Last 30 days")
    print("  2. Last 90 days")
    print("  3. Last year")
    print("  4. Year-to-date")
    print("  5. Custom")
    # Implement logic
```

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the example output
3. Verify all dependencies are installed
4. Check the Data module documentation

## Version History

- **v1.0.0** (2024-10-22)
  - Initial release
  - Interactive symbol and date selection
  - Integration with Data module
  - Full and quick modes
  - Windows batch scripts
  - Comprehensive validation
  - Auto-save results

## Future Enhancements

Potential additions:
- [ ] Multiple symbol backtesting
- [ ] Portfolio backtesting
- [ ] Strategy comparison mode
- [ ] Visual charts and plots
- [ ] Email results notification
- [ ] Database storage for results
- [ ] Web interface option
