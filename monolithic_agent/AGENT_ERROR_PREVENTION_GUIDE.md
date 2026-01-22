# Preventing API Errors in Agent-Generated Strategies

## Overview

This guide shows how to configure your Copilot agents to avoid common API errors when generating trading strategies. Based on lessons learned from E2E testing, we've identified patterns and implemented preventive measures.

---

## Problem Analysis

### Common Errors Encountered

1. **Import Errors** - Wrong module names (simbroker vs sim_broker)
2. **API Signature Mismatches** - Using old API instead of BacktestConfig
3. **Signal Schema Violations** - Missing or incorrect parameters
4. **Method Name Errors** - Calling non-existent methods
5. **Data Format Issues** - Incorrect market data structure

### Root Causes

- **Incomplete prompts** - Copilot didn't have full API specifications
- **Ambiguous examples** - Similar but incorrect patterns in context
- **Lack of validation** - No pre-execution checks
- **Outdated documentation** - API evolved but prompts didn't

---

## Solutions Implemented

### 1. Comprehensive API Documentation

**File:** `Backtest/SIMBROKER_API_REFERENCE.md`

Complete reference including:
- ✅ Exact import patterns
- ✅ Configuration setup examples
- ✅ Complete signal schema with all required fields
- ✅ Valid enum values (OrderSide, OrderAction)
- ✅ Broker method signatures
- ✅ Working examples
- ✅ Common errors and solutions

**Usage:**
```bash
# Reference for manual development
cat Backtest/SIMBROKER_API_REFERENCE.md

# Include in Copilot prompts
# (Already integrated in copilot_strategy_generator.py)
```

### 2. Enhanced Copilot Prompts

**File:** `Backtest/copilot_strategy_generator.py`

Updated fallback prompt includes:
- ✅ Critical import patterns with examples
- ✅ Broker initialization using BacktestConfig
- ✅ Complete signal schema with all fields
- ✅ Valid enum values explicitly listed
- ✅ Common mistakes to avoid
- ✅ Required strategy structure

**Key improvements:**
```python
# Before: Minimal guidance
base_prompt = "Generate strategy using SimBroker..."

# After: Comprehensive spec
base_prompt = """
CRITICAL: Signal Schema
signal = {
    'signal_id': f'sig_{counter:04d}',  # Required
    'timestamp': timestamp.isoformat(),
    'symbol': 'AAPL',
    'side': 'BUY',          # 'BUY' or 'SELL' (NOT 'LONG')
    'action': 'ENTRY',       # 'ENTRY' or 'EXIT' (NOT 'BUY')
    'order_type': 'MARKET',
    'size': 100,            # NOT 'quantity'
    'meta': {...}           # NOT 'reason' directly
}
"""
```

### 3. Pre-Execution Validation

**File:** `Backtest/pre_execution_validator.py`

Static code analysis before execution:
- ✅ Validates imports against required patterns
- ✅ Checks for forbidden import styles
- ✅ Validates signal schema compliance
- ✅ Detects incorrect method names
- ✅ Verifies market data format
- ✅ Provides actionable error messages

**Usage:**
```python
from Backtest.pre_execution_validator import validate_strategy

# Validate before execution
report = validate_strategy('path/to/strategy.py')
if not report.is_valid:
    for error in report.errors:
        print(f"ERROR: {error}")
    exit(1)

# Or validate code string
from Backtest.pre_execution_validator import validate_generated_code
is_valid, errors = validate_generated_code(code_string)
```

### 4. Integration in E2E Test

**File:** `strategy_api/management/commands/test_copilot_e2e.py`

Already integrated validation:
```python
# Existing validation method (lines 192-216)
def _validate_imports(self, code: str) -> Tuple[bool, List[str]]:
    """Validates that generated code uses correct import patterns"""
    
    errors = []
    
    # Check for required imports
    required_imports = [
        r'from\s+Backtest\.sim_broker\s+import',
        r'from\s+Backtest\.config\s+import'
    ]
    
    # Check for forbidden patterns
    forbidden_patterns = [
        (r'from\s+simbroker\s+import', 'simbroker'),
        (r'import\s+simbroker\b', 'simbroker'),
        # ...
    ]
    
    # Returns validation results
    return len(errors) == 0, errors
```

---

## Recommended Configuration

### For New Strategies

**Step 1: Update Copilot Prompt Template**

Create/update `Backtest/prompts/strategy_generation_prompt.txt`:

```markdown
# Trading Strategy Generation - SimBroker API v1.0

CRITICAL REQUIREMENTS:
1. Import Pattern (EXACT):
   from Backtest.sim_broker import SimBroker
   from Backtest.config import BacktestConfig
   
2. Initialization (REQUIRED):
   config = BacktestConfig(symbol="AAPL", ...)
   broker = SimBroker(config)
   
3. Signal Schema (ALL FIELDS REQUIRED):
   {
       'signal_id': str,      # e.g., 'sig_0001'
       'timestamp': str,      # ISO format
       'symbol': str,         # e.g., 'AAPL'
       'side': str,           # 'BUY' or 'SELL'
       'action': str,         # 'ENTRY' or 'EXIT'
       'order_type': str,     # 'MARKET' or 'LIMIT'
       'size': int,           # Positive integer
       'meta': dict           # Optional metadata
   }

FORBIDDEN VALUES:
- side: NOT 'LONG', 'SHORT', 'OPEN', 'CLOSE'
- action: NOT 'BUY', 'SELL', 'OPEN', 'CLOSE'
- field names: NOT 'quantity', NOT 'reason' (use 'size', 'meta')

METHODS:
- get_statistics() ✅ (NOT get_metrics() ❌)
- step_to(timestamp, market_data)
- submit_signal(signal_dict)

For full API reference, see: Backtest/SIMBROKER_API_REFERENCE.md
```

**Step 2: Enable Pre-Execution Validation**

In your strategy generation code:

```python
from Backtest.copilot_strategy_generator import CopilotStrategyGenerator
from Backtest.pre_execution_validator import validate_generated_code

# Generate strategy
generator = CopilotStrategyGenerator()
code = generator.generate_strategy(description)

# Validate BEFORE saving/executing
is_valid, errors = validate_generated_code(code)
if not is_valid:
    print("❌ Generated code failed validation:")
    for error in errors:
        print(f"  - {error}")
    
    # Option 1: Fail fast
    raise ValueError("Invalid strategy generated")
    
    # Option 2: Auto-fix (implement if needed)
    # code = auto_fix_common_errors(code, errors)
    # is_valid, errors = validate_generated_code(code)

# Only proceed if valid
if is_valid:
    save_strategy(code)
    execute_strategy(code)
```

**Step 3: Add Validation to Existing Workflows**

Update any script that generates/executes strategies:

```python
# Before execution
from Backtest.pre_execution_validator import validate_strategy

report = validate_strategy(file_path)
if not report.is_valid:
    print(report)  # Shows formatted error report
    return False

# Proceed with execution
result = execute_strategy(file_path)
```

### For Frontend Integration

**API Endpoint:** Add validation endpoint

```python
# In strategy_api/views.py
from Backtest.pre_execution_validator import validate_generated_code
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['POST'])
def validate_strategy_code(request):
    """Validate strategy code before execution"""
    code = request.data.get('code')
    
    is_valid, errors = validate_generated_code(code)
    
    return Response({
        'is_valid': is_valid,
        'errors': errors,
        'can_execute': is_valid
    })
```

**Frontend:** Show validation results

```typescript
// Before executing strategy
const validateStrategy = async (code: string) => {
  const response = await fetch('/api/validate-strategy', {
    method: 'POST',
    body: JSON.stringify({ code }),
    headers: { 'Content-Type': 'application/json' }
  });
  
  const { is_valid, errors } = await response.json();
  
  if (!is_valid) {
    showErrors(errors);  // Display to user
    return false;
  }
  
  return true;
};

// In execution handler
const handleExecute = async () => {
  const isValid = await validateStrategy(strategyCode);
  if (!isValid) {
    return;  // Don't execute invalid code
  }
  
  // Proceed with execution
  executeStrategy(strategyCode);
};
```

---

## Maintenance Guidelines

### When Adding New API Features

1. **Update API Reference** (`SIMBROKER_API_REFERENCE.md`)
   - Add new methods/parameters
   - Include working examples
   - Document breaking changes

2. **Update Copilot Prompts** (`copilot_strategy_generator.py`)
   - Add new patterns to prompts
   - Update examples
   - Add new forbidden patterns if applicable

3. **Update Validator** (`pre_execution_validator.py`)
   - Add validation rules for new features
   - Update required/forbidden patterns
   - Add test cases

4. **Update E2E Test** (`test_copilot_e2e.py`)
   - Test new features in E2E flow
   - Add validation for new patterns

### When Deprecating Features

1. **Mark as forbidden** in validator
2. **Add to "Common Mistakes"** in API reference
3. **Update prompts** to explicitly avoid deprecated patterns
4. **Provide migration examples** in docs

### Quality Checks

Run these regularly:

```bash
# Test strategy generation
python manage.py test_copilot_e2e

# Validate existing strategies
find Backtest/codes -name "*.py" -exec python Backtest/pre_execution_validator.py {} \;

# Check API reference is up to date
diff Backtest/sim_broker.py <(extract_api_from_reference.py)
```

---

## Quick Reference Card

**Print this or keep handy when developing:**

```
✅ CORRECT PATTERNS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Imports:
  from Backtest.sim_broker import SimBroker
  from Backtest.config import BacktestConfig

Initialization:
  config = BacktestConfig(symbol="AAPL", ...)
  broker = SimBroker(config)

Signal:
  signal = {
    'signal_id': 'sig_0001',
    'timestamp': dt.isoformat(),
    'symbol': 'AAPL',
    'side': 'BUY',           # or 'SELL'
    'action': 'ENTRY',        # or 'EXIT'
    'order_type': 'MARKET',
    'size': 100,
    'meta': {'reason': '...'}
  }

Market Data:
  data = {'AAPL': {'open': 150, 'close': 151, ...}}
  broker.step_to(timestamp, data)

Statistics:
  stats = broker.get_statistics()

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ FORBIDDEN PATTERNS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ from simbroker import ...
❌ from sim_broker import ...  (without Backtest)
❌ SimBroker(symbol="AAPL", ...)
❌ 'side': 'LONG'  (use 'BUY')
❌ 'action': 'BUY'  (use 'ENTRY')
❌ 'quantity': 100  (use 'size')
❌ 'reason': '...'  (use 'meta': {'reason': '...'})
❌ broker.get_metrics()  (use get_statistics())
❌ data = {'open': 150, ...}  (missing symbol level)
```

---

## Summary

To avoid API errors in agent-generated strategies:

1. ✅ **Use comprehensive prompts** with exact API specifications
2. ✅ **Validate before execution** using pre_execution_validator
3. ✅ **Reference API docs** (SIMBROKER_API_REFERENCE.md)
4. ✅ **Keep prompts updated** when API changes
5. ✅ **Test end-to-end** regularly with test_copilot_e2e
6. ✅ **Show validation errors** to users before execution

**Result:** Dramatically reduce runtime errors and improve user experience.
