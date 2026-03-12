# Quick Reference

**Last Updated:** March 10, 2026
**See also:** [Full API Docs](../api/API_ENDPOINTS.md) | [Architecture](../architecture/ARCHITECTURE.md) | [Configuration](../CONFIGURATION.md)

---

## Key URLs

| Environment | URL |
|-------------|-----|
| Local backend | `http://localhost:8000/api/` |
| Local frontend | `http://localhost:8081/` |
| Production backend | `https://chiqoke254.pythonanywhere.com/api/` |
| Production frontend | `https://algo-rho.vercel.app` / `https://algoai.biz` |
| Admin panel | `http://localhost:8000/admin/` |
| WebSocket | `ws://localhost:8000/ws/backtest/stream/` |

---

## File Layout

```
AlgoAgent/
    .env                          <-- secrets (gitignored)
    .env.example                  <-- env template
    monolithic_agent/
        algoagent_api/            <-- Django project settings & root URLs
        auth_api/                 <-- JWT auth, UserProfile, AIContext, ChatSession
        data_api/                 <-- Symbol/MarketData CRUD, indicator registry
        strategy_api/             <-- Strategy CRUD, AI generation, validation, production endpoints
        backtest_api/             <-- BacktestConfig/Run/Result CRUD, async backtest runner
        trading/                  <-- WebSocket consumer for live backtest streaming
        workflows_api/            <-- Stub app (reserved)
        Backtest/                 <-- AI pipeline library
            ai_developer_agent.py
            gemini_strategy_generator.py
            bot_executor.py
            bot_error_fixer.py
            backtesting_adapter.py
            canonical_schema_v2.py
            metrics_engine.py
            sim_broker.py
        docs/                     <-- This documentation
        manage.py
        requirements.txt
        db.sqlite3                <-- SQLite dev database
        logs/
```

---

## Authentication

All protected endpoints require `Authorization: Bearer <access_token>`.

### Login (PowerShell)
```powershell
$r = Invoke-RestMethod -Method POST http://localhost:8000/api/auth/login/ `
  -ContentType "application/json" `
  -Body '{"username":"youruser","password":"yourpass"}'
$TOKEN = $r.access
```

### Login (curl)
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"youruser","password":"yourpass"}' | jq -r .access)
```

### Use token
```powershell
Invoke-RestMethod http://localhost:8000/api/strategies/ `
  -Headers @{Authorization="Bearer $TOKEN"}
```

### Refresh token
```powershell
$r = Invoke-RestMethod -Method POST http://localhost:8000/api/auth/token/refresh/ `
  -ContentType "application/json" `
  -Body "{`"refresh`":`"$REFRESH_TOKEN`"}"
$TOKEN = $r.access
```

Tokens expire: access = **1 hour**, refresh = **7 days**.

---

## Common Operations

### Get current user
```powershell
Invoke-RestMethod http://localhost:8000/api/auth/user/me/ `
  -Headers @{Authorization="Bearer $TOKEN"}
```

### List strategies
```powershell
Invoke-RestMethod http://localhost:8000/api/strategies/strategies/ `
  -Headers @{Authorization="Bearer $TOKEN"}
```

### Generate a strategy (AI)
```powershell
$body = @{
    description = "RSI mean-reversion strategy on AAPL"
    symbols     = @("AAPL")
    timeframe   = "1d"
    period      = "1y"
} | ConvertTo-Json

$r = Invoke-RestMethod -Method POST `
  http://localhost:8000/api/strategies/generate_strategy_unified/ `
  -Headers @{Authorization="Bearer $TOKEN"} `
  -ContentType "application/json" -Body $body

$JOB_ID = $r.job_id
```

### Poll job to completion
```powershell
do {
    Start-Sleep 3
    $status = Invoke-RestMethod "http://localhost:8000/api/jobs/$JOB_ID/" `
      -Headers @{Authorization="Bearer $TOKEN"}
    Write-Host $status.status
} while ($status.status -notin @("SUCCESS","FAILURE"))

$status.result
```

### Run a backtest
```powershell
$body = @{
    strategy_id  = 42
    symbols      = @("AAPL","MSFT")
    start_date   = "2023-01-01"
    end_date     = "2024-01-01"
    initial_capital = 10000
} | ConvertTo-Json

$r = Invoke-RestMethod -Method POST `
  http://localhost:8000/api/backtests/run_backtest/ `
  -Headers @{Authorization="Bearer $TOKEN"} `
  -ContentType "application/json" -Body $body

$JOB_ID = $r.job_id
# then poll as above
```

### Fetch market data for a symbol
```powershell
Invoke-RestMethod `
  "http://localhost:8000/api/data/market-data/?symbol=AAPL&period=1y&interval=1d" `
  -Headers @{Authorization="Bearer $TOKEN"}
```

---

## Async Job States

All long-running operations (strategy generation, backtests) return a `job_id` immediately.

`GET /api/jobs/<job_id>/`

| `status` | Meaning |
|----------|---------|
| `PENDING` | Queued, not started |
| `STARTED` | Worker picked up |
| `PROGRESS` | Running — `result` may include `progress` (0–100) |
| `SUCCESS` | Done — `result` has output data |
| `FAILURE` | Failed — `result.error` has message |

---

## Django Management Commands

```powershell
cd AlgoAgent/monolithic_agent

# Apply migrations
python manage.py migrate

# Create a superuser
python manage.py createsuperuser

# Open Django shell
python manage.py shell

# Start Django dev server
python manage.py runserver 0.0.0.0:8000

# Collect static files (production)
python manage.py collectstatic

# Backup database
python manage.py dumpdata > backup.json

# Restore database
python manage.py loaddata backup.json
```

---

## Celery Commands

```powershell
cd AlgoAgent/monolithic_agent

# Start worker
celery -A algoagent_api worker --loglevel=info

# Check active tasks
celery -A algoagent_api inspect active

# Purge the queue
celery -A algoagent_api purge

# Run with concurrency limit (useful on low-memory machines)
celery -A algoagent_api worker --concurrency=2 --loglevel=info
```

---

## Test Commands

```powershell
cd AlgoAgent/monolithic_agent

# All tests
pytest tests/ -v

# One file
pytest tests/test_auth_flow.py -v

# One test by name
pytest tests/ -k "test_create_strategy" -v

# With coverage
pytest tests/ --cov=strategy_api --cov-report=term-missing
```

---

## Common Response Shapes

### Paginated list
```json
{
  "count": 42,
  "next": "http://.../?page=2",
  "previous": null,
  "results": [ ... ]
}
```

### Async job response
```json
{
  "job_id": "abc-123",
  "status": "queued"
}
```

### Error response
```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

## Production API Endpoints Quick Map

| Short name | Full path |
|------------|-----------|
| validate-schema | `POST /api/production/validate-schema/` |
| validate-code | `POST /api/production/validate-code/` |
| sandbox-test | `POST /api/production/sandbox-test/` |
| lifecycle | `POST /api/production/lifecycle/` |
| deploy | `POST /api/production/deploy/` |
| rollback | `POST /api/production/rollback/` |

See [Production API Guide](../api/PRODUCTION_API_GUIDE.md) for full request/response field tables.

---

## Health Checks

```powershell
Invoke-RestMethod http://localhost:8000/api/auth/health/
Invoke-RestMethod http://localhost:8000/api/strategies/health/
Invoke-RestMethod http://localhost:8000/api/data/health/
Invoke-RestMethod http://localhost:8000/api/backtests/health/
```

All return `{ "status": "ok" }` when the app is running normally.
