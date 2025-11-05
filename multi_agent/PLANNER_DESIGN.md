# Planner Design: Predictable, Testable, Debuggable

**Status:** Design Specification  
**Date:** November 5, 2025  
**Purpose:** Define the architecture for making the Planner deterministic, testable, and automatically debuggable through branch todos

---

## 🎯 Core Principles

The Planner must produce **predictable, independently testable milestones** where:

1. **Every step has machine-executable acceptance tests**
2. **Failures create branch todos for automated debugging**
3. **Contract-first development prevents spec drift**
4. **Deterministic tests ensure reproducibility**
5. **Shallow debugging trees prevent exponential complexity**

---

## ✅ Verdict: This Approach is Sound

### Strengths

✅ **Isolation** - Each milestone is small and testable, easier to debug  
✅ **Fail-fast** - Failures surface at precise step boundaries  
✅ **Reproducibility** - Deterministic tests make CI reliable  
✅ **Traceability** - Branch todos create clear audit trail  
✅ **Human-in-the-loop** - Controlled automation with approval gates  

### Risk Mitigation

| Risk | Mitigation Strategy |
|------|---------------------|
| **Spec drift between steps** | Machine-readable contracts from Architect before Coder runs |
| **Flaky tests** | Deterministic fixtures, fixed seeds, separate `flaky_retry` policy |
| **Too-large milestones** | Enforce max complexity/time limits, auto-split in Planner |
| **Exponential branching** | Limit depth (`max_debug_branch_depth=3`), require human approval after N cycles |

---

## 📋 The 4 Primary Steps (Default Template)

Every strategy workflow should follow these 4 atomic milestones:

### 1. Data Loading Integration

**Purpose:** Implement data fetching and preparation  
**Agent Role:** `coder`

**Contract:**
```python
def fetch_and_prepare_data(symbol: str, start: str, end: str) -> pd.DataFrame:
    """
    Returns: DataFrame with columns ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    """
```

**Acceptance Tests:**
```json
{
  "tests": [
    {
      "cmd": "pytest tests/test_adapter.py::test_fetch -q --json-report",
      "timeout_seconds": 30
    },
    {
      "cmd": "pytest tests/test_adapter.py::test_columns -q --json-report",
      "timeout_seconds": 20
    }
  ],
  "expected_artifacts": [
    "Backtest/backtesting_adapter.py",
    "fixtures/sample_aapl.csv"
  ],
  "metrics": [
    {"name": "rows_min", "operator": ">=", "value": 10}
  ]
}
```

**Deterministic Fixtures:**
- `fixtures/sample_aapl.csv` - Known OHLCV data for reproducible tests
- Mock yfinance/API calls to return fixture data

---

### 2. Indicator & Candle Pattern Loading

**Purpose:** Implement technical indicators and pattern recognition  
**Agent Role:** `architect` (defines interfaces) → `coder` (implements)

**Contract:**
```python
def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """RSI calculation with defined NaN handling"""

def is_engulfing(candle_window: pd.DataFrame) -> bool:
    """Bullish engulfing pattern detector"""
```

**Acceptance Tests:**
```json
{
  "tests": [
    {
      "cmd": "pytest tests/test_indicators.py::test_rsi_values -q --json-report",
      "timeout_seconds": 20,
      "fixture": "fixtures/rsi_expected.json"
    },
    {
      "cmd": "pytest tests/test_patterns.py::test_engulfing_detection -q --json-report",
      "timeout_seconds": 20
    }
  ],
  "expected_artifacts": [
    "contracts/indicator_contract.json",
    "indicators/rsi.py",
    "indicators/patterns.py"
  ]
}
```

**Deterministic Fixtures:**
- `fixtures/rsi_expected.json` - Known RSI values for sample data
- `fixtures/pattern_cases.json` - Labeled candle patterns

---

### 3. Entry Conditions Setup

**Purpose:** Implement buy signal logic  
**Agent Role:** `coder`

**Contract:**
```python
def should_enter(bar: pd.Series, indicators: dict, position: Optional[dict]) -> bool:
    """
    Args:
        bar: Current OHLCV row
        indicators: Dict of indicator values (e.g., {'rsi': 28.5, 'macd': 1.2})
        position: Current position or None
    
    Returns:
        True if entry conditions met, False otherwise
    """
```

**Acceptance Tests:**
```json
{
  "tests": [
    {
      "cmd": "pytest tests/test_entry.py::test_entry_true_false -q --json-report",
      "timeout_seconds": 20,
      "fixture": "fixtures/entry_scenarios.json"
    }
  ],
  "expected_artifacts": [
    "Backtest/codes/ai_strategy_entry.py"
  ]
}
```

**Deterministic Fixtures:**
- `fixtures/entry_scenarios.json` - Cases that should/shouldn't trigger entry

---

### 4. Exit Conditions Setup

**Purpose:** Implement sell signal and stop/target logic  
**Agent Role:** `coder`

**Contract:**
```python
def should_exit(bar: pd.Series, indicators: dict, position: dict) -> bool:
    """
    Args:
        bar: Current OHLCV row
        indicators: Dict of indicator values
        position: {'entry_price': float, 'size': int, 'pnl': float}
    
    Returns:
        True if exit conditions met (profit target, stop loss, signal)
    """
```

**Acceptance Tests:**
```json
{
  "tests": [
    {
      "cmd": "pytest tests/test_exit.py::test_stop_loss -q --json-report",
      "timeout_seconds": 20
    },
    {
      "cmd": "pytest tests/test_exit.py::test_take_profit -q --json-report",
      "timeout_seconds": 20
    }
  ],
  "expected_artifacts": [
    "Backtest/codes/ai_strategy_exit.py"
  ]
}
```

**Deterministic Fixtures:**
- `fixtures/exit_scenarios.json` - Stop loss and take profit cases

---

## 🌳 Branch Todo Pattern (Automated Debugging)

### When to Create Branch Todos

When a primary step **fails its acceptance tests**, the Orchestrator automatically creates a **branch todo** to diagnose and fix the issue.

### Branch Todo Structure

```json
{
  "id": "t2_branch_01",
  "parent_id": "t2_indicators",
  "title": "Debug indicator failures (RSI mismatch)",
  "agent_role": "debugger",
  "branch_reason": "test_failure",
  "debug_instructions": "pytest failed: RSI values mismatch. Expected 28.5, got 32.1. Check SMA window calculation and NaN handling.",
  "acceptance_criteria": {
    "tests": [
      {
        "cmd": "pytest tests/test_indicators.py::test_rsi_values -q --json-report",
        "timeout_seconds": 20
      }
    ],
    "expected_artifacts": [
      "diagnostics/t2_indicators_failure_report.json"
    ]
  },
  "dependencies": [],
  "is_temporary": true,
  "max_debug_attempts": 3,
  "max_lifetime_seconds": 600
}
```

### Branch Todo Fields

| Field | Type | Description |
|-------|------|-------------|
| `parent_id` | string | ID of the failing primary todo |
| `branch_reason` | enum | `test_failure`, `spec_mismatch`, `timeout`, `implementation_bug` |
| `debug_instructions` | string | Diagnostic summary (tracebacks, failing tests, sample inputs) |
| `is_temporary` | boolean | Always `true` for branch todos |
| `max_debug_attempts` | integer | Max retry attempts (default: 3) |
| `max_lifetime_seconds` | integer | Time limit for branch resolution |
| `target_agent_role` | string | Which agent handles this: `coder`, `architect`, `tester`, `debugger` |

---

## 🔀 Failure Routing Logic

The Orchestrator routes failures to the appropriate agent based on **failure type**:

### Failure Categories

```json
"failure_routing": {
  "implementation_bug": "coder",
  "spec_mismatch": "architect",
  "timeout": "tester",
  "flaky_test": "tester",
  "missing_dependency": "coder"
}
```

### Routing Rules

| Failure Type | Description | Target Agent | Example |
|--------------|-------------|--------------|---------|
| `implementation_bug` | Logic error, failing assertions | `coder` | RSI calculation returns wrong value |
| `spec_mismatch` | Contract violation, wrong interface | `architect` | Function signature doesn't match contract |
| `timeout` | Test exceeds time limit | `tester` | Infinite loop or slow computation |
| `flaky_test` | Intermittent failures | `tester` | Non-deterministic test needs fixtures |
| `missing_dependency` | Import errors, missing files | `coder` | Module not found |

### Example: Routing Decision Tree

```python
def determine_failure_target(test_report: dict) -> str:
    """Analyze failure and route to appropriate agent."""
    
    if "ImportError" in test_report['error_message']:
        return "coder", "missing_dependency"
    
    if "AssertionError: expected" in test_report['error_message']:
        # Check if it's interface vs value mismatch
        if "signature" in test_report['error_message'].lower():
            return "architect", "spec_mismatch"
        else:
            return "coder", "implementation_bug"
    
    if test_report['duration'] > test_report['timeout']:
        return "tester", "timeout"
    
    # Default to debugger for analysis
    return "debugger", "unknown"
```

---

## 🎛️ Orchestrator Behavior Rules

### 1. Run Primary Todo

```python
# Execute task with acceptance tests
result = execute_task(task_id)

if result.status == "passed":
    # Continue to next task
    mark_completed(task_id)
    continue_workflow()
else:
    # Capture diagnostics
    diagnostics = {
        "test_report": result.test_report,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "traceback": result.traceback,
        "artifacts": result.artifacts
    }
```

### 2. Decide Branch Target

```python
# Analyze failure type
failure_type, target_agent = determine_failure_target(diagnostics['test_report'])

# Check failure routing config
routing_config = task.failure_routing or DEFAULT_ROUTING
target_agent = routing_config.get(failure_type, "debugger")
```

### 3. Create Branch Todo

```python
branch_todo = {
    "id": f"{task_id}_branch_{branch_count:02d}",
    "parent_id": task_id,
    "title": f"Debug {task.title} - {failure_type}",
    "agent_role": target_agent,
    "branch_reason": failure_type,
    "debug_instructions": generate_debug_instructions(diagnostics),
    "acceptance_criteria": task.acceptance_criteria,  # Re-use parent tests
    "is_temporary": True,
    "max_debug_attempts": 3,
    "dependencies": []
}

# Block downstream tasks
block_tasks_depending_on(task_id)

# Dispatch branch
dispatch_task(branch_todo)
```

### 4. Branch Lifecycle Management

```python
# Retry loop for branch
for attempt in range(branch_todo.max_debug_attempts):
    branch_result = execute_task(branch_todo.id)
    
    if branch_result.status == "passed":
        # Branch succeeded, re-run parent tests
        parent_result = rerun_acceptance_tests(task_id)
        
        if parent_result.status == "passed":
            mark_completed(task_id)
            unblock_downstream_tasks(task_id)
            break
        else:
            # Still failing, create deeper branch or escalate
            if current_branch_depth < max_branch_depth:
                create_branch_todo(task_id, branch_depth + 1)
            else:
                escalate_to_human(task_id)
    else:
        # Branch failed, retry or escalate
        if attempt == branch_todo.max_debug_attempts - 1:
            set_workflow_status("blocked")
            notify_planner_review_required(task_id, diagnostics)
```

### 5. Planner Approval Modes

**Auto-fix Mode:**
```json
{
  "auto_fix_mode": true,
  "max_branch_depth": 2,
  "max_debug_attempts": 3
}
```
- Automatically creates and runs branch todos
- Suitable for low-risk, well-tested workflows

**Manual Mode:**
```json
{
  "auto_fix_mode": false,
  "require_planner_approval": true
}
```
- Orchestrator pauses on failure
- Emits `planner.review_required` event
- Human reviews diagnostics and approves branch creation

---

## 📊 Example: Complete TodoList with Branch Support

```json
{
  "todo_list_id": "workflow_momentum_001",
  "workflow_name": "Momentum Strategy with RSI",
  "metadata": {
    "auto_fix_mode": true,
    "max_branch_depth": 2,
    "max_debug_attempts": 3
  },
  "items": [
    {
      "id": "t1_data_integration",
      "title": "Data Loading Integration",
      "agent_role": "coder",
      "acceptance_criteria": {
        "tests": [
          {
            "cmd": "pytest tests/test_adapter.py::test_fetch -q --json-report",
            "timeout_seconds": 30
          }
        ],
        "expected_artifacts": ["Backtest/backtesting_adapter.py"],
        "metrics": [{"name": "rows_min", "operator": ">=", "value": 10}]
      },
      "failure_routing": {
        "implementation_bug": "coder",
        "spec_mismatch": "architect",
        "timeout": "tester"
      },
      "dependencies": [],
      "max_retries": 2,
      "priority": 1
    },
    {
      "id": "t2_indicators",
      "title": "Indicator & Candle Patterns",
      "agent_role": "architect",
      "acceptance_criteria": {
        "tests": [
          {
            "cmd": "pytest tests/test_indicators.py::test_rsi_values -q --json-report",
            "timeout_seconds": 20
          },
          {
            "cmd": "pytest tests/test_patterns.py::test_engulfing_detection -q --json-report",
            "timeout_seconds": 20
          }
        ],
        "expected_artifacts": [
          "contracts/indicator_contract.json",
          "indicators/rsi.py"
        ]
      },
      "failure_routing": {
        "implementation_bug": "coder",
        "spec_mismatch": "architect"
      },
      "dependencies": ["t1_data_integration"],
      "max_retries": 2,
      "priority": 2
    },
    {
      "id": "t3_entry_conditions",
      "title": "Entry Conditions",
      "agent_role": "coder",
      "acceptance_criteria": {
        "tests": [
          {
            "cmd": "pytest tests/test_entry.py::test_entry_true_false -q --json-report",
            "timeout_seconds": 20
          }
        ],
        "expected_artifacts": ["Backtest/codes/ai_strategy_entry.py"]
      },
      "failure_routing": {
        "implementation_bug": "coder"
      },
      "dependencies": ["t2_indicators"],
      "max_retries": 2,
      "priority": 3
    },
    {
      "id": "t4_exit_conditions",
      "title": "Exit Conditions",
      "agent_role": "coder",
      "acceptance_criteria": {
        "tests": [
          {
            "cmd": "pytest tests/test_exit.py::test_stop_loss -q --json-report",
            "timeout_seconds": 20
          }
        ],
        "expected_artifacts": ["Backtest/codes/ai_strategy_exit.py"]
      },
      "failure_routing": {
        "implementation_bug": "coder"
      },
      "dependencies": ["t3_entry_conditions"],
      "max_retries": 2,
      "priority": 4
    }
  ]
}
```

### If `t2_indicators` Fails:

**Orchestrator creates:**

```json
{
  "id": "t2_branch_01",
  "parent_id": "t2_indicators",
  "title": "Debug indicator failures (RSI mismatch)",
  "agent_role": "debugger",
  "branch_reason": "test_failure",
  "debug_instructions": "pytest failed: test_rsi_values\n\nAssertion Error:\nExpected RSI: 28.5\nActual RSI: 32.1\n\nSample input: fixtures/rsi_expected.json\nSuggestions:\n- Check SMA window calculation\n- Verify NaN handling at start\n- Confirm Wilder's smoothing formula",
  "acceptance_criteria": {
    "tests": [
      {
        "cmd": "pytest tests/test_indicators.py::test_rsi_values -q --json-report",
        "timeout_seconds": 20
      }
    ],
    "expected_artifacts": [
      "diagnostics/t2_indicators_failure_report.json"
    ]
  },
  "dependencies": [],
  "is_temporary": true,
  "max_debug_attempts": 3
}
```

---

## 🚦 Policy: Limits to Prevent Runaway Branches

### Configuration Defaults

```python
DEFAULT_BRANCH_POLICY = {
    "max_debug_attempts": 3,           # Retries per branch
    "max_branch_depth": 2,             # Max nested branches
    "auto_approve_branches": False,    # Require human approval
    "branch_timeout_seconds": 600,     # 10 minutes per branch
    "max_concurrent_branches": 5,      # Limit parallel debugging
    "notify_after_n_failures": 3       # Alert human after N failed branches
}
```

### Depth Limiting

```
Primary Todo (t2_indicators) [depth=0]
  └─ Branch 1 (t2_branch_01) [depth=1]
      └─ Branch 2 (t2_branch_02) [depth=2]
          └─ BLOCKED: max_branch_depth reached
              → Escalate to human
```

### Notification Triggers

| Condition | Action |
|-----------|--------|
| `branch_depth > max_branch_depth` | Block, notify Planner |
| `failed_branches > notify_after_n_failures` | Alert human reviewer |
| `branch_timeout exceeded` | Kill branch, escalate |
| `circular dependency in branches` | Block workflow, alert |

---

## 🧪 Testing Strategy for Branch Todos

### Unit Tests

```python
def test_orchestrator_creates_branch_on_failure():
    """Verify orchestrator creates branch todo when task fails."""
    task = create_sample_task()
    task_result = simulate_failure(task, error_type="implementation_bug")
    
    branch = orchestrator.handle_failure(task, task_result)
    
    assert branch.parent_id == task.id
    assert branch.agent_role == "coder"
    assert branch.is_temporary == True

def test_failure_routing_logic():
    """Test failure type detection and routing."""
    assert determine_failure_target({"error": "ImportError"}) == ("coder", "missing_dependency")
    assert determine_failure_target({"error": "AssertionError: signature"}) == ("architect", "spec_mismatch")
```

### Integration Tests

```python
def test_branch_lifecycle_success():
    """Branch resolves, parent tests pass, workflow continues."""
    workflow = create_test_workflow()
    orchestrator.execute(workflow)
    
    # Simulate t2 failure
    inject_failure("t2_indicators", "RSI mismatch")
    
    # Verify branch created
    assert orchestrator.has_branch("t2_indicators")
    
    # Simulate branch fix
    inject_success("t2_branch_01")
    
    # Verify parent re-run
    assert orchestrator.get_status("t2_indicators") == "completed"
    assert orchestrator.get_status("t3_entry_conditions") == "running"

def test_branch_blocks_downstream():
    """Failed task blocks dependent tasks until branch resolves."""
    workflow = create_test_workflow()
    orchestrator.execute(workflow)
    
    inject_failure("t2_indicators")
    
    assert orchestrator.get_status("t3_entry_conditions") == "blocked"
    assert orchestrator.get_status("t4_exit_conditions") == "blocked"
```

### End-to-End Tests

```python
def test_full_workflow_with_branch_recovery():
    """Complete workflow with failure, branch creation, and recovery."""
    user_request = "Create momentum strategy with RSI"
    
    # 1. Planner generates TodoList
    todo_list = planner.create_plan(user_request)
    
    # 2. Orchestrator executes
    workflow_id = orchestrator.load_todo_list(todo_list)
    
    # 3. Simulate indicator failure
    inject_failure(
        task_id="t2_indicators",
        error_type="implementation_bug",
        message="RSI calculation incorrect"
    )
    
    # 4. Verify branch created
    branches = orchestrator.get_branches(workflow_id)
    assert len(branches) == 1
    assert branches[0].agent_role == "coder"
    
    # 5. Simulate branch resolution
    inject_success(branches[0].id)
    
    # 6. Verify workflow completes
    result = orchestrator.wait_for_completion(workflow_id, timeout=300)
    assert result.status == "completed"
    assert all(task.status == "completed" for task in result.tasks)
```

---

## 📝 Planner Output Requirements

### Required Fields for Each Primary Step

```json
{
  "id": "t1_data_integration",
  "title": "Data Loading Integration",
  "agent_role": "coder",
  
  "acceptance_criteria": {
    "tests": [
      {
        "cmd": "pytest tests/test_adapter.py::test_fetch -q --json-report",
        "timeout_seconds": 30,
        "fixture": "fixtures/sample_aapl.csv"  // Optional
      }
    ],
    "expected_artifacts": ["Backtest/backtesting_adapter.py"],
    "metrics": [{"name": "rows_min", "operator": ">=", "value": 10}]
  },
  
  "failure_routing": {
    "implementation_bug": "coder",
    "spec_mismatch": "architect",
    "timeout": "tester"
  },
  
  "contract_path": "contracts/data_adapter_contract.json",  // Optional
  "max_retries": 2,
  "timeout_seconds": 300,
  "dependencies": []
}
```

### Planner Validation Checklist

Before outputting a TodoList, Planner must verify:

- [x] Every item has at least one `test_command`
- [x] Every `test_command` is deterministic (uses fixtures)
- [x] `failure_routing` is defined for common failure types
- [x] `timeout_seconds` is reasonable for task complexity
- [x] `max_retries` is set (default: 2)
- [x] Dependencies are acyclic
- [x] Primary steps follow the 4-step template
- [x] Contracts referenced exist or will be created by Architect

---

## 🔧 Implementation Checklist for Developers

### Immediate (This Week)

- [ ] **Update todo_schema.json**
  - Add `parent_id`, `branch_reason`, `is_temporary`, `max_debug_attempts`
  - Add `failure_routing` dict
  - Add `fixture` field to test specs

- [ ] **Update Planner**
  - Enforce 4 primary steps as default template
  - Generate `failure_routing` for each task
  - Validate `test_command` is deterministic
  - Add fixture generation hints

- [ ] **Update Orchestrator**
  - Implement `determine_failure_target()` logic
  - Add branch todo creation on failure
  - Block downstream tasks when branch active
  - Re-run parent tests after branch success
  - Enforce `max_branch_depth` and `max_debug_attempts`

### Short Term (Next 2 Weeks)

- [ ] **Add Debugger Agent**
  - Skeleton agent that handles branch todos
  - Collects logs, tracebacks, diagnostics
  - Runs quick fixes (common patterns)
  - Annotates failures for human review

- [ ] **Add Metrics & Monitoring**
  - Track `branch_count` per workflow
  - Measure `avg_branch_resolution_time`
  - Alert on `blocked_workflows`
  - Dashboard for branch lifecycle visualization

- [ ] **Create Deterministic Fixtures**
  - `fixtures/sample_aapl.csv` - Known OHLCV data
  - `fixtures/rsi_expected.json` - Expected RSI values
  - `fixtures/entry_scenarios.json` - Entry test cases
  - `fixtures/exit_scenarios.json` - Exit test cases

### Medium Term (3-4 Weeks)

- [ ] **Branch Todo Database Schema**
  - Store parent-child relationships
  - Track branch attempts and outcomes
  - Persist diagnostics and resolutions
  - Enable branch history queries

- [ ] **Human Approval UI**
  - Display failed task diagnostics
  - Show proposed branch todo
  - Allow approve/reject/modify decisions
  - Provide "auto-approve for similar" option

- [ ] **Advanced Routing Logic**
  - ML-based failure classification
  - Learning from past branch successes
  - Confidence scores for routing decisions

---

## 📚 References

- **Schema Definitions:** `contracts/todo_schema.json`
- **Orchestrator Logic:** `orchestrator_service/orchestrator.py`
- **Planner Templates:** `planner_service/templates/`
- **Test Fixtures:** `fixtures/`
- **Branch Todo Examples:** `contracts/sample_branch_todo.json`

---

## 🎓 Key Takeaways

1. **Default to 4 primary steps** for all strategy workflows
2. **Every step needs machine-executable tests** with fixtures
3. **Failures auto-create branch todos** routed to appropriate agents
4. **Limit branch depth** (default: 2) and attempts (default: 3)
5. **Notify humans early** for repeated failures
6. **Use deterministic fixtures** to eliminate flakiness
7. **Track branch metrics** for continuous improvement

---

**Status:** 🟢 Design Complete - Ready for Implementation  
**Next:** Update schemas, implement orchestrator branch logic, create fixtures
