# Data Models Reference

**Last Updated:** March 10, 2026
**See also:** [Architecture](architecture/ARCHITECTURE.md) | [API Endpoints](api/API_ENDPOINTS.md) | [AI Pipeline](AI_PIPELINE.md)

---

## Overview

All models live in Django app-specific `models.py` files. Every model that belongs to a user is filtered by `created_by=request.user` in querysets, enforced by the `IsOwner` permission class.

**Shared conventions:**
- `created_at` / `updated_at` — Auto-set timestamps on every model
- `created_by` — ForeignKey to `auth.User` (most models)
- `id` — Auto-incrementing integer primary key

---

## App: `auth_api`

### UserProfile

Extended profile for each user. Auto-created by a post-save signal when a `User` is registered.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `user` | OneToOne → User | unique | |
| `default_risk_tolerance` | string | max 20, blank | "low", "medium", "high" |
| `default_timeframe` | string | max 10, blank | e.g. "1d", "1h" |
| `preferred_symbols` | JSON | default `[]` | List of ticker strings |
| `trading_goals` | text | blank | Free text |
| `strategy_preferences` | text | blank | Free text |
| `risk_parameters` | JSON | default `{}` | Arbitrary risk config object |

**Relations:** One UserProfile per User (1:1).

---

### AIContext

Persistent AI instruction sets. Active contexts are included in all LLM calls for the user.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `user` | FK → User | cascade | Owner |
| `session_name` | string | max 200 | Label |
| `instructions` | text | | System-level prompt instructions |
| `context_data` | JSON | default `{}` | Extra structured context |
| `is_active` | bool | default `True` | Include in LLM calls |

---

### ChatSession

Legacy general-purpose chat session (predates strategy-specific chat).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `user` | FK → User | cascade | Owner |
| `session_id` | string | unique, max 100 | Client-assigned or auto-generated |
| `title` | string | max 200 | Display name |
| `strategy_template_id` | int | null | Linked template (optional) |
| `messages` | JSON | default `[]` | Array of `{role, content, timestamp}` |
| `generated_strategies` | JSON | default `[]` | Array of strategy IDs generated in this session |

---

### ChatMessage

Individual messages within a `ChatSession`.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `session` | FK → ChatSession | cascade | Parent session |
| `role` | string | max 20 | "user", "assistant", "system" |
| `content` | text | | Message body |
| `tokens_used` | int | default 0 | Token count for this message |

---

## App: `data_api`

### Symbol

A tradeable instrument.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `symbol` | string | unique, max 20 | Ticker, e.g. "AAPL" |
| `name` | string | max 200 | Full name |
| `exchange` | string | max 50, blank | e.g. "NASDAQ", "NYSE" |
| `sector` | string | max 100, blank | |
| `industry` | string | max 200, blank | |
| `is_active` | bool | default `True` | |

---

### DataRequest

Tracks a request to fetch data for a symbol.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `request_id` | string | unique | UUID |
| `symbol` | FK → Symbol | set_null | |
| `period` | string | max 20 | e.g. "1y", "max" |
| `interval` | string | max 10 | e.g. "1d", "1h" |
| `status` | string | max 20 | "pending", "completed", "failed" |
| `error_message` | text | blank | Populated on failure |

---

### MarketData

OHLCV candle data.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `symbol` | FK → Symbol | cascade | |
| `timestamp` | datetime | | Candle time |
| `open` | decimal | | |
| `high` | decimal | | |
| `low` | decimal | | |
| `close` | decimal | | |
| `adj_close` | decimal | null | Adjusted close |
| `volume` | bigint | | |
| `interval` | string | max 10 | e.g. "1d" |

**Unique together:** `(symbol, timestamp, interval)`

---

### Indicator

Indicator definition/registry entry.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `name` | string | unique, max 50 | Internal key, e.g. "rsi" |
| `display_name` | string | max 100 | Human label |
| `category` | string | max 30 | "trend", "momentum", "volatility", "volume" |
| `parameters` | JSON | default `{}` | Parameter schema with types and defaults |

---

### IndicatorData

Calculated indicator values for a symbol.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `symbol` | FK → Symbol | cascade | |
| `indicator` | FK → Indicator | cascade | |
| `timestamp` | datetime | | |
| `value` | JSON | | Calculated value(s) — can be scalar or object |
| `parameters` | JSON | default `{}` | The parameter set used for this calculation |

---

### DataCache

Processed dataset cache keyed by a string.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `cache_key` | string | unique, max 200 | Identifies what's cached |
| `data_type` | string | max 50 | e.g. "ohlcv", "indicator" |
| `data` | JSON | | Cached payload |
| `expires_at` | datetime | null | TTL (null = no expiry) |

---

## App: `strategy_api`

### Strategy

A trading strategy (the core object of the system).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `name` | string | max 200 | |
| `strategy_code` | text | | Full Python source code |
| `parameters` | JSON | default `{}` | Parameter key/value pairs |
| `status` | string | max 20 | "draft", "validating", "valid", "invalid", "active", "inactive" |
| `version` | int | default 1 | Auto-incremented on each code update |
| `timeframe` | string | max 10, blank | e.g. "1d" |
| `risk_level` | string | max 20, blank | "low", "medium", "high" |
| `tags` | M2M → StrategyTag | | |
| `created_by` | FK → User | set_null | Owner |

**Relations:**
- `StrategyTemplate` → `Strategy` (linked_strategy FK)
- `StrategyValidation` → `Strategy` (FK)
- `StrategyPerformance` → `Strategy` (FK)
- `StrategyChat` → `Strategy` (FK)
- `BacktestRun` → `Strategy` (FK)
- `LatestBacktestResult` → `Strategy` (OneToOne)
- `BotPerformance` → `Strategy` (FK)

---

### StrategyTemplate

A reusable strategy scaffold, optionally linked to a specific Strategy.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `name` | string | max 200 | |
| `template_code` | text | | Base Python code |
| `parameters_schema` | JSON | default `{}` | Schema for template parameters |
| `is_system_template` | bool | default `False` | System templates cannot be auto-updated |
| `linked_strategy` | FK → Strategy | null | Points to the live strategy this template tracks |
| `chat_history` | JSON | default `[]` | Last 50 chat messages used to generate this template |
| `latest_strategy_code` | text | blank | Most recent generated code (cached for quick access) |

---

### StrategyValidation

Record of a single validation run against a strategy.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `strategy` | FK → Strategy | cascade | |
| `validation_type` | string | max 50 | "syntax", "semantic", "ai", "execution" |
| `status` | string | max 20 | "pending", "passed", "failed", "warning" |
| `score` | float | null | 0–100 |
| `passed_checks` | JSON | default `[]` | |
| `failed_checks` | JSON | default `[]` | |
| `warnings` | JSON | default `[]` | |
| `recommendations` | JSON | default `[]` | |
| `execution_time` | float | null | Seconds |
| `created_by` | FK → User | set_null | |

---

### StrategyPerformance

Aggregated performance summary for a strategy across all its backtests.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `strategy` | FK → Strategy | cascade | |
| `total_return` | float | null | |
| `annualized_return` | float | null | |
| `sharpe_ratio` | float | null | |
| `max_drawdown` | float | null | |
| `win_rate` | float | null | |
| `total_trades` | int | null | |
| `avg_trade_return` | float | null | |

---

### StrategyComment

User comment or review on a strategy.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `strategy` | FK → Strategy | cascade | |
| `content` | text | | |
| `rating` | int | null, 1–5 | Star rating |
| `is_review` | bool | default `False` | Review vs regular comment |
| `parent` | FK → self | null | For threaded replies |
| `created_by` | FK → User | set_null | |

---

### StrategyTag

Tag that can be applied to strategies.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `name` | string | unique, max 50 | e.g. "momentum" |
| `color` | string | max 7 | Hex color code, e.g. "#FF5733" |

---

### StrategyChat

A chat session tied to a specific strategy (for iterative AI refinement).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `session_id` | string | unique, max 100 | UUID or client-assigned |
| `strategy` | FK → Strategy | null, cascade | The strategy being discussed |
| `title` | string | max 200 | Display name |
| `context_summary` | text | blank | Compressed summary of conversation so far |
| `message_count` | int | default 0 | Cached count |
| `model_name` | string | max 100, blank | LLM model used |
| `temperature` | float | null | LLM temperature setting |
| `max_tokens` | int | null | |
| `created_by` | FK → User | set_null | |

---

### StrategyChatMessage

Individual message in a `StrategyChat`.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `session` | FK → StrategyChat | cascade | |
| `role` | string | max 20 | "user", "assistant", "system" |
| `content` | text | | |
| `tokens_used` | int | default 0 | |
| `metadata` | JSON | default `{}` | Arbitrary extra data |
| `function_call` | JSON | null | Tool/function call payload (for LLM tool use) |

---

### BotPerformance

Aggregated performance record for a strategy bot (updated after each successful backtest).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `strategy` | FK → Strategy | cascade | |
| `is_verified` | bool | default `False` | Passed automated verification |
| `verification_date` | datetime | null | |
| `total_runs` | int | default 0 | Number of execution attempts |
| `successful_runs` | int | default 0 | |
| `avg_return_pct` | float | null | |
| `best_return_pct` | float | null | |
| `worst_return_pct` | float | null | |
| `avg_sharpe` | float | null | |
| `avg_win_rate` | float | null | |
| `created_by` | FK → User | set_null | |

---

### LatestBacktestResult

One record per strategy — stores the most recent successful backtest result for fast frontend display.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `strategy` | OneToOne → Strategy | cascade | |
| `symbol` | string | max 20 | Symbol tested |
| `timeframe` | string | max 10 | |
| `period` | string | max 20 | e.g. "1y" |
| `total_trades` | int | | |
| `win_rate` | float | | |
| `return_pct` | float | | |
| `sharpe_ratio` | float | | |
| `max_drawdown` | float | | |
| `equity_curve` | JSON | | Array of portfolio value over time |
| `symbol_stats` | JSON | | Per-symbol breakdown |

---

## App: `backtest_api`

### BacktestConfig

Reusable backtest parameter set.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `name` | string | max 200 | |
| `start_date` | date | | |
| `end_date` | date | | |
| `initial_capital` | float | default 10000 | |
| `commission` | float | default 0.001 | Fraction per trade |
| `slippage` | float | default 0.001 | |
| `max_position_size` | float | null | Fraction of capital |
| `stop_loss` | float | null | Fraction |
| `take_profit` | float | null | Fraction |
| `data_source` | string | max 50, blank | e.g. "yfinance" |
| `timeframe` | string | max 10 | e.g. "1d" |
| `benchmark_symbol` | string | max 20, blank | e.g. "SPY" |
| `is_template` | bool | default `False` | System-level reusable config |
| `created_by` | FK → User | set_null | |

---

### BacktestRun

A single backtest execution instance.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `run_id` | string | unique, max 100 | UUID |
| `config` | FK → BacktestConfig | null | Optional linked config |
| `strategy` | FK → Strategy | null | The strategy being tested |
| `symbols` | JSON | default `[]` | List of ticker strings |
| `status` | string | max 20 | "pending", "queued", "running", "completed", "failed" |
| `progress` | int | default 0 | 0–100 |
| `execution_time` | float | null | Seconds |
| `total_return` | float | null | Summary metric (copied from result) |
| `sharpe_ratio` | float | null | |
| `max_drawdown` | float | null | |
| `total_trades` | int | null | |
| `win_rate` | float | null | |
| `celery_task_id` | string | max 100, blank | Used to cancel the task |
| `created_by` | FK → User | set_null | |

---

### BacktestResult

Detailed result associated with a `BacktestRun` (one-to-one, created on completion).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `run` | OneToOne → BacktestRun | cascade | |
| `final_portfolio_value` | float | | |
| `total_return_pct` | float | | |
| `annualized_return` | float | | |
| `volatility` | float | | |
| `sharpe_ratio` | float | | |
| `sortino_ratio` | float | | |
| `calmar_ratio` | float | | |
| `max_drawdown` | float | | |
| `win_rate` | float | | |
| `total_trades` | int | | |
| `profit_factor` | float | | |
| `alpha` | float | null | vs benchmark |
| `beta` | float | null | vs benchmark |
| `portfolio_values` | JSON | | Time series array |
| `portfolio_returns` | JSON | | Time series array |
| `portfolio_drawdowns` | JSON | | Time series array |
| `positions` | JSON | | Position history array |

---

### Trade

Individual trade record from a backtest.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `run` | FK → BacktestRun | cascade | |
| `entry_time` | datetime | | |
| `exit_time` | datetime | null | |
| `entry_price` | float | | |
| `exit_price` | float | null | |
| `pnl` | float | null | Profit/loss in currency |
| `return_pct` | float | null | |
| `side` | string | max 10 | "LONG", "SHORT" |
| `size` | float | null | Position size |

---

### BacktestAlert

Alerts generated during a backtest (e.g. stop-loss triggered, data gaps).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `run` | FK → BacktestRun | cascade | |
| `alert_type` | string | max 50 | e.g. "stop_loss", "data_gap", "low_trades" |
| `message` | text | | |
| `severity` | string | max 20 | "info", "warning", "error" |
| `timestamp` | datetime | | When during the backtest this occurred |

---

## App: `trading`

This app has no persistent models. It only runs the `BacktestStreamConsumer` WebSocket consumer which writes its final output to `LatestBacktestResult` (owned by `strategy_api`).

---

## App: `workflows_api`

No models. Stub only.

---

## Entity Relationship Summary

```
auth.User
    |
    +-- UserProfile (1:1)
    |
    +-- AIContext (1:N)
    |
    +-- ChatSession (1:N)
    |       |
    |       +-- ChatMessage (1:N)
    |
    +-- Strategy (1:N)  [created_by]
    |       |
    |       +-- StrategyTemplate (N:1 via linked_strategy)
    |       +-- StrategyValidation (1:N)
    |       +-- StrategyPerformance (1:N)
    |       +-- StrategyComment (1:N)
    |       +-- StrategyChat (1:N)
    |       |       +-- StrategyChatMessage (1:N)
    |       +-- BotPerformance (1:N)
    |       +-- LatestBacktestResult (1:1)
    |       +-- BacktestRun (1:N)
    |               +-- BacktestResult (1:1)
    |               +-- Trade (1:N)
    |               +-- BacktestAlert (1:N)
    |
    +-- BacktestConfig (1:N)  [created_by]

data_api:
    Symbol (1:N) --> MarketData
    Symbol (1:N) --> DataRequest
    Symbol (1:N) --> IndicatorData
    Indicator (1:N) --> IndicatorData
```
