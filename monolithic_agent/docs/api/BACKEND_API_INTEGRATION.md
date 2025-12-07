# Backend-to-API Integration Architecture

**Last Updated:** December 4, 2025  
**Status:** ✅ Production Ready  
**Version:** 2.0

---

## Overview

The AlgoAgent monolithic system features a complete Django REST API with full integration to backend autonomous capabilities. This document details the architecture, endpoints, and integration patterns.

---

## 🏗️ Architecture Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                          │
│                    (React/Vue/Angular/etc.)                    │
└────────────────────────────┬───────────────────────────────────┘
                             │ HTTP/REST
                             ▼
┌────────────────────────────────────────────────────────────────┐
│                    Django REST API Layer                       │
│                      (Port 8000)                               │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────────────────────────────────────────┐    │
│  │           Strategy API (StrategyViewSet)             │    │
│  ├──────────────────────────────────────────────────────┤    │
│  │                                                      │    │
│  │  • GET  /strategies/                                 │    │
│  │  • POST /strategies/                                 │    │
│  │  • GET  /strategies/{id}/                            │    │
│  │  • POST /strategies/generate_with_ai/               │    │
│  │  • POST /strategies/{id}/execute/                   │    │
│  │  • POST /strategies/{id}/fix_errors/                │    │
│  │  • GET  /strategies/{id}/execution_history/         │    │
│  │  • GET  /strategies/available_indicators/           │    │
│  │                                                      │    │
│  └──────────────────────────────────────────────────────┘    │
│                             │                                  │
│                             │ Imports & Calls                  │
│                             ▼                                  │
├────────────────────────────────────────────────────────────────┤
│                    Backend Integration Layer                   │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────────────┐  ┌──────────────────────────────┐  │
│  │ GeminiStrategy      │  │  KeyManager                   │  │
│  │ Generator           │◄─┤  (key_rotation.py)            │  │
│  │                     │  │  • 8 API keys                 │  │
│  │ • AI generation     │  │  • Load distribution          │  │
│  │ • Key rotation      │  │  • Health tracking            │  │
│  │ • Auto-fix loop     │  │  • Cooldown management        │  │
│  └──────────┬──────────┘  └──────────────────────────────┘  │
│             │                                                  │
│             ▼                                                  │
│  ┌─────────────────────┐  ┌──────────────────────────────┐  │
│  │ BotExecutor         │  │  ErrorAnalyzer                │  │
│  │                     │  │  (bot_error_fixer.py)         │  │
│  │ • Execute strategy  │  │  • 10 error types             │  │
│  │ • Capture results   │  │  • AI-powered fixes           │  │
│  │ • Store metrics     │  │  • Iterative fixing           │  │
│  │ • Track history     │  │  • Success tracking           │  │
│  └──────────┬──────────┘  └───────────┬──────────────────┘  │
│             │                          │                      │
│             ▼                          ▼                      │
│  ┌─────────────────────┐  ┌──────────────────────────────┐  │
│  │ IndicatorRegistry   │  │  Execution History DB         │  │
│  │                     │  │  (SQLite)                     │  │
│  │ • 7 indicators      │  │  • Timestamp                  │  │
│  │ • Parameter schemas │  │  • Metrics                    │  │
│  │ • Usage examples    │  │  • Strategy link              │  │
│  │ • Formatting        │  │  • Success/failure            │  │
│  └─────────────────────┘  └──────────────────────────────┘  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────┐
│                      Storage Layer                             │
├────────────────────────────────────────────────────────────────┤
│  • Django DB (PostgreSQL/SQLite) - Strategy metadata          │
│  • Execution History DB (SQLite) - Performance tracking       │
│  • File System - Generated strategy code                      │
│  • Results Storage - JSON/CSV backtest results                │
└────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Base URL
```
http://localhost:8000/api/strategies/
```

### Endpoint Overview

| Endpoint | Method | Purpose | Backend Integration |
|----------|--------|---------|---------------------|
| `/strategies/` | GET | List strategies | Django ORM |
| `/strategies/` | POST | Create strategy | Django ORM |
| `/strategies/{id}/` | GET | Get strategy | Django ORM |
| `/strategies/{id}/` | PUT | Update strategy | Django ORM |
| `/strategies/{id}/` | DELETE | Delete strategy | Django ORM |
| `/strategies/generate_with_ai/` | POST | Generate with AI | `gemini_strategy_generator.py` ✅ |
| `/strategies/{id}/execute/` | POST | Execute strategy | `bot_executor.py` ✅ |
| `/strategies/{id}/fix_errors/` | POST | Fix errors | `bot_error_fixer.py` ✅ |
| `/strategies/{id}/execution_history/` | GET | Get history | `bot_executor.py` (DB) ✅ |
| `/strategies/available_indicators/` | GET | List indicators | `indicator_registry.py` ✅ |

✅ = Backend Integration Complete

---

## 📋 Detailed Endpoint Specifications

### 1. Generate Strategy with AI (Key Rotation Enabled)

**Endpoint:** `POST /api/strategies/generate_with_ai/`

**Description:** Generates a trading strategy from natural language using AI with automatic key rotation across 8 Gemini API keys.

**Request:**
```json
{
  "description": "RSI strategy: buy when RSI < 30, sell when RSI > 70",
  "save_to_backtest_codes": true,
  "execute_after_generation": true
}
```

**Response:**
```json
{
  "strategy_id": 124,
  "status": "success",
  "file_path": "Backtest/codes/rsi_strategy_20251204.py",
  "key_used": "gemini_key_03",
  "key_rotation_active": true,
  "generation_time": 4.2,
  "execution_result": {
    "success": true,
    "return_pct": 12.3,
    "num_trades": 38,
    "win_rate": 0.57,
    "sharpe_ratio": 1.4
  }
}
```

**Backend Flow:**
```python
# In strategy_api/views.py
def generate_with_ai(self, request):
    from Backtest.gemini_strategy_generator import GeminiStrategyGenerator
    
    # Key rotation enabled here!
    generator = GeminiStrategyGenerator(enable_key_rotation=True)
    
    output_file, execution_result = generator.generate_and_save(
        description=description,
        execute_after_generation=execute_after
    )
```

**Key Rotation:** ✅ Active  
**Error Handling:** Automatic with up to 3 fix attempts  
**Rate Limiting:** Distributed across 8 keys

---

### 2. Execute Strategy

**Endpoint:** `POST /api/strategies/{id}/execute/`

**Description:** Executes a strategy and returns backtest results with performance metrics.

**Request:**
```json
{
  "test_symbol": "AAPL",
  "start_date": "2020-01-01",
  "end_date": "2023-12-31"
}
```

**Response:**
```json
{
  "success": true,
  "metrics": {
    "return_pct": 15.5,
    "num_trades": 45,
    "win_rate": 0.55,
    "sharpe_ratio": 1.2,
    "max_drawdown": -8.3,
    "execution_time": 2.1
  },
  "results_file": "Backtest/codes/results/strategy_123_20251204.json",
  "error_message": null
}
```

**Backend Flow:**
```python
# Uses BotExecutor
from Backtest.bot_executor import BotExecutor

executor = BotExecutor()
result = executor.execute_bot(
    strategy_file=strategy.file_path,
    test_symbol=test_symbol
)
```

**Features:**
- Real backtesting with `backtesting.py`
- Metric extraction and storage
- Error capture and reporting
- Results persistence

---

### 3. Fix Errors Automatically

**Endpoint:** `POST /api/strategies/{id}/fix_errors/`

**Description:** Automatically detects and fixes errors in generated strategies using AI.

**Request:**
```json
{
  "max_attempts": 3
}
```

**Response:**
```json
{
  "success": true,
  "attempts": 1,
  "total_time": 8.5,
  "fixes": [
    {
      "attempt": 1,
      "success": true,
      "error_type": "import_error",
      "error_message": "ModuleNotFoundError: No module named 'Backtest'",
      "fix_description": "Added sys.path manipulation to resolve imports",
      "timestamp": "2025-12-04T14:30:22Z"
    }
  ],
  "final_status": "working"
}
```

**Backend Flow:**
```python
# Uses BotErrorFixer
from Backtest.bot_error_fixer import BotErrorFixer
from Backtest.gemini_strategy_generator import GeminiStrategyGenerator

generator = GeminiStrategyGenerator(enable_key_rotation=True)
fix_attempts = generator.fix_bot_errors_iteratively(
    bot_file=strategy.file_path,
    max_attempts=max_attempts
)
```

**Error Types Supported:**
- ImportError
- SyntaxError
- AttributeError
- TypeError
- ValueError
- IndexError
- KeyError
- RuntimeError
- TimeoutError
- FileError

---

### 4. Get Execution History

**Endpoint:** `GET /api/strategies/{id}/execution_history/`

**Description:** Retrieves historical execution results for a strategy.

**Response:**
```json
{
  "strategy_id": 123,
  "strategy_name": "RSI Strategy",
  "file_path": "Backtest/codes/rsi_strategy.py",
  "total_executions": 5,
  "success_rate": 0.8,
  "executions": [
    {
      "timestamp": "2025-12-04T10:30:00Z",
      "success": true,
      "return_pct": 15.5,
      "num_trades": 45,
      "win_rate": 0.55,
      "sharpe_ratio": 1.2,
      "execution_time": 2.1
    },
    {
      "timestamp": "2025-12-03T14:20:00Z",
      "success": true,
      "return_pct": 12.3,
      "num_trades": 38,
      "win_rate": 0.57,
      "sharpe_ratio": 1.4,
      "execution_time": 1.9
    }
  ]
}
```

**Backend Flow:**
```python
# Queries execution history database
from Backtest.bot_executor import BotExecutor

executor = BotExecutor()
history = executor.get_strategy_history(strategy_name)
```

**Storage:** SQLite database at `Backtest/codes/results/execution_history.db`

---

### 5. Available Indicators

**Endpoint:** `GET /api/strategies/available_indicators/`

**Description:** Lists all pre-built technical indicators with parameter schemas.

**Response:**
```json
{
  "count": 7,
  "indicators": [
    {
      "name": "SMA",
      "display_name": "Simple Moving Average",
      "description": "Pre-built SMA indicator",
      "parameters": [
        {
          "name": "period",
          "type": "int",
          "default": 20,
          "description": "Number of periods for moving average"
        }
      ],
      "example": "sma = self.I(SMA, self.data.Close, period=20)",
      "usage": "Use in strategy: if self.data.Close[-1] > sma[-1]: self.buy()"
    },
    {
      "name": "EMA",
      "display_name": "Exponential Moving Average",
      "parameters": [
        {
          "name": "period",
          "type": "int",
          "default": 12
        }
      ],
      "example": "ema = self.I(EMA, self.data.Close, period=12)"
    },
    {
      "name": "RSI",
      "display_name": "Relative Strength Index",
      "parameters": [
        {
          "name": "period",
          "type": "int",
          "default": 14
        }
      ],
      "example": "rsi = self.I(RSI, self.data.Close, period=14)"
    },
    {
      "name": "MACD",
      "display_name": "Moving Average Convergence Divergence",
      "parameters": [
        {
          "name": "fast",
          "type": "int",
          "default": 12
        },
        {
          "name": "slow",
          "type": "int",
          "default": 26
        },
        {
          "name": "signal",
          "type": "int",
          "default": 9
        }
      ],
      "example": "macd = self.I(MACD, self.data.Close, fast=12, slow=26, signal=9)"
    },
    {
      "name": "BollingerBands",
      "display_name": "Bollinger Bands",
      "parameters": [
        {
          "name": "period",
          "type": "int",
          "default": 20
        },
        {
          "name": "std_dev",
          "type": "float",
          "default": 2.0
        }
      ],
      "example": "bb = self.I(BollingerBands, self.data.Close, period=20, std_dev=2.0)"
    },
    {
      "name": "ATR",
      "display_name": "Average True Range",
      "parameters": [
        {
          "name": "period",
          "type": "int",
          "default": 14
        }
      ],
      "example": "atr = self.I(ATR, self.data.High, self.data.Low, self.data.Close, period=14)"
    },
    {
      "name": "Stochastic",
      "display_name": "Stochastic Oscillator",
      "parameters": [
        {
          "name": "k_period",
          "type": "int",
          "default": 14
        },
        {
          "name": "d_period",
          "type": "int",
          "default": 3
        }
      ],
      "example": "stoch = self.I(Stochastic, self.data.High, self.data.Low, self.data.Close, k_period=14, d_period=3)"
    }
  ]
}
```

**Backend Flow:**
```python
# Reads from indicator registry
from Backtest.indicator_registry import INDICATOR_REGISTRY

indicators = []
for name, info in INDICATOR_REGISTRY.items():
    if info.get('available', False):
        indicators.append({...})
```

---

## 🔐 Key Rotation System

### Architecture

```
┌─────────────────────────────────────────────────────┐
│              KeyManager (key_rotation.py)           │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  Key 1   │  │  Key 2   │  │  Key 3   │  ...   │
│  ├──────────┤  ├──────────┤  ├──────────┤        │
│  │ RPM: 60  │  │ RPM: 60  │  │ RPM: 60  │        │
│  │ TPM: 1M  │  │ TPM: 1M  │  │ TPM: 1M  │        │
│  │ Active   │  │ Active   │  │ Cooldown │        │
│  └──────────┘  └──────────┘  └──────────┘        │
│                                                     │
│  Selection Algorithm:                              │
│  1. Filter by model preference                     │
│  2. Check cooldown status                          │
│  3. Verify RPM/TPM capacity (Redis)                │
│  4. Shuffle for load distribution                  │
│  5. Return first available                         │
│                                                     │
│  Health Tracking:                                  │
│  • Last used timestamp                             │
│  • Error count                                     │
│  • Success count                                   │
│  • Cooldown until timestamp                        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Configuration

**Environment Variables (.env):**
```env
ENABLE_KEY_ROTATION=true
SECRET_STORE_TYPE=env
REDIS_URL=redis://localhost:6379/0

# 8 API Keys
GEMINI_KEY_gemini_key_01=AIza...
GEMINI_KEY_gemini_key_02=AIza...
GEMINI_KEY_gemini_key_03=AIza...
GEMINI_KEY_gemini_key_04=AIza...
GEMINI_KEY_gemini_key_05=AIza...
GEMINI_KEY_gemini_key_06=AIza...
GEMINI_KEY_gemini_key_07=AIza...
GEMINI_KEY_gemini_key_08=AIza...
```

### Features

- **Load Distribution:** Rotates across 8 keys
- **Rate Limiting:** Tracks RPM/TPM per key
- **Health Monitoring:** Tracks success/error rates
- **Automatic Cooldown:** Exponential backoff on errors
- **Failover:** Automatic switching on errors

---

## 📊 Data Flow

### Strategy Generation Flow

```
User Request
    │
    ▼
API Endpoint (/strategies/generate_with_ai/)
    │
    ├─→ KeyManager.select_key()
    │   └─→ Returns available API key
    │
    ├─→ GeminiStrategyGenerator.generate_and_save()
    │   ├─→ Calls Gemini API with selected key
    │   ├─→ Generates Python strategy code
    │   ├─→ Saves to Backtest/codes/
    │   └─→ Optional: Execute after generation
    │
    ├─→ BotExecutor.execute_bot() [if execute_after=true]
    │   ├─→ Runs strategy with backtesting.py
    │   ├─→ Captures metrics
    │   └─→ Stores in execution_history.db
    │
    └─→ Return response with results
```

### Error Fixing Flow

```
Strategy Execution Fails
    │
    ▼
BotExecutor detects error
    │
    ├─→ ErrorAnalyzer.classify_error()
    │   └─→ Returns error type + severity
    │
    ├─→ BotErrorFixer.fix_errors_iteratively()
    │   │
    │   ├─→ Iteration 1:
    │   │   ├─→ Generate fix with AI
    │   │   ├─→ Apply patch to file
    │   │   └─→ Re-execute
    │   │
    │   ├─→ Iteration 2 (if needed):
    │   │   ├─→ Analyze new error
    │   │   ├─→ Generate different fix
    │   │   └─→ Re-execute
    │   │
    │   └─→ Iteration 3 (if needed):
    │       └─→ Final attempt
    │
    └─→ Return fix history + success status
```

---

## 🗄️ Database Schema

### Django Models (Django ORM)

**Strategy Model:**
```python
class Strategy(models.Model):
    name = CharField(max_length=200)
    description = TextField()
    file_path = CharField(max_length=500)
    strategy_code = TextField()
    status = CharField(max_length=50)  # 'generated', 'executed', 'failed', 'working'
    template = ForeignKey(StrategyTemplate)
    created_by = ForeignKey(User)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    last_validated = DateTimeField(null=True)
    version = IntegerField(default=1)
```

### Execution History (SQLite)

**Location:** `Backtest/codes/results/execution_history.db`

**Schema:**
```sql
CREATE TABLE execution_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_name TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    return_pct REAL,
    num_trades INTEGER,
    win_rate REAL,
    sharpe_ratio REAL,
    max_drawdown REAL,
    execution_time REAL,
    test_symbol TEXT,
    results_file TEXT,
    error_message TEXT
);

CREATE INDEX idx_strategy_timestamp ON execution_history(strategy_name, timestamp DESC);
CREATE INDEX idx_success ON execution_history(success, timestamp DESC);
```

---

## 🔧 Integration Patterns

### Pattern 1: Generate + Execute + Fix

```python
# API handles the full workflow
POST /api/strategies/generate_with_ai/
{
  "description": "RSI strategy...",
  "execute_after_generation": true,
  "auto_fix_on_error": true
}

# Backend flow:
1. Generate strategy code
2. Execute with BotExecutor
3. If error: Automatically fix
4. Return final results
```

### Pattern 2: Separate Execution

```python
# Generate first
POST /api/strategies/generate_with_ai/
{
  "description": "RSI strategy...",
  "execute_after_generation": false
}

# Then execute later
POST /api/strategies/{id}/execute/
{
  "test_symbol": "AAPL"
}

# Fix if needed
POST /api/strategies/{id}/fix_errors/
```

### Pattern 3: Historical Analysis

```python
# Get all executions
GET /api/strategies/{id}/execution_history/

# Analyze trends
for execution in executions:
    if execution['success']:
        analyze_performance(execution['metrics'])
```

---

## 🚀 Deployment

### Production Checklist

- [ ] Set `DEBUG=False` in Django settings
- [ ] Configure proper database (PostgreSQL recommended)
- [ ] Set up Redis for key rotation (optional but recommended)
- [ ] Configure all 8 API keys in production environment
- [ ] Set up proper CORS settings
- [ ] Configure rate limiting at API gateway level
- [ ] Set up monitoring and logging
- [ ] Configure backup for execution_history.db
- [ ] Test all endpoints in staging
- [ ] Document API keys for team access

### Environment Variables

```env
# Django
DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DATABASE_URL=postgresql://user:pass@localhost/algoagent

# Key Rotation
ENABLE_KEY_ROTATION=true
SECRET_STORE_TYPE=env
REDIS_URL=redis://localhost:6379/0

# API Keys (8 required)
GEMINI_KEY_gemini_key_01=...
GEMINI_KEY_gemini_key_02=...
...
```

### Scaling Considerations

- **Horizontal Scaling:** Stateless API allows easy load balancing
- **Redis Required:** For multi-instance key rotation coordination
- **Database:** Consider read replicas for execution history queries
- **File Storage:** Consider cloud storage (S3) for generated strategies
- **Rate Limiting:** Implement at API gateway level

---

## 📈 Monitoring & Metrics

### Key Metrics to Track

1. **API Performance**
   - Request latency per endpoint
   - Error rates
   - Throughput (requests/second)

2. **Key Rotation Health**
   - Active keys count
   - Key error rates
   - Cooldown frequency
   - Load distribution

3. **Strategy Generation**
   - Generation success rate
   - Average generation time
   - Fix iteration statistics
   - Execution success rate

4. **Execution Metrics**
   - Average execution time
   - Success vs failure ratio
   - Performance metrics distribution
   - Error type frequency

### Recommended Tools

- **APM:** New Relic, DataDog, or Application Insights
- **Logging:** ELK Stack or CloudWatch
- **Monitoring:** Prometheus + Grafana
- **Alerts:** PagerDuty or OpsGenie

---

## 🔍 Troubleshooting

### Common Issues

**1. Endpoints Return 404**
- **Cause:** Django server not restarted after code changes
- **Fix:** Restart Django server
- **Verify:** Run `check_routes.py` to confirm registration

**2. Key Rotation Not Working**
- **Cause:** `ENABLE_KEY_ROTATION=false` or missing keys
- **Fix:** Check `.env` configuration
- **Verify:** Check logs for key selection messages

**3. Import Errors in Generated Strategies**
- **Cause:** Path issues or missing modules
- **Fix:** System prompt includes proper path setup
- **Verify:** Check generated code for `sys.path` manipulation

**4. Execution Timeout**
- **Cause:** Large dataset or complex strategy
- **Fix:** Increase timeout in BotExecutor
- **Verify:** Check execution logs

---

## 📚 Related Documentation

- **[Backend Error Fixing](../../AUTOMATED_ERROR_FIXING_COMPLETE.md)** - Error fixing system details
- **[E2E Autonomous Agent](../../E2E_AUTONOMOUS_AGENT_SUMMARY.md)** - Backend capabilities overview
- **[Quick Start Guide](../../QUICK_START.md)** - Getting started with the system
- **[Production API Guide](PRODUCTION_API_GUIDE.md)** - Advanced production features

---

## ✅ Integration Checklist

- [x] Backend autonomous system working
- [x] Django REST API infrastructure
- [x] 5 core endpoints implemented
- [x] Key rotation enabled at API level
- [x] Error fixing accessible via HTTP
- [x] Execution history tracked in database
- [x] Indicator registry exposed
- [x] Routes registered with Django router
- [x] Error handling implemented
- [x] Test suite created
- [x] Documentation complete

---

**Architecture Status:** ✅ Production Ready  
**Last Updated:** December 4, 2025  
**Version:** 2.0 - Full Backend-to-API Integration
