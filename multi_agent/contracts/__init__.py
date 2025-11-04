"""Multi-Agent AI Developer System - Contracts Package"""

__version__ = "0.1.0"

from contracts.event_types import Event, EventType, TaskEvent
from contracts.message_bus import MessageBus, get_message_bus, Channels
from contracts.validate_contract import SchemaValidator, validate_todo_file, validate_contract_file

__all__ = [
    "Event",
    "EventType", 
    "TaskEvent",
    "MessageBus",
    "get_message_bus",
    "Channels",
    "SchemaValidator",
    "validate_todo_file",
    "validate_contract_file"
]
