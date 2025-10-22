# Setup Guide for Interactive Backtest

## Prerequisites

Before using the interactive backtest runner, ensure you have the following dependencies installed:

### Required Python Packages

```bash
pip install yfinance pandas numpy
```

Or install from the requirements file in the Data directory:

```bash
cd Data
pip install -r requirements.txt
```

### Verify Installation

Run this command to verify yfinance is installed:

```bash
python -c "import yfinance; print('yfinance version:', yfinance.__version__)"
```

## Quick Start

### 1. Install Dependencies

```bash
# From the root directory
pip install yfinance pandas numpy

# Or from Data directory
cd Data
pip install -r requirements.txt
```

### 2. Run a Test

**Option A: Quick Test (Recommended for first-time users)**

```bash
cd Backtest
python quick_interactive_backtest.py
```

Follow the prompts:
- Enter symbol: `AAPL`
- Start date: `2024-01-01`
- End date: `2024-10-22`

**Option B: Full Interactive Test**

```bash
cd Backtest
python interactive_backtest_runner.py
```

**Option C: Using Batch Files (Windows)**

Double-click:
- `run_quick_backtest.bat` for quick mode
- `run_interactive_backtest.bat` for full mode

### 3. View Results

Results are saved in `Backtest/results/`:
- CSV files contain trade details
- JSON files contain performance metrics

## Example Session

```
Symbol: MSFT
From: 2024-06-01
To: 2024-10-22

✓ Data fetched: 98 bars
✓ Running backtest...
✓ Results:
  Net Profit: $5,234.56 (5.23%)
  Win Rate: 58.3%
  Sharpe Ratio: 1.45
```

## Troubleshooting

### ModuleNotFoundError: No module named 'yfinance'

**Solution:**
```bash
pip install yfinance
```

### No data returned for symbol

**Possible causes:**
- Symbol doesn't exist or is delisted
- Date range is too narrow or old
- Network connectivity issues

**Solution:**
- Verify the symbol on Yahoo Finance website
- Try a different date range
- Check your internet connection

### ImportError: Data module not found

**Solution:**
- Ensure you're running from the correct directory
- The Data module should be in the parent directory
- Check sys.path includes the parent directory

### Empty DataFrame after fetching

**Possible causes:**
- Market was closed for entire period
- Symbol format is incorrect
- yfinance API issues

**Solution:**
- Try a more recent date range
- Verify symbol format (e.g., use `AAPL` not `AAPL.US`)
- Wait and retry (API rate limits)

## Advanced Setup

### Custom Strategy Integration

To use your own strategy:

1. Create your strategy class in `Backtest/` directory
2. Edit `interactive_backtest_runner.py`:

```python
# Replace line ~476
from Backtest.your_strategy import YourStrategy

# Update strategy initialization
strategy_params = {
    'your_param1': value1,
    'your_param2': value2,
}
```

### Environment Variables

You can set default values using environment variables:

```bash
# Windows
set DEFAULT_START_CASH=50000
set DEFAULT_INTERVAL=1d

# Linux/Mac
export DEFAULT_START_CASH=50000
export DEFAULT_INTERVAL=1d
```

Then modify the script to read these values.

## File Structure

After setup, your structure should look like:

```
AlgoAgent/
├── Data/
│   ├── data_fetcher.py          # Data fetching module
│   └── requirements.txt         # Dependencies
├── Backtest/
│   ├── interactive_backtest_runner.py      # Full interactive mode
│   ├── quick_interactive_backtest.py       # Quick mode
│   ├── run_interactive_backtest.bat        # Windows launcher
│   ├── run_quick_backtest.bat              # Quick launcher
│   ├── test_interactive_backtest.py        # Component tests
│   ├── sim_broker.py                       # Broker simulator
│   ├── config.py                           # Configuration
│   └── results/                            # Output directory
│       ├── AAPL_trades_*.csv
│       └── AAPL_metrics_*.json
```

## Testing

To verify your setup works:

1. **Basic Test (Recommended)**
   ```bash
   cd Backtest
   python -c "from interactive_backtest_runner import validate_date; print(validate_date('2024-01-01'))"
   ```
   
   Expected output: `(True, datetime.datetime(2024, 1, 1, 0, 0))`

2. **Data Fetcher Test**
   ```bash
   cd Data
   python -c "from data_fetcher import DataFetcher; df = DataFetcher().fetch_historical_data('AAPL', '1mo', '1d'); print(f'Fetched {len(df)} rows')"
   ```
   
   Expected output: `Fetched 20 rows` (approximate)

3. **Full Component Test** (requires yfinance)
   ```bash
   cd Backtest
   python test_interactive_backtest.py
   ```

## Next Steps

Once setup is complete:

1. ✅ Run your first backtest with `run_quick_backtest.bat`
2. ✅ Review the results in the `results/` directory
3. ✅ Customize configuration for your needs
4. ✅ Integrate your own trading strategies
5. ✅ Compare different symbols and date ranges

## Support

For issues:
- Check the troubleshooting section above
- Review error messages carefully
- Verify all dependencies are installed
- Ensure you're in the correct directory

## Additional Resources

- **yfinance documentation**: https://pypi.org/project/yfinance/
- **Pandas documentation**: https://pandas.pydata.org/docs/
- **Backtest documentation**: See `INTERACTIVE_BACKTEST_README.md`
