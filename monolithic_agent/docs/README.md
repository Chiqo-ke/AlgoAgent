# AlgoAgent — System Documentation

**Last Updated:** March 10, 2026
**Status:** Current — reflects live implementation

---

## What is AlgoAgent?

AlgoAgent is an AI-powered algorithmic trading platform. Users describe trading strategies in plain language; the system generates production-quality Python code, backtests it against historical market data, and stores the verified results. It is composed of a Django REST backend (this repository) and a React/Vite frontend ([Algo](../../Algo/)).

---

## Technology Stack

| Layer              | Technology                                           |
|--------------------|------------------------------------------------------|
| Backend framework  | Django 4.2 + Django REST Framework 3.14              |
| Authentication     | JWT (simplejwt) + Google OAuth (allauth)             |
| Task queue         | Celery 5.3 + Redis                                   |
| WebSockets         | Django Channels 4 + Daphne                           |
| Database           | SQLite (dev) / PostgreSQL (prod)                     |
| AI / LLM           | Google Gemini 2.0 Flash via LangChain                |
| Backtesting engine | backtesting.py (kernc/backtesting.py)                |
| Frontend           | React 18, Vite, TypeScript, TanStack Query, shadcn/ui|
| Hosting (prod)     | PythonAnywhere (backend), Vercel (frontend)          |

---

## Documentation Map

Start with **Architecture** to understand the big picture, then go deeper into whichever area you need.

### Core References (current, maintained)

| Document | What it covers |
|----------|----------------|
| [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md) | Component diagram, request lifecycle, all Django apps, Celery pattern, WebSocket streaming |
| [api/API_ENDPOINTS.md](api/API_ENDPOINTS.md) | Every REST endpoint — method, path, auth, request params, response fields |
| [api/PRODUCTION_API_GUIDE.md](api/PRODUCTION_API_GUIDE.md) | Production-hardened endpoints: schema validation, sandboxing, deploy, rollback |
| [DATA_MODELS.md](DATA_MODELS.md) | All Django ORM models across all apps — fields, types, relationships |
| [AI_PIPELINE.md](AI_PIPELINE.md) | End-to-end AI strategy generation flow: prompt → LLM → code → fix loop → execution → DB |
| [CONFIGURATION.md](CONFIGURATION.md) | Environment variables, local dev setup, JWT/CORS settings, Google OAuth |
| [guides/QUICK_REFERENCE.md](guides/QUICK_REFERENCE.md) | Fast-lookup cheat sheet for endpoints, auth, and job polling |

### Historical / Archive (informational, not maintained)

These documents record past implementation decisions, bug fixes, and one-time migrations. They are accurate as of their creation date but may not reflect the current state.

| Folder | Contents |
|--------|----------|
| [archive/](archive/) | Completed migrations, copilot integration, consolidated fix summaries |
| [implementation/](implementation/) | Deep-dives: key rotation, bot execution internals, indicator system, throttling, zero-trades fix |
| [testing/](testing/) | E2E test reports and test index (January 2026) |
| [guides/](guides/) | Bot creation walkthroughs, error prevention, E2E workflow guides |

---

## Quick Start (Local Development)

See [CONFIGURATION.md](CONFIGURATION.md) for the full setup. Minimum steps:

```
# 1. Install dependencies (use the project venv)
pip install -r requirements.txt

# 2. Start Redis (required for Celery)
redis-server

# 3. Run Django on port 8000
python manage.py runserver 0.0.0.0:8000

# 4. Start Celery worker (separate terminal)
celery -A algoagent_api worker --loglevel=info

# 5. Frontend runs separately at http://localhost:8081
#    See Algo/ repository for frontend setup
```

Default backend URL: `http://localhost:8000`
Default frontend URL: `http://localhost:8081`

---

## System Entry Points

| Entry point | Description |
|-------------|-------------|
| `POST /api/auth/login/` | Get JWT access + refresh tokens |
| `POST /api/strategies/api/generate_strategy_unified/` | Main AI strategy generation endpoint |
| `POST /api/backtests/api/run_backtest/` | Run a backtest against historical data |
| `GET /api/jobs/<task_id>/` | Poll any async Celery task for status/result |
| `ws://host/ws/backtest/stream/` | WebSocket for real-time backtest streaming |
| `/admin/` | Django admin panel |

---

## Repository Layout

```
monolithic_agent/
├── algoagent_api/          # Django project settings, root URLs, Celery config, ASGI/WSGI
├── auth_api/               # JWT auth, Google OAuth, user profiles, AI chat sessions
├── data_api/               # Market symbols, OHLCV data, indicators, data cache
├── strategy_api/           # Strategies, AI generation, validation, templates, bot performance
├── backtest_api/           # Backtest configs, runs, results, trades, alerts
├── trading/                # WebSocket consumer for real-time backtest streaming
├── workflows_api/          # Placeholder (stub, currently returns empty list)
├── Backtest/               # Core Python library: AI agent, executor, error fixer, broker
├── Strategy/               # Strategy interaction tools (CLI, validator, integrator)
├── Data/                   # Data ingestion, indicator registry
├── Live/                   # Live trading module (in development)
├── Trade/                  # Trade execution models
├── docs/                   # This documentation
├── tests/                  # Pytest test suite
├── scripts/                # Utility scripts
├── logs/                   # Rotating log files (django.log, frontend_errors.log)
├── manage.py
├── requirements.txt
├── pytest.ini
└── db.sqlite3              # SQLite database (dev)
```

---

## Key Concepts for New Developers

**1. Async Jobs (Celery)**
Long-running tasks (strategy generation, backtests) are offloaded to Celery. The API returns a `job_id` immediately; clients poll `GET /api/jobs/<job_id>/` for progress and results. See [AI_PIPELINE.md](AI_PIPELINE.md) and [api/API_ENDPOINTS.md](api/API_ENDPOINTS.md#async-job-polling).

**2. Owner-Scoped Data**
All querysets filter by `created_by=request.user`. Users only see their own strategies, backtests, and profiles. The `IsOwner` permission class enforces this on detail views.

**3. AI Generation Loop**
Strategy generation is iterative: generate → execute → detect errors → fix (up to 8 attempts) → persist. The entire loop lives in `Backtest/` and is exposed via the `generate_strategy_unified` endpoint. See [AI_PIPELINE.md](AI_PIPELINE.md).

**4. Production vs Standard Endpoints**
`/api/production/` endpoints add Pydantic validation, static safety checks, sandbox execution, lifecycle tracking, and Git-based deployment on top of the standard CRUD endpoints. See [api/PRODUCTION_API_GUIDE.md](api/PRODUCTION_API_GUIDE.md).

**5. WebSocket Streaming**
The `trading` app exposes a WebSocket consumer at `ws/backtest/stream/` that streams candle-by-candle backtest execution in real time, pairing fills into round-trip trades and persisting the final result to `LatestBacktestResult`.
