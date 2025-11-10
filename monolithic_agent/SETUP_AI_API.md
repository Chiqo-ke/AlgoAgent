# Complete Setup Guide: AI Strategy Validation API

## Prerequisites
- Python 3.8+ installed
- Django server configured
- AlgoAgent project cloned

## Step-by-Step Setup

### Step 1: Install Dependencies

```bash
cd c:\Users\nyaga\Documents\AlgoAgent

# Install Strategy module dependencies
pip install -r strategy_requirements.txt
```

**What gets installed:**
- ✅ `jsonschema` - JSON schema validation for canonical format
- ✅ `google-generativeai` - Gemini AI API for intelligent analysis
- ✅ `python-dotenv` - Environment variable management

### Step 2: Set Up Environment Variables

Create or update `.env` file in AlgoAgent root:

```bash
# .env file
GEMINI_API_KEY=your_gemini_api_key_here
```

**Get Gemini API Key:**
1. Go to https://makersuite.google.com/app/apikey
2. Create a new API key
3. Copy and paste into `.env` file

**Windows Alternative (without .env file):**
```bash
# Set in current session
set GEMINI_API_KEY=your_api_key_here

# Set permanently
setx GEMINI_API_KEY "your_api_key_here"
```

### Step 3: Verify Installation

```bash
# Test imports
python test_strategy_import.py
```

**Expected Output:**
```
✓ StrategyValidatorBot imported successfully
✓ StrategyValidatorBot initialized successfully
✓ Validation completed with status: success
✅ ALL TESTS PASSED!
```

### Step 4: Start Django Server

```bash
python manage.py runserver
```

**Expected Output:**
```
Django version 4.x.x, using settings 'algoagent_api.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

### Step 5: Test API Endpoints

```bash
# In a new terminal
python test_ai_strategy_api.py
```

**Expected Output:**
```
✓ PASS - health
✓ PASS - validation  
✓ PASS - creation
✓ PASS - update
✓ PASS - freetext

All tests passed!
```

## Verification Checklist

### ✅ Dependencies Installed
```bash
pip list | findstr "jsonschema google-generativeai dotenv"
```
Should show:
- jsonschema (version 4.x.x)
- google-generativeai (version 0.x.x)
- python-dotenv (version 1.x.x)

### ✅ Environment Variable Set
```bash
# Windows
echo %GEMINI_API_KEY%

# Should show your API key (not "ECHO is off")
```

### ✅ Strategy Module Accessible
```bash
python -c "from Strategy.strategy_validator import StrategyValidatorBot; print('OK')"
```
Should print: `OK`

### ✅ API Health Check
```bash
curl http://localhost:8000/api/strategies/api/health/
```
Should return:
```json
{
  "status": "healthy",
  "validator_available": true,
  "generator_available": true
}
```

## Troubleshooting

### Issue 1: "No module named 'jsonschema'"

**Solution:**
```bash
pip install jsonschema
# Restart Django server
```

### Issue 2: "No module named 'google.generativeai'"

**Solution:**
```bash
pip install google-generativeai
# Restart Django server
```

### Issue 3: "GEMINI_API_KEY not found"

**Solution:**
```bash
# Create .env file in AlgoAgent root
echo GEMINI_API_KEY=your_key_here > .env

# Or set environment variable
set GEMINI_API_KEY=your_key_here

# Restart Django server
```

### Issue 4: "Strategy validator not available"

**Solution:**
```bash
# 1. Verify Strategy/__init__.py exists
dir Strategy\__init__.py

# 2. Test import directly
python test_strategy_import.py

# 3. Clear Python cache
del /s /q __pycache__

# 4. Restart Django server
python manage.py runserver
```

### Issue 5: Import errors persist

**Solution:**
```bash
# Nuclear option - reinstall everything
pip uninstall -y jsonschema google-generativeai python-dotenv
pip install -r strategy_requirements.txt

# Clear all caches
del /s /q __pycache__
del /s /q *.pyc

# Restart Django
python manage.py runserver
```

## Success Criteria

After setup, you should be able to:

✅ **Import the validator:**
```python
from Strategy.strategy_validator import StrategyValidatorBot
bot = StrategyValidatorBot()
```

✅ **Call the API:**
```bash
curl -X POST http://localhost:8000/api/strategies/api/validate_strategy_with_ai/ \
  -H "Content-Type: application/json" \
  -d '{"strategy_text": "Buy when RSI < 30", "input_type": "freetext"}'
```

✅ **Get AI responses:**
```json
{
  "status": "success",
  "canonicalized_steps": [...],
  "recommendations": "AI-powered suggestions...",
  "confidence": "medium"
}
```

## Next Steps

Once setup is complete:

1. **Import Postman Collection:**
   - `Quick_AI_Strategy_Validation.json`

2. **Read Documentation:**
   - `AI_STRATEGY_API_GUIDE.md` - Complete API guide
   - `QUICK_START_AI_API.md` - Quick reference

3. **Start Testing:**
   - Use Postman collection
   - Or run `python test_ai_strategy_api.py`

4. **Integrate with Frontend:**
   - Use API endpoints in your React/Vue/Angular app
   - Display AI recommendations in UI

## Additional Resources

- **Gemini API Docs:** https://ai.google.dev/docs
- **JSONSchema Docs:** https://json-schema.org/
- **Django REST Framework:** https://www.django-rest-framework.org/

## Support

If you encounter issues:

1. Check `STRATEGY_IMPORT_FIX.md` for detailed solutions
2. Run `python test_strategy_import.py` for diagnostics
3. Check Django logs for error details
4. Verify all dependencies with `pip list`

---

**Setup Complete! 🎉**

You now have AI-powered strategy validation integrated into your API!
