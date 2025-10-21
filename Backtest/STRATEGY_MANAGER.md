# Strategy Manager

Automatic strategy code generation and backtest orchestration.

## Overview

The Strategy Manager automates the workflow of converting JSON strategy definitions into executable Python backtests:

1. **Scan** - Finds all JSON strategy files in `codes/` directory
2. **Check** - Determines which strategies have Python implementations
3. **Generate** - Auto-creates missing Python code using Gemini AI
4. **Execute** - Runs backtests on implemented strategies

## Quick Start

### 1. Check Strategy Status

```bash
# Windows
strategy_manager.bat status

# Python
python strategy_manager.py --status
```

Shows:
- All JSON strategy definitions found
- Which ones have Python implementations
- Which ones need to be generated

### 2. Generate Missing Strategies

```bash
# Windows
strategy_manager.bat generate

# Python
python strategy_manager.py --generate
```

Automatically generates Python code for any JSON strategy that doesn't have a `.py` file.

### 3. Run a Backtest

```bash
# Windows
strategy_manager.bat run test_strategy

# Python
python strategy_manager.py --run test_strategy
```

Executes the backtest for `test_strategy.py`.

### 4. Run All Backtests

```bash
# Windows
strategy_manager.bat run-all

# Python
python strategy_manager.py --run-all
```

Runs backtests for all implemented strategies sequentially.

## File Naming Convention

The system automatically matches JSON and Python files:

```
codes/
├── my_strategy.json          # Strategy definition
└── my_strategy.py            # Auto-generated implementation
```

**Rule**: Python filename = JSON filename (with `.py` extension)

## Workflow

### Complete Workflow Example

```bash
# 1. Add JSON strategy to codes/ folder
#    (created by Strategy module or manually)

# 2. Check what needs to be generated
strategy_manager.bat status

# 3. Generate missing Python code
strategy_manager.bat generate

# 4. Run the new strategy
strategy_manager.bat run my_new_strategy

# Or run all strategies
strategy_manager.bat run-all
```

## Command Reference

### Status Command
```bash
python strategy_manager.py --status
```
- Lists all JSON strategies
- Shows which have Python implementations
- Displays strategy metadata (ID, title, created date)

### Generate Command
```bash
python strategy_manager.py --generate [--force]
```
- Generates Python code for strategies without implementations
- `--force`: Regenerate even if Python file exists
- Uses Gemini AI to convert JSON strategy to executable code

### Run Command
```bash
python strategy_manager.py --run STRATEGY_NAME
```
- Runs backtest for specific strategy
- `STRATEGY_NAME`: filename without `.py` extension
- Executes the strategy's `run_backtest()` function

### Run All Command
```bash
python strategy_manager.py --run-all
```
- Runs all implemented strategies sequentially
- Displays summary of results

## Integration with Strategy Module

The Strategy Manager works seamlessly with the Strategy module:

1. **Strategy Module** creates JSON canonical strategies in `codes/`
2. **Strategy Manager** detects new JSON files
3. **Strategy Manager** generates Python implementations
4. **Backtest** executes strategies using SimBroker

### Example Integration Flow

```python
# In Strategy module - creates JSON
strategy_validator = StrategyValidatorBot()
strategy_json = strategy_validator.validate("Buy when RSI < 30")
# Saves to: Backtest/codes/rsi_strategy.json

# In Backtest module - generates Python
from strategy_manager import StrategyManager
manager = StrategyManager()
manager.generate_missing_strategies()
# Creates: Backtest/codes/rsi_strategy.py

# Run backtest
manager.run_backtest(Path("codes/rsi_strategy.py"))
```

## JSON Strategy Format

Your JSON strategies should follow the canonical schema:

```json
{
  "strategy_id": "strat-20251022-abc123",
  "version": "0.1.0",
  "title": "EMA Crossover Strategy",
  "description": "Buy when 50 EMA crosses above 200 EMA",
  "classification": {
    "type": "trend-following",
    "risk_tier": "medium",
    "primary_instruments": ["EMA"]
  },
  "steps": [
    {
      "step_id": "s1",
      "order": 1,
      "title": "Entry Signal",
      "trigger": "50 EMA crosses above 200 EMA",
      "action": {
        "type": "enter",
        "order_type": "market"
      }
    }
  ],
  "metadata": {
    "created_at": "2025-10-22T00:00:00",
    "created_by": "user:trader1"
  }
}
```

## Generated Python Code

The manager generates Python strategies that:
- Import SimBroker and required modules
- Define a strategy class with `__init__` and `on_bar` methods
- Implement the logic from JSON steps
- Include a `run_backtest()` function for easy execution

Example generated structure:

```python
from sim_broker import SimBroker
from config import BacktestConfig, get_realistic_config
from canonical_schema import create_signal, OrderSide
from data_loader import load_market_data

class EMAStrategy:
    def __init__(self, broker: SimBroker):
        self.broker = broker
        # Strategy initialization
    
    def on_bar(self, timestamp, data):
        # Strategy logic from JSON steps
        pass

def run_backtest():
    config = get_realistic_config()
    broker = SimBroker(config)
    strategy = EMAStrategy(broker)
    # Run backtest
```

## Advanced Usage

### Custom Codes Directory

```bash
python strategy_manager.py --codes-dir /path/to/strategies --status
```

### Force Regeneration

Useful after updating Gemini prompts or strategy templates:

```bash
python strategy_manager.py --generate --force
```

### Programmatic Usage

```python
from strategy_manager import StrategyManager

manager = StrategyManager()

# Check status
status = manager.check_strategy_status()
for s in status:
    print(f"{s['title']}: {'✓' if s['has_python'] else '✗'}")

# Generate missing
results = manager.generate_missing_strategies()

# Run specific strategy
from pathlib import Path
manager.run_backtest(Path("codes/my_strategy.py"))
```

## Troubleshooting

### "No strategy class found"
- Ensure generated Python file has a class (not just functions)
- Check that class name doesn't conflict with imports

### "Failed to load JSON"
- Verify JSON is valid (use a JSON validator)
- Check file encoding is UTF-8

### "GEMINI_API_KEY not found"
- Set environment variable: `GEMINI_API_KEY=your_key_here`
- Or create `.env` file in Backtest directory

### Generation fails
- Check Gemini API quota/limits
- Verify internet connection
- Check system prompt in `SYSTEM_PROMPT.md`

## Best Practices

1. **Version Control**: Commit both JSON and generated Python files
2. **Review Generated Code**: Always review AI-generated strategies before trading
3. **Test Incrementally**: Generate and test one strategy at a time first
4. **Backup**: Keep backups before using `--force` regeneration
5. **Naming**: Use descriptive, lowercase filenames with underscores

## Files Created

When you run strategy_manager, these files are managed:

```
Backtest/
├── strategy_manager.py      # Main manager script
├── strategy_manager.bat     # Windows batch wrapper
├── STRATEGY_MANAGER.md      # This file
└── codes/
    ├── strategy1.json       # Strategy definitions
    ├── strategy1.py         # Generated code
    ├── strategy2.json
    └── strategy2.py
```

## Related Documentation

- `API_REFERENCE.md` - SimBroker API documentation
- `SYSTEM_PROMPT.md` - Gemini code generation prompt
- `QUICK_START_GUIDE.md` - Getting started with backtesting
- `../Strategy/canonical_schema.py` - JSON strategy schema

## Support

For issues or questions:
1. Check existing JSON is valid
2. Run with `--status` to see system state
3. Review generated Python code manually
4. Check logs for detailed error messages
