# AlgoAgent Monolithic - Setup & Integration Guide

**Date:** December 3, 2025  
**Target Audience:** Developers, DevOps Engineers  
**Difficulty:** Intermediate

---

## Quick Start (5 minutes)

### Prerequisites
- Python 3.9+
- pip package manager
- Gemini API key (free tier available)
- Virtual environment tool

### Step 1: Clone & Navigate
```bash
cd c:\Users\nyaga\Documents\AlgoAgent\monolithic_agent
```

### Step 2: Create Virtual Environment
```bash
python -m venv .venv
.venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment
```bash
# Create .env file in workspace root
echo GEMINI_API_KEY=your-api-key-here > .env
echo DEBUG=False >> .env
echo SECRET_KEY=your-secret-key >> .env
```

### Step 5: Initialize Database
```bash
python manage.py migrate
python manage.py createsuperuser
```

### Step 6: Start Server
```bash
python manage.py runserver
```

**Server Ready:** `http://localhost:8000/api/`

---

## Detailed Installation

### 1. System Requirements

**Minimum:**
- Python 3.9+
- 4GB RAM
- 500MB disk space
- Windows 10+ / macOS / Linux

**Recommended:**
- Python 3.11+
- 8GB RAM
- 2GB disk space
- SSD storage

### 2. Python Environment Setup

#### Option A: venv (Built-in)
```bash
# Create virtual environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Verify activation (should show path to .venv)
which python
```

#### Option B: conda (Anaconda)
```bash
# Create conda environment
conda create -n algoagent python=3.11

# Activate
conda activate algoagent
```

### 3. Install Dependencies

**Core Requirements:**
```bash
pip install -r requirements.txt
```

**What Gets Installed:**
- Django 4.2+ (web framework)
- djangorestframework (REST API)
- backtesting.py (backtesting engine)
- talib (technical indicators)
- yfinance (market data)
- pydantic (validation)
- google-generativeai (Gemini API)
- pytest (testing)
- python-dotenv (environment variables)

**Verify Installation:**
```bash
python -c "
import django
import backtesting
import talib
import yfinance
print('✓ All core dependencies installed')
"
```

### 4. Environment Configuration

**File:** `.env` (workspace root)

**Create with:**
```bash
# PowerShell
New-Item -Path .env -ItemType File

# Or manually edit and add:
```

**Required Variables:**
```bash
# Django
DEBUG=False
SECRET_KEY=your-super-secret-key-here-min-50-chars
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Gemini API
GEMINI_API_KEY=sk-... (get from https://makersuite.google.com)

# JWT
JWT_SECRET=your-jwt-secret-key
JWT_EXPIRY=3600

# Features
USE_BACKTESTING_PY=True
USE_CONVERSATION_MEMORY=True
DEBUG_MODE=False
```

**Getting Gemini API Key:**
1. Go to https://makersuite.google.com
2. Sign in with Google account
3. Click "Get API Key"
4. Create new key
5. Copy and paste into `.env`

### 5. Database Initialization

**First Time Setup:**
```bash
# Run migrations
python manage.py migrate

# Create superuser (for admin panel)
python manage.py createsuperuser
# Follow prompts for username, email, password

# Create test data (optional)
python manage.py loaddata tests/fixtures/initial_data.json
```

**Verify Database:**
```bash
# Check database exists
dir db.sqlite3

# Check tables created
python manage.py dbshell
# .tables
# .quit
```

**Database Schema:**
```sql
-- Tables created:
auth_user              -- Django user accounts
strategy_api_strategy  -- Trading strategies
strategy_api_strategyvalidation  -- Validation results
backtest_api_backtestrun  -- Backtest runs
strategy_api_conversationmemory  -- Chat history
```

### 6. Start Django Development Server

**Option A: Direct Python**
```bash
python manage.py runserver
```

**Option B: PowerShell Script**
```powershell
# Edit start_server.ps1 if needed
.\start_server.ps1
```

**Option C: Specify Port**
```bash
python manage.py runserver 0.0.0.0:8080
```

**Server Output:**
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

**Access Points:**
- REST API: `http://localhost:8000/api/`
- Admin Panel: `http://localhost:8000/admin/`
- Health Check: `http://localhost:8000/api/health/`

---

## API Integration

### 1. Authentication Flow

**Endpoint:** `POST /api/auth/login/`

**Request:**
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user_id": 1,
  "username": "your_username"
}
```

**Using Token:**
```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  http://localhost:8000/api/strategies/
```

### 2. Create Strategy

**Endpoint:** `POST /api/strategies/`

**Request:**
```json
{
  "name": "RSI_Oversold_v1",
  "description": "Buy when RSI < 30, sell when RSI > 70",
  "canonical_json": {
    "strategy_name": "RSI Oversold",
    "entry_rules": [
      {
        "condition": "RSI < 30",
        "action": "BUY"
      }
    ],
    "exit_rules": [
      {
        "condition": "RSI > 70",
        "action": "SELL"
      }
    ],
    "indicators": [
      {
        "name": "RSI",
        "timeperiod": 14
      }
    ],
    "risk_management": {
      "stop_loss_pct": 2.0,
      "take_profit_pct": 5.0
    }
  }
}
```

**Response:**
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

### 3. Generate Executable Code

**Endpoint:** `POST /api/strategies/{id}/generate-code/`

**Request:**
```json
{
  "strategy_name": "RSI_Oversold_v1"
}
```

**Response:**
```json
{
  "success": true,
  "strategy_code": "from backtesting import Backtest, Strategy\n...",
  "file_path": "Backtest/codes/rsi_oversold_v1.py",
  "file_name": "rsi_oversold_v1.py",
  "message": "Code generated successfully"
}
```

**Generated File Location:**
```
Backtest/codes/rsi_oversold_v1.py
```

### 4. Run Backtest

**Endpoint:** `POST /api/backtests/quick-run/`

**Request:**
```json
{
  "strategy_id": 1,
  "ticker": "AAPL",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_cash": 100000
}
```

**Response:**
```json
{
  "status": "completed",
  "return_pct": 18.5,
  "sharpe_ratio": 1.45,
  "max_drawdown": -8.3,
  "win_rate": 0.62,
  "total_trades": 42,
  "total_pnl": 2500.50,
  "trades_csv": "artifacts/trades_1.csv",
  "equity_csv": "artifacts/equity_1.csv"
}
```

**CSV Files Generated:**
- `artifacts/trades_1.csv` - Trade list
- `artifacts/equity_1.csv` - Equity curve

---

## Testing

### Run All Tests

```bash
# Activate environment
.venv\Scripts\activate

# Run tests with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_auth_flow.py -v

# Run with coverage
pytest tests/ --cov=strategy_api --cov=backtest_api

# Run tests matching pattern
pytest tests/ -k "test_create" -v
```

### Expected Output
```
tests/test_auth_flow.py::test_user_registration PASSED [ 10%]
tests/test_auth_flow.py::test_jwt_login PASSED [ 20%]
tests/test_strategy_conversation_memory.py::test_memory PASSED [ 30%]
...
======================== 26 passed in 2.45s =========================
```

### Test Files & Coverage

| File | Tests | Status |
|------|-------|--------|
| test_auth_flow.py | 4 | ✅ PASS |
| test_strategy_conversation_memory.py | 2 | ✅ PASS |
| test_ai_strategy_api.py | 4 | ✅ PASS |
| test_dynamic_data_loader.py | 3 | ✅ PASS |
| test_production_api_integration.py | 4 | ✅ PASS |
| test_production_endpoints.py | 4 | ✅ PASS |
| **Total** | **26+** | **✅ PASS** |

---

## Interactive Strategy Tester

### CLI Interface

**Launch:**
```bash
cd Strategy
python interactive_strategy_tester.py
```

**Menu:**
```
1. Enter a new strategy (free text)
2. Enter a strategy (numbered steps)
3. Load example strategy
4. Analyze strategy from URL
5. View session history
6. Exit
```

**Example: Free Text Input**
```
Enter your strategy: Buy AAPL when RSI < 30, sell when RSI > 70, stop at 2%

Expected Output:
✓ Strategy canonicalized
✓ AI analysis complete
✓ Recommendations generated
```

### Workflow

```
User Input
    ↓
Strategy Validator (canonicalization)
    ↓
Gemini AI Analysis (Recommendations)
    ↓
JSON Export (Save to DB)
    ↓
Ready for Code Generation
```

---

## Common Integration Patterns

### Pattern 1: CLI-based Strategy Creation

```bash
# 1. Launch interactive tester
cd Strategy
python interactive_strategy_tester.py

# 2. Enter strategy description
# 3. Review canonicalized JSON
# 4. Accept recommendations
# 5. Export JSON

# 6. Create strategy via API
curl -X POST http://localhost:8000/api/strategies/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d @strategy.json

# 7. Generate code
curl -X POST http://localhost:8000/api/strategies/1/generate-code/ \
  -H "Authorization: Bearer TOKEN"

# 8. Run backtest
curl -X POST http://localhost:8000/api/backtests/quick-run/ \
  -H "Authorization: Bearer TOKEN" \
  -d "{\"strategy_id\": 1, ...}"
```

### Pattern 2: Programmatic Strategy Creation

```python
import requests
import json

BASE_URL = "http://localhost:8000/api"
TOKEN = "your-jwt-token"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# 1. Create strategy
canonical_json = {
    "strategy_name": "RSI_Oversold",
    "entry_rules": [{"condition": "RSI < 30", "action": "BUY"}],
    "exit_rules": [{"condition": "RSI > 70", "action": "SELL"}],
    "indicators": [{"name": "RSI", "timeperiod": 14}]
}

response = requests.post(
    f"{BASE_URL}/strategies/",
    headers=HEADERS,
    json={"name": "RSI_v1", "canonical_json": canonical_json}
)
strategy_id = response.json()["id"]

# 2. Generate code
response = requests.post(
    f"{BASE_URL}/strategies/{strategy_id}/generate-code/",
    headers=HEADERS
)
code_path = response.json()["file_path"]
print(f"Code saved to: {code_path}")

# 3. Run backtest
response = requests.post(
    f"{BASE_URL}/backtests/quick-run/",
    headers=HEADERS,
    json={
        "strategy_id": strategy_id,
        "ticker": "AAPL",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    }
)
results = response.json()
print(f"PnL: {results['total_pnl']}, Sharpe: {results['sharpe_ratio']}")
```

### Pattern 3: Batch Strategy Testing

```python
# Test multiple strategies
strategies = [
    {"name": "RSI_Oversold", "rsi_threshold": 30},
    {"name": "MA_Crossover", "fast_period": 20, "slow_period": 50},
    {"name": "Bollinger_Bands", "period": 20, "dev": 2}
]

results = []
for strategy in strategies:
    # Create → Generate → Test
    ...
    results.append({
        "name": strategy["name"],
        "pnl": response["total_pnl"],
        "sharpe": response["sharpe_ratio"],
        "trades": response["total_trades"]
    })

# Export results to CSV
import pandas as pd
df = pd.DataFrame(results)
df.to_csv("backtest_results.csv", index=False)
```

---

## Troubleshooting

### Issue 1: "ModuleNotFoundError: No module named 'backtesting'"

**Solution:**
```bash
pip install backtesting
# or reinstall all requirements
pip install -r requirements.txt
```

### Issue 2: "Gemini API key not found"

**Solution:**
```bash
# Verify .env exists and contains key
cat .env

# Should show:
# GEMINI_API_KEY=sk-...

# If not, add it
echo GEMINI_API_KEY=your-key >> .env
```

### Issue 3: "UNIQUE constraint failed"

**Cause:** Strategy name + version must be unique per user

**Solution:**
```python
# Use version suffix
strategy_name = "RSI_Oversold_v1"
strategy_name = "RSI_Oversold_v2"  # Next version
```

### Issue 4: "TALIB not installed"

**Solution:**
```bash
# Windows: Use pre-compiled wheel
pip install TA-Lib

# macOS: Use Homebrew first
brew install ta-lib
pip install TA-Lib

# Linux: Build from source
pip install TA-Lib
```

### Issue 5: "No trades generated"

**Solution:**
1. Check entry condition is correct
2. Verify indicator values (print in debug)
3. Use longer date range
4. Check timeframe alignment

```python
# Debug strategy
from backtesting_adapter import BacktestingAdapter
adapter = BacktestingAdapter(None)
df = adapter.fetch_and_prepare_data("AAPL", "2024-01-01", "2024-12-31")
print(df[['Close', 'RSI_14']].tail(20))
```

### Issue 6: "Database is locked"

**Solution:**
```bash
# Remove database and reinitialize
del db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] All tests passing (`pytest tests/ -v`)
- [ ] `.env` configured with production values
- [ ] Database migrated to PostgreSQL
- [ ] API keys in secrets manager (AWS Secrets, Vault)
- [ ] HTTPS configured
- [ ] CORS whitelist updated
- [ ] Rate limiting enabled
- [ ] Logging aggregation setup
- [ ] Monitoring & alerts configured
- [ ] Backups configured

### Environment Variables (Production)

```bash
# Django
DEBUG=False
SECRET_KEY=generate-new-key-using-secrets-manager
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com

# Database
DATABASE_URL=postgresql://user:pass@host:5432/algoagent

# Gemini
GEMINI_API_KEY=use-secrets-manager

# Security
JWT_SECRET=use-secrets-manager
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Features
DEBUG_MODE=False
USE_BACKTESTING_PY=True
USE_CONVERSATION_MEMORY=True
```

### Docker Deployment (Optional)

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "algoagent_api.wsgi:application", "--bind", "0.0.0.0:8000"]
```

**Build & Run:**
```bash
docker build -t algoagent .
docker run -p 8000:8000 -e GEMINI_API_KEY=$GEMINI_API_KEY algoagent
```

---

## Performance Tuning

### Backtest Performance

**Optimize for Speed:**
```python
# Use daily data instead of hourly
interval = "1d"  # Faster than "1h"

# Reduce date range for testing
start_date = "2024-01-01"
end_date = "2024-03-31"  # 3 months instead of 1 year

# Use simpler indicators
# ❌ Too many: RSI, MACD, Bollinger, Stochastic, ADX
# ✅ Better: RSI + SMA
```

### Database Performance

**Index Frequently Queried Fields:**
```python
# In models.py
class Strategy(models.Model):
    user = ForeignKey(User, db_index=True)
    name = CharField(max_length=255, db_index=True)
    created_at = DateTimeField(db_index=True)
```

### API Performance

**Enable Caching:**
```python
# In views.py
from django.views.decorators.cache import cache_page

@cache_page(60 * 5)  # Cache for 5 minutes
def get_indicators(request):
    ...
```

---

## Security Hardening

### 1. Environment Variables

```bash
# ❌ NEVER commit .env
echo ".env" >> .gitignore

# ✅ Use .env.example instead
cp .env .env.example
# Remove sensitive values from .env.example
```

### 2. Database

```bash
# ✅ Use strong password for superuser
python manage.py createsuperuser

# ✅ Migrate to PostgreSQL for production
# ✅ Enable database backups
```

### 3. API Security

```bash
# ✅ Use JWT tokens (already implemented)
# ✅ Set SHORT expiry (default 1 hour)
# ✅ Require HTTPS in production
# ✅ Enable CORS restrictions

# In .env
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
ALLOWED_HOSTS=yourdomain.com
```

### 4. Code Validation

```bash
# ✅ All generated code scanned (already implemented)
# ✅ Dangerous patterns rejected
# ✅ No hardcoded credentials allowed
```

---

## Monitoring & Logging

### Application Logs

**Location:** `logs/` directory (configure in settings.py)

**Log Level:** Set via environment
```bash
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

**View Logs:**
```bash
tail -f logs/algoagent.log
```

### Database Monitoring

```bash
# Check database size
python manage.py dbshell
SELECT SUM(pages) * 4096 / 1024 / 1024 AS size_mb FROM sqlite_master WHERE type='table';
```

### API Monitoring

```bash
# Monitor API requests
curl http://localhost:8000/api/health/
# Should return: {"status": "healthy"}
```

---

## Support Resources

### Documentation
- `ARCHITECTURE.md` - System design
- `STATUS.md` - Component status
- `PRODUCTION_API_GUIDE.md` - API reference
- `STRATEGY_QUICKSTART.md` - Strategy guide

### External Resources
- backtesting.py: https://kernc.github.io/backtesting.py/
- Gemini API: https://ai.google.dev/
- Django: https://docs.djangoproject.com/
- pytest: https://docs.pytest.org/

---

**END OF SETUP & INTEGRATION GUIDE**

For questions or issues, refer to `STATUS.md` troubleshooting section or contact the development team.
