# Production API Guide

**Last Updated:** March 10, 2026
**See also:** [API Endpoints](API_ENDPOINTS.md) | [Architecture](../architecture/ARCHITECTURE.md) | [AI Pipeline](../AI_PIPELINE.md)

---

## Overview

The Production API at `/api/production/` wraps standard strategy and backtest operations with six additional safety layers before any code is deployed or executed. Use these endpoints when you need:

- Verified safety of AI-generated code before running in production
- Full audit trail of all generation and validation attempts
- Git-tracked versioning of deployed strategies
- Rollback capability after a bad deploy

**Standard endpoints** (`/api/strategies/`, `/api/backtests/`) do basic CRUD and run the AI generation loop.
**Production endpoints** (`/api/production/`) apply validation → sandboxing → lifecycle tracking → git deployment on top of that.

---

## Production Components

```
Incoming request (strategy_code)
          |
          v
  1. Canonical Schema v2   ← Pydantic validation of signal structure
          |
          v
  2. Output Validator      ← Static code safety checks (no exec, eval, subprocess, etc.)
          |
          v
  3. Sandbox Orchestrator  ← Run in isolated process with resource limits
          |
          v
  4. State Manager         ← Log each step to the lifecycle audit trail in DB
          |
          v
  5. Safe Tools            ← File operations use sandboxed paths only
          |
          v
  6. Git Patch Manager     ← On deploy: git commit + tag the strategy code
```

| Component | Module | Purpose |
|-----------|--------|---------|
| Canonical Schema v2 | `Backtest/canonical_schema_v2.py` | Pydantic models: `Signal`, `OrderSide`, `OrderType`, `OrderAction`, `SizeType` |
| Output Validator | `strategy_api/production_views.py` | Detects: `exec`, `eval`, `subprocess`, `os.system`, raw network calls, file writes outside sandbox |
| Sandbox Orchestrator | `strategy_api/production_views.py` | Isolated subprocess with CPU/memory/time limits |
| State Manager | `strategy_api/production_views.py` | Records every state transition to DB (`lifecycle` action) |
| Safe Tools | `strategy_api/production_views.py` | Restricts file access to permitted sandbox directories |
| Git Patch Manager | `strategy_api/production_views.py` | `git commit` + `git tag` on deploy; `git checkout` on rollback |

---

## Typical Production Workflow

```
Developer has a new strategy ready
              |
              v
Step 1: Validate schema
  POST /api/production/strategies/validate-schema/
  → check: does the code conform to the canonical Signal schema?
              |
              v
Step 2: Safety-check the code
  POST /api/production/strategies/validate-code/
  → check: no dangerous patterns, no network calls, no arbitrary file writes
              |
              v
Step 3: Smoke test in sandbox
  POST /api/production/strategies/sandbox-test/
  → executes with limited resources against a small test dataset
              |
              v
Step 4: Review lifecycle
  GET /api/production/strategies/<id>/lifecycle/
  → see full history of all attempts, validations, and test results
              |
        all clear?
       /          \
     YES           NO → fix the code, repeat steps 1-3
      |
      v
Step 5: Deploy
  POST /api/production/strategies/<id>/deploy/
  → commits code to git, applies a version tag
              |
              v
        running in production
              |
   issue found?
       /      \
     YES        NO → done
      |
      v
Step 6: Rollback
  POST /api/production/strategies/<id>/rollback/
  → checks out previous git tag, marks prior version active
```

---

## Endpoint Reference

### POST /api/production/strategies/validate-schema/

Validates the strategy code structure against the canonical Pydantic schema (`Signal`, `OrderSide`, `OrderType`, etc.).

**Auth required:** Yes

**Request body:**
| Field | Type | Required |
|-------|------|----------|
| `strategy_code` | string | Yes |

**Response `200`:**
| Field | Type | Description |
|-------|------|-------------|
| `valid` | bool | Schema conforms |
| `errors` | array[string] | List of schema violations |
| `schema_version` | string | Version of canonical schema used |
| `warnings` | array[string] | Non-blocking issues |

---

### POST /api/production/strategies/validate-code/

Static analysis to detect security violations and dangerous code patterns.

**Auth required:** Yes

**Request body:**
| Field | Type | Required |
|-------|------|----------|
| `strategy_code` | string | Yes |

**Patterns detected and blocked:**
- `exec()`, `eval()`, `compile()` — dynamic code execution
- `subprocess`, `os.system`, `os.popen` — shell execution
- `socket`, `urllib`, `requests`, `httpx` — network access
- `open()` writes outside sandbox path — unauthorized file writes
- `import ctypes`, `import pickle` — unsafe imports

**Response `200`:**
| Field | Type | Description |
|-------|------|-------------|
| `safe` | bool | No violations found |
| `violations` | array | Each: `{ pattern, line, severity: "error"/"warning" }` |
| `summary` | string | Human-readable verdict |

---

### POST /api/production/strategies/sandbox-test/

Executes the strategy code in an isolated sandbox with resource limits. No network, no file system writes outside the sandbox path.

**Auth required:** Yes

**Request body:**
| Field | Type | Required | Default |
|-------|------|----------|---------|
| `strategy_code` | string | Yes | — |
| `test_symbol` | string | No | "AAPL" |
| `test_period` | string | No | "1y" |
| `initial_capital` | float | No | 10000 |

**Response `200`:**
| Field | Type | Description |
|-------|------|-------------|
| `success` | bool | Did execution complete without error |
| `execution_time` | float | Seconds |
| `metrics.return_pct` | float | |
| `metrics.total_trades` | int | |
| `metrics.win_rate` | float | |
| `metrics.sharpe_ratio` | float | |
| `metrics.max_drawdown` | float | |
| `logs` | string | stdout/stderr from sandbox |
| `error` | string | Error message if `success=false` |

---

### GET /api/production/strategies/<id>/lifecycle/

Returns the full audit trail for a strategy — every generation attempt, validation step, fix iteration, and deployment.

**Auth required:** Yes (owner)

**Response:** Array of state entries (newest first):

| Field | Type | Description |
|-------|------|-------------|
| `state` | string | e.g. "generated", "schema_valid", "code_safe", "sandbox_passed", "deployed", "rolled_back" |
| `timestamp` | datetime | When this state was recorded |
| `attempt_number` | int | Fix iteration number (if applicable) |
| `details` | object | State-specific detail (errors, metrics, commit hash) |

---

### POST /api/production/strategies/<id>/deploy/

Commits the strategy code to Git with a version tag. Marks the strategy as deployed in the lifecycle trail.

**Auth required:** Yes (owner)

**Request body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `commit_message` | string | No | Defaults to "Deploy strategy {name} v{version}" |
| `tag` | string | No | Defaults to `v{version}-{timestamp}` |

**Response `200`:**
| Field | Type |
|-------|------|
| `deployed` | bool |
| `commit_hash` | string |
| `tag` | string |
| `strategy_version` | int |

---

### POST /api/production/strategies/<id>/rollback/

Rolls the strategy back to a previous Git tag.

**Auth required:** Yes (owner)

**Request body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `target_tag` | string | No | If omitted, reverts one version |

**Response `200`:**
| Field | Type |
|-------|------|
| `rolled_back` | bool |
| `previous_tag` | string — the tag that was reverted from |
| `current_tag` | string — the tag now active |

---

### Production Backtest Endpoints

#### POST /api/production/backtests/validate-config/

Validate a backtest configuration object using Pydantic before submitting a run.

**Auth required:** Yes

**Request body:** Same fields as `BacktestConfig` (see [API_ENDPOINTS.md](API_ENDPOINTS.md#backtest-configs-viewset))

**Response `200`:** `{ valid: bool, errors: [string] }`

---

#### POST /api/production/backtests/run-sandbox/

Run a backtest in an isolated sandbox with full lifecycle tracking. Returns a `job_id`.

**Auth required:** Yes

Same request/response as `POST /api/backtests/api/run_backtest/` but with sandbox isolation and audit trail.

---

#### GET /api/production/backtests/<id>/status/

Get the execution status of a production backtest run.

**Auth required:** Yes (owner)

**Response:** `{ status, progress, current_step, started_at, completed_at, error }`

---

#### POST /api/production/backtests/<id>/stop/

Force-stop a running production backtest.

**Auth required:** Yes (owner)

**Response `200`:** `{ stopped: true }`

---

## Canonical Schema Reference

The `Backtest/canonical_schema_v2.py` module defines the typed signal schema that all production strategies must conform to.

**Key enums:**

| Enum | Values |
|------|--------|
| `OrderSide` | `BUY`, `SELL` |
| `OrderAction` | `ENTRY`, `EXIT`, `MODIFY`, `CANCEL` |
| `OrderType` | `MARKET`, `LIMIT`, `STOP` |
| `OrderStatus` | `PENDING`, `FILLED`, `PARTIAL`, `CANCELLED`, `REJECTED` |
| `SizeType` | `FIXED`, `PERCENT`, `RISK_PCT`, `ATR_BASED`, `KELLY`, `VOLATILITY_SCALED` |

**`Signal` model fields:**
| Field | Type | Description |
|-------|------|-------------|
| `symbol` | string | Ticker |
| `side` | `OrderSide` | Buy or sell |
| `action` | `OrderAction` | Entry, exit, etc. |
| `order_type` | `OrderType` | Market, limit, stop |
| `size_type` | `SizeType` | How position size is determined |
| `size_value` | float | The sizing value |
| `price` | float | Limit/stop price (None for market orders) |
| `timestamp` | datetime | Signal time |
| `metadata` | dict | Optional extra fields |

---

## Notes for AI Coding Agents

- Always run `validate-schema/` and `validate-code/` before `sandbox-test/`. If either fails, fix the code and retry **before** reaching sandbox.
- The `lifecycle/` endpoint is your source of truth for what has already been attempted — check it before starting a new generation to avoid duplicate work.
- Do not call `deploy/` until `sandbox-test/` returns `success: true`.
- Rollback does not delete DB records — the lifecycle trail is immutable. It only switches which git tag is active.
- The `workflows_api` is a stub and not connected to the production pipeline. Do not route production workflows through it.
