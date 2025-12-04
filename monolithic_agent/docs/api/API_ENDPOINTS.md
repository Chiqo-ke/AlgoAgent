# API Endpoints Reference

**Last Updated:** December 4, 2025  
**Base URL:** `http://localhost:8000/api/`  
**Version:** 2.0

---

## Table of Contents

- [Authentication](#authentication)
- [Strategy Endpoints](#strategy-endpoints)
- [AI Generation](#ai-generation)
- [Execution](#execution)
- [Error Management](#error-management)
- [Indicators](#indicators)
- [Rate Limits](#rate-limits)
- [Error Codes](#error-codes)

---

## Authentication

Currently using AllowAny permissions for development. Production should implement token-based authentication.

**Headers Required:**
```http
Content-Type: application/json
```

**Production Headers (future):**
```http
Content-Type: application/json
Authorization: Bearer <your_token>
```

---

## Strategy Endpoints

### List All Strategies

**GET** `/strategies/`

Returns a paginated list of all strategies.

**Query Parameters:**
- `page` (integer, optional): Page number (default: 1)
- `page_size` (integer, optional): Results per page (default: 20)
- `status` (string, optional): Filter by status ('generated', 'executed', 'failed', 'working')
- `ordering` (string, optional): Sort field (use `-` prefix for descending)

**Example Request:**
```http
GET /api/strategies/?status=working&ordering=-created_at&page=1
```

**Example Response:**
```json
{
  "count": 45,
  "next": "http://localhost:8000/api/strategies/?page=2",
  "previous": null,
  "results": [
    {
      "id": 123,
      "name": "RSI Strategy v2",
      "description": "Buy when RSI < 30, sell when RSI > 70",
      "file_path": "Backtest/codes/rsi_strategy_20251204.py",
      "status": "working",
      "created_at": "2025-12-04T10:30:00Z",
      "updated_at": "2025-12-04T11:45:00Z",
      "last_validated": "2025-12-04T11:45:00Z",
      "version": 2,
      "created_by": {
        "id": 1,
        "username": "admin"
      }
    }
  ]
}
```

---

### Get Single Strategy

**GET** `/strategies/{id}/`

Returns details for a specific strategy.

**Path Parameters:**
- `id` (integer, required): Strategy ID

**Example Request:**
```http
GET /api/strategies/123/
```

**Example Response:**
```json
{
  "id": 123,
  "name": "RSI Strategy v2",
  "description": "Buy when RSI < 30, sell when RSI > 70",
  "file_path": "Backtest/codes/rsi_strategy_20251204.py",
  "strategy_code": "from backtesting import Strategy...",
  "status": "working",
  "template": {
    "id": 1,
    "name": "Basic RSI Template"
  },
  "created_by": {
    "id": 1,
    "username": "admin"
  },
  "created_at": "2025-12-04T10:30:00Z",
  "updated_at": "2025-12-04T11:45:00Z",
  "last_validated": "2025-12-04T11:45:00Z",
  "version": 2
}
```

---

### Create Strategy

**POST** `/strategies/`

Creates a new strategy manually (without AI generation).

**Request Body:**
```json
{
  "name": "My Custom Strategy",
  "description": "Custom MACD strategy",
  "strategy_code": "from backtesting import Strategy...",
  "template_id": 1
}
```

**Example Response:**
```json
{
  "id": 124,
  "name": "My Custom Strategy",
  "description": "Custom MACD strategy",
  "file_path": "Backtest/codes/custom_strategy_124.py",
  "status": "generated",
  "created_at": "2025-12-04T14:30:00Z",
  "message": "Strategy created successfully"
}
```

---

### Update Strategy

**PUT** `/strategies/{id}/`  
**PATCH** `/strategies/{id}/`

Updates an existing strategy.

**Request Body (PUT - all fields required):**
```json
{
  "name": "Updated Strategy Name",
  "description": "Updated description",
  "strategy_code": "from backtesting import Strategy..."
}
```

**Request Body (PATCH - partial update):**
```json
{
  "description": "Updated description only"
}
```

---

### Delete Strategy

**DELETE** `/strategies/{id}/`

Deletes a strategy and its associated files.

**Example Response:**
```json
{
  "message": "Strategy deleted successfully"
}
```

---

## AI Generation

### Generate Strategy with AI

**POST** `/strategies/generate_with_ai/`

Generates a trading strategy from natural language description using AI with automatic key rotation.

**Request Body:**
```json
{
  "description": "Create an RSI strategy that buys when RSI is below 30 and sells when RSI is above 70. Use a 14-period RSI.",
  "save_to_backtest_codes": true,
  "execute_after_generation": true,
  "auto_fix_on_error": true,
  "test_symbol": "AAPL",
  "start_date": "2020-01-01",
  "end_date": "2023-12-31"
}
```

**Request Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `description` | string | ✅ Yes | - | Natural language strategy description |
| `save_to_backtest_codes` | boolean | No | true | Save to Backtest/codes/ directory |
| `execute_after_generation` | boolean | No | false | Execute immediately after generation |
| `auto_fix_on_error` | boolean | No | true | Automatically fix errors if execution fails |
| `test_symbol` | string | No | "AAPL" | Stock symbol for backtesting |
| `start_date` | string | No | "2020-01-01" | Backtest start date (YYYY-MM-DD) |
| `end_date` | string | No | "2023-12-31" | Backtest end date (YYYY-MM-DD) |

**Example Response (Success):**
```json
{
  "success": true,
  "strategy_id": 125,
  "strategy_name": "RSI Strategy",
  "file_path": "Backtest/codes/rsi_strategy_20251204_143022.py",
  "status": "working",
  "key_used": "gemini_key_03",
  "key_rotation_active": true,
  "generation_time": 4.2,
  "execution_result": {
    "success": true,
    "metrics": {
      "return_pct": 15.5,
      "num_trades": 45,
      "win_rate": 0.55,
      "sharpe_ratio": 1.2,
      "max_drawdown": -8.3,
      "execution_time": 2.1
    },
    "results_file": "Backtest/codes/results/strategy_125_20251204.json"
  },
  "error_fixing": {
    "required": false,
    "attempts": 0
  }
}
```

**Example Response (With Error Fixing):**
```json
{
  "success": true,
  "strategy_id": 126,
  "strategy_name": "MACD Strategy",
  "file_path": "Backtest/codes/macd_strategy_20251204_143522.py",
  "status": "working",
  "key_used": "gemini_key_05",
  "key_rotation_active": true,
  "generation_time": 3.8,
  "execution_result": {
    "success": true,
    "metrics": {
      "return_pct": 12.3,
      "num_trades": 38,
      "win_rate": 0.57,
      "sharpe_ratio": 1.4
    }
  },
  "error_fixing": {
    "required": true,
    "attempts": 1,
    "total_fix_time": 6.2,
    "fixes": [
      {
        "attempt": 1,
        "success": true,
        "error_type": "import_error",
        "error_message": "ModuleNotFoundError: No module named 'Backtest'",
        "fix_description": "Added sys.path manipulation for imports",
        "timestamp": "2025-12-04T14:35:30Z"
      }
    ]
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Generation failed after 3 attempts",
  "error_type": "generation_failure",
  "details": {
    "last_error": "API rate limit exceeded",
    "attempts": 3,
    "key_used": "gemini_key_07"
  }
}
```

---

## Execution

### Execute Strategy

**POST** `/strategies/{id}/execute/`

Executes a strategy with backtesting and returns performance metrics.

**Path Parameters:**
- `id` (integer, required): Strategy ID

**Request Body:**
```json
{
  "test_symbol": "AAPL",
  "start_date": "2020-01-01",
  "end_date": "2023-12-31",
  "initial_capital": 10000,
  "commission": 0.002
}
```

**Request Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `test_symbol` | string | No | "AAPL" | Stock symbol for backtesting |
| `start_date` | string | No | "2020-01-01" | Backtest start date |
| `end_date` | string | No | "2023-12-31" | Backtest end date |
| `initial_capital` | number | No | 10000 | Starting capital |
| `commission` | number | No | 0.002 | Commission per trade (0.2%) |

**Example Response (Success):**
```json
{
  "success": true,
  "strategy_id": 123,
  "strategy_name": "RSI Strategy v2",
  "execution_id": "exec_20251204_143022",
  "timestamp": "2025-12-04T14:30:22Z",
  "metrics": {
    "return_pct": 15.5,
    "num_trades": 45,
    "win_rate": 0.55,
    "sharpe_ratio": 1.2,
    "max_drawdown": -8.3,
    "sortino_ratio": 1.6,
    "calmar_ratio": 1.9,
    "execution_time": 2.1
  },
  "test_parameters": {
    "symbol": "AAPL",
    "start_date": "2020-01-01",
    "end_date": "2023-12-31",
    "initial_capital": 10000,
    "commission": 0.002
  },
  "results_file": "Backtest/codes/results/strategy_123_20251204.json",
  "status": "executed"
}
```

**Example Response (Failure):**
```json
{
  "success": false,
  "strategy_id": 123,
  "error_type": "runtime_error",
  "error_message": "Strategy execution failed: Division by zero in calculate_position_size",
  "error_details": {
    "traceback": "File 'strategy.py', line 45, in next\n  size = 1000 / price",
    "line_number": 45
  },
  "suggestion": "Use the fix_errors endpoint to automatically fix this error"
}
```

---

### Get Execution History

**GET** `/strategies/{id}/execution_history/`

Retrieves historical execution results for a strategy.

**Path Parameters:**
- `id` (integer, required): Strategy ID

**Query Parameters:**
- `limit` (integer, optional): Maximum number of results (default: 20, max: 100)
- `success_only` (boolean, optional): Filter for successful executions only

**Example Request:**
```http
GET /api/strategies/123/execution_history/?limit=10&success_only=true
```

**Example Response:**
```json
{
  "strategy_id": 123,
  "strategy_name": "RSI Strategy v2",
  "file_path": "Backtest/codes/rsi_strategy_20251204.py",
  "total_executions": 5,
  "successful_executions": 4,
  "failed_executions": 1,
  "success_rate": 0.8,
  "average_return": 13.2,
  "executions": [
    {
      "execution_id": "exec_20251204_143022",
      "timestamp": "2025-12-04T14:30:22Z",
      "success": true,
      "metrics": {
        "return_pct": 15.5,
        "num_trades": 45,
        "win_rate": 0.55,
        "sharpe_ratio": 1.2,
        "max_drawdown": -8.3
      },
      "test_parameters": {
        "symbol": "AAPL",
        "start_date": "2020-01-01",
        "end_date": "2023-12-31"
      },
      "execution_time": 2.1
    },
    {
      "execution_id": "exec_20251203_102015",
      "timestamp": "2025-12-03T10:20:15Z",
      "success": true,
      "metrics": {
        "return_pct": 12.3,
        "num_trades": 38,
        "win_rate": 0.57,
        "sharpe_ratio": 1.4
      },
      "execution_time": 1.9
    }
  ]
}
```

---

## Error Management

### Fix Errors Automatically

**POST** `/strategies/{id}/fix_errors/`

Automatically detects and fixes errors in a strategy using AI.

**Path Parameters:**
- `id` (integer, required): Strategy ID

**Request Body:**
```json
{
  "max_attempts": 3,
  "error_context": "Strategy fails during execution with ImportError"
}
```

**Request Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `max_attempts` | integer | No | 3 | Maximum fix attempts (1-5) |
| `error_context` | string | No | null | Additional context about the error |

**Example Response (Success):**
```json
{
  "success": true,
  "strategy_id": 123,
  "total_attempts": 1,
  "total_time": 8.5,
  "final_status": "working",
  "fixes": [
    {
      "attempt": 1,
      "success": true,
      "error_type": "import_error",
      "error_message": "ModuleNotFoundError: No module named 'Backtest'",
      "fix_description": "Added sys.path manipulation to resolve Backtest module imports",
      "code_changes": {
        "lines_added": 3,
        "lines_modified": 0,
        "lines_deleted": 0
      },
      "timestamp": "2025-12-04T14:30:22Z",
      "execution_time": 8.5
    }
  ],
  "verification": {
    "execution_successful": true,
    "metrics": {
      "return_pct": 15.5,
      "num_trades": 45,
      "win_rate": 0.55
    }
  }
}
```

**Example Response (Partial Success):**
```json
{
  "success": false,
  "strategy_id": 124,
  "total_attempts": 3,
  "total_time": 24.3,
  "final_status": "failed",
  "fixes": [
    {
      "attempt": 1,
      "success": false,
      "error_type": "import_error",
      "fix_description": "Attempted to fix imports",
      "timestamp": "2025-12-04T14:30:22Z"
    },
    {
      "attempt": 2,
      "success": false,
      "error_type": "syntax_error",
      "fix_description": "Fixed syntax but introduced new error",
      "timestamp": "2025-12-04T14:30:30Z"
    },
    {
      "attempt": 3,
      "success": false,
      "error_type": "runtime_error",
      "error_message": "Unable to resolve complex logic error",
      "timestamp": "2025-12-04T14:30:46Z"
    }
  ],
  "message": "Strategy could not be automatically fixed. Manual intervention required.",
  "suggestion": "Review the generated code manually and check for logical errors"
}
```

**Supported Error Types:**
- `import_error` - Missing imports or module path issues
- `syntax_error` - Python syntax errors
- `attribute_error` - Missing attributes or methods
- `type_error` - Type mismatches
- `value_error` - Invalid values
- `index_error` - Array index out of bounds
- `key_error` - Dictionary key not found
- `runtime_error` - General runtime errors
- `timeout_error` - Execution timeout
- `file_error` - File I/O errors

---

## Indicators

### Get Available Indicators

**GET** `/strategies/available_indicators/`

Returns a list of all pre-built technical indicators with parameter schemas and usage examples.

**Example Request:**
```http
GET /api/strategies/available_indicators/
```

**Example Response:**
```json
{
  "count": 7,
  "indicators": [
    {
      "name": "SMA",
      "display_name": "Simple Moving Average",
      "description": "Pre-built SMA indicator with configurable period",
      "category": "trend",
      "parameters": [
        {
          "name": "period",
          "type": "int",
          "default": 20,
          "min": 1,
          "max": 200,
          "description": "Number of periods for moving average calculation"
        }
      ],
      "returns": {
        "type": "array",
        "description": "Array of SMA values"
      },
      "example_usage": "sma = self.I(SMA, self.data.Close, period=20)",
      "strategy_integration": "if self.data.Close[-1] > sma[-1]:\n    self.buy()",
      "documentation_url": null
    },
    {
      "name": "EMA",
      "display_name": "Exponential Moving Average",
      "description": "Exponentially weighted moving average",
      "category": "trend",
      "parameters": [
        {
          "name": "period",
          "type": "int",
          "default": 12,
          "min": 1,
          "max": 200
        }
      ],
      "example_usage": "ema = self.I(EMA, self.data.Close, period=12)"
    },
    {
      "name": "RSI",
      "display_name": "Relative Strength Index",
      "description": "Momentum oscillator (0-100)",
      "category": "momentum",
      "parameters": [
        {
          "name": "period",
          "type": "int",
          "default": 14,
          "min": 2,
          "max": 50
        }
      ],
      "returns": {
        "type": "array",
        "description": "Array of RSI values between 0-100"
      },
      "example_usage": "rsi = self.I(RSI, self.data.Close, period=14)",
      "strategy_integration": "if rsi[-1] < 30:\n    self.buy()  # Oversold\nelif rsi[-1] > 70:\n    self.sell()  # Overbought"
    },
    {
      "name": "MACD",
      "display_name": "Moving Average Convergence Divergence",
      "description": "Trend-following momentum indicator",
      "category": "momentum",
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
      "returns": {
        "type": "object",
        "description": "Object with 'macd', 'signal', and 'histogram' arrays"
      },
      "example_usage": "macd_result = self.I(MACD, self.data.Close, fast=12, slow=26, signal=9)"
    },
    {
      "name": "BollingerBands",
      "display_name": "Bollinger Bands",
      "description": "Volatility bands around price",
      "category": "volatility",
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
      "returns": {
        "type": "object",
        "description": "Object with 'upper', 'middle', and 'lower' band arrays"
      },
      "example_usage": "bb = self.I(BollingerBands, self.data.Close, period=20, std_dev=2.0)"
    },
    {
      "name": "ATR",
      "display_name": "Average True Range",
      "description": "Volatility indicator",
      "category": "volatility",
      "parameters": [
        {
          "name": "period",
          "type": "int",
          "default": 14
        }
      ],
      "example_usage": "atr = self.I(ATR, self.data.High, self.data.Low, self.data.Close, period=14)"
    },
    {
      "name": "Stochastic",
      "display_name": "Stochastic Oscillator",
      "description": "Momentum indicator (0-100)",
      "category": "momentum",
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
      "returns": {
        "type": "object",
        "description": "Object with '%K' and '%D' arrays"
      },
      "example_usage": "stoch = self.I(Stochastic, self.data.High, self.data.Low, self.data.Close, k_period=14, d_period=3)"
    }
  ]
}
```

---

## Rate Limits

### Current Limits (Development)

No rate limits enforced in development mode.

### Production Limits (Recommended)

| Endpoint | Rate Limit | Notes |
|----------|-----------|-------|
| `/strategies/` (GET) | 60 req/min | List operations |
| `/strategies/` (POST) | 10 req/min | Strategy creation |
| `/strategies/generate_with_ai/` | 5 req/min | AI generation (resource intensive) |
| `/strategies/{id}/execute/` | 10 req/min | Backtesting execution |
| `/strategies/{id}/fix_errors/` | 5 req/min | Error fixing (resource intensive) |
| `/strategies/available_indicators/` | 60 req/min | Static data |

### Rate Limit Headers

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1701705600
```

---

## Error Codes

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Successful request |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required (production) |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Server temporarily unavailable |

### Application Error Codes

```json
{
  "error_code": "GENERATION_FAILED",
  "error_message": "AI generation failed after 3 attempts",
  "details": {
    "last_error": "API rate limit exceeded",
    "attempts": 3
  }
}
```

**Error Code Reference:**

| Code | Description | Resolution |
|------|-------------|------------|
| `GENERATION_FAILED` | AI generation unsuccessful | Try again or check API keys |
| `EXECUTION_FAILED` | Strategy execution error | Use fix_errors endpoint |
| `INVALID_STRATEGY_CODE` | Malformed Python code | Review generated code |
| `FILE_NOT_FOUND` | Strategy file missing | Regenerate strategy |
| `IMPORT_ERROR` | Module import failure | Use fix_errors endpoint |
| `RUNTIME_ERROR` | Execution runtime error | Check strategy logic |
| `TIMEOUT_ERROR` | Operation timeout | Reduce backtest period |
| `KEY_ROTATION_ERROR` | No available API keys | Check key configuration |
| `RATE_LIMIT_EXCEEDED` | API rate limit hit | Wait and retry |
| `DATABASE_ERROR` | Database operation failed | Contact support |

---

## Pagination

All list endpoints support pagination.

**Query Parameters:**
- `page` (integer): Page number (default: 1)
- `page_size` (integer): Results per page (default: 20, max: 100)

**Response Format:**
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/strategies/?page=2",
  "previous": null,
  "results": [...]
}
```

---

## Filtering & Sorting

### Available Filters

**Strategies:**
- `status`: Filter by status ('generated', 'executed', 'failed', 'working')
- `created_by`: Filter by user ID
- `created_at__gte`: Created after date
- `created_at__lte`: Created before date

**Example:**
```http
GET /api/strategies/?status=working&created_at__gte=2025-12-01
```

### Sorting

Use `ordering` parameter with field name. Prefix with `-` for descending.

**Available Fields:**
- `created_at`
- `updated_at`
- `name`
- `status`

**Example:**
```http
GET /api/strategies/?ordering=-created_at
```

---

## WebSocket Support (Future)

Real-time updates via WebSocket (planned for future release):

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/strategies/');

// Listen for execution updates
ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Execution update:', data);
};
```

---

## Additional Resources

- **[Backend-API Integration](BACKEND_API_INTEGRATION.md)** - Architecture details
- **[Production API Guide](PRODUCTION_API_GUIDE.md)** - Production deployment
- **[Quick Reference](../guides/QUICK_REFERENCE.md)** - Common tasks
- **[Integration Status](INTEGRATION_STATUS.md)** - Current status

---

**Last Updated:** December 4, 2025  
**Version:** 2.0 - Backend-to-API Integration Complete
