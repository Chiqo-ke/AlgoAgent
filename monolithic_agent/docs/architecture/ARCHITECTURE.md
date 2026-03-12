# AlgoAgent — System Architecture

**Last Updated:** March 10, 2026
**See also:** [API Endpoints](../api/API_ENDPOINTS.md) | [Data Models](../DATA_MODELS.md) | [AI Pipeline](../AI_PIPELINE.md) | [Configuration](../CONFIGURATION.md)

---

## 1. High-Level Overview

AlgoAgent is a **monolithic Django backend** that exposes a REST API consumed by a React SPA (frontend). The core purpose is AI-powered trading strategy creation and backtesting. CPU-intensive work (LLM calls, code execution, backtests) runs asynchronously via Celery. Real-time streaming of backtest data is delivered through a WebSocket consumer.

```
+----------------+     HTTPS REST      +----------------------+
|                | ------------------> |                      |
|  React/Vite    |                     |   Django (Daphne)    |
|  Frontend      | <------------------ |   Port 8000          |
|  (Algo/)       |     JSON responses  |                      |
|                |                     |   + Django Channels  |
|  Port 8081     | === WebSocket ====> |   ws/backtest/stream |
+----------------+                     +----------+-----------+
                                                   |
                           +---------------+       |  enqueue tasks
                           |               |       |
                           |    Redis      | <-----+
                           |    (broker)   |
                           |               |
                           +-------+-------+
                                   |  dequeue
                           +-------v-------+
                           |               |
                           |  Celery       |
                           |  Worker       |
                           |               |
                           +-------+-------+
                                   |
                  +----------------+----------------+
                  |                                 |
         +--------v--------+             +----------v--------+
         |  AI Generation  |             |  Backtest Runner  |
         |  (Backtest/)    |             |  (backtest_api)   |
         |  Gemini LLM     |             |  backtesting.py   |
         +-----------------+             +-------------------+
                  |                                 |
                  +----------------+----------------+
                                   |
                           +-------v-------+
                           |               |
                           |  SQLite /     |
                           |  PostgreSQL   |
                           |               |
                           +---------------+
```

---

## 2. Django Application Structure

The project is a single Django project (`algoagent_api`) containing six apps. Each app owns its models, serializers, views, and URL routes.

```
algoagent_api/          # Project config (settings, root URLs, Celery, ASGI/WSGI)
auth_api/               # Users, JWT auth, Google OAuth, profiles, AI chat sessions
data_api/               # Symbols, OHLCV market data, indicators, caching
strategy_api/           # Strategies, AI generation, validation, templates, bot perf
backtest_api/           # Backtest configs, runs, results, trades, alerts
trading/                # WebSocket consumer — real-time backtest streaming
workflows_api/          # Stub (currently returns empty list at GET /api/workflows/)
```

**Core Python library (not a Django app):**

```
Backtest/               # AI agent, strategy generator, executor, error fixer, broker
Strategy/               # CLI tools, validator, integrator (used by Backtest/)
Data/                   # Data ingestion, indicator registry
```

---

## 3. URL Routing Map

Root router (`algoagent_api/urls.py`) mounts each app at a prefix:

```
/admin/                         Django admin panel
/api/                           API root (returns link index)
/api/auth/                      → auth_api.urls
/api/data/                      → data_api.urls
/api/strategies/                → strategy_api.urls
/api/backtests/                 → backtest_api.urls
/api/workflows/                 → workflows_api.urls
/api/production/                → algoagent_api.production_api_urls
/api/jobs/<task_id>/            Generic Celery job status endpoint
/api/logs/frontend-errors/      Receives error reports from the frontend logger
```

WebSocket routing (`trading/routing.py`):

```
ws://<host>/ws/backtest/stream/ → trading.consumers.BacktestStreamConsumer
```

Full endpoint reference: [API_ENDPOINTS.md](../api/API_ENDPOINTS.md)

---

## 4. Django Apps — Responsibilities

### 4.1 `auth_api`

Handles all identity and session management.

- **Auth:** JWT (access token 1 h, refresh token 7 d, auto-rotation + blacklist). Google OAuth via django-allauth.
- **Models:** `UserProfile`, `AIContext`, `ChatSession`, `ChatMessage`
- **Key views:** `UserRegistrationView`, `UserLoginView`, `google_auth_redirect`, `google_auth_callback`, `ai_chat_view`
- **Profile auto-creation:** A post-save signal on `User` creates a `UserProfile` automatically on registration.

### 4.2 `data_api`

Manages all market data.

- **Models:** `Symbol`, `DataRequest`, `MarketData` (OHLCV candles), `Indicator`, `IndicatorData`, `DataCache`
- **Fetch flow:** Client POSTs to `/api/data/api/fetch_data/` → `DataRequestViewSet` creates a `DataRequest` record → data is fetched (yfinance/external) and stored as `MarketData` rows.
- **Caching:** `DataCache` stores processed datasets by `cache_key` to avoid redundant fetches.

### 4.3 `strategy_api`

The largest app — owns strategy lifecycle from creation to performance tracking.

- **Models:** `Strategy`, `StrategyTemplate`, `StrategyValidation`, `StrategyPerformance`, `StrategyComment`, `StrategyTag`, `StrategyChat`, `StrategyChatMessage`, `BotPerformance`, `LatestBacktestResult`
- **Standard CRUD:** `StrategyViewSet` (full ModelViewSet), `StrategyTemplateViewSet`
- **AI generation:** `StrategyAPIViewSet.generate_strategy_unified()` — the main generation endpoint. Submits a Celery task (`generate_strategy_task`) and returns a `job_id`.
- **Validation:** `StrategyViewSet.validate_strategy()` custom action calls `StrategyValidatorBot`.
- **Bot performance:** `BotPerformanceViewSet` and `LatestBacktestResultViewSet` (read-only) track aggregated execution metrics per strategy.
- **Celery task:** `strategy_api.tasks.generate_strategy_task` — runs the full AI generation + fix loop.

### 4.4 `backtest_api`

Manages backtest execution against historical data.

- **Models:** `BacktestConfig`, `BacktestRun`, `BacktestResult`, `Trade`, `BacktestAlert`
- **Run flow:** Client POSTs to `/api/backtests/api/run_backtest/` → creates `BacktestRun` with `status=pending` → submits `run_backtest_task` → returns `job_id` → client polls `/api/jobs/<id>/`.
- **Celery task:** `backtest_api.tasks.run_backtest_task` — uses `InteractiveBacktestRunner`, populates `BacktestResult` + `Trade` rows on completion.
- **Custom actions on BacktestRunViewSet:** `result`, `trades`, `alerts`, `cancel`

### 4.5 `trading`

Single WebSocket consumer for real-time backtest streaming.

- **Consumer:** `BacktestStreamConsumer` (AsyncWebsocketConsumer)
  - Accepts WS connection
  - Streams candles and order signals sequentially
  - Calls `pair_fills_to_trades()` to compute round-trip PnL
  - Persists final result to `LatestBacktestResult`
- **Channel layer:** `InMemoryChannelLayer` (dev). Switch to `RedisChannelLayer` for production (config in `CONFIGURATION.md`).

### 4.6 `workflows_api`

Placeholder. Returns `{"workflows": []}` at `GET /api/workflows/`. No models defined.

---

## 5. Cross-Cutting Systems

### 5.1 Authentication & Permissions

```
Request arrives
      |
      v
JWTAuthentication (simplejwt) checks Authorization: Bearer <token>
      |
      | valid           | invalid
      v                 v
  request.user       AnonymousUser
  populated          (AllowAny default → passes; IsAuthenticated → 401)
      |
      v
IsOwner permission: filters querysets to created_by=request.user
```

- Default DRF permission: `AllowAny` (set at framework level)
- Viewsets that contain user data apply `IsAuthenticated` + `IsOwner` explicitly
- Token blacklist: revoked refresh tokens are recorded in `token_blacklist_blacklistedtoken`

### 5.2 Async Job Pattern (Celery)

Every long-running operation follows the same pattern:

```
  Client                     Django View              Celery Worker
    |                             |                        |
    |--POST /api/.../run_X/ ----> |                        |
    |                             |--create DB record      |
    |                             |  status='pending'      |
    |                             |--enqueue task -------> |
    |                             |  return job_id         |
    | <---{ job_id: "abc123" }--- |                        |
    |                             |                   task runs
    |--GET /api/jobs/abc123/ ---> |                        |
    |                             |--AsyncResult.state     |
    |                             |  PROGRESS →            |
    | <---{ state, progress } --- |                        |
    |                             |                   task completes
    |--GET /api/jobs/abc123/ ---> |                        |
    |                             |--AsyncResult.state     |
    |                             |  SUCCESS →             |
    | <---{ state, result } ----- |                        |
```

Task states returned by `/api/jobs/<id>/`:
- `PENDING` — queued, not yet started
- `PROGRESS` — running (includes `current`, `total`, `status` fields)
- `SUCCESS` — done (includes `result` object)
- `FAILURE` — error (includes `error` message)
- `REVOKED` — cancelled

### 5.3 Middleware Stack (in order)

```
1. CorsMiddleware          — CORS headers (must be first)
2. SecurityMiddleware      — HTTPS, HSTS, XSS protection
3. SessionMiddleware       — Session cookie handling
4. CommonMiddleware        — Trailing slash, content-type
5. CsrfViewMiddleware      — CSRF protection
6. AuthenticationMiddleware — request.user population
7. AccountMiddleware       — django-allauth account handling
8. MessageMiddleware       — Django flash messages
9. XFrameOptionsMiddleware — Clickjacking protection
```

### 5.4 Logging

Two rotating log files under `logs/`:

| File | Max size | Backups | Content |
|------|----------|---------|---------|
| `logs/django.log` | 10 MB | 3 | Django application logs |
| `logs/frontend_errors.log` | 5 MB | 5 | Frontend errors (from `/api/logs/frontend-errors/`) |

Console handler also active on both.

---

## 6. The `Backtest/` Library

The `Backtest/` directory is a plain Python package (not a Django app) that contains the core AI and execution machinery. Django apps import from it directly.

```
Backtest/
  ai_developer_agent.py         LangChain agent with Gemini LLM + conversation memory
  gemini_strategy_generator.py  Generates Python strategy code from a natural language prompt
  bot_executor.py               Executes a strategy file in a venv-isolated subprocess (900 s timeout)
  bot_error_fixer.py            Iterative AI error fixing loop (up to 8 attempts)
  enhanced_error_detector.py    Classifies errors: framework vs bot-code, encoding, filter issues
  code_change_logger.py         Records diffs across fix iterations
  backtesting_adapter.py        Thin wrapper around the backtesting.py library
  sim_broker.py                 Simulated broker used by BacktestStreamConsumer
  bot_dry_runner.py             Pre-execution smoke test
  pre_execution_validator.py    Static validation before running
  strategy_validator.py         Strategy quality checks
  strategy_manager.py           Strategy lifecycle state machine
  metrics_engine.py             Performance metrics (Sharpe, drawdown, win rate, etc.)
  data_loader.py                Fetches and prepares OHLCV data (yfinance)
  canonical_schema_v2.py        Pydantic models: Signal, OrderSide, OrderType, SizeType
  request_router.py             Routes requests to correct LLM provider
  config.py                     Library configuration
  terminal_executor.py          Runs shell commands from within the AI agent loop
  workflow_tracker.py           Workflow state persistence
```

Flow detail: [AI_PIPELINE.md](../AI_PIPELINE.md)

---

## 7. Production API Layer

`/api/production/` endpoints wrap standard CRUD with additional validation and deployment safety:

```
POST /api/production/strategies/validate-schema/   Pydantic schema check
POST /api/production/strategies/validate-code/     Static safety analysis
POST /api/production/strategies/sandbox-test/      Isolated Docker execution
GET  /api/production/strategies/<id>/lifecycle/    Full audit trail
POST /api/production/strategies/<id>/deploy/       Git commit + tag + deploy
POST /api/production/strategies/<id>/rollback/     Revert to previous Git tag
```

These views (`ProductionStrategyViewSet`) use:
- `canonical_schema_v2` — Pydantic runtime validation
- `output_validator` — dangerous pattern detection
- `sandbox_orchestrator` — sandboxed execution with resource limits
- `git_patch_manager` — version-controlled deployment

See [PRODUCTION_API_GUIDE.md](../api/PRODUCTION_API_GUIDE.md).

---

## 8. Frontend Integration

The React frontend (in `Algo/`) communicates with this backend exclusively via:

1. **HTTP REST** — all standard operations
2. **WebSocket** — real-time backtest streaming at `ws://<host>/ws/backtest/stream/`

Key frontend patterns:
- JWT stored in `localStorage` (`access_token`, `refresh_token`)
- All authenticated requests include `Authorization: Bearer <access_token>`
- 401 responses trigger a global session expiration handler → redirect to `/login`
- Long-running operations use the Celery job polling pattern via `jobPoller.ts`
- Dual AI provider support: Copilot and Gemini, both routing through `generate_strategy_unified`

CORS is configured to allow:
- `http://localhost:8081` (local frontend dev)
- `http://localhost:5173` (Vite dev server)
- `https://algo-rho.vercel.app` (production)
- `https://*.algoai.biz` (production custom domain)

---

## 9. Data Flow Example: Strategy Generation

```
User types "Create a MACD crossover strategy for BTC"
                    |
           POST /api/strategies/api/generate_strategy_unified/
           Body: { description, ai_provider, auto_fix, max_fix_attempts }
                    |
           StrategyAPIViewSet.generate_strategy_unified()
                    |
           Celery task: generate_strategy_task(description, user_id, ...)
                    |
           Returns: { job_id: "xyz" }  ← client begins polling
                    |
           ========= Inside Celery Worker =========
                    |
           GeminiStrategyGenerator.generate(description)
                    |
           Python strategy code produced
                    |
           BotExecutor.execute(code_file)   ← runs in .venv subprocess
                    |
           ┌── success? ──────────────────────────────────┐
           |   YES                        NO               |
           |   metrics extracted          BotErrorFixer    |
           |   Strategy saved to DB       .fix(error_log)  |
           |   LatestBacktestResult       repeat up to     |
           |   created                    max_fix_attempts |
           └──────────────────────────────────────────────┘
                    |
           GET /api/jobs/xyz/  → { state: "SUCCESS", result: { strategy_id, metrics } }
```

See [AI_PIPELINE.md](../AI_PIPELINE.md) for the complete fix-loop internals.

---

## 10. Dependency Summary

| Package | Version | Purpose |
|---------|---------|---------|
| Django | >=4.2, <5.0 | Web framework |
| djangorestframework | >=3.14 | REST API |
| djangorestframework-simplejwt | >=5.3 | JWT auth |
| django-allauth | >=0.57 | Google OAuth |
| django-cors-headers | >=4.3 | CORS |
| channels | >=4.0 | WebSockets |
| daphne | >=4.0 | ASGI server |
| celery | >=5.3 | Task queue |
| redis | >=5.0 | Celery broker |
| django-celery-results | >=2.5 | Task result storage |
| psycopg2-binary | >=2.9 | PostgreSQL driver |
| google-generativeai | >=0.3 | Gemini LLM |
| langchain | >=0.1 | LLM orchestration |
| backtesting | — | Backtesting engine |
| pandas | >=2.1 | Data analysis |
| numpy | >=1.26 | Numerical computing |
