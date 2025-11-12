# Gemini AI Integration Guide

## ✅ Integration Complete!

The Gemini API has been successfully integrated with the SimBroker backtesting system.

## 📋 What's Been Set Up

### 1. **Environment Configuration**
- ✅ GEMINI_API_KEY configured in `.env` file
- ✅ API key validated: `AIzaSyAvxd...mj7w`

### 2. **Package Installation**
- ✅ `google-generativeai` installed
- ✅ `python-dotenv` installed
- ✅ Model: `gemini-2.0-flash` (fast, stable)

### 3. **Integration Components**
- ✅ `gemini_strategy_generator.py` - Main generator class
- ✅ `test_gemini_integration.py` - Test suite
- ✅ `SYSTEM_PROMPT.md` - AI code generation guide
- ✅ `API_REFERENCE.md` - Complete API documentation

### 4. **Test Results**
All 6 tests passed:
- ✅ Environment configuration
- ✅ Package installation
- ✅ API connection
- ✅ Strategy generation (8,033 characters)
- ✅ Code validation
- ✅ File save

---

## 🚀 How to Use

### **Method 1: Command Line**

Generate a strategy directly from command line:

```bash
# Basic usage
python gemini_strategy_generator.py "Buy when MACD crosses above signal line, sell when crosses below" -o my_macd_strategy.py

# With validation
python gemini_strategy_generator.py "Mean reversion strategy using Bollinger Bands" -o bollinger_strategy.py --validate

# Custom strategy name
python gemini_strategy_generator.py "Momentum strategy with RSI" -o momentum.py -n MomentumRSI
```

### **Method 2: Python Code**

```python
from gemini_strategy_generator import GeminiStrategyGenerator

# Initialize generator
generator = GeminiStrategyGenerator()

# Generate strategy
code = generator.generate_strategy(
    description="Buy when price crosses above 50-day MA, sell when crosses below",
    strategy_name="MAStrategy"
)

# Validate generated code
validation = generator.validate_generated_code(code)
print(f"Valid: {validation['valid']}")

# Save to file
with open('ma_strategy.py', 'w') as f:
    f.write(code)
```

### **Method 3: Convenience Function**

```python
from gemini_strategy_generator import generate_strategy_from_description

# One-liner
code = generate_strategy_from_description(
    "Triple EMA crossover strategy",
    output_file="triple_ema.py"
)
```

---

## 📝 Strategy Description Best Practices

### **Good Descriptions** ✅

```
"Buy when RSI < 30 and price above 200 MA, sell when RSI > 70"

"Mean reversion strategy using Bollinger Bands: 
 - Buy when price touches lower band
 - Sell when price touches upper band
 - Use 20-period bands with 2 standard deviations"

"Momentum breakout strategy:
 - Enter long when price breaks above 20-day high
 - Exit when price crosses below 10-day MA
 - Use ATR-based position sizing"
```

### **Vague Descriptions** ❌

```
"Make me a good strategy"
"Something with moving averages"
"Profitable trading bot"
```

---

## 🔧 Advanced Features

### **Improve Existing Strategy**

```python
from gemini_strategy_generator import GeminiStrategyGenerator

generator = GeminiStrategyGenerator()

# Read existing strategy
with open('my_strategy.py', 'r') as f:
    existing_code = f.read()

# Request improvements
improved_code = generator.improve_strategy(
    existing_code=existing_code,
    improvement_request="Add stop-loss at 2% and take-profit at 5%"
)

# Save improved version
with open('my_strategy_v2.py', 'w') as f:
    f.write(improved_code)
```

### **Validate Before Running**

```python
from gemini_strategy_generator import GeminiStrategyGenerator

generator = GeminiStrategyGenerator()

# Generate strategy
code = generator.generate_strategy("Your description here")

# Validate
validation = generator.validate_generated_code(code)

if validation['valid']:
    print("✅ Strategy is valid!")
    # Save and run
else:
    print("❌ Issues found:")
    for issue in validation['issues']:
        print(f"  - {issue}")
```

---

## 📚 Example Strategies

### **1. RSI Oversold/Overbought**
```bash
python gemini_strategy_generator.py "Buy when RSI < 30, sell when RSI > 70" -o rsi_strategy.py
```

### **2. Moving Average Crossover**
```bash
python gemini_strategy_generator.py "Golden cross strategy: buy when 50 MA crosses above 200 MA, sell when crosses below" -o golden_cross.py
```

### **3. Bollinger Band Mean Reversion**
```bash
python gemini_strategy_generator.py "Buy when price touches lower Bollinger Band, sell when price reaches middle band" -o bollinger_mean_reversion.py
```

### **4. MACD Momentum**
```bash
python gemini_strategy_generator.py "Enter long when MACD crosses above signal line and histogram positive" -o macd_momentum.py
```

---

## 🔍 Validation Checks

The validator ensures generated code:

✅ **Required Imports**
- `from sim_broker import SimBroker`
- `from canonical_schema import create_signal, OrderSide, OrderAction, OrderType`
- `from config import BacktestConfig`

✅ **Stable API Usage**
- Uses `broker.submit_signal()`
- Uses `broker.step_to()`
- Uses `broker.compute_metrics()`

✅ **No Internal Access**
- Doesn't access `broker.order_manager`
- Doesn't access `broker.execution_simulator`
- Doesn't modify SimBroker internals

✅ **Proper Signal Creation**
- Uses `create_signal()` helper
- Includes all required signal fields

---

## 🎯 What Gets Generated

Each generated strategy includes:

1. **Header Comment**
   ```python
   # MUST NOT EDIT SimBroker
   """
   Strategy: StrategyName
   Description: Strategy description
   """
   ```

2. **Imports**
   ```python
   from sim_broker import SimBroker
   from config import BacktestConfig
   from canonical_schema import create_signal, OrderSide, OrderAction, OrderType
   ```

3. **Strategy Class**
   ```python
   class MyStrategy:
       def __init__(self, broker: SimBroker):
           self.broker = broker
           # Strategy initialization
       
       def on_bar(self, timestamp: datetime, data: dict):
           # Strategy logic
           # Emit signals using create_signal()
   ```

4. **Backtest Runner**
   ```python
   def run_backtest():
       config = BacktestConfig(...)
       broker = SimBroker(config)
       # Load data, run strategy
       # Export results
   ```

5. **Main Block**
   ```python
   if __name__ == "__main__":
       run_backtest()
   ```

---

## 🐛 Troubleshooting

### **Issue: "GEMINI_API_KEY not found"**
**Solution:** Create `.env` file with:
```
GEMINI_API_KEY=your_api_key_here
```

### **Issue: "google-generativeai not installed"**
**Solution:** Install package:
```bash
pip install google-generativeai python-dotenv
```

### **Issue: "Model not found"**
**Solution:** The generator uses `gemini-2.0-flash` by default. If it's not available, check available models:
```python
import google.generativeai as genai
genai.configure(api_key="your_key")
for m in genai.list_models():
    print(m.name)
```

### **Issue: Generated code has errors**
**Solution:** Use the validator:
```python
validation = generator.validate_generated_code(code)
print(validation['issues'])
```

---

## 📖 Full Workflow Example

```python
# 1. Generate strategy
from gemini_strategy_generator import GeminiStrategyGenerator

generator = GeminiStrategyGenerator()

code = generator.generate_strategy(
    description="""
    Trend following strategy:
    - Enter long when 20 EMA crosses above 50 EMA
    - Exit when 20 EMA crosses below 50 EMA
    - Use 2% position sizing
    """,
    strategy_name="TrendFollowingEMA"
)

# 2. Validate
validation = generator.validate_generated_code(code)
assert validation['valid'], f"Validation failed: {validation['issues']}"

# 3. Save
with open('trend_following.py', 'w') as f:
    f.write(code)

# 4. Run backtest
import subprocess
subprocess.run(['python', 'trend_following.py'])
```

---

## ✨ Key Features

1. **Immutable Core**: SimBroker API never changes
2. **AI-Powered**: Natural language → working code
3. **Validated**: Automatic checks for API compliance
4. **Documented**: Full system prompt for consistency
5. **Tested**: 6-test suite ensures reliability

---

## 📞 Support

- **Test Integration**: `python test_gemini_integration.py`
- **API Reference**: See `API_REFERENCE.md`
- **System Prompt**: See `SYSTEM_PROMPT.md`
- **Example Strategy**: See `example_strategy.py`

---

**Status**: ✅ Fully operational
**Last Updated**: 2025-10-16
**Version**: 1.0.0
