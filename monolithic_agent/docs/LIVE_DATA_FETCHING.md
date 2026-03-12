# Live Data Fetching Integration

## Overview

The Live Data Fetching system enables **on-demand and scheduled real-time data acquisition** from TradingView for your trading bots. Fresh market bars can be fetched at specific times, automatically merged into the local warehouse, and made immediately available to your backtesting strategies—without modifying any bot code.

**Key features:**
- ✅ Fetch fresh OHLCV bars from TradingView using `tvDatafeed`
- ✅ Automatically strip incomplete (currently-forming) bars
- ✅ Merge into local warehouse CSVs with deduplication
- ✅ Scheduled refresh via cron-based APScheduler
- ✅ On-demand refresh via REST API
- ✅ Zero changes to existing bot/strategy code

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Django Application                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  REST API Layer (live_api/views.py)                          │
│  ├─ POST /api/live/data/refresh/      (on-demand fetch)      │
│  ├─ GET  /api/live/data/status/       (warehouse freshness)  │
│  ├─ POST /api/live/scheduler/activate/   (register cron job) │
│  ├─ POST /api/live/scheduler/deactivate/ (remove cron job)   │
│  └─ GET  /api/live/scheduler/jobs/    (list active jobs)     │
│                                                               │
│  APScheduler (live_api/scheduler.py)                         │
│  └─ Background cron-based warehouse refresh engine           │
│                                                               │
│  Data Fetcher (Live/live_data_fetcher.py)                    │
│  ├─ tvDatafeed integration → fetch fresh bars                │
│  ├─ Incomplete bar stripping logic                           │
│  └─ Warehouse CSV upsert (deduplication, merge)              │
│                                                               │
│  Warehouse (Data/data/*.csv)                                 │
│  └─ Flat CSVs: eurusd_1h.csv, aapl_1d.csv, ...              │
│                                                               │
│  Backtesting Pipeline (Backtest/data_loader.py)              │
│  └─ Reads warehouse → feeds bots (no changes needed)         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Concepts

### 1. Incomplete Bar Stripping

**Problem:** tvDatafeed always returns the currently-forming bar as the last row.

**Example (1h interval at 08:25 UTC):**
```
Raw tvDatafeed result:
  07:00 ✓ CLOSED (00:00–08:00)
  08:00 ✗ OPEN   (08:00–09:00, still forming)

After strip:
  07:00 ✓ CLOSED (latest complete bar)
```

**How it works:**

1. **Unconditional strip** — Always remove `df.iloc[-1]` (tvDatafeed's convention)
2. **Verify new last bar** — Calculate `bar_open + interval_duration` and check if it's past current UTC time
   - If `08:00 + 1h = 09:00 > 08:25 (now)` → still incomplete → strip again

**Result:** Only closed bars are added to the warehouse.

### 2. Cron Scheduling (APScheduler)

Jobs fire at the **close of each bar period** + 1–2 minutes buffer for TradingView propagation:

| Interval | Cron Schedule | Example |
|----------|---------------|---------| 
| `1m` | Every minute | Fires at :00, :01, :02, ... |
| `5m` | `:01, :06, :11, :16, :21, :26, :31, :36, :41, :46, :51, :56` | At minute 1, 6, 11, etc. |
| `15m` | `:01, :16, :31, :46` | Four times per hour |
| `30m` | `:01, :31` | Twice per hour |
| `1h` | `HH:01` | At minute 1 of every hour |
| `4h` | `00:01, 04:01, 08:01, 12:01, 16:01, 20:01 UTC` | Six times daily |
| `1d` | `00:02 UTC` | Once per day |
| `1w` | `Monday 00:05 UTC` | Once per week |

All times are **UTC**.

### 3. Warehouse Schema

**File naming:** `Data/data/{symbol_lower}_{interval}.csv`

**Column format (lowercase, matches tvDatafeed output):**
```csv
datetime,symbol,open,high,low,close,volume
2026-03-11 05:00:00,EURUSD,1.1050,1.1065,1.1040,1.1055,150000
2026-03-11 06:00:00,EURUSD,1.1055,1.1070,1.1050,1.1062,160000
```

The `Backtest/data_loader.py` automatically normalizes these to proper case (`Open`, `High`, etc.) when loading for strategies.

---

## Installation

### 1. Add Dependencies

APScheduler is already installed in the venv. Confirm:
```bash
pip list | grep -i apscheduler
# Output: apscheduler 3.11.2
```

If missing:
```bash
pip install "apscheduler>=3.10.0"
```

### 2. Verify Django Configuration

The following changes are already applied:

**`algoagent_api/settings.py`** — `live_api` added to `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    # ...
    'live_api',  # Live trading data fetching & scheduler
]
```

**`algoagent_api/urls.py`** — Route added:
```python
urlpatterns = [
    # ...
    path('api/live/', include('live_api.urls')),
]
```

**`requirements.txt`** — APScheduler added:
```
apscheduler>=3.10.0
```

### 3. Verify Installation

```bash
cd C:\Users\nyaga\Documents\AlgoAgent\monolithic_agent
python -c "
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'algoagent_api.settings'
import django
django.setup()
from Live.live_data_fetcher import LiveDataFetcher
from live_api.scheduler import get_scheduler
print('✓ All modules load successfully')
"
```

---

## API Reference

### 1. On-Demand Data Refresh

**Endpoint:** `POST /api/live/data/refresh/`

Fetch fresh bars from TradingView and upsert them into the warehouse immediately.

**Request:**
```json
{
  "symbol": "EURUSD",
  "exchange": "FX",
  "interval": "1h",
  "n_bars": 500
}
```

**Parameters:**
| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `symbol` | string | ✓ | — | Trading symbol (e.g., `EURUSD`, `AAPL`) |
| `exchange` | string | ✓ | — | Exchange per tvDatafeed (e.g., `FX`, `NASDAQ`, `BITSTAMP`) |
| `interval` | string | ✓ | — | Timeframe (e.g., `1h`, `4h`, `1d`) |
| `n_bars` | int | ✗ | 500 | Bars to fetch (max 4000) |

**Response (200 OK):**
```json
{
  "symbol": "EURUSD",
  "exchange": "FX",
  "interval": "1h",
  "warehouse_path": "/home/.../Data/data/eurusd_1h.csv",
  "new_rows": 42,
  "updated_rows": 3,
  "total_rows": 3847,
  "latest_bar": "2026-03-11T07:00:00+00:00",
  "fetch_time_utc": "2026-03-11T08:25:17.334521+00:00",
  "status": "ok",
  "message": "42 new bars added, 3 existing bars refreshed."
}
```

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/api/live/data/refresh/ \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "EURUSD",
    "exchange": "FX",
    "interval": "1h",
    "n_bars": 500
  }'
```

---

### 2. Warehouse Status (No Fetch)

**Endpoint:** `GET /api/live/data/status/?symbol=EURUSD&interval=1h`

Return freshness info for a warehouse file without fetching.

**Query Parameters:**
- `symbol` (required) — Trading symbol
- `interval` (required) — Timeframe

**Response:**
```json
{
  "symbol": "EURUSD",
  "interval": "1h",
  "warehouse_path": "/home/.../Data/data/eurusd_1h.csv",
  "exists": true,
  "total_rows": 3805,
  "latest_bar": "2026-03-11T07:00:00+00:00",
  "oldest_bar": "2024-09-01T00:00:00+00:00",
  "stale_minutes": 85,
  "status": "ok"
}
```

**Example (cURL):**
```bash
curl -X GET "http://localhost:8000/api/live/data/status/?symbol=EURUSD&interval=1h" \
  -H "Authorization: Bearer <your_token>"
```

---

### 3. Activate Scheduled Refresh

**Endpoint:** `POST /api/live/scheduler/activate/`

Register a recurring cron-based warehouse refresh for a symbol/interval feed.

The scheduler will automatically fire at the close of each bar period and fetch fresh data.

**Request:**
```json
{
  "symbol": "EURUSD",
  "exchange": "FX",
  "interval": "1h",
  "n_bars": 500
}
```

**Response (200 OK):**
```json
{
  "status": "activated",
  "job_id": "live_feed__EURUSD__FX__1h",
  "symbol": "EURUSD",
  "exchange": "FX",
  "interval": "1h",
  "n_bars": 500,
  "cron": {
    "minute": "1"
  },
  "next_run_utc": "2026-03-11T09:01:00+00:00"
}
```

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/api/live/scheduler/activate/ \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "EURUSD",
    "exchange": "FX",
    "interval": "1h",
    "n_bars": 500
  }'
```

---

### 4. Deactivate Scheduled Refresh

**Endpoint:** `POST /api/live/scheduler/deactivate/`

Remove a previously activated refresh job.

**Request:**
```json
{
  "symbol": "EURUSD",
  "exchange": "FX",
  "interval": "1h"
}
```

**Response:**
```json
{
  "status": "deactivated",
  "job_id": "live_feed__EURUSD__FX__1h"
}
```

---

### 5. List Active Jobs

**Endpoint:** `GET /api/live/scheduler/jobs/`

List all currently scheduled refresh jobs and scheduler state.

**Response:**
```json
{
  "is_running": true,
  "jobs": [
    {
      "job_id": "live_feed__EURUSD__FX__1h",
      "name": "EURUSD 1h warehouse refresh",
      "next_run_utc": "2026-03-11T09:01:00+00:00"
    },
    {
      "job_id": "live_feed__AAPL__NASDAQ__1d",
      "name": "AAPL 1d warehouse refresh",
      "next_run_utc": "2026-03-12T00:02:00+00:00"
    }
  ]
}
```

---

## Usage Examples

### Example 1: Manual On-Demand Refresh

Fetch EURUSD 1h data right now:

```python
import requests

url = "http://localhost:8000/api/live/data/refresh/"
headers = {"Authorization": f"Bearer {your_token}"}
payload = {
    "symbol": "EURUSD",
    "exchange": "FX",
    "interval": "1h",
    "n_bars": 500
}

response = requests.post(url, json=payload, headers=headers)
result = response.json()

print(f"Status: {result['status']}")
print(f"New bars: {result['new_rows']}")
print(f"Latest bar: {result['latest_bar']}")
```

### Example 2: Enable Automatic Hourly Refresh

Set up EURUSD to refresh automatically every hour:

```python
import requests

url = "http://localhost:8000/api/live/scheduler/activate/"
headers = {"Authorization": f"Bearer {your_token}"}
payload = {
    "symbol": "EURUSD",
    "exchange": "FX",
    "interval": "1h",
    "n_bars": 500
}

response = requests.post(url, json=payload, headers=headers)
result = response.json()

print(f"Activated: {result['job_id']}")
print(f"Next refresh: {result['next_run_utc']}")
```

From now on, the warehouse will automatically refresh at HH:01 UTC every hour (starting the next hour).

### Example 3: Multi-Symbol Setup

Enable scheduled refresh for multiple feeds:

```python
import requests

feeds = [
    {"symbol": "EURUSD", "exchange": "FX", "interval": "1h"},
    {"symbol": "GBPUSD", "exchange": "FX", "interval": "4h"},
    {"symbol": "AAPL", "exchange": "NASDAQ", "interval": "1d"},
    {"symbol": "BTCUSD", "exchange": "BITSTAMP", "interval": "4h"},
]

headers = {"Authorization": f"Bearer {your_token}"}

for feed in feeds:
    response = requests.post(
        "http://localhost:8000/api/live/scheduler/activate/",
        json=feed,
        headers=headers
    )
    print(f"✓ {feed['symbol']} {feed['interval']}: {response.json()['status']}")
```

### Example 4: Check Warehouse Freshness

Before running a backtest, verify that your data is recent:

```python
import requests
from datetime import datetime, timedelta, timezone

headers = {"Authorization": f"Bearer {your_token}"}

response = requests.get(
    "http://localhost:8000/api/live/data/status/?symbol=EURUSD&interval=1h",
    headers=headers
)
status = response.json()

if not status["exists"]:
    print("❌ Warehouse file does not exist")
    exit(1)

stale_minutes = status["stale_minutes"]
if stale_minutes > 120:  # Older than 2 hours
    print(f"⚠️ Data is stale ({stale_minutes} minutes old)")
    # Trigger an immediate refresh
    requests.post(
        "http://localhost:8000/api/live/data/refresh/",
        json={"symbol": "EURUSD", "exchange": "FX", "interval": "1h"},
        headers=headers
    )
else:
    print(f"✓ Data is fresh ({stale_minutes} minutes old)")

print(f"Latest bar: {status['latest_bar']}")
print(f"Total rows: {status['total_rows']}")
```

---

## Supported Symbols & Exchanges

The live fetcher supports any symbol/exchange combination that **tvDatafeed** supports. Common examples:

### Equities (NASDAQ, NYSE, etc.)
- `symbol`: `AAPL`, `MSFT`, `TSLA`, `NVDA`, `GOOGL`, `AMZN`
- `exchange`: `NASDAQ`

### Forex (FX)
- `symbol`: `EURUSD`, `GBPUSD`, `USDJPY`, `AUDUSD`
- `exchange`: `FX`

### Cryptocurrencies (Bitstamp, Coinbase)
- `symbol`: `BTCUSD`, `ETHUSD`
- `exchange`: `BITSTAMP`

### Commodities (TradingView)
- `symbol`: `XAUUSD` (Gold), `XAGUSD` (Silver), `XPTUSD` (Platinum)
- `exchange`: `TVC`

### Indices
- `symbol`: `SPY` (S&P 500 ETF), `QQQ` (NASDAQ-100 ETF)
- `exchange`: `AMEX` or `NASDAQ`

**Note:** Verify the exact symbol/exchange spelling with TradingView's website before using.

---

## Configuration

### LiveDataFetcher Defaults

**File:** `Live/live_data_fetcher.py`

```python
MAX_BARS = 4000  # tvDatafeed hard limit

INTERVAL_MINUTES = {
    '1m': 1,
    '5m': 5,
    '15m': 15,
    '30m': 30,
    '1h': 60,
    '4h': 240,
    '1d': 1440,
    '1w': 10080,
}

WAREHOUSE_DIR = Path(__file__).parent.parent / 'Data' / 'data'
```

### Scheduler Configuration

**File:** `live_api/scheduler.py`

The scheduler uses APScheduler with:
- **Timezone:** UTC
- **Backend:** In-process memory jobstore (jobs lost on server restart)
- **Coalesce:** True (merge missed runs into one)
- **Max instances:** 1 per job (no overlapping runs)
- **Misfire grace time:** 120 seconds

To persist jobs across restarts, modify `algoagent_api/settings.py`:
```python
APSCHEDULER_JOBSTORES = {
    'default': {
        'type': 'sqlalchemy',
        'url': 'sqlite:///live_jobs.db'
    }
}
```

---

## Troubleshooting

### Issue: "tvDatafeed is not installed"

**Solution:**
```bash
pip install tvDatafeed
```

Confirm:
```bash
python -c "from tvDatafeed import TvDatafeed; print('OK')"
```

---

### Issue: "No data returned from tvDatafeed"

**Causes:**
1. Symbol/exchange spelling is incorrect
2. Market is closed
3. TradingView's API is temporarily unavailable

**Debug:**
```bash
python -c "
from tvDatafeed import TvDatafeed, Interval
tv = TvDatafeed()
data = tv.get_hist('EURUSD', 'FX', Interval.in_1_hour, 10)
print(data)
"
```

---

### Issue: "Scheduler is not running"

Check if the scheduler auto-starts:

```bash
python -c "
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'algoagent_api.settings'
os.environ['RUN_MAIN'] = 'true'  # Simulate runserver
import django
django.setup()
from live_api.scheduler import get_scheduler
sched = get_scheduler()
print('Scheduler running:', sched.is_running)
"
```

**Note:** The scheduler **only** auto-starts when `RUN_MAIN=true` (i.e., during `python manage.py runserver`). For production (gunicorn, etc.), explicitly start it or use Celery-Beat.

**To start manually:**
```python
from live_api.scheduler import get_scheduler
get_scheduler().start()
```

---

### Issue: "Warehouse file not found"

The warehouse file is created automatically on first refresh. If it doesn't exist:

1. **Trigger an on-demand refresh:**
   ```bash
   POST /api/live/data/refresh/ 
   {"symbol": "EURUSD", "exchange": "FX", "interval": "1h"}
   ```

2. **Verify the file was created:**
   ```bash
   ls -lh Data/data/eurusd_1h.csv
   ```

3. **If still missing, check permissions:**
   ```bash
   ls -ld Data/data/
   # Should show: drwxr-xr-x (755)
   ```

---

### Issue: "Incomplete bars appearing in backtest"

This shouldn't happen if the incomplete bar stripping logic is working. Debug:

```python
from Live.live_data_fetcher import LiveDataFetcher
fetcher = LiveDataFetcher()

# Check the latest fetched bars
result = fetcher.refresh("EURUSD", "FX", "1h")
print(result["latest_bar"])  # Should be a CLOSED bar

# Inspect the warehouse
import pandas as pd
df = pd.read_csv("Data/data/eurusd_1h.csv")
print(df.tail(3))  # Last 3 bars
```

If the latest bar is still forming (close time > current UTC time), the stripping logic may have failed. Report in logs.

---

## Integration with Backtesting

**No changes needed!** The existing `Backtest/data_loader.py` automatically picks up fresh warehouse data.

**Workflow:**
1. Activate scheduled refresh for `EURUSD 1h`
2. Scheduler fires every hour at HH:01 → fetches fresh bars → updates `Data/data/eurusd_1h.csv`
3. Run your backtest for EURUSD with `interval=1h`
4. `Backtest/data_loader.py::load_market_data()` loads from warehouse → includes the fresh bars
5. Your strategy sees up-to-date data ✓

---

## Performance Considerations

### Fetch Size

- **Smaller fetches (e.g., `n_bars=100`):** Faster, less data transfer
- **Larger fetches (e.g., `n_bars=4000`):** Slower, but ensures a complete history on first activation

**Recommendation:** Use `n_bars=500` for balance.

### Warehouse Size

Warehouse CSVs grow over time. Monitor:
```bash
du -sh Data/data/
```

Clean up old data if needed (e.g., keep only 2 years):
```python
import pandas as pd
df = pd.read_csv("Data/data/eurusd_1h.csv")
df['datetime'] = pd.to_datetime(df['datetime'])
cutoff = pd.Timestamp.now() - pd.Timedelta(days=730)
df_recent = df[df['datetime'] >= cutoff]
df_recent.to_csv("Data/data/eurusd_1h.csv", index=False)
```

### Scheduler Load

With many active feeds, the scheduler processes them sequentially. High-frequency (1m) feeds may queue up. Monitor in logs:
```
[LiveScheduler] Scheduled refresh → EURUSD FX 1m
[LiveScheduler] Scheduled refresh → GBPUSD FX 1m
...
```

If latency is excessive, reduce `n_bars` or increase the interval gracetime.

---

## Logging

The live_api module logs to `logging.getLogger('live_api')`. To capture logs:

**`logging.conf` (or settings.py):**
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'logs/live_api.log',
        },
    },
    'loggers': {
        'live_api': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    },
}
```

---

## Summary

| Feature | Status |
|---------|--------|
| On-demand data refresh | ✅ Fully implemented |
| Scheduled (cron) refresh | ✅ APScheduler-based |
| Incomplete bar stripping | ✅ Automatic |
| Warehouse CSV management | ✅ Auto-create, deduplicate, merge |
| REST API endpoints | ✅ 5 endpoints (fetch, status, activate, deactivate, list jobs) |
| Authentication | ✅ Required (`IsAuthenticated`) |
| Backtest integration | ✅ Zero bot changes needed |
| tvDatafeed support | ✅ All symbols/exchanges |
| Auto-start on `python manage.py runserver` | ✅ Via `apps.py::ready()` |

---

## Next Steps

1. **Test the endpoints** using the examples above
2. **Activate scheduled feeds** for your trading symbols
3. **Run backtests** to verify fresh data is picked up
4. **Monitor warehouse growth** and archive old data if needed
5. **(Future)** Integrate with bot execution engine to trigger trades on live signals

---

## Files Modified/Created

| File | Type | Purpose |
|------|------|---------|
| `Live/live_data_fetcher.py` | NEW | Core data fetcher engine |
| `live_api/__init__.py` | NEW | Empty init (Django convention) |
| `live_api/apps.py` | NEW | AppConfig with scheduler auto-start |
| `live_api/scheduler.py` | NEW | APScheduler cron engine |
| `live_api/views.py` | NEW | 5 REST API views |
| `live_api/urls.py` | NEW | URL routing |
| `Live/__init__.py` | MODIFIED | Wrapped MT5 imports in try/except |
| `algoagent_api/settings.py` | MODIFIED | Added `live_api` to `INSTALLED_APPS` |
| `algoagent_api/urls.py` | MODIFIED | Added `path('api/live/', include(...))` |
| `requirements.txt` | MODIFIED | Added `apscheduler>=3.10.0` |

---

**Version:** 1.0.0  
**Last Updated:** March 11, 2026  
**Author:** AlgoAgent Live Data Fetching System
