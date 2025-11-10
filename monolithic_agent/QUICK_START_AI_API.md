# Quick Start: AI Strategy API Integration

## 🚀 Start Here

### 0. Install Dependencies (First Time Only)
```bash
cd c:\Users\nyaga\Documents\AlgoAgent
pip install -r strategy_requirements.txt
```

This installs:
- `jsonschema` - JSON schema validation
- `google-generativeai` - Gemini AI API
- `python-dotenv` - Environment variables

### 1. Start Django Server
```bash
cd c:\Users\nyaga\Documents\AlgoAgent
python manage.py runserver
```

### 2. Test with cURL (Quick Test)

#### Validate a Strategy
```bash
curl -X POST http://localhost:8000/api/strategies/api/validate_strategy_with_ai/ ^
  -H "Content-Type: application/json" ^
  -d "{\"strategy_text\": \"Buy when RSI < 30, sell when RSI > 70. Stop at 2%%.\", \"input_type\": \"freetext\", \"use_gemini\": true}"
```

#### Create a Strategy
```bash
curl -X POST http://localhost:8000/api/strategies/api/create_strategy_with_ai/ ^
  -H "Content-Type: application/json" ^
  -d "{\"strategy_text\": \"1. Buy: RSI < 30\n2. Sell: RSI > 70\n3. Stop: 2%%\", \"name\": \"RSI Strategy\", \"save_to_backtest\": true}"
```

### 3. Or Use Test Script
```bash
cd c:\Users\nyaga\Documents\AlgoAgent
python test_ai_strategy_api.py
```

### 4. Or Use Postman
1. Import `postman_collections/Strategy_AI_Validation_Collection.json`
2. Set environment `base_url` = `http://localhost:8000`
3. Run "1. Validate Strategy with AI"

## 📋 What You Get

Each API call returns:
- ✅ **Canonicalized Steps**: Structured, numbered strategy steps
- ✅ **Classification**: Strategy type (trend-following, mean-reversion, etc.)
- ✅ **AI Recommendations**: Prioritized improvement suggestions
- ✅ **Risk Assessment**: Low/medium/high risk tier
- ✅ **Confidence Level**: High/medium/low
- ✅ **Canonical JSON**: Complete canonical schema
- ✅ **Warnings**: Security and risk warnings
- ✅ **Next Actions**: Suggested improvements

## 🎯 Common Use Cases

### Use Case 1: Validate User Input
```json
POST /api/strategies/api/validate_strategy_with_ai/
{
  "strategy_text": "User's free-text description...",
  "input_type": "auto"
}
```
**Returns:** AI analysis without creating database records

### Use Case 2: Create Complete Strategy
```json
POST /api/strategies/api/create_strategy_with_ai/
{
  "strategy_text": "Numbered or free-text strategy...",
  "name": "My Strategy",
  "save_to_backtest": true
}
```
**Creates:** Strategy record + Template + Saves to Backtest/codes/

### Use Case 3: Edit Existing Strategy
```json
PUT /api/strategies/api/1/update_strategy_with_ai/
{
  "strategy_text": "Updated strategy description...",
  "update_description": "What changed"
}
```
**Updates:** Strategy + Template chat history

## 🔍 Example Response

```json
{
  "status": "success",
  "canonicalized_steps": [
    "Step 1: Entry Condition - Buy when RSI(14) < 30 (oversold)",
    "Step 2: Exit Condition - Sell when RSI(14) > 70 (overbought)"
  ],
  "classification": "Strategy Type: mean-reversion | Risk Tier: medium",
  "classification_detail": {
    "type": "mean-reversion",
    "risk_tier": "medium",
    "primary_instruments": []
  },
  "recommendations": "HIGH PRIORITY:\n1. Add stop-loss rule to protect capital\n2. Define position sizing strategy\n\nMEDIUM PRIORITY:\n3. Specify timeframe for RSI calculation",
  "recommendations_list": [
    {
      "title": "Add stop-loss rule",
      "priority": "high",
      "rationale": "Protect capital from large losses"
    }
  ],
  "confidence": "medium",
  "next_actions": [
    "Define position sizing strategy",
    "Add stop-loss and take-profit rules",
    "Specify timeframe (1m, 5m, 1h, etc.)"
  ],
  "warnings": [
    "Missing stop-loss - high risk without protection"
  ],
  "canonical_json": "{...}",
  "metadata": {
    "confidence": "medium",
    "created_at": "2025-10-28T15:00:00Z"
  }
}
```

## 📚 Full Documentation

- **Complete Guide**: `AI_STRATEGY_API_GUIDE.md`
- **Summary**: `STRATEGY_AI_INTEGRATION_SUMMARY.md`
- **Postman Collection**: `postman_collections/Strategy_AI_Validation_Collection.json`
- **Test Script**: `test_ai_strategy_api.py`

## ⚙️ Configuration

### Enable/Disable AI
```json
{
  "use_gemini": false  // Disables AI, uses basic validation
}
```

### Strict Security Mode
```json
{
  "strict_mode": true  // Raises exceptions on security violations
}
```

### Save to Backtest
```json
{
  "save_to_backtest": true  // Saves canonical JSON to Backtest/codes/
}
```

## 🐛 Troubleshooting

### "No module named 'jsonschema'" or other import errors
**Cause:** Missing dependencies  
**Fix:**
```bash
# Install all Strategy module dependencies
cd c:\Users\nyaga\Documents\AlgoAgent
pip install -r strategy_requirements.txt

# Or install individually
pip install jsonschema google-generativeai python-dotenv

# Then restart Django server
```

### "Strategy validator not available" or "No module named 'canonical_schema'"
**Cause:** Strategy module import path issue  
**Fix:**
```bash
# 1. Verify Strategy/__init__.py exists
cd c:\Users\nyaga\Documents\AlgoAgent\Strategy
dir __init__.py

# 2. Test import
cd ..
python -c "from Strategy.strategy_validator import StrategyValidatorBot; print('OK')"

# 3. If still fails, run verification script
python test_strategy_import.py
```

**If import still fails:**
- Restart Django server (Ctrl+C, then `python manage.py runserver`)
- Check `STRATEGY_IMPORT_FIX.md` for detailed solutions

### "Gemini API error"
**Fix:** Check environment variable
```bash
# Windows
echo %GEMINI_API_KEY%

# If not set
set GEMINI_API_KEY=your_api_key_here
```

### "Server not running" or Connection refused
**Fix:** Start Django server
```bash
cd c:\Users\nyaga\Documents\AlgoAgent
python manage.py runserver
```

### 503 Service Unavailable
**Cause:** Django server not running or crashed  
**Fix:**
```bash
# Check if server is running
netstat -an | findstr :8000

# Restart server
python manage.py runserver
```

### Import errors after restart
**Fix:** Clear Python cache
```bash
cd c:\Users\nyaga\Documents\AlgoAgent
# Delete __pycache__ folders
del /s /q __pycache__
# Restart server
python manage.py runserver
```

## ✅ Quick Verification

### Test 1: Import Check
```bash
python test_strategy_import.py
```
Expected output:
```
✓ StrategyValidatorBot imported successfully
✓ StrategyValidatorBot initialized successfully
✓ Validation completed
✅ ALL TESTS PASSED!
```

### Test 2: API Check
```bash
python test_ai_strategy_api.py
```
Expected output:
```
✓ PASS - health
✓ PASS - validation  
✓ PASS - creation
✓ PASS - update
✓ PASS - freetext

All tests passed!
```

### Test 3: Health Endpoint
```bash
curl http://localhost:8000/api/strategies/api/health/
```
Expected response:
```json
{
  "status": "healthy",
  "validator_available": true,
  "generator_available": true
}
```

## 🎉 You're Ready!

The API is now fully integrated with the AI strategy validation system. Your endpoint `/api/strategies/api/create_strategy/` now has AI-powered validation capabilities through the new endpoints!
