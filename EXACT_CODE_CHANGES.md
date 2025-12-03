# Exact Code Changes - Strategy Creation Fixes

## File: `/monolithic_agent/strategy_api/views.py`

### Change 1: Improved Error Handling (Lines 1039-1059)

#### BEFORE:
```python
# Check if validation was successful
if ai_result.get('status') != 'success':
    # Store failure in conversation
    conv_manager.add_ai_message(
        f"Strategy validation failed: {ai_result.get('message', 'Unknown error')}",
        metadata={
            'action': 'creation_failed',
            'status': ai_result.get('status'),
            'result': ai_result
        }
    )
    return Response({
        'error': 'Strategy validation failed',
        'validation_result': ai_result,
        'session_id': conv_manager.session_id
    }, status=status.HTTP_400_BAD_REQUEST)
```

#### AFTER:
```python
# Check if validation was successful
if ai_result.get('status') != 'success':
    # Store failure in conversation
    error_message = ai_result.get('message', 'Unknown error')
    conv_manager.add_ai_message(
        f"Strategy validation failed: {error_message}",
        metadata={
            'action': 'creation_failed',
            'status': ai_result.get('status'),
            'result': ai_result
        }
    )
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

**What Changed:**
- ✅ Added `message` field with error message
- ✅ Added `details` field with additional info
- ✅ Added `suggestions` list for user guidance

---

### Change 2: Duplicate Name/Version Handling (Lines 1113-1133)

#### BEFORE:
```python
# Generate strategy name if not provided
strategy_name = data.get('name')
if not strategy_name:
    strategy_name = canonical_data.get('title', 'AI Generated Strategy')

# Get or create template
template = None
auto_created_template = False
template_id = data.get('template_id')

if template_id:
    try:
        template = StrategyTemplate.objects.get(id=template_id)
    except StrategyTemplate.DoesNotExist:
        return Response({
            'error': 'Template not found'
        }, status=status.HTTP_404_NOT_FOUND)

# Extract metadata from AI result
classification = ai_result.get('classification_detail', {})
strategy_type = classification.get('type', '')
risk_tier = (classification.get('risk_tier', '') or '')[:20]
timeframe = (canonical_data.get('metadata', {}).get('timeframe', '') or '')[:20]

# Parse optional numeric fields
expected_return = None
max_drawdown = None
try:
    if 'expected_return' in canonical_data.get('metadata', {}):
        expected_return = float(canonical_data['metadata']['expected_return'])
except (ValueError, TypeError):
    pass

try:
    if 'max_drawdown' in canonical_data.get('metadata', {}):
        max_drawdown = float(canonical_data['metadata']['max_drawdown'])
except (ValueError, TypeError):
    pass

# Create the Strategy record
strategy = Strategy.objects.create(
    name=strategy_name,
    description=data.get('description', canonical_data.get('description', '')),
    template=template,
    strategy_code=canonical_json_str,  # Store canonical JSON as code
    parameters=canonical_data.get('metadata', {}),
    tags=data.get('tags', classification.get('primary_instruments', [])),
    timeframe=timeframe,
    risk_level=risk_tier,
    expected_return=expected_return,
    max_drawdown=max_drawdown,
    created_by=request.user if request.user.is_authenticated else None
)
```

#### AFTER:
```python
# Generate strategy name if not provided
strategy_name = data.get('name')
if not strategy_name:
    strategy_name = canonical_data.get('title', 'AI Generated Strategy')

# Get or create template
template = None
auto_created_template = False
template_id = data.get('template_id')

if template_id:
    try:
        template = StrategyTemplate.objects.get(id=template_id)
    except StrategyTemplate.DoesNotExist:
        return Response({
            'error': 'Template not found'
        }, status=status.HTTP_404_NOT_FOUND)

# Extract metadata from AI result
classification = ai_result.get('classification_detail', {})
strategy_type = classification.get('type', '')
risk_tier = (classification.get('risk_tier', '') or '')[:20]
timeframe = (canonical_data.get('metadata', {}).get('timeframe', '') or '')[:20]

# Parse optional numeric fields
expected_return = None
max_drawdown = None
try:
    if 'expected_return' in canonical_data.get('metadata', {}):
        expected_return = float(canonical_data['metadata']['expected_return'])
except (ValueError, TypeError):
    pass

try:
    if 'max_drawdown' in canonical_data.get('metadata', {}):
        max_drawdown = float(canonical_data['metadata']['max_drawdown'])
except (ValueError, TypeError):
    pass

# Handle duplicate name/version constraint
# Check if strategy with this name already exists and find next available version
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

# Create the Strategy record
strategy = Strategy.objects.create(
    name=strategy_name,
    version=version_str,
    description=data.get('description', canonical_data.get('description', '')),
    template=template,
    strategy_code=canonical_json_str,  # Store canonical JSON as code
    parameters=canonical_data.get('metadata', {}),
    tags=data.get('tags', classification.get('primary_instruments', [])),
    timeframe=timeframe,
    risk_level=risk_tier,
    expected_return=expected_return,
    max_drawdown=max_drawdown,
    created_by=request.user if request.user.is_authenticated else None
)
```

**What Changed:**
- ✅ Added version duplicate detection (lines 1113-1119)
- ✅ Added version number extraction logic (lines 1120-1129)
- ✅ Auto-append version suffix to name (line 1130)
- ✅ Generate semantic version string (line 1132)
- ✅ Pass `version` parameter to `create()` (line 1138)

---

## Summary of Changes

| Item | Before | After |
|------|--------|-------|
| Error Response Fields | 2 | 5 |
| Duplicate Name Handling | ❌ None | ✅ Auto-increment |
| Error Suggestions | ❌ None | ✅ 4 suggestions |
| Version Handling | ❌ Not set | ✅ Auto-computed |
| User Guidance | ❌ Generic | ✅ Specific |

---

## Code Diff View

### What Gets Added
```diff
+ # Handle duplicate name/version constraint
+ base_name = strategy_name
+ version_num = 1
+ existing = Strategy.objects.filter(name=strategy_name, version='1.0.0').first()
+ if existing:
+     existing_strategies = Strategy.objects.filter(name__startswith=base_name)
+     version_numbers = []
+     for strat in existing_strategies:
+         try:
+             parts = str(strat.version).split('.')
+             version_numbers.append(int(parts[0]))
+         except (ValueError, IndexError):
+             pass
+     version_num = max(version_numbers) + 1 if version_numbers else 1
+     strategy_name = f"{base_name} v{version_num}"
+ version_str = f"{version_num}.0.0"
```

### What Gets Enhanced
```diff
  return Response({
      'error': 'Strategy validation failed',
+     'message': error_message,
+     'details': ai_result.get('details', ''),
      'validation_result': ai_result,
      'session_id': conv_manager.session_id,
+     'suggestions': [
+         'Ensure your strategy description is clear and specific',
+         'Include entry and exit signal descriptions',
+         'Specify what indicators or conditions to use',
+         'Try regenerating or modifying the strategy description'
+     ]
  }, status=status.HTTP_400_BAD_REQUEST)
```

---

## Testing the Changes

### Verify Duplicate Name Handling
```python
# In Django shell:
from strategy_api.models import Strategy

# Create first
s1 = Strategy.objects.create(name="Test", version="1.0.0")
# s1.name = "Test", s1.version = "1.0.0" ✅

# Create second (via API, should auto-increment)
# s2.name = "Test v2", s2.version = "2.0.0" ✅

# Create third
# s3.name = "Test v3", s3.version = "3.0.0" ✅

# No constraint errors! ✅
```

### Verify Error Messages
```bash
curl -X POST http://localhost:8000/api/strategies/api/create_strategy_with_ai/ \
  -H "Content-Type: application/json" \
  -d '{"strategy_text": "bad"}'

# Response (400):
# {
#   "error": "Strategy validation failed",
#   "message": "No trades executed in 1-year test",
#   "suggestions": [...],
#   ...
# }
```

---

## Migration/Deployment

**No migrations required!**
- Only Python code changes
- No database schema changes
- Safe to deploy immediately
- Backward compatible

```bash
# Deploy steps:
1. git pull
2. (no migrations needed)
3. python manage.py runserver  # Restart
4. Test with duplicate names
5. Verify error messages improved
```

---

## Files Modified

- ✅ `/monolithic_agent/strategy_api/views.py` - 2 changes, ~50 lines
- ✅ No other files modified
- ✅ No migrations needed
- ✅ No database changes required

---

## Verification Checklist

- [ ] Code changes applied to `views.py`
- [ ] Django server restarted
- [ ] Can create strategy (no errors)
- [ ] Can create duplicate strategy name (no constraint error)
- [ ] Error message includes suggestions
- [ ] Multiple duplicate names auto-increment correctly
- [ ] Existing strategies unaffected

---

Generated: December 2, 2025
