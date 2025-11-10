# Strategy Validator System - Quick Start Guide

## Overview

The Strategy Validator System is a complete implementation of the StrategyValidatorBot specification. It provides:

✅ **Multi-format input parsing** (free text, numbered steps, URLs)  
✅ **Canonical JSON schema** for standardized strategy representation  
✅ **Security guardrails** to detect scams and dangerous patterns  
✅ **Smart recommendations** with prioritized, actionable suggestions  
✅ **Provenance tracking** for full audit trail  
✅ **Automatic classification** of strategy type and risk tier  
✅ **Confidence assessment** based on completeness  

## Installation

```bash
cd c:\Users\nyaga\Documents\AlgoAgent\Strategy

# Install dependencies
pip install jsonschema pytest

# Or using the project virtual environment
C:/Users/nyaga/Documents/AlgoAgent/.venv/Scripts/python.exe -m pip install jsonschema pytest
```

## Quick Examples

### Example 1: Python API

```python
from strategy_validator import StrategyValidatorBot

# Initialize bot
bot = StrategyValidatorBot(username="your_username")

# Process a strategy
result = bot.process_input("""
Buy 100 shares when 50 EMA crosses above 200 EMA. 
Set stop loss at 1% below entry. 
Take profit at 2% above entry.
""")

# Get formatted output
if result["status"] == "success":
    print(bot.get_formatted_output())
    
    # Access specific components
    steps = result["canonicalized_steps"]
    recommendations = result["recommendations_list"]
    json_payload = result["canonical_json"]
```

### Example 2: Command Line

```bash
# Interactive mode
python validator_cli.py --interactive

# Process from text
python validator_cli.py --text "Buy when EMA crosses, sell at 2% profit"

# List examples
python validator_cli.py --examples

# Run example
python validator_cli.py --example 1
```

### Example 3: Run Demo

```bash
# Run the full demo
python demo.py
```

## Module Structure

| Module | Purpose |
|--------|---------|
| `canonical_schema.py` | JSON schema definition and validation |
| `input_parser.py` | Parse various input formats |
| `provenance_tracker.py` | Track sources and metadata |
| `recommendation_engine.py` | Generate recommendations |
| `guardrails.py` | Security and safety checks |
| `strategy_validator.py` | Main orchestrator (StrategyValidatorBot) |
| `system_prompt.py` | System prompts and conversation patterns |
| `examples.py` | Example strategies for testing |
| `test_strategy_validator.py` | Comprehensive test suite |
| `validator_cli.py` | Command-line interface |
| `demo.py` | Demo script |

## Running Tests

```bash
# Run all tests
pytest test_strategy_validator.py -v

# Run specific test class
pytest test_strategy_validator.py::TestStrategyValidator -v

# Run specific test
pytest test_strategy_validator.py::TestCanonicalSchema::test_create_minimal_example -v

# With coverage
pytest test_strategy_validator.py --cov=. --cov-report=html
```

## Output Format

The validator returns:

1. **Canonicalized Steps** - Human-readable numbered list
2. **Classification & Meta** - Strategy type, risk tier, instruments
3. **Recommendations** - Prioritized suggestions with rationale
4. **Confidence & Next Actions** - Confidence level and available actions
5. **JSON Payload** - Canonical strategy in JSON format

## Security Features

The system includes:

- ✅ Scam detection (pump-and-dump, guaranteed profits)
- ✅ Dangerous operation warnings (unlimited risk, excessive leverage)
- ✅ Credential request blocking
- ✅ Live trading approval gates
- ✅ Position sizing validation

## Supported Input Formats

### Free Text
```
Buy 100 shares when price breaks above resistance. Set stop at 2%.
```

### Numbered Steps
```
1. Buy when RSI < 30
2. Sell when RSI > 70
3. Stop loss at 2%
```

### URL References
```
https://youtube.com/watch?v=abc123 - analyze this strategy
```

## Configuration

### Strict Mode
Raises exceptions on security violations:
```python
bot = StrategyValidatorBot(username="user", strict_mode=True)
```

### Custom Username
For provenance tracking:
```python
bot = StrategyValidatorBot(username="trader123")
```

## Common Use Cases

### Use Case 1: Validate User-Submitted Strategy
```python
user_input = request.form.get('strategy')
result = validate_strategy(user_input, username=current_user.id)

if result["status"] == "success":
    # Store canonical JSON in database
    db.save_strategy(result["canonical_json"])
    
    # Show recommendations to user
    return render_template('recommendations.html', 
                          recommendations=result["recommendations_list"])
```

### Use Case 2: Batch Processing
```python
strategies_file = "strategies.txt"
with open(strategies_file, 'r') as f:
    for line in f:
        result = validate_strategy(line.strip())
        # Process result...
```

### Use Case 3: API Endpoint
```python
@app.route('/api/validate', methods=['POST'])
def validate_endpoint():
    strategy_text = request.json.get('strategy')
    bot = StrategyValidatorBot(username=request.user.id)
    result = bot.process_input(strategy_text)
    return jsonify(result)
```

## Next Steps

1. ✅ **Test the system**: Run `python demo.py`
2. ✅ **Run unit tests**: Run `pytest test_strategy_validator.py -v`
3. 🔄 **Try the CLI**: Run `python validator_cli.py --interactive`
4. 🔄 **Implement content_fetcher**: Add URL content fetching for YouTube/web articles
5. 🔄 **Integrate with backtesting**: Connect to your backtesting engine
6. 🔄 **Build UI**: Create web interface for strategy validation

## Troubleshooting

### Import Error
```
ModuleNotFoundError: No module named 'jsonschema'
```
**Solution**: Install dependencies: `pip install jsonschema`

### Path Issues
**Solution**: Use absolute imports or add Strategy directory to PYTHONPATH

### Classification Issues
**Solution**: Add more specific keywords to your strategy description

## Support

- 📖 See `README.md` for detailed documentation
- 🧪 See `test_strategy_validator.py` for usage examples
- 🎯 See `examples.py` for example strategies
- 💻 See `demo.py` for working demos

## Production Checklist

Before deploying to production:

- [ ] Run full test suite
- [ ] Enable strict mode for security
- [ ] Set up logging and monitoring
- [ ] Configure rate limiting
- [ ] Add database persistence
- [ ] Implement user authentication
- [ ] Add approval workflows for live trading
- [ ] Set up backup and recovery
- [ ] Document API endpoints
- [ ] Create user documentation

---

**Status**: ✅ All core modules implemented and tested  
**Last Updated**: October 14, 2025  
**Version**: 0.1.0
