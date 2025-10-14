# Strategy Validator System

A production-ready system for validating, canonicalizing, and analyzing trading strategies. This system implements the StrategyValidatorBot specification with comprehensive safety guardrails and multi-format input support.

## Features

- **Multi-format Input Parsing**: Supports free text, numbered steps, and URLs
- **Canonical Schema**: Standardized JSON schema for strategy representation
- **Security Guardrails**: Detects scams, dangerous patterns, and security violations
- **Smart Recommendations**: Generates prioritized, actionable recommendations
- **Provenance Tracking**: Maintains audit trail of strategy sources
- **Classification**: Automatically classifies strategy type and risk tier
- **Confidence Assessment**: Evaluates strategy completeness and quality

## Module Structure

```
Strategy/
├── canonical_schema.py      # JSON schema definition and validation
├── input_parser.py          # Parse various input formats
├── provenance_tracker.py    # Track sources and metadata
├── recommendation_engine.py # Generate recommendations
├── guardrails.py           # Security and safety checks
├── strategy_validator.py   # Main orchestrator (StrategyValidatorBot)
├── system_prompt.py        # System prompts and conversation patterns
├── examples.py             # Example strategies for testing
├── test_strategy_validator.py # Comprehensive test suite
├── validator_cli.py        # Command-line interface
├── content_fetcher.py      # URL content fetching (existing)
├── input_parser.py         # Input parsing (existing)
├── strategy_parser.py      # Strategy parsing (existing)
└── README.md              # This file
```

## Quick Start

### Python API

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
```

### Command-Line Interface

```bash
# Interactive mode
python validator_cli.py --interactive

# Process from file
python validator_cli.py --file strategy.txt --output result.json

# Process from command line
python validator_cli.py --text "Buy when EMA crosses"

# List examples
python validator_cli.py --examples

# Run specific example
python validator_cli.py --example 1

# Show system prompt
python validator_cli.py --prompt
```

## Usage Examples

### Example 1: Simple Strategy

```python
from strategy_validator import validate_strategy

result = validate_strategy(
    "Buy 100 shares when 50 EMA crosses above 200 EMA",
    username="trader1"
)

print(result["canonicalized_steps"])
print(result["recommendations"])
print(result["canonical_json"])
```

### Example 2: Numbered Steps

```python
strategy_text = """
1. Entry: Buy when RSI < 30
2. Size: Risk 1% of account
3. Exit: Take profit at RSI > 70
4. Stop: 2% below entry
"""

result = validate_strategy(strategy_text)
```

### Example 3: Using the Bot Directly

```python
bot = StrategyValidatorBot(username="trader1")

# Process strategy
result = bot.process_input("Your strategy here...")

# Access components
if result["status"] == "success":
    steps = result["canonicalized_steps"]
    classification = result["classification_detail"]
    recommendations = result["recommendations_list"]
    json_payload = result["canonical_json"]
```

## Output Format

The validator returns a structured response with:

1. **Canonicalized Steps** - Human-readable numbered list
2. **Classification & Meta** - Strategy type, risk tier, data needs
3. **Recommendations** - Prioritized, actionable suggestions
4. **Confidence & Next Actions** - Confidence level and available actions
5. **JSON Payload** - Canonical strategy in JSON format

Example output:
```json
{
  "status": "success",
  "canonicalized_steps": [
    "1. Entry rule — 50 EMA crosses above 200 EMA → enter"
  ],
  "classification": "Type: trend-following, Risk: medium",
  "recommendations": "1. Replace fixed size with dynamic sizing...",
  "confidence": "medium",
  "next_actions": ["Run quick backtest", "Approve -> Generate code"],
  "canonical_json": "{...}",
  "warnings": []
}
```

## Canonical Schema

Strategies are canonicalized into a strict JSON schema:

```json
{
  "strategy_id": "strat-20251014-001",
  "version": "0.1.0",
  "title": "EMA Crossover Simple",
  "description": "Strategy description",
  "classification": {
    "type": "trend-following",
    "risk_tier": "medium",
    "primary_instruments": ["AAPL"]
  },
  "steps": [
    {
      "step_id": "s1",
      "order": 1,
      "title": "Entry rule",
      "trigger": "50 EMA crosses above 200 EMA",
      "action": {
        "type": "enter",
        "order_type": "market",
        "size": {"mode": "fixed", "value": 100}
      },
      "exit": {
        "stop_loss": "1% below entry",
        "take_profit": "2% above entry"
      }
    }
  ],
  "provenance": {
    "sources": [...]
  },
  "metadata": {
    "created_at": "2025-10-14T10:00:00Z",
    "created_by": "user:trader1",
    "confidence": "medium"
  }
}
```

## Security Guardrails

The system includes comprehensive security checks:

- **Scam Detection**: Identifies pump-and-dump schemes, guaranteed profits claims
- **Dangerous Operations**: Warns about unlimited risk, excessive leverage
- **Credential Protection**: Blocks credential requests
- **Live Trading Gate**: Requires explicit approval for live execution
- **Position Sizing Validation**: Ensures reasonable position sizes

## Testing

Run the test suite:

```bash
# Run all tests
pytest test_strategy_validator.py -v

# Run specific test class
pytest test_strategy_validator.py::TestStrategyValidator -v

# Run with coverage
pytest test_strategy_validator.py --cov=. --cov-report=html
```

## Configuration

### System Prompt

The system prompt is defined in `system_prompt.py` and follows the production specification. It includes:

- Behavior principles
- Security guardrails
- Input handling rules
- Output format requirements
- Example conversations

### Strict Mode

Enable strict mode to raise exceptions on security violations:

```python
bot = StrategyValidatorBot(username="user", strict_mode=True)
```

## API Reference

### StrategyValidatorBot

Main class for strategy validation.

```python
bot = StrategyValidatorBot(username="user", strict_mode=False)
result = bot.process_input(user_input, input_type="auto")
formatted = bot.get_formatted_output()
```

### validate_strategy()

Convenience function for quick validation.

```python
result = validate_strategy(
    user_input="strategy text",
    username="user",
    input_type="auto"
)
```

### InputParser

Parse various input formats.

```python
from input_parser import InputParser

parser = InputParser()
result = parser.parse(user_input, input_type="auto")
```

### ProvenanceTracker

Track strategy sources.

```python
from provenance_tracker import ProvenanceTracker

tracker = ProvenanceTracker()
tracker.add_user_input("strategy text", "username")
tracker.add_web_article(url="...", author="...", snippet="...")
```

### RecommendationEngine

Generate recommendations.

```python
from recommendation_engine import RecommendationEngine

engine = RecommendationEngine()
engine.analyze_strategy(strategy_dict)
recommendations = engine.get_recommendations()
```

### Guardrails

Security and safety checks.

```python
from guardrails import Guardrails

guardrails = Guardrails(strict_mode=False)
is_safe, issues = guardrails.check_strategy(strategy_dict, raw_input)
```

## Development

### Adding New Features

1. Create new module in `Strategy/` directory
2. Add tests in `test_strategy_validator.py`
3. Update `strategy_validator.py` to integrate new module
4. Update this README with usage examples

### Contributing

1. Ensure all tests pass
2. Follow existing code style
3. Add tests for new features
4. Update documentation

## Troubleshooting

### Common Issues

**Issue**: "No module named 'canonical_schema'"
**Solution**: Ensure you're running from the correct directory or add Strategy/ to PYTHONPATH

**Issue**: Strategy classified as "unknown"
**Solution**: Add more specific keywords or indicators to your strategy description

**Issue**: Too many warnings
**Solution**: This is expected for incomplete strategies. Follow the recommendations to improve.

## Future Enhancements

- [ ] URL content fetching implementation
- [ ] YouTube/TikTok transcript extraction
- [ ] Multi-language support
- [ ] Visual strategy builder UI
- [ ] Integration with backtesting engine
- [ ] Strategy comparison and version control
- [ ] Machine learning for classification improvement

## License

See project root LICENSE file.

## Contact

For issues and questions, please open a GitHub issue in the AlgoAgent repository.
