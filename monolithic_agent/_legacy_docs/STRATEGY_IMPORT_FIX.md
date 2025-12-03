# Strategy Module Import Fix

## Problem
```
Service Unavailable: /api/strategies/api/create_strategy_with_ai/
"error": "Strategy validator not available",
"details": "No module named 'canonical_schema'"
OR
"details": "No module named 'jsonschema'"
```

## Root Cause
1. The Strategy module wasn't being recognized as a Python package
2. Missing required dependencies (jsonschema, google-generativeai)

## Solution Applied

### 1. Install Required Dependencies
```bash
cd c:\Users\nyaga\Documents\AlgoAgent
pip install -r strategy_requirements.txt
```

Or install individually:
```bash
pip install jsonschema>=4.20.0
pip install google-generativeai>=0.3.0
pip install python-dotenv>=1.0.0
```

### 2. Created `Strategy/__init__.py`
Made Strategy a proper Python package:
```python
# Strategy/__init__.py
__version__ = "1.0.0"
__all__ = ["StrategyValidatorBot", "CanonicalStrategy", ...]
```

### 2. Updated `strategy_validator.py`
Added explicit path setup:
```python
# Add Strategy directory to path
STRATEGY_DIR = Path(__file__).parent
if str(STRATEGY_DIR) not in sys.path:
    sys.path.insert(0, str(STRATEGY_DIR))
```

### 3. Updated `strategy_api/views.py`
Added Strategy directory to Python path:
```python
PARENT_DIR = Path(__file__).parent.parent
STRATEGY_DIR = PARENT_DIR / "Strategy"
if str(STRATEGY_DIR) not in sys.path:
    sys.path.insert(0, str(STRATEGY_DIR))
```

## Verification

### Quick Test
```bash
cd c:\Users\nyaga\Documents\AlgoAgent
python test_strategy_import.py
```

Should output:
```
✓ StrategyValidatorBot imported successfully
✓ StrategyValidatorBot initialized successfully
✓ Validation completed
✅ ALL TESTS PASSED!
```

### Django Test
Restart Django server:
```bash
cd c:\Users\nyaga\Documents\AlgoAgent
python manage.py runserver
```

Then test the endpoint:
```bash
curl -X POST http://localhost:8000/api/strategies/api/validate_strategy_with_ai/ ^
  -H "Content-Type: application/json" ^
  -d "{\"strategy_text\": \"Buy when RSI < 30\", \"input_type\": \"freetext\"}"
```

Should return 200 OK with AI validation results.

## Files Modified

1. ✅ `Strategy/__init__.py` - Created (makes it a package)
2. ✅ `Strategy/strategy_validator.py` - Updated imports
3. ✅ `strategy_api/views.py` - Added Strategy to path
4. ✅ `test_strategy_import.py` - Created (verification script)

## Alternative Fix (if still having issues)

If you still get import errors, try this in `strategy_api/views.py`:

```python
# More aggressive path setup
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STRATEGY_DIR = BASE_DIR / "Strategy"

# Add both to path
for path in [str(BASE_DIR), str(STRATEGY_DIR)]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Also try setting PYTHONPATH
os.environ['PYTHONPATH'] = f"{STRATEGY_DIR}:{os.environ.get('PYTHONPATH', '')}"
```

## Django Settings Alternative

Or add to `settings.py`:
```python
# settings.py
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STRATEGY_DIR = BASE_DIR / "Strategy"

sys.path.insert(0, str(STRATEGY_DIR))
```

## Restart Required

After making changes, always restart Django:
```bash
# Kill the server (Ctrl+C)
# Then restart
python manage.py runserver
```

## Expected Behavior After Fix

✅ Health check shows validator available:
```json
{
  "status": "healthy",
  "validator_available": true,
  "generator_available": true
}
```

✅ Validation works:
```json
{
  "status": "success",
  "canonicalized_steps": [...],
  "recommendations": "..."
}
```

✅ Strategy creation works:
```json
{
  "success": true,
  "strategy": {...},
  "ai_validation": {...}
}
```
