"""
Backend Bridge Package

This package provides integration between the multi-agent system and the Django backend.
It enables REST API access and WebSocket streaming of workflow events to external clients.

Components:
- MessageBusListener: Subscribes to agent events from the message bus
- EventForwarder: Forwards events to Django Channels WebSocket consumers
- OrchestratorClient: Submits workflows and monitors status
- Django Models: Workflow, Task, Event persistence
- Django Views: REST API endpoints (WorkflowViewSet)
- Django Consumers: WebSocket real-time streaming (WorkflowConsumer)
"""

__version__ = "1.0.0"

from .message_bus_listener import MessageBusListener
from .event_forwarder import EventForwarder
from .orchestrator_client import OrchestratorClient

__all__ = [
    "MessageBusListener",
    "EventForwarder",
    "OrchestratorClient",
]
