# MT5 Bridge Service

**Last Updated:** March 25, 2026  
**Scope:** Architecture, file locations, HTTP API reference, startup sequence, watchdog mechanism, credentials, health checks, and integration with the live trader.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [File Locations](#file-locations)
4. [Systemd Services](#systemd-services)
   - [xvfb-99.service](#xvfb-99service)
   - [mt5.service](#mt5service)
   - [mt5_bridge.service](#mt5_bridgeservice)
   - [mt5_algo_watchdog.service](#mt5_algo_watchdogservice)
5. [Startup Sequence](#startup-sequence)
6. [Auto-Initialisation (Background Thread)](#auto-initialisation-background-thread)
7. [Algo Trading Watchdog](#algo-trading-watchdog)
8. [HTTP API Reference](#http-api-reference)
9. [Two MT5 Accounts](#two-mt5-accounts)
10. [Credentials Locations](#credentials-locations)
11. [Integration with live_trader.py](#integration-with-live_traderpy)
12. [Health Checks and Service Management](#health-checks-and-service-management)
13. [Logs](#logs)
14. [Known Limitations](#known-limitations)

---

## Overview

MetaTrader 5's Python package (`MetaTrader5`) is Windows-only. The server runs Linux, so MT5 is run headlessly inside **Wine** on a virtual X11 display. A small **Flask HTTP server** (`mt5_bridge.py`) runs inside the same Wine environment, wrapping all MT5 Python calls and exposing them as a local HTTP API on `127.0.0.1:5555`.

The Django/Celery backend and live trader subprocesses never import `MetaTrader5` directly — they call this bridge via HTTP.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Linux host                                             │
│                                                         │
│  live_trader.py  ──HTTP──►  mt5_bridge.py  (Wine)       │
│  (Python 3.12)              (Python 3.11 inside Wine)   │
│                                    │                    │
│                              terminal64.exe  (Wine)     │
│                                    │                    │
│                              FBS-Demo broker (TCP)      │
└─────────────────────────────────────────────────────────┘
```

All MT5 calls are serialised inside the bridge via `threading.Lock()` because the `MetaTrader5` Python package is not thread-safe. Flask runs in threaded mode, so concurrent HTTP requests queue on that lock.

---

## File Locations

| Component | Path |
|-----------|------|
| Bridge server script | `/home/algoagent/.mt5/drive_c/mt5_bridge/mt5_bridge.py` |
| Bridge log (Wine) | `/home/algoagent/.mt5/drive_c/mt5_bridge/mt5_bridge.log` |
| Algo-trading trigger file | `/home/algoagent/.mt5/drive_c/mt5_bridge/enable_trading.trigger` |
| MT5 terminal binary | `/home/algoagent/.mt5/drive_c/Program Files/MetaTrader 5/terminal64.exe` |
| Wine prefix | `/home/algoagent/.mt5/` |
| Wine Python 3.11 | `C:\users\algoagent\AppData\Local\Programs\Python\Python311\python.exe` (inside Wine) |
| Ensure-algo-trading script | `/opt/algoagent/bin/ensure_algo_trading.sh` |
| Algo watchdog script | `/opt/algoagent/bin/mt5_algo_watchdog.sh` |
| Bridge credentials env | `/etc/algoagent/mt5_credentials.env` |
| Bridge systemd log | `/var/log/mt5/mt5_bridge.log` |
| MT5 terminal systemd log | `/var/log/mt5/mt5.log` |
| Algo watchdog systemd log | `/var/log/mt5/algo_watchdog.log` |
| Bridge connector (Django side) | `monolithic_agent/Live/mt5_bridge_connector.py` |

---

## Systemd Services

Four services cooperate. All run as the `algoagent` user except `xvfb-99.service` (which runs as root/default).

### xvfb-99.service

**Purpose:** Creates virtual X11 display `:99` (headless, 1024×768 16-bit). Wine and `xdotool` both target this display.

```ini
ExecStart=/usr/bin/Xvfb :99 -screen 0 1024x768x16 -nolisten tcp
Restart=always
RestartSec=3
```

### mt5.service

**Purpose:** Runs `terminal64.exe` via Wine in portable mode on display `:99`.

```ini
After=network-online.target xvfb-99.service
Environment=DISPLAY=:99
Environment=WINEPREFIX=/home/algoagent/.mt5
ExecStart=/opt/wine-staging/bin/wine ".../terminal64.exe" /portable
Restart=on-failure
RestartSec=10
```

### mt5_bridge.service

**Purpose:** Starts the Flask HTTP bridge server inside Wine Python 3.11.

Key details:
- `After=xvfb-99.service mt5.service` — waits for MT5 to be up before starting
- `ExecStartPre=/bin/sleep 30` — extra 30-second delay to let `terminal64.exe` fully initialise
- `ExecStartPost=-/opt/algoagent/bin/ensure_algo_trading.sh` — one-shot script to enable Algo Trading after startup
- Loads broker credentials from `EnvironmentFile=/etc/algoagent/mt5_credentials.env`
- On failure, restarts after 15 seconds

```ini
ExecStart=/opt/wine-staging/bin/wine \
  ".../Python311/python.exe" \
  "C:/mt5_bridge/mt5_bridge.py"
StandardOutput=append:/var/log/mt5/mt5_bridge.log
StandardError=append:/var/log/mt5/mt5_bridge.log
```

### mt5_algo_watchdog.service

**Purpose:** Continuously monitors `trade_allowed` and re-enables Algo Trading whenever it drops to `false` (e.g. after MT5 auto-restart or network reconnect).

```ini
After=mt5_bridge.service
ExecStart=/opt/algoagent/bin/mt5_algo_watchdog.sh
Restart=always
RestartSec=10
```

---

## Startup Sequence

```
1. xvfb-99.service   → Virtual display :99 is created
2. mt5.service       → terminal64.exe starts inside Wine on :99
3. mt5_bridge.service
   a. sleep 30       → Wait for MT5 terminal to fully start
   b. Flask starts   → Bridge HTTP server listening on 127.0.0.1:5555
   c. Background thread → _auto_init_worker() retries mt5.initialize() every 30s
   d. ExecStartPost  → ensure_algo_trading.sh waits for init, then sends Ctrl+E if needed
4. mt5_algo_watchdog.service → polls /health + /terminal_info every 5s
```

Total cold-start time to `trade_allowed=True`: typically **60–120 seconds**.

---

## Auto-Initialisation (Background Thread)

When the bridge starts, a daemon thread (`_auto_init_worker`) immediately begins retrying `mt5.initialize()` every 30 seconds until it succeeds. This means:

- The Flask server is immediately reachable (returns 503 via `@require_init` if MT5 is not yet ready)
- No manual call to `POST /initialize` is needed in normal operation
- The `/health` endpoint exposes `init_in_progress: true` while the thread is working

The thread reads credentials from environment variables (injected from `mt5_credentials.env`):

```
MT5_LOGIN     → login ID for auto-init
MT5_PASSWORD  → password
MT5_SERVER    → broker server name
```

If credentials are not set, `mt5.initialize()` is called without auth (relies on the terminal's saved session).

---

## Algo Trading Watchdog

MetaTrader 5 sometimes disables the **Algo Trading** toolbar button after reconnecting to the broker or after a restart. When this happens, `trade_allowed` becomes `false` and all order submissions fail with retcode `10027` (`TRADE_RETCODE_CLIENT_DISABLES_AT`).

The watchdog handles this in two ways:

### 1. Triggered mode (immediate)

When the bridge's `POST /enable_algo_trading` endpoint is called (which the `MT5BridgeConnector` does automatically on startup if `trade_allowed=False`), the bridge writes a trigger file:

```
/home/algoagent/.mt5/drive_c/mt5_bridge/enable_trading.trigger
```

The watchdog script detects this file within 5 seconds (its poll interval), deletes it, and calls `enable_algo_trading()`.

### 2. Periodic mode (background)

Every 5 seconds the watchdog polls `/health` and `/terminal_info`. If the bridge is initialised and `trade_allowed=False`, it calls `enable_algo_trading()`.

### enable_algo_trading() logic

```bash
1. xdotool windowfocus  (focus MT5 window)
2. xdotool key ctrl+e   (MT5 keyboard shortcut to toggle Algo Trading)
3. Wait 2s, check trade_allowed via /terminal_info
4. If still False: xdotool mousemove 289 55 click 1  (click toolbar button at known coordinates)
5. Wait 2s, log final state
```

The coordinates `(289, 55)` are the Algo Trading toolbar button position in a 1024×768 window.

---

## HTTP API Reference

All requests and responses are JSON. Error responses always include `{"error": "..."}`. Endpoints marked with `[init]` return HTTP 503 if MT5 is not initialised.

Base URL: `http://127.0.0.1:5555`

---

### GET /health

Check bridge and MT5 status. Does **not** require MT5 to be initialised.

**Response:**
```json
{
  "status": "ok",
  "initialised": true,
  "init_in_progress": false,
  "mt5_version": [500, 3700, 20]
}
```

---

### POST /initialize `[no init required]`

Explicitly initialise MT5. In normal operation this is not needed (the background thread handles it), but can be called to force a reinit.

**Request body (all optional):**
```json
{
  "path":     "/path/to/terminal64.exe",
  "timeout":  60000,
  "login":    102641850,
  "password": "secret",
  "server":   "FBS-Demo",
  "force":    false
}
```

**Responses:**
- `200 {"status": "initialised", "version": [...]}` — success or already initialised
- `202 {"error": "...", "retry_after": 15}` — auto-init in progress, caller should retry
- `500 {"error": "mt5.initialize failed: ..."}` — MT5 rejected the call

**Notes:**
- If `initialised=true` and `force=false` and no `login` given, returns 200 immediately without reinit
- If `force=true`, shuts down existing session and reinitialises

---

### POST /login `[init]`

Log in to a specific broker account. Called by `MT5BridgeConnector` at the start of each live session (when `dry_run=False`).

**Request body:**
```json
{
  "login":    102641850,
  "password": "broker_password",
  "server":   "FBS-Demo"
}
```

**Responses:**
- `200 {"status": "logged_in", "account": {...full AccountInfo dict...}}`
- `400 {"error": "login, password and server are required"}`
- `401 {"error": "mt5.login failed: ..."}`

---

### POST /enable_algo_trading `[init]`

Writes the `enable_trading.trigger` file so the Linux watchdog enables the Algo Trading button within ~5 seconds. Returns the current `trade_allowed` state (which may still be `false` — the watchdog acts asynchronously).

**Response:**
```json
{
  "trade_allowed": false,
  "action": "trigger_written"
}
```

---

### POST /shutdown `[no init required]`

Calls `mt5.shutdown()` and resets the `_initialised` flag.

**Response:**
```json
{"status": "shutdown"}
```

---

### GET /account_info `[init]`

Returns the full MT5 `AccountInfo` namedtuple as a dict.

Key fields: `login`, `balance`, `equity`, `profit`, `margin`, `margin_free`, `currency`, `server`, `trade_allowed`, `trade_expert`, `leverage`.

---

### GET /terminal_info `[init]`

Returns the full MT5 `TerminalInfo` namedtuple as a dict.

Key fields: `trade_allowed`, `tradeapi_disabled`, `connected`, `build`, `company`.

---

### GET /symbol_info?symbol=BTCUSD `[init]`

Returns full symbol specification. Calls `mt5.symbol_select(symbol, True)` first to ensure the symbol is subscribed.

**Error:** `404 {"error": "symbol_info failed for BTCUSD: ..."}` if symbol not available on the broker.

---

### GET /symbol_info_tick?symbol=BTCUSD `[init]`

Returns the latest tick (bid/ask/last/volume/time).

---

### GET /symbols_get?group=* `[init]`

Returns all available symbols, optionally filtered by `group` pattern (e.g. `group=*USD*`).

---

### GET /copy_rates_from_pos `[init]`

Fetch OHLCV bars from a position offset.

**Query params:**
- `symbol` (required)
- `timeframe` — MT5 timeframe int, default `16408` (TIMEFRAME_H1)
- `start_pos` — bar offset from current, default `0`
- `count` — number of bars, default `100`

**Response:** Array of `{"time", "open", "high", "low", "close", "tick_volume", "spread", "real_volume"}`.

---

### GET /copy_ticks_from `[init]`

Fetch ticks from a Unix timestamp.

**Query params:** `symbol`, `date_from` (Unix timestamp), `count` (default 100), `flags` (default 1).

---

### GET /positions_get?symbol=BTCUSD `[init]`

Returns open positions. `symbol` is optional. Returns `[]` if no positions (never returns null).

---

### GET /orders_get?symbol=BTCUSD `[init]`

Returns pending orders. `symbol` is optional.

---

### GET /history_orders_get?date_from=0&date_to=9999999999 `[init]`

Returns historical orders in a Unix timestamp range.

---

### GET /history_deals_get?date_from=0&date_to=9999999999 `[init]`

Returns historical deals (filled orders) in a Unix timestamp range.

---

### POST /order_check `[init]`

Pre-flight check for an order request. Passes the body dict directly to `mt5.order_check()`.

**Request body:** Standard MT5 order request dict (same shape as `/order_send`).

**Response:** MT5 `OrderCheckResult` as dict (`retcode`, `balance`, `equity`, `profit`, `margin`, `margin_free`, `margin_level`, `comment`, `request`).

---

### POST /order_send `[init]`

Place a market or pending order.

**Request body (example BUY market):**
```json
{
  "action":      1,
  "symbol":      "BTCUSD",
  "volume":      0.01,
  "type":        0,
  "price":       70664.0,
  "sl":          69000.0,
  "tp":          72000.0,
  "deviation":   20,
  "magic":       123456,
  "comment":     "AlgoAgent",
  "type_time":   0,
  "type_filling": 1
}
```

**Response:** MT5 `OrderSendResult` as dict:
```json
{
  "retcode":  10009,
  "deal":     123456789,
  "order":    987654321,
  "volume":   0.01,
  "price":    70664.0,
  "comment":  "Request executed",
  "request_id": 1
}
```

Success retcodes: `10008` (DONE) or `10009` (DONE_PARTIAL).

---

### GET /last_error `[init]`

Returns the last MT5 error.

**Response:** `{"code": 0, "description": "No error"}`

---

## Two MT5 Accounts

Two separate MT5 accounts are in use simultaneously:

| Account | Login | Purpose | Credentials source |
|---------|-------|---------|-------------------|
| Bridge auto-init | `105891299` | Background thread auto-initialises MT5 at startup | `/etc/algoagent/mt5_credentials.env` |
| Live trading | `102641850` | Per-session broker account (Robinson Macharia Nyaga, Balance $99.29, FBS-Demo) | Django DB → `session_manager.py` env vars → `MT5BridgeConnector` → `POST /login` |

**Flow for the live trading account:**

```
DB: LiveTradingSession.mt5_login = 102641850
  → session_manager.py: env_vars['MT5_LOGIN'] = '102641850'
  → live_trader.py subprocess
  → config.py: LiveConfig.mt5_login = 102641850
  → mt5_bridge_connector.py: POST /login { login: 102641850, ... }
  → mt5_bridge.py: mt5.login(login=102641850, ...)
  → FBS-Demo broker: authenticated as account 102641850
```

The bridge auto-init account (`105891299`) establishes the initial MT5 terminal connection. The live trading account (`102641850`) is then layered on top via `POST /login` for each trading session.

---

## Credentials Locations

```
/etc/algoagent/.env              — Django app secrets (no MT5 creds)
/etc/algoagent/mt5_credentials.env  — Bridge auto-init creds (MT5_LOGIN=105891299)
```

`/etc/algoagent/mt5_credentials.env` is root-readable only and is injected into the `mt5_bridge.service` process via `EnvironmentFile=`.

Live trading account credentials (login `102641850`) are stored in the Django database (`LiveTradingSession` model) and are never written to disk in plaintext on the host outside the DB.

---

## Integration with live_trader.py

The connector class `MT5BridgeConnector` in `monolithic_agent/Live/mt5_bridge_connector.py` is a drop-in replacement for the original Windows-only `MT5Connector`. No other file in `Live/` calls the bridge directly.

**Initialization flow (`MT5BridgeConnector.initialize()`):**

1. Poll `/health` for up to 30s until bridge is reachable
2. If `initialised=True` in health: skip `/initialize` (avoids race condition with concurrent sessions)
3. If `init_in_progress=True`: poll every 10s up to 3 minutes
4. Otherwise: `POST /initialize`
5. If `dry_run=False` and credentials are set: `POST /login`
6. `GET /terminal_info` + `GET /account_info`
7. If `trade_allowed=False`: poll every 5s up to 30s (watchdog enables it in background)
8. Check all trading permissions; return `False` if any issue found

**Order send flow (`MT5BridgeConnector.send_order()`):**

```python
if dry_run:
    return fake_success_dict   # retcode=10008, deal=999999

# Check terminal trading permissions
terminal_issue = _describe_terminal_trading_issue()
if terminal_issue:
    return {"retcode": 10027, ...}   # block order, log issue

# Send to bridge
result = POST /order_send  { action, symbol, volume, type, price, sl, tp, ... }
result["retcode_message"] = MT5Constants.get_retcode_message(retcode)
return result
```

**Environment variables required for subprocesses (set by `session_manager.py`):**

```
MT5_USE_BRIDGE=true
MT5_BRIDGE_URL=http://127.0.0.1:5555
MT5_LOGIN=<session login>
MT5_PASSWORD=<session password>
MT5_SERVER=<broker server>
DRY_RUN=false
```

---

## Health Checks and Service Management

### Check all service statuses

```bash
systemctl status xvfb-99 mt5 mt5_bridge mt5_algo_watchdog
```

### Check bridge HTTP health

```bash
curl http://127.0.0.1:5555/health
```

### Check if algo trading is enabled

```bash
curl http://127.0.0.1:5555/terminal_info | python3 -m json.tool | grep trade_allowed
```

### Check current account

```bash
curl http://127.0.0.1:5555/account_info | python3 -m json.tool
```

### Restart the full stack

```bash
sudo systemctl restart xvfb-99
sudo systemctl restart mt5
sudo systemctl restart mt5_bridge
sudo systemctl restart mt5_algo_watchdog
```

Allow ~120 seconds after restart before the bridge is fully initialised and `trade_allowed=True`.

### Restart only the bridge (MT5 already running)

```bash
sudo systemctl restart mt5_bridge
# bridge will re-initialise via background thread (usually <30s if MT5 is already up)
```

### Manually enable algo trading

```bash
curl -X POST http://127.0.0.1:5555/enable_algo_trading
# watchdog will press Ctrl+E within 5 seconds
```

### Force a one-off algo trading enable without restart

```bash
sudo -u algoagent DISPLAY=:99 XAUTHORITY=/home/algoagent/.Xauthority \
  /opt/algoagent/bin/ensure_algo_trading.sh
```

---

## Logs

| Log file | Content |
|----------|---------|
| `/var/log/mt5/mt5_bridge.log` | Flask + MT5 calls (systemd capture) |
| `/home/algoagent/.mt5/drive_c/mt5_bridge/mt5_bridge.log` | Same, written directly by Wine Python logging |
| `/var/log/mt5/mt5.log` | terminal64.exe stdout/stderr |
| `/var/log/mt5/algo_watchdog.log` | Watchdog poll results and Ctrl+E actions |
| `monolithic_agent/Live/session_logs/session_N.log` | Per-session live trader log (includes bridge connector activity) |

Tail the bridge log in real time:
```bash
tail -f /var/log/mt5/mt5_bridge.log
```

---

## Known Limitations

- **Thread safety:** All MT5 calls share a single `threading.Lock()`. Under high concurrency (many simultaneous live sessions), requests will queue. In practice one session per bot loop iteration is fine.
- **Single Wine process:** If `terminal64.exe` crashes, the bridge also becomes unusable. The systemd `Restart=on-failure` chain will recover it, but recovery takes ~60–120 seconds.
- **xdotool coordinates:** The Algo Trading button click fallback at `(289, 55)` assumes a 1024×768 virtual display and the default MT5 window layout. If the layout changes, the coordinates must be updated in `mt5_algo_watchdog.sh` and `ensure_algo_trading.sh`.
- **Windows-only MT5 Python:** The bridge can never run natively on Linux. Wine + Xvfb is the only supported path.
- **No TLS:** The bridge binds to `127.0.0.1` only and is never exposed externally. No authentication on the HTTP API — any local process can call it.
