# 🚀 AlgoAgent Strategy Validator - Quick Start

## ✅ Setup Complete!

Your Strategy Validator has been enhanced with AI-powered analysis using Gemini API.

## 🎯 Start Testing Now

### Option 1: Interactive Tester (Recommended)

```powershell
cd Strategy
python interactive_strategy_tester.py
```

Or simply **double-click**: `Strategy\start_tester.bat`

### Option 2: Run Demo

```powershell
cd Strategy
python demo.py
```

### Option 3: Python API

```python
from Strategy.strategy_validator import StrategyValidatorBot

bot = StrategyValidatorBot(username="your_name", use_gemini=True)
result = bot.process_input("Buy when RSI < 30, sell when RSI > 70")
print(result)
```

## 📚 Documentation

- **TESTING_GUIDE.md** - Complete testing guide (START HERE)
- **INTEGRATION_SUMMARY.md** - What changed and how to use it
- **README.md** - Full system documentation
- **QUICKSTART.md** - Quick reference

## 🤖 AI Features

Your system now uses Gemini AI for:

✅ Intelligent strategy parsing from natural language  
✅ Smart recommendations with rationale  
✅ Missing element detection  
✅ Risk assessment  
✅ Clarifying questions  
✅ URL content analysis  

## 🎓 Next Steps

1. **Read**: `Strategy/TESTING_GUIDE.md` (5 min)
2. **Test**: Run interactive tester (15 min)
3. **Explore**: Try your own strategies (15 min)

## ⚡ Quick Test

```powershell
cd Strategy
python interactive_strategy_tester.py
```

Then:
1. Enter your username
2. Select option 3 (Load example strategy)
3. Choose example 1 (EMA Crossover)
4. Review the AI-generated recommendations!

## 🎉 What You'll Get

For each strategy:
- ✅ Canonicalized steps (structured format)
- ✅ Classification (type, risk, instruments)
- ✅ AI-powered recommendations
- ✅ Confidence score
- ✅ Next actions
- ✅ Machine-readable JSON

## 💡 Example Session

```
> Enter your strategy:
Buy AAPL when 50 EMA crosses above 200 EMA.
Set stop at 2%, take profit at 5%.

✓ Strategy validated successfully

CANONICALIZED STEPS
1. Entry — 50 EMA crosses above 200 EMA
2. Exit — Stop at 2% OR profit at 5%

AI RECOMMENDATIONS
1. Add position sizing rule (Why: Fixed size risky)
2. Specify timeframe (Why: EMA behaves differently)
3. Add re-entry cooldown (Why: Prevents whipsaws)
```

## 🆘 Issues?

See `Strategy/INTEGRATION_SUMMARY.md` for troubleshooting.

---

**Ready?** → `cd Strategy && python interactive_strategy_tester.py`
