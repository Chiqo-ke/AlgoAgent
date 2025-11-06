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

The Tester Agent MUST:

1. **Build sandbox** - Ensure Docker image is ready
2. **Run tests** - Execute pytest in isolated container
3. **Static checks** - Run mypy, flake8, bandit
4. **Determinism check** - Run backtest twice with same seed
5. **Validate schema** - Ensure test_report.json matches schema
6. **Collect artifacts** - Save all outputs to artifacts/
7. **Publish events** - Send TEST_PASSED/TEST_FAILED to message bus
8. **Create branch todos** - On failure, trigger Debugger agent

**Test execution:**
```bash
# Build
docker build -t algo-sandbox -f sandbox_runner/Dockerfile.sandbox .

# Test
docker run --rm --network=none --memory=1g --cpus=0.5 \
  -v $(pwd):/app -w /app algo-sandbox \
  bash -c "pytest tests/test_strategy.py --json-report --json-report-file=/app/artifacts/test_report.json && python -m tools.validate_test_report /app/artifacts/test_report.json"
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
