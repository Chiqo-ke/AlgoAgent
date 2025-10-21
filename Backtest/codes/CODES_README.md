# Strategy Codes Directory

This directory contains trading strategy definitions and their implementations.

## File Structure

Each strategy consists of two files:
- **JSON file** - Canonical strategy definition (from Strategy module)
- **Python file** - Executable backtest implementation (auto-generated)

Example:
```
ema_crossover.json          # Strategy definition
ema_crossover.py            # Executable code
```

## Automatic Code Generation

The **Strategy Manager** automatically detects JSON files and generates corresponding Python implementations.

### Check Status
```bash
cd ..
python strategy_manager.py --status
```

### Generate Missing Code
```bash
cd ..
python strategy_manager.py --generate
```

### Run Backtest
```bash
cd ..
python strategy_manager.py --run ema_crossover
```

## File Naming Convention

**Rule**: Python filename MUST match JSON filename (stem)

✅ Correct:
- `my_strategy.json` → `my_strategy.py`
- `rsi_30.json` → `rsi_30.py`

❌ Incorrect:
- `my_strategy.json` → `strategy.py` (different name)
- `rsi_30.json` → `rsi_strategy.py` (doesn't match)

## JSON Strategy Format

Strategies follow the canonical schema:

```json
{
  "strategy_id": "strat-20251022-abc123",
  "version": "0.1.0",
  "title": "Strategy Name",
  "description": "What the strategy does",
  "classification": {
    "type": "trend-following",
    "risk_tier": "medium",
    "primary_instruments": ["EMA", "RSI"]
  },
  "steps": [
    {
      "step_id": "s1",
      "order": 1,
      "title": "Entry Signal",
      "trigger": "Condition that starts this step",
      "action": {
        "type": "enter",
        "order_type": "market"
      }
    }
  ],
  "metadata": {
    "created_at": "2025-10-22T00:00:00",
    "created_by": "user:trader"
  }
}
```

## Generated Python Code

Auto-generated Python files include:
- Strategy class with `__init__` and `on_bar` methods
- SimBroker integration
- `run_backtest()` function for execution
- Proper imports and path setup

Example structure:
```python
from sim_broker import SimBroker
from canonical_schema import create_signal, OrderSide

class MyStrategy:
    def __init__(self, broker: SimBroker):
        self.broker = broker
    
    def on_bar(self, timestamp, data):
        # Strategy logic from JSON
        pass

def run_backtest():
    # Backtest setup and execution
    pass

if __name__ == "__main__":
    run_backtest()
```

## Workflow

### 1. Strategy Created (Strategy Module)
Strategy module creates JSON definition:
```
Strategy Module → codes/my_strategy.json
```

### 2. Code Generated (Strategy Manager)
Strategy manager detects and generates:
```
Strategy Manager → codes/my_strategy.py
```

### 3. Backtest Executed
Run the strategy:
```bash
python strategy_manager.py --run my_strategy
```

## Running Strategies

### Individual Strategy
```bash
# From Backtest directory
python strategy_manager.py --run ema_crossover

# Or directly
python codes/ema_crossover.py
```

### All Strategies
```bash
python strategy_manager.py --run-all
```

## Manual Strategy Creation

You can also create strategies manually:

1. Create JSON file following canonical schema
2. Save to this directory
3. Run `python strategy_manager.py --generate`
4. Python code will be auto-generated

## Testing Strategies

Each generated strategy includes:
- Example data generation (if needed)
- Backtest configuration
- Metrics reporting
- Results saving

Run and check:
```bash
python codes/my_strategy.py
# Results saved to: Backtest/results/
```

## Best Practices

1. **Naming**: Use descriptive, lowercase names with underscores
2. **Version Control**: Commit both JSON and Python files
3. **Testing**: Always run generated code before live trading
4. **Review**: Review AI-generated code for correctness
5. **Backup**: Keep backups before regenerating with `--force`

## Troubleshooting

### "Strategy not found"
Ensure JSON file exists and run `--status` to verify

### "No strategy class found"
Check Python file has a class definition (not just functions)

### "Failed to generate"
- Verify Gemini API key is set
- Check JSON file is valid
- Review error message for details

## Integration with Live Trading

Once validated through backtesting:
```python
# In Live module
from Backtest.codes.my_strategy import MyStrategy
```

Strategies can be imported and adapted for live trading.

## Files in This Directory

### test_strategy.py
Example strategy file (manually created for testing)

### *.json
Strategy definitions from Strategy module

### *.py (auto-generated)
Executable backtest implementations

## Related Documentation

- **[../STRATEGY_MANAGER.md](../STRATEGY_MANAGER.md)** - Complete manager guide
- **[../API_REFERENCE.md](../API_REFERENCE.md)** - SimBroker API
- **[../QUICK_START_GUIDE.md](../QUICK_START_GUIDE.md)** - Getting started
- **[../../Strategy/canonical_schema.py](../../Strategy/canonical_schema.py)** - JSON schema

## Support

For issues:
1. Check JSON is valid: use a JSON validator
2. Run `python strategy_manager.py --status`
3. Check logs for detailed error messages
4. Review generated code for issues
