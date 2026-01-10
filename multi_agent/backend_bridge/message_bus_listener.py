"""
Message Bus Listener

Subscribes to all channels in the multi-agent message bus and forwards events
to the Django backend via the EventForwarder.

This acts as the bridge between the in-process message bus (Redis or in-memory)
and the Django Channels layer for WebSocket broadcasting.
"""

import logging
import asyncio
from typing import Callable, Optional, Dict, List
from contracts.message_bus import get_message_bus, Channels
from contracts.event_types import Event, EventType
from .event_forwarder import EventForwarder


logger = logging.getLogger(__name__)


class MessageBusListener:
    """
    Listens to multi-agent message bus and forwards events to Django backend.
    
    Subscribes to all event channels and routes events to appropriate handlers:
    - Workflow events → EventForwarder → Django Channels → WebSocket clients
    - Task events → Database persistence + WebSocket
    - Agent events → Real-time monitoring feed
    """
    
    def __init__(self, event_forwarder: Optional[EventForwarder] = None):
        """
        Initialize the message bus listener.
        
        Args:
            event_forwarder: EventForwarder instance (created if not provided)
        """
        self.message_bus = get_message_bus()
        self.event_forwarder = event_forwarder or EventForwarder()
        self.subscriptions: Dict[str, Callable] = {}
        self.is_running = False
        
    def start(self):
        """Start listening to all message bus channels."""
        if self.is_running:
            logger.warning("MessageBusListener already running")
            return
            
        logger.info("Starting MessageBusListener...")
        
        # Subscribe to all channels
        self._subscribe_to_channel(Channels.WORKFLOW_EVENTS, self._handle_workflow_event)
        self._subscribe_to_channel(Channels.TASK_EVENTS, self._handle_task_event)
        self._subscribe_to_channel(Channels.AGENT_RESULTS, self._handle_agent_event)
        self._subscribe_to_channel(Channels.TEST_RESULTS, self._handle_test_event)
        self._subscribe_to_channel(Channels.ARTIFACTS, self._handle_artifact_event)
        self._subscribe_to_channel(Channels.APPROVALS, self._handle_approval_event)
        
        self.is_running = True
        logger.info("MessageBusListener started successfully")
        
    def stop(self):
        """Stop listening to message bus channels."""
        if not self.is_running:
            return
            
        logger.info("Stopping MessageBusListener...")
        # Unsubscribe would be implemented in message bus
        self.subscriptions.clear()
        self.is_running = False
        logger.info("MessageBusListener stopped")
        
    def _subscribe_to_channel(self, channel: str, handler: Callable[[Event], None]):
        """
        Subscribe to a message bus channel with a handler.
        
        Args:
            channel: Channel name (from Channels enum)
            handler: Callback function to handle events
        """
        logger.debug(f"Subscribing to channel: {channel}")
        self.message_bus.subscribe(channel, handler)
        self.subscriptions[channel] = handler
        
    def _handle_workflow_event(self, event: Event):
        """
        Handle workflow lifecycle events.
        
        Events: WORKFLOW_CREATED, WORKFLOW_STARTED, WORKFLOW_COMPLETED, etc.
        """
        try:
            logger.debug(f"Workflow event: {event.event_type}")
            
            # Forward to Django Channels for WebSocket broadcast
            asyncio.create_task(
                self.event_forwarder.forward_event(event)
            )
            
            # Additional workflow-specific handling
            if event.event_type == EventType.WORKFLOW_COMPLETED:
                logger.info(f"Workflow {event.workflow_id} completed successfully")
            elif event.event_type == EventType.WORKFLOW_FAILED:
                logger.warning(f"Workflow {event.workflow_id} failed: {event.data.get('reason')}")
                
        except Exception as e:
            logger.error(f"Error handling workflow event: {e}", exc_info=True)
            
    def _handle_task_event(self, event: Event):
        """
        Handle task execution events.
        
        Events: TASK_DISPATCHED, TASK_STARTED, TASK_COMPLETED, TASK_FAILED, etc.
        """
        try:
            logger.debug(f"Task event: {event.event_type} for task {event.task_id}")
            
            # Forward to WebSocket clients
            asyncio.create_task(
                self.event_forwarder.forward_event(event)
            )
            
            # Log task failures for monitoring
            if event.event_type == EventType.TASK_FAILED:
                error_msg = event.data.get('error_message', 'Unknown error')
                logger.warning(
                    f"Task {event.task_id} failed: {error_msg}, "
                    f"retry_count={event.data.get('retry_count', 0)}"
                )
                
        except Exception as e:
            logger.error(f"Error handling task event: {e}", exc_info=True)
            
    def _handle_agent_event(self, event: Event):
        """
        Handle agent activity events.
        
        Events: AGENT_THINKING, AGENT_ACTION, AGENT_ERROR, etc.
        """
        try:
            logger.debug(f"Agent event: {event.event_type} from {event.source}")
            
            # Forward to WebSocket for real-time agent monitoring
            asyncio.create_task(
                self.event_forwarder.forward_event(event)
            )
            
        except Exception as e:
            logger.error(f"Error handling agent event: {e}", exc_info=True)
            
    def _handle_test_event(self, event: Event):
        """
        Handle test execution events.
        
        Events: TEST_STARTED, TEST_PASSED, TEST_FAILED, etc.
        """
        try:
            logger.debug(f"Test event: {event.event_type}")
            
            # Forward to WebSocket
            asyncio.create_task(
                self.event_forwarder.forward_event(event)
            )
            
            # Log test results
            if event.event_type == EventType.TEST_PASSED:
                logger.info(
                    f"Tests passed for task {event.task_id}, "
                    f"coverage={event.data.get('coverage', 'N/A')}"
                )
            elif event.event_type == EventType.TEST_FAILED:
                failures = event.data.get('failures', 0)
                logger.warning(f"Tests failed for task {event.task_id}: {failures} failures")
                
        except Exception as e:
            logger.error(f"Error handling test event: {e}", exc_info=True)
            
    def _handle_artifact_event(self, event: Event):
        """
        Handle artifact creation/update events.
        
        Events: ARTIFACT_CREATED, ARTIFACT_UPDATED, ARTIFACT_DELETED
        """
        try:
            logger.debug(f"Artifact event: {event.event_type}")
            
            # Forward to WebSocket
            asyncio.create_task(
                self.event_forwarder.forward_event(event)
            )
            
            # Log artifact creation
            if event.event_type == EventType.ARTIFACT_CREATED:
                artifact_path = event.data.get('artifact_path')
                logger.info(f"Artifact created: {artifact_path}")
                
        except Exception as e:
            logger.error(f"Error handling artifact event: {e}", exc_info=True)
            
    def _handle_approval_event(self, event: Event):
        """
        Handle approval workflow events.
        
        Events: APPROVAL_REQUIRED, APPROVAL_GRANTED, APPROVAL_DENIED
        """
        try:
            logger.debug(f"Approval event: {event.event_type}")
            
            # Forward to WebSocket
            asyncio.create_task(
                self.event_forwarder.forward_event(event)
            )
            
            # Log approval requests
            if event.event_type == EventType.APPROVAL_REQUIRED:
                approval_type = event.data.get('approval_type')
                logger.info(f"Approval required for task {event.task_id}: {approval_type}")
                
        except Exception as e:
            logger.error(f"Error handling approval event: {e}", exc_info=True)
            
    def get_statistics(self) -> Dict:
        """
        Get listener statistics.
        
        Returns:
            Dictionary with subscription count and status
        """
        return {
            "is_running": self.is_running,
            "subscribed_channels": len(self.subscriptions),
            "channels": list(self.subscriptions.keys())
        }


# Singleton instance
_listener_instance: Optional[MessageBusListener] = None


def get_message_bus_listener() -> MessageBusListener:
    """Get or create the global MessageBusListener instance."""
    global _listener_instance
    if _listener_instance is None:
        _listener_instance = MessageBusListener()
    return _listener_instance


def start_listener():
    """Start the global message bus listener."""
    listener = get_message_bus_listener()
    listener.start()
    return listener


def stop_listener():
    """Stop the global message bus listener."""
    listener = get_message_bus_listener()
    listener.stop()
