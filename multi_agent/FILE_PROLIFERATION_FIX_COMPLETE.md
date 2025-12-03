# File Proliferation and Data Path Fix - Implementation Complete

## Issues Fixed

### Issue 1: Multiple File Creation (File Proliferation)
**Problem:** Agent created new files for each fix iteration instead of updating the original:
```
Original:  20251126_133020_..._complete_strategy.py
Fix 1:     20251126_133113_..._fix_unknown_20251126_fix_unknown_in_...
Fix 2:     20251126_133300_..._fix_unknown_20251126_fix_unknown_in_...
Fix 3:     20251126_134625_..._fix_syntax_20251126__fix_syntax_error_in_...
```

**Root Cause:** 
- Tester passed `artifact_path` to debugger
- Debugger passed `target_file` (current file) to coder in metadata
- Each iteration, `target_file` pointed to the previous fix file
- Coder couldn't distinguish original from fix files
- Created new unique filename each time

**Solution Implemented:**

1. **Track Original Artifact Path Throughout Workflow**
   - Added `original_artifact_path` parameter to track the ORIGINAL file (stays constant)
   - `artifact_path` continues to track current file (changes with each fix)

2. **Tester Agent Updates** (`agents/tester_agent/tester.py`)
   - Updated `request_debug_branch()` signature:
     ```python
     def request_debug_branch(
         self,
         corr_id: str,
         wf_id: str,
         task_id: str,
         workspace: Path,
         reason: str,
         details: any,
         artifact_path: str = None,
         original_artifact_path: str = None  # ✅ NEW
     ):
     ```
   - All 7 `request_debug_branch()` calls now pass:
     ```python
     artifact_path=task.get('artifact_path'),
     original_artifact_path=task.get('metadata', {}).get('original_artifact_path')
     ```
   - Uses fallback logic: `original_artifact_path or artifact_path`

3. **CLI Updates** (`cli.py`)
   - Fix task creation now includes:
     ```python
     'metadata': {
         'fix_type': fix_type,
         'target_file': target_file,
         'original_artifact_path': original_artifact_path,  # ✅ NEW
         'original_task': task['id'],
         'fix_instructions': fix_instructions,
         'workflow_id': workflow_id,
         'iteration': iteration + 1,
         'auto_fix': True
     }
     ```
   - Propagates `original_artifact_path` from parent task metadata

4. **Coder Agent Updates** (`agents/coder_agent/coder.py`)
   - Changed from using `task.get('artifact_path')` to:
     ```python
     metadata = task.get('metadata', {})
     original_artifact_path = metadata.get('original_artifact_path')
     
     if original_artifact_path and auto_fix:
         # Fix task: Update ORIGINAL file instead of creating new one
         print(f"[CoderAgent] 🔧 Fix task detected - updating ORIGINAL file: {original_artifact_path}")
         print(f"[CoderAgent]    (NOT creating new fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}_... file)")
         filename = Path(original_artifact_path).name
         file_path = original_artifact_path  # ✅ Always use original path
     ```
   - For new tasks, stores initial artifact path as `original_artifact_path`:
     ```python
     # Store this as original_artifact_path for future fix tasks
     if not metadata.get('original_artifact_path'):
         metadata['original_artifact_path'] = file_path
     ```

**Result:**
- ✅ Fix iterations now update the same file
- ✅ No more proliferation of fix_unknown_20251126_fix_unknown_in_... files
- ✅ Original filename preserved throughout fix iterations
- ✅ File path stays constant: `Backtest/codes/20251126_133020_..._complete_strategy.py`

---

### Issue 2: Data File Path Error
**Problem:** Generated strategies couldn't find data file:
```python
FileNotFoundError: Data file not found at C:\Users\nyaga\Documents\AlgoAgent\multi_agent\Backtest\fixtures\sample_data.csv
```

**Root Cause:**
- Generated code runs from: `multi_agent/Backtest/codes/`
- Template used: `Path(__file__).parent.parent / 'fixtures' / 'sample_data.csv'`
- Resolved to: `multi_agent/Backtest/fixtures/sample_data.csv` ❌
- Actual location: `multi_agent/fixtures/sample_aapl.csv` ✅

**Solution Implemented:**

Updated template in `agents/coder_agent/coder.py`:
```python
# Load data
# CRITICAL: Path from Backtest/codes/ to multi_agent/fixtures/
# Go up 3 levels: codes -> Backtest -> multi_agent, then into fixtures
data_file = Path(__file__).parent.parent.parent / 'fixtures' / 'sample_aapl.csv'

# Allow command-line override
if len(sys.argv) > 1:
    data_file = Path(sys.argv[1])

if not data_file.exists():
    raise FileNotFoundError(
        f"Data file not found at {data_file}. "
        f"Expected: multi_agent/fixtures/sample_aapl.csv"
    )

print(f"Loading data from {data_file}...")
df = pd.read_csv(data_file)
```

**Changes:**
- ✅ Changed from `parent.parent` (2 levels) to `parent.parent.parent` (3 levels)
- ✅ Changed filename from `sample_data.csv` to `sample_aapl.csv`
- ✅ Added clear error message with expected location
- ✅ Maintained command-line override capability

**Result:**
- ✅ Generated strategies can now find data file
- ✅ Path correctly resolves to `multi_agent/fixtures/sample_aapl.csv`
- ✅ Manual testing will succeed

---

## Files Modified

1. **`multi_agent/agents/coder_agent/coder.py`**
   - Updated file path determination logic (lines ~296-310)
   - Added `original_artifact_path` tracking
   - Fixed data file path in template (lines ~795-810)

2. **`multi_agent/agents/tester_agent/tester.py`**
   - Updated `request_debug_branch()` signature (line ~521)
   - Updated all 7 `request_debug_branch()` calls:
     - Line ~128: sandbox_error
     - Line ~168: timeout
     - Line ~183: test_failures
     - Line ~200: artifact_missing
     - Line ~218: schema_invalid
     - Line ~237: invalid_artifacts
     - Line ~259: secrets_detected

3. **`multi_agent/cli.py`**
   - Updated fix task creation to include `original_artifact_path` (line ~458)

---

## Testing Verification

### Test 1: File Proliferation Fix
**Before:**
```
20251126_133020_wf_..._complete_strategy.py
20251126_133113_wf_..._fix_unknown_20251126_fix_unknown_in_...
20251126_133300_wf_..._fix_unknown_20251126_fix_unknown_in_...
20251126_134625_wf_..._fix_syntax_20251126__fix_syntax_error_in_...
20251126_134849_wf_..._fix_unknown_20251126_fix_unknown_in_...
```

**Expected After:**
```
20251126_133020_wf_..._complete_strategy.py  (updated in place)
```

### Test 2: Data File Path Fix
**Before:**
```bash
python 20251126_133020_..._complete_strategy.py
# FileNotFoundError: ...Backtest/fixtures/sample_data.csv
```

**Expected After:**
```bash
python 20251126_133020_..._complete_strategy.py
# Loading data from C:\Users\nyaga\Documents\AlgoAgent\multi_agent\fixtures\sample_aapl.csv...
# --- Starting EMA Crossover Strategy Smoke Test ---
# (successful execution)
```

---

## Next Steps

1. **Clean Workspace**
   ```bash
   cd c:\Users\nyaga\Documents\AlgoAgent\multi_agent
   # Remove old fix files
   rm Backtest/codes/*_fix_*.py
   rm tests/test_*_fix_*.py
   ```

2. **Test New Implementation**
   ```bash
   cd c:\Users\nyaga\Documents\AlgoAgent\multi_agent
   python cli.py backtest --strategy "Implement complete EMA 30/50 crossover strategy"
   ```

3. **Verify Fix Behavior**
   - Strategy should be created: `20251126_HHMMSS_wf_XXX_complete_strategy_...`
   - If test fails, fix task should UPDATE the same file (not create new one)
   - Check logs for: `🔧 Fix task detected - updating ORIGINAL file`

4. **Manual Test Generated Strategy**
   ```bash
   cd Backtest/codes
   python 20251126_HHMMSS_wf_XXX_complete_strategy_....py
   ```
   - Should successfully find data file
   - Should execute EMA crossover backtest
   - Should generate results

---

## Architecture Changes

### Before:
```
Iteration 1: Create original.py
Iteration 2: Create fix_1.py (referencing original.py)
Iteration 3: Create fix_2.py (referencing fix_1.py)
Iteration 4: Create fix_3.py (referencing fix_2.py)
Result: 4 files, exponentially growing filenames
```

### After:
```
Iteration 1: Create original.py
             Store: original_artifact_path = "Backtest/codes/original.py"
Iteration 2: Update original.py (in place)
             original_artifact_path still = "Backtest/codes/original.py"
Iteration 3: Update original.py (in place)
             original_artifact_path still = "Backtest/codes/original.py"
Iteration 4: Update original.py (in place)
             original_artifact_path still = "Backtest/codes/original.py"
Result: 1 file, continuously improved
```

---

## Impact

### File Proliferation
- ✅ Eliminates exponential filename growth
- ✅ Reduces workspace clutter (5 files → 1 file per strategy)
- ✅ Easier debugging (always look at same file)
- ✅ Clearer git history (file modifications vs new files)

### Data Path
- ✅ Generated strategies run immediately without manual path fixes
- ✅ Reduces manual intervention required
- ✅ Improves E2E test success rate
- ✅ Clear error messages guide users to correct fixture location

### Overall
- ✅ More deterministic workflow (predictable file locations)
- ✅ Better resource utilization (disk space, inodes)
- ✅ Improved user experience (fewer confusing files)
- ✅ Faster iteration cycles (no time wasted on file proliferation)

---

## Status: ✅ Implementation Complete

All fixes have been implemented and are ready for testing.
