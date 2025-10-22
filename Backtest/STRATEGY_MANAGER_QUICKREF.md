# Strategy Manager - Quick Reference Card

## One-Line Summary
Automatically detect JSON strategies and generate Python backtest code.

## Essential Commands

```bash
# Check what strategies exist and which need code
python strategy_manager.py --status

# Generate all missing Python implementations
python strategy_manager.py --generate

# Run a specific strategy backtest
python strategy_manager.py --run strategy_name

# Run all strategy backtests
python strategy_manager.py --run-all
```

## Windows Shortcuts

```batch
strategy_manager.bat status        # Check status
strategy_manager.bat generate      # Generate code
strategy_manager.bat run NAME      # Run one
strategy_manager.bat run-all       # Run all
```

## File Convention

```
codes/my_strategy.json  →  codes/my_strategy.py
      (definition)              (generated code)
```

**Rule**: JSON stem = Python stem

## Typical Workflow

```bash
# 1. Strategy Module creates JSON
# → Saved to: Backtest/codes/new_strategy.json

# 2. Check status
cd Backtest
python strategy_manager.py --status
# Output: ✗ new_strategy (MISSING)

# 3. Generate code
python strategy_manager.py --generate
# Output: ✓ Generated new_strategy.py

# 4. Run backtest
python strategy_manager.py --run new_strategy
# Output: [backtest results...]
```

## Status Indicators

- `✓` - Python code exists
- `✗` - Python code missing (needs generation)

## Quick Checks

```bash
# How many strategies total?
python strategy_manager.py --status | grep "Total Strategies"

# Which ones are missing?
python strategy_manager.py --status | grep "✗"

# Generate and run in one go
python strategy_manager.py --generate && python strategy_manager.py --run-all
```

## Setup (First Time Only)

```bash
# 1. Install Gemini package (for generation)
pip install google-generativeai

# 2. Set API key
# In .env file:
GEMINI_API_KEY=your_key_here

# Or in PowerShell:
$env:GEMINI_API_KEY="your_key_here"
```

## Common Tasks

### Add New Strategy
1. Create JSON in `codes/` folder (or use Strategy module)
2. Run `python strategy_manager.py --generate`
3. Run `python strategy_manager.py --run strategy_name`

### Update Strategy
1. Edit JSON file
2. Regenerate: `python strategy_manager.py --generate --force`
3. Test: `python strategy_manager.py --run strategy_name`

### Batch Generate
```bash
# Generate all missing strategies at once
python strategy_manager.py --generate
```

### Check Before Running
```bash
# See what's ready to run
python strategy_manager.py --status
# Only strategies with ✓ can be run
```

## Files Location

```
AlgoAgent/
└── Backtest/
    ├── strategy_manager.py        ← Main script
    ├── strategy_manager.bat       ← Windows helper
    ├── STRATEGY_MANAGER.md        ← Full guide
    └── codes/
        ├── strategy1.json         ← Definition
        ├── strategy1.py           ← Generated code
        ├── strategy2.json
        └── strategy2.py
```

## Integration

### From Strategy Module
```python
# Strategy module creates JSON → automatically detected
from canonical_schema import CanonicalStrategy
strategy = create_strategy("Buy when RSI < 30")
save_to_json("codes/rsi_strategy.json")
# → Run: python strategy_manager.py --generate
```

### To Live Trading
```python
# After backtest validation
from Backtest.codes.rsi_strategy import RsiStrategy
# Use in live trading
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "No strategies found" | Add JSON files to `codes/` |
| "Failed to generate" | Check GEMINI_API_KEY is set |
| "Strategy not found" | Use filename without `.py` |
| "No strategy class" | Check Python file has class |

## Help & Documentation

```bash
# Built-in help
python strategy_manager.py --help

# Full documentation
cat STRATEGY_MANAGER.md

# Implementation details
cat STRATEGY_MANAGER_IMPLEMENTATION.md

# Test the system
python test_strategy_manager.py
```

## Best Practices

1. ✅ Always run `--status` first to see current state
2. ✅ Review generated code before running backtests
3. ✅ Commit both JSON and Python files to version control
4. ✅ Use `--generate` without `--force` to preserve manual edits
5. ✅ Test individual strategies before `--run-all`

## Quick Tips

💡 **Tip 1**: Use descriptive filenames
```
good: ema_crossover_50_200.json
bad:  strat1.json
```

💡 **Tip 2**: Check status frequently
```bash
# Before any operation
python strategy_manager.py --status
```

💡 **Tip 3**: Generate incrementally
```bash
# Add one strategy, generate, test
# Then add next strategy
```

💡 **Tip 4**: Use batch file on Windows
```batch
REM Simpler than typing Python commands
strategy_manager.bat status
```

💡 **Tip 5**: Check test file for examples
```bash
python test_strategy_manager.py
```

## Advanced Usage

### Custom Directory
```bash
python strategy_manager.py --codes-dir /path/to/strategies --status
```

### Force Regenerate All
```bash
# Regenerate even if Python exists
python strategy_manager.py --generate --force
```

### Programmatic Usage
```python
from strategy_manager import StrategyManager

manager = StrategyManager()
status = manager.check_strategy_status()
results = manager.generate_missing_strategies()
```

## Output Example

```
$ python strategy_manager.py --status

================================================================================
STRATEGY STATUS REPORT
================================================================================
Codes Directory: C:\...\Backtest\codes
Total Strategies: 3
================================================================================

✓ Implemented: 2
✗ Missing Code: 1

--------------------------------------------------------------------------------

1. ✓ EMA Crossover Strategy
   JSON: ema_crossover.json
   Python: ema_crossover.py (exists)
   Strategy ID: strat-20251022-001
   Created: 2025-10-22T00:00:00

2. ✗ RSI Oversold Strategy
   JSON: rsi_oversold.json
   Python: rsi_oversold.py (MISSING)
   Strategy ID: strat-20251022-002
   Created: 2025-10-22T01:00:00

================================================================================
```

## Remember

🔑 **Key Point**: JSON filename stem MUST match Python filename stem

📁 **Location**: Always run from `Backtest/` directory

🔄 **Workflow**: Create JSON → Generate Python → Run Backtest

📚 **Docs**: See `STRATEGY_MANAGER.md` for complete guide

---

*For full documentation, see STRATEGY_MANAGER.md*
*For implementation details, see STRATEGY_MANAGER_IMPLEMENTATION.md*
