# Bot Execution Quick Reference

## Overview

The agent now **automatically tests bots after creation** and stores results for future reference.

---

## Key Features

✅ Auto-execute bots immediately after generation  
✅ Capture execution output and metrics  
✅ Store results in logs, JSON, metrics, and database  
✅ Query execution history anytime  
✅ Get performance summaries  
✅ Timeout protection for long-running strategies  

---

## Quick Start

### 1️⃣ Generate Strategy with Auto-Execution

**Python Code:**
```python
from Backtest.gemini_strategy_generator import GeminiStrategyGenerator

generator = GeminiStrategyGenerator()
output_file, result = generator.generate_and_save(
    description="RSI strategy: buy < 30, sell > 70",
    output_path="Backtest/codes/rsi_bot.py",
    execute_after_generation=True  # <-- Enable execution
)

if result and result.success:
    print(f"✓ Bot returned {result.return_pct:.2f}%")
    print(f"  Trades: {result.trades}")
else:
    print(f"✗ Error: {result.error if result else 'No execution'}")
```

**Command Line:**
```bash
python Backtest/gemini_strategy_generator.py \
    "RSI strategy: buy < 30, sell > 70" \
    --execute \
    --name RSIBot
```

### 2️⃣ Execute Existing Bot

**Python Code:**
```python
from Backtest.bot_executor import get_bot_executor

executor = get_bot_executor()
result = executor.execute_bot(
    strategy_file="Backtest/codes/my_bot.py",
    strategy_name="MyBot"
)

print(f"Status: {result.status}")
print(f"Return: {result.return_pct:.2f}%")
```

**Command Line:**
```bash
python Backtest/bot_executor.py Backtest/codes/my_bot.py --name MyBot
```

### 3️⃣ View Results

**Get History:**
```python
executor = get_bot_executor()
history = executor.get_strategy_history("MyBot")

for run in history[:5]:  # Last 5 runs
    print(f"{run.execution_timestamp}: {run.return_pct:.2f}%")
```

**Command Line:**
```bash
python Backtest/bot_executor.py --history --name MyBot
```

**Get Summary:**
```python
summary = executor.get_performance_summary()
print(f"Success Rate: {summary['success_rate']:.1%}")
print(f"Avg Return: {summary['avg_return_pct']:.2f}%")
```

**Command Line:**
```bash
python Backtest/bot_executor.py --summary
```

---

## Results Storage

All results saved to: `Backtest/codes/results/`

```
results/
├── execution_history.db          # Database of all runs
├── logs/
│   └── Strategy_20251203_123456.log    # Full output
├── metrics/
│   └── Strategy_20251203_123456.txt    # Formatted metrics
└── json/
    └── Strategy_20251203_123456.json   # Parsed results
```

---

## Key Options

### generate_and_save()
```python
generator.generate_and_save(
    description="Your strategy",
    output_path="Backtest/codes/bot.py",
    execute_after_generation=True,    # Enable auto-execution
    test_symbol="AAPL",               # Test symbol (default: AAPL)
    test_period_days=365              # Test period (default: 365)
)
```

### execute_bot()
```python
executor.execute_bot(
    strategy_file="Backtest/codes/bot.py",
    strategy_name="MyBot",
    test_symbol="AAPL",
    test_period_days=365,
    save_results=True                 # Save to disk (default: True)
)
```

### BotExecutor()
```python
from Backtest.bot_executor import BotExecutor

executor = BotExecutor(
    results_dir="Backtest/codes/results",  # Results directory
    timeout_seconds=300,                   # Max execution time
    verbose=True                           # Detailed logging
)
```

---

## Result Object

```python
result = executor.execute_bot(...)

# Status
result.success              # True/False
result.error               # Error message if failed
result.duration_seconds    # How long it took

# Metrics
result.return_pct          # Total return percentage
result.trades              # Number of trades
result.win_rate            # Percentage of winning trades
result.max_drawdown        # Maximum drawdown %
result.sharpe_ratio        # Risk-adjusted return

# References
result.results_file        # Path to saved results
result.output_log          # Full stdout/stderr
result.json_results        # Parsed JSON if available
```

---

## Common Patterns

### Generate → Test → Store
```python
from Backtest.gemini_strategy_generator import GeminiStrategyGenerator

gen = GeminiStrategyGenerator()
file, result = gen.generate_and_save(
    description="Your idea",
    output_path="Backtest/codes/strategy.py",
    execute_after_generation=True  # One command!
)

# Immediate feedback
if result:
    print(f"Return: {result.return_pct}%")
    print(f"Results: {result.results_file}")
```

### Compare Multiple Runs
```python
from Backtest.bot_executor import get_bot_executor

executor = get_bot_executor()

# Get all runs for a strategy
history = executor.get_strategy_history("MyStrategy")

# Find best and worst
best = max(history, key=lambda x: x.return_pct or -999)
worst = min(history, key=lambda x: x.return_pct or 999)

print(f"Best: {best.return_pct:.2f}%")
print(f"Worst: {worst.return_pct:.2f}%")
print(f"Avg: {sum(r.return_pct for r in history) / len(history):.2f}%")
```

### Check Success Rate
```python
executor = get_bot_executor()
summary = executor.get_performance_summary()

success_rate = summary['success_rate']
if success_rate < 0.9:
    print("⚠️ Alert: Success rate below 90%!")
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Timeout after 300s" | Increase timeout: `BotExecutor(timeout_seconds=600)` |
| "No metrics parsed" | Check bot's print output format; add JSON output |
| "File not found" | Verify bot file path exists |
| "BotExecutor not available" | Run: `pip install -r requirements.txt` |
| "Database locked" | Wait for other processes; use single executor instance |

---

## File Locations

| Purpose | Path |
|---------|------|
| Bot Executor | `Backtest/bot_executor.py` |
| Results | `Backtest/codes/results/` |
| Database | `Backtest/codes/results/execution_history.db` |
| Example | `example_bot_execution_workflow.py` |
| Guide | `BOT_EXECUTION_INTEGRATION_GUIDE.md` |

---

## One-Liner Examples

```bash
# Generate and execute bot
python Backtest/gemini_strategy_generator.py "Your description" --execute

# Check execution history
python Backtest/bot_executor.py --history --name StrategyName

# View overall performance
python Backtest/bot_executor.py --summary

# Execute specific bot
python Backtest/bot_executor.py Backtest/codes/my_bot.py
```

---

## Integration with Workflow

```
┌─────────────────────────┐
│ Agent has an idea       │
└────────────┬────────────┘
             │
┌────────────▼────────────┐
│ Generate strategy code  │ (GeminiStrategyGenerator)
└────────────┬────────────┘
             │
┌────────────▼────────────────────────┐
│ Execute bot (auto or manual)        │ (BotExecutor)
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│ Capture results & metrics           │
│ - return_pct, trades, win_rate      │
│ - max_drawdown, sharpe_ratio        │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│ Store results for future reference  │
│ - logs/, metrics/, json/            │
│ - execution_history.db              │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│ Query & analyze performance         │
│ - get_strategy_history()            │
│ - get_performance_summary()         │
└─────────────────────────────────────┘
```

---

## Next Steps

1. ✅ Generate a strategy with `--execute`
2. ✅ Check `Backtest/codes/results/` for output
3. ✅ Query execution history with `get_strategy_history()`
4. ✅ Use metrics for optimization and reporting
5. ✅ Track performance over time

---

**The agent now has complete visibility into bot performance!**

For detailed info: See `BOT_EXECUTION_INTEGRATION_GUIDE.md`  
For working examples: Run `python example_bot_execution_workflow.py`
