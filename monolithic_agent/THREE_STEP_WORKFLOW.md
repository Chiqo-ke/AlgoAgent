# Three-Step Code Generation Workflow ✅

## Overview

The system now implements a three-step workflow for code generation:

1. **Code Generation** - AI generates Python strategy code
2. **Execution in Virtual Environment** - Bot runs in `.venv` Python environment
3. **Auto-Debugging** - AI debugs errors and validates trades were made

---

## Step 1: Code Generation

When user clicks "Generate Code", the system:

- Uses **GitHub Copilot** (GPT-4o) or **Gemini** as fallback
- Generates Python trading bot based on canonical JSON
- Saves to `Backtest/codes/<strategy_name>.py`
- Returns generated code to frontend

**Endpoint**: `/api/strategies/api/generate_strategy_unified/`

**Parameters**:
- `canonical_json` - Strategy specification
- `auto_execute` - Enable automatic execution (Step 2)
- `auto_fix` - Enable debugging (Step 3)
- `max_fix_attempts` - Maximum debugging iterations (default: 3)

---

## Step 2: Execution in Virtual Environment

The system **automatically executes** the generated code if `auto_execute=true`.

### Virtual Environment Enforcement

✅ **Default venv**: `C:\Users\nyaga\Documents\.venv`

The `BotExecutor` class now:
- Uses **virtual environment Python** by default
- Locates Python at `.venv/Scripts/python.exe`
- Falls back to system Python if venv not found
- Logs which Python is being used

**Code Changes** (`Backtest/bot_executor.py`):
```python
def __init__(self, venv_path=None):
    # Default to Documents/.venv
    self.venv_path = Path(r"C:\Users\nyaga\Documents\.venv")
    self.python_executable = str(self.venv_path / "Scripts" / "python.exe")
    
    # Execute using venv Python
    cmd = [self.python_executable, str(strategy_file)]
```

### Execution Output Capture

The executor:
- Runs strategy as subprocess
- Captures **stdout** and **stderr**
- Parses metrics (return %, trades, win rate, etc.)
- Returns `BotExecutionResult` with all details

---

## Step 3: Auto-Debugging

The system performs **intelligent debugging** based on execution results.

### Trade Validation ⚠️ CRITICAL

**Requirement**: Bot **MUST** make at least one trade to pass debugging test.

If bot executes but makes **0 trades**:
- Execution marked as **FAILED**
- Error: `"Strategy executed but made NO TRADES (0 trades). Bot must place at least one trade to pass."`
- Auto-fix triggered (if enabled)

**Code Changes** (`Backtest/bot_executor.py`):
```python
# Validate that at least one trade was made
if result['trades'] is not None and result['trades'] == 0:
    result['success'] = False
    result['error'] = "Strategy executed but made NO TRADES (0 trades). Bot must place at least one trade to pass."
    logger.warning("⚠️ TRADE VALIDATION FAILED: Bot made 0 trades")
```

### Auto-Fix Process

When execution fails (`auto_fix=true`):

1. **Detect Error Type**:
   - Syntax errors
   - Import errors
   - Logic errors
   - **No trades made** ← NEW

2. **AI Debugging**:
   - Copilot/Gemini analyzes code and error
   - Identifies why trades weren't placed
   - Generates fixed code

3. **Re-Execution**:
   - Applies fix
   - Re-runs strategy
   - Validates trades made

4. **Iteration**:
   - Repeats up to `max_fix_attempts` times
   - Tracks fix history
   - Records in learning system

**Code Changes** (`strategy_api/views.py`):
```python
# Detect "no trades" issue
is_no_trades_error = (
    execution_result.trades == 0
) or (
    "NO TRADES" in execution_result.error.upper()
)

if auto_fix:
    # Pass error context to AI
    success, final_path, fix_attempts = generator.fix_bot_errors_iteratively(
        strategy_file=str(python_file),
        max_iterations=max_fix_attempts,
        learning_system=learning_system,
        error_context={
            'is_no_trades': is_no_trades_error,
            'trades_count': execution_result.trades,
            'execution_error': execution_result.error
        } if is_no_trades_error else None
    )
```

---

## Complete Workflow Example

### Frontend Request
```javascript
POST /api/strategies/api/generate_strategy_unified/

{
  "canonical_json": "{...}",
  "auto_execute": true,      // Enable Step 2
  "auto_fix": true,           // Enable Step 3
  "max_fix_attempts": 3       // Max debugging iterations
}
```

### Backend Processing

**Step 1: Generation**
```
✅ Code generated (1,586 chars via Copilot)
✅ Saved to: Backtest/codes/rsialgo.py
```

**Step 2: Execution**
```
ℹ️  Using virtual environment: C:\Users\nyaga\Documents\.venv
ℹ️  Python executable: C:\Users\nyaga\Documents\.venv\Scripts\python.exe
⚙️  Executing strategy...
✅ Execution completed
❌ Trades made: 0
⚠️  TRADE VALIDATION FAILED: Bot made 0 trades
```

**Step 3: Auto-Debugging**
```
⚠️  NO TRADES ISSUE - AI will debug why strategy didn't place trades
   Trades count: 0
   Error: Strategy executed but made NO TRADES

🔧 ATTEMPT 1/3: Analyzing code...
   AI identified issue: Entry conditions too restrictive
   Generating fix...
   ✅ Fix applied

⚙️  Re-executing after fix...
✅ Execution completed
✅ Trades made: 15
✅ Return: +8.3%
✅ SUCCESS after 1 fix attempt
```

---

## API Response Structure

```json
{
  "status": "success",
  "code_length": 1586,
  "execution_result": {
    "success": true,
    "trades": 15,
    "return_pct": 8.3,
    "win_rate": 0.67,
    "duration_seconds": 23.4
  },
  "auto_fix_summary": {
    "attempts": 1,
    "success": true,
    "fix_history": [
      {
        "attempt": 1,
        "error_type": "no_trades",
        "success": true,
        "description": "Relaxed entry conditions to allow trades"
      }
    ]
  },
  "validation_status": "passed"
}
```

---

## Configuration

### Enable Three-Step Workflow

**Frontend (Dashboard.tsx)**:
```typescript
const response = await fetch('/api/strategies/api/generate_strategy_unified/', {
  method: 'POST',
  body: JSON.stringify({
    canonical_json: strategyJSON,
    auto_execute: true,     // Enable execution
    auto_fix: true,         // Enable debugging
    max_fix_attempts: 3     // Max iterations
  })
});
```

**PowerShell Test Script**:
```powershell
$generatePayload = @{
    canonical_json = $canonicalJson
    auto_execute = $true
    auto_fix = $true
    max_fix_attempts = 3
} | ConvertTo-Json -Depth 10
```

### Virtual Environment Setup

Ensure `.venv` exists at `C:\Users\nyaga\Documents\.venv`:

```powershell
cd C:\Users\nyaga\Documents
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## Key Benefits

1. **Automatic Execution** - No manual bot running needed
2. **Virtual Environment Isolation** - Dependencies managed properly
3. **Trade Validation** - Ensures bots actually trade
4. **Intelligent Debugging** - AI fixes errors automatically
5. **Learning System** - Records errors and fixes for improvement
6. **Full Observability** - Complete logs and metrics captured

---

## Files Modified

### Core Execution
- `Backtest/bot_executor.py` - Virtual environment enforcement + trade validation
- `strategy_api/views.py` - Auto-fix trigger for "no trades" scenarios

### AI Generators
- `Backtest/copilot_strategy_generator.py` - Added error_context parameter
- `Backtest/gemini_strategy_generator.py` - Added error_context parameter

### Error Fixing
- `Backtest/bot_error_fixer.py` - Existing (supports context already)

---

## Testing

### Test with PowerShell
```powershell
cd C:\Users\nyaga\Documents
.\test_user_journey.ps1
```

Expected output:
```
========================================
STEP 1: LOGIN
========================================
✅ Login successful

========================================
STEP 2: VALIDATE STRATEGY
========================================
✅ Validation successful (Copilot)

========================================
STEP 3: GENERATE & EXECUTE
========================================
✅ Code generated (1,586 chars)
⚙️  Executing in .venv...
⚠️  Bot made 0 trades - triggering auto-fix
🔧 Fix attempt 1/3...
✅ SUCCESS - Bot now makes 15 trades
```

---

## Future Enhancements

- [ ] Add minimum trade count requirement (e.g., >= 5 trades)
- [ ] Validate win rate is reasonable (e.g., > 20%)
- [ ] Check for profit factor threshold
- [ ] Add risk management validation (SL/TP present)
- [ ] Implement performance benchmarking
- [ ] Add unit test generation for strategies

---

## Summary

The three-step workflow ensures:

1. ✅ **Code is generated** by AI (Copilot/Gemini)
2. ✅ **Code runs in proper environment** (`.venv` Python)
3. ✅ **Code makes trades** (validated and auto-fixed if needed)

This creates a **complete, automated, self-healing** code generation pipeline.
