# Event Schema Reference

## Base Event Structure

All events inherit from the base `Event` class:

```python
@dataclass
class Event:
    """Base event class for all system events."""
    event_id: str                    # Unique identifier (UUID)
    event_type: EventType            # Event type enum
    correlation_id: str              # Links related events
    workflow_id: str                 # Parent workflow
    task_id: Optional[str]          # Associated task (if applicable)
    timestamp: str                   # ISO 8601 timestamp
    source: str                      # Event originator
    data: Dict[str, Any]            # Event-specific payload
    metadata: Optional[Dict]         # Additional context
```

## EventType Enumeration

### Workflow Lifecycle Events
```python
class EventType(Enum):
    # Workflow lifecycle
    WORKFLOW_CREATED = "workflow.created"
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    WORKFLOW_PAUSED = "workflow.paused"
    WORKFLOW_RESUMED = "workflow.resumed"
    WORKFLOW_CANCELLED = "workflow.cancelled"
```

### Task Execution Events
```python
    # Task execution
    TASK_CREATED = "task.created"
    TASK_DISPATCHED = "task.dispatched"
    TASK_STARTED = "task.started"
    TASK_PROGRESS = "task.progress"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_RETRYING = "task.retrying"
    TASK_TIMEOUT = "task.timeout"
```

### Agent Activity Events
```python
    # Agent activity
    AGENT_THINKING = "agent.thinking"
    AGENT_ACTION = "agent.action"
    AGENT_ERROR = "agent.error"
    AGENT_WAITING = "agent.waiting"
```

### Test Execution Events
```python
    # Test execution
    TEST_STARTED = "test.started"
    TEST_PASSED = "test.passed"
    TEST_FAILED = "test.failed"
    TEST_SKIPPED = "test.skipped"
```

### Artifact Management Events
```python
    # Artifact management
    ARTIFACT_CREATED = "artifact.created"
    ARTIFACT_UPDATED = "artifact.updated"
    ARTIFACT_DELETED = "artifact.deleted"
```

### Approval & Human-in-Loop Events
```python
    # Approval workflow
    APPROVAL_REQUIRED = "approval.required"
    APPROVAL_GRANTED = "approval.granted"
    APPROVAL_DENIED = "approval.denied"
```

### System Events
```python
    # System events
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"
    RATE_LIMIT_EXCEEDED = "system.rate_limit"
```

---

## Event Data Schemas

### WORKFLOW_CREATED

```json
{
  "event_type": "workflow.created",
  "data": {
    "request": "string",              // User's natural language request
    "auto_execute": "boolean",        // Auto-start flag
    "auto_fix_mode": "boolean",       // Auto-fix enabled
    "max_branch_depth": "integer",    // Max retry depth
    "task_count": "integer",          // Number of tasks in TodoList
    "context": "object"               // Additional context
  }
}
```

### WORKFLOW_STARTED

```json
{
  "event_type": "workflow.started",
  "data": {
    "estimated_duration_seconds": "integer",
    "planner_model": "string",
    "agents_involved": ["string"]
  }
}
```

### WORKFLOW_COMPLETED

```json
{
  "event_type": "workflow.completed",
  "data": {
    "total_duration_seconds": "integer",
    "tasks_completed": "integer",
    "tasks_failed": "integer",
    "artifacts": ["string"],          // List of generated files
    "final_status": "string"
  }
}
```

### WORKFLOW_FAILED

```json
{
  "event_type": "workflow.failed",
  "data": {
    "reason": "string",               // Failure reason
    "failed_task": "string",          // Task that caused failure
    "error_message": "string",
    "retry_count": "integer",
    "exceeded_retry_limit": "boolean"
  }
}
```

---

### TASK_DISPATCHED

```json
{
  "event_type": "task.dispatched",
  "task_id": "string",
  "data": {
    "agent": "string",                // Agent name (coder, tester, etc.)
    "description": "string",
    "priority": "integer",
    "depends_on": ["string"],         // Task dependencies
    "test_command": "string"
  }
}
```

### TASK_STARTED

```json
{
  "event_type": "task.started",
  "task_id": "string",
  "data": {
    "agent": "string",
    "agent_version": "string",
    "llm_model": "string",            // LLM model used
    "temperature": "float"
  }
}
```

### TASK_PROGRESS

```json
{
  "event_type": "task.progress",
  "task_id": "string",
  "data": {
    "progress": "float",              // 0.0 to 1.0
    "current_step": "string",
    "estimated_remaining_seconds": "integer"
  }
}
```

### TASK_COMPLETED

```json
{
  "event_type": "task.completed",
  "task_id": "string",
  "data": {
    "artifacts": ["string"],          // Generated files
    "duration_seconds": "integer",
    "tokens_used": "integer",
    "llm_cost_usd": "float",
    "status": "string",               // success, partial_success
    "confidence": "float"             // Agent confidence (0.0-1.0)
  }
}
```

### TASK_FAILED

```json
{
  "event_type": "task.failed",
  "task_id": "string",
  "data": {
    "error_type": "string",           // implementation_bug, spec_mismatch, etc.
    "error_message": "string",
    "traceback": "string",
    "will_retry": "boolean",
    "retry_count": "integer",
    "failure_classification": "string"
  }
}
```

---

### AGENT_THINKING

```json
{
  "event_type": "agent.thinking",
  "task_id": "string",
  "data": {
    "thought": "string",              // Agent's reasoning
    "confidence": "float",
    "alternatives_considered": ["string"]
  }
}
```

### AGENT_ACTION

```json
{
  "event_type": "agent.action",
  "task_id": "string",
  "data": {
    "action": "string",               // Action description
    "target": "string",               // Target resource
    "parameters": "object"
  }
}
```

### AGENT_ERROR

```json
{
  "event_type": "agent.error",
  "task_id": "string",
  "data": {
    "error_type": "string",
    "error_message": "string",
    "recovery_action": "string"
  }
}
```

---

### TEST_STARTED

```json
{
  "event_type": "test.started",
  "task_id": "string",
  "data": {
    "test_suite": "string",           // Test command
    "sandbox_id": "string",           // Docker container ID
    "fixtures": ["string"]
  }
}
```

### TEST_PASSED

```json
{
  "event_type": "test.passed",
  "task_id": "string",
  "data": {
    "tests_run": "integer",
    "duration_seconds": "integer",
    "coverage": "float",              // Code coverage (0.0-1.0)
    "artifacts": ["string"],          // trades.csv, equity_curve.csv
    "performance_metrics": {
      "total_return": "float",
      "sharpe_ratio": "float",
      "max_drawdown": "float"
    }
  }
}
```

### TEST_FAILED

```json
{
  "event_type": "test.failed",
  "task_id": "string",
  "data": {
    "failed_tests": [
      {
        "name": "string",
        "error": "string",
        "line_number": "integer"
      }
    ],
    "tests_run": "integer",
    "failures": "integer",
    "errors": "integer",
    "test_report_path": "string"
  }
}
```

---

### ARTIFACT_CREATED

```json
{
  "event_type": "artifact.created",
  "task_id": "string",
  "data": {
    "artifact_path": "string",
    "artifact_type": "string",        // python_code, csv, json, etc.
    "size_bytes": "integer",
    "content_hash": "string",         // SHA-256
    "git_branch": "string",           // Git branch if committed
    "git_commit": "string"            // Git commit hash
  }
}
```

### ARTIFACT_UPDATED

```json
{
  "event_type": "artifact.updated",
  "task_id": "string",
  "data": {
    "artifact_path": "string",
    "change_type": "string",          // bug_fix, refactor, enhancement
    "diff_lines": "integer",
    "previous_hash": "string",
    "new_hash": "string"
  }
}
```

---

### APPROVAL_REQUIRED

```json
{
  "event_type": "approval.required",
  "task_id": "string",
  "data": {
    "approval_type": "string",        // deploy_to_live, merge_to_main, etc.
    "reason": "string",
    "approval_url": "string",
    "approvers": ["string"],          // User IDs who can approve
    "timeout_seconds": "integer"      // Auto-deny after timeout
  }
}
```

### APPROVAL_GRANTED

```json
{
  "event_type": "approval.granted",
  "task_id": "string",
  "data": {
    "approved_by": "string",          // User ID
    "timestamp": "string",
    "comment": "string"
  }
}
```

### APPROVAL_DENIED

```json
{
  "event_type": "approval.denied",
  "task_id": "string",
  "data": {
    "denied_by": "string",
    "reason": "string",
    "timestamp": "string"
  }
}
```

---

## Common Metadata Fields

The `metadata` object can include:

```json
{
  "metadata": {
    "retry_count": "integer",
    "branch_depth": "integer",        // Auto-fix branch depth
    "parent_task_id": "string",       // For branch todos
    "user_id": "string",
    "session_id": "string",
    "environment": "string",          // dev, staging, prod
    "version": "string"               // System version
  }
}
```

---

## Event Creation Helper

```python
from contracts.event_types import Event, EventType

# Create workflow event
event = Event.create(
    event_type=EventType.WORKFLOW_CREATED,
    correlation_id="corr_abc123",
    workflow_id="wf_20260107_103000_abc123",
    data={
        "request": "Create RSI strategy",
        "auto_execute": True,
        "task_count": 4
    },
    source="orchestrator"
)

# Create task event
task_event = Event.create(
    event_type=EventType.TASK_COMPLETED,
    correlation_id="corr_abc123",
    workflow_id="wf_20260107_103000_abc123",
    task_id="task_1",
    data={
        "artifacts": ["strategy.py"],
        "duration_seconds": 185
    },
    source="coder_agent",
    metadata={"retry_count": 0}
)
```

---

## Event Validation

Events are validated against JSON schemas before publishing:

```python
from contracts.validate_contract import SchemaValidator

validator = SchemaValidator()

# Validate event schema
is_valid = validator.validate_event(event_dict)

if not is_valid:
    print(validator.errors)
```

Schema files: `contracts/event_schema.json`

---

## Event Serialization

Events can be serialized for storage or transmission:

```python
# To JSON
event_json = event.to_json()

# From JSON
event = Event.from_json(event_json)

# To dict
event_dict = event.to_dict()
```

---

## Best Practices

1. **Always include correlation_id** to link related events
2. **Use structured data** in the `data` field, not free-form strings
3. **Include timestamps** for all time-sensitive data
4. **Add metadata** for debugging context
5. **Validate events** before publishing to message bus
6. **Use event_id** for idempotent event processing
7. **Include source** to track event origin
8. **Add confidence scores** for AI-generated outputs
