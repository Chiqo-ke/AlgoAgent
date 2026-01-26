# Event Streaming (WebSocket)

## Overview

Real-time event streaming via WebSocket provides instant notifications about workflow execution, task progress, and agent activity. This eliminates the need for polling and enables responsive user interfaces.

## WebSocket Connection

### Endpoint

```
ws://localhost:8000/ws/workflows/{workflow_id}/?token={jwt_token}
```

**Parameters:**
- `workflow_id` - Target workflow to monitor
- `token` - JWT authentication token (query param for WebSocket compatibility)

### Connection Example (JavaScript)

```javascript
const workflowId = 'wf_20260107_103000_abc123';
const token = localStorage.getItem('access_token');
const ws = new WebSocket(
  `ws://localhost:8000/ws/workflows/${workflowId}/?token=${token}`
);

ws.onopen = () => {
  console.log('Connected to workflow stream');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  handleEvent(data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = (event) => {
  console.log('Connection closed:', event.code, event.reason);
  // Implement reconnection logic
};
```

### Connection Example (Python)

```python
import asyncio
import websockets
import json

async def stream_workflow_events(workflow_id: str, token: str):
    uri = f"ws://localhost:8000/ws/workflows/{workflow_id}/?token={token}"
    
    async with websockets.connect(uri) as websocket:
        print(f"Connected to workflow {workflow_id}")
        
        async for message in websocket:
            event = json.loads(message)
            print(f"Event: {event['event_type']}")
            print(f"Data: {event['data']}")

# Run
asyncio.run(stream_workflow_events('wf_123abc', 'your_jwt_token'))
```

---

## Event Message Format

All events follow the same structure:

```json
{
  "event_id": "evt_unique_id",
  "event_type": "TASK_COMPLETED",
  "correlation_id": "corr_workflow_abc123",
  "workflow_id": "wf_20260107_103000_abc123",
  "task_id": "task_1",
  "timestamp": "2026-01-07T10:35:42.123Z",
  "source": "coder_agent",
  "data": {
    "artifacts": ["strategy_rsi.py"],
    "status": "success",
    "duration_seconds": 185
  },
  "metadata": {
    "retry_count": 0,
    "branch_depth": 0
  }
}
```

**Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| `event_id` | string | Unique identifier for this event |
| `event_type` | string | Event type constant (see Event Types below) |
| `correlation_id` | string | Links related events across the workflow |
| `workflow_id` | string | Parent workflow identifier |
| `task_id` | string | Task identifier (null for workflow-level events) |
| `timestamp` | string | ISO 8601 timestamp with milliseconds |
| `source` | string | Event originator (agent name or service) |
| `data` | object | Event-specific payload |
| `metadata` | object | Additional context (optional) |

---

## Event Types

### Workflow Events

#### WORKFLOW_CREATED
```json
{
  "event_type": "WORKFLOW_CREATED",
  "source": "orchestrator",
  "data": {
    "request": "Create RSI strategy with 30/70 levels",
    "auto_execute": true,
    "task_count": 4
  }
}
```

#### WORKFLOW_STARTED
```json
{
  "event_type": "WORKFLOW_STARTED",
  "source": "orchestrator",
  "data": {
    "estimated_duration_seconds": 600
  }
}
```

#### WORKFLOW_COMPLETED
```json
{
  "event_type": "WORKFLOW_COMPLETED",
  "source": "orchestrator",
  "data": {
    "total_duration_seconds": 542,
    "tasks_completed": 4,
    "artifacts": [
      "strategy_rsi.py",
      "test_rsi_strategy.py",
      "backtest_results.json"
    ]
  }
}
```

#### WORKFLOW_FAILED
```json
{
  "event_type": "WORKFLOW_FAILED",
  "source": "orchestrator",
  "data": {
    "reason": "Max retry limit exceeded",
    "failed_task": "task_2",
    "error_message": "Test execution timeout after 300s"
  }
}
```

#### WORKFLOW_PAUSED
```json
{
  "event_type": "WORKFLOW_PAUSED",
  "source": "orchestrator",
  "data": {
    "paused_by": "user_456",
    "reason": "Manual pause request"
  }
}
```

#### WORKFLOW_CANCELLED
```json
{
  "event_type": "WORKFLOW_CANCELLED",
  "source": "orchestrator",
  "data": {
    "cancelled_by": "user_456",
    "incomplete_tasks": ["task_3", "task_4"]
  }
}
```

---

### Task Events

#### TASK_DISPATCHED
```json
{
  "event_type": "TASK_DISPATCHED",
  "task_id": "task_1",
  "source": "orchestrator",
  "data": {
    "agent": "coder",
    "description": "Generate RSI strategy with indicators",
    "priority": 1
  }
}
```

#### TASK_STARTED
```json
{
  "event_type": "TASK_STARTED",
  "task_id": "task_1",
  "source": "coder_agent",
  "data": {
    "agent_version": "2.1.0",
    "llm_model": "claude-sonnet-4.5"
  }
}
```

#### TASK_PROGRESS
```json
{
  "event_type": "TASK_PROGRESS",
  "task_id": "task_1",
  "source": "coder_agent",
  "data": {
    "progress": 0.65,
    "current_step": "Generating entry conditions",
    "estimated_remaining_seconds": 45
  }
}
```

#### TASK_COMPLETED
```json
{
  "event_type": "TASK_COMPLETED",
  "task_id": "task_1",
  "source": "coder_agent",
  "data": {
    "artifacts": [
      "Backtest/codes/20260107_103000_wf_abc123_task_1_rsi_strategy.py"
    ],
    "duration_seconds": 185,
    "tokens_used": 3421,
    "status": "success"
  }
}
```

#### TASK_FAILED
```json
{
  "event_type": "TASK_FAILED",
  "task_id": "task_2",
  "source": "tester_agent",
  "data": {
    "error_type": "TestExecutionError",
    "error_message": "AssertionError: Expected profit > 0, got -150.5",
    "traceback": "...",
    "will_retry": true,
    "retry_count": 1
  }
}
```

---

### Agent Events

#### AGENT_THINKING
```json
{
  "event_type": "AGENT_THINKING",
  "task_id": "task_1",
  "source": "coder_agent",
  "data": {
    "thought": "Analyzing RSI indicator requirements",
    "confidence": 0.85
  }
}
```

#### AGENT_ACTION
```json
{
  "event_type": "AGENT_ACTION",
  "task_id": "task_1",
  "source": "debugger_agent",
  "data": {
    "action": "Creating branch todo for fixing entry logic",
    "target_task": "task_1_fix_1"
  }
}
```

---

### Test Events

#### TEST_STARTED
```json
{
  "event_type": "TEST_STARTED",
  "task_id": "task_2",
  "source": "tester_agent",
  "data": {
    "test_suite": "pytest tests/test_rsi_strategy.py",
    "sandbox_id": "sandbox_docker_789"
  }
}
```

#### TEST_PASSED
```json
{
  "event_type": "TEST_PASSED",
  "task_id": "task_2",
  "source": "tester_agent",
  "data": {
    "tests_run": 12,
    "duration_seconds": 45,
    "coverage": 0.92,
    "artifacts": [
      "trades.csv",
      "equity_curve.csv",
      "test_report.json"
    ]
  }
}
```

#### TEST_FAILED
```json
{
  "event_type": "TEST_FAILED",
  "task_id": "task_2",
  "source": "tester_agent",
  "data": {
    "failed_tests": [
      {
        "name": "test_entry_signal",
        "error": "AssertionError: RSI threshold not respected"
      }
    ],
    "tests_run": 12,
    "failures": 1,
    "test_report_path": "artifacts/test_report_task2.json"
  }
}
```

---

### Artifact Events

#### ARTIFACT_CREATED
```json
{
  "event_type": "ARTIFACT_CREATED",
  "task_id": "task_1",
  "source": "coder_agent",
  "data": {
    "artifact_path": "Backtest/codes/strategy_rsi.py",
    "artifact_type": "python_code",
    "size_bytes": 4523,
    "git_branch": "ai/generated/wf_abc123/task_1"
  }
}
```

#### ARTIFACT_UPDATED
```json
{
  "event_type": "ARTIFACT_UPDATED",
  "task_id": "task_1_fix_1",
  "source": "coder_agent",
  "data": {
    "artifact_path": "Backtest/codes/strategy_rsi.py",
    "change_type": "bug_fix",
    "diff_lines": 23
  }
}
```

---

### Approval Events

#### APPROVAL_REQUIRED
```json
{
  "event_type": "APPROVAL_REQUIRED",
  "task_id": "task_5",
  "source": "orchestrator",
  "data": {
    "approval_type": "deploy_to_live",
    "reason": "Strategy passed all tests, ready for live deployment",
    "approval_url": "https://backend.com/approvals/app_123"
  }
}
```

#### APPROVAL_GRANTED
```json
{
  "event_type": "APPROVAL_GRANTED",
  "task_id": "task_5",
  "source": "approval_service",
  "data": {
    "approved_by": "user_456",
    "timestamp": "2026-01-07T11:00:00Z"
  }
}
```

---

## Event Filtering

Clients can request specific event types by sending a filter message:

```javascript
ws.send(JSON.stringify({
  "type": "subscribe",
  "event_types": [
    "TASK_COMPLETED",
    "TASK_FAILED",
    "TEST_PASSED",
    "TEST_FAILED"
  ]
}));
```

**Default:** All event types are sent.

---

## Heartbeat & Keepalive

The server sends heartbeat messages every 30 seconds:

```json
{
  "type": "heartbeat",
  "timestamp": "2026-01-07T10:35:00Z",
  "workflow_status": "running"
}
```

Clients should respond with a pong:

```javascript
ws.send(JSON.stringify({"type": "pong"}));
```

If no pong received within 60 seconds, the connection may be closed.

---

## Reconnection Strategy

**Recommended Pattern:**

```javascript
class WorkflowWebSocket {
  constructor(workflowId, token) {
    this.workflowId = workflowId;
    this.token = token;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.connect();
  }

  connect() {
    const uri = `ws://localhost:8000/ws/workflows/${this.workflowId}/?token=${this.token}`;
    this.ws = new WebSocket(uri);

    this.ws.onopen = () => {
      console.log('Connected');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'heartbeat') {
        this.ws.send(JSON.stringify({type: 'pong'}));
      } else {
        this.handleEvent(data);
      }
    };

    this.ws.onclose = (event) => {
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
        console.log(`Reconnecting in ${delay}ms...`);
        setTimeout(() => {
          this.reconnectAttempts++;
          this.connect();
        }, delay);
      }
    };
  }

  handleEvent(event) {
    // Your event handling logic
    console.log('Event:', event.event_type, event.data);
  }
}
```

---

## Error Handling

### Connection Errors

**4001 - Invalid Token**
```json
{
  "type": "error",
  "code": 4001,
  "message": "Invalid or expired JWT token"
}
```

**4003 - Workflow Not Found**
```json
{
  "type": "error",
  "code": 4003,
  "message": "Workflow wf_invalid not found or access denied"
}
```

**4004 - Rate Limit Exceeded**
```json
{
  "type": "error",
  "code": 4004,
  "message": "Too many connections. Max 5 concurrent connections per user."
}
```

---

## Performance Considerations

1. **Event Filtering:** Subscribe only to needed event types to reduce bandwidth
2. **Buffering:** Implement client-side buffering for high-frequency events
3. **Compression:** WebSocket compression is enabled by default (permessage-deflate)
4. **Connection Pooling:** Reuse connections for multiple workflow subscriptions when possible
5. **Graceful Degradation:** Fall back to HTTP polling if WebSocket unavailable

---

## Textual CLI Integration Example

```python
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, ListView, ListItem
from textual.containers import Container
import asyncio
import websockets
import json

class WorkflowStream(Static):
    def __init__(self, workflow_id: str, token: str):
        super().__init__()
        self.workflow_id = workflow_id
        self.token = token
        self.events = []

    async def stream_events(self):
        uri = f"ws://localhost:8000/ws/workflows/{self.workflow_id}/?token={self.token}"
        async with websockets.connect(uri) as ws:
            async for message in ws:
                event = json.loads(message)
                self.events.append(event)
                self.update_display(event)

    def update_display(self, event):
        event_type = event['event_type']
        timestamp = event['timestamp']
        self.update(f"[{timestamp}] {event_type}")

class WorkflowMonitorApp(App):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            WorkflowStream(workflow_id="wf_123", token="your_token")
        )
        yield Footer()

if __name__ == "__main__":
    app = WorkflowMonitorApp()
    app.run()
```

---

## Event Channels Mapping

| Message Bus Channel | WebSocket Event Types |
|---------------------|----------------------|
| `workflow.lifecycle` | `WORKFLOW_*` |
| `task.updates` | `TASK_*` |
| `agent.results` | `AGENT_*` |
| `test.results` | `TEST_*` |
| `artifact.events` | `ARTIFACT_*` |
| `approval.requests` | `APPROVAL_*` |

All events from these channels are forwarded to WebSocket clients in real-time.
