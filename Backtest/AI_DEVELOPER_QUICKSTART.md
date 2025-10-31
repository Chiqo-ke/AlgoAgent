# AI Developer Agent - Quick Start Guide

## Overview

The **AI Developer Agent** is an intelligent assistant that can generate, test, and automatically fix trading strategies. It combines:

- **Gemini AI** for strategy generation
- **Terminal execution** to run strategies in .venv
- **LangChain memory** for conversation context
- **Automatic error fixing** using pattern matching and AI
- **Interactive mode** for iterative development

---

## Installation

### 1. Prerequisites

```bash
# Ensure you're in the AlgoAgent directory
cd C:\Users\nyaga\Documents\AlgoAgent

# Activate virtual environment
.\.venv\Scripts\activate

# Verify installations
python -c "import langchain; print(f'LangChain: {langchain.__version__}')"
python -c "import backtesting; print(f'backtesting.py: {backtesting.__version__}')"
python -c "import google.generativeai as genai; print('Gemini: OK')"
```

### 2. Environment Setup

Make sure your `.env` file contains:
```env
GEMINI_API_KEY=your_api_key_here
```

---

## Quick Start (5 Minutes)

### Method 1: Interactive Mode (Recommended)

```bash
python Backtest/ai_developer_agent.py --interactive
```

Then try these commands:

```
> generate Buy AAPL when RSI < 30, sell when RSI > 70

# AI will:
# 1. Generate the strategy code
# 2. Test it automatically
# 3. Fix any errors
# 4. Show you the results

> test test_ma_crossover_backtesting_py.py

# Test an existing strategy

> chat Can you add stop loss and take profit to the strategy?

# Chat to modify strategies

> reference

# Show all available commands

> save

# Save session for later review
```

### Method 2: Command Line

```bash
# Generate and test a strategy
python Backtest/ai_developer_agent.py --generate "EMA crossover strategy"

# Test existing strategy
python Backtest/ai_developer_agent.py --test test_ma_crossover_backtesting_py.py
```

### Method 3: Programmatic Usage

```python
from Backtest.ai_developer_agent import AIDeveloperAgent

# Create agent
agent = AIDeveloperAgent()

# Generate and test strategy
result = agent.generate_and_test_strategy(
    description="RSI mean reversion strategy",
    strategy_name="rsi_strategy",
    auto_fix=True
)

if result['success']:
    print(f"✅ Strategy created successfully!")
    print(f"Metrics: {result['results']}")
else:
    print(f"❌ Failed: {result.get('error')}")
```

---

## How It Works

### The Test-Fix-Retest Loop

```
1. Generate Strategy
   ↓
2. Test in .venv
   ↓
3. Parse Results
   ↓
4. Errors Found?
   ├─ No → ✅ Done!
   └─ Yes → Fix Code → Go to Step 2
```

### Example Session

```bash
$ python Backtest/ai_developer_agent.py --interactive

> generate Buy when price crosses above 50-day SMA

================================================================================
STEP 1: Generating Strategy
================================================================================
✓ Strategy generated: ai_strategy_20251031_143022.py

================================================================================
STEP 2.1: Testing Strategy (Iteration 1/5)
================================================================================
❌ Execution failed

Errors (1):
  - ModuleNotFoundError: No module named 'Backtest'
    File: ai_strategy_20251031_143022.py, Line: 5

================================================================================
STEP 3.1: Analyzing and Fixing Errors
================================================================================
✓ Code updated with fixes

================================================================================
STEP 2.2: Testing Strategy (Iteration 2/5)
================================================================================
✅ Strategy executed successfully!

Metrics:
  return_pct: 15.23
  sharpe_ratio: 1.45
  max_drawdown_pct: -8.34
  win_rate_pct: 58.0
  trade_count: 12
  symbol: AAPL
```

---

## Features

### 1. Automatic Error Fixing

The agent can automatically fix common errors:

| Error Type | Auto-Fix |
|------------|----------|
| `ModuleNotFoundError` | Adds sys.path setup |
| `KeyError: 'Close'` | Fixes column names |
| MultiIndex columns | Flattens columns |
| Missing imports | Adds required imports |
| Syntax errors | Uses AI to fix |

### 2. Conversation Memory

The agent remembers your conversation:

```
> generate RSI strategy
AI: [Generates strategy]

> chat Add a 2% stop loss
AI: [Remembers the RSI strategy and adds stop loss]

> chat What's the current win rate?
AI: [Recalls the test results from memory]
```

### 3. Reference Cards

Built-in reference for commands and patterns:

```
> reference

{
  "commands": {
    "run_strategy": "python codes/<strategy_name>.py",
    "run_backtest": "python strategy_manager.py --run <name>",
    ...
  },
  "available_scripts": [...],
  "common_imports": {...}
}
```

### 4. Session Logging

All conversations are saved:

```
Backtest/logs/
└── session_20251031_143022.json
```

Load and review later:

```python
import json
with open('logs/session_20251031_143022.json') as f:
    session = json.load(f)
    
for entry in session:
    print(f"User: {entry['user']}")
    print(f"AI: {entry['ai']}")
```

---

## Common Use Cases

### 1. Quick Strategy Testing

```bash
# Generate and test in one command
python Backtest/ai_developer_agent.py --generate "MACD crossover"

# If it works, you'll get:
✅ Strategy successfully created!
Iterations: 2
```

### 2. Iterative Development

```
> generate Simple moving average crossover

> test ai_strategy_*.py

> chat The strategy doesn't trade enough. Can you lower the fast SMA to 5?

> test ai_strategy_*.py
```

### 3. Debugging Existing Code

```
> test my_broken_strategy.py

AI: I found these errors:
  - NameError: 'SMA' is not defined
  
  Suggestions:
  1. Import SMA: from backtesting.test import SMA
  2. Or use pandas_ta: ta.sma()

> chat Fix the SMA import issue
```

### 4. Learning and Exploration

```
> chat What's the difference between Strategy.init() and Strategy.next()?

> chat Show me an example of using RSI indicator

> chat How do I add risk management to a strategy?
```

---

## Advanced Configuration

### Custom Memory Type

```python
# Use summary memory for long conversations (memory efficient)
agent = AIDeveloperAgent(memory_type="summary")

# Use buffer memory for full context (more accurate)
agent = AIDeveloperAgent(memory_type="buffer")
```

### Adjust Max Iterations

```python
# Allow more fix attempts
agent = AIDeveloperAgent(max_iterations=10)
```

### Disable Auto-Fix

```bash
# Generate without auto-fixing (you fix manually)
python Backtest/ai_developer_agent.py --generate "RSI strategy" --no-fix
```

---

## Troubleshooting

### Issue: "GEMINI_API_KEY not found"

**Solution:**
```bash
# Check .env file
cat .env | grep GEMINI_API_KEY

# Or set manually
export GEMINI_API_KEY=your_key_here  # Linux/Mac
$env:GEMINI_API_KEY="your_key_here"  # PowerShell
```

### Issue: "Python executable not found"

**Solution:**
```bash
# Make sure .venv exists
ls .venv

# Recreate if needed
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### Issue: Agent generates broken code

**Possible causes:**
1. Prompt is too vague → Be more specific
2. Max iterations too low → Increase max_iterations
3. Complex strategy → Break into simpler parts

**Solutions:**
```
# Bad prompt:
> generate trading strategy

# Good prompt:
> generate Buy AAPL when 10-day SMA crosses above 30-day SMA, sell on opposite crossover

# Very good prompt:
> generate A momentum strategy that buys when price breaks above 20-day high with volume > average volume, hold for 5 days or until price drops 2%
```

### Issue: Tests take too long

**Solution:**
```python
# Use shorter date range in strategy
df = fetch_and_prepare_data('AAPL', '2023-01-01', '2024-01-01')  # 1 year

# Or set timeout
executor = TerminalExecutor()
result = executor.run_script(script, timeout=60)  # 60 seconds
```

---

## Best Practices

### 1. Start Simple

```
✅ Good: "Buy when RSI < 30"
❌ Too complex: "Multi-timeframe MACD with volume-weighted price action and adaptive position sizing"
```

### 2. Test Incrementally

```
1. Generate basic strategy
2. Test it
3. Add one feature (e.g., stop loss)
4. Test again
5. Add next feature
```

### 3. Use Descriptive Names

```python
# Good
agent.generate_and_test_strategy(
    description="RSI mean reversion",
    strategy_name="rsi_mean_reversion_v1"
)

# Bad
agent.generate_and_test_strategy(
    description="RSI",
    strategy_name="strat"
)
```

### 4. Save Sessions Regularly

```
> save   # Save after important work

# Or auto-save on exit
> exit   # Automatically saves
```

### 5. Review Logs

Check `Backtest/logs/` to see:
- What prompts worked well
- How many iterations were needed
- What errors occurred
- AI's reasoning

---

## Integration with Existing Tools

### With strategy_manager.py

```bash
# Generate with AI agent
python ai_developer_agent.py --generate "EMA strategy"

# Then use strategy manager
python strategy_manager.py --status
python strategy_manager.py --run ema_strategy
```

### With gemini_strategy_generator.py

```python
# The AI agent uses gemini_strategy_generator internally
# But you can also call it directly:

from Backtest.gemini_strategy_generator import GeminiStrategyGenerator

gen = GeminiStrategyGenerator()
code = gen.generate_strategy("RSI strategy")
```

### With terminal_executor.py

```python
# Test any script
from Backtest.terminal_executor import run_script_in_venv

result = run_script_in_venv("codes/my_strategy.py")

print(f"Status: {result.status}")
print(f"Metrics: {result.summary}")
```

---

## Examples Gallery

### Example 1: Simple MA Crossover

```
> generate Buy when 10-day SMA crosses above 30-day SMA
```

### Example 2: RSI with Risk Management

```
> generate RSI strategy: Buy below 30, sell above 70, with 2% stop loss
```

### Example 3: Bollinger Bands

```
> generate Buy when price touches lower Bollinger Band, sell at middle band
```

### Example 4: MACD Momentum

```
> generate Buy when MACD crosses signal line and histogram is positive
```

### Example 5: Volume Breakout

```
> generate Buy when price breaks 20-day high with volume > 1.5x average
```

---

## API Reference

### AIDeveloperAgent

```python
class AIDeveloperAgent:
    def __init__(
        self,
        api_key: Optional[str] = None,
        memory_type: str = "buffer",
        max_iterations: int = 5
    )
    
    def generate_and_test_strategy(
        self,
        description: str,
        strategy_name: Optional[str] = None,
        auto_fix: bool = True
    ) -> Dict[str, Any]
    
    def test_existing_strategy(
        self,
        script_path: Path
    ) -> ExecutionResult
    
    def chat(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str
    
    def save_session(
        self,
        output_path: Optional[Path] = None
    )
```

### TerminalExecutor

```python
class TerminalExecutor:
    def run_script(
        self,
        script_path: Path,
        args: Optional[List[str]] = None,
        timeout: Optional[int] = 300
    ) -> ExecutionResult
    
    def run_command(
        self,
        command: str,
        cwd: Optional[Path] = None
    ) -> ExecutionResult
```

### CodeAnalyzer

```python
class CodeAnalyzer:
    def analyze_error(
        self,
        error_dict: Dict[str, Any]
    ) -> List[CodeFix]
    
    def auto_fix_code(
        self,
        code: str,
        errors: List[Dict[str, Any]]
    ) -> Tuple[str, List[CodeFix]]
    
    def validate_strategy_structure(
        self,
        code: str
    ) -> Dict[str, Any]
```

---

## Next Steps

1. **Try the examples** in this guide
2. **Read the reference cards** (`AI_DEVELOPER_REFERENCE_CARDS.md`)
3. **Experiment** with different strategy descriptions
4. **Review session logs** to understand AI behavior
5. **Combine with other tools** (strategy_manager, etc.)

---

## Support Files

- `ai_developer_agent.py` - Main agent
- `terminal_executor.py` - Script runner
- `code_analyzer.py` - Error fixer
- `AI_DEVELOPER_REFERENCE_CARDS.md` - Command reference
- `BACKTESTING_PY_MIGRATION_COMPLETE.md` - Framework docs

---

**Version:** 1.0.0  
**Last Updated:** 2025-10-31  
**Author:** AlgoAgent Team
