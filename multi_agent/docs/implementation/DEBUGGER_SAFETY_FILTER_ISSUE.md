# Debugger Agent Safety Filter Issue

**Date:** November 22, 2025  
**Status:** ⚠️ BLOCKING - Safety filter prevents automated fix workflow  
**Severity:** High - Blocks iterative loop completion  
**Component:** Debugger Agent → Coder Agent integration

---

## Problem Summary

The Debugger Agent successfully analyzes test failures and creates fix tasks, but the **Coder Agent cannot execute these fix tasks** because Gemini's safety filter (finish_reason=2: SAFETY) blocks all requests containing error context, debugging instructions, or performance optimization directives.

### Impact

- ✅ Iteration loop correctly detects pending tasks and continues
- ✅ Debugger properly analyzes failures and creates fix tasks
- ❌ **Coder cannot generate fixes** due to safety filter
- ❌ **Automated error recovery workflow is blocked**
- ❌ System cannot complete multi-iteration improvements

---

## Root Cause Analysis

### 1. Safety Filter Trigger Points

Gemini's safety filter blocks requests containing:

1. **Error descriptions** with words like "timeout", "failure", "error"
2. **Stack traces or debugging context** (even sanitized)
3. **Code optimization instructions** mentioning "fix", "debug", "performance issue"
4. **References to failing code** or problematic behavior

### 2. Current Sanitization Attempts (All Failed)

We've progressively sanitized the debugger output:

#### Attempt 1: Remove raw tracebacks
```python
# BEFORE
description: f"""
Error: {error_details}
Traceback: {full_traceback[:1000]}
"""

# AFTER
description: f"""
Issue: {error_message}  # Extracted summary only
"""
```
**Result:** ❌ Still blocked

#### Attempt 2: Remove code examples
```python
# BEFORE
**Example Optimization:**
```python
df['ema'] = df['close'].ewm(span=period).mean()
```

# AFTER
**Requirements:**
- Use vectorized pandas operations
- Pre-calculate all indicators
```
**Result:** ❌ Still blocked

#### Attempt 3: Use neutral task-oriented language
```python
# BEFORE
description: "Fix timeout error in strategy"

# AFTER  
description: "Optimize strategy to improve execution speed"
```
**Result:** ❌ Still blocked

### 3. Architecture Conflict

Per **ARCHITECTURE.md Section K.7**, the Debugger Agent MUST:

> "For each failure, Tester MUST:
> 1. Classify failure type
> 2. Extract minimal repro (failing test + fixture)
> 3. Publish `workflow.branch_created` to `DEBUGGER_REQUESTS` with:
>    - Failing test names + traceback
>    - Minimal fixture (e.g., bar_simple_long.csv)
>    - Exact reproduce command (Docker command)
>    - Correlation ID + task ID"

**The architecture requires passing error context, but Gemini blocks it.**

---

## Evidence: Test Execution Flow

### Successful Iterations (1-2)

```
ITERATION 1
✓ Coder generated strategy (103s)
✓ Tester detected timeout
✓ Debugger analyzed failure
✓ Created fix task: fix_timeout_..._iter1

ITERATION 2  
✓ Debugger executed fix_timeout_..._iter1
✓ Analyzed timeout error
✓ Created coder fix task: fix_timeout_..._iter2
✓ Updated TodoList

ITERATION 3
✓ Detected pending task: fix_timeout_..._iter2
✓ Initialized Coder Agent
❌ BLOCKED: finish_reason=2 (SAFETY)
```

### Error Output

```
[CoderAgent] Safety filter triggered with gemini-2.5-flash
[CoderAgent] 🔄 Retrying with Gemini 2.5 Pro (relaxed safety)...
❌ Failed: Non-retryable provider error

Gemini API error: The `response.text` quick accessor requires 
the response to contain a valid `Part`, but none were returned. 
The candidate's [finish_reason] is 2.
```

**finish_reason=2 = SAFETY** - Gemini refused to generate response

---

## Attempted Solutions

### Solution 1: Sanitize All Error Context ❌

**Implementation:**
- Removed raw tracebacks
- Removed code examples  
- Used neutral language ("optimize" instead of "fix")
- Extracted only error message summary

**Result:** Still blocked by safety filter

**Why it failed:** Even minimal references to errors/failures trigger the filter

### Solution 2: Generic Optimization Request ❌

**Implementation:**
```python
if "timeout" in error_details.lower():
    description = """Optimize strategy performance.

Requirements:
- Use vectorized operations
- Complete execution within 30 seconds
"""
```

**Result:** Still blocked

**Why it failed:** Context from reading the failing strategy file might still trigger filter

### Solution 3: Remove File Reading ⏳ (Not yet tested)

**Hypothesis:** Reading the 8KB failing strategy file and passing it to Coder might trigger the filter, even if the task description is clean.

**Proposed change:**
```python
# CURRENT: Debugger reads failing file
strategy_code = strategy_path.read_text()

# PROPOSED: Don't pass failing code, just tell Coder to regenerate
description = "Regenerate strategy with performance optimizations"
```

---

## Architecture Implications

### Current Architecture Issues

1. **Message Bus Design**
   - Architecture assumes error context can be passed via message bus
   - Gemini safety filter makes this impossible
   - Conflicts with Section K.7 requirements

2. **Debugger-Coder Contract**
   - Debugger is supposed to provide detailed fix instructions
   - Coder needs error context to generate appropriate fixes
   - Safety filter breaks this contract

3. **Iterative Loop Workflow**
   - Designed for: Test Failure → Debug → Fix → Retest
   - Reality: Test Failure → Debug → **BLOCKED** → Manual intervention

### Architecture Compliance Status

| Requirement | Status | Notes |
|-------------|--------|-------|
| K.7: Pass failing test names + traceback | ❌ | Triggers safety filter |
| K.7: Include minimal repro command | ❌ | Triggers safety filter |
| K.7: Extract failure classification | ✅ | Works (syntax_error, timeout, etc.) |
| K.7: Publish to DEBUGGER_REQUESTS | ✅ | Message bus works |
| K.7: Create branch todos | ✅ | TodoList updated correctly |
| K.1: Iterative fix workflow | ❌ | Blocked at Coder execution |

---

## Proposed Solutions

### Option 1: Use Alternative LLM for Fix Tasks ⭐ RECOMMENDED

**Implementation:**
```python
# In cli.py _execute_coder_task()
if task.get('metadata', {}).get('auto_fix'):
    # Use Claude/GPT-4 for fix tasks (no aggressive safety filter)
    model = "claude-3-5-sonnet"
else:
    # Use Gemini for normal generation
    model = "gemini-2.5-flash"
```

**Pros:**
- ✅ Maintains architecture design (error context passed as intended)
- ✅ No changes to message bus contract
- ✅ Automated workflow continues
- ✅ Claude/GPT-4 have less aggressive safety filters

**Cons:**
- ⚠️ Requires additional API keys
- ⚠️ Increased cost per fix iteration
- ⚠️ Adds model routing complexity

**Architecture impact:** Minimal - add model selection logic to LLM router

### Option 2: Human-in-the-Loop for Fix Tasks

**Implementation:**
- Debugger generates detailed report
- System pauses and notifies human
- Human reviews and approves fix instructions
- Coder executes with approved context

**Pros:**
- ✅ Aligns with Section L "manual approval" philosophy
- ✅ Ensures fix quality
- ✅ No safety filter issues

**Cons:**
- ❌ Breaks automated iterative loop
- ❌ Defeats purpose of multi-agent automation
- ❌ Slows down development significantly

**Architecture impact:** Major - requires approval workflow, notification system

### Option 3: Generic Regeneration (No Error Context)

**Implementation:**
```python
# Debugger creates minimal fix task
fix_task = {
    'title': 'Optimize strategy performance',
    'description': 'Regenerate with vectorized operations',
    # NO error details, NO failing code
}
```

**Pros:**
- ✅ Avoids safety filter
- ✅ Maintains automated workflow
- ✅ No additional LLM costs

**Cons:**
- ❌ Coder lacks context about what failed
- ❌ May regenerate same bug
- ❌ Violates architecture Section K.7
- ❌ Lower fix success rate

**Architecture impact:** Major - removes error feedback loop

### Option 4: Retry with Escalating Simplification

**Implementation:**
```python
# Attempt 1: Full error context (may be blocked)
# Attempt 2: Sanitized error summary (may be blocked)
# Attempt 3: Generic optimization request (likely works)
# Attempt 4: Complete regeneration (always works)
```

**Pros:**
- ✅ Tries to provide maximum context
- ✅ Falls back to working solution
- ✅ Maintains automation

**Cons:**
- ⚠️ Multiple API calls increase latency and cost
- ⚠️ Complex retry logic
- ⚠️ Still may fail if even generic requests blocked

**Architecture impact:** Moderate - add retry logic to Coder Agent

---

## Recommended Implementation: Option 1 + Option 4

### Phase 1: Multi-Model Support (Immediate)

1. **Update LLM Router** (`llm/router.py`):
   ```python
   def send_chat(self, task_type='generation', **kwargs):
       if task_type == 'fix' or task_type == 'debug':
           # Use Claude for fix tasks
           provider = 'anthropic'
           model = 'claude-3-5-sonnet'
       else:
           # Use Gemini for normal generation
           provider = 'gemini'
           model = 'gemini-2.5-flash'
   ```

2. **Update Coder Agent** (`agents/coder_agent/coder.py`):
   ```python
   auto_fix = task.get('metadata', {}).get('auto_fix', False)
   response = self.router.send_chat(
       task_type='fix' if auto_fix else 'generation',
       messages=[{'role': 'user', 'content': prompt}]
   )
   ```

3. **Add Claude Provider** (`llm/providers.py`):
   ```python
   class AnthropicProvider:
       def chat_completion(self, api_key, model, messages, **kwargs):
           # Implement Anthropic API client
   ```

### Phase 2: Fallback Logic (Future)

If Claude also blocks (unlikely), add escalating simplification:

```python
attempts = [
    ('full_context', full_error_description),
    ('sanitized', sanitized_description),
    ('generic', generic_optimization_request),
    ('regenerate', minimal_regeneration_task)
]

for attempt_type, description in attempts:
    try:
        result = coder.generate(description)
        break  # Success
    except SafetyFilterError:
        continue  # Try next attempt
```

---

## Testing Plan

### Test 1: Claude Integration
```bash
# Add ANTHROPIC_API_KEY to .env
# Run iteration with fix task
python cli.py iterate wf_0fc6bbb9f3f4
```

**Expected:** Iteration 3 completes successfully with Claude

### Test 2: Fallback Logic
```bash
# Temporarily disable Claude
# Verify fallback to generic optimization
python cli.py iterate wf_0fc6bbb9f3f4
```

**Expected:** Falls back to generic request, still completes

### Test 3: End-to-End
```bash
# Fresh workflow
python cli.py submit "Create EMA crossover strategy"
```

**Expected:** 
- Iteration 1: Generate (Gemini)
- Iteration 2: Debug (Debugger)
- Iteration 3: Fix (Claude)
- Iteration 4: Retest (Tester)
- Success!

---

## Architecture Updates Required

### 1. Update ARCHITECTURE.md

Add new section:

**Section K.12 — LLM Model Selection for Safety Filter Compliance**

```markdown
The system uses different LLM models based on task type:

- **Gemini 2.5 Flash/Pro:** Strategy generation, normal tasks
- **Claude 3.5 Sonnet:** Fix tasks, debugging, error recovery
- **GPT-4:** Fallback for both (if needed)

**Rationale:** Gemini has aggressive safety filters that block
error-related content. Claude handles debugging context without
blocking, maintaining the automated fix workflow.

**Configuration:** Set via environment variables:
- GEMINI_API_KEY (required)
- ANTHROPIC_API_KEY (required for fix tasks)
- OPENAI_API_KEY (optional fallback)
```

### 2. Update LLM Router Documentation

File: `docs/api/llm_key_rotation.md`

Add:
- Multi-provider support
- Task-type based routing
- Safety filter handling strategy

### 3. Update Debugger Documentation

File: `docs/implementation/DEBUGGER_AGENT_COMPLETE.md` (create)

Document:
- Error context sanitization
- Model selection for fix tasks
- Fallback strategies

---

## Open Questions

1. **Cost Impact:** Claude is ~3x more expensive than Gemini. Acceptable for fix tasks?
   - **Recommendation:** Yes - fix tasks are infrequent and critical

2. **API Key Management:** Should we require Claude key or make it optional?
   - **Recommendation:** Required for automated workflow, warn if missing

3. **Model Selection:** Should we allow user to override model choice?
   - **Recommendation:** Yes - add `--fix-model` CLI flag

4. **Fallback Order:** If Claude unavailable, try GPT-4 or fail?
   - **Recommendation:** Try GPT-4, then fail with helpful error

---

## Success Metrics

After implementing Option 1:

- ✅ Fix tasks complete without safety filter blocks
- ✅ Iterative loop completes 3+ iterations automatically
- ✅ Success rate > 80% for timeout/performance fixes
- ✅ <5 second overhead for model switching
- ✅ Architecture compliance maintained

---

## Timeline

| Phase | Task | Duration | Owner |
|-------|------|----------|-------|
| 1 | Add Claude provider to LLM router | 2 hours | Dev |
| 2 | Update Coder Agent for task-type routing | 1 hour | Dev |
| 3 | Test Claude integration with fix tasks | 1 hour | QA |
| 4 | Update architecture documentation | 1 hour | Dev |
| 5 | Add fallback logic (optional) | 2 hours | Dev |

**Total:** 1 day for critical path (Phase 1-4)

---

## Conclusion

The safety filter issue is a **fundamental architectural conflict** between:
- Gemini's aggressive content filtering
- The architecture's requirement to pass error context

**Recommended solution:** Use Claude for fix tasks while maintaining Gemini for generation. This preserves the automated workflow while working within LLM provider constraints.

**Alternative:** If cost is prohibitive, implement human-in-the-loop approval for fix tasks (Option 2), but this defeats the automation goal.

---

**Status:** Awaiting decision on implementation approach  
**Next Steps:** Approve Option 1 and begin Phase 1 implementation  
**Blockers:** ANTHROPIC_API_KEY required
