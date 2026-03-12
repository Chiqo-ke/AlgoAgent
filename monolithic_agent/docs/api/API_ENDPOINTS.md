# API Endpoints Reference

**Last Updated:** March 11, 2026
**Base URL:** `http://localhost:8000` (dev) | `https://chiqoke254.pythonanywhere.com` (prod)
**See also:** [Architecture](../architecture/ARCHITECTURE.md) | [Production API](PRODUCTION_API_GUIDE.md) | [Quick Reference](../guides/QUICK_REFERENCE.md)

---

## Table of Contents

- [Authentication Notes](#authentication-notes)
- [Auth API — `/api/auth/`](#auth-api)
- [Data API — `/api/data/`](#data-api)
- [Strategy API — `/api/strategies/`](#strategy-api)
- [Backtest API — `/api/backtests/`](#backtest-api)
- [Production API — `/api/production/`](#production-api)
- [Trading Sessions API — `/api/trading/`](#trading-sessions-api)
- [Workflows API — `/api/workflows/`](#workflows-api)
- [Utility Endpoints](#utility-endpoints)
- [WebSocket Endpoint](#websocket-endpoint)
- [Async Job Polling](#async-job-polling)
- [Pagination](#pagination)
- [Error Responses](#error-responses)

---

## Authentication Notes

**Method:** JWT Bearer token

All protected endpoints require:
```
Authorization: Bearer <access_token>
```

Tokens are obtained from `POST /api/auth/login/`. The access token expires after **1 hour**; use `POST /api/auth/token/refresh/` with the refresh token to get a new one.

The default DRF permission is `AllowAny`. Endpoints that require authentication explicitly declare `IsAuthenticated`. All user-owned resources are filtered by `created_by=request.user` — users cannot access other users' data.

---

## Auth API

**Base path:** `/api/auth/`

### POST /api/auth/register/

Register a new user account.

**Auth required:** No

**Request body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | Yes | Unique username |
| `email` | string | Yes | Email address |
| `password` | string | Yes | Password |
| `password_confirm` | string | Yes | Password confirmation |

**Response `201`:**
| Field | Type | Description |
|-------|------|-------------|
| `user.id` | int | New user ID |
| `user.username` | string | Username |
| `user.email` | string | Email |
| `tokens.access` | string | JWT access token |
| `tokens.refresh` | string | JWT refresh token |

---

### POST /api/auth/login/

Authenticate and receive JWT tokens.

**Auth required:** No

**Request body:**
| Field | Type | Required |
|-------|------|----------|
| `username` | string | Yes |
| `password` | string | Yes |

**Response `200`:**
| Field | Type | Description |
|-------|------|-------------|
| `user.id` | int | User ID |
| `user.username` | string | |
| `user.email` | string | |
| `tokens.access` | string | 1-hour JWT access token |
| `tokens.refresh` | string | 7-day JWT refresh token |

---

### POST /api/auth/logout/

Revoke the refresh token (server-side blacklist).

**Auth required:** Yes

**Request body:**
| Field | Type | Required |
|-------|------|----------|
| `refresh` | string | Yes — the refresh token to blacklist |

**Response `200`:** `{ "detail": "Successfully logged out." }`

---

### POST /api/auth/token/refresh/

Get a new access token using a valid refresh token.

**Auth required:** No

**Request body:**
| Field | Type | Required |
|-------|------|----------|
| `refresh` | string | Yes |

**Response `200`:**
| Field | Type |
|-------|------|
| `access` | string — new access token |
| `refresh` | string — new refresh token (rotation enabled) |

---

### GET /api/auth/user/me/

Get the currently authenticated user's details.

**Auth required:** Yes

**Response `200`:**
| Field | Type |
|-------|------|
| `id` | int |
| `username` | string |
| `email` | string |
| `date_joined` | datetime |

---

### POST /api/auth/change-password/

Change the current user's password.

**Auth required:** Yes

**Request body:**
| Field | Type | Required |
|-------|------|----------|
| `old_password` | string | Yes |
| `new_password` | string | Yes |
| `new_password_confirm` | string | Yes |

**Response `200`:** `{ "detail": "Password changed successfully." }`

---

### GET /api/auth/google/

Redirect to Google OAuth consent screen. Used to initiate the Google login flow.

**Auth required:** No | **Response:** 302 redirect to Google

---

### GET /api/auth/google/callback/

Google OAuth callback. Handles the authorization code returned by Google, creates or links a user account, and returns JWT tokens.

**Auth required:** No | **Response:** Redirect to frontend with tokens

---

### POST /api/auth/chat/

Send a message to the general AI chat assistant.

**Auth required:** Yes

**Request body:**
| Field | Type | Required |
|-------|------|----------|
| `message` | string | Yes |
| `session_id` | string | No — ties message to an existing chat session |
| `context` | object | No — additional context passed to the LLM |

**Response `200`:**
| Field | Type |
|-------|------|
| `response` | string — AI reply |
| `session_id` | string |
| `tokens_used` | int |

---

### GET /api/auth/health/

Health check for auth service.

**Auth required:** No | **Response `200`:** `{ "status": "ok" }`

---

### User Profiles (ViewSet)

**Auth required:** Yes (owner-scoped)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/auth/profiles/` | List profiles (returns current user's profile) |
| POST | `/api/auth/profiles/` | Create profile (auto-created on registration) |
| GET | `/api/auth/profiles/<id>/` | Get profile |
| PUT/PATCH | `/api/auth/profiles/<id>/` | Update profile |

**Profile fields (request/response):**
| Field | Type | Description |
|-------|------|-------------|
| `default_risk_tolerance` | string | e.g. "low", "medium", "high" |
| `default_timeframe` | string | e.g. "1d", "1h" |
| `preferred_symbols` | array[string] | e.g. ["AAPL", "BTC-USD"] |
| `trading_goals` | string | Free text |
| `strategy_preferences` | string | Free text |
| `risk_parameters` | object | JSON risk config |

---

### AI Contexts (ViewSet)

Persistent AI instruction sets that are sent with LLM calls.

**Auth required:** Yes (owner-scoped)

| Method | Path |
|--------|------|
| GET/POST | `/api/auth/ai-contexts/` |
| GET/PUT/PATCH/DELETE | `/api/auth/ai-contexts/<id>/` |

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `session_name` | string | Human label |
| `instructions` | string | System-level instructions for the AI |
| `context_data` | object | Extra JSON context |
| `is_active` | bool | Whether to include in LLM calls |

---

### Chat Sessions (ViewSet)

Legacy chat sessions (pre-strategy-specific chat). Still functional.

**Auth required:** Yes (owner-scoped)

| Method | Path |
|--------|------|
| GET/POST | `/api/auth/chat-sessions/` |
| GET/PUT/PATCH/DELETE | `/api/auth/chat-sessions/<id>/` |

**Response fields:** `session_id`, `title`, `messages` (array), `generated_strategies` (array), `created_at`

---

## Data API

**Base path:** `/api/data/`

### Symbols (ViewSet)

**Auth required:** Yes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/data/symbols/` | List all active symbols |
| POST | `/api/data/symbols/` | Create a symbol |
| GET | `/api/data/symbols/<id>/` | Get symbol |
| PUT/PATCH | `/api/data/symbols/<id>/` | Update symbol |
| POST | `/api/data/symbols/bulk_create/` | Create multiple symbols |
| GET | `/api/data/symbols/search/` | Search by name/ticker |

**Symbol fields:**
| Field | Type | Description |
|-------|------|-------------|
| `symbol` | string | Ticker (unique), e.g. "AAPL" |
| `name` | string | Full name |
| `exchange` | string | e.g. "NASDAQ" |
| `sector` | string | |
| `industry` | string | |
| `is_active` | bool | |

---

### POST /api/data/api/fetch_data/

Fetch historical OHLCV data for a symbol and store it.

**Auth required:** Yes

**Request body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `symbol` | string | Yes | Ticker, e.g. "AAPL" |
| `period` | string | Yes | e.g. "1y", "6mo", "max" |
| `interval` | string | Yes | e.g. "1d", "1h", "15m" |

**Response `202`:**
| Field | Type |
|-------|------|
| `request_id` | string — poll this for completion |
| `status` | "pending" |

---

### GET /api/data/market-data/

Query stored OHLCV candles.

**Auth required:** Yes

**Query params:**
| Param | Type | Description |
|-------|------|-------------|
| `symbol` | string | Filter by ticker |
| `interval` | string | e.g. "1d" |
| `start_date` | date | ISO format |
| `end_date` | date | ISO format |
| `page` | int | Pagination |

**Response fields per record:** `symbol`, `timestamp`, `open`, `high`, `low`, `close`, `adj_close`, `volume`, `interval`

---

### GET /api/data/api/available_indicators/

List all indicators with their parameter schemas.

**Auth required:** Yes

**Response:** Array of `{ name, display_name, category, parameters }` objects.

---

### GET /api/data/indicators/

List indicator definitions.

**Auth required:** Yes

**Response fields per record:** `name`, `display_name`, `category` (trend/momentum/volatility/volume), `parameters` (JSON schema)

---

### GET /api/data/api/health/

**Auth required:** No | **Response `200`:** `{ "status": "ok" }`

---

## Strategy API

**Base path:** `/api/strategies/`

### Strategies (ViewSet)

**Auth required:** Yes (owner-scoped)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/strategies/strategies/` | List strategies |
| POST | `/api/strategies/strategies/` | Create strategy |
| GET | `/api/strategies/strategies/<id>/` | Get strategy |
| PUT/PATCH | `/api/strategies/strategies/<id>/` | Update strategy |
| DELETE | `/api/strategies/strategies/<id>/` | Delete strategy |
| POST | `/api/strategies/strategies/<id>/validate/` | Validate by ID |
| POST | `/api/strategies/strategies/<id>/backtest/` | Quick backtest |
| POST | `/api/strategies/strategies/<id>/clone/` | Clone strategy |

**List query params:** `status`, `timeframe`, `risk_level`, `ordering`, `page`

**Strategy fields (create/update request):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Strategy name |
| `strategy_code` | string | Yes | Python code |
| `parameters` | object | No | Strategy parameters JSON |
| `status` | string | No | draft / validating / valid / invalid / active / inactive |
| `timeframe` | string | No | e.g. "1d" |
| `risk_level` | string | No | low / medium / high |
| `tags` | array[int] | No | Tag IDs |

**Strategy response fields:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | int | |
| `name` | string | |
| `strategy_code` | string | Full Python code |
| `status` | string | Current lifecycle status |
| `version` | int | Auto-incremented on updates |
| `timeframe` | string | |
| `risk_level` | string | |
| `created_at` | datetime | |
| `updated_at` | datetime | |
| `created_by` | object | `{id, username}` |
| `latest_backtest` | object | Nested summary (see LatestBacktestResult) |

---

### POST /api/strategies/validate/

Validate a strategy by submitting code directly (no saved strategy required).

**Auth required:** Yes

**Request body:**
| Field | Type | Required |
|-------|------|----------|
| `strategy_code` | string | Yes |
| `parameters` | object | No |

**Response `200`:**
| Field | Type | Description |
|-------|------|-------------|
| `is_valid` | bool | |
| `score` | float | 0–100 |
| `passed_checks` | array[string] | |
| `failed_checks` | array[string] | |
| `warnings` | array[string] | |
| `recommendations` | array[string] | |
| `execution_time` | float | Seconds |

---

### POST /api/strategies/validate-file/

Validate a strategy uploaded as a `.py` file.

**Auth required:** Yes | **Content-Type:** `multipart/form-data`

**Request body:**
| Field | Type | Required |
|-------|------|----------|
| `file` | file | Yes — `.py` file |

**Response:** Same structure as POST /validate/ above.

---

### GET /api/strategies/templates/

**Auth required:** Yes | Standard CRUD ViewSet.

**Template fields:** `name`, `template_code`, `parameters_schema`, `is_system_template`, `linked_strategy` (int), `chat_history`, `latest_strategy_code`

**Custom actions:**
- `POST /api/strategies/templates/<id>/sync_from_strategy/` — Update template from linked strategy's latest code
- `GET /api/strategies/templates/<id>/get_context/` — Get full AI context including linked strategy info

---

### POST /api/strategies/api/generate_strategy_unified/

**The primary AI strategy generation endpoint.** Submits a Celery task and returns immediately with a `job_id`. Use [job polling](#async-job-polling) to track progress.

**Auth required:** Yes

**Request body:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `description` | string | Yes | — | Natural language strategy description |
| `ai_provider` | string | No | `"gemini"` | `"gemini"` or `"copilot"` |
| `auto_fix` | bool | No | `true` | Enable the error-fix loop |
| `max_fix_attempts` | int | No | `8` | Max iterations of the fix loop |
| `execute_after` | bool | No | `true` | Run a backtest after generation |
| `test_symbol` | string | No | `"AAPL"` | Symbol to test against |
| `test_period_days` | int | No | `365` | Days of historical data |
| `template_id` | int | No | — | Base on an existing template |

**Response `202`:**
| Field | Type | Description |
|-------|------|-------------|
| `job_id` | string | Poll `GET /api/jobs/<job_id>/` for result |
| `status` | string | "pending" |

**Polled result (SUCCESS):**
| Field | Type | Description |
|-------|------|-------------|
| `strategy_id` | int | Saved Strategy ID |
| `strategy_name` | string | |
| `execution_success` | bool | Whether backtest ran cleanly |
| `metrics.return_pct` | float | |
| `metrics.total_trades` | int | |
| `metrics.win_rate` | float | |
| `metrics.sharpe_ratio` | float | |
| `metrics.max_drawdown` | float | |
| `fix_attempts` | int | Iterations needed |

---

### POST /api/strategies/api/validate_strategy_with_ai/

AI-powered strategy validation with detailed feedback.

**Auth required:** Yes

**Request body:**
| Field | Type | Required |
|-------|------|----------|
| `strategy_code` | string | Yes |
| `context` | string | No — additional context for the AI reviewer |

**Response `200`:** Same structure as POST /validate/ plus:
| Field | Type |
|-------|------|
| `ai_feedback` | string — narrative explanation |
| `suggestions` | array[string] |

---

### POST /api/strategies/api/create_strategy_with_ai/

Synchronous AI strategy creation (smaller, simpler generation without the full fix loop).

**Auth required:** Yes

**Request body:**
| Field | Type | Required |
|-------|------|----------|
| `description` | string | Yes |
| `ai_provider` | string | No |

**Response `200`:** `{ strategy_code, name, parameters }`

---

### POST /api/strategies/api/{id}/update_strategy_with_ai/

Update an existing strategy's code using AI.

**Auth required:** Yes (owner required)

**Request body:**
| Field | Type | Required |
|-------|------|----------|
| `instruction` | string | Yes — what to change |

**Response `200`:** `{ strategy_id, new_code, changes_description }`

---

### GET /api/strategies/api/categories/

List available strategy categories.

**Auth required:** Yes | **Response:** `{ categories: [string] }`

---

### GET /api/strategies/api/health/

**Auth required:** No | **Response `200`:** `{ "status": "ok" }`

---

### Bot Performance (ViewSet)

Aggregated execution metrics per strategy.

**Auth required:** Yes (owner-scoped)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/strategies/bot-performance/` | List bot performance records |
| GET | `/api/strategies/bot-performance/<id>/` | Get single record |
| GET | `/api/strategies/bot-performance/verified_bots/` | List verified bots only |
| POST | `/api/strategies/bot-performance/verify_bot/` | Manually verify a bot |
| POST | `/api/strategies/bot-performance/verify_all/` | Trigger verification of all user bots |

---

### Latest Backtest Results (Read-only ViewSet)

One result per strategy — the most recent successful backtest.

**Auth required:** Yes (owner-scoped)

| Method | Path |
|--------|------|
| GET | `/api/strategies/backtest-results/` |
| GET | `/api/strategies/backtest-results/<strategy_id>/` |

**Response fields:** `strategy_id`, `symbol`, `timeframe`, `period`, `total_trades`, `win_rate`, `return_pct`, `sharpe_ratio`, `max_drawdown`, `equity_curve` (JSON), `symbol_stats` (JSON), `created_at`

---

### Strategy Validations (Read-only ViewSet)

**Auth required:** Yes (owner-scoped)

| Method | Path |
|--------|------|
| GET | `/api/strategies/validations/` |
| GET | `/api/strategies/validations/<id>/` |

**Query params:** `strategy` (int), `validation_type`, `status`

---

### Strategy Chat (ViewSet)

Strategy-specific AI chat sessions (linked to a strategy).

**Auth required:** Yes (owner-scoped)

| Method | Path |
|--------|------|
| GET/POST | `/api/strategies/chat/` |
| GET/PUT/PATCH/DELETE | `/api/strategies/chat/<id>/` |

**Fields:** `session_id`, `strategy` (int), `title`, `context_summary`, `message_count`, `model_name`, `messages` (array of `{role, content, tokens_used}`)

---

### Other Read/Write ViewSets

| Endpoint prefix | Model | Type |
|-----------------|-------|------|
| `/api/strategies/performance/` | StrategyPerformance | Full CRUD |
| `/api/strategies/comments/` | StrategyComment | Full CRUD |
| `/api/strategies/tags/` | StrategyTag | Full CRUD |

---

## Backtest API

**Base path:** `/api/backtests/`

### POST /api/backtests/api/run_backtest/

Submit a full backtest. Returns a `job_id`; use [job polling](#async-job-polling).

**Auth required:** Yes

**Request body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `strategy_id` | int | Yes | ID of saved strategy to backtest |
| `symbols` | array[string] | Yes | e.g. `["AAPL", "MSFT"]` |
| `start_date` | date | Yes | ISO format |
| `end_date` | date | Yes | ISO format |
| `initial_capital` | float | No | Default 10000 |
| `commission` | float | No | Commission per trade (fraction) |
| `timeframe` | string | No | e.g. "1d" |
| `config_id` | int | No | Use a saved BacktestConfig |

**Response `202`:** `{ job_id, run_id, status: "pending" }`

**Polled result (SUCCESS):**
| Field | Type |
|-------|------|
| `run_id` | int |
| `final_portfolio_value` | float |
| `total_return_pct` | float |
| `annualized_return` | float |
| `sharpe_ratio` | float |
| `sortino_ratio` | float |
| `calmar_ratio` | float |
| `max_drawdown` | float |
| `win_rate` | float |
| `total_trades` | int |
| `profit_factor` | float |
| `alpha` | float |
| `beta` | float |

---

### POST /api/backtests/api/quick_run/

Run a backtest with sensible defaults (last 1 year, daily bars, $10k capital).

**Auth required:** Yes

**Request body:**
| Field | Type | Required |
|-------|------|----------|
| `strategy_id` | int | Yes |
| `symbol` | string | Yes |

**Response `202`:** `{ job_id, run_id }`

---

### Backtest Configs (ViewSet)

Reusable parameter sets.

**Auth required:** Yes (owner-scoped)

| Method | Path |
|--------|------|
| GET/POST | `/api/backtests/configs/` |
| GET/PUT/PATCH/DELETE | `/api/backtests/configs/<id>/` |

**Config fields:** `start_date`, `end_date`, `initial_capital`, `commission`, `slippage`, `max_position_size`, `stop_loss`, `take_profit`, `data_source`, `timeframe`, `benchmark_symbol`, `is_template`

---

### Backtest Runs (ViewSet)

**Auth required:** Yes (owner-scoped)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/backtests/runs/` | List runs |
| GET | `/api/backtests/runs/<id>/` | Get run |
| GET | `/api/backtests/runs/<id>/result/` | Get detailed result |
| GET | `/api/backtests/runs/<id>/trades/` | List trades for this run |
| GET | `/api/backtests/runs/<id>/alerts/` | List alerts for this run |
| POST | `/api/backtests/runs/<id>/cancel/` | Cancel a running backtest |

**Run status values:** `pending` → `queued` → `running` → `completed` / `failed`

---

### Read-only ViewSets

| Endpoint | Model | Description |
|----------|-------|-------------|
| `GET /api/backtests/results/` | BacktestResult | Summary results |
| `GET /api/backtests/results/<id>/` | BacktestResult | Single result |
| `GET /api/backtests/trades/` | Trade | Trade records |
| `GET /api/backtests/trades/<id>/` | Trade | Single trade |
| `GET /api/backtests/alerts/` | BacktestAlert | Alerts from backtests |

**Trade fields:** `entry_time`, `exit_time`, `entry_price`, `exit_price`, `pnl`, `return_pct`

---

### GET /api/backtests/api/monitor/

Poll the status of a specific backtest run.

**Auth required:** Yes

**Query params:** `run_id` (int)

**Response:** `{ run_id, status, progress (0–100), current_step, error_message }`

---

### GET /api/backtests/api/health/

**Auth required:** No | **Response `200`:** `{ "status": "ok" }`

---

## Production API

**Base path:** `/api/production/`

These endpoints add validation, sandboxing, and deployment on top of the standard endpoints. See [PRODUCTION_API_GUIDE.md](PRODUCTION_API_GUIDE.md) for the full workflow.

### POST /api/production/strategies/validate-schema/

Validate strategy code against the canonical Pydantic schema.

**Auth required:** Yes

**Request body:**
| Field | Type | Required |
|-------|------|----------|
| `strategy_code` | string | Yes |

**Response `200`:** `{ valid: bool, errors: [string], schema_version: string }`

---

### POST /api/production/strategies/validate-code/

Static safety analysis — detects dangerous patterns (exec, eval, subprocess, network calls, etc.).

**Auth required:** Yes

**Request body:**
| Field | Type | Required |
|-------|------|----------|
| `strategy_code` | string | Yes |

**Response `200`:** `{ safe: bool, violations: [{ pattern, line, severity }] }`

---

### POST /api/production/strategies/sandbox-test/

Execute the strategy in an isolated sandbox with resource limits.

**Auth required:** Yes

**Request body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `strategy_code` | string | Yes | |
| `test_symbol` | string | No | Default "AAPL" |
| `test_period` | string | No | Default "1y" |

**Response `200`:** `{ success: bool, metrics: {...}, logs: string, execution_time: float }`

---

### GET /api/production/strategies/<id>/lifecycle/

Full audit trail of all generation attempts, validation steps, and fixes for a strategy.

**Auth required:** Yes (owner)

**Response:** Array of state entries, each with `{ state, timestamp, details, attempt_number }`

---

### POST /api/production/strategies/<id>/deploy/

Deploy a strategy with a Git commit and tag.

**Auth required:** Yes (owner)

**Request body:**
| Field | Type | Required |
|-------|------|----------|
| `commit_message` | string | No |
| `tag` | string | No — auto-generated if omitted |

**Response `200`:** `{ deployed: bool, commit_hash: string, tag: string }`

---

### POST /api/production/strategies/<id>/rollback/

Roll back a deployed strategy to its previous Git tag.

**Auth required:** Yes (owner)

**Request body:**
| Field | Type | Required |
|-------|------|----------|
| `target_tag` | string | No — rolls back one version if omitted |

**Response `200`:** `{ rolled_back: bool, current_tag: string }`

---

### Production Backtest Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/production/backtests/validate-config/` | Validate config with Pydantic before running |
| POST | `/api/production/backtests/run-sandbox/` | Run in isolated sandbox with audit trail |
| GET | `/api/production/backtests/<id>/status/` | Get execution status |
| POST | `/api/production/backtests/<id>/stop/` | Force-stop a running sandbox backtest |

---

## Trading Sessions API

**Status:** ✅ NEW (March 2026) | **Base path:** `/api/trading/`

**Full documentation:** [LIVE_TRADING_SESSIONS_API.md](../LIVE_TRADING_SESSIONS_API.md)

**Quick Summary:**
- Save encrypted broker credentials (MT5 login, server, terminal path)
- Start/stop live trading sessions for strategies
- Monitor subprocess health (PID, status, timestamps)
- Graceful termination via kill-switch mechanism
- Dry-run mode for testing

**Key Endpoints:**
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/credentials/` | Save broker credential |
| GET | `/credentials/` | List user's credentials |
| GET | `/credentials/{id}/` | Get one credential |
| PUT/PATCH | `/credentials/{id}/` | Update credential |
| DELETE | `/credentials/{id}/` | Delete credential |
| POST | `/sessions/` | Start live session |
| GET | `/sessions/` | List sessions |
| GET | `/sessions/{id}/` | Get session details |
| POST | `/sessions/{id}/stop/` | Stop running session |
| DELETE | `/sessions/{id}/` | Delete session |

**E2E Test Status:** ✅ All 5 steps passing
- Login → Save credential → List credentials → Start session (dry_run) → Stop session

---

## Workflows API

**Base path:** `/api/workflows/`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/workflows/` | Returns `{ "workflows": [] }` — stub, under development |

---

## Utility Endpoints

### GET /api/

API root — returns a JSON index of all endpoint groups.

**Auth required:** No

---

### POST /api/logs/frontend-errors/

Receives structured error reports from the frontend logger (`src/lib/logger.ts`).

**Auth required:** No (intentionally open — frontend must be able to report errors even before auth)

**Request body:**
| Field | Type | Description |
|-------|------|-------------|
| `level` | string | "error", "warn", "info" |
| `category` | string | "api", "auth", "ui", etc. |
| `message` | string | Error message |
| `stack` | string | Stack trace (optional) |
| `metadata` | object | Additional context |

**Response `200`:** `{ "logged": true }`

---

## WebSocket Endpoint

### ws://<host>/ws/backtest/stream/

Real-time backtest streaming. Data is pushed candle-by-candle as the simulation runs.

**Auth:** Pass JWT access token as a query param: `?token=<access_token>`

**Consumer:** `trading.consumers.BacktestStreamConsumer`

**Channel layer:** `InMemoryChannelLayer` (dev) — switch to Redis for prod (see [CONFIGURATION.md](../CONFIGURATION.md)).

**Message types sent to client:**

| Type | Fields | Description |
|------|--------|-------------|
| `candle` | `timestamp`, `open`, `high`, `low`, `close`, `volume` | Current OHLCV bar |
| `trade` | `entry_time`, `exit_time`, `entry_price`, `exit_price`, `pnl`, `side` | Completed round-trip trade |
| `progress` | `current`, `total`, `pct_complete` | Bar-by-bar progress |
| `result` | Full metrics object (same as BacktestResult) | Sent once at completion |
| `error` | `message` | Sent if the backtest fails |

**On completion:** Final result is persisted to `LatestBacktestResult` (one per strategy).

---

## Async Job Polling

All endpoints that trigger long-running Celery tasks respond immediately with a `job_id`. Poll the job endpoint:

### GET /api/jobs/<task_id>/

**Auth required:** No (but task results are only returned if the task exists)

**Response fields:**
| Field | Type | States present | Description |
|-------|------|----------------|-------------|
| `state` | string | all | PENDING / PROGRESS / SUCCESS / FAILURE / REVOKED |
| `current` | int | PROGRESS | Steps completed |
| `total` | int | PROGRESS | Total steps |
| `status` | string | PROGRESS | Description of current step |
| `result` | object | SUCCESS | Task result payload (varies by task) |
| `error` | string | FAILURE | Error message |

**Recommended polling interval:** 2 seconds for generation tasks, 1 second for backtests.

---

## Pagination

All list endpoints use page-number pagination.

**Query params:** `page` (int, default 1), `page_size` (int, default 50, max configurable)

**Response envelope:**
```
{
  "count":    <total items>,
  "next":     <URL or null>,
  "previous": <URL or null>,
  "results":  [...]
}
```

---

## Error Responses

| Status | Meaning | Body shape |
|--------|---------|-----------|
| `400` | Validation error | `{ "field_name": ["error message"] }` |
| `401` | Not authenticated | `{ "detail": "Authentication credentials were not provided." }` |
| `403` | Permission denied (not owner) | `{ "detail": "You do not have permission..." }` |
| `404` | Not found | `{ "detail": "Not found." }` |
| `500` | Server error | `{ "detail": "Internal server error." }` |
