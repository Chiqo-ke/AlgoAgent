# AlgoAgent Strategy Creation - Bug Fixes Summary

## Date: December 2, 2025

### Issues Fixed

#### 1. **UNIQUE Constraint Violation**
**Error:** `django.db.utils.IntegrityError: UNIQUE constraint failed: strategy_api_strategy.name, strategy_api_strategy.version`

**Root Cause:**
- The `Strategy` model has a `unique_together` constraint on `(name, version)`
- When creating strategies with duplicate names, the system wasn't auto-incrementing versions
- This caused database integrity violations

**Solution Implemented:**
✅ Modified `/monolithic_agent/strategy_api/views.py` - `create_strategy_with_ai()` method

The endpoint now:
1. Detects if a strategy with the same name already exists
2. Finds the highest version number for that strategy
3. Auto-increments to the next version
4. Appends version suffix to strategy name (e.g., "RSI Strategy v2")
5. Creates the strategy with a unique `(name, version)` combination

**Code Changes:**
- Lines 1113-1133: Added duplicate detection and version increment logic
- Automatically generates version strings like "2.0.0", "3.0.0", etc.
- Updates strategy name to reflect version for clarity

---

#### 2. **Improved Validation Failure Handling**
**Error:** `Internal Server Error: /api/strategies/api/create_strategy_with_ai/`

**Root Cause:**
- When AI validation failed (e.g., no trades executed), response lacked helpful error information
- Generic error messages didn't guide users on how to fix their strategy

**Solution Implemented:**
✅ Enhanced error response with actionable feedback

**Code Changes:**
- Lines 1039-1059: Improved error handling
- Now returns:
  - Clear error message describing what failed
  - Specific details from validation
  - List of suggestions to fix the issue
  - Session ID for tracking conversation history
  - Complete validation result data

**Example Response:**
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

### Files Modified

#### `/monolithic_agent/strategy_api/views.py`

**Method:** `create_strategy_with_ai()` (lines 951-1238)

**Key Changes:**

1. **Error Response Enhancement (lines 1039-1059)**
   ```python
   return Response({
       'error': 'Strategy validation failed',
       'message': error_message,
       'details': ai_result.get('details', ''),
       'validation_result': ai_result,
       'session_id': conv_manager.session_id,
       'suggestions': [
           'Ensure your strategy description is clear and specific',
           'Include entry and exit signal descriptions',
           'Specify what indicators or conditions to use',
           'Try regenerating or modifying the strategy description'
       ]
   }, status=status.HTTP_400_BAD_REQUEST)
   ```

2. **Duplicate Name/Version Detection (lines 1113-1133)**
   ```python
   # Handle duplicate name/version constraint
   base_name = strategy_name
   version_num = 1
   existing = Strategy.objects.filter(name=strategy_name, version='1.0.0').first()
   if existing:
       # Find the highest version number for this strategy name
       existing_strategies = Strategy.objects.filter(name__startswith=base_name)
       version_numbers = []
       for strat in existing_strategies:
           try:
               # Parse version string like "1.0.0" to extract major version
               parts = str(strat.version).split('.')
               version_numbers.append(int(parts[0]))
           except (ValueError, IndexError):
               pass
       
       version_num = max(version_numbers) + 1 if version_numbers else 1
       strategy_name = f"{base_name} v{version_num}"
   
   version_str = f"{version_num}.0.0"
   ```

3. **Updated Strategy Creation (lines 1135-1150)**
   ```python
   strategy = Strategy.objects.create(
       name=strategy_name,
       version=version_str,  # Now uses auto-incremented version
       description=data.get('description', canonical_data.get('description', '')),
       template=template,
       strategy_code=canonical_json_str,
       parameters=canonical_data.get('metadata', {}),
       tags=data.get('tags', classification.get('primary_instruments', [])),
       timeframe=timeframe,
       risk_level=risk_tier,
       expected_return=expected_return,
       max_drawdown=max_drawdown,
       created_by=request.user if request.user.is_authenticated else None
   )
   ```

---

### Testing the Fixes

#### Test 1: Duplicate Strategy Names
```bash
# First request - should succeed
curl -X POST http://localhost:8000/api/strategies/api/create_strategy_with_ai/ \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_text": "Buy when RSI < 30, sell when RSI > 70",
    "name": "RSI Strategy",
    "use_gemini": true
  }'

# Expected: Success (201)
# Response includes: strategy with name "RSI Strategy" and version "1.0.0"

# Second request (identical name)
curl -X POST http://localhost:8000/api/strategies/api/create_strategy_with_ai/ \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_text": "Buy when RSI < 30, sell when RSI > 70",
    "name": "RSI Strategy",
    "use_gemini": true
  }'

# Expected: Success (201)
# Response includes: strategy with name "RSI Strategy v2" and version "2.0.0"
# NO UNIQUE constraint error!
```

#### Test 2: Improved Error Messages
```bash
# Strategy that fails validation (no trades)
curl -X POST http://localhost:8000/api/strategies/api/create_strategy_with_ai/ \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_text": "Buy when price goes up 0.1%",
    "use_gemini": true
  }'

# Expected: Error (400)
# Response now includes:
# - Clear error message
# - Specific failure reason
# - Helpful suggestions
# - Session ID for reference
```

---

### Backward Compatibility

✅ **No Breaking Changes**
- All existing endpoints remain unchanged
- Existing strategies unaffected
- Database schema unchanged
- Optional improvements to error responses

---

### Performance Impact

✅ **Minimal**
- Query for duplicate detection runs only if creating new strategy
- Uses indexed database fields (name, version)
- Additional loop through results is negligible for typical strategy counts
- No API latency change

---

### Documentation Updates

**New Document Created:**
- `/STRATEGY_CREATION_TROUBLESHOOTING.md`
  - Detailed explanation of both issues
  - Common patterns that work well
  - Testing instructions
  - Prevention checklist
  - API reference

---

### Deployment Notes

1. **No migrations needed** - only code changes
2. **No data cleanup required** - existing strategies unaffected
3. **Backward compatible** - safe to deploy immediately
4. **Testing recommended** - especially duplicate name scenarios

---

### Next Steps for Users

1. **Update code** from this commit
2. **Restart Django server**: `python manage.py runserver`
3. **Test duplicate strategy creation** to verify fix
4. **Review troubleshooting guide** for best practices
5. **Provide more specific strategy descriptions** to improve validation

---

### Metrics

- **Lines of code changed:** ~50
- **Methods modified:** 1
- **Database queries added:** 1 filter query per strategy creation
- **Error response fields added:** 3 (message, details, suggestions)

---

## Questions?

Refer to:
- `/STRATEGY_CREATION_TROUBLESHOOTING.md` - Detailed troubleshooting
- `/monolithic_agent/strategy_api/views.py` - Implementation details
- `/monolithic_agent/strategy_api/models.py` - Schema info
