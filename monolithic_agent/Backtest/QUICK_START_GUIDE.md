# 🚀 Strategy Generator - Quick Start Guide

**Last Updated:** 2025-10-17  
**Status:** ✅ Ready to Use

---

## 📋 Three Ways to Generate Strategies

### **Method 1: Interactive Menu (Easiest!)** ⭐ RECOMMENDED

```powershell
python quick_generate.py
```

This opens an interactive menu where you can:
- Choose from 5 pre-made strategy examples
- Create custom strategies with guided prompts
- No need to worry about command syntax!

**Example Session:**
```
============================================================
QUICK STRATEGY GENERATOR
============================================================

Choose an option:

  [1-5] Generate example strategy
  [c]   Custom strategy (enter your own description)
  [q]   Quit

Example Strategies:
  1. RSI Oversold/Overbought
  2. EMA Crossover
  3. MACD Momentum
  4. Bollinger Bands
  5. Moving Average Trend

Your choice: 2

Generating: EMA Crossover
✅ Success! Strategy saved to: ema_crossover_strategy.py
```

---

### **Method 2: Quick Command (Simple)**

```powershell
python quick_generate.py "Your strategy description" output_file.py
```

**Examples:**

```powershell
# RSI strategy
python quick_generate.py "Buy when RSI < 30, sell when RSI > 70" rsi.py

# EMA crossover
python quick_generate.py "Buy when 50 EMA crosses above 200 EMA" ema.py

# MACD momentum
python quick_generate.py "Buy when MACD crosses above signal line" macd.py
```

---

### **Method 3: Direct Generator (Advanced)**

```powershell
python gemini_strategy_generator.py "Description" -o output.py --validate
```

**⚠️ IMPORTANT for PowerShell:**
- Put entire description in quotes: `"..."`
- Write command on ONE line (no backslashes `\`)
- Or use backtick `` ` `` for line continuation (not `\`)

**Correct:**
```powershell
python gemini_strategy_generator.py "Buy when RSI < 30, sell when RSI > 70" -o rsi.py --validate
```

**Wrong (Don't use backslash in PowerShell):**
```powershell
# ❌ This FAILS in PowerShell:
python gemini_strategy_generator.py \
  "Buy when RSI < 30" \
  -o rsi.py
```

**If you need multiple lines in PowerShell, use backtick:**
```powershell
python gemini_strategy_generator.py `
  "Buy when RSI < 30, sell when RSI > 70" `
  -o rsi.py `
  --validate
```

---

## 🎯 Strategy Description Best Practices

### **Good Descriptions** ✅

```
"Buy AAPL when RSI < 30 and price above 200 SMA, sell when RSI > 70"

"EMA crossover: Buy when 50 EMA crosses above 200 EMA, sell when crosses below"

"Bollinger Bands mean reversion: Buy at lower band, sell at middle band"

"MACD momentum: Enter long when MACD crosses above signal and histogram positive"

"Breakout strategy: Buy when price breaks above 20-day high with volume spike"
```

### **What to Include:**

1. **Entry Conditions:** When to buy
2. **Exit Conditions:** When to sell
3. **Indicators:** Which ones to use (RSI, SMA, EMA, MACD, BBANDS, etc.)
4. **Ticker:** Which stock (AAPL, SPY, TSLA, etc.)
5. **Parameters:** Optional (e.g., "14-period RSI", "50-day moving average")

### **Vague Descriptions** ❌

```
"Make me money"           ❌ Too vague
"Good trading strategy"   ❌ Not specific
"Something with RSI"      ❌ No entry/exit rules
```

---

## 📁 Pre-Made Strategy Examples

Run `python quick_generate.py` and choose from:

### **1. RSI Oversold/Overbought**
- Buy when RSI < 30
- Sell when RSI > 70
- Classic mean reversion

### **2. EMA Crossover**
- Buy when fast EMA crosses above slow EMA
- Sell when fast EMA crosses below slow EMA
- Trend following

### **3. MACD Momentum**
- Buy when MACD crosses above signal line
- Histogram must be positive
- Momentum trading

### **4. Bollinger Bands**
- Buy when price touches lower band
- Sell when price reaches middle band
- Mean reversion

### **5. Moving Average Trend**
- Buy when price crosses above 20 SMA
- Sell when price crosses below
- Simple trend following

---

## 🔧 Generated Strategy Structure

Every generated strategy includes:

```python
# MUST NOT EDIT SimBroker
from sim_broker import SimBroker
from config import BacktestConfig
from canonical_schema import create_signal, OrderSide, OrderAction, OrderType
from data_loader import load_market_data

class MyStrategy:
    def __init__(self, broker: SimBroker):
        self.broker = broker
    
    def on_bar(self, timestamp, data):
        # Your strategy logic here
        if should_buy:
            signal = create_signal(...)
            self.broker.submit_signal(signal.to_dict())

def run_backtest():
    # Load data with indicators
    df, metadata = load_market_data(
        ticker='AAPL',
        indicators={'RSI': {'timeperiod': 14}}
    )
    
    # Run simulation
    # Generate metrics
    # Export results
```

---

## ⚡ Quick Commands Reference

### **Generate Strategy**
```powershell
# Interactive (easiest)
python quick_generate.py

# Quick command
python quick_generate.py "Description" output.py

# Direct (advanced)
python gemini_strategy_generator.py "Description" -o output.py --validate
```

### **Run Generated Strategy**
```powershell
python your_strategy.py
```

### **Test Integration**
```powershell
# Test Gemini
python test_gemini_integration.py

# Test Data Loader
python test_data_loader.py
```

### **List Available Data**
```powershell
python -c "from data_loader import list_available_data; files = list_available_data(); print(f'{len(files)} files available'); [print(f['ticker'], f['period'], f['interval']) for f in files[:5]]"
```

### **List Available Indicators**
```powershell
python -c "from data_loader import get_available_indicators; print(get_available_indicators())"
```

---

## 📊 Common Strategy Patterns

### **Mean Reversion**
```
"Buy when RSI < 30, sell when RSI > 70"
"Buy when price 2 std devs below 20 SMA, sell at SMA"
"Buy at Bollinger lower band, sell at middle band"
```

### **Trend Following**
```
"Buy when 50 EMA > 200 EMA and price > 50 EMA"
"Buy when MACD crosses above signal line"
"Buy when price breaks 20-day high"
```

### **Momentum**
```
"Buy when RSI > 50 and price > 20 SMA"
"Buy when MACD histogram increasing for 3 bars"
"Buy when price gains 2% with high volume"
```

### **Volatility**
```
"Buy when ATR expands above 2% and price pullbacks"
"Enter trades only when Bollinger Bands width > threshold"
```

---

## 🎓 Complete Workflow Example

**Step 1:** Generate strategy
```powershell
python quick_generate.py
```

Choose option 2 (EMA Crossover)

**Step 2:** Strategy is created as `ema_crossover_strategy.py`

**Step 3:** Review the generated code (optional)
```powershell
notepad ema_crossover_strategy.py
```

**Step 4:** Run backtest
```powershell
python ema_crossover_strategy.py
```

**Step 5:** Review results
```
============================================================
BACKTEST RESULTS
============================================================
Period: 2025-10-13 13:30:00+00:00 to 2025-10-13 14:30:00+00:00
Duration: 0 days

Starting Capital: $100,000.00
Final Equity: $100,234.56
Net Profit: $234.56 (0.23%)

Total Trades: 1
Win Rate: 100.0%
Profit Factor: inf

Max Drawdown: -0.00%
Sharpe Ratio: 0.00
Sortino Ratio: 0.00
============================================================
```

---

## 🐛 Troubleshooting

### **Error: "unrecognized arguments"**

**Problem:** Using backslash `\` in PowerShell
```powershell
# ❌ Wrong
python gemini_strategy_generator.py \
  "Description" \
  -o output.py
```

**Solution:** Write on one line or use backtick
```powershell
# ✅ Correct
python gemini_strategy_generator.py "Description" -o output.py

# Or with backtick
python gemini_strategy_generator.py `
  "Description" `
  -o output.py
```

### **Error: "GEMINI_API_KEY not found"**

**Problem:** API key not configured

**Solution:** Create or update `.env` file in project root:
```
GEMINI_API_KEY=your_api_key_here
```

### **Error: "No data file found"**

**Problem:** No data for requested ticker

**Solution:** Check available data:
```powershell
python -c "from data_loader import list_available_data; [print(f['ticker']) for f in list_available_data()]"
```

Use a ticker that exists (e.g., AAPL, SPY, TSLA)

### **Strategy runs but no trades**

**Problem:** Not enough data bars for indicators

**Solution:** 
- Check how many bars loaded: Look for "Loaded X bars" message
- Some indicators need minimum bars (e.g., 200 EMA needs 200+ bars)
- Try with more data or shorter indicator periods

---

## 💡 Tips & Tricks

### **1. Start Simple**
Begin with basic strategies (RSI, single moving average) before complex ones

### **2. Use Interactive Mode**
The interactive `quick_generate.py` is easiest for beginners

### **3. Validate Always**
Always use `--validate` flag to check generated code

### **4. Test with Small Data**
Start with small datasets to iterate quickly

### **5. Review Generated Code**
Open generated `.py` file to understand and learn

### **6. Iterate**
Generate, test, improve description, regenerate

---

## 📚 Available Indicators

Commonly supported indicators:

**Trend:**
- SMA (Simple Moving Average)
- EMA (Exponential Moving Average)  
- MACD (Moving Average Convergence Divergence)
- ADX (Average Directional Index)

**Momentum:**
- RSI (Relative Strength Index)
- STOCH (Stochastic Oscillator)
- CCI (Commodity Channel Index)
- MOM (Momentum)

**Volatility:**
- BBANDS (Bollinger Bands)
- ATR (Average True Range)
- NATR (Normalized ATR)

**Volume:**
- OBV (On Balance Volume)
- AD (Accumulation/Distribution)
- VWAP (Volume Weighted Average Price)

Use `get_available_indicators()` for complete list.

---

## 🎯 Next Steps

1. **Generate your first strategy:**
   ```powershell
   python quick_generate.py
   ```

2. **Run a backtest:**
   ```powershell
   python your_strategy.py
   ```

3. **Iterate and improve:**
   - Adjust indicator parameters
   - Add more conditions
   - Try different exit rules

4. **Explore more:**
   - Read `API_REFERENCE.md` for SimBroker details
   - Read `DATA_LOADER_SUMMARY.md` for data loading
   - Read `SYSTEM_PROMPT.md` for AI integration details

---

**Happy Trading! 📈**

For issues or questions, check the documentation files in this directory.
