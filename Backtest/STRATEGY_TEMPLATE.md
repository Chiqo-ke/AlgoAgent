# Strategy Template and Import Guidelines

## Correct Import Pattern for Generated Strategies

All strategies generated in the `codes/` directory MUST use the following import pattern to work with both the Backtest module and the Live trading module:

```python
# MUST NOT EDIT SimBroker
"""
Strategy: YourStrategyName
Description: Your strategy description
Generated: YYYY-MM-DD
"""

# Add parent directory to path for imports
import sys
from pathlib import Path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import from Backtest package
from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig
from Backtest.canonical_schema import create_signal, OrderSide, OrderAction, OrderType
from Backtest.data_loader import load_market_data
from datetime import datetime
import pandas as pd
```

## Why This Pattern?

### ❌ Old Pattern (BROKEN for Live Trading)
```python
from sim_broker import SimBroker
from config import BacktestConfig
from canonical_schema import create_signal
```

**Problem:** This uses absolute imports that fail when:
1. The strategy is loaded by the Live trading module
2. The Backtest module uses relative imports internally (`.canonical_schema`)
3. Results in: `ImportError: attempted relative import with no known parent package`

### ✅ New Pattern (WORKS EVERYWHERE)
```python
from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig
from Backtest.canonical_schema import create_signal
```

**Benefits:**
1. ✅ Works in backtesting mode
2. ✅ Works in live trading mode
3. ✅ Works when strategy is imported dynamically
4. ✅ Works with the Backtest package's internal relative imports

## Strategy Template

Use this template for all AI-generated strategies:

```python
# MUST NOT EDIT SimBroker
"""
Strategy: {STRATEGY_NAME}
Description: {STRATEGY_DESCRIPTION}
Generated: {DATE}
"""

# Add parent directory to path for imports
import sys
from pathlib import Path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig
from Backtest.canonical_schema import create_signal, OrderSide, OrderAction, OrderType
from Backtest.data_loader import load_market_data
from datetime import datetime
import pandas as pd


class {STRATEGY_NAME}:
    """
    {STRATEGY_DESCRIPTION}
    """
    
    def __init__(self, broker: SimBroker):
        """Initialize strategy with broker instance"""
        self.broker = broker
        self.position = None
        
    def on_bar(self, timestamp: datetime, data: dict):
        """
        Called for each bar of data
        
        Args:
            timestamp: Current bar timestamp
            data: Dictionary with keys 'open', 'high', 'low', 'close', 'volume'
        """
        # Your strategy logic here
        pass


def run_backtest():
    """Complete backtesting runner"""
    # Configuration
    config = BacktestConfig(
        starting_balance=10000.0,
        commission_pct=0.1,
        slippage_pct=0.05
    )
    
    # Load data
    df = load_market_data(
        symbol='AAPL',
        from_ts='2023-01-01',
        to_ts='2024-01-01',
        timeframe='1d',
        indicators=['RSI', 'SMA_50', 'SMA_200']
    )
    
    # Initialize broker and strategy
    broker = SimBroker(config)
    strategy = {STRATEGY_NAME}(broker)
    
    # Run backtest
    for timestamp, row in df.iterrows():
        data = row.to_dict()
        strategy.on_bar(timestamp, data)
        
        # Step broker forward
        broker.step_to(
            timestamp=timestamp,
            open=row['open'],
            high=row['high'],
            low=row['low'],
            close=row['close']
        )
    
    # Get results
    metrics = broker.compute_metrics()
    print(f"Total Return: {metrics['total_return_pct']:.2f}%")
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {metrics['max_drawdown_pct']:.2f}%")
    
    return metrics


if __name__ == '__main__':
    run_backtest()
```

## Generator Configuration

The `gemini_strategy_generator.py` has been updated to automatically use this pattern. When generating new strategies:

1. The generator template includes the correct import pattern
2. Validation checks accept both old and new import styles
3. All example strategies have been updated as references

## Migration Guide

If you have existing strategies with old imports:

### Quick Fix
Replace the import section with:

```python
# Add parent directory to path for imports
import sys
from pathlib import Path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig
from Backtest.canonical_schema import create_signal, OrderSide, OrderAction, OrderType
from Backtest.data_loader import load_market_data
```

### Verification
Test your strategy works in both modes:

```bash
# Test backtesting
cd Backtest/codes
python your_strategy.py

# Test live trading (dry-run)
cd Live
python live_trader.py --strategy ..\Backtest\codes\your_strategy.py --dry-run
```

## Reference Examples

All these strategies use the correct import pattern:
- `Backtest/example_strategy.py` - Moving average crossover
- `Backtest/rsi_strategy.py` - RSI-based strategy
- `Backtest/ema_strategy.py` - EMA crossover
- `Backtest/example_gemini_strategy.py` - Momentum strategy
- `Backtest/codes/my_strategy.py` - Your generated strategy

## Troubleshooting

### Error: `ImportError: attempted relative import with no known parent package`
**Solution:** Update imports to use `from Backtest.module import ...` pattern

### Error: `ModuleNotFoundError: No module named 'Backtest'`
**Solution:** Ensure the path setup code is included:
```python
import sys
from pathlib import Path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
```

### Error: `ModuleNotFoundError: No module named 'canonical_schema'`
**Solution:** You're using old imports. Update to `from Backtest.canonical_schema import ...`

## Summary

✅ **Always use:** `from Backtest.module import ...`  
❌ **Never use:** `from module import ...` (in strategies)

This ensures your strategies work seamlessly in both backtesting and live trading environments.
