# AI Developer Agent - Reference Cards

## Overview
Quick reference for commands and scripts available to the AI Developer Agent.

---

## Available Commands

### Strategy Development

```bash
# Generate new strategy
python gemini_strategy_generator.py "description" -o output.py

# Generate and auto-test with AI agent
python ai_developer_agent.py --generate "RSI strategy that buys below 30"

# Test existing strategy
python ai_developer_agent.py --test test_ma_crossover_backtesting_py.py
```

### Strategy Management

```bash
# Check strategy status
python strategy_manager.py --status

# Generate missing implementations
python strategy_manager.py --generate

# Run specific strategy
python strategy_manager.py --run strategy_name

# Run all strategies
python strategy_manager.py --run-all
```

### Interactive Mode

```bash
# Start AI developer in interactive mode
python ai_developer_agent.py --interactive

# Commands in interactive mode:
generate <description>  - Generate and test strategy
test <file>            - Test existing strategy
chat <message>         - Chat with AI
reference              - Show reference cards
save                   - Save session
exit                   - Exit and save
```

---

## Python Script Templates

### 1. Basic backtesting.py Strategy

```python
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.test import SMA
from Backtest.backtesting_adapter import fetch_and_prepare_data

class MyStrategy(Strategy):
    # Parameters
    fast_period = 10
    slow_period = 30
    
    def init(self):
        # Initialize indicators using self.I()
        close = self.data.Close
        self.fast_ma = self.I(SMA, close, self.fast_period)
        self.slow_ma = self.I(SMA, close, self.slow_period)
    
    def next(self):
        # Trading logic
        if crossover(self.fast_ma, self.slow_ma):
            if not self.position:
                self.buy()
        elif crossover(self.slow_ma, self.fast_ma):
            if self.position:
                self.position.close()

def run_backtest():
    # Fetch data
    df = fetch_and_prepare_data('AAPL', '2020-01-01', '2024-01-01')
    
    # Run backtest
    bt = Backtest(df, MyStrategy, cash=10000, commission=.002)
    stats = bt.run()
    print(stats)
    bt.plot()

if __name__ == "__main__":
    run_backtest()
```

### 2. Strategy with Custom Indicators

```python
import pandas as pd
import numpy as np

class RSIStrategy(Strategy):
    rsi_period = 14
    rsi_upper = 70
    rsi_lower = 30
    
    def init(self):
        close = pd.Series(self.data.Close)
        
        # Calculate RSI
        def calc_rsi(prices, period):
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))
        
        self.rsi = self.I(calc_rsi, close, self.rsi_period)
    
    def next(self):
        if self.rsi[-1] < self.rsi_lower:
            if not self.position:
                self.buy()
        elif self.rsi[-1] > self.rsi_upper:
            if self.position:
                self.position.close()
```

### 3. Strategy with Risk Management

```python
class ManagedStrategy(Strategy):
    risk_per_trade = 0.02  # 2% risk per trade
    
    def init(self):
        # Indicators...
        pass
    
    def next(self):
        if not self.position:
            # Entry signal
            if self.entry_condition():
                # Calculate position size
                risk_amount = self.equity * self.risk_per_trade
                stop_loss = self.calculate_stop_loss()
                
                # Size based on risk
                size = risk_amount / (self.data.Close[-1] - stop_loss)
                size = min(size, self.equity / self.data.Close[-1])
                
                self.buy(size=size, sl=stop_loss)
    
    def entry_condition(self):
        # Your entry logic
        return True
    
    def calculate_stop_loss(self):
        # ATR-based or fixed percentage
        return self.data.Close[-1] * 0.98
```

---

## Common Imports

### backtesting.py Framework
```python
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.test import SMA, GOOG  # Built-in indicators and test data
```

### Data Fetching
```python
from Backtest.backtesting_adapter import (
    fetch_and_prepare_data,
    BacktestingAdapter,
    run_backtest_from_canonical
)
from Data.data_fetcher import fetch_historical_data
```

### Indicators
```python
import pandas as pd
import numpy as np
import pandas_ta as ta

# Technical indicators
df['RSI'] = ta.rsi(df['Close'], length=14)
df['MACD'] = ta.macd(df['Close'])
df['BB'] = ta.bbands(df['Close'], length=20)
```

---

## Common Errors and Fixes

### 1. Import Error: Module not found
**Error:**
```
ModuleNotFoundError: No module named 'Backtest'
```

**Fix:**
```python
# Add to top of file
import sys
from pathlib import Path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))
```

### 2. MultiIndex Column Error
**Error:**
```
TypeError: Cannot index by location index with a non-integer key
```

**Fix:**
```python
# Flatten MultiIndex columns
df.columns = df.columns.get_level_values(0)
```

### 3. Missing OHLCV Columns
**Error:**
```
KeyError: 'Close'
```

**Fix:**
```python
# Rename columns to uppercase
df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
# Or use helper
from Backtest.backtesting_adapter import fetch_and_prepare_data
```

### 4. Strategy Not Trading
**Issue:** No trades executed

**Check:**
1. Verify indicators are calculated correctly
2. Check entry/exit conditions are reachable
3. Ensure `self.position` logic is correct
4. Add debug prints: `print(f"Signal: {self.rsi[-1]}")`

### 5. Invalid Size/Price
**Error:**
```
ValueError: size must be positive
```

**Fix:**
```python
# Always validate size
size = max(0.01, min(size, self.equity / self.data.Close[-1]))
```

---

## Backtest Metrics Explained

| Metric | Description | Good Value |
|--------|-------------|------------|
| **Return [%]** | Total return percentage | > 0% |
| **Sharpe Ratio** | Risk-adjusted return | > 1.0 |
| **Max Drawdown [%]** | Largest peak-to-trough decline | < 20% |
| **Win Rate [%]** | Percentage of winning trades | > 50% |
| **# Trades** | Total number of trades | > 10 (statistical significance) |
| **Avg. Trade [%]** | Average return per trade | > 0% |
| **Exposure Time [%]** | Time in market | Varies by strategy |

---

## Best Practices

### 1. Data Quality
- Use at least 2 years of historical data
- Verify OHLCV columns are properly formatted
- Check for missing data or gaps

### 2. Strategy Design
- Start simple, add complexity incrementally
- Use meaningful parameter names
- Add docstrings to explain logic
- Test edge cases (no position, full position, etc.)

### 3. Risk Management
- Always use stop losses
- Limit position size (1-2% risk per trade)
- Consider portfolio heat (total open risk)

### 4. Testing
- Test on multiple symbols
- Use walk-forward analysis
- Compare to buy-and-hold benchmark
- Monitor overfitting (in-sample vs out-of-sample)

### 5. Code Quality
- Use type hints
- Add error handling
- Log important events
- Keep functions small and focused

---

## Quick Troubleshooting

```bash
# Check Python environment
python --version  # Should be 3.10+

# Verify in .venv
python -c "import sys; print(sys.prefix)"
# Should show: C:\Users\nyaga\Documents\AlgoAgent\.venv

# Check installed packages
python -c "import backtesting; print(backtesting.__version__)"

# Test data fetcher
python -c "from Data.data_fetcher import fetch_historical_data; print('OK')"

# Test terminal executor
python Backtest/terminal_executor.py

# Test AI agent
python Backtest/ai_developer_agent.py --help
```

---

## File Structure

```
AlgoAgent/
└── Backtest/
    ├── ai_developer_agent.py          # Main AI agent
    ├── terminal_executor.py           # Terminal command runner
    ├── gemini_strategy_generator.py   # Strategy code generator
    ├── backtesting_adapter.py         # backtesting.py adapter
    ├── strategy_manager.py            # Strategy management
    │
    ├── codes/                         # Generated strategies
    │   ├── test_ma_crossover_backtesting_py.py
    │   └── <your_strategies>.py
    │
    └── logs/                          # Session logs
        └── session_<timestamp>.json
```

---

## Example Workflow

```bash
# 1. Start interactive mode
python Backtest/ai_developer_agent.py --interactive

# 2. Generate a strategy
> generate Buy AAPL when RSI < 30, sell when RSI > 70

# 3. AI will:
#    - Generate code
#    - Test it
#    - Fix errors automatically
#    - Show results

# 4. Test manually if needed
> test my_strategy.py

# 5. Chat for modifications
> chat Can you add a stop loss at 2% below entry?

# 6. Save session
> save
```

---

## Advanced Usage

### Custom Memory Type
```python
from Backtest.ai_developer_agent import AIDeveloperAgent

# Use summary memory for long conversations
agent = AIDeveloperAgent(memory_type="summary")

# Or buffer memory for recent context
agent = AIDeveloperAgent(memory_type="buffer")
```

### Programmatic Usage
```python
# Generate and test
result = agent.generate_and_test_strategy(
    description="EMA crossover strategy",
    strategy_name="ema_cross",
    auto_fix=True
)

# Chat with context
response = agent.chat(
    "Optimize the strategy",
    context={"last_result": result}
)

# Test existing
from pathlib import Path
script = Path("codes/my_strategy.py")
result = agent.test_existing_strategy(script)
```

---

## Support

- Documentation: `BACKTESTING_PY_MIGRATION_COMPLETE.md`
- Quick Start: `AI_DEVELOPER_AGENT_QUICKSTART.md`
- Issues: Check `logs/` folder for session history
- Terminal output: Check stdout/stderr in ExecutionResult

---

**Version:** 1.0.0  
**Last Updated:** 2025-10-31
