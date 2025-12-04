# AlgoAgent Monolithic - Quick Reference

**Last Updated:** December 3, 2025  
**Status:** Quick lookup guide for developers

---

## File Structure at a Glance

```
monolithic_agent/
├── ARCHITECTURE.md             ← System design (START HERE)
├── STATUS.md                   ← What works/doesn't work
├── SETUP_AND_INTEGRATION.md   ← Installation guide
├── QUICK_REFERENCE.md         ← This file
│
├── algoagent_api/             # Django settings
│   └── settings.py, urls.py, wsgi.py, asgi.py
│
├── auth_api/                  # JWT authentication
│   ├── views.py
│   └── models.py
│
├── strategy_api/              # Strategy management
│   ├── views.py               # Core endpoints
│   ├── production_views.py    # Hardened endpoints
│   ├── models.py              # ORM: Strategy, StrategyValidation, ConversationMemory
│   └── serializers.py         # Pydantic schemas
│
├── backtest_api/              # Backtesting
│   ├── views.py
│   ├── production_views.py
│   ├── models.py              # ORM: BacktestRun
│   └── serializers.py
│
├── data_api/                  # Market data
│   ├── views.py
│   └── models.py              # ORM: DataSet
│
├── trading/                   # Live trading (placeholder)
│   ├── views.py
│   └── models.py
│
├── Backtest/                  # Backtesting engine
│   ├── backtesting_adapter.py          # ⭐ Main interface
│   ├── gemini_strategy_generator.py    # ⭐ AI code generation
│   ├── data_manager.py
│   ├── codes/                          # Generated .py files
│   ├── indicators/                     # TA-Lib wrappers
│   └── SYSTEM_PROMPT_BACKTESTING_PY.md # AI system prompt
│
├── Strategy/                  # Strategy interaction
│   ├── interactive_strategy_tester.py  # ⭐ CLI tool
│   ├── strategy_validator.py
│   └── gemini_strategy_integrator.py
│
├── Data/                      # Data ingestion
│   ├── main.py                # DataIngestionModel
│   ├── indicator_registry.py
│   └── tests/
│
├── tests/                     # Unit & integration tests
│   ├── test_auth_flow.py
│   ├── test_ai_strategy_api.py
│   ├── test_production_endpoints.py
│   └── ...
│
├── manage.py                  # Django CLI
├── requirements.txt           # Dependencies
├── pytest.ini                 # Test config
├── db.sqlite3                 # Database
└── start_server.ps1          # Server launcher
```

---

## Quick Commands

### Server Management

```bash
# Activate environment
.venv\Scripts\activate

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start server
python manage.py runserver

# Run in background (PowerShell)
.\start_server.ps1
```

### Testing

```bash
# All tests
pytest tests/ -v

# Specific file
pytest tests/test_auth_flow.py -v

# With coverage
pytest tests/ --cov=strategy_api

# Specific test
pytest tests/ -k "test_create_strategy" -v

# Verbose output
pytest tests/ -vv --tb=long
```

### Interactive Tools

```bash
# Launch strategy tester
cd Strategy
python interactive_strategy_tester.py

# Generate strategy from JSON
python -c "
from Backtest.gemini_strategy_generator import GeminiStrategyGenerator
gen = GeminiStrategyGenerator()
code = gen.generate_from_canonical({...}, 'strategy_name')
print(code)
"

# Run backtest manually
python -c "
from Backtest.backtesting_adapter import BacktestingAdapter
adapter = BacktestingAdapter(None)
results = adapter.run_backtest_from_canonical({...})
print(results)
"
```

### Database

```bash
# View tables
python manage.py dbshell
.tables

# Reset database
del db.sqlite3
python manage.py migrate
python manage.py createsuperuser

# Dump data
python manage.py dumpdata > data_backup.json

# Load data
python manage.py loaddata data_backup.json
```

---

## API Quick Reference

### Base URL
```
http://localhost:8000/api/
```

### Authentication

**Login:**
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# Response includes: access_token, refresh_token
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."
```

**Use Token:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/strategies/
```

### Strategy Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/strategies/` | Create strategy |
| GET | `/strategies/` | List all strategies |
| GET | `/strategies/{id}/` | Get strategy details |
| PUT | `/strategies/{id}/` | Update strategy |
| DELETE | `/strategies/{id}/` | Delete strategy |
| POST | `/strategies/{id}/validate/` | Validate canonical JSON |
| POST | `/strategies/{id}/generate-code/` | Generate Python code |

### Backtest Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/backtests/` | Create backtest run |
| GET | `/backtests/` | List all backtests |
| GET | `/backtests/{id}/` | Get backtest results |
| POST | `/backtests/quick-run/` | Quick backtest from canonical JSON |

### Data Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/data/indicators/` | List available indicators |
| POST | `/data/fetch/` | Fetch OHLCV data |

---

## API Request/Response Formats

### Create Strategy

**Request:**
```bash
POST /api/strategies/
Content-Type: application/json
Authorization: Bearer TOKEN

{
  "name": "RSI_Oversold_v1",
  "description": "Buy RSI oversold",
  "canonical_json": {
    "strategy_name": "RSI Oversold",
    "entry_rules": [{"condition": "RSI < 30", "action": "BUY"}],
    "exit_rules": [{"condition": "RSI > 70", "action": "SELL"}],
    "indicators": [{"name": "RSI", "timeperiod": 14}],
    "risk_management": {"stop_loss_pct": 2.0}
  }
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "user_id": 1,
  "name": "RSI_Oversold_v1",
  "version": 1,
  "canonical_json": {...},
  "created_at": "2025-12-03T10:30:00Z"
}
```

### Generate Code

**Request:**
```bash
POST /api/strategies/1/generate-code/
Authorization: Bearer TOKEN
```

**Response (200 OK):**
```json
{
  "success": true,
  "strategy_code": "from backtesting import...",
  "file_path": "Backtest/codes/rsi_oversold_v1.py",
  "file_name": "rsi_oversold_v1.py",
  "message": "Code generated successfully"
}
```

### Quick Backtest

**Request:**
```bash
POST /api/backtests/quick-run/
Authorization: Bearer TOKEN

{
  "strategy_id": 1,
  "ticker": "AAPL",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_cash": 100000
}
```

**Response (200 OK):**
```json
{
  "status": "completed",
  "return_pct": 18.5,
  "sharpe_ratio": 1.45,
  "max_drawdown": -8.3,
  "win_rate": 0.62,
  "profit_factor": 2.15,
  "total_trades": 42,
  "total_pnl": 2500.50,
  "trades_csv": "artifacts/trades_1.csv",
  "equity_csv": "artifacts/equity_1.csv",
  "created_at": "2025-12-03T10:35:00Z"
}
```

---

## Key Classes & Functions

### backtesting_adapter.py

```python
from Backtest.backtesting_adapter import BacktestingAdapter

# Initialize (wraps backtesting.py)
adapter = BacktestingAdapter(None)

# Fetch data
df = adapter.fetch_and_prepare_data(
    ticker="AAPL",
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# Create strategy from canonical JSON
strategy_class = adapter.create_strategy_from_canonical(
    canonical_json={...},
    strategy_name="RSI_Oversold"
)

# Run full backtest
results = adapter.run_backtest_from_canonical(
    canonical_json={...},
    ticker="AAPL",
    start_date="2024-01-01",
    end_date="2024-12-31"
)
# Returns: {
#   "total_pnl": 2500.50,
#   "sharpe_ratio": 1.45,
#   "trades_csv": "...",
#   ...
# }
```

### gemini_strategy_generator.py

```python
from Backtest.gemini_strategy_generator import GeminiStrategyGenerator

# Initialize (loads API key from .env)
generator = GeminiStrategyGenerator(use_backtesting_py=True)

# Generate code from canonical JSON
code = generator.generate_from_canonical(
    canonical_json={...},
    strategy_name="RSI_Oversold"
)
# Returns: Python code string (executable)

# Save code
with open("Backtest/codes/rsi_oversold.py", "w") as f:
    f.write(code)
```

### strategy_validator.py

```python
from Strategy.strategy_validator import StrategyValidatorBot

# Initialize
bot = StrategyValidatorBot()

# Validate user input
canonical_json = bot.validate_user_input(
    user_input="Buy when RSI < 30, sell when RSI > 70"
)
# Returns: validated JSON schema

# Get AI recommendations
recommendations = bot.get_recommendations(canonical_json)
# Returns: {"suggestions": [...], "risks": [...]}
```

### DataIngestionModel

```python
from Data.main import DataIngestionModel

# Initialize
model = DataIngestionModel()

# Ingest & process data
df = model.ingest_and_process(
    ticker="AAPL",
    required_indicators=[
        {"name": "RSI", "timeperiod": 14},
        {"name": "SMA", "timeperiod": 20},
        {"name": "MACD"}
    ],
    period="60d",
    interval="1h"
)
# Returns: DataFrame with OHLCV + indicators
```

---

## Indicator Reference

### Supported Indicators (TA-Lib)

| Indicator | Column Name | Parameters | Notes |
|-----------|-------------|------------|-------|
| RSI | RSI_14 | timeperiod=14 | Relative Strength Index |
| SMA | SMA_20 | timeperiod=20 | Simple Moving Average |
| EMA | EMA_12 | timeperiod=12 | Exponential Moving Average |
| MACD | MACD, MACD_SIGNAL, MACD_HIST | fastperiod=12, slowperiod=26 | MACD |
| ATR | ATR_14 | timeperiod=14 | Average True Range |
| STOCH | STOCH_K, STOCH_D | fastk_period=5, slowk_period=3 | Stochastic |
| ADX | ADX_14 | timeperiod=14 | Average Directional Index |
| CCI | CCI_20 | timeperiod=20 | Commodity Channel Index |
| Bollinger | BB_UPPER, BB_MIDDLE, BB_LOWER | timeperiod=20, nbdev=2 | Bollinger Bands |

### Usage in Strategy

```python
def init(self):
    # Calculate indicators in init() - vectorized
    self.rsi = self.I(ta.RSI, self.data.Close, 14)
    self.sma_20 = self.I(ta.SMA, self.data.Close, 20)
    self.sma_200 = self.I(ta.SMA, self.data.Close, 200)

def next(self):
    # Access in next() - current bar
    if self.rsi[-1] < 30 and not self.position:
        self.buy()
    elif self.rsi[-1] > 70 and self.position:
        self.position.close()
```

---

## Common Patterns

### Pattern 1: User → API → Backtest

```python
import requests

# 1. User login
resp = requests.post("http://localhost:8000/api/auth/login/", 
                     json={"username": "user", "password": "pass"})
token = resp.json()["access_token"]

# 2. Create strategy
resp = requests.post("http://localhost:8000/api/strategies/",
                     headers={"Authorization": f"Bearer {token}"},
                     json={"name": "RSI_v1", "canonical_json": {...}})
strategy_id = resp.json()["id"]

# 3. Generate code
resp = requests.post(f"http://localhost:8000/api/strategies/{strategy_id}/generate-code/",
                     headers={"Authorization": f"Bearer {token}"})
code_path = resp.json()["file_path"]

# 4. Run backtest
resp = requests.post("http://localhost:8000/api/backtests/quick-run/",
                     headers={"Authorization": f"Bearer {token}"},
                     json={"strategy_id": strategy_id, "ticker": "AAPL", ...})
results = resp.json()
print(f"PnL: {results['total_pnl']}, Sharpe: {results['sharpe_ratio']}")
```

### Pattern 2: Batch Testing

```python
import pandas as pd

# Test multiple parameter combinations
results = []
for rsi_period in [10, 14, 20]:
    for rsi_threshold in [20, 25, 30]:
        canonical = {
            "strategy_name": f"RSI_{rsi_period}_{rsi_threshold}",
            "indicators": [{"name": "RSI", "timeperiod": rsi_period}],
            "entry_rules": [{"condition": f"RSI < {rsi_threshold}", "action": "BUY"}],
            ...
        }
        # Create → Generate → Test
        results.append({
            "rsi_period": rsi_period,
            "rsi_threshold": rsi_threshold,
            "pnl": response["total_pnl"],
            "sharpe": response["sharpe_ratio"]
        })

df = pd.DataFrame(results).sort_values("sharpe", ascending=False)
print(df.to_string())
```

### Pattern 3: Custom Entry/Exit Logic

```python
class CustomStrategy(Strategy):
    # Entry: RSI oversold + above SMA
    def entry_logic(self):
        rsi_oversold = self.rsi[-1] < 30
        above_sma = self.close[-1] > self.sma_200[-1]
        return rsi_oversold and above_sma
    
    # Exit: TP at 5% or SL at 2%
    def exit_logic(self):
        if not self.position:
            return False
        pnl_pct = (self.data.Close[-1] - self.position.open_price) / self.position.open_price * 100
        return pnl_pct > 5 or pnl_pct < -2
```

---

## Environment Variables

### Required
```bash
GEMINI_API_KEY=sk-...         # Gemini API key
SECRET_KEY=...                # Django secret
DEBUG=False                   # Debug mode
```

### Optional
```bash
DATABASE_URL=...              # Custom database (default: SQLite)
ALLOWED_HOSTS=...             # Allowed domains
JWT_SECRET=...                # Custom JWT secret
JWT_EXPIRY=3600               # Token expiry seconds
USE_BACKTESTING_PY=True       # Use backtesting.py (default)
USE_CONVERSATION_MEMORY=True  # Use memory (default)
```

---

## Debugging Tips

### 1. Check Indicator Values
```python
from Backtest.backtesting_adapter import BacktestingAdapter
adapter = BacktestingAdapter(None)
df = adapter.fetch_and_prepare_data("AAPL", "2024-01-01", "2024-12-31")
print(df[['Close', 'RSI_14', 'SMA_20']].tail(20))
```

### 2. Verify Entry Conditions
```python
# Add debug prints in generated code
def next(self):
    if self.rsi[-1] < 30:
        print(f"Entry signal: RSI={self.rsi[-1]:.2f}, Close={self.data.Close[-1]:.2f}")
        if not self.position:
            self.buy()
```

### 3. View Generated Code
```bash
# List all generated strategies
ls -la Backtest/codes/

# View specific strategy
cat Backtest/codes/rsi_oversold_v1.py
```

### 4. Test Database Queries
```bash
python manage.py dbshell
SELECT * FROM strategy_api_strategy;
SELECT COUNT(*) FROM strategy_api_strategy;
.schema strategy_api_strategy
```

---

## Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| "ModuleNotFoundError: backtesting" | Missing import | `pip install backtesting` |
| "Gemini API key not found" | .env not configured | `echo GEMINI_API_KEY=... >> .env` |
| "UNIQUE constraint failed" | Duplicate strategy name | Use version suffix: `RSI_v1`, `RSI_v2` |
| "No trades generated" | Entry conditions never met | Debug: print indicators, adjust thresholds |
| "TALIB not installed" | Missing TA-Lib | `pip install TA-Lib` |
| "Database is locked" | SQLite contention | Restart Django, or use PostgreSQL |
| "ModuleNotFoundError: yfinance" | Missing dependency | `pip install -r requirements.txt` |

---

## Performance Metrics

| Operation | Duration |
|-----------|----------|
| Strategy creation | ~200ms |
| Code generation | ~2-5s (API call) |
| Backtest 1 year daily | ~1-2s |
| Data fetch 1 year | ~500ms |
| API response (cached) | <100ms |

---

## Useful Links

**Internal Docs:**
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [STATUS.md](STATUS.md) - Component status
- [SETUP_AND_INTEGRATION.md](SETUP_AND_INTEGRATION.md) - Installation
- [PRODUCTION_API_GUIDE.md](PRODUCTION_API_GUIDE.md) - API details

**External Resources:**
- backtesting.py: https://kernc.github.io/backtesting.py/
- Gemini API: https://ai.google.dev/
- Django REST: https://www.django-rest-framework.org/
- TA-Lib: https://mrjbq7.github.io/ta-lib/

---

**END OF QUICK REFERENCE**

Print this page for desk reference!
