# Interactive Backtest Runner v2.0 - Strategy Integration Summary

## What Was Done

I've successfully integrated the **Strategy module** workflow into the **Interactive Backtest Runner**, creating a seamless end-to-end backtesting system. Users can now enter strategies in plain English, have them validated by AI, generate code automatically, and run backtests—all in one interactive session.

## Key Changes

### 1. Enhanced Imports

Added integration with Strategy module and Gemini generator:

```python
# Strategy module integration
from strategy_validator import StrategyValidatorBot

# Gemini code generator
from gemini_strategy_generator import GeminiStrategyGenerator
```

### 2. New Strategy Selection Flow

Added three options for strategy selection:

**Option 1: Enter New Strategy**
- User describes strategy in plain English
- AI validates using `StrategyValidatorBot`
- Generates canonical JSON
- Creates Python code using `GeminiStrategyGenerator`
- Saves to `Backtest/codes/`

**Option 2: Use Existing Strategy**
- Lists strategies in `Backtest/codes/`
- User selects one
- Loads strategy class dynamically

**Option 3: Use Example Strategy**
- Quick start with `SimpleMAStrategy`
- User can customize parameters

### 3. New Functions Added

#### Strategy Selection
```python
get_user_strategy_choice() -> str
```
Prompts user to choose strategy source.

#### Strategy Entry
```python
enter_new_strategy() -> Optional[str]
```
Multi-line strategy description input.

#### Validation & Canonicalization
```python
validate_and_canonicalize_strategy(strategy_text: str) -> Optional[Dict]
```
Uses Strategy module's AI-powered validator:
- Parses natural language
- Security guardrails
- Generates canonical JSON
- Classification and recommendations

#### Code Generation
```python
generate_strategy_code(canonical_json: str, strategy_name: str) -> Optional[Path]
```
Generates Python code from canonical JSON:
- Uses Gemini AI
- Creates SimBroker-compatible code
- Saves `.py` and `.json` files

#### Strategy Management
```python
list_existing_strategies() -> List[Path]
select_existing_strategy() -> Optional[Path]
load_strategy_class_from_file(python_file: Path)
get_strategy_parameters(strategy_class) -> Dict[str, Any]
```

### 4. Enhanced Main Function

The main workflow now includes strategy selection before backtest execution:

```
1. Symbol & Dates → 2. Interval → 3. Fetch Data → 4. Config →
5. Initialize Broker → 6. **STRATEGY SELECTION** → 7. Run Backtest →
8. Display Results → 9. Save
```

## Complete Workflow Example

### User Session

```bash
cd Backtest
python interactive_backtest_runner.py
```

```
========================================
INTERACTIVE BACKTEST RUNNER
========================================

STOCK SYMBOL SELECTION
Enter stock symbol: AAPL
✓ Selected symbol: AAPL

DATE RANGE SELECTION
From (start date): 2024-01-01
✓ Start date: 2024-01-01
To (end date): 2024-10-22
✓ End date: 2024-10-22
📅 Backtest period: 295 days

DATA INTERVAL SELECTION
Select interval: 1
✓ Selected interval: 1d

FETCHING MARKET DATA
✓ Data fetched successfully!
  Total bars: 207

BACKTEST CONFIGURATION
Use default configuration? Y
✓ Configuration set

INITIALIZING BROKER
✓ SimBroker initialized (API v3.0.0)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STRATEGY SELECTION (NEW!)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. Enter a new strategy (will be validated and generated)
  2. Use existing strategy from Backtest/codes/
  3. Use example strategy
Select: 1

ENTER NEW STRATEGY
Enter your strategy (press Enter twice when done):

Buy when RSI drops below 30 and price is above 200-day moving average.
Sell when RSI goes above 70.
Stop loss at 3% below entry.
Position size: 100 shares per trade.

[User presses Enter twice]

VALIDATING STRATEGY
⏳ Analyzing strategy with AI assistance...
✓ Strategy validated successfully!

CANONICALIZED STRATEGY
Step 1: Entry - RSI < 30 AND Price > 200 MA
  Trigger: RSI crosses below 30
  Condition: Price above 200-day MA
  Action: BUY 100 shares
  
Step 2: Exit - RSI > 70
  Trigger: RSI crosses above 70
  Action: SELL position
  
Step 3: Stop Loss
  Trigger: Price drops 3% below entry
  Action: SELL position

CLASSIFICATION
  Type: mean-reversion
  Risk Tier: medium

GENERATING STRATEGY CODE
⏳ Generating Python code with Gemini AI...
✓ Strategy code generated!
  Python: Backtest/codes/rsi_mean_reversion.py
  JSON: Backtest/codes/rsi_mean_reversion.json

✓ Strategy class loaded: RsiMeanReversion

STRATEGY PARAMETERS
Available parameters:
  rsi_period: 14
    Enter value (or press Enter for default): 
  rsi_oversold: 30
    Enter value (or press Enter for default): 25
  rsi_overbought: 70
    Enter value (or press Enter for default): 
  ma_period: 200
    Enter value (or press Enter for default): 
  position_size: 100
    Enter value (or press Enter for default): 

✓ Strategy ready: RsiMeanReversion

RUNNING BACKTEST SIMULATION
✓ Strategy initialized: RsiMeanReversion

Simulating 207 bars...
  Progress: 100% ✓

✓ Simulation complete!

========================================
BACKTEST RESULTS
========================================
Period: 2024-01-02 to 2024-10-22
Duration: 294 days

Starting Capital: $100,000.00
Final Equity: $108,456.78
Net Profit: $8,456.78 (8.46%)

Total Trades: 15
Winning Trades: 10
Losing Trades: 5
Win Rate: 66.7%

Sharpe Ratio: 1.89
Max Drawdown: $3,245.12 (3.24%)
========================================

Save results to files? Y

SAVING RESULTS
✓ Trades saved to: results/AAPL_trades_20241022_165432.csv
✓ Metrics saved to: results/AAPL_metrics_20241022_165432.json

========================================
BACKTEST COMPLETE
========================================
```

## Integration Architecture

```
┌────────────────────────────────────────────────────────────┐
│                  USER INTERACTION                          │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────────┐
│         Interactive Backtest Runner (v2.0)                 │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. Symbol & Date Selection                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                       │                                     │
│                       ▼                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 2. Data Fetching (Data Module)                      │  │
│  │    └─► DataFetcher.fetch_data_by_date_range()      │  │
│  └──────────────────────────────────────────────────────┘  │
│                       │                                     │
│                       ▼                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 3. Strategy Selection (NEW!)                        │  │
│  │                                                      │  │
│  │  ┌─────────────────────────────────────────────┐   │  │
│  │  │ Option 1: New Strategy                      │   │  │
│  │  │   ├─► User enters description               │   │  │
│  │  │   ├─► Strategy Module validates             │   │  │
│  │  │   │    └─► StrategyValidatorBot             │   │  │
│  │  │   │        └─► AI parsing & canonicalization│   │  │
│  │  │   ├─► Generates canonical JSON              │   │  │
│  │  │   └─► Gemini generates Python code          │   │  │
│  │  │       └─► GeminiStrategyGenerator           │   │  │
│  │  └─────────────────────────────────────────────┘   │  │
│  │                                                      │  │
│  │  ┌─────────────────────────────────────────────┐   │  │
│  │  │ Option 2: Existing Strategy                 │   │  │
│  │  │   ├─► List codes/ directory                 │   │  │
│  │  │   ├─► User selects                          │   │  │
│  │  │   └─► Dynamic class loading                 │   │  │
│  │  └─────────────────────────────────────────────┘   │  │
│  │                                                      │  │
│  │  ┌─────────────────────────────────────────────┐   │  │
│  │  │ Option 3: Example Strategy                  │   │  │
│  │  │   └─► SimpleMAStrategy with params          │   │  │
│  │  └─────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
│                       │                                     │
│                       ▼                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 4. Backtest Execution                                │  │
│  │    ├─► SimBroker simulation                         │  │
│  │    ├─► Strategy.on_bar() calls                      │  │
│  │    └─► Metrics computation                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                       │                                     │
│                       ▼                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 5. Results & Export                                  │  │
│  │    ├─► Display comprehensive metrics                │  │
│  │    └─► Save CSV and JSON files                      │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

## Files Modified

### Main File
- **`interactive_backtest_runner.py`** - Enhanced with strategy integration

### New Documentation
- **`STRATEGY_INTEGRATION_GUIDE.md`** - Complete usage guide
- **`STRATEGY_INTEGRATION_SUMMARY.md`** - This summary

## Requirements

### Existing
```bash
pip install yfinance pandas numpy
```

### New (for strategy integration)
```bash
pip install google-generativeai python-dotenv
```

### Configuration
Create `.env` file with Gemini API key:
```bash
GEMINI_API_KEY=your_api_key_here
```

## Benefits

### ✅ Complete End-to-End Workflow
One script handles everything from strategy creation to backtest results.

### ✅ AI-Powered Strategy Validation
Leverages Strategy module's validation with Gemini AI:
- Natural language parsing
- Security guardrails
- Canonical JSON generation
- Intelligent recommendations

### ✅ Automatic Code Generation
No manual coding required:
- Describe strategy in plain English
- AI generates SimBroker-compatible Python code
- Saves to organized directory structure

### ✅ Flexible Strategy Sources
Three ways to get strategies:
- Generate new ones on the fly
- Reuse existing validated strategies
- Quick start with examples

### ✅ Strategy Library Management
- All generated strategies saved to `codes/`
- Canonical JSON preserved alongside Python code
- Easy to reuse and share

## Comparison: Before vs After

### Before (v1.0)
```python
# Fixed to example strategy
from Backtest.example_strategy import SimpleMAStrategy

strategy = SimpleMAStrategy(broker, fast=10, slow=30, size=100)
# User had to modify code to use different strategies
```

### After (v2.0)
```
User:
  "Buy when RSI < 30 and price > 200 MA.
   Sell when RSI > 70. Stop at 3%."

System:
  ✓ Validates with AI
  ✓ Generates canonical JSON
  ✓ Creates Python code
  ✓ Loads and runs strategy
  ✓ Saves for future use
```

## Integration with Strategy Manager

The interactive runner now follows the same pattern as `strategy_manager.py`:

| Aspect | strategy_manager.py | interactive_backtest_runner.py |
|--------|---------------------|-------------------------------|
| **Input** | JSON files in codes/ | User text description |
| **Validation** | No (assumes valid JSON) | Yes (AI-powered) |
| **Code Gen** | Yes (for missing .py) | Yes (immediate) |
| **Execution** | CLI batch mode | Interactive session |
| **Results** | Saved to results/ | Saved to results/ |

## Testing

### Quick Test

```bash
cd Backtest
python interactive_backtest_runner.py

# Try it with:
Symbol: AAPL
From: 2024-09-01
To: 2024-10-22
Interval: 1d
Strategy: [Option 3 - Example]
```

### Full Test (New Strategy)

```bash
python interactive_backtest_runner.py

# Enter:
Symbol: MSFT
Dates: 2024-01-01 to 2024-10-22
Strategy: [Option 1 - New]

# Describe:
"Buy when price breaks above 50-day high.
 Sell when price drops 2% from entry.
 Risk 1% of capital per trade."

# Watch as system:
- Validates strategy
- Generates code
- Runs backtest
- Saves results
```

## Directory Structure After Use

```
Backtest/
├── interactive_backtest_runner.py    # ◄── Enhanced with strategy integration
├── gemini_strategy_generator.py      # Used for code generation
├── STRATEGY_INTEGRATION_GUIDE.md     # Usage documentation
├── codes/                             # ◄── Generated strategies
│   ├── rsi_mean_reversion.py         # Generated Python code
│   ├── rsi_mean_reversion.json       # Canonical JSON
│   ├── breakout_strategy.py
│   ├── breakout_strategy.json
│   └── ...
└── results/                           # Backtest results
    ├── AAPL_trades_*.csv
    ├── AAPL_metrics_*.json
    └── ...
```

## Next Steps

1. **Try It Out**
   ```bash
   cd Backtest
   python interactive_backtest_runner.py
   ```

2. **Enter Your First Strategy**
   - Choose "Enter a new strategy"
   - Describe a simple strategy
   - Watch AI validate and generate code

3. **Build Your Strategy Library**
   - Create multiple strategies
   - Save them for reuse
   - Compare performance

4. **Advanced Usage**
   - Fine-tune generated strategies
   - Modify parameters
   - Test across different symbols

## Support

- **Full Guide**: See `STRATEGY_INTEGRATION_GUIDE.md`
- **Setup Help**: See `SETUP_GUIDE.md`
- **Quick Reference**: See `QUICK_REFERENCE.md`
- **Original Docs**: See `INTERACTIVE_BACKTEST_README.md`

## Summary

**Version 2.0 Achievement:** 🎉

✅ **Strategy Module Integration** - Seamless validation and canonicalization  
✅ **AI-Powered Code Generation** - From text to executable Python  
✅ **Three Strategy Sources** - New, existing, or example  
✅ **Complete Workflow** - One tool, end-to-end  
✅ **Organized Output** - Canonical JSON + Python code  
✅ **Reusable Library** - Build your strategy collection  

**The Interactive Backtest Runner is now a complete strategy development and testing platform!** 🚀
