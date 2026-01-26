# Multi-Agent Workflow API Documentation

## Overview

The Multi-Agent Workflow API provides RESTful endpoints and WebSocket connections for managing AI-driven trading strategy development workflows. This API bridges the multi-agent system (Planner, Coder, Tester, Debugger) with external clients through a Django backend.

## Base URL

```
Development: http://localhost:8000/api
Production: https://api.yourbackend.com/api
```

## Authentication

All endpoints require JWT Bearer token authentication:

```http
Authorization: Bearer <your_jwt_token>
```

Obtain tokens via the `/api/auth/login/` endpoint.

## API Sections

1. [Workflow Management](./workflow-endpoints.md) - Create, monitor, and control workflows
2. [Task Management](./task-endpoints.md) - View and manage individual tasks
3. [Event Streaming](./event-streaming.md) - Real-time WebSocket event feed
4. [Agent Status](./agent-endpoints.md) - Monitor agent health and activity
5. [Artifact Management](./artifact-endpoints.md) - Access generated code and test results

## Quick Start

### 1. Submit a Workflow

```bash
curl -X POST http://localhost:8000/api/workflows/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "request": "Create RSI strategy with 30/70 levels",
    "auto_execute": true,
    "auto_fix_mode": true
  }'
```

**Response:**
```json
{
  "workflow_id": "wf_123abc",
  "status": "created",
  "created_at": "2026-01-07T10:30:00Z",
  "todo_list": {
    "tasks": [
      {
        "id": "task_1",
        "description": "Generate RSI strategy code",
        "agent": "coder"
      }
    ]
  }
}
```

### 2. Monitor Workflow Progress

```bash
curl -X GET http://localhost:8000/api/workflows/wf_123abc/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "workflow_id": "wf_123abc",
  "status": "running",
  "progress": 0.5,
  "tasks": [
    {
      "task_id": "task_1",
      "status": "completed",
      "agent": "coder",
      "artifacts": ["strategy_rsi.py"]
    },
    {
      "task_id": "task_2",
      "status": "running",
      "agent": "tester"
    }
  ]
}
```

### 3. Stream Real-Time Events (WebSocket)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/workflows/wf_123abc/?token=YOUR_TOKEN');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.event_type, data.data);
};
```

**Event Example:**
```json
{
  "event_type": "TASK_COMPLETED",
  "correlation_id": "corr_456",
  "workflow_id": "wf_123abc",
  "task_id": "task_1",
  "timestamp": "2026-01-07T10:31:15Z",
  "data": {
    "artifacts": ["strategy_rsi.py"],
    "status": "success"
  },
  "source": "coder_agent"
}
```

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Textual CLI / Frontend                    │
│                  (HTTP REST + WebSocket)                     │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                   Django REST Backend                        │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Workflow API (workflow_api app)                   │     │
│  │  - REST endpoints: WorkflowViewSet                 │     │
│  │  - WebSocket: WorkflowConsumer                     │     │
│  │  - Models: Workflow, Task, Event                   │     │
│  └────────────┬───────────────────────────────────────┘     │
│               │                                              │
│  ┌────────────▼───────────────────────────────────────┐     │
│  │  Multi-Agent Bridge (bridge service)               │     │
│  │  - MessageBusListener                              │     │
│  │  - EventForwarder → Django Channels                │     │
│  │  - OrchestratorClient                              │     │
│  └────────────┬───────────────────────────────────────┘     │
└───────────────┼──────────────────────────────────────────────┘
                │ Message Bus (Redis)
┌───────────────▼──────────────────────────────────────────────┐
│              Multi-Agent System                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Orchestrator │←→│ Message Bus  │←→│   Agents     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────────────────────────────────────────┘
```

## Message Bus Events

The system publishes 30+ event types across 6 channels:

### Event Channels
- `workflow.lifecycle` - Workflow state changes
- `task.updates` - Task progress and completion
- `agent.results` - Agent execution results
- `approval.requests` - Human approval required
- `artifact.events` - Code/file generation
- `test.results` - Test execution outcomes

### Key Event Types

| Event Type | Channel | Description |
|------------|---------|-------------|
| `WORKFLOW_CREATED` | workflow.lifecycle | New workflow submitted |
| `WORKFLOW_STARTED` | workflow.lifecycle | Workflow execution began |
| `WORKFLOW_COMPLETED` | workflow.lifecycle | All tasks completed successfully |
| `TASK_DISPATCHED` | task.updates | Task sent to agent |
| `TASK_STARTED` | task.updates | Agent started processing task |
| `TASK_COMPLETED` | task.updates | Task finished successfully |
| `TASK_FAILED` | task.updates | Task failed with error |
| `TEST_PASSED` | test.results | Strategy passed all tests |
| `TEST_FAILED` | test.results | Strategy failed tests |
| `ARTIFACT_CREATED` | artifact.events | New file generated |

See [Event Schema](./event-schema.md) for complete event definitions.

## Error Handling

### Standard Error Response

```json
{
  "error": "WorkflowNotFound",
  "message": "Workflow with ID wf_123abc not found",
  "code": "404",
  "details": {
    "workflow_id": "wf_123abc"
  }
}
```

### HTTP Status Codes

| Code | Meaning | Common Scenarios |
|------|---------|------------------|
| 200 | OK | Successful GET request |
| 201 | Created | Workflow/resource created |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Missing/invalid JWT token |
| 403 | Forbidden | User lacks permission |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Workflow already exists |
| 500 | Server Error | Internal system error |

## Rate Limiting

- **Workflow Submission:** 10 requests/minute per user
- **Status Polling:** 60 requests/minute per user
- **WebSocket Connections:** 5 concurrent per user

Exceeded limits return HTTP 429 with `Retry-After` header.

## Versioning

API version is included in the URL path:

```
/api/v1/workflows/
```

Current version: **v1** (stable)

## Support

- Documentation Issues: [GitHub Issues](https://github.com/yourrepo/issues)
- API Questions: api-support@yourbackend.com
- System Status: https://status.yourbackend.com

## Changelog

### v1.0.0 (2026-01-07)
- Initial release
- Workflow CRUD operations
- WebSocket event streaming
- JWT authentication
- Task management
- Artifact retrieval
