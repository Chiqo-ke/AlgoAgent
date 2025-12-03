# Bot Execution & Testing Integration Guide
## Automated Testing of AI-Generated Trading Strategies

**Last Updated**: December 3, 2025  
**Version**: 1.0.0

---

## Overview

The system now **automatically executes newly created bots and captures results** for future reference and analysis. When the agent generates a trading strategy, it can immediately run and test it, then store detailed metrics and logs.

### Key Features

✅ **Automatic Execution** - Run bot immediately after generation  
✅ **Result Capture** - Extract key metrics from execution output  
✅ **Persistent Storage** - Save results to logs, JSON, metrics files, and database  
✅ **Performance History** - Track performance across multiple runs  
✅ **Summary Reports** - Generate readable metrics summaries  
✅ **Error Handling** - Graceful degradation with detailed error logging  

---

## Architecture

### Components

#### 1. **BotExecutor** (`Backtest/bot_executor.py`)
Main class that handles bot execution and result management.

**Responsibilities:**
- Execute Python bot files as subprocesses
- Capture stdout/stderr output
- Parse execution results and metrics
- Store results to disk (logs, JSON, metrics files)
- Maintain SQLite database of execution history
- Generate performance summaries

**Key Methods:**
```python
execute_bot()                  # Run a bot and capture results
get_strategy_history()         # Retrieve execution history for strategy
get_all_executions()          # Get recent execution results
get_performance_summary()     # Get overall performance statistics
```

#### 2. **GeminiStrategyGenerator Integration**
Updated `gemini_strategy_generator.py` to support auto-execution.

**Updated Methods:**
```python
generate_and_save()           # Generate, save, and optionally execute bot
```

**New Parameters:**
- `execute_after_generation` - Boolean to enable auto-execution
- `test_symbol` - Symbol for testing (default: AAPL)
- `test_period_days` - Historical data period (default: 365)

#### 3. **BotExecutionResult** (Data Structure)
Dataclass containing complete execution result information.

**Fields:**
```
strategy_name              # Name of the strategy
file_path                  # Path to Python file
execution_timestamp        # When it was executed
success                    # True/False if successful
duration_seconds           # How long execution took
error                      # Error message if failed
return_pct                 # Total return percentage
trades                     # Number of trades generated
win_rate                   # Percentage of winning trades
max_drawdown              # Maximum drawdown %
sharpe_ratio              # Risk-adjusted return metric
output_log                # Full stdout/stderr output
results_file              # Path to saved results
json_results              # Parsed JSON results
```

---

## Usage Examples

### 1. Basic Bot Execution (After Generation)

```python
from Backtest.gemini_strategy_generator import GeminiStrategyGenerator
from Backtest.bot_executor import get_bot_executor

# Generate strategy and execute it
generator = GeminiStrategyGenerator()
output_file, execution_result = generator.generate_and_save(
    description="Buy when RSI < 30, sell when RSI > 70",
    output_path="Backtest/codes/rsi_strategy.py",
    strategy_name="RSIStrategy",
    execute_after_generation=True,  # <-- Enable auto-execution
    test_symbol="AAPL",
    test_period_days=365
)

# Check execution results
if execution_result:
    if execution_result.success:
        print(f"✓ Bot ran successfully!")
        print(f"  Return: {execution_result.return_pct:.2f}%")
        print(f"  Trades: {execution_result.trades}")
    else:
        print(f"✗ Bot execution failed: {execution_result.error}")
```

### 2. Manual Bot Execution

```python
from Backtest.bot_executor import get_bot_executor

executor = get_bot_executor()

result = executor.execute_bot(
    strategy_file="Backtest/codes/rsi_strategy.py",
    strategy_name="RSIStrategy",
    description="RSI-based entry/exit strategy",
    test_symbol="AAPL",
    test_period_days=365
)

print(f"Status: {result.status if result.success else 'FAILED'}")
print(f"Return: {result.return_pct:.2f}%")
print(f"Results saved to: {result.results_file}")
```

### 3. View Execution History

```python
from Backtest.bot_executor import get_bot_executor

executor = get_bot_executor()

# Get history for specific strategy
history = executor.get_strategy_history("RSIStrategy")

for run in history:
    print(f"Run: {run.execution_timestamp}")
    print(f"  Status: {'✓' if run.success else '✗'}")
    print(f"  Return: {run.return_pct:.2f}%")
    print(f"  Trades: {run.trades}")
```

### 4. View Performance Summary

```python
from Backtest.bot_executor import get_bot_executor

executor = get_bot_executor()

summary = executor.get_performance_summary()

print(f"Total Executions: {summary['total_executions']}")
print(f"Success Rate: {summary['success_rate']:.1%}")
print(f"Avg Return: {summary['avg_return_pct']:.2f}%")
print(f"Avg Trades: {summary['avg_trades']:.0f}")
print(f"Avg Win Rate: {summary['avg_win_rate']:.1%}")
print(f"Avg Sharpe: {summary['avg_sharpe_ratio']:.2f}")
```

---

## Command Line Usage

### Generate and Execute Bot

```bash
# Generate strategy and auto-execute it
python Backtest/gemini_strategy_generator.py \
    "Buy when RSI < 30, sell when RSI > 70" \
    --execute \
    --name RSIStrategy \
    --symbol AAPL \
    --days 365

# With output file
python Backtest/gemini_strategy_generator.py \
    "Moving average crossover strategy" \
    --execute \
    -o strategies/ma_crossover.py \
    -n MAStrategy
```

### Execute Existing Bot

```bash
# Run a specific bot and capture results
python Backtest/bot_executor.py Backtest/codes/my_strategy.py \
    --name MyStrategy \
    --symbol AAPL \
    --days 365 \
    --timeout 300

# Show execution history
python Backtest/bot_executor.py \
    --history \
    --name MyStrategy

# Show performance summary
python Backtest/bot_executor.py \
    --summary
```

---

## Result Storage Structure

Results are stored in `Backtest/codes/results/`:

```
results/
├── execution_history.db          # SQLite database of all executions
├── logs/
│   ├── RSIStrategy_20251203_123456.log    # Full execution output
│   └── MAStrategy_20251203_124512.log
├── metrics/
│   ├── RSIStrategy_20251203_123456.txt    # Formatted metrics
│   └── MAStrategy_20251203_124512.txt
└── json/
    ├── RSIStrategy_20251203_123456.json   # Parsed results JSON
    └── MAStrategy_20251203_124512.json
```

### Example Metrics File

```
======================================================================
Bot Execution Results - RSIStrategy
======================================================================

File: Backtest/codes/rsi_strategy.py
Timestamp: 2025-12-03T12:34:56.789123
Duration: 12.34s
Status: SUCCESS

Description: Buy when RSI < 30, sell when RSI > 70

METRICS:
----------------------------------------------------------------------
  Return: 15.42%
  Trades: 23
  Win Rate: 56.5%
  Max Drawdown: -8.23%
  Sharpe Ratio: 1.45

TEST CONFIGURATION:
----------------------------------------------------------------------
  Symbol: AAPL
  Period: 365 days
```

### Example JSON Result

```json
{
  "strategy_name": "RSIStrategy",
  "file_path": "Backtest/codes/rsi_strategy.py",
  "execution_timestamp": "2025-12-03T12:34:56.789123",
  "success": true,
  "duration_seconds": 12.34,
  "error": null,
  "return_pct": 15.42,
  "trades": 23,
  "win_rate": 0.565,
  "max_drawdown": -8.23,
  "sharpe_ratio": 1.45,
  "test_symbol": "AAPL",
  "test_period_days": 365,
  "description": "Buy when RSI < 30, sell when RSI > 70",
  "parameters": {
    "fast_period": 14,
    "upper_threshold": 70,
    "lower_threshold": 30
  }
}
```

---

## How It Works

### Execution Flow

```
┌─────────────────────────────────────┐
│ Agent generates strategy            │
│ (via GeminiStrategyGenerator)        │
└──────────────┬──────────────────────┘
               │
               ├─ Save to disk
               │
               └─> Check execute flag
                   │
                   ├─ YES: Continue below
                   └─ NO: Return (user runs later)
                        │
┌──────────────────────▼──────────────────────┐
│ BotExecutor.execute_bot()                    │
│ 1. Spawn subprocess for bot file            │
│ 2. Capture stdout/stderr with timeout       │
│ 3. Parse output for metrics                 │
│ 4. Save results to files & database         │
│ 5. Return BotExecutionResult                │
└──────────────┬───────────────────────────────┘
               │
               ├─> logs/strategy_TIMESTAMP.log
               ├─> json/strategy_TIMESTAMP.json
               ├─> metrics/strategy_TIMESTAMP.txt
               └─> SQLite: execution_history.db
                   │
                   └─> Future queries:
                       - get_strategy_history()
                       - get_performance_summary()
```

### Metric Parsing Strategy

The executor tries multiple methods to extract metrics:

1. **JSON Extraction** - Look for JSON blocks in output
2. **Text Pattern Matching** - Search for keywords like "Return:", "Trades:", etc.
3. **Output inspection** - Check for errors, exceptions, empty output

If any metrics are found and no errors detected, execution is marked as successful.

---

## Integration Points

### In Strategy Generator

```python
# Auto-generate and test strategy
output_file, result = generator.generate_and_save(
    description="Your strategy description",
    output_path="Backtest/codes/my_strategy.py",
    execute_after_generation=True  # <-- Trigger execution
)

# Access results immediately
if result and result.success:
    # Use metrics for reporting, optimization, etc.
    performance_metrics = {
        'return': result.return_pct,
        'trades': result.trades,
        'win_rate': result.win_rate,
        'sharpe': result.sharpe_ratio
    }
```

### In Backtesting System

When an agent creates a strategy file:
- Strategy includes `run_backtest()` function
- BotExecutor spawns process and runs that function
- Results captured from stdout/stderr
- Metrics extracted and stored

### For Future Analysis

```python
# Query execution history
executor = get_bot_executor()

# Get all runs for a strategy
history = executor.get_strategy_history("MyStrategy")

# Find best performing run
best_run = max(history, key=lambda x: x.return_pct or -999)

# Get overall statistics
summary = executor.get_performance_summary()
print(f"Success rate: {summary['success_rate']:.1%}")
print(f"Avg return: {summary['avg_return_pct']:.2f}%")
```

---

## Error Handling

### Execution Errors

The executor gracefully handles:

- **Timeout** - Bot takes too long (default 300s timeout)
- **Import Errors** - Missing modules in bot code
- **Runtime Errors** - Exceptions during bot execution
- **Missing Files** - Strategy file not found
- **Invalid Output** - Can't parse results

All errors are:
- Logged with full tracebacks
- Stored in results database
- Included in execution result (`error` field)
- Reported back to user

### Parse Failures

If metrics can't be parsed:
- `success` is set based on output (no errors + some output = success)
- Metrics fields remain `None`
- Full output captured in `output_log`
- User can manually inspect logs for debugging

---

## Configuration

### BotExecutor Options

```python
executor = BotExecutor(
    results_dir="Backtest/codes/results",  # Where to save results
    timeout_seconds=300,                   # Max execution time
    verbose=True                           # Enable detailed logging
)
```

### Generator Options

```python
generator.generate_and_save(
    description="Strategy description",
    output_path="Backtest/codes/my_bot.py",
    execute_after_generation=True,        # Enable auto-execution
    test_symbol="AAPL",                   # Symbol for backtest
    test_period_days=365                  # Period in days
)
```

---

## Monitoring & Logging

### Log Levels

```python
import logging

logging.basicConfig(level=logging.INFO)  # Show info + errors

# Or for debugging
logging.basicConfig(level=logging.DEBUG)  # Show everything
```

### Output Examples

**Successful Execution:**
```
INFO:Backtest.bot_executor:======================================================================
INFO:Backtest.bot_executor:Executing Bot: RSIStrategy
INFO:Backtest.bot_executor:File: Backtest/codes/rsi_strategy.py
INFO:Backtest.bot_executor:======================================================================
INFO:Backtest.bot_executor:Starting execution (timeout: 300s)...
...execution output...
INFO:Backtest.bot_executor:✓ Execution completed successfully
INFO:Backtest.bot_executor:  Return: 15.42%
INFO:Backtest.bot_executor:  Trades: 23
INFO:Backtest.bot_executor:  Win Rate: 56.5%
```

**Failed Execution:**
```
WARNING:Backtest.bot_executor:Execution completed with errors
WARNING:Backtest.bot_executor:  Error: IndexError: list index out of range
ERROR:Backtest.bot_executor:Traceback (most recent call last):
  ...traceback...
```

---

## Database Query Examples

### View All Executions

```sql
SELECT * FROM bot_executions 
ORDER BY execution_timestamp DESC 
LIMIT 10;
```

### Get Performance by Strategy

```sql
SELECT 
    strategy_name,
    COUNT(*) as runs,
    AVG(return_pct) as avg_return,
    AVG(win_rate) as avg_win_rate,
    MAX(return_pct) as best_return
FROM bot_executions
GROUP BY strategy_name
ORDER BY avg_return DESC;
```

### Find Failed Executions

```sql
SELECT 
    strategy_name,
    execution_timestamp,
    error
FROM bot_executions
WHERE success = 0
ORDER BY execution_timestamp DESC;
```

### Success Rate Trend

```sql
SELECT 
    DATE(execution_timestamp) as date,
    COUNT(*) as total,
    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
    ROUND(100.0 * SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) as success_rate
FROM bot_executions
GROUP BY DATE(execution_timestamp)
ORDER BY date DESC;
```

---

## Best Practices

### 1. Always Capture Results

```python
# ✓ Good - Results are captured and stored
output_file, result = generator.generate_and_save(
    description="...",
    output_path="...",
    execute_after_generation=True
)

# ✗ Bad - No execution feedback
generator.generate_and_save(
    description="...",
    output_path="..."
)
```

### 2. Check Results Before Use

```python
# ✓ Good - Verify success before using metrics
if result and result.success:
    print(f"Return: {result.return_pct:.2f}%")
else:
    print(f"Error: {result.error if result else 'No execution'}")

# ✗ Bad - Assumes success
metrics = result.return_pct  # Could be None!
```

### 3. Set Appropriate Timeout

```python
# ✓ Good - Timeout based on expected duration
# Simple strategy: 60-120 seconds
# Complex strategy: 180-300 seconds
executor = BotExecutor(timeout_seconds=300)

# ✗ Bad - Too short timeout
executor = BotExecutor(timeout_seconds=10)  # Likely to fail
```

### 4. Use Descriptive Names

```python
# ✓ Good - Descriptive names for tracking
result = executor.execute_bot(
    strategy_file="...",
    strategy_name="RSI_OVERBOUGHT_14",
    description="RSI < 30 entry, > 70 exit with period 14"
)

# ✗ Bad - Vague names
result = executor.execute_bot(
    strategy_file="...",
    strategy_name="strategy1"
)
```

### 5. Monitor Execution History

```python
# ✓ Good - Regularly check performance
summary = executor.get_performance_summary()
if summary['success_rate'] < 0.9:
    print("⚠️ Alert: Success rate dropped!")

history = executor.get_strategy_history("MyStrategy")
recent_return = history[0].return_pct
if recent_return < -10:
    print("⚠️ Alert: Large drawdown detected!")
```

---

## Troubleshooting

### Issue: "BotExecutor not available"

**Cause:** Import failed due to missing dependencies

**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: Bot execution times out

**Cause:** Strategy takes longer than timeout period

**Solution:**
```python
# Increase timeout
executor = BotExecutor(timeout_seconds=600)  # 10 minutes
```

### Issue: Metrics not parsed

**Cause:** Bot output format doesn't match parser

**Solution:**
1. Check bot's `print()` statements match expected format
2. Review captured logs in `results/logs/`
3. Add explicit JSON output to bot's `run_backtest()` function:

```python
def run_backtest():
    # ... backtest code ...
    
    # Add explicit JSON output
    results = {
        'return_pct': 15.42,
        'trades': 23,
        'win_rate': 0.565,
        'max_drawdown': -8.23,
        'sharpe_ratio': 1.45
    }
    print(json.dumps(results))
```

### Issue: Database locked

**Cause:** Multiple processes writing to database

**Solution:** SQLite handles concurrency, but if issues persist:
- Wait for other processes to complete
- Use single executor instance
- Increase timeout for database operations

---

## Next Steps

1. **Generate your first bot** with auto-execution enabled
2. **Check results** in `Backtest/codes/results/`
3. **Review metrics** for performance insights
4. **Query history** to track improvements over time
5. **Optimize** strategies based on historical data

---

## Summary

The bot execution system provides:

✅ **Automated Testing** - Run bots immediately after generation  
✅ **Result Persistence** - Store execution history for analysis  
✅ **Performance Tracking** - Monitor metrics across multiple runs  
✅ **Error Handling** - Graceful degradation with detailed logging  
✅ **Easy Integration** - Works seamlessly with existing code  
✅ **Future Reference** - Query any past execution anytime  

**The agent now has complete visibility into bot performance and can use historical data to improve strategy generation!**
