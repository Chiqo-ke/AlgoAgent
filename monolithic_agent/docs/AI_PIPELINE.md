# AI Strategy Generation Pipeline

**Last Updated:** March 10, 2026
**See also:** [Architecture](architecture/ARCHITECTURE.md) | [API Endpoints](api/API_ENDPOINTS.md) | [Production API Guide](api/PRODUCTION_API_GUIDE.md)

---

## Overview

AlgoAgent uses a multi-stage AI pipeline to: (1) generate trading strategy Python code from a natural-language description, (2) execute and validate the code in an isolated environment, (3) iteratively fix errors, and (4) persist a verified strategy with backtest results.

The entire pipeline runs asynchronously as a **Celery task**. The API endpoint returns a `job_id` immediately and the client polls `GET /api/jobs/<task_id>/` for status.

---

## Entry Point

### Endpoint: `POST /api/strategies/generate_strategy_unified/`

| Field | Type | Description |
|-------|------|-------------|
| `description` | string | Natural-language strategy description |
| `symbols` | list | Tickers to backtest against |
| `timeframe` | string | e.g. "1d" |
| `period` | string | e.g. "1y" |
| `strategy_id` | int | (optional) Update an existing strategy instead of creating |

**Returns:**
```json
{ "job_id": "<celery_task_id>", "status": "queued" }
```

The client then polls `GET /api/jobs/<job_id>/` until `status` is `"SUCCESS"` or `"FAILURE"`.

---

## Pipeline: Step-by-Step

```
Client
  |
  | POST /api/strategies/generate_strategy_unified/
  v
generate_strategy_unified (view)
  |
  | .delay() — enqueues Celery task, returns job_id to client
  v
generate_strategy_task (Celery task)  [Backtest/celery_tasks.py]
  |
  +--[Step 1]---> GeminiStrategyGenerator.generate(description)
  |                   |-- Builds LangChain prompt with canonical schema docs
  |                   |-- Calls Gemini 2.0 Flash
  |                   |-- Returns Python source code string
  |
  +--[Step 2]---> BotExecutor.execute(code, symbols, timeframe, period)
  |                   |-- Writes code to temp file
  |                   |-- Spawns subprocess in .venv (isolated)
  |                   |-- 900 second timeout
  |                   |-- Captures stdout/stderr + metrics JSON
  |                   |-- Returns ExecutionResult dataclass
  |
  +--[Step 3]---> BotErrorFixer.fix(code, error)   [if Step 2 failed]
  |                   |-- Up to 8 fix attempts
  |                   |-- Each attempt: EnhancedErrorDetector -> LLM call -> BotExecutor
  |                   |-- Records ErrorFixAttempt dataclass per try
  |                   |-- CodeChangeLogger diffs each attempt
  |                   |-- Stops when execution succeeds or max attempts reached
  |
  +--[Step 4]---> canonical_schema_v2.validate(code)
  |                   |-- Checks Signal return, field types, enum compliance
  |                   |-- If invalid: back to BotErrorFixer
  |
  +--[Step 5]---> Save to database
                      |-- Creates/Updates Strategy record
                      |-- Creates LatestBacktestResult
                      |-- Creates BotPerformance entry
                      |-- Sets strategy.status = "valid" or "invalid"
```

---

## Core Modules

### `Backtest/gemini_strategy_generator.py` — GeminiStrategyGenerator

Wraps the Gemini API for code generation.

| Attribute | Value |
|-----------|-------|
| Model | `gemini-2.0-flash` (via LangChain `ChatGoogleGenerativeAI`) |
| Prompt style | System prompt with canonical schema docs + user description |
| Output | Raw Python source code (stripped of markdown fences) |

**Key methods:**

| Method | Description |
|--------|-------------|
| `generate(description)` | Produces strategy code from a description |
| `_build_system_prompt()` | Injects `canonical_schema_v2` reference + coding rules |
| `_extract_code(response)` | Strips ` ```python ` fences from LLM output |

---

### `Backtest/bot_executor.py` — BotExecutor

Runs a strategy code file safely in a subprocess.

| Attribute | Value |
|-----------|-------|
| Execution environment | `.venv` at `C:\Users\nyaga\Documents\.venv` |
| Timeout | 900 seconds (15 minutes) |
| Execution mode | `subprocess.run()` with `capture_output=True` |
| Metrics collection | Writes a JSON file to temp dir; executor reads it back |

**How isolation works:**
1. Strategy code is written to a temporary `.py` file
2. `BotExecutor` spawns `python temp_strategy.py` using the `.venv` interpreter
3. The strategy script imports `backtesting_adapter`, runs the backtest, writes metrics JSON to a known path
4. The executor reads metrics JSON and returns an `ExecutionResult` dataclass

**`ExecutionResult` fields:**

| Field | Type | Description |
|-------|------|-------------|
| `success` | bool | Whether execution completed without error |
| `stdout` | string | Captured stdout |
| `stderr` | string | Captured stderr (error details on failure) |
| `metrics` | dict | Backtest metrics JSON (when `success=True`) |
| `execution_time` | float | Wall-clock seconds |

---

### `Backtest/bot_error_fixer.py` — BotErrorFixer

Iterative auto-fixer that retries failed strategy execution.

| Attribute | Value |
|-----------|-------|
| Max attempts | 8 |
| Per-attempt record | `ErrorFixAttempt` dataclass |
| Error classifier | `EnhancedErrorDetector` |
| Change tracker | `CodeChangeLogger` |

**Fix loop:**

```
attempt = 1
while attempt <= 8:
    error_type = EnhancedErrorDetector.classify(stderr)
    |
    +-- "framework_error"  → fix import paths, API calls, backtesting.py usage
    +-- "bot_error"        → fix strategy logic, variable names, missing indicators
    +-- "encoding_error"   → strip non-ASCII characters
    +-- "filter_error"     → fix pandas/numpy filter expressions
    +-- "case_error"       → fix column name casing
    |
    fixed_code = AIDeveloperAgent.fix(original_code, error, error_type)
    result = BotExecutor.execute(fixed_code)
    |
    if result.success:
        return fixed_code, result
    attempt += 1

return original_code, failure_result   # after 8 attempts
```

**`ErrorFixAttempt` fields:**

| Field | Description |
|-------|-------------|
| `attempt_number` | 1–8 |
| `error_type` | Classified error category |
| `original_error` | Raw stderr from failed execution |
| `fixed_code` | Code after this fix attempt |
| `execution_result` | ExecutionResult from re-running |
| `code_diff` | Unified diff from CodeChangeLogger |

---

### `Backtest/ai_developer_agent.py` — AIDeveloperAgent

The LLM agent that writes and fixes strategy code.

| Attribute | Value |
|-----------|-------|
| LLM | Gemini 2.0 Flash via LangChain |
| Memory | `ChatMessageHistory` with sliding window (last 20 messages) |
| Router | `RequestRouter` classifies requests before dispatching |

**`RequestRouter` routes:**

| Route | Trigger pattern | Handler |
|-------|----------------|---------|
| `generate` | "Write a strategy...", "Create a bot..." | `generate_strategy()` |
| `fix` | "Fix error...", "The error is...", exception text | `fix_strategy()` |
| `modify` | "Change...", "Update...", "Adjust..." | `modify_strategy()` |
| `explain` | "What does...", "How does..." | `explain_strategy()` |
| `optimize` | "Optimize...", "Improve performance..." | `optimize_strategy()` |

**Reference cards injected into every prompt:**
- `canonical_schema_v2` field reference
- `backtesting_adapter` API docs
- Common error → fix mapping table
- Example valid strategy skeleton

---

### `Backtest/canonical_schema_v2.py` — Canonical Schema

Defines the required interface that every strategy must implement.

**Required return type: `Signal`**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action` | `OrderAction` | Yes | What to do |
| `side` | `OrderSide` | Yes | Direction |
| `order_type` | `OrderType` | Yes | Execution type |
| `size_type` | `SizeType` | Yes | How to size the position |
| `size` | float | Yes | Numeric size value |
| `price` | float | No | Limit price (required for LIMIT orders) |
| `stop_price` | float | No | Stop price |
| `notes` | string | No | Human-readable reason |

**Enums:**

| Enum | Values |
|------|--------|
| `OrderAction` | `BUY`, `SELL`, `HOLD` |
| `OrderSide` | `LONG`, `SHORT` |
| `OrderType` | `MARKET`, `LIMIT`, `STOP`, `STOP_LIMIT` |
| `SizeType` | `FIXED`, `PERCENT`, `RISK_BASED` |
| `OrderStatus` | `PENDING`, `FILLED`, `CANCELLED`, `REJECTED` |

**Required strategy function signature:**
```python
def generate_signal(data: pd.DataFrame, params: dict) -> Signal:
    ...
```

`canonical_schema_v2.validate(code)` checks:
- `generate_signal` function is defined
- Returns a `Signal` instance
- All required fields are set
- Enum values are valid members

---

### `Backtest/backtesting_adapter.py` — BacktestingAdapter

Bridges the canonical schema to the `backtesting.py` (kernc) library.

| Responsibility | Detail |
|----------------|--------|
| Data fetching | Downloads OHLCV via yfinance for given symbol/period/interval |
| Strategy wrapping | Wraps `generate_signal` into a `backtesting.Strategy` subclass |
| Order routing | Translates `Signal.action` / `Signal.order_type` into `backtesting.py` order calls |
| Metrics extraction | Pulls stats from `Backtest.run()` results dict into standard format |
| Output | Writes metrics JSON file for `BotExecutor` to read back |

---

### `Backtest/metrics_engine.py` — MetricsEngine

Post-processes raw `backtesting.py` stats into the reporting schema.

| Output metric | Source |
|---------------|--------|
| `total_return_pct` | `stats['Return [%]']` |
| `sharpe_ratio` | `stats['Sharpe Ratio']` |
| `max_drawdown` | `stats['Max. Drawdown [%]']` |
| `win_rate` | `stats['Win Rate [%]']` |
| `profit_factor` | `stats['Profit Factor']` |
| `total_trades` | `stats['# Trades']` |
| `equity_curve` | `stats['_equity_curve']` — sampled time series |

---

### `Backtest/sim_broker.py` — SimBroker

A lightweight simulated broker used in quick-validation runs (not full backtests).

| Feature | Detail |
|---------|--------|
| Order types | MARKET, LIMIT, STOP |
| Commission | Configurable percentage per trade |
| Slippage | Configurable tick offset |
| Use case | `sandbox-test` in the production API; fast `quick_run` endpoint |

---

## Job Status Tracking

All pipeline runs are tracked via Celery result backend (`django-db`).

Poll endpoint: `GET /api/jobs/<task_id>/`

| `status` | Meaning |
|----------|---------|
| `PENDING` | Task queued, not started yet |
| `STARTED` | Celery worker has picked up the task |
| `PROGRESS` | Task is in progress — `result` may include `progress` int and `message` |
| `SUCCESS` | Complete — `result` contains strategy data and backtest metrics |
| `FAILURE` | Task failed — `result.error` contains message |

**`SUCCESS` result shape:**

| Field | Description |
|-------|-------------|
| `strategy_id` | ID of the created/updated Strategy |
| `status` | "valid" or "invalid" (from schema validation) |
| `metrics` | Backtest metrics object |
| `fix_attempts` | Number of auto-fix iterations run (0 if code worked first time) |

---

## Error Outcomes

| Scenario | Result |
|----------|--------|
| Code generated, runs first try | `strategy.status = "valid"`, metrics saved |
| Code fails, fixed within 8 attempts | `strategy.status = "valid"`, metrics saved |
| Code still fails after 8 attempts | `strategy.status = "invalid"`, last error saved, no metrics |
| Schema validation fails | Back to `BotErrorFixer`; counted toward 8 attempts |
| Celery task crashed (unhandled exception) | `job.status = "FAILURE"`, strategy not created |

---

## File Locations

| Module | Path |
|--------|------|
| Celery task | `strategy_api/tasks.py` (or `Backtest/celery_tasks.py`) |
| GeminiStrategyGenerator | `Backtest/gemini_strategy_generator.py` |
| BotExecutor | `Backtest/bot_executor.py` |
| BotErrorFixer | `Backtest/bot_error_fixer.py` |
| EnhancedErrorDetector | `Backtest/bot_error_fixer.py` (inner class) |
| CodeChangeLogger | `Backtest/bot_error_fixer.py` (inner class) |
| AIDeveloperAgent | `Backtest/ai_developer_agent.py` |
| canonical_schema_v2 | `Backtest/canonical_schema_v2.py` |
| BacktestingAdapter | `Backtest/backtesting_adapter.py` |
| MetricsEngine | `Backtest/metrics_engine.py` |
| SimBroker | `Backtest/sim_broker.py` |
