# Interactive Backtest with Strategy Integration

## Overview

The Interactive Backtest Runner now integrates with the Strategy module, allowing users to:
1. **Enter new strategies** - Describe strategies in plain English
2. **Validate strategies** - AI-powered validation and canonicalization
3. **Generate code** - Automatic Python code generation from canonical JSON
4. **Run backtests** - Execute strategies with custom parameters

## New Features

### 🎯 Strategy Selection Options

When running a backtest, you now have **three options** for strategy selection:

1. **Enter a new strategy** - AI validates and generates code
2. **Use existing strategy** - Select from previously generated strategies
3. **Use example strategy** - Quick start with built-in examples

### 🔄 Complete Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Enter Symbol & Dates (AAPL, 2024-01-01 to 2024-10-22)   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Select Data Interval (1d, 1h, 30m, etc.)                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Fetch Market Data (from Yahoo Finance via Data module)  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. STRATEGY SELECTION (NEW!)                                │
│                                                              │
│  Option 1: NEW STRATEGY                                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ • Enter strategy description                           │ │
│  │ • AI validates (Strategy module)                       │ │
│  │ • Generates canonical JSON                             │ │
│  │ • Creates Python code (Gemini)                         │ │
│  │ • Saves to Backtest/codes/                             │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  Option 2: EXISTING STRATEGY                                │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ • Lists strategies in Backtest/codes/                  │ │
│  │ • User selects one                                     │ │
│  │ • Loads strategy class                                 │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  Option 3: EXAMPLE STRATEGY                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ • Uses SimpleMAStrategy                                │ │
│  │ • User can customize parameters                        │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Configure Strategy Parameters                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Run Backtest Simulation                                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Display Results & Save                                   │
└─────────────────────────────────────────────────────────────┘
```

## Usage Examples

### Example 1: New Strategy from Scratch

```bash
cd Backtest
python interactive_backtest_runner.py
```

**Session:**
```
Symbol: AAPL
From: 2024-01-01
To: 2024-10-22
Interval: 1d

STRATEGY SELECTION
  1. Enter a new strategy
  2. Use existing strategy
  3. Use example strategy
Select: 1

ENTER NEW STRATEGY
Describe your trading strategy...

[User enters:]
Buy when RSI drops below 30 and price is above 200-day MA.
Sell when RSI goes above 70.
Stop loss at 3% below entry.
Position size: 100 shares.

⏳ Analyzing strategy with AI assistance...
✓ Strategy validated successfully!

CANONICALIZED STRATEGY
Step 1: Entry - RSI < 30 and price > 200 MA
Step 2: Exit - RSI > 70
Step 3: Stop Loss - 3% below entry

⏳ Generating Python code with Gemini AI...
✓ Strategy code generated!
  Python: Backtest/codes/rsi_mean_reversion.py
  JSON: Backtest/codes/rsi_mean_reversion.json

✓ Strategy class loaded: RsiMeanReversion

[Backtest runs...]
```

### Example 2: Use Existing Strategy

```bash
cd Backtest
python interactive_backtest_runner.py
```

**Session:**
```
Symbol: MSFT
From: 2024-06-01
To: 2024-10-22
Interval: 1d

STRATEGY SELECTION
Select: 2

EXISTING STRATEGIES
  1. ema_crossover_strategy
  2. rsi_mean_reversion
  3. momentum_breakout
Select: 2

✓ Selected: rsi_mean_reversion.py
✓ Strategy class loaded: RsiMeanReversion

STRATEGY PARAMETERS
  threshold: 30
  Enter value (or press Enter for default): 25

[Backtest runs...]
```

### Example 3: Quick Test with Example

```bash
cd Backtest
python interactive_backtest_runner.py
```

**Session:**
```
Symbol: GOOGL
From: 2024-09-01
To: 2024-10-22
Interval: 1d

STRATEGY SELECTION
Select: 3

⚠️  Using example Simple MA Crossover strategy

Customize strategy parameters? N

✓ Strategy parameters:
  Fast MA: 10
  Slow MA: 30
  Position Size: 100

[Backtest runs...]
```

## Integration Points

### Strategy Module Integration

The interactive runner now uses components from the **Strategy module**:

```python
from strategy_validator import StrategyValidatorBot

# Validate user's strategy
validator = StrategyValidatorBot(
    username="backtest_user",
    strict_mode=False,
    use_gemini=True
)

result = validator.process_input(strategy_text, "auto")
```

**Features Used:**
- ✅ Natural language strategy parsing
- ✅ AI-powered validation and canonicalization
- ✅ Security guardrails
- ✅ Canonical JSON generation
- ✅ Classification and recommendations

### Code Generation Integration

Uses **Gemini Strategy Generator** from Backtest module:

```python
from gemini_strategy_generator import GeminiStrategyGenerator

# Generate Python code
generator = GeminiStrategyGenerator()
code = generator.generate_strategy(
    description=strategy_description,
    strategy_name="MyStrategy"
)
```

**Features Used:**
- ✅ Canonical JSON to Python code
- ✅ SimBroker API compliance
- ✅ Proper imports and structure
- ✅ run_backtest() function generation

### Strategy Manager Similarity

Similar workflow to `strategy_manager.py`:

| Strategy Manager | Interactive Runner |
|------------------|-------------------|
| Scans codes/ for JSON | User enters strategy text |
| Checks for .py files | Validates with AI |
| Generates missing code | Generates code immediately |
| Runs backtest via CLI | Runs backtest interactively |

## File Organization

```
AlgoAgent/
├── Strategy/                           # Strategy validation module
│   ├── strategy_validator.py          # ◄── VALIDATES strategies
│   ├── interactive_strategy_tester.py # Standalone tester
│   └── ...
│
└── Backtest/                           # Backtest execution module
    ├── interactive_backtest_runner.py # ◄── MAIN integrated runner
    ├── gemini_strategy_generator.py   # ◄── GENERATES code
    ├── strategy_manager.py            # CLI strategy manager
    └── codes/                          # ◄── Generated strategies
        ├── ema_crossover.py
        ├── ema_crossover.json
        ├── rsi_mean_reversion.py
        └── rsi_mean_reversion.json
```

## New Functions

### Strategy Selection

```python
def get_user_strategy_choice() -> str
```
Prompts user to choose strategy source (new/existing/example).

### Strategy Entry

```python
def enter_new_strategy() -> Optional[str]
```
Allows user to enter strategy description in plain English.

### Validation

```python
def validate_and_canonicalize_strategy(strategy_text: str) -> Optional[Dict]
```
Validates strategy using Strategy module's AI-powered validator.

### Code Generation

```python
def generate_strategy_code(canonical_json: str, strategy_name: str) -> Optional[Path]
```
Generates Python code from canonical JSON using Gemini.

### Strategy Management

```python
def list_existing_strategies() -> List[Path]
def select_existing_strategy() -> Optional[Path]
def load_strategy_class_from_file(python_file: Path)
def get_strategy_parameters(strategy_class) -> Dict[str, Any]
```

## Requirements

### Python Packages

```bash
# Existing requirements
pip install yfinance pandas numpy

# New requirements for strategy integration
pip install google-generativeai python-dotenv
```

### API Keys

Set your Gemini API key:

```bash
# Create .env file in project root
echo "GEMINI_API_KEY=your_key_here" > .env
```

Or set environment variable:

```bash
# Windows
set GEMINI_API_KEY=your_key_here

# Linux/Mac
export GEMINI_API_KEY=your_key_here
```

## Benefits

### Before (v1.0)
```python
# Hardcoded strategy
from Backtest.example_strategy import SimpleMAStrategy

strategy = SimpleMAStrategy(broker, fast=10, slow=30, size=100)
```

### After (v2.0)
```
User enters:
"Buy when price breaks above 20-day high.
 Sell when price drops 2% from entry.
 Risk 1% per trade."

System:
✓ Validates strategy
✓ Generates canonical JSON
✓ Creates Python code
✓ Runs backtest
✓ Saves to codes/
```

## Error Handling

The system includes comprehensive error handling:

1. **Validation Failures**
   - User can retry with modified strategy
   - Clear error messages from AI

2. **Code Generation Failures**
   - Fallback to example strategy option
   - Error logs for debugging

3. **Strategy Loading Failures**
   - Checks for valid strategy classes
   - Returns to selection menu

## Testing

### Test New Strategy Flow

```bash
python interactive_backtest_runner.py

# Test with simple strategy
Strategy: "Buy when RSI < 30, sell when RSI > 70"
```

### Test Existing Strategy Flow

```bash
# First generate a strategy
python strategy_manager.py --generate

# Then use it in backtest
python interactive_backtest_runner.py
# Select option 2 (existing)
```

### Test Example Strategy Flow

```bash
python interactive_backtest_runner.py
# Select option 3 (example)
```

## Comparison Matrix

| Feature | interactive_strategy_tester.py | strategy_manager.py | interactive_backtest_runner.py (v2.0) |
|---------|-------------------------------|---------------------|--------------------------------------|
| **Purpose** | Test strategy validation | Manage & generate strategies | Run complete backtests |
| **User Input** | Strategy text | JSON files in codes/ | Symbol, dates, strategy |
| **Validation** | ✅ Yes | ❌ No | ✅ Yes |
| **Code Generation** | ❌ No | ✅ Yes | ✅ Yes |
| **Run Backtest** | ❌ No | ✅ Yes (CLI) | ✅ Yes (Interactive) |
| **Data Fetching** | ❌ No | ❌ No | ✅ Yes (Real-time) |
| **Results Export** | ❌ No | ✅ Yes | ✅ Yes |
| **Interactive Flow** | ✅ Yes | ❌ No | ✅ Yes |

## Next Steps

1. **Run First Test**
   ```bash
   cd Backtest
   python interactive_backtest_runner.py
   ```

2. **Try New Strategy**
   - Enter a simple strategy description
   - Watch AI validate and generate code
   - See backtest results

3. **Build Strategy Library**
   - Generate multiple strategies
   - Reuse them from existing strategies menu
   - Compare performance across symbols

4. **Advanced Usage**
   - Modify generated strategies
   - Fine-tune parameters
   - Combine with different data intervals

## Troubleshooting

### "Strategy validator not available"
**Fix:** Ensure Strategy module is in parent directory
```bash
ls ../Strategy/strategy_validator.py
```

### "Gemini generator not available"
**Fix:** Install google-generativeai and set API key
```bash
pip install google-generativeai
echo "GEMINI_API_KEY=your_key" > .env
```

### "No strategy class found"
**Fix:** Check generated Python file has valid strategy class
```bash
cat codes/your_strategy.py
```

## Summary

The **Interactive Backtest Runner v2.0** now provides a complete end-to-end workflow:

1. ✅ Interactive symbol and date selection
2. ✅ Real-time data fetching
3. ✅ **NEW:** AI-powered strategy validation
4. ✅ **NEW:** Automatic code generation
5. ✅ **NEW:** Strategy library management
6. ✅ Full backtest execution
7. ✅ Comprehensive results

**One tool, complete workflow!** 🚀
