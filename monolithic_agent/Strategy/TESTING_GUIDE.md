# AlgoAgent Strategy Validator - Interactive Testing Guide

## 🚀 Quick Start

### Step 1: Install Dependencies

```powershell
# Navigate to Strategy folder
cd c:\Users\nyaga\Documents\AlgoAgent\Strategy

# Install required packages
pip install -r requirements.txt

# Or use your virtual environment
C:/Users/nyaga/Documents/AlgoAgent/.venv/Scripts/python.exe -m pip install -r requirements.txt
```

### Step 2: Verify API Key

Make sure your Gemini API key is set in the `.env` file:

```env
GEMINI_API_KEY=AIzaSyAvxduYuA8rCmGtQirS3GXsHGv0GW7mj7w
```

### Step 3: Run Interactive Tester

```powershell
python interactive_strategy_tester.py
```

## 🎯 What You Can Test

### 1. Free Text Strategy Input
Enter your trading strategy in plain English:
```
Buy AAPL when the 50-day EMA crosses above the 200-day EMA.
Set a stop loss at 2% below entry.
Take profit at 5% above entry.
Risk 1% of account per trade.
```

### 2. Numbered Steps Input
Enter structured steps:
```
1. Entry: Buy when RSI < 30 on daily chart
2. Exit: Sell when RSI > 70
3. Stop Loss: 3% below entry
4. Position Size: Risk 1% of account
5. Re-entry: Wait 2 days before re-entering same symbol
```

### 3. URL Analysis
Paste a URL containing a trading strategy:
```
https://youtube.com/watch?v=example
https://example.com/trading-strategy-article
```

### 4. Example Strategies
Load pre-built examples:
- EMA Crossover Strategy
- RSI Mean Reversion Strategy
- Scalping Strategy

## 🤖 AI-Enhanced Features

The system now uses Gemini API for:

1. **Intelligent Text Parsing**: Extracts strategy steps from unstructured text
2. **Smart Recommendations**: AI-generated suggestions based on strategy analysis
3. **Missing Element Detection**: Identifies gaps in your strategy
4. **Risk Assessment**: Evaluates risk level and suggests improvements
5. **Clarifying Questions**: Asks intelligent questions when information is missing

## 📊 What You'll Get

### Output Includes:
1. **Canonicalized Steps** - Your strategy broken down into clear steps
2. **Classification** - Strategy type, risk level, instruments, timeframe
3. **AI Recommendations** - Prioritized suggestions with rationale
4. **Confidence Level** - Assessment of strategy completeness
5. **Next Actions** - Suggested next steps (backtest, parameter sweep, etc.)
6. **Canonical JSON** - Machine-readable strategy format

### Example Output:
```
CANONICALIZED STEPS
------------------------
1. Entry rule — 50 EMA crosses above 200 EMA → enter long
2. Exit rule — Stop loss at 2% OR take profit at 5%
3. Position sizing — Risk 1% of account per trade

CLASSIFICATION & METADATA
---------------------------
Strategy Type: trend-following
Risk Tier: medium
Instruments: AAPL
Timeframe: daily
Data Needs: Daily bars, 200+ day history

AI-POWERED RECOMMENDATIONS
---------------------------
1. Add re-entry cooldown rule
   Why: Prevents overtrading after stop-outs
   Test: Try 1-3 day cooldowns

2. Implement trailing stop
   Why: Protects profits in trending moves
   Test: Trail at 1.5-2x initial stop distance

3. Test with realistic slippage
   Why: Ensures profitability after costs
   Test: 0.05% - 0.1% slippage assumption

CONFIDENCE: MEDIUM
Next Actions: [Run backtest] [Parameter sweep] [Generate code]
```

## 🔧 Configuration Options

### Enable/Disable Gemini AI
```python
# In code
bot = StrategyValidatorBot(use_gemini=True)

# In interactive mode: Select "Configure Settings" from menu
```

### Strict Mode
Raises exceptions on security violations:
```python
bot = StrategyValidatorBot(strict_mode=True)
```

### Username for Provenance
Track who created each strategy:
```python
bot = StrategyValidatorBot(username="your_name")
```

## 🛡️ Security Features

The system automatically detects:
- ❌ Pump-and-dump schemes
- ❌ "Guaranteed profit" claims
- ❌ Excessive leverage (>5x)
- ❌ Unlimited risk positions
- ❌ Credential requests
- ⚠️ Live trading attempts (requires approval)

## 💡 Usage Tips

### Best Practices:
1. **Be Specific**: Include entry rules, exit rules, and position sizing
2. **Include Risk Management**: Stops, take profits, max position size
3. **Mention Timeframe**: Daily, hourly, 5-minute, etc.
4. **Specify Instruments**: What you're trading (stocks, forex, crypto)

### What Makes a Good Strategy Input:
✅ Clear entry and exit conditions
✅ Defined risk management rules
✅ Position sizing methodology
✅ Re-entry/cooldown rules
✅ Specific timeframe and instruments

### What to Avoid:
❌ Vague descriptions ("buy low, sell high")
❌ Missing risk management
❌ No position sizing rules
❌ Unrealistic claims ("never loses")

## 📁 Session Management

### Save Results
Results can be saved as JSON for later analysis:
- Automatic timestamped filenames
- Full canonical schema included
- All recommendations preserved

### View History
Track all strategies analyzed in your session:
- Timestamp of analysis
- Success/failure status
- Quick reference to inputs

## 🔍 Troubleshooting

### Gemini API Issues
```
⚠ No valid Gemini API key found - Using mock mode
```
**Solution**: Check your `.env` file and ensure API key is valid

### Import Errors
```
ModuleNotFoundError: No module named 'google.generativeai'
```
**Solution**: Run `pip install google-generativeai`

### JSON Errors
```
JSONDecodeError: Expecting value
```
**Solution**: This is normal - the system will fall back to text parsing

## 📚 Next Steps

After validating your strategy:

1. **Run Backtest**: Test on historical data
2. **Parameter Sweep**: Optimize parameters (stop loss %, position size, etc.)
3. **Walk-Forward Analysis**: Test robustness over time
4. **Paper Trading**: Test in simulated environment
5. **Code Generation**: Generate executable code (requires approval)

## 🤝 Integration Examples

### API Integration
```python
from strategy_validator import StrategyValidatorBot

def validate_user_strategy(user_input):
    bot = StrategyValidatorBot(username="api_user")
    result = bot.process_input(user_input)
    return result
```

### Web Application
```python
@app.route('/validate', methods=['POST'])
def validate():
    strategy_text = request.json['strategy']
    bot = StrategyValidatorBot(username=current_user.id)
    result = bot.process_input(strategy_text)
    return jsonify(result)
```

### Batch Processing
```python
strategies = load_strategies_from_file("strategies.txt")
for strategy in strategies:
    result = bot.process_input(strategy)
    save_result(result)
```

## 📞 Support

For issues or questions:
1. Check the README.md in the Strategy folder
2. Review QUICKSTART.md for quick reference
3. See IMPLEMENTATION_SUMMARY.md for technical details
4. Run the demo: `python demo.py`

## 🎓 Learning Resources

- **examples.py**: Study example strategies
- **test_strategy_validator.py**: See comprehensive test cases
- **system_prompt.py**: Understand the AI system prompts
- **canonical_schema.py**: Learn the JSON schema structure

---

**Ready to start?** Run: `python interactive_strategy_tester.py`
