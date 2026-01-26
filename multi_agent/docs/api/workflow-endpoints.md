# Workflow Management Endpoints

## Overview

Workflows represent complete strategy development lifecycles, from natural language request to tested strategy code. Each workflow contains a TodoList with multiple tasks executed by different agents.

## Endpoints

### Create Workflow

Submit a new strategy development request.

**Endpoint:** `POST /api/workflows/`

**Authentication:** Required (JWT Bearer token)

**Request Body:**

```json
{
  "request": "Create RSI strategy with 30/70 levels and 50 SMA filter",
  "auto_execute": true,
  "auto_fix_mode": true,
  "max_branch_depth": 2,
  "context": {
    "symbol": "EURUSD",
    "timeframe": "1H",
    "initial_balance": 10000
  }
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `request` | string | Yes | Natural language description of strategy |
| `auto_execute` | boolean | No | Auto-start workflow (default: true) |
| `auto_fix_mode` | boolean | No | Enable auto-fix on failures (default: true) |
| `max_branch_depth` | integer | No | Max fix retry depth (default: 2) |
| `context` | object | No | Additional context for strategy generation |

**Response:** `201 Created`

```json
{
  "workflow_id": "wf_20260107_103000_abc123",
  "status": "created",
  "created_at": "2026-01-07T10:30:00Z",
  "user_id": "user_456",
  "todo_list": {
    "title": "RSI Strategy Development",
    "tasks": [
      {
        "id": "task_1",
        "description": "Generate RSI strategy with indicators",
        "agent": "coder",
        "depends_on": [],
        "test_command": "pytest tests/test_rsi_strategy.py",
        "failure_routing": {
          "implementation_bug": ["debugger", "coder"],
          "spec_mismatch": ["architect", "coder"]
        }
      },
      {
        "id": "task_2",
        "description": "Run backtest validation",
        "agent": "tester",
        "depends_on": ["task_1"]
      }
    ]
  },
  "metadata": {
    "planner_model": "gemini-pro",
    "estimated_duration": "5-10 minutes"
  }
}
```

---

### Get Workflow Status

Retrieve current status and progress of a workflow.

**Endpoint:** `GET /api/workflows/{workflow_id}/`

**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `workflow_id` | string | Unique workflow identifier |

**Response:** `200 OK`

```json
{
  "workflow_id": "wf_20260107_103000_abc123",
  "status": "running",
  "progress": 0.67,
  "created_at": "2026-01-07T10:30:00Z",
  "started_at": "2026-01-07T10:30:15Z",
  "updated_at": "2026-01-07T10:35:42Z",
  "user_id": "user_456",
  "request": "Create RSI strategy with 30/70 levels",
  "tasks": [
    {
      "task_id": "task_1",
      "description": "Generate RSI strategy with indicators",
      "agent": "coder",
      "status": "completed",
      "started_at": "2026-01-07T10:30:15Z",
      "completed_at": "2026-01-07T10:33:20Z",
      "retry_count": 0,
      "artifacts": [
        "Backtest/codes/20260107_103000_wf_abc123_task_1_rsi_strategy.py",
        "tests/test_rsi_strategy.py"
      ],
      "result": {
        "status": "success",
        "message": "Strategy generated successfully"
      }
    },
    {
      "task_id": "task_2",
      "description": "Run backtest validation",
      "agent": "tester",
      "status": "running",
      "started_at": "2026-01-07T10:33:25Z",
      "retry_count": 0
    }
  ],
  "branch_todos": [],
  "auto_fix_mode": true,
  "max_branch_depth": 2
}
```

**Status Values:**
- `created` - Workflow created, not started
- `running` - Currently executing tasks
- `paused` - Execution paused by user
- `completed` - All tasks completed successfully
- `failed` - Workflow failed (exceeded retry limit or critical error)
- `cancelled` - Manually cancelled by user

---

### List Workflows

Get all workflows for the authenticated user.

**Endpoint:** `GET /api/workflows/`

**Authentication:** Required

**Query Parameters:**

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `status` | string | Filter by status (created, running, completed, failed) | All |
| `limit` | integer | Number of results (1-100) | 20 |
| `offset` | integer | Pagination offset | 0 |
| `order_by` | string | Sort field (created_at, updated_at) | -created_at |

**Example:** `GET /api/workflows/?status=running&limit=10`

**Response:** `200 OK`

```json
{
  "count": 42,
  "next": "http://localhost:8000/api/workflows/?offset=10&limit=10",
  "previous": null,
  "results": [
    {
      "workflow_id": "wf_20260107_103000_abc123",
      "status": "running",
      "progress": 0.67,
      "created_at": "2026-01-07T10:30:00Z",
      "request": "Create RSI strategy with 30/70 levels",
      "task_count": 3,
      "completed_tasks": 2
    },
    {
      "workflow_id": "wf_20260106_153000_def456",
      "status": "completed",
      "progress": 1.0,
      "created_at": "2026-01-06T15:30:00Z",
      "request": "MACD crossover strategy",
      "task_count": 4,
      "completed_tasks": 4
    }
  ]
}
```

---

### Pause Workflow

Pause a running workflow.

**Endpoint:** `PATCH /api/workflows/{workflow_id}/pause/`

**Authentication:** Required

**Response:** `200 OK`

```json
{
  "workflow_id": "wf_20260107_103000_abc123",
  "status": "paused",
  "message": "Workflow paused successfully",
  "paused_at": "2026-01-07T10:40:00Z"
}
```

**Note:** Current task will complete before pausing.

---

### Resume Workflow

Resume a paused workflow.

**Endpoint:** `PATCH /api/workflows/{workflow_id}/resume/`

**Authentication:** Required

**Response:** `200 OK`

```json
{
  "workflow_id": "wf_20260107_103000_abc123",
  "status": "running",
  "message": "Workflow resumed successfully",
  "resumed_at": "2026-01-07T10:45:00Z"
}
```

---

### Cancel Workflow

Cancel a workflow permanently.

**Endpoint:** `DELETE /api/workflows/{workflow_id}/`

**Authentication:** Required

**Response:** `200 OK`

```json
{
  "workflow_id": "wf_20260107_103000_abc123",
  "status": "cancelled",
  "message": "Workflow cancelled successfully",
  "cancelled_at": "2026-01-07T10:50:00Z"
}
```

**Note:** Cannot be undone. In-progress tasks will be terminated.

---

### Get Workflow Tasks

Retrieve detailed task information for a workflow.

**Endpoint:** `GET /api/workflows/{workflow_id}/tasks/`

**Authentication:** Required

**Response:** `200 OK`

```json
{
  "workflow_id": "wf_20260107_103000_abc123",
  "tasks": [
    {
      "task_id": "task_1",
      "description": "Generate RSI strategy with indicators",
      "agent": "coder",
      "status": "completed",
      "started_at": "2026-01-07T10:30:15Z",
      "completed_at": "2026-01-07T10:33:20Z",
      "duration_seconds": 185,
      "retry_count": 0,
      "artifacts": [
        {
          "path": "Backtest/codes/20260107_103000_wf_abc123_task_1_rsi_strategy.py",
          "size_bytes": 4523,
          "type": "python_code"
        }
      ],
      "result": {
        "status": "success",
        "llm_model": "claude-sonnet-4.5",
        "tokens_used": 3421,
        "confidence": 0.95
      }
    }
  ]
}
```

---

### Get Workflow Events

Retrieve event history for a workflow.

**Endpoint:** `GET /api/workflows/{workflow_id}/events/`

**Authentication:** Required

**Query Parameters:**

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `event_type` | string | Filter by event type | All |
| `limit` | integer | Number of events (1-500) | 100 |
| `after` | string | ISO timestamp - events after this time | None |

**Response:** `200 OK`

```json
{
  "workflow_id": "wf_20260107_103000_abc123",
  "events": [
    {
      "event_id": "evt_789",
      "event_type": "WORKFLOW_STARTED",
      "correlation_id": "corr_abc123",
      "timestamp": "2026-01-07T10:30:15Z",
      "source": "orchestrator",
      "data": {
        "auto_execute": true
      }
    },
    {
      "event_id": "evt_790",
      "event_type": "TASK_DISPATCHED",
      "correlation_id": "corr_abc123",
      "task_id": "task_1",
      "timestamp": "2026-01-07T10:30:16Z",
      "source": "orchestrator",
      "data": {
        "agent": "coder",
        "description": "Generate RSI strategy"
      }
    }
  ]
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "ValidationError",
  "message": "Invalid request format",
  "details": {
    "request": ["This field is required"]
  }
}
```

### 404 Not Found
```json
{
  "error": "WorkflowNotFound",
  "message": "Workflow with ID wf_invalid not found"
}
```

### 409 Conflict
```json
{
  "error": "InvalidStateTransition",
  "message": "Cannot pause a completed workflow",
  "details": {
    "current_status": "completed",
    "requested_action": "pause"
  }
}
```

---

## Workflow State Diagram

```
    [CREATED]
       │
       ├─ auto_execute=true ─────→ [RUNNING]
       │                              │
       └─ auto_execute=false          ├─ all tasks complete ──→ [COMPLETED]
                                      │
                                      ├─ user action ──→ [PAUSED] ─┐
                                      │                      │     │
                                      │                      └─ resume ─┘
                                      │
                                      ├─ user action ──→ [CANCELLED]
                                      │
                                      └─ error/timeout ──→ [FAILED]
```

## Best Practices

1. **Use WebSocket for real-time updates** instead of polling GET requests
2. **Enable auto_fix_mode** for production workflows to handle transient failures
3. **Set appropriate max_branch_depth** (1-3) to avoid infinite retry loops
4. **Monitor workflow progress** field for estimated completion
5. **Store workflow_id** immediately after creation for tracking
6. **Use event filtering** when retrieving history to reduce payload size
7. **Implement exponential backoff** if polling is necessary
