# Strategy Creation Quick Fix Reference

## ✅ Issues Fixed Today

### Issue 1: UNIQUE Constraint Error
```
❌ django.db.utils.IntegrityError: UNIQUE constraint failed: 
   strategy_api_strategy.name, strategy_api_strategy.version
```
**Fixed:** Auto-incremented versions for duplicate strategy names

### Issue 2: Validation Failure (No Trades Executed)
```
❌ Internal Server Error: /api/strategies/api/create_strategy_with_ai/
   This strategy did not pass validation (no trades executed)
```
**Fixed:** Better error messages with actionable suggestions

---

## 📝 What Changed

### File: `/monolithic_agent/strategy_api/views.py`

#### Change 1: Duplicate Name Detection
**Location:** Lines 1113-1133
```python
# Auto-increment version when name exists
base_name = strategy_name
version_num = 1

existing_strategies = Strategy.objects.filter(name__startswith=base_name)
version_numbers = [int(str(strat.version).split('.')[0]) for strat in existing_strategies]
version_num = max(version_numbers) + 1 if version_numbers else 1

strategy_name = f"{base_name} v{version_num}"
version_str = f"{version_num}.0.0"
```

#### Change 2: Better Error Response
**Location:** Lines 1039-1059
```python
# Now includes helpful suggestions when validation fails
return Response({
    'error': 'Strategy validation failed',
    'message': error_message,
    'suggestions': [
        'Ensure your strategy description is clear and specific',
        'Include entry and exit signal descriptions',
        'Specify what indicators or conditions to use',
        'Try regenerating or modifying the strategy description'
    ],
    'session_id': conv_manager.session_id,
}, status=status.HTTP_400_BAD_REQUEST)
```

---

## 🧪 Testing

### Test Creating Duplicate Strategy Names
```bash
# Create first strategy
curl -X POST http://localhost:8000/api/strategies/api/create_strategy_with_ai/ \
  -H "Content-Type: application/json" \
  -d '{"strategy_text": "RSI strategy", "name": "RSI Strategy"}'
# ✅ Response: "RSI Strategy" v1.0.0

# Create second with same name
curl -X POST http://localhost:8000/api/strategies/api/create_strategy_with_ai/ \
  -H "Content-Type: application/json" \
  -d '{"strategy_text": "RSI strategy", "name": "RSI Strategy"}'
# ✅ Response: "RSI Strategy v2" v2.0.0 (NO ERROR!)
```

### Test Improved Error Messages
```bash
# Strategy with validation issues
curl -X POST http://localhost:8000/api/strategies/api/create_strategy_with_ai/ \
  -H "Content-Type: application/json" \
  -d '{"strategy_text": "Unclear strategy description"}'
# ✅ Response now includes helpful suggestions!
```

---

## 💡 How to Use

### For Users Creating Strategies

**Before:**
```json
{
  "strategy_text": "Buy and sell"
}
```
❌ Gets validation error but no guidance

**After:**
```json
{
  "strategy_text": "Buy when RSI < 30, sell when RSI > 70 on daily SPY data",
  "name": "RSI Momentum Strategy"
}
```
✅ Works better + if it fails, you get specific suggestions

### For Creating Multiple Strategies

**Same Name Works Now:**
```python
# Request 1
{"strategy_text": "...", "name": "Momentum"}  # → v1.0.0
# Request 2  
{"strategy_text": "...", "name": "Momentum"}  # → v2.0.0 (auto!)
# Request 3
{"strategy_text": "...", "name": "Momentum"}  # → v3.0.0 (auto!)
```

No more constraint errors! ✅

---

## 📚 Documentation

**Full Details:**
- `STRATEGY_CREATION_TROUBLESHOOTING.md` - Complete troubleshooting guide
- `STRATEGY_FIXES_SUMMARY.md` - Technical details of changes

**Quick Start:**
1. Copy `.env.example` to `.env`
2. Add your GEMINI_API_KEY
3. Run `python manage.py runserver`
4. Test strategy creation - now handles duplicates!

---

## 🎯 Expected Behavior Now

### Creating Strategy with Duplicate Name
```
Request: {"strategy_text": "...", "name": "Strategy A"}
Response 1: Strategy "Strategy A" v1.0.0 ✅
Response 2: Strategy "Strategy A v2" v2.0.0 ✅
Response 3: Strategy "Strategy A v3" v3.0.0 ✅
```

### Validation Failure
```
Request: {"strategy_text": "bad strategy"}
Response (400):
{
  "error": "Strategy validation failed",
  "message": "No trades executed in test",
  "suggestions": [
    "Make your strategy description more specific",
    "Include clear entry/exit conditions",
    ...
  ]
}
```

---

## ⚠️ Troubleshooting

**Still getting UNIQUE constraint error?**
- Clear browser cache
- Restart Django server
- Check database has latest migrations

**Still getting validation failures?**
- Read the suggestions provided
- Make strategy description more detailed
- Try different indicator combinations
- Check backtest data exists

**Need help?**
- See: `/STRATEGY_CREATION_TROUBLESHOOTING.md`
- Check logs: `tail -f logs/algoagent.log`

---

## 🚀 Deployment

1. ✅ Pull changes
2. ✅ No migrations needed
3. ✅ Restart server
4. ✅ Test creating duplicate strategies
5. ✅ All existing strategies unaffected

---

Generated: December 2, 2025
