# Quick Start - AlgoAgent Systems

**Last Updated:** December 17, 2025  
**Time to Complete:** 5-10 minutes per system

---

## 🎯 Choose Your System

AlgoAgent provides **two independent systems** optimized for different use cases. Follow the appropriate guide below.

---

## 🔹 Monolithic Agent - Quick Start

**Best for:** Production trading, API integration, frontend applications

### 1. Setup (One-Time)

```powershell
# Navigate to monolithic agent
cd c:\Users\nyaga\Documents\AlgoAgent\monolithic_agent

# Install dependencies
pip install -r requirements.txt

# Configure API keys (see API Keys section below)
# Edit .env file with your Gemini API keys
```

### 2. Start Django Server

```powershell
# Start the server
python manage.py runserver

# Server runs at: http://127.0.0.1:8000/
```

### 3. Test the API

```powershell
# Generate a strategy via API
curl -X POST http://localhost:8000/api/strategies/generate_with_ai/ \
  -H "Content-Type: application/json" \
  -d '{
    "description": "RSI strategy: buy when RSI < 30, sell when RSI > 70",
    "execute_after_generation": true
  }'
```

**✅ See [monolithic_agent/README.md](monolithic_agent/README.md) for complete documentation**

---

## 🔹 Multi-Agent System - Quick Start

**Best for:** Research, advanced workflows, development

### 1. Setup (One-Time)

```powershell
# Navigate to multi-agent system
cd c:\Users\nyaga\Documents\AlgoAgent\multi_agent

# Install dependencies
pip install -r requirements.txt

# Configure API keys (see API Keys section below)
# Edit keys.json with your Gemini API keys
```

### 2. Start CLI Interface

```powershell
# Interactive mode
python cli.py

# In CLI:
>>> submit Create RSI strategy: buy at RSI<30, sell at RSI>70
>>> execute workflow_abc123
>>> status workflow_abc123
```

### 3. Or Use Single-Command Mode

```powershell
# Generate and execute in one command
python cli.py --request "Create MACD crossover strategy" --run
```

**✅ See [multi_agent/README.md](multi_agent/README.md) for complete documentation**

---

## 🔑 API Keys Configuration

### For Monolithic Agent

1. Navigate to `monolithic_agent/` directory
2. Copy `.env.example` to `.env`
3. Add your Gemini API keys:

```env
# Gemini API Keys for Key Rotation (8 keys recommended)
GEMINI_API_KEY_1=your_key_1
GEMINI_API_KEY_2=your_key_2
GEMINI_API_KEY_3=your_key_3
GEMINI_API_KEY_4=your_key_4
GEMINI_API_KEY_5=your_key_5
GEMINI_API_KEY_6=your_key_6
GEMINI_API_KEY_7=your_key_7
GEMINI_API_KEY_8=your_key_8

# Enable key rotation
ENABLE_KEY_ROTATION=True
SECRET_STORE_TYPE=environment
```

### For Multi-Agent System

1. Navigate to `multi_agent/` directory
2. Copy `keys_example.json` to `keys.json`
3. Add your Gemini API keys:

```json
{
  "gemini_flash_1": {
    "api_key": "your_key_1",
    "model": "gemini-1.5-flash",
    "rpm_limit": 60
  },
  "gemini_flash_2": {
    "api_key": "your_key_2",
    "model": "gemini-1.5-flash",
    "rpm_limit": 60
  }
}
```

**Get API Keys:** https://makersuite.google.com/app/apikey

---

## 📚 Documentation Navigation

After completing quick start, explore:

### For Monolithic Agent Users
1. [monolithic_agent/docs/guides/QUICK_REFERENCE.md](monolithic_agent/docs/guides/QUICK_REFERENCE.md) - Common commands
2. [monolithic_agent/docs/api/API_ENDPOINTS.md](monolithic_agent/docs/api/API_ENDPOINTS.md) - API reference
3. [monolithic_agent/STATUS.md](monolithic_agent/STATUS.md) - System status

### For Multi-Agent Users
1. [multi_agent/QUICKSTART_GUIDE.md](multi_agent/QUICKSTART_GUIDE.md) - Detailed guide
2. [multi_agent/docs/guides/CLI_READY.md](multi_agent/docs/guides/CLI_READY.md) - CLI commands
3. [multi_agent/ARCHITECTURE.md](multi_agent/ARCHITECTURE.md) - System architecture

### General
- [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) - Complete navigation
- [README.md](README.md) - Project overview

---

## 💡 Usage Examples

### Monolithic Agent - Python API

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
```

### Multi-Agent - CLI Interface

```powershell
# Start CLI
cd multi_agent
python cli.py

# Submit request
>>> submit Create EMA crossover: buy when EMA(10) > EMA(30), sell when EMA(10) < EMA(30)

# Check workflow
>>> list

# Execute workflow
>>> execute workflow_abc123

# Check status
>>> status workflow_abc123

# Exit
>>> exit
```
```

---

## 🧪 Running Tests

### Monolithic Agent Tests

```powershell
cd monolithic_agent

# E2E autonomous workflow test
python tests/test_e2e_autonomous.py

# API integration tests
python tests/test_api_backend_integration.py
python tests/test_api_integration.py

# Backtesting API test
python tests/test_backtest_api.py

# Bot execution & error fixing tests
python tests/test_autonomous_bot_fix.py
python tests/test_ema_crossover_bot.py
```

Expected output:
```
✅ E2E TEST PASSED (18/20 tests)
  Agent successfully:
  1. Generated RSI strategy
  2. Executed it with proper setup
  3. Automatically fixed any errors
  4. Verified working solution
```

### Multi-Agent Tests

```powershell
cd multi_agent

# Run all unit tests
python -m pytest tests/test_*.py

# Specific tests
python -m pytest tests/test_simbroker.py
python -m pytest tests/test_key_manager.py
```

---

## 🔍 Strategy Examples

### RSI Strategy
```
Create a simple RSI strategy:
- RSI period: 14
- Buy when RSI < 30 (oversold)
- Sell when RSI > 70 (overbought)
- Stop loss: 2%
- Take profit: 5%
```

### EMA Crossover
```
Create an EMA crossover strategy:
- Fast EMA: 10 periods
- Slow EMA: 30 periods
- Buy when fast crosses above slow
- Sell when fast crosses below slow
- Stop loss: 2%
- Take profit: 5%
```

### Bollinger Bands
```
Create a Bollinger Bands mean reversion strategy:
- Period: 20
- Standard deviations: 2
- Buy when price touches lower band
- Sell when price touches upper band
- Stop loss: 1.5%
- Take profit: 3%
```

### MACD Momentum
```
Create a MACD momentum strategy:
- Fast: 12, Slow: 26, Signal: 9
- Buy when MACD crosses above signal
- Sell when MACD crosses below signal
- Stop loss: 2%
- Take profit: 4%
```

---

## ⚙️ Configuration Options

### Monolithic Agent - Adjust Parameters

```python
# Adjust max fix attempts
success, final_path, history = gen.fix_bot_errors_iteratively(
    strategy_file=strategy_file,
    max_iterations=5,  # Try up to 5 times (default: 3)
    test_symbol="AAPL",
    test_period_days=730  # 2 years of data
)

# Custom execution timeout
from monolithic_agent.Backtest.bot_executor import BotExecutor
executor = BotExecutor(timeout_seconds=600)  # 10 minute timeout
```

### Multi-Agent - CLI Commands

```bash
# List available commands
>>> help

# Submit with custom workflow ID
>>> submit --id my_workflow_123 Create RSI strategy

# Execute with verbose output
>>> execute --verbose workflow_abc123

# Check all workflows
>>> list --all
```

---

## 🚨 Troubleshooting

### Monolithic Agent

**Issue:** API key errors
```powershell
# Check keys are configured
python -c "from dotenv import load_dotenv; import os; load_dotenv('monolithic_agent/.env'); print(f'Keys configured: {sum(1 for i in range(1,9) if os.getenv(f\"GEMINI_API_KEY_{i}\"))}')"
```

**Issue:** Server won't start
```powershell
# Check Django configuration
cd monolithic_agent
python manage.py check
```

### Multi-Agent

**Issue:** CLI won't start
```powershell
# Check dependencies
cd multi_agent
pip install -r requirements.txt

# Verify imports
python -c "import agents; print('✓ Agents module loaded')"
```

**Issue:** Template fallback
- Multi-agent uses template fallback when AI quota is exhausted
- This is normal behavior - strategies will still be generated

---

## 📖 Next Steps

### For Monolithic Agent Users
1. Explore [API documentation](monolithic_agent/docs/api/API_ENDPOINTS.md)
2. Check [system status](monolithic_agent/STATUS.md)
3. Read [production guide](monolithic_agent/docs/api/PRODUCTION_API_GUIDE.md)

### For Multi-Agent Users
1. Read [architecture guide](multi_agent/ARCHITECTURE.md)
2. Explore [CLI features](multi_agent/docs/guides/CLI_READY.md)
3. Learn about [adapters](multi_agent/ARCHITECTURE.md#adapter-architecture)

### General Resources
- [Complete documentation index](DOCUMENTATION_INDEX.md)
- [Test summaries](TEST_SUMMARY.md)
- [System comparison](README.md#system-comparison)

---

**✅ You're all set! Choose your system and start building autonomous trading strategies.**
