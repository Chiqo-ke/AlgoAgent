# Strategy Creation Troubleshooting Guide

## Issue 1: UNIQUE constraint failed: strategy_api_strategy.name, strategy_api_strategy.version

### What Causes This Error
This error occurs when you try to create a strategy with a name and version combination that already exists in the database.

### Root Cause
- The Strategy model has a `unique_together` constraint on `(name, version)`
- When creating a new strategy with the same name, the system wasn't auto-incrementing the version
- This caused duplicate key violations

### Solution Implemented
✅ **Fixed in `/strategy_api/views.py`**

The `create_strategy_with_ai` endpoint now:
1. Checks if a strategy with the same name already exists
2. Automatically increments the version number
3. Appends version to the strategy name for clarity (e.g., "RSI Strategy v2")
4. Creates the strategy with a unique `(name, version)` combination

### How It Works
```python
# Before attempting to create:
base_name = strategy_name  # e.g., "RSI Strategy"
version_num = 1

# Check for existing strategies
existing_strategies = Strategy.objects.filter(name__startswith=base_name)
version_numbers = [extract_version(strat.version) for strat in existing_strategies]

# Get next available version
version_num = max(version_numbers) + 1 if version_numbers else 1

# Create with unique name/version
strategy = Strategy.objects.create(
    name=f"{base_name} v{version_num}",
    version=f"{version_num}.0.0",
    ...
)
```

### Testing the Fix
```bash
# Try creating the same strategy multiple times
curl -X POST http://localhost:8000/api/strategies/api/create_strategy_with_ai/ \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_text": "Buy when RSI < 30, sell when RSI > 70",
    "name": "RSI Strategy",
    "use_gemini": true
  }'

# Expected: First attempt succeeds
# Expected: Second attempt succeeds with auto-incremented version (v2)
# Expected: Third attempt succeeds with auto-incremented version (v3)
```

---

## Issue 2: Validation Failed - No Trades Executed in Test Period

### What Causes This Error
Your generated strategy code is syntactically correct but doesn't generate any actual trading signals during backtesting.

### Common Reasons
1. **Indicator conditions too strict** - Entry signal rarely or never triggers
2. **Data issues** - Market data doesn't match strategy requirements
3. **Parameter misalignment** - Signal thresholds don't align with actual data ranges
4. **Logic errors** - Strategy code has bugs preventing signal generation

### Example: Why This Fails
```python
# Too strict condition - might never trigger in real data
if rsi < 30 and price > moving_average_200 and volume > 1000000:
    # This combination might never all align
    buy_signal = True
```

### Solution

#### Option 1: Improve Your Strategy Description
Provide more detailed and realistic strategy descriptions:

```python
# ❌ Too Vague
"Buy when RSI is low and sell when RSI is high"

# ✅ Better
"Buy AAPL when RSI(14) drops below 30 on daily charts with volume above average. 
Exit when RSI exceeds 70 or after 5 days, whichever comes first. 
Use $10k capital with 2% stop loss."
```

#### Option 2: Include Specific Parameters
```json
{
  "strategy_text": "RSI momentum strategy on AAPL with 14-period RSI",
  "input_type": "detailed",
  "name": "AAPL RSI Momentum",
  "description": "Entry when RSI < 35, Exit when RSI > 65 or 5 bars pass",
  "use_gemini": true
}
```

#### Option 3: Use the Suggestions Provided
The improved error response now includes suggestions:
```json
{
  "error": "Strategy validation failed",
  "suggestions": [
    "Ensure your strategy description is clear and specific",
    "Include entry and exit signal descriptions",
    "Specify what indicators or conditions to use",
    "Try regenerating or modifying the strategy description"
  ]
}
```

#### Option 4: Check Backtest Data
Ensure your test data has the market movement patterns your strategy expects:

```bash
# View backtest data info
python manage.py shell
```

```python
import pandas as pd
# Check if data has enough variation for signals
df = pd.read_csv('./Data/your_symbol.csv')
print(df.describe())
# Look for columns with good variance
```

#### Option 5: Enable Relaxed Validation
If you're in development, temporarily disable strict validation:

```json
{
  "strategy_text": "Your strategy...",
  "use_gemini": true,
  "strict_mode": false
}
```

### API Response with Better Error Information

**Before (Now Improved):**
```json
{
  "error": "Strategy validation failed",
  "validation_result": {...}
}
```

**After (More Helpful):**
```json
{
  "error": "Strategy validation failed",
  "message": "No trades executed in 1-year test",
  "details": "The generated strategy code is valid but generated no signals",
  "suggestions": [
    "Ensure your strategy description is clear and specific",
    "Include entry and exit signal descriptions",
    "Specify what indicators or conditions to use",
    "Try regenerating or modifying the strategy description"
  ],
  "session_id": "chat_abc123",
  "validation_result": {...}
}
```

---

## Common Strategy Patterns That Work

### Pattern 1: Simple Moving Average Crossover
```
"Buy when fast MA (9-period) crosses above slow MA (21-period). 
Sell when fast MA crosses below slow MA. 
Use 1-day data for swing trading."
```

### Pattern 2: RSI Extreme Levels
```
"Buy when RSI(14) goes below 30 for 2 consecutive bars. 
Sell when RSI exceeds 70 or after 10 bars. 
Risk 2% per trade."
```

### Pattern 3: Support/Resistance
```
"Identify support at 20-day low. Buy when price bounces from support. 
Take profit at 20-day high. Stop loss 2% below entry."
```

### Pattern 4: Momentum
```
"Buy when price closes above 50-day moving average with volume above average. 
Sell when price closes below 50-day MA. Hold for maximum 20 days."
```

---

## Testing Your Strategy Locally

```bash
# 1. Navigate to monolithic_agent
cd monolithic_agent

# 2. Start Django shell
python manage.py shell

# 3. Test strategy creation
from strategy_api.views import StrategyViewSet
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

factory = APIRequestFactory()
request = factory.post('/api/strategies/api/create_strategy_with_ai/', {
    'strategy_text': 'Your test strategy',
    'use_gemini': True
})

viewset = StrategyViewSet()
viewset.request = request
response = viewset.create_strategy_with_ai(request)

print(f"Status: {response.status_code}")
print(f"Response: {response.data}")
```

---

## Changes Made to Fix These Issues

### File: `/monolithic_agent/strategy_api/views.py`

**Change 1: Auto-increment version on duplicate names**
- Location: Lines ~1075-1095
- Checks existing strategies with same name
- Extracts version numbers and finds next available
- Creates strategy with incremented version

**Change 2: Improved error handling**
- Location: Lines ~1030-1055
- Provides clear error message
- Includes specific failure reason
- Offers actionable suggestions
- Returns complete validation details

---

## Quick Reference: API Endpoint

### Create Strategy with AI

**Endpoint:** `POST /api/strategies/api/create_strategy_with_ai/`

**Required Fields:**
- `strategy_text` (string) - Natural language strategy description

**Optional Fields:**
- `name` (string) - Custom strategy name (auto-generated if omitted)
- `description` (string) - Detailed description
- `use_gemini` (boolean) - Use Gemini AI (default: true)
- `strict_mode` (boolean) - Require trades in backtest (default: false)
- `tags` (array) - Strategy tags for classification
- `template_id` (integer) - Link to existing template

**Success Response (201):**
```json
{
  "strategy": {...},
  "ai_validation": {...},
  "success": true,
  "session_id": "...",
  "auto_created_template": {...}
}
```

**Error Response (400/500):**
```json
{
  "error": "Strategy validation failed",
  "message": "...",
  "suggestions": [...],
  "session_id": "..."
}
```

---

## Prevention Checklist

- ✅ Use descriptive, specific strategy descriptions
- ✅ Include entry and exit signal definitions
- ✅ Specify indicators and their parameters
- ✅ Consider realistic market conditions
- ✅ Test with different strategy descriptions
- ✅ Check backtest data availability
- ✅ Provide expected timeframe and holding period
- ✅ Include risk management rules

---

## Need Help?

1. **Check logs:** `tail -f logs/algoagent.log`
2. **Test endpoint:** Use Postman or curl to test API directly
3. **Database:** Review existing strategies with `Strategy.objects.all()`
4. **Validator:** Check strategy validator output in response
5. **Conversation:** Review session history for detailed feedback
