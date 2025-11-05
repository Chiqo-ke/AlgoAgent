"""
Event Types for Multi-Agent System

Defines all event types and their schemas for the message bus.
"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid


class EventType(Enum):
    """All event types in the system."""
    
    # Workflow events
    WORKFLOW_CREATED = "workflow.created"
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_PAUSED = "workflow.paused"
    WORKFLOW_RESUMED = "workflow.resumed"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    WORKFLOW_BRANCH_CREATED = "workflow.branch.created"
    
    # Task events
    TASK_CREATED = "task.created"
    TASK_DISPATCHED = "task.dispatched"
    TASK_STARTED = "task.started"
    TASK_PROGRESS = "task.progress"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_RETRYING = "task.retrying"
    TASK_TIMEOUT = "task.timeout"
    
    # Agent events
    AGENT_REGISTERED = "agent.registered"
    AGENT_HEARTBEAT = "agent.heartbeat"
    AGENT_OFFLINE = "agent.offline"
    
    # Approval events
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_GRANTED = "approval.granted"
    APPROVAL_DENIED = "approval.denied"
    
    # Artifact events
    ARTIFACT_CREATED = "artifact.created"
    ARTIFACT_VALIDATED = "artifact.validated"
    ARTIFACT_COMMITTED = "artifact.committed"
    
    # Test events
    TEST_STARTED = "test.started"
    TEST_PASSED = "test.passed"
    TEST_FAILED = "test.failed"


@dataclass
class Event:
    """Base event class."""
    
    event_id: str
    event_type: EventType
    correlation_id: str
    workflow_id: str
    timestamp: str
    data: Dict[str, Any]
    source: str
    
    @classmethod
    def create(cls, event_type: EventType, correlation_id: str, workflow_id: str,
               data: Dict[str, Any], source: str = "unknown") -> 'Event':
        """Create a new event with auto-generated ID and timestamp."""
        return cls(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            event_type=event_type,
            correlation_id=correlation_id,
            workflow_id=workflow_id,
            timestamp=datetime.utcnow().isoformat(),
            data=data,
            source=source
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result['event_type'] = self.event_type.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create from dictionary."""
        data = data.copy()
        data['event_type'] = EventType(data['event_type'])
        return cls(**data)


@dataclass
class TaskEvent(Event):
    """Task-specific event with task_id."""
    
    task_id: Optional[str] = None
    
    @classmethod
    def create(cls, event_type: EventType, correlation_id: str, workflow_id: str,
               task_id: str, data: Dict[str, Any], source: str = "unknown") -> 'TaskEvent':
        """Create a new task event."""
        return cls(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            event_type=event_type,
            correlation_id=correlation_id,
            workflow_id=workflow_id,
            task_id=task_id,
            timestamp=datetime.utcnow().isoformat(),
            data=data,
            source=source
        )


# Event data schemas (for validation)
EVENT_SCHEMAS = {
    EventType.WORKFLOW_CREATED: {
        "type": "object",
        "required": ["todo_list_id", "workflow_name"],
        "properties": {
            "todo_list_id": {"type": "string"},
            "workflow_name": {"type": "string"},
            "total_tasks": {"type": "integer"}
        }
    },
    
    EventType.TASK_DISPATCHED: {
        "type": "object",
        "required": ["task_id", "agent_role", "agent_id"],
        "properties": {
            "task_id": {"type": "string"},
            "agent_role": {"type": "string"},
            "agent_id": {"type": "string"}
        }
    },
    
    EventType.TASK_COMPLETED: {
        "type": "object",
        "required": ["task_id", "artifacts", "duration_seconds"],
        "properties": {
            "task_id": {"type": "string"},
            "artifacts": {"type": "array"},
            "duration_seconds": {"type": "number"},
            "test_report_id": {"type": "string"}
        }
    },
    
    EventType.TASK_FAILED: {
        "type": "object",
        "required": ["task_id", "error", "retry_count"],
        "properties": {
            "task_id": {"type": "string"},
            "error": {"type": "string"},
            "retry_count": {"type": "integer"},
            "traceback": {"type": "string"}
        }
    }
}
