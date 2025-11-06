# Multi-Agent System Architecture
## Single-File Strategy + Adapter-Driven + Docker Sandbox

**Version:** 2.0  
**Date:** November 7, 2025  
**Status:** Production Specification for Coder and Tester Agents

---

## A — High-Level Architecture

```
Planner → TodoList (contract.json)
   ↓
Orchestrator dispatch → Coder Agent
   └─ produces: Backtest/codes/<strategy>.py (single-file)
         ├─ uses Adapter API (BaseAdapter)
         ├─ contains Strategy class + run_backtest/run_live helpers
   ↓
Tester Agent (Docker sandbox)
   ├─ retrieves strategy file
   ├─ installs deps inside container
   ├─ runs unit tests + static checks + integration backtest using SimBroker
   ├─ produces test_report.json + artifacts (trades.csv, equity_curve.csv)
   └─ publishes TEST_PASSED/TEST_FAILED events to message bus
   ↓ (pass)
Artifact Store (git branch ai/generated/<wf>/<task>) ← commit & tag
   ↓ (manual/auto approval)
Deployment → LiveAdapter (human approval required to run live)
```

### Key Principles

1. **Single-File Strategy** - Each strategy is one `.py` file usable for both backtest and live
2. **Adapter Pattern** - Business logic uses `BaseAdapter` interface, never direct broker imports
3. **Isolated Testing** - All tests run in Docker sandbox with network disabled
4. **Deterministic** - Strategies use RNG seeds for reproducible results
5. **Security-First** - Live mode requires manual approval, credentials from secrets manager

---

## B — Module Layout

```
AlgoAgent/
└─ multi_agent/
   ├─ planner_service/         # TodoList generation
   ├─ orchestrator_service/    # Workflow execution
   ├─ agents/
   │   ├─ coder_agent/         # Strategy code generation
   │   ├─ tester_agent/        # Docker sandbox testing
   │   └─ debugger_agent/      # Failure analysis
   ├─ simulator/
   │   ├─ simbroker.py        # Backtest broker
   │   └─ configs.yaml
   ├─ adapters/               ⭐ NEW - Universal broker interface
   │   ├─ base_adapter.py     # Protocol (interface definition)
   │   ├─ simbroker_adapter.py # SimBroker → BaseAdapter
   │   └─ live_adapter.py      # MT5/IBKR → BaseAdapter (manual use only)
   ├─ Backtest/
   │   └─ codes/              # Generated strategy files
   ├─ tests/
   │   └─ fixtures/           # CSV fixtures for testing
   ├─ sandbox_runner/         ⭐ NEW - Docker test execution
   │   ├─ Dockerfile.sandbox
   │   └─ run_in_sandbox.py
   ├─ artifacts/              # Test outputs
   └─ ci/                     # Pipeline definitions
```

---

## C — BaseAdapter Interface (Exact API)

**File:** `adapters/base_adapter.py`

All broker interactions go through this interface. Coder Agent must generate code using ONLY this API.

```python
from typing import Dict, List, Protocol
import pandas as pd

class BaseAdapter(Protocol):
    """Universal broker adapter - implemented by SimBroker, MT5, IBKR."""
    
    def place_order(self, order_request: Dict) -> Dict:
        """
        Place order.
        
        Args:
            order_request: {
                'action': 'BUY' | 'SELL',
                'symbol': str,
                'volume': float,
                'type': 'MARKET' | 'LIMIT',
                'price': float (optional),
                'sl': float (optional),
                'tp': float (optional),
                'comment': str (optional)
            }
        
        Returns:
            {
                'success': bool,
                'order_id': str,
                'position_id': str,
                'fill_price': float,
                'error': str (if failed)
            }
        """
        ...
    
    def cancel_order(self, order_id: str) -> bool: ...
    
    def close_position(self, pos_id: str, price: float = None) -> Dict: ...
    
    def step_bar(self, bar: pd.Series) -> List[Dict]:
        """
        Process one bar (backtest only).
        
        Returns events: position_opened, position_closed, sl_hit, tp_hit
        """
        ...
    
    def get_positions(self) -> List[Dict]: ...
    
    def get_account(self) -> Dict: ...
    
    def generate_report(self) -> Dict: ...
    
    def save_report(self, out_dir: str) -> Dict[str, str]: ...
```

**Implementations:**

1. **SimBrokerAdapter** - Wraps `SimBroker` for backtesting
2. **LiveAdapter** - Wraps MT5/IBKR for live trading (requires manual approval)

---

## D — Single-File Strategy Template

**File:** `Backtest/codes/strategy_template_adapter_driven.py`

Coder Agent must generate strategies following this exact structure:

```python
from typing import Dict, List, Optional
import pandas as pd
from adapters.base_adapter import BaseAdapter

class Strategy:
    """Strategy implementation - works for backtest AND live."""
    
    def __init__(self, cfg: Dict):
        """Initialize with config."""
        self.cfg = cfg
    
    def prepare_indicators(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Compute indicators ONCE (vectorized).
        
        Returns: {'rsi': pd.Series, 'sma': pd.Series, ...}
        """
        # Calculate all indicators before main loop
        # Example: RSI, SMA, MACD, etc.
        raise NotImplementedError
    
    def find_entries(
        self,
        df: pd.DataFrame,
        indicators: Dict[str, pd.Series],
        idx: int
    ) -> Optional[Dict]:
        """
        Check for entry signal at current bar.
        
        CRITICAL: Do NOT call adapter.place_order() here.
        Return order_request dict or None.
        
        Returns: {
            'action': 'BUY',
            'symbol': 'AAPL',
            'volume': 1.0,
            'type': 'MARKET',
            'sl': 145.0,
            'tp': 155.0,
            'comment': 'RSI oversold'
        }
        """
        raise NotImplementedError
    
    def find_exits(
        self,
        position: Dict,
        df: pd.DataFrame,
        indicators: Dict[str, pd.Series],
        idx: int
    ) -> Optional[Dict]:
        """
        Check for exit signal (beyond SL/TP).
        
        Returns: {'position_id': str, 'reason': str}
        """
        return None  # Optional

def run_backtest(adapter: BaseAdapter, df: pd.DataFrame, cfg: Dict) -> Dict:
    """Run backtest using adapter."""
    strategy = Strategy(cfg)
    indicators = strategy.prepare_indicators(df)
    
    for idx in range(len(df)):
        bar = df.iloc[idx]
        
        # Check entries
        order_request = strategy.find_entries(df, indicators, idx)
        if order_request:
            adapter.place_order(order_request)
        
        # Step bar
        events = adapter.step_bar(bar)
        
        # Check exits
        for position in adapter.get_positions():
            exit_request = strategy.find_exits(position, df, indicators, idx)
            if exit_request:
                adapter.close_position(exit_request['position_id'])
    
    return adapter.generate_report()

def run_live(adapter: BaseAdapter, cfg: Dict):
    """Run live (requires manual approval)."""
    raise NotImplementedError("Live trading requires manual approval")
```

**CLI Usage:**

```bash
# Backtest
python strategy.py --mode backtest --data data.csv --out results/

# Live (requires approval token)
python strategy.py --mode live --approval-token human_verified_<timestamp>
```

---

## E — Docker Sandbox Workflow

### Sandbox Image

**File:** `sandbox_runner/Dockerfile.sandbox`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt pytest mypy flake8 bandit
RUN useradd -m runner && chown -R runner /app
USER runner
ENTRYPOINT ["python", "-u"]
```

### Tester Agent Steps

1. **Build image** (once):
   ```bash
   docker build -t algo-sandbox -f sandbox_runner/Dockerfile.sandbox .
   ```

2. **Run tests** (network disabled, resource limited):
   ```bash
   docker run --rm \
     --network=none \
     --memory=1g \
     --cpus=0.5 \
     -v $(pwd):/app \
     -w /app \
     algo-sandbox \
     python -m pytest tests/test_strategy.py \
       --json-report \
       --json-report-file=/app/artifacts/test_report.json
   ```

3. **Validate results**:
   - Check `test_report.json` against schema
   - Verify exit code == 0
   - Collect artifacts (trades.csv, equity_curve.csv)
   - Run determinism check (same seed → same results)

4. **Publish events**:
   - `TEST_PASSED` → Orchestrator proceeds to artifact store
   - `TEST_FAILED` → Debugger creates branch todo

---

## F — Test Requirements Per Todo Milestone

### Todo 1: Data Loading Integration

**Unit Test:**
```python
def test_data_load():
    df = pd.read_csv('fixtures/sample_aapl.csv')
    assert 'Close' in df.columns
    assert not df['Close'].isna().any()
```

**Integration Test:**
```python
def test_adapter_with_real_data():
    adapter = SimBrokerAdapter(SimBroker())
    df = pd.read_csv('fixtures/sample_aapl.csv')
    # Verify data flows through adapter correctly
```

### Todo 2: Indicators

**Unit Test:**
```python
def test_indicators():
    strategy = Strategy(cfg)
    df = pd.read_csv('fixtures/sample_aapl.csv')
    indicators = strategy.prepare_indicators(df)
    
    # Compare with fixture expected values
    expected_rsi = pd.read_json('fixtures/RSI_expected.json')
    pd.testing.assert_series_equal(
        indicators['rsi'],
        expected_rsi['rsi'],
        atol=0.01
    )
```

### Todo 3: Entry Logic

**Unit Test:**
```python
def test_find_entries():
    strategy = Strategy(cfg)
    df, indicators = load_entry_scenario_fixture()
    
    # Test bar where entry expected
    order_request = strategy.find_entries(df, indicators, idx=15)
    
    assert order_request is not None
    assert order_request['action'] == 'BUY'
    assert order_request['sl'] < order_request['tp']
```

**Determinism Test:**
```python
def test_determinism():
    # Run backtest twice with same seed
    report1 = run_backtest(adapter1, df, cfg)
    report2 = run_backtest(adapter2, df, cfg)
    
    assert report1['total_pnl'] == report2['total_pnl']
    assert report1['total_trades'] == report2['total_trades']
```

### Todo 4: Exit Logic

**Unit Test:**
```python
def test_exits():
    strategy = Strategy(cfg)
    position = {'position_id': 'pos_123', 'action': 'BUY', ...}
    df, indicators = load_exit_scenario_fixture()
    
    exit_request = strategy.find_exits(position, df, indicators, idx=20)
    
    assert exit_request is not None
    assert exit_request['position_id'] == 'pos_123'
```

**Integration Test:**
```python
def test_full_backtest():
    adapter = SimBrokerAdapter(SimBroker())
    df = pd.read_csv('fixtures/sample_aapl.csv')
    
    report = run_backtest(adapter, df, cfg)
    
    assert report['total_trades'] > 0
    assert 'win_rate' in report
    assert 'max_drawdown' in report
```

---

## G — CI/CD Gating Rules

### Pre-Commit (Local)

- ✅ Lint (flake8)
- ✅ Unit tests

### Tester Agent Sandbox (Mandatory)

- ✅ pytest exit code 0
- ✅ mypy --strict (no errors)
- ✅ flake8 (max-line-length=100)
- ✅ bandit (security checks)
- ✅ Determinism check (run twice, compare)
- ✅ test_report.json validates against schema

### Artifact Commit (On TEST_PASSED)

1. Create git branch: `ai/generated/<workflow_id>/<task_id>`
2. Commit files:
   - `strategy.py`
   - `test_report.json`
   - `trades.csv`
   - `equity_curve.csv`
   - `events.log`
3. Tag with: `correlation_id`, `prompt_hash`
4. Push to remote

### Live Deployment (Manual Gate)

- ⚠️ **Human approval required**
- ⚠️ Approval recorded in `approvals` channel
- ⚠️ Credentials from secrets manager (never in code)
- ⚠️ Dry-run mode available for testing

---

## H — Artifacts & Observability

### Required Artifacts

Every test run must produce:

| Artifact | Description | Validation |
|----------|-------------|------------|
| `test_report.json` | pytest JSON report | Schema validation |
| `trades.csv` | All trade records | Non-empty if trades occurred |
| `equity_curve.csv` | Balance over time | Monotonic timestamps |
| `events.log` | Structured event log | JSON lines format |
| `summary.json` | Performance metrics | Contains win_rate, max_drawdown |

### Logging Rules

- Use structured JSON logs (one event per line)
- Include correlation_id in all logs
- NO secrets in logs (API keys, credentials)
- Timestamps in ISO 8601 format

**Example log entry:**
```json
{
  "timestamp": "2025-11-07T14:30:00Z",
  "correlation_id": "corr_abc123",
  "event": "position_opened",
  "position_id": "pos_456",
  "symbol": "AAPL",
  "action": "BUY",
  "price": 150.50
}
```

---

## I — Security & Safety

### Sandbox Security

- ✅ Network isolation: `--network=none`
- ✅ Memory limit: `--memory=1g`
- ✅ CPU limit: `--cpus=0.5`
- ✅ Non-root user: `USER runner`
- ✅ Timeout enforcement: 300s default

### Live Trading Safety

- ⚠️ **Manual approval required** (`--approval-token human_verified_<timestamp>`)
- ⚠️ **Credentials** stored in secrets manager (AWS Secrets Manager, HashiCorp Vault)
- ⚠️ **Never in CI/CD** - live adapter cannot run in automated pipelines
- ⚠️ **Dry-run mode** available for testing live logic without real trades
- ⚠️ **Audit trail** - all live actions logged with timestamps and approvals

### Code Security

- Run `bandit` on all generated code before commit
- Scan for hardcoded secrets
- Validate all file paths (prevent directory traversal)
- Sanitize user inputs

---

## J — Coder Agent Requirements

The Coder Agent MUST:

1. **Use adapter pattern** - All broker calls via `BaseAdapter`
2. **Follow template** - Use exact structure from `strategy_template_adapter_driven.py`
3. **Deterministic** - Use RNG seeds for reproducible results
4. **Documented** - Include docstrings for all methods
5. **Configurable** - Support config dict for parameters
6. **Testable** - Generate unit tests for each todo milestone
7. **Self-contained** - Single file with no external dependencies beyond adapters

**Generated files:**
- `Backtest/codes/<strategy_name>.py` - Strategy implementation
- `tests/test_<strategy_name>.py` - Unit and integration tests

---

## K — Tester Agent Requirements

### K.1 — Responsibilities

The Tester Agent MUST:

1. **Listen for tasks** - Subscribe to `Channels.AGENT_REQUESTS` for `agent_role: tester`
2. **Pull artifacts** - Retrieve generated strategy file + tests + fixtures from workspace
3. **Build sandbox** - Ensure Docker image `algo-sandbox` is available
4. **Run tests in isolation**:
   - Unit tests (pytest)
   - Integration backtest (SimBroker via adapter)
   - Static checks: mypy --strict, flake8, bandit
   - Determinism check (run backtest twice with same seed)
   - Validate test_report.json against schema
5. **Collect artifacts** - Save test_report.json, trades.csv, equity_curve.csv, events.log, summary.json
6. **Publish events** - TEST_PASSED (with metrics) or TEST_FAILED (with failures)
7. **Create branch todos** - On failure, publish to Debugger with minimal repro
8. **Enforce security** - Network disabled, resource limits, timeouts
9. **Report metrics** - Duration, trade count, win rate, drawdown to orchestrator

### K.2 — Message Bus Events

**Incoming (AGENT_REQUESTS):**
```json
{
  "event_type": "task.dispatched",
  "correlation_id": "corr_abc123",
  "workflow_id": "wf_456",
  "task_id": "task_tester_001",
  "task": {
    "agent_role": "tester",
    "artifact_path": "Backtest/codes/rsi_strategy.py",
    "tests": ["tests/test_rsi_strategy.py"],
    "fixtures": ["tests/fixtures/bar_simple_long.csv"],
    "timeout_seconds": 300,
    "rng_seed": 42
  },
  "source": "orchestrator"
}
```

**Outgoing (TEST_RESULTS):**

**TEST_STARTED:**
```json
{
  "event_type": "test.started",
  "correlation_id": "corr_abc123",
  "task_id": "task_tester_001",
  "source": "tester"
}
```

**TEST_PASSED:**
```json
{
  "event_type": "test.passed",
  "correlation_id": "corr_abc123",
  "workflow_id": "wf_456",
  "task_id": "task_tester_001",
  "metrics": {
    "total_trades": 12,
    "net_pnl": 120.5,
    "win_rate": 0.58,
    "max_drawdown": 45.2
  },
  "artifacts": {
    "test_report": "artifacts/corr_abc123/task_tester_001/test_report.json",
    "trades": "artifacts/corr_abc123/task_tester_001/trades.csv",
    "equity_curve": "artifacts/corr_abc123/task_tester_001/equity_curve.csv",
    "events_log": "artifacts/corr_abc123/task_tester_001/events.log"
  },
  "duration_seconds": 34.2,
  "source": "tester"
}
```

**TEST_FAILED:**
```json
{
  "event_type": "test.failed",
  "correlation_id": "corr_abc123",
  "workflow_id": "wf_456",
  "task_id": "task_tester_001",
  "failures": [
    {
      "check": "pytest",
      "test_name": "test_find_entries",
      "message": "AssertionError: order_request was None",
      "trace": "tests/test_rsi_strategy.py:42..."
    },
    {
      "check": "determinism",
      "message": "PnL mismatch: run1=120.5, run2=118.3"
    }
  ],
  "artifacts": {
    "logs": "artifacts/corr_abc123/task_tester_001/events.log",
    "traceback": "artifacts/corr_abc123/task_tester_001/traceback.txt"
  },
  "source": "tester"
}
```

**BRANCH_TODO_REQUEST (to DEBUGGER_REQUESTS):**
```json
{
  "event_type": "workflow.branch_created",
  "correlation_id": "corr_abc123",
  "workflow_id": "wf_456",
  "origin_task": "task_tester_001",
  "branch_todo": {
    "title": "Debug failing tests: test_rsi_strategy.py",
    "description": "pytest failed on test_find_entries with fixture bar_simple_long.csv. RSI calculation may be incorrect.",
    "attachments": [
      "artifacts/traceback.txt",
      "tests/fixtures/bar_simple_long.csv"
    ],
    "target_agent": "debugger",
    "failure_classification": "test_failures",
    "reproduce_command": "docker run --rm -v $(pwd):/app algo-sandbox pytest tests/test_rsi_strategy.py::test_find_entries"
  },
  "source": "tester"
}
```

### K.3 — Module Layout

```
agents/tester_agent/
├── tester.py              # Main agent daemon (subscribes to message bus)
├── sandbox_client.py      # Docker wrapper to call run_in_sandbox.py
├── test_runner.py         # Local logic: pytest/mypy/flake8/determinism
├── validators.py          # test_report.json schema validator
├── config.py              # Timeouts, resource limits, security settings
└── __init__.py
```

**Shared infrastructure:**
```
sandbox_runner/
├── Dockerfile.sandbox     # Python 3.11 + pytest/mypy/flake8/bandit
├── run_in_sandbox.py      # Helper script for test execution
└── requirements.txt       # Sandbox dependencies

tools/
├── validate_test_report.py   # JSON schema validation
├── check_determinism.py      # Run backtest twice and compare
└── secret_scanner.py         # Scan for hardcoded secrets (optional)
```

### K.4 — Runtime Algorithm

**Core flow (pseudocode):**

```python
class TesterAgent:
    def __init__(self):
        self.bus = get_message_bus()
        self.bus.subscribe(Channels.AGENT_REQUESTS, self.handle_task)
    
    def handle_task(self, event):
        task = event.data.get('task', event.data)
        if task.get('agent_role') != 'tester':
            return
        
        corr_id = event.correlation_id
        wf_id = event.workflow_id
        task_id = event.task_id
        
        # 1. Publish TEST_STARTED
        self.publish_test_started(corr_id, wf_id, task_id)
        
        # 2. Prepare workspace
        workspace = Path('artifacts') / corr_id / task_id
        workspace.mkdir(parents=True, exist_ok=True)
        
        # 3. Build sandbox parameters
        sandbox_params = {
            "strategy": task['task']['artifact_path'],
            "tests": task['task'].get('tests', []),
            "fixtures": task['task'].get('fixtures', []),
            "out_dir": str(workspace),
            "timeout": task['task'].get('timeout_seconds', 300),
            "seed": task['task'].get('rng_seed', 42)
        }
        
        # 4. Run tests in Docker sandbox
        try:
            result = run_tests_in_sandbox(sandbox_params)
        except Exception as e:
            self.publish_test_failed(corr_id, wf_id, task_id, 
                [{"check": "sandbox", "message": str(e)}], workspace)
            self.request_debug_branch(corr_id, wf_id, task_id, 
                workspace, "sandbox_error", str(e))
            return
        
        # 5. Check exit code
        if result['exit_code'] != 0:
            self.publish_test_failed(corr_id, wf_id, task_id, 
                result.get('failures', []), workspace)
            self.request_debug_branch(corr_id, wf_id, task_id, 
                workspace, "test_failures", result['failures'])
            return
        
        # 6. Validate test_report.json schema
        report_path = Path(result['artifacts']['test_report'])
        try:
            validate_test_report_schema(report_path)
        except Exception as e:
            self.publish_test_failed(corr_id, wf_id, task_id,
                [{"check": "report_schema", "message": str(e)}], workspace)
            self.request_debug_branch(corr_id, wf_id, task_id,
                workspace, "schema_invalid", str(e))
            return
        
        # 7. Determinism check
        det_ok, det_info = self.run_determinism_check(sandbox_params, workspace)
        if not det_ok:
            self.publish_test_failed(corr_id, wf_id, task_id,
                [{"check": "determinism", "message": det_info}], workspace)
            self.request_debug_branch(corr_id, wf_id, task_id,
                workspace, "non_deterministic", det_info)
            return
        
        # 8. Success: publish TEST_PASSED
        metrics = self.extract_metrics(report_path)
        self.publish_test_passed(corr_id, wf_id, task_id, 
            metrics, result['artifacts'], result['duration_seconds'])
    
    def run_determinism_check(self, params, workspace):
        """Run backtest twice with same seed and compare."""
        # Implementation: run_tests_in_sandbox() twice, compare:
        # - total_net_pnl (exact match or tolerance)
        # - total_trades (exact match)
        # - equity_curve hash or row-by-row comparison
        pass
    
    def extract_metrics(self, report_path):
        """Parse test_report.json and extract key metrics."""
        with open(report_path) as f:
            report = json.load(f)
        return {
            "total_trades": report.get('summary', {}).get('total_trades', 0),
            "net_pnl": report.get('summary', {}).get('net_pnl', 0),
            "win_rate": report.get('summary', {}).get('win_rate', 0),
            "max_drawdown": report.get('summary', {}).get('max_drawdown', 0)
        }
```

### K.5 — Sandbox Execution (run_tests_in_sandbox)

**Contract for `sandbox_client.run_tests_in_sandbox(params)`:**

**Input:**
```python
{
    "strategy": "Backtest/codes/rsi_strategy.py",
    "tests": ["tests/test_rsi_strategy.py"],
    "fixtures": ["tests/fixtures/bar_simple_long.csv"],
    "out_dir": "artifacts/corr_abc123/task_tester_001",
    "timeout": 300,
    "seed": 42
}
```

**Actions:**
1. Build or reuse `algo-sandbox` Docker image
2. Run container with:
   - `--network=none` (network isolation)
   - `--memory=1g` (memory limit)
   - `--cpus=0.5` (CPU limit)
   - `-v $(pwd):/app` (mount workspace)
   - Timeout enforcement (kill after `timeout` seconds)
3. Execute inside container:
   ```bash
   # Unit tests
   pytest {tests} --json-report --json-report-file={out_dir}/test_report.json
   
   # Static checks
   mypy --strict {strategy}
   flake8 {strategy}
   bandit -r {strategy}
   
   # Determinism check
   python tools/check_determinism.py --strategy {strategy} \
     --data {fixtures[0]} --runs 2 --seed {seed}
   ```

**Output:**
```python
{
    "exit_code": 0,
    "duration_seconds": 34.2,
    "artifacts": {
        "test_report": "artifacts/.../test_report.json",
        "trades": "artifacts/.../trades.csv",
        "equity_curve": "artifacts/.../equity_curve.csv",
        "events_log": "artifacts/.../events.log"
    },
    "failures": []  # List of failure dicts if exit_code != 0
}
```

**Docker command example:**
```bash
docker run --rm --network=none --memory=1g --cpus=0.5 \
  -v $(pwd):/app -w /app algo-sandbox \
  bash -lc "pytest tests/test_rsi_strategy.py --json-report \
    --json-report-file=/app/artifacts/test_report.json && \
    mypy --strict Backtest/codes/rsi_strategy.py && \
    flake8 Backtest/codes/rsi_strategy.py"
```

### K.6 — Determinism Check Implementation

**Tool:** `tools/check_determinism.py`

**Purpose:** Run backtest twice with same seed and verify identical results

**Algorithm:**
1. Load strategy and fixtures
2. Run backtest #1 with seed=42 → save report1.json
3. Run backtest #2 with seed=42 → save report2.json
4. Compare critical metrics:
   - `total_net_pnl` (tolerance: 0.01)
   - `total_trades` (exact match)
   - `equity_curve` (row-by-row comparison or hash)
   - `trade_sequence` (order IDs, timestamps)
5. Return success/failure + diff details

**Usage:**
```bash
python tools/check_determinism.py \
  --strategy Backtest/codes/rsi_strategy.py \
  --data tests/fixtures/bar_simple_long.csv \
  --runs 2 \
  --seed 42 \
  --out artifacts/det_check.json
```

**Output (det_check.json):**
```json
{
  "deterministic": true,
  "run1_pnl": 120.50,
  "run2_pnl": 120.50,
  "run1_trades": 12,
  "run2_trades": 12,
  "differences": []
}
```

### K.7 — Failure Classification & Branch Todo Rules

**Failure categories:**
- `test_failures` - pytest failing tests (include trace)
- `static_failures` - mypy/flake8 errors
- `non_deterministic` - determinism mismatch
- `sandbox_error` - Docker/build/runtime errors
- `artifact_schema` - Invalid test_report.json

**For each failure, Tester MUST:**
1. Classify failure type
2. Extract minimal repro (failing test + fixture)
3. Publish `workflow.branch_created` to `DEBUGGER_REQUESTS` with:
   - Failing test names + traceback
   - Minimal fixture (e.g., bar_simple_long.csv)
   - Exact reproduce command (Docker command)
   - Correlation ID + task ID
4. Include suggested fix (if obvious, e.g., "Check RSI calculation")

### K.8 — Security & Resource Policies

**Enforced by Tester:**
- ✅ Network isolation: `--network=none` (no external API calls)
- ✅ Memory limit: `--memory=1g`
- ✅ CPU limit: `--cpus=0.5`
- ✅ Timeout: Kill container after `timeout_seconds` (default 300s)
- ✅ Non-root user: Container runs as `USER runner`
- ✅ Ephemeral containers: `docker run --rm` (no state preserved)
- ✅ Secret scanning: Check artifacts/events.log for API keys (regex patterns)
- ✅ Pre-built image: No network install during test run (dependencies pre-installed)

**Image build (one-time):**
```bash
docker build -t algo-sandbox -f sandbox_runner/Dockerfile.sandbox .
```

### K.9 — Success Criteria (TEST_PASSED)

All conditions MUST be met:
- ✅ pytest exit code = 0 (all tests pass)
- ✅ test_report.json exists and validates against schema
- ✅ mypy --strict exit code = 0 (type checking)
- ✅ flake8 exit code = 0 (style)
- ✅ bandit exit code = 0 (security, or warnings only)
- ✅ Determinism check passes (PnL/trades match exactly or within tolerance)
- ✅ Required artifacts present: trades.csv, equity_curve.csv, events.log, summary.json
- ✅ Artifacts non-empty: trades.csv has expected columns (time, symbol, action, pnl)
- ✅ No secrets detected in logs (API keys, tokens)
- ✅ Correlation ID present in all log entries

**If any check fails:** Publish TEST_FAILED with failure details

### K.10 — Integration with Orchestrator/Debugger/Artifact Store

**Orchestrator:**
- Waits for `test.passed` on `Channels.TEST_RESULTS` before artifact commit
- Validates correlation_id matches dispatched task
- Proceeds to artifact store commit on success
- Triggers rollback on `test.failed` if in production pipeline

**Debugger:**
- Subscribes to `Channels.DEBUGGER_REQUESTS`
- Receives `workflow.branch_created` with failure details
- Analyzes failure and creates branch todo for Coder/Architect
- Routes based on `failure_classification`

**Artifact Store:**
- Receives artifact paths from `test.passed` event
- Creates git branch: `ai/generated/<workflow_id>/<task_id>`
- Commits: strategy.py, test_report.json, trades.csv, equity_curve.csv, events.log
- Tags commit with `correlation_id`, `prompt_hash`, `agent_version`
- Pushes to remote for review/deployment

### K.11 — Example Commands (Manual Testing)

**Build sandbox image:**
```bash
docker build -t algo-sandbox -f sandbox_runner/Dockerfile.sandbox .
```

**Run tests manually:**
```bash
docker run --rm --network=none --memory=1g --cpus=0.5 \
  -v $(pwd):/app -w /app algo-sandbox \
  bash -lc "pytest tests/test_rsi_strategy.py --json-report \
    --json-report-file=artifacts/test_report.json"
```

**Run determinism check:**
```bash
python tools/check_determinism.py \
  --strategy Backtest/codes/rsi_strategy.py \
  --data tests/fixtures/bar_simple_long.csv \
  --runs 2 --seed 42 --out artifacts/det_check.json
```

**Validate test report schema:**
```bash
python tools/validate_test_report.py artifacts/test_report.json
```

**Run Tester Agent locally:**
```bash
python -m agents.tester_agent.tester
# (subscribes to message bus, processes tester tasks)
```

---

## L — Orchestrator Requirements

The Orchestrator MUST:

1. **Dispatch tasks** - Send coder tasks with contract
2. **Wait for tests** - Block on TEST_PASSED event
3. **Commit artifacts** - Only after tests pass
4. **Enforce gates** - No live deployment without approval
5. **Track correlation IDs** - All events must include correlation_id
6. **Handle failures** - Create branch todos via Debugger on TEST_FAILED
7. **Rollback support** - Revert to previous artifact if live issues occur

---

## M — Example Commands

### For Coder Agent (Manual Testing)

```bash
# Generate strategy
python -m agents.coder_agent.coder \
  --contract contracts/rsi_strategy.json \
  --output Backtest/codes/rsi_strategy.py

# Test locally (before sandbox)
python Backtest/codes/rsi_strategy.py \
  --mode backtest \
  --data fixtures/sample_aapl.csv \
  --out results/
```

### For Tester Agent (Automated)

```bash
# Build sandbox
docker build -t algo-sandbox -f sandbox_runner/Dockerfile.sandbox .

# Run tests
python sandbox_runner/run_in_sandbox.py \
  --strategy Backtest/codes/rsi_strategy.py \
  --tests tests/test_rsi_strategy.py \
  --timeout 300

# Validate report
python tools/validate_test_report.py artifacts/test_report.json
```

### For Orchestrator (Production)

```bash
# Execute workflow
python -m orchestrator_service.orchestrator \
  contracts/workflow_rsi_strategy.json

# Monitor events
python tools/monitor_message_bus.py --channel task.events
```

---

## N — Success Criteria

A strategy is **ready for artifact commit** when:

- ✅ All unit tests pass (pytest exit code 0)
- ✅ All static checks pass (mypy, flake8, bandit)
- ✅ Determinism verified (same seed → same results)
- ✅ test_report.json validates against schema
- ✅ Required artifacts present (trades.csv, equity_curve.csv, events.log)
- ✅ No hardcoded secrets detected
- ✅ Correlation ID present in all logs

A strategy is **ready for live deployment** when:

- ✅ All above criteria met
- ✅ Human approval granted (`--approval-token` provided)
- ✅ Credentials loaded from secrets manager
- ✅ Dry-run mode tested successfully
- ✅ Audit trail established

---

## O — Rollback Procedure

If live deployment encounters issues:

1. **Stop live trading** - Human intervention required
2. **Create incident report** - Log failure details
3. **Revert to previous artifact** - Orchestrator checks out previous git tag
4. **Create branch todo** - Debugger analyzes failure
5. **Re-test fix** - New coder task with failure context
6. **Re-deploy after approval** - Requires new approval token

---

## P — Questions & Troubleshooting

### Q: Strategy not generating trades?

- Check indicator values (print in test)
- Verify entry/exit conditions match contract
- Ensure sufficient lookback period

### Q: Determinism check failing?

- Verify RNG seed is set
- Check for timestamp-dependent logic
- Ensure no external network calls

### Q: Sandbox build failing?

- Check `requirements.txt` has all dependencies
- Verify Docker has enough disk space
- Ensure base image (python:3.11-slim) is accessible

### Q: Live mode not working?

- Verify approval token format: `human_verified_<timestamp>`
- Check credentials in secrets manager
- Ensure dry-run mode tested first
- Confirm network connectivity (live mode needs network)

---

**END OF ARCHITECTURE SPECIFICATION**

Use this document as the authoritative source for all Coder and Tester agent implementations.
