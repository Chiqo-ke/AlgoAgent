# Strategy Validation Workflow - Quick Reference

**Status:** ✓ Fixed - Validation fields now properly mapped

---

## What Was Fixed

**Error:** `Invalid field name(s) for model StrategyValidation`  
**Cause:** Code using non-existent field names  
**Solution:** Updated validation to use correct model fields

### Field Mapping (Corrected)

| Old Field Name | New Field Name | Type | Purpose |
|---|---|---|---|
| `validation_errors` | `failed_checks` | JSONField | Store failed validation checks |
| `validation_warnings` | `warnings` | JSONField | Store warning messages |
| `validation_suggestions` | `recommendations` | JSONField | Store recommendations |
| `validated_at` | `completed_at` | DateTime | Completion timestamp |
| `validated_by` | (removed) | - | Not needed (system validation) |
| `results` | (split into fields) | - | Use `passed_checks`, `score`, etc. |

---

## Validation Workflow

### Step 1: Create Strategy
```
POST /api/strategies/api/create_strategy/
Input: Strategy code, name, description
Output: Strategy ID, status='pending'
```

### Step 2: Generate Code
```
POST /api/strategies/api/generate_executable_code/
Input: Strategy ID, framework, test_period
Output: Code path, trigger background validation
Note: Automatically triggers background validation
```

### Step 3: Validation Starts (Background)
```
Background Thread: validate_strategy_background()
├─ Parse strategy code
├─ Check syntax
├─ Check required components (class, init, next)
├─ Run backtest (1 year by default)
├─ Collect results
└─ Update StrategyValidation record
```

### Step 4: Check Results
```
GET /api/strategies/strategies/{id}/
Returns: status='valid' or 'invalid', validation details
```

---

## Validation Result Fields

### Database Fields Populated

```python
StrategyValidation.objects.create(
    strategy=strategy,                    # ForeignKey to Strategy
    validation_type='backtest',           # Type of validation
    status='passed',                      # passed, failed, etc.
    score=75.5,                           # 0-100 score
    
    # Results
    passed_checks=[
        'Syntax check passed',
        'Required components present',
        'No security issues'
    ],
    failed_checks=[],                     # Empty if passed
    warnings=[                            # Non-blocking issues
        'High slippage detected',
        'Low profit factor'
    ],
    recommendations=[                     # Suggestions for improvement
        'Optimize entry conditions',
        'Increase position sizing'
    ],
    
    # Metadata
    validation_config={
        'framework': 'backtesting.py',
        'test_period': '1 year',
        'symbol': 'AAPL'
    },
    execution_time=8.24,                  # Seconds
    completed_at=datetime.now(),
)
```

---

## Real Workflow Example

### 1. Create Strategy
```bash
curl -X POST http://127.0.0.1:8000/api/strategies/api/create_strategy/ \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "name": "test111",
    "strategy_code": "from backtesting import ...",
    "description": "Test strategy"
  }'
```

**Response:**
```json
{
  "id": 7,
  "name": "test111",
  "status": "pending",
  "created_at": "2025-12-02T16:05:52.152Z"
}
```

### 2. Generate Code (Triggers Validation)
```bash
curl -X POST http://127.0.0.1:8000/api/strategies/api/generate_executable_code/ \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "strategy_id": 7,
    "framework": "backtesting.py"
  }'
```

**Response:**
```json
{
  "status": "generated",
  "code_path": "C:\\...\\test111.py",
  "execution_time": 8.24
}
```

**Background (logs):**
```
2025-12-02 16:05:52,152 | [VALIDATION] Starting background validation for strategy 7
2025-12-02 16:05:52,163 | Validating Strategy: test111
2025-12-02 16:05:52,168 | [OK] Syntax check passed
2025-12-02 16:06:00,302 | Strategy generated successfully
```

### 3. Check Status
```bash
curl -X GET http://127.0.0.1:8000/api/strategies/strategies/7/ \
  -H "Authorization: Bearer TOKEN"
```

**Response:**
```json
{
  "id": 7,
  "name": "test111",
  "status": "valid",
  "validations": [
    {
      "id": 5,
      "validation_type": "backtest",
      "status": "passed",
      "score": 78.5,
      "passed_checks": [
        "Syntax check passed",
        "Required components present",
        "Backtest completed successfully"
      ],
      "failed_checks": [],
      "warnings": ["No trades executed in first 100 bars"],
      "recommendations": [
        "Consider adjusting entry conditions",
        "Increase indicator periods for stability"
      ],
      "execution_time": 8.24,
      "completed_at": "2025-12-02T16:06:00.302Z"
    }
  ]
}
```

---

## Validation Status Codes

| Status | Meaning | Action |
|--------|---------|--------|
| `pending` | Waiting to validate | Wait for generation |
| `running` | Currently validating | Check back soon |
| `passed` | Validation successful | Ready to use |
| `failed` | Validation failed | Review recommendations |
| `error` | Validation error | Check logs |

---

## Common Validation Results

### ✓ Passed Validation
```json
{
  "status": "passed",
  "score": 85,
  "passed_checks": [
    "Syntax valid",
    "Required components present",
    "Backtest completed",
    "Profitable trades executed"
  ],
  "failed_checks": [],
  "warnings": [],
  "recommendations": []
}
```

### ⚠ Passed with Warnings
```json
{
  "status": "passed",
  "score": 65,
  "passed_checks": ["Syntax valid", "Components present"],
  "failed_checks": [],
  "warnings": [
    "Low trade frequency",
    "High slippage impact"
  ],
  "recommendations": [
    "Optimize entry/exit timing",
    "Consider market microstructure"
  ]
}
```

### ✗ Failed Validation
```json
{
  "status": "failed",
  "score": 15,
  "passed_checks": ["Syntax valid"],
  "failed_checks": [
    "No trades executed",
    "Negative returns",
    "Insufficient hold period"
  ],
  "warnings": ["Very high slippage"],
  "recommendations": [
    "Review strategy logic",
    "Adjust indicators",
    "Test different parameters"
  ]
}
```

---

## Troubleshooting

### Issue: "Missing required components"
**Solution:** Strategy missing `Strategy` class, `init()`, or `next()` method
```python
# Correct structure:
class MyStrategy(Strategy):
    def init(self):
        pass
    
    def next(self):
        pass
```

### Issue: Validation never completes
**Solution:** Check background thread logs
```bash
# In server logs, look for:
# [VALIDATION] Triggered background validation thread
# If not present, thread may have crashed
```

### Issue: "Invalid field name(s)"
**Solution:** Already fixed! Fields now correctly mapped to model
- Use: `passed_checks`, `failed_checks`, `warnings`, `recommendations`

### Issue: Code path not saved
**Solution:** Ensure code directory exists and is writable
```bash
mkdir -p C:\Users\nyaga\Documents\AlgoAgent\monolithic_agent\Backtest\codes
```

---

## Quick Commands Reference

```bash
# Create strategy
POST /api/strategies/api/create_strategy/

# Generate code (triggers validation)
POST /api/strategies/api/generate_executable_code/

# Check validation status
GET /api/strategies/strategies/{id}/

# Get validation details
GET /api/strategy-validations/?strategy_id={id}

# List all validations
GET /api/strategy-validations/

# Validate code directly
POST /api/production/strategies/validate-code/
```

---

## Data Flow Diagram

```
1. Create Strategy
   ↓
2. Generate Code (POST)
   ↓
3. Save Code File
   ↓
4. Start Background Validation Thread
   ↓
5. Parse Code
   ├─ Check Syntax
   ├─ Check Components
   └─ Run Backtest
   ↓
6. Collect Results
   ├─ passed_checks
   ├─ failed_checks
   ├─ warnings
   └─ recommendations
   ↓
7. Update StrategyValidation Record
   ↓
8. Update Strategy Status
   ├─ status = 'valid' (if passed)
   └─ status = 'invalid' (if failed)
   ↓
9. Ready to Query via API
```

---

## Model Fields Reference

```python
class StrategyValidation(models.Model):
    # Relationships
    strategy = ForeignKey(Strategy)          # Links to strategy
    
    # Validation info
    validation_type = CharField(50)          # 'backtest', 'syntax', etc.
    status = CharField(20)                   # 'pending', 'running', 'passed', 'failed'
    score = DecimalField(0-100)              # Validation score
    
    # Results
    passed_checks = JSONField(list)          # List of passed checks
    failed_checks = JSONField(list)          # List of failed checks
    warnings = JSONField(list)               # Warning messages
    recommendations = JSONField(list)        # Improvement suggestions
    
    # Metadata
    validator_version = CharField(20)        # Version of validator used
    validation_config = JSONField(dict)      # Configuration used
    execution_time = DecimalField()          # Validation time in seconds
    
    # Timestamps
    created_at = DateTimeField(auto_now_add) # When validation started
    completed_at = DateTimeField()           # When validation completed
```

---

## Next Steps

1. ✓ Database fields now correctly mapped
2. ✓ Validation runs automatically after code generation
3. ✓ Results stored in StrategyValidation model
4. ✓ Status accessible via API

**Recommended Next:**
- Test strategy creation with proper code structure
- Monitor validation background thread
- Review validation results in database
- Iterate on strategy improvements based on recommendations

---

**Last Updated:** December 2, 2025  
**Status:** ✓ Field Mapping Fixed
**Next:** Test with proper strategy code
