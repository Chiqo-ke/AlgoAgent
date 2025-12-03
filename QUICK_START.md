# Quick Start - Autonomous Strategy Generation

**Last Updated:** December 3, 2025

## Prerequisites

1. Python 3.10+ installed
2. Virtual environment activated
3. API keys configured in `.env`

## 1. Setup (One-Time)

```bash
# Navigate to project
cd AlgoAgent

# Activate virtual environment
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate    # Linux/Mac

# Verify environment
python -c "from monolithic_agent.Backtest.gemini_strategy_generator import GeminiStrategyGenerator; print('✓ Ready')"
```

## 2. Generate & Execute Strategy

### Simple Example
```python
from pathlib import Path
from monolithic_agent.Backtest.gemini_strategy_generator import GeminiStrategyGenerator

# Initialize generator (uses key rotation automatically)
gen = GeminiStrategyGenerator()

# Describe your strategy in natural language
prompt = """
Create a simple RSI strategy:
- RSI period: 14
- Buy when RSI < 30 (oversold)
- Sell when RSI > 70 (overbought)
- Stop loss: 10 pips
- Take profit: 30 pips
Use GOOG data for testing
"""

# Generate strategy
code = gen.generate_strategy(prompt)

# Save to file
output_dir = Path("monolithic_agent/Backtest/generated_strategies")
output_dir.mkdir(exist_ok=True, parents=True)
strategy_file = output_dir / "my_rsi_strategy.py"
strategy_file.write_text(code)

print(f"✓ Strategy saved: {strategy_file}")

# Execute with automatic error fixing
success, final_path, history = gen.fix_bot_errors_iteratively(
    strategy_file=strategy_file,
    max_iterations=3,
    test_symbol="GOOG",
    test_period_days=365
)

if success:
    print(f"✅ SUCCESS! Strategy is working")
    print(f"   Final file: {final_path}")
    print(f"   Fixed in {len(history)} iteration(s)")
    
    # View metrics
    from monolithic_agent.Backtest.bot_executor import BotExecutor
    executor = BotExecutor()
    result = executor.execute_bot(strategy_file=final_path)
    
    print(f"\n📊 RESULTS:")
    print(f"   Return: {result.return_pct}%")
    print(f"   Trades: {result.trades}")
    print(f"   Win Rate: {result.win_rate}")
    print(f"   Sharpe: {result.sharpe_ratio}")
else:
    print(f"❌ Could not fix after {len(history)} attempts")
    print("Fix history:")
    for i, fix in enumerate(history, 1):
        print(f"  {i}. {fix['error_type']} - {fix['fix_description'][:60]}...")
```

## 3. Run End-to-End Test

Test the complete autonomous workflow:

```bash
# Run the automated test
python monolithic_agent\tests\test_e2e_autonomous.py
```

Expected output:
```
✅ END-TO-END TEST PASSED
  Agent successfully:
  1. Generated RSI strategy
  2. Executed it with proper setup
  3. Automatically fixed any errors
  4. Verified working solution
```

## 4. Common Use Cases

### Use Case 1: Moving Average Crossover
```python
prompt = """
Create an EMA crossover strategy:
- Fast EMA: 10 periods
- Slow EMA: 30 periods
- Buy when fast crosses above slow
- Sell when fast crosses below slow
- Stop loss: 2%
- Take profit: 5%
"""

code = gen.generate_strategy(prompt)
# ... save and execute as above
```

### Use Case 2: Bollinger Bands Mean Reversion
```python
prompt = """
Create a Bollinger Bands mean reversion strategy:
- Period: 20
- Standard deviations: 2
- Buy when price touches lower band
- Sell when price touches upper band
- Stop loss: 1.5%
- Take profit: 3%
"""

code = gen.generate_strategy(prompt)
# ... save and execute as above
```

### Use Case 3: MACD Momentum
```python
prompt = """
Create a MACD momentum strategy:
- Fast: 12, Slow: 26, Signal: 9
- Buy when MACD crosses above signal
- Sell when MACD crosses below signal
- Stop loss: 2%
- Take profit: 4%
"""

code = gen.generate_strategy(prompt)
# ... save and execute as above
```

## 5. Configuration Options

### Adjust Max Fix Attempts
```python
success, final_path, history = gen.fix_bot_errors_iteratively(
    strategy_file=strategy_file,
    max_iterations=5,  # Try up to 5 times (default: 3)
    test_symbol="AAPL",
    test_period_days=730  # 2 years of data
)
```

### Change Test Symbol
```python
# Test on different stock
success, final_path, history = gen.fix_bot_errors_iteratively(
    strategy_file=strategy_file,
    test_symbol="TSLA",  # Tesla
    test_period_days=365
)
```

### Custom Execution Timeout
```python
from monolithic_agent.Backtest.bot_executor import BotExecutor

executor = BotExecutor(timeout_seconds=600)  # 10 minute timeout
result = executor.execute_bot(strategy_file=strategy_file)
```

## 6. Verify Key Rotation

Check if API key rotation is working:

```python
import os
from dotenv import load_dotenv

# Load environment
load_dotenv("monolithic_agent/.env")

# Check configuration
print(f"Key Rotation Enabled: {os.getenv('ENABLE_KEY_ROTATION')}")
print(f"Secret Store Type: {os.getenv('SECRET_STORE_TYPE')}")

# Count available keys
keys = [k for k in os.environ if k.startswith('API_KEY_gemini')]
print(f"Available API Keys: {len(keys)}")
```

Expected output:
```
Key Rotation Enabled: true
Secret Store Type: env
Available API Keys: 8
```

## 7. Troubleshooting

### Issue: Import Errors
**Solution:** The system should auto-fix these. If not, check:
- Virtual environment is activated
- All dependencies installed: `pip install -r monolithic_agent/requirements.txt`

### Issue: API Key Errors
**Solution:** Verify `.env` file:
```bash
# Check if keys are set
cat monolithic_agent/.env | grep "API_KEY_gemini"
```

### Issue: Timeout Errors
**Solution:** Increase timeout:
```python
executor = BotExecutor(timeout_seconds=600)
```

### Issue: Strategy Not Profitable
**Note:** This is expected! The auto-fix system ensures strategies *execute* correctly, not that they're profitable. You'll need to:
1. Optimize parameters
2. Test different indicators
3. Adjust entry/exit rules

## 8. Next Steps

1. **Read Full Documentation**
   - `E2E_AUTONOMOUS_AGENT_SUMMARY.md` - Complete system overview
   - `AUTOMATED_ERROR_FIXING_COMPLETE.md` - Error fixing details
   - `BOT_ERROR_FIXING_GUIDE.md` - Advanced usage

2. **Explore Pre-Built Indicators**
   - Check `monolithic_agent/Backtest/indicator_registry.py`
   - 7 indicators available: EMA, SMA, RSI, MACD, Bollinger Bands, ATR, Stochastic

3. **View Generated Code**
   - Location: `monolithic_agent/Backtest/generated_strategies/`
   - Learn from AI-generated examples

4. **Check Results**
   - Location: `monolithic_agent/Backtest/codes/results/`
   - JSON, CSV, and SQLite database
   - Review metrics and performance

---

## Quick Reference

| Task | Command |
|------|---------|
| Generate strategy | `gen.generate_strategy(prompt)` |
| Execute with auto-fix | `gen.fix_bot_errors_iteratively(file)` |
| Run E2E test | `python monolithic_agent/tests/test_e2e_autonomous.py` |
| Check key rotation | `print(os.getenv('ENABLE_KEY_ROTATION'))` |
| View results | Check `monolithic_agent/Backtest/codes/results/` |

---

**Need Help?** See full documentation in project root:
- `E2E_AUTONOMOUS_AGENT_SUMMARY.md`
- `BOT_ERROR_FIXING_GUIDE.md`
- `QUICK_REFERENCE_ERROR_FIXING.md`
