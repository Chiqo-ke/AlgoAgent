# Production API Integration Guide

## Overview

The AlgoAgent API has been enhanced with production-hardened endpoints that integrate all 6 production components:

1. **Canonical Schema v2** - Pydantic validation
2. **State Manager** - SQLite lifecycle tracking
3. **Safe Tools** - Sandboxed file operations
4. **Output Validator** - Code safety checks
5. **Sandbox Orchestrator** - Docker isolation
6. **Git Patch Manager** - Version control workflow

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Django REST API                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────┐        ┌──────────────────┐     │
│  │  Strategy API    │        │  Backtest API    │     │
│  │  (Original)      │        │  (Original)      │     │
│  └──────────────────┘        └──────────────────┘     │
│                                                         │
│  ┌──────────────────┐        ┌──────────────────┐     │
│  │  Production      │        │  Production      │     │
│  │  Strategy API    │        │  Backtest API    │     │
│  │  (Enhanced)      │        │  (Enhanced)      │     │
│  └────────┬─────────┘        └─────────┬────────┘     │
│           │                            │              │
├───────────┼────────────────────────────┼──────────────┤
│           │  Production Components     │              │
│           │                            │              │
│  ┌────────▼────────┐  ┌─────────────┐ │              │
│  │ Canonical       │  │ State       │ │              │
│  │ Schema v2       │  │ Manager     │ │              │
│  │ (Pydantic)      │  │ (SQLite)    │ │              │
│  └─────────────────┘  └─────────────┘ │              │
│                                        │              │
│  ┌─────────────────┐  ┌─────────────┐ │              │
│  │ Output          │  │ Safe Tools  │ │              │
│  │ Validator       │  │ (Sandboxed) │ │              │
│  │ (Safety Checks) │  │             │ │              │
│  └─────────────────┘  └─────────────┘ │              │
│                                        │              │
│  ┌─────────────────┐  ┌─────────────┐ │              │
│  │ Sandbox         │  │ Git Patch   │ │              │
│  │ Orchestrator    │  │ Manager     │ │              │
│  │ (Docker)        │  │ (Version)   │ │              │
│  └─────────────────┘  └─────────────┘ │              │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## API Endpoints

### Production Strategy API

Base URL: `/api/production/strategies/`

#### 1. Validate Schema
**POST** `/api/production/strategies/validate-schema/`

Validates strategy JSON against Pydantic schema.

**Request:**
```json
{
  "name": "RSI_Reversal",
  "description": "RSI reversal strategy",
  "parameters": {
    "rsi_period": 14,
    "oversold": 30,
    "overbought": 70
  },
  "indicators": {
    "rsi": {
      "period": 14,
      "source": "close"
    }
  },
  "entry_rules": [
    "rsi < 30",
    "volume > sma(volume, 20)"
  ],
  "exit_rules": [
    "rsi > 70"
  ]
}
```

**Response (Success):**
```json
{
  "status": "valid",
  "message": "Strategy schema is valid",
  "validated_data": { ... },
  "schema_version": "2.0"
}
```

**Response (Error):**
```json
{
  "status": "invalid",
  "message": "Strategy schema validation failed",
  "errors": [
    {
      "loc": ["parameters", "rsi_period"],
      "msg": "Field required",
      "type": "missing"
    }
  ],
  "details": "..."
}
```

#### 2. Validate Code
**POST** `/api/production/strategies/validate-code/`

Checks generated code for dangerous patterns.

**Request:**
```json
{
  "code": "class MyStrategy:\n    def on_bar(self):\n        pass",
  "strict_mode": true
}
```

**Response (Safe):**
```json
{
  "status": "validated",
  "safe": true,
  "message": "Code passed all safety checks",
  "formatted_code": "...",
  "checks_passed": [
    "No dangerous imports",
    "No system commands",
    "No eval/exec usage",
    "Syntax valid",
    "AST analysis passed"
  ]
}
```

**Response (Unsafe):**
```json
{
  "status": "rejected",
  "safe": false,
  "message": "Code contains dangerous patterns",
  "issues": [
    "Dangerous import detected: os.system",
    "Dangerous function: eval()"
  ],
  "severity": "high"
}
```

#### 3. Sandbox Test
**POST** `/api/production/strategies/sandbox-test/`

Runs strategy code in isolated Docker container.

**Request:**
```json
{
  "strategy_id": 123,
  "timeout": 60,
  "resource_limits": {
    "cpu": "0.5",
    "memory": "512m"
  }
}
```

**Response:**
```json
{
  "status": "completed",
  "success": true,
  "execution_time": 12.5,
  "exit_code": 0,
  "output": "Strategy executed successfully...",
  "errors": "",
  "timed_out": false,
  "resource_usage": {
    "max_memory_mb": 245,
    "cpu_percent": 45
  }
}
```

#### 4. Get Lifecycle
**GET** `/api/production/strategies/{id}/lifecycle/`

Retrieves complete state history for a strategy.

**Response:**
```json
{
  "strategy_id": 123,
  "name": "RSI_Reversal",
  "current_status": "passed",
  "lifecycle_tracking": {
    "generation_attempts": 3,
    "test_attempts": 2,
    "fix_attempts": 1,
    "error_count": 1,
    "last_error": "Syntax error on line 42"
  },
  "timestamps": {
    "created_at": "2025-01-01T10:00:00Z",
    "last_generation": "2025-01-01T10:05:00Z",
    "last_test": "2025-01-01T10:10:00Z",
    "last_success": "2025-01-01T10:15:00Z"
  },
  "audit_log": [
    {
      "timestamp": "2025-01-01T10:00:00Z",
      "event": "created",
      "details": "Strategy registered"
    },
    {
      "timestamp": "2025-01-01T10:05:00Z",
      "event": "generation",
      "details": "Code generated"
    }
  ]
}
```

#### 5. Deploy
**POST** `/api/production/strategies/{id}/deploy/`

Deploys strategy with git commit and state update.

**Request:**
```json
{
  "commit_message": "Deploy RSI strategy v1.0",
  "create_tag": true,
  "tag_version": "v1.0.0"
}
```

**Response:**
```json
{
  "status": "deployed",
  "strategy_id": 123,
  "branch": "strategy-RSI_Reversal-gen",
  "commit": "abc123def456",
  "tag": "v1.0.0",
  "message": "Strategy RSI_Reversal deployed successfully"
}
```

#### 6. Rollback
**POST** `/api/production/strategies/{id}/rollback/`

Reverts strategy to previous version.

**Request:**
```json
{
  "commit_hash": "abc123",
  "reason": "Bug in production"
}
```

**Response:**
```json
{
  "status": "rolled_back",
  "strategy_id": 123,
  "reverted_to": "abc123",
  "branch": "strategy-RSI_Reversal-rollback",
  "reason": "Bug in production",
  "message": "Strategy RSI_Reversal rolled back successfully"
}
```

#### 7. Health Check
**GET** `/api/production/strategies/health/`

Checks health of all production components.

**Response:**
```json
{
  "overall": "healthy",
  "components": {
    "state_manager": {
      "available": true,
      "strategies_tracked": 42
    },
    "safe_tools": {
      "available": true,
      "workspace": "/path/to/codes"
    },
    "output_validator": {
      "available": true,
      "strict_mode": true
    },
    "sandbox_runner": {
      "available": true,
      "docker_available": true
    },
    "git_manager": {
      "available": true,
      "repo_path": "/path/to/codes"
    }
  }
}
```

### Production Backtest API

Base URL: `/api/production/backtests/`

#### 1. Validate Config
**POST** `/api/production/backtests/validate-config/`

Validates backtest configuration against Pydantic schema.

**Request:**
```json
{
  "initial_capital": 100000,
  "commission": 0.001,
  "slippage": 0.0005,
  "position_size": 0.1,
  "max_positions": 5
}
```

**Response:**
```json
{
  "status": "valid",
  "message": "Backtest configuration is valid",
  "validated_config": { ... },
  "warnings": []
}
```

#### 2. Run Sandbox
**POST** `/api/production/backtests/run-sandbox/`

Executes backtest in isolated Docker container.

**Request:**
```json
{
  "strategy_id": 123,
  "config_id": 456,
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "symbols": ["AAPL", "GOOGL"],
  "resource_limits": {
    "cpu": "1.0",
    "memory": "1g",
    "timeout": 300
  }
}
```

**Response:**
```json
{
  "status": "completed",
  "backtest_id": 789,
  "results": {
    "total_return": 0.15,
    "sharpe_ratio": 1.5,
    "max_drawdown": -0.10,
    "win_rate": 0.55,
    "total_trades": 100
  },
  "execution_time": 45.2,
  "resource_usage": {
    "max_memory_mb": 512,
    "cpu_percent": 85
  }
}
```

#### 3. Get Status
**GET** `/api/production/backtests/{id}/status/`

Retrieves detailed status of a backtest run.

**Response:**
```json
{
  "backtest_id": 789,
  "status": "completed",
  "started_at": "2025-01-01T10:00:00Z",
  "completed_at": "2025-01-01T10:00:45Z",
  "execution_time": 45.2,
  "error_message": null,
  "state_tracking": {
    "current_status": "passed",
    "test_attempts": 1,
    "error_count": 0,
    "last_error": null
  },
  "audit_log": [ ... ],
  "results": {
    "total_return": 0.15,
    "sharpe_ratio": 1.5,
    "max_drawdown": -0.10,
    "win_rate": 0.55,
    "total_trades": 100
  }
}
```

#### 4. Health Check
**GET** `/api/production/backtests/health/`

Checks health of backtest production components.

**Response:**
```json
{
  "overall": "healthy",
  "components": {
    "state_manager": {
      "available": true
    },
    "output_validator": {
      "available": true,
      "strict_mode": true
    },
    "sandbox_runner": {
      "available": true,
      "docker_available": true
    }
  }
}
```

## Security Features

### 1. Code Safety Validation
All code is validated before execution:
- ❌ `os.system()` blocked
- ❌ `eval()` blocked
- ❌ `exec()` blocked
- ❌ `subprocess` blocked
- ❌ `socket` blocked
- ✅ Safe imports only
- ✅ AST validation
- ✅ Syntax checking

### 2. Docker Isolation
All execution happens in isolated containers:
- Network isolation (--network=none by default)
- CPU limits (configurable)
- Memory limits (configurable)
- Timeout enforcement
- Automatic cleanup

### 3. State Tracking
Complete lifecycle tracking:
- Generation attempts
- Test attempts
- Fix attempts
- Error history
- Audit logs
- Status transitions

### 4. Git Workflow
Version control integration:
- Feature branch creation
- Atomic commits
- Tag creation
- Rollback support
- Merge to main

## Usage Examples

### Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000/api/production"

# 1. Validate strategy schema
response = requests.post(f"{BASE_URL}/strategies/validate-schema/", json={
    "name": "RSI_Reversal",
    "description": "RSI reversal strategy",
    "parameters": {"rsi_period": 14},
    "indicators": {"rsi": {"period": 14}},
    "entry_rules": ["rsi < 30"],
    "exit_rules": ["rsi > 70"]
})
print("Schema validation:", response.json())

# 2. Validate code safety
code = """
class MyStrategy:
    def on_bar(self):
        if self.rsi < 30:
            self.buy()
"""

response = requests.post(f"{BASE_URL}/strategies/validate-code/", json={
    "code": code,
    "strict_mode": True
})
print("Code safety:", response.json())

# 3. Run sandbox test
response = requests.post(f"{BASE_URL}/strategies/sandbox-test/", json={
    "strategy_id": 123,
    "timeout": 60,
    "resource_limits": {"cpu": "0.5", "memory": "512m"}
})
print("Sandbox test:", response.json())

# 4. Check health
response = requests.get(f"{BASE_URL}/strategies/health/")
print("Health:", response.json())
```

### cURL Examples

```bash
# Validate schema
curl -X POST http://localhost:8000/api/production/strategies/validate-schema/ \
  -H "Content-Type: application/json" \
  -d '{"name":"RSI","description":"Test","parameters":{},"indicators":{},"entry_rules":[],"exit_rules":[]}'

# Validate code
curl -X POST http://localhost:8000/api/production/strategies/validate-code/ \
  -H "Content-Type: application/json" \
  -d '{"code":"class Strategy: pass","strict_mode":true}'

# Run sandbox test
curl -X POST http://localhost:8000/api/production/strategies/sandbox-test/ \
  -H "Content-Type: application/json" \
  -d '{"strategy_id":123,"timeout":60}'

# Get lifecycle
curl http://localhost:8000/api/production/strategies/123/lifecycle/

# Deploy
curl -X POST http://localhost:8000/api/production/strategies/123/deploy/ \
  -H "Content-Type: application/json" \
  -d '{"commit_message":"Deploy v1.0","create_tag":true,"tag_version":"v1.0.0"}'

# Health check
curl http://localhost:8000/api/production/strategies/health/
```

## Error Handling

All endpoints return consistent error formats:

```json
{
  "error": "Brief error description",
  "details": "Detailed error message",
  "code": "ERROR_CODE",
  "timestamp": "2025-01-01T10:00:00Z"
}
```

HTTP Status Codes:
- `200` - Success
- `400` - Bad Request (validation failed)
- `404` - Not Found
- `500` - Internal Server Error
- `503` - Service Unavailable (components not available)

## Backwards Compatibility

The original API endpoints remain unchanged:
- `/api/strategies/` - Original strategy API
- `/api/backtests/` - Original backtest API

Production endpoints are available under:
- `/api/production/strategies/` - Enhanced strategy API
- `/api/production/backtests/` - Enhanced backtest API

## Testing

Test the production endpoints:

```bash
# Start Django server
cd AlgoAgent
python manage.py runserver

# Test health endpoints
curl http://localhost:8000/api/production/strategies/health/
curl http://localhost:8000/api/production/backtests/health/

# Test API root
curl http://localhost:8000/api/
```

## Monitoring

Monitor production components:
- State database: `AlgoAgent/production_state.db`
- Docker containers: `docker ps`
- Git repository: `AlgoAgent/codes/`
- Logs: Django logs + component logs

## Next Steps

1. Test health endpoints
2. Validate a strategy schema
3. Run code safety checks
4. Execute sandbox tests
5. Monitor state tracking
6. Test deployment workflow
7. Test rollback functionality
