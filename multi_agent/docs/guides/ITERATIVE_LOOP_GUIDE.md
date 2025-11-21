# Iterative Agent Loop - Quick Start Guide

## Overview

The **Iterative Loop** automatically improves your trading strategy until all tests pass. It continuously cycles through Coder → Tester → Debugger → Fixer until success or max iterations reached.

## How It Works

```
┌─────────────────────────────────────────┐
│  1. Coder generates strategy code       │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│  2. Tester validates with pytest        │
│     - Syntax check                      │
│     - Import validation                 │
│     - Logic tests                       │
│     - Contract compliance               │
└──────────────┬──────────────────────────┘
               ↓
         ┌─────────┐
         │ Passed? │
         └────┬────┘
              │
      ┌───────┴──────┐
      │              │
     YES            NO
      │              │
      ↓              ↓
   SUCCESS   ┌───────────────────────┐
             │ 3. Analyze failures   │
             │    - Classify error   │
             │    - Create fix task  │
             └───────┬───────────────┘
                     ↓
             ┌───────────────────────┐
             │ 4. Route to agent     │
             │    - Syntax → Coder   │
             │    - Imports → Coder  │
             │    - Logic → Debugger │
             │    - Contract → Arch  │
             └───────┬───────────────┘
                     ↓
             ┌───────────────────────┐
             │ 5. Agent fixes issue  │
             └───────┬───────────────┘
                     ↓
             Back to step 1 (loop)
```

## Usage

### Interactive Mode

```powershell
cd C:\Users\nyaga\Documents\AlgoAgent\multi_agent
python cli.py

>>> iterate wf_abc123
# or with custom max iterations
>>> iterate wf_abc123 10
```

### Command-Line Mode

```powershell
# Default: 5 iterations
python cli.py --iterate wf_abc123

# Custom max iterations
python cli.py --iterate wf_abc123 --max-iterations 10
```

### One-Shot Mode (Submit + Iterate)

```powershell
# Submit strategy and auto-improve until it works
python cli.py --request "Create RSI strategy with buy<30 sell>70" --run

# Then iterate
python cli.py --iterate wf_<returned_id>
```

## What Happens Each Iteration

### Iteration 1
```
🔄 ITERATION 1/5

📝 Step 1: Executing workflow tasks...
   [CoderAgent] Generating strategy code...
   ✓ Code generated: ai_strategy_rsi.py

🧪 Step 2: Testing generated strategy...
   Testing: ai_strategy_rsi
   Strategy: ai_strategy_rsi.py
   Test: test_ai_strategy_rsi.py
   ❌ FAILED (1.23s)
      SyntaxError: invalid decimal literal

📊 Test Results:
   Total: 1
   Passed: 0 ✅
   Failed: 1 ❌

🔧 Step 3: Analyzing failures and generating fixes...
   Error Type: syntax_error
   + fix_syntax_ai_strategy_rsi_iter1: Fix syntax error in ai_strategy_rsi
   ✅ Created 1 fix task(s)
   ✅ Updated TodoList with fix tasks
   🔄 Retrying in next iteration...
```

### Iteration 2
```
🔄 ITERATION 2/5

📝 Step 1: Executing workflow tasks...
   [CoderAgent] Fixing syntax error...
   ✓ Fixed: ai_strategy_rsi.py

🧪 Step 2: Testing generated strategy...
   Testing: ai_strategy_rsi
   ✅ PASSED (2.45s)

📊 Test Results:
   Total: 1
   Passed: 1 ✅
   Failed: 0 ❌

======================================================================
✅ SUCCESS! All tests passed in iteration 2
======================================================================
```

## Error Classification & Routing

The system automatically classifies errors and routes to the appropriate agent:

| Error Type | Detection | Routed To | Priority |
|------------|-----------|-----------|----------|
| **Syntax Error** | `SyntaxError`, `invalid syntax` | Coder | High (1) |
| **Import Error** | `ImportError`, `ModuleNotFoundError` | Coder | High (1) |
| **Logic Error** | Test failures, `AssertionError` | Debugger | Medium (2) |
| **Contract Mismatch** | Interface violations | Architect | High (1) |
| **Unknown Error** | Other exceptions | Debugger | Low (3) |

## Fix Task Structure

Each iteration creates fix tasks with detailed context:

```json
{
  "id": "fix_syntax_ai_strategy_rsi_iter1",
  "title": "Fix syntax error in ai_strategy_rsi",
  "description": "Syntax error detected: invalid decimal literal at line 7",
  "agent_role": "coder",
  "priority": 1,
  "dependencies": [],
  "metadata": {
    "fix_type": "syntax",
    "target_file": "Backtest/codes/ai_strategy_rsi.py",
    "error_details": "SyntaxError: invalid decimal literal",
    "iteration": 1,
    "previous_attempt": "Generated: 2023-10-27T12:00:00Z"
  }
}
```

## Configuration

### Max Iterations

Default: **5 iterations**

```powershell
# Use more iterations for complex strategies
python cli.py --iterate wf_abc123 --max-iterations 10

# Or in Python
from iterative_loop import IterativeLoop

loop = IterativeLoop(
    cli=cli,
    max_iterations=10,
    auto_fix=True
)
```

### Auto-Fix

Default: **Enabled**

```python
# Disable auto-fix (manual intervention required)
loop = IterativeLoop(
    cli=cli,
    max_iterations=5,
    auto_fix=False  # Will stop after first failure
)
```

## Output Files

### Iteration Report

Saved as: `workflows/iteration_report_<workflow_id>_<timestamp>.json`

```json
{
  "workflow_id": "wf_abc123",
  "success": true,
  "total_iterations": 2,
  "max_iterations": 5,
  "completed_at": "2025-11-20T16:45:00",
  "iteration_history": [
    {
      "iteration": 1,
      "status": "completed",
      "timestamp": "2025-11-20T16:43:00",
      "data": {
        "execution": {...},
        "tests": {
          "summary": {"total": 1, "passed": 0, "failed": 1},
          "results": [...]
        },
        "duration": 15.23
      }
    },
    {
      "iteration": 2,
      "status": "completed",
      "timestamp": "2025-11-20T16:45:00",
      "data": {
        "execution": {...},
        "tests": {
          "summary": {"total": 1, "passed": 1, "failed": 0},
          "results": [...]
        },
        "duration": 12.45
      }
    }
  ]
}
```

### Updated TodoList

After each iteration, the TodoList is updated with fix tasks:

`workflows/<workflow_id>_todolist.json`

## Success Criteria

The loop stops when:

✅ **All tests pass** - No failures in test results  
✅ **Strategy validated** - Syntax, imports, logic all correct  
✅ **Artifacts generated** - trades.csv, test reports created  

OR

❌ **Max iterations reached** - Stopped after N attempts  
❌ **Execution failed** - Workflow cannot proceed  
❌ **No fixes generated** - Cannot classify or fix errors  

## Example Session

```powershell
(.venv) PS> python cli.py

>>> submit Create RSI momentum strategy with buy signal when RSI<30 and price above 200 SMA
✅ Submitted: wf_def789

>>> iterate wf_def789

======================================================================
   ITERATIVE LOOP: wf_def789
   Max Iterations: 5
   Auto-Fix: ENABLED
======================================================================

──────────────────────────────────────────────────────────────────────
🔄 ITERATION 1/5
──────────────────────────────────────────────────────────────────────

📝 Step 1: Executing workflow tasks...
   ✅ Workflow execution completed

🧪 Step 2: Testing generated strategy...
   📁 Found 4 strategy file(s)
   
   🧪 Testing: ai_strategy_data_loading
      ❌ FAILED (1.2s)
         ImportError: No module named 'pandas'
   
   🧪 Testing: ai_strategy_indicators
      ❌ FAILED (0.8s)
         SyntaxError: invalid syntax at line 15

📊 Test Results:
   Total: 4
   Passed: 0 ✅
   Failed: 4 ❌

🔧 Step 3: Analyzing failures and generating fixes...
   Error Type: import_error
      + fix_imports_ai_strategy_data_loading_iter1
   Error Type: syntax_error
      + fix_syntax_ai_strategy_indicators_iter1
   ✅ Created 2 fix task(s)
   🔄 Retrying in next iteration...

──────────────────────────────────────────────────────────────────────
🔄 ITERATION 2/5
──────────────────────────────────────────────────────────────────────

📝 Step 1: Executing workflow tasks...
   [CoderAgent] Fixing import errors...
   [CoderAgent] Fixing syntax errors...
   ✅ Workflow execution completed

🧪 Step 2: Testing generated strategy...
   🧪 Testing: ai_strategy_data_loading
      ✅ PASSED (2.1s)
   
   🧪 Testing: ai_strategy_indicators
      ✅ PASSED (1.8s)
   
   🧪 Testing: ai_strategy_entry
      ❌ FAILED (1.5s)
         AssertionError: Expected signal==1, got signal==0

📊 Test Results:
   Total: 4
   Passed: 3 ✅
   Failed: 1 ❌

🔧 Step 3: Analyzing failures and generating fixes...
   Error Type: logic_error
      + fix_logic_ai_strategy_entry_iter2
   ✅ Created 1 fix task(s)
   🔄 Retrying in next iteration...

──────────────────────────────────────────────────────────────────────
🔄 ITERATION 3/5
──────────────────────────────────────────────────────────────────────

📝 Step 1: Executing workflow tasks...
   [DebuggerAgent] Analyzing logic error...
   [DebuggerAgent] Fix: Corrected RSI threshold comparison
   ✅ Workflow execution completed

🧪 Step 2: Testing generated strategy...
   🧪 Testing: ai_strategy_entry
      ✅ PASSED (1.9s)

📊 Test Results:
   Total: 4
   Passed: 4 ✅
   Failed: 0 ❌

======================================================================
✅ SUCCESS! All tests passed in iteration 3
======================================================================

======================================================================
📊 FINAL REPORT
======================================================================
Status: ✅ SUCCESS
Total Iterations: 3/5
Report: iteration_report_wf_def789_20251120_164500.json
======================================================================

✅ Strategy perfected in 3 iterations!
```

## Tips

1. **Start Simple** - Test with simple strategies first to verify the loop works
2. **Monitor Progress** - Watch each iteration to understand what's being fixed
3. **Check Reports** - Review iteration_report JSON for detailed history
4. **Adjust Iterations** - Increase `--max-iterations` for complex strategies
5. **Use Fast Validate** - Run `fast_validate.py` first for quick syntax checks

## Troubleshooting

### Loop Not Making Progress

**Problem:** Same error repeated across iterations

**Solution:**
- Check if error is actually fixable by the agents
- Review fix task metadata to see what was attempted
- Manually inspect the generated code
- Increase max iterations

### Agent Not Responding

**Problem:** Execution hangs or times out

**Solution:**
- Check agent logs in console
- Verify message bus is running (Redis if configured)
- Restart CLI and try again
- Check router keys are valid

### Tests Still Failing

**Problem:** All iterations used but tests still fail

**Solution:**
- Review the iteration report to see error patterns
- Run `fast_validate.py` to check for basic syntax issues
- Manually fix obvious errors and rerun
- Simplify the strategy request

## Next Steps

After successful iteration:

1. ✅ Review generated strategy code
2. ✅ Check test reports and metrics
3. ✅ Run backtest with real data
4. ✅ Deploy to paper trading
5. ✅ Monitor live performance

---

**Ready to build self-improving strategies!** 🚀
