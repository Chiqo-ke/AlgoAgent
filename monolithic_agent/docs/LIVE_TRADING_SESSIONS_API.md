# Live Trading Sessions API

**Last Updated:** March 11, 2026  
**Status:** ✅ Fully Implemented & E2E Tested  
**Base Path:** `/api/trading/`

---

## Overview

The Live Trading Sessions API enables **real-time trading session management** with stored broker credentials, secure subprocess spawning, and lifecycle control for running strategies on MetaTrader 5.

**Key Features:**
- ✅ Save encrypted broker credentials per user
- ✅ Start live trading sessions using saved or inline credentials
- ✅ Monitor session status, PID, and subprocess health
- ✅ Graceful session termination via kill-switch mechanism
- ✅ Dry-run mode for testing without real orders
- ✅ Credential rotation support (multiple brokers per user)

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     REST API Layer                            │
│           (/api/trading/credentials/ & /sessions/)            │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  BrokerCredential Model (Encrypted Storage)                   │
│  ├─ user FK, label, mt5_login, mt5_password_encrypted         │
│  ├─ mt5_server, mt5_terminal_path, is_default                 │
│  └─ Methods: set_password(plaintext), get_password()          │
│                                                                │
│  LiveTradingSession Model (Session Tracking)                  │
│  ├─ strategy FK, status, pid, symbols, timeframe              │
│  ├─ mt5_login, mt5_password_encrypted, mt5_server             │
│  └─ created_by FK, timestamps, error_message                  │
│                                                                │
│  SessionManager (Subprocess Lifecycle)                        │
│  ├─ .start_session(session)  → spawn subprocess               │
│  ├─ .stop_session(session)   → kill-switch + taskkill         │
│  ├─ .is_running(pid)         → tasklist poll                  │
│  └─ .cleanup_session_files() → remove temp files              │
│                                                                │
│  Live/live_trader.py (Strategy Subprocess)                    │
│  ├─ MT5 connection & initialization                           │
│  ├─ Strategy signal generation & order execution              │
│  ├─ Kill-switch polling (every loop)                          │
│  └─ Error logging & graceful shutdown                         │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

---

## Endpoints

### Broker Credentials Management

**Base path:** `/api/trading/credentials/`

#### POST /credentials/ — Create Credential

Save a new broker credential (encrypted).

**Auth required:** Yes

**Request body:**
```json
{
  "label": "FBS Demo Account",
  "mt5_login": 102641850,
  "mt5_password": "U-Ea6.cs",
  "mt5_server": "FBS-Demo",
  "mt5_terminal_path": "",
  "is_default": true
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `label` | string | Yes | Unique per user (constraint: `(user, label)`) |
| `mt5_login` | integer | Yes | MT5 account number |
| `mt5_password` | string | Yes | Plaintext; encrypted on save |
| `mt5_server` | string | Yes | e.g. "FBS-Demo", "FBS-Real", "ICMarkets" |
| `mt5_terminal_path` | string | No | Path to `terminal64.exe`; auto-found if blank |
| `is_default` | boolean | No | If true, clears `is_default` on other credentials |

**Response `201` Created:**
```json
{
  "id": 1,
  "label": "FBS Demo Account",
  "mt5_login": 102641850,
  "mt5_server": "FBS-Demo",
  "mt5_terminal_path": "",
  "is_default": true,
  "created_at": "2026-03-11T13:38:22.952652Z",
  "updated_at": "2026-03-11T13:38:22.952652Z"
}
```

**Response `400` Bad Request (IntegrityError):**
```json
{
  "label": ["A credential with this label already exists."]
}
```

---

#### GET /credentials/ — List Credentials

List all credentials for the current user.

**Auth required:** Yes

**Query params:** None

**Response `200` OK:**
```json
[
  {
    "id": 1,
    "label": "FBS Demo Account",
    "mt5_login": 102641850,
    "mt5_server": "FBS-Demo",
    "is_default": true,
    "created_at": "2026-03-11T13:38:22Z"
  },
  {
    "id": 2,
    "label": "ICMarkets Live",
    "mt5_login": 987654321,
    "mt5_server": "ICMarkets-Live",
    "is_default": false,
    "created_at": "2026-03-10T10:00:00Z"
  }
]
```

---

#### GET /credentials/{id}/ — Retrieve Credential

Get one credential by ID (user-scoped).

**Auth required:** Yes

**Response `200` OK:** Same as POST response above

**Response `404` Not Found:** If credential doesn't belong to user

---

#### PUT /credentials/{id}/ — Update All Fields

Update all credential fields (password is re-encrypted).

**Auth required:** Yes

**Request body:** Same as create (all fields required)

**Response `200` OK:** Updated credential

---

#### PATCH /credentials/{id}/ — Update Specific Fields

Partial update (only provided fields updated).

**Auth required:** Yes

**Request body:** Any subset of create fields

**Response `200` OK:** Updated credential

---

#### DELETE /credentials/{id}/ — Delete Credential

Remove a saved credential.

**Auth required:** Yes

**Response `204` No Content:** Credential deleted

---

### Live Trading Sessions

**Base path:** `/api/trading/sessions/`

#### POST /sessions/ — Start Session

Begin a live trading session for a strategy. Either use a saved `credential_id` or provide inline credentials.

**Auth required:** Yes

**Request body (Option A: Saved Credential):**
```json
{
  "strategy_id": 133,
  "credential_id": 1,
  "symbols": ["EURUSD"],
  "timeframe": "1h",
  "dry_run": true,
  "risk_pct": "1.00",
  "magic_number": 234567
}
```

**Request body (Option B: Inline Credentials):**
```json
{
  "strategy_id": 133,
  "mt5_login": 102641850,
  "mt5_password": "U-Ea6.cs",
  "mt5_server": "FBS-Demo",
  "symbols": ["EURUSD"],
  "timeframe": "1h",
  "dry_run": true,
  "risk_pct": "1.00"
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `strategy_id` | integer | Yes | ID of strategy to run |
| `credential_id` | integer | Conditional | Required if not using inline creds |
| `mt5_login` | integer | Conditional | Required if not using credential_id |
| `mt5_password` | string | Conditional | Required if not using credential_id |
| `mt5_server` | string | Conditional | Required if not using credential_id |
| `symbols` | array[string] | Yes | e.g. `["EURUSD", "GBPUSD"]` |
| `timeframe` | string | Yes | "1m", "5m", "15m", "1h", "4h", "1d" |
| `dry_run` | boolean | No | Default: false (real orders) |
| `risk_pct` | string/decimal | No | Risk % per trade; default: "1.00" |
| `magic_number` | integer | No | Optional MT5 magic number |
| `mt5_terminal_path` | string | No | Override credential's terminal path |

**Response `201` Created:**
```json
{
  "id": 1,
  "strategy": 133,
  "strategy_name": "Algotdrjkhhmjfgxc",
  "created_by": 1,
  "created_by_username": "algotrader",
  "status": "RUNNING",
  "pid": 8728,
  "symbols": ["EURUSD"],
  "timeframe": "1h",
  "dry_run": true,
  "risk_pct": "1.00",
  "magic_number": 234567,
  "mt5_login": 102641850,
  "mt5_server": "FBS-Demo",
  "mt5_terminal_path": "",
  "created_at": "2026-03-11T13:38:22.952652Z",
  "started_at": "2026-03-11T13:38:23.119073Z",
  "stopped_at": null,
  "error_message": "",
  "temp_file_path": "C:\\Users\\nyaga\\...\\strategy_1_d1ecf8b8.py",
  "kill_switch_path": "C:\\Users\\nyaga\\...\\STOP_1"
}
```

**Response `400` Bad Request:**
```json
{
  "detail": "Must provide either credential_id OR (mt5_login + mt5_password + mt5_server)"
}
```

**Response `400` Bad Request (strategy not found):**
```json
{
  "strategy_id": ["Not found."]
}
```

---

#### GET /sessions/ — List Sessions

List all sessions created by the current user.

**Auth required:** Yes

**Query params:**
| Param | Type | Description |
|-------|------|-------------|
| `status` | string | Filter by PENDING/RUNNING/STOPPED/ERROR |
| `ordering` | string | e.g. "-created_at" (newest first) |
| `page` | int | Pagination |

**Response `200` OK:**
```json
[
  {
    "id": 1,
    "strategy_name": "Algotdrjkhhmjfgxc",
    "status": "STOPPED",
    "pid": 8728,
    "symbols": ["EURUSD"],
    "timeframe": "1h",
    "dry_run": true,
    "created_at": "2026-03-11T13:38:22Z",
    "started_at": "2026-03-11T13:38:23Z",
    "stopped_at": "2026-03-11T13:39:02Z"
  }
]
```

---

#### GET /sessions/{id}/ — Get Session Details

Retrieve full session details (user-scoped).

**Auth required:** Yes

**Response `200` OK:** Full session object (same as POST response above)

**Response `404` Not Found:** If session doesn't belong to user

---

#### POST /sessions/{id}/stop/ — Stop Session

Terminate a running session. Uses kill-switch file; falls back to `taskkill /F`.

**Auth required:** Yes

**Request body:** Empty `{}`

**Response `200` OK:**
```json
{
  "detail": "Session stopped.",
  "session": {
    "id": 1,
    "status": "STOPPED",
    "stopped_at": "2026-03-11T13:39:02.833689Z",
    "error_message": ""
  }
}
```

**Response `400` Bad Request (already stopped):**
```json
{
  "detail": "Session is not running."
}
```

---

#### DELETE /sessions/{id}/ — Delete Session

Permanently delete a session and clean up temp files.

**Auth required:** Yes

**Response `204` No Content:** Session deleted

---

## Data Models

### BrokerCredential

```python
class BrokerCredential(models.Model):
    user = ForeignKey(User, on_delete=models.CASCADE)
    label = CharField(max_length=255)
    mt5_login = IntegerField()
    mt5_password_encrypted = TextField()  # Fernet-encrypted
    mt5_server = CharField(max_length=255)
    mt5_terminal_path = CharField(max_length=500, blank=True)
    is_default = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('user', 'label')]

    def set_password(self, plaintext: str):
        """Encrypt and store password"""

    def get_password(self) -> str:
        """Decrypt and return password"""
```

### LiveTradingSession

```python
class LiveTradingSession(models.Model):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    ERROR = "ERROR"
    
    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (RUNNING, "Running"),
        (STOPPED, "Stopped"),
        (ERROR, "Error"),
    ]

    strategy = ForeignKey(Strategy, on_delete=models.CASCADE)
    status = CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    pid = IntegerField(null=True, blank=True)
    
    symbols = JSONField(default=list)  # ["EURUSD", "GBPUSD"]
    timeframe = CharField(max_length=20)  # "1h"
    dry_run = BooleanField(default=False)
    risk_pct = DecimalField(max_digits=5, decimal_places=2, default="1.00")
    magic_number = IntegerField(default=234567)
    
    mt5_login = IntegerField()
    mt5_password_encrypted = TextField()  # Fernet-encrypted
    mt5_server = CharField(max_length=255)
    mt5_terminal_path = CharField(max_length=500, blank=True)
    
    created_by = ForeignKey(User, on_delete=models.CASCADE)
    created_at = DateTimeField(auto_now_add=True)
    started_at = DateTimeField(null=True, blank=True)
    stopped_at = DateTimeField(null=True, blank=True)
    error_message = TextField(blank=True)

    def set_mt5_password(self, plaintext: str):
        """Encrypt password for storage"""

    def get_mt5_password(self) -> str:
        """Decrypt password"""
```

---

## Usage Examples

### Example 1: Save a Broker Credential

```bash
curl -X POST http://localhost:8000/api/trading/credentials/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "label": "FBS Demo",
    "mt5_login": 102641850,
    "mt5_password": "U-Ea6.cs",
    "mt5_server": "FBS-Demo",
    "is_default": true
  }'
```

### Example 2: Start a Live Session

```bash
curl -X POST http://localhost:8000/api/trading/sessions/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_id": 133,
    "credential_id": 1,
    "symbols": ["EURUSD"],
    "timeframe": "1h",
    "dry_run": true,
    "risk_pct": "1.50"
  }'
```

**Response:**
```json
{
  "id": 1,
  "status": "RUNNING",
  "pid": 8728,
  "created_at": "2026-03-11T13:38:22.952652Z",
  "started_at": "2026-03-11T13:38:23.119073Z"
}
```

### Example 3: Stop a Session

```bash
curl -X POST http://localhost:8000/api/trading/sessions/1/stop/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## Session Lifecycle

### 1. Create (POST /sessions/)
- Resolve credentials (either from `credential_id` or inline)
- Decrypt MT5 password
- Write temp strategy file with code
- Write encrypted `.env` with credentials
- Spawn subprocess via `SessionManager.start_session()`
- Session status → `RUNNING`
- Return session object with `pid`

### 2. Running
- Subprocess polls kill-switch file every loop iteration
- MT5 connections established; orders executed
- Logs written to subprocess stdout/stderr
- SessionManager monitors `is_running(pid)`

### 3. Stop (POST /sessions/{id}/stop/)
- Touch kill-switch file: `Live/kill_switches/STOP_<session_id>`
- Poll `is_running(pid)` for up to 30 seconds
- If still alive, run `taskkill /F /PID <pid>`
- Session status → `STOPPED`
- Record `stopped_at` timestamp

### 4. Cleanup (DELETE /sessions/{id}/)
- Remove temp strategy file
- Remove kill-switch marker file
- Session deleted from database

---

## Error Handling

### Common HTTP Status Codes

| Status | Scenario |
|--------|----------|
| `200` | Successful operation (list, get, stop) |
| `201` | Session created and started |
| `204` | Resource deleted |
| `400` | Validation error (missing fields, credential conflict) |
| `401` | Not authenticated |
| `403` | Forbidden (not owner of resource) |
| `404` | Resource not found |
| `500` | Server error (check Django logs) |

### Session Error States

If `status = "ERROR"`, check `error_message` field for details:

```json
{
  "id": 2,
  "status": "ERROR",
  "error_message": "MT5 terminal not found. Please set mt5_terminal_path or install MetaTrader 5.",
  "created_at": "2026-03-11T14:00:00Z",
  "started_at": "2026-03-11T14:00:01Z"
}
```

---

## Security Notes

1. **Password Encryption:** All MT5 passwords are encrypted with Fernet (AES-128) before storage. `FERNET_KEY` must be present in `.env`.

2. **Credential Isolation:** Credentials are user-scoped. A user can only list/update/delete their own credentials via the API.

3. **Session Isolation:** Sessions are user-scoped. Only the creator can view/stop/delete a session.

4. **Subprocess Isolation (Windows):** Live trader subprocesses run in isolated process groups (`CREATE_NEW_PROCESS_GROUP`), preventing stray signals.

5. **Plaintext Password in Request:** Passwords are sent plaintext in the request body but are encrypted immediately upon server receipt. Never stored plaintext.

---

## Deployment Checklist

- [x] `FERNET_KEY` present in `.env`
- [x] `migration 0002_brokercredential` applied
- [x] `trading_sessions_api` app registered in `INSTALLED_APPS`
- [x] URL router registered in main `urls.py`
- [x] `Live/temp_strategies/` and `Live/kill_switches/` directories exist (auto-created on first session)
- [x] VirtualEnv path correct in `SessionManager.VENV_PYTHON` (Windows-specific)
- [x] Django dev server or production server running

---

## Troubleshooting

### Session starts but immediately goes to ERROR

**Check:**
1. Django logs for `[ERROR]` messages in `Live/live_trader.py`
2. Is MT5 installed on the machine?
3. Is `mt5_terminal_path` correct, or is it auto-discoverable?

### Session won't stop (stuck in RUNNING)

**Check:**
1. Kill-switch file created: `Live/kill_switches/STOP_<id>`
2. Is subprocess still alive: `tasklist | findstr <pid>`
3. Manual kill: `taskkill /F /PID <pid>`

### Duplicate credential error on retry

**Expected behavior:** POST duplicate credential returns 400. Use GET /credentials/ to fetch and reuse the existing id.

### Password reset takes forever

**Previously fixed:** Stray Ctrl+C from terminal was interrupting PBKDF2 hashing. Use `Start-Process -WindowStyle Hidden` for management scripts.

---

## Next Steps

1. **Real Account Testing:** Update credentials to real FBS account; set `dry_run=False`
2. **MT5 Path Detection:** Implement auto-discovery of `terminal64.exe` on different systems
3. **Logging Dashboard:** Add realtime subprocess output viewer in frontend
4. **Session Analytics:** Track P&L, trade count, and session duration per user
5. **Multiplatform Support:** Extend `SessionManager` to macOS/Linux

---

