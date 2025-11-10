# Quick Reference Card - Interactive Backtest

## 🚀 Quick Start

### Windows (Easiest)
```
1. Double-click: run_quick_backtest.bat
2. Enter symbol: AAPL
3. Enter dates: 2024-01-01 to 2024-10-22
4. Done! Results auto-saved
```

### Command Line
```bash
cd Backtest
python quick_interactive_backtest.py
```

## 📋 Input Format

| Input | Format | Example |
|-------|--------|---------|
| **Symbol** | Uppercase ticker | `AAPL` `MSFT` `GOOGL` |
| **Start Date** | YYYY-MM-DD | `2024-01-01` |
| **End Date** | YYYY-MM-DD | `2024-10-22` |
| **Interval** | Number + unit | `1d` `1h` `30m` `5m` |

## 📊 Available Intervals

| Code | Description | Use For |
|------|-------------|---------|
| `1d` | Daily | Swing trading, long-term |
| `1h` | Hourly | Day trading |
| `30m` | 30 minutes | Intraday strategies |
| `15m` | 15 minutes | Short-term trading |
| `5m` | 5 minutes | Scalping |

## 🎯 Common Workflows

### Test a Stock for Last Year
```
Symbol: AAPL
From: 2023-10-22
To: 2024-10-22
```

### Test Recent Performance
```
Symbol: MSFT
From: 2024-09-01
To: 2024-10-22
```

### Test Specific Quarter
```
Symbol: GOOGL
From: 2024-07-01
To: 2024-09-30
```

## 📁 Output Files

Located in: `Backtest/results/`

```
{SYMBOL}_trades_{TIMESTAMP}.csv    # Trade details
{SYMBOL}_metrics_{TIMESTAMP}.json  # Performance metrics
```

Example:
```
AAPL_trades_20241022_153045.csv
AAPL_metrics_20241022_153045.json
```

## 📈 Key Metrics Explained

| Metric | What It Means | Good Value |
|--------|---------------|------------|
| **Net Profit** | Total money made/lost | > 0 |
| **Win Rate** | % of winning trades | > 50% |
| **Sharpe Ratio** | Risk-adjusted return | > 1.0 |
| **Max Drawdown** | Largest loss from peak | < 20% |
| **Profit Factor** | Gross profit / Gross loss | > 1.5 |

## 🔧 Two Modes

### Quick Mode (Recommended)
```
✓ Minimal prompts
✓ Default settings
✓ Fast testing
✓ Auto-save

Use when: Quick tests, standard configs
```

### Full Mode
```
✓ All customization
✓ Configure fees/slippage
✓ Adjust strategy params
✓ Choose save option

Use when: Detailed testing, custom setups
```

## ⚡ Keyboard Shortcuts

| Action | Key |
|--------|-----|
| Accept default | `Enter` |
| Cancel | `Ctrl+C` |
| Yes | `Y` or `y` |
| No | `N` or `n` |

## ❌ Common Errors

### "No data returned"
**Fix**: Check symbol exists, try different date range

### "ModuleNotFoundError: yfinance"
**Fix**: `pip install yfinance`

### "Invalid date format"
**Fix**: Use YYYY-MM-DD format (e.g., 2024-01-01)

### "End date before start date"
**Fix**: Ensure end date is after start date

## 📝 Example Session

```
> Symbol: TSLA
> From: 2024-08-01
> To: 2024-10-22

✓ Data fetched: 58 bars
✓ Running backtest...
✓ Complete!

Results:
  Net Profit: +$3,456.78 (3.46%)
  Win Rate: 54.5%
  Trades: 11
  Sharpe: 1.23
```

## 🛠️ Customization

### Use Your Own Strategy

Edit `interactive_backtest_runner.py` line ~476:

```python
from Backtest.my_strategy import MyStrategy

strategy_params = {
    'param1': value1,
    'param2': value2,
}

metrics = run_backtest_simulation(
    strategy_class=MyStrategy,
    strategy_params=strategy_params,
    ...
)
```

### Change Defaults

Edit these values in the script:

```python
# Default interval
interval = '1d'  # Change to '1h', '30m', etc.

# Default starting cash
config.start_cash = 100000  # Change amount

# Default fees
config.fee_pct = 0.001  # 0.1%
```

## 📚 Files to Know

| File | Purpose | When to Use |
|------|---------|-------------|
| `run_quick_backtest.bat` | Quick launcher | Quick tests |
| `run_interactive_backtest.bat` | Full launcher | Custom configs |
| `validate_setup.py` | Check setup | First time |
| `SETUP_GUIDE.md` | Installation | Setup help |
| `INTERACTIVE_BACKTEST_README.md` | Full docs | Detailed info |

## 🔍 Validation Checklist

Before first run:
- [ ] Python installed
- [ ] yfinance installed (`pip install yfinance`)
- [ ] In correct directory (Backtest/)
- [ ] Data module accessible

Run: `python validate_setup.py` to check

## 💡 Pro Tips

1. **Start Simple**: Use quick mode first
2. **Recent Data**: Use last 3-6 months for testing
3. **Save Results**: Always save for comparison
4. **Test Multiple Symbols**: Compare performance
5. **Check Data Quality**: Verify bar count makes sense
6. **Use Realistic Fees**: Don't forget transaction costs

## 🎓 Learning Path

1. **Beginner**: Run quick backtest with AAPL, last 3 months
2. **Intermediate**: Test multiple symbols, compare results
3. **Advanced**: Customize strategy, tune parameters
4. **Expert**: Integrate custom strategies, batch testing

## 📞 Getting Help

1. Check error message carefully
2. Review SETUP_GUIDE.md
3. Run validate_setup.py
4. Check INTERACTIVE_BACKTEST_README.md
5. Verify all files are present

## ⏱️ Typical Runtime

| Data Size | Runtime |
|-----------|---------|
| 30 days (daily) | < 1 second |
| 1 year (daily) | 1-2 seconds |
| 30 days (hourly) | 2-3 seconds |
| 1 year (hourly) | 10-15 seconds |

## 🔐 Data Privacy

- All data fetched from Yahoo Finance (public)
- No login required
- Results saved locally only
- No data sent to external servers

## 🌟 Features at a Glance

✅ Interactive symbol selection  
✅ Custom date ranges  
✅ Real-time data fetching  
✅ Multiple intervals supported  
✅ Full validation  
✅ Progress tracking  
✅ Comprehensive metrics  
✅ Auto-save results  
✅ CSV and JSON export  
✅ Windows batch files  
✅ Easy to customize  

## 🚦 Status Indicators

| Symbol | Meaning |
|--------|---------|
| ✓ | Success |
| ✗ | Error |
| ⚠️ | Warning |
| 📅 | Date info |
| 📊 | Data info |
| 🎉 | Complete |

## 📦 Package Requirements

```bash
pip install yfinance pandas numpy
```

That's it! Three packages, ready to go.

---

**Ready to start?** Just run: `run_quick_backtest.bat`

**Need help?** Read: `SETUP_GUIDE.md`

**Want details?** See: `INTERACTIVE_BACKTEST_README.md`
