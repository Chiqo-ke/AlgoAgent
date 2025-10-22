# 🚀 Quick Start Guide - Enhanced Backtesting

## What You Have Now

Your backtesting system now logs:
1. **Every row** of data with pattern detection (True/False) 
2. **All trading signals** with full context for simulation

## Run the Demo

```bash
cd c:\Users\nyaga\Documents\AlgoAgent
python -m Backtest.test_logging_simple
```

You'll see:
```
✓ Strategy initialized with loggers
✓ Generated 60 bars
✓ Simulation complete

Total Rows Analyzed: 78
Patterns Found: 2
Total Signals: 2

📁 Logs saved in: Backtest/signals/
```

## Check Your Logs

```bash
cd Backtest\signals
dir
```

You'll find 3 files per test:
- `*_patterns_*.csv` - Every row with True/False
- `*_signals_*.csv` - All trading signals
- `*_signals_*.json` - Signals in JSON format

## Use in Your Strategy

```python
from Backtest.pattern_logger import PatternLogger
from Backtest.signal_logger import SignalLogger

class MyStrategy:
    def __init__(self, broker, symbol, strategy_id):
        # Add these two lines
        self.pattern_logger = PatternLogger(strategy_id)
        self.signal_logger = SignalLogger(strategy_id)
    
    def on_bar(self, timestamp, data):
        # Log EVERY row
        self.pattern_logger.log_pattern(
            timestamp=timestamp,
            symbol=self.symbol,
            step_id="entry",
            step_title="Check Entry",
            pattern_condition="Your condition",
            pattern_found=True,  # Your logic
            market_data={...},
            indicator_values={...}
        )
        
        # Log signals when generated
        if pattern_found:
            self.signal_logger.log_signal(
                timestamp=timestamp,
                symbol=self.symbol,
                side="BUY",
                action="ENTRY",
                order_type="MARKET",
                size=100,
                price=150.00,
                reason="Why you entered",
                market_data={...},
                indicator_values={...}
            )
    
    def finalize(self):
        # Add this at end of backtest
        self.pattern_logger.close()
        self.signal_logger.close()
```

## Documentation

- 📖 **Full Guide**: `ENHANCED_BACKTEST_SUMMARY.md`
- 📚 **Usage Docs**: `LOGGING_SYSTEM.md`
- ⚡ **Quick Ref**: `LOGGING_QUICKREF.md`
- 🔀 **Flow Diagram**: `FLOW_DIAGRAM.md`
- ✅ **Test Results**: `TEST_VERIFIED.md`

## Examples

- 📝 **Enhanced Template**: `strategy_template_enhanced.py`
- 🧪 **Working Test**: `test_logging_simple.py`

## That's It!

You now have:
✅ Sequential row-by-row processing
✅ Pattern logging (True/False debugging)
✅ Signal logging (trade simulation)
✅ Working test with sample output
✅ Complete documentation

**Next**: Copy `strategy_template_enhanced.py` and build your own strategy!
