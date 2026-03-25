# Live Trading Signal Generation Fix

**Date:** March 20, 2026  
**Severity:** Critical — both live bots running for 15+ hours with zero trade signals  
**Status:** Fixed & Deployed  
**Sessions Affected:** Session 5 (Algo, 1d), Session 6 (Trend Follow 1, 1h)

---

## Summary

Both live trading bots were running continuously but producing **zero trade signals** for over 9 hours. Root cause was a two-part bug in `backtesting_bridge.py`: a hard-coded `period='1mo'` combined with a strict `[from_ts, to_ts]` date filter, and a broken order-count check referencing a non-existent `SimBroker.orders` attribute. The fix loads full warehouse history for indicator warmup, applies a safe fallback when no bars fall in the request window, and corrects the order introspection path.

---

## Root Cause Analysis

### Bug 1 — Empty DataFrame After Date Filter

**File:** `Live/backtesting_bridge.py`, line 76–93 (original)

`generate_signals()` loaded data with `period='1mo'`, then immediately filtered to `[from_ts, to_ts]`.

`live_trader.py` passes:
```python
end_time   = datetime.now(timezone.utc)          # e.g. 2026-03-20 10:10 UTC
start_time = end_time - timedelta(days=7)         # e.g. 2026-03-13 10:10 UTC
```

The filter worked correctly in isolation — the warehouse did have bars in that 7-day window. However, the **running process** had loaded the file at session start when `live_trader.py` still contained `timedelta(days=1)` (a prior in-memory version). The 1-day window `[2026-03-19, 2026-03-20]` contained **no closed daily bars** because the latest warehouse bar was `2026-03-18 21:00 UTC`.

Every iteration logged:
```
Loaded 33 rows for EURUSD from warehouse file eurusd_1d.csv
WARNING - No data available for EURUSD in range 2026-03-19 10:10:37+00:00 to 2026-03-20 10:10:37+00:00
```

This is also a structural problem: even with a 7-day window the approach is fragile on weekends or when the warehouse hasn't been refreshed. Daily bars close at 21:00–22:00 UTC; the window `[now-7d, now]` can exclude the latest bar entirely if the bot checks at the wrong time of day.

### Bug 2 — `AttributeError: 'SimBroker' has no attribute 'orders'`

**File:** `Live/backtesting_bridge.py`, line 128 (original)

The signal-detection logic counted orders via:
```python
old_signal_count = len(self.mock_broker.orders)
```

`SimBroker` stores orders inside `self.order_manager.orders` (an `OrderManager` instance). The top-level `.orders` attribute does not exist, raising `AttributeError` on every bar. Because this exception was not caught inside the per-bar loop, the entire `generate_signals()` call crashed silently (the outer `except Exception` in `live_trader._process_symbol` swallowed it and logged "No signals generated").

---

## Fix Applied

**File:** `Live/backtesting_bridge.py`

### Change 1 — Load full history, cap at 500 bars

```python
# Before
df, metadata = load_market_data(
    ticker=symbol,
    indicators=indicators,
    period='1mo',   # too short; combined with date filter → empty
    interval=timeframe
)
df = df[(df.index >= from_ts) & (df.index <= to_ts)]   # strict filter
if df.empty:
    logger.warning(f"No data available for {symbol} ...")
    return pd.DataFrame()

# After
df, metadata = load_market_data(
    ticker=symbol,
    indicators=indicators,
    period='max',   # full warehouse history for indicator warmup
    interval=timeframe
)
if df.empty:
    logger.warning(f"No warehouse data found for {symbol} ({timeframe})")
    return pd.DataFrame()

df = df.tail(500)   # cap at 500 bars to bound memory and runtime
```

### Change 2 — Correct order introspection

```python
# Before (crashes — SimBroker has no .orders attribute)
old_signal_count = len(self.mock_broker.orders)
...
new_signal_count = len(self.mock_broker.orders)
if new_signal_count > old_signal_count:
    latest_order = list(self.mock_broker.orders.values())[-1]
    signal_type = 'BUY' if latest_order['side'] == 'BUY' else 'SELL'
    ...price/action/size via dict access...

# After (uses correct attribute path; Order is a dataclass)
old_order_count = self.mock_broker.order_manager.orders_created
...
new_order_count = self.mock_broker.order_manager.orders_created
if new_order_count > old_order_count:
    all_orders = list(self.mock_broker.order_manager.orders.values())
    latest_order = all_orders[-1]                          # Order dataclass
    signal_type = 'BUY' if latest_order.side == 'BUY' else 'SELL'
    signals_list.append({
        ...
        'price':  latest_order.price or row['Close'],
        'action': latest_order.meta.get('action'),
        'size':   latest_order.size_requested
    })
```

### Change 3 — Post-loop filter with graceful fallback

After running the strategy over all 500 bars, filter the collected signals to the caller's `[from_ts, to_ts]` window. If that window is empty (e.g., no bar closed today yet), fall back to the single most-recent bar's signal so the live trader always receives a result:

```python
signals_df = signals_df[
    (signals_df.index >= from_ts) & (signals_df.index <= to_ts)
]

if signals_df.empty:
    logger.warning(f"No signals in window [{from_ts} → {to_ts}] for {symbol}. "
                   "Falling back to latest bar signal.")
    full_df = pd.DataFrame(signals_list).set_index('timestamp')
    if not full_df.empty:
        signals_df = full_df.iloc[[-1]]
```

---

## Verification

Smoke-tested before deploying by running the bridge directly against the `strategy_5_bd389cee.py` strategy with a 1-day window (worst-case scenario):

```
INFO  - Running strategy over 500 bars for EURUSD
        (signals window: 2026-03-19 10:12 → 2026-03-20 10:12)
INFO  - Loaded 4501 rows from warehouse file eurusd_1d.csv
WARNING - No signals in requested window [...]. Falling back to latest bar.
INFO  - Falling back to latest bar signal: 2026-03-18 21:00:00+00:00 → HOLD

Signals returned: 1
```

Post-restart log confirmation:
```
INFO - Running strategy over 500 bars for BTCUSD
       (signals window: 2026-03-13 10:25 → 2026-03-20 10:25)
INFO - Loaded 4500 rows from warehouse file btcusd_1d.csv
INFO - Returning 6 signals, 0 actionable
INFO - HOLD signal for BTCUSD
```

---

## Session Restart

Both sessions were restarted programmatically via the Django `SessionManager` after the fix was deployed:

| Session | Strategy | Symbols | Timeframe | Old PID | New PID | Status |
|---------|----------|---------|-----------|---------|---------|--------|
| 5 | Algo | EURUSD, BTCUSD, GBPUSD | 1d | 555885 (zombie) | 601567 | RUNNING |
| 6 | Trend Follow 1 | EURUSD, XAUUSD, BTCUSD | 1h | 556816 (dead) | 601608 | RUNNING |

Session 5 had been running since `2026-03-19 18:31` (~16 hours) with zero signals due to these bugs.

### Kill Switch Issue (Session 5)

During shutdown, the expected kill switch at `kill_switches/STOP_5` was ignored because the session's temp `.env` file had been deleted by the deferred-cleanup thread before the OS had flushed the `KILL_SWITCH_FILE` env var into the child process's `os.environ`. The process fell back to the default `EMERGENCY_STOP` filename. Creating `Live/EMERGENCY_STOP` triggered the graceful shutdown successfully.

**Follow-up:** The `session_manager.py` deferred delete should verify the env var was loaded before deleting the temp file, or the kill switch path should be re-propagated via a signal/file outside the env system.

---

## Known Minor Issue

On first iteration after restart, sessions log:

```
sqlite3.IntegrityError: UNIQUE constraint failed: signals.signal_id
```

This occurs because `signal_id = f"{symbol}_{timestamp}"` uses the same latest-bar timestamp that was already logged in the previous session run. The exception is caught and non-fatal. On the second iteration, `is_signal_processed(signal_id)` returns `True` and the duplicate log attempt is skipped entirely. No trading impact.

---

## Files Changed

| File | Change |
|------|--------|
| `Live/backtesting_bridge.py` | Load `period='max'`, cap 500 bars, fix order introspection, add fallback signal |

---

## Infrastructure Notes (from session audit)

| Component | Detail |
|-----------|--------|
| Production path | `/opt/algoagent/AlgoAgent/` |
| Production venv | `/opt/algoagent/venv/` (Python 3.12) |
| MT5 bridge | Wine Flask server, `http://127.0.0.1:5555`, already running |
| Warehouse data | `/opt/algoagent/AlgoAgent/monolithic_agent/Data/data/*.csv` |
| Session logs | `Live/session_logs/session_N.log` |
| Kill switches | `Live/kill_switches/STOP_N` |
| FERNET_KEY | Present in `/etc/algoagent/.env` (earlier note was stale) |
