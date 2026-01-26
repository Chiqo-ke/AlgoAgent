"""
Event Forwarder

Forwards events from the multi-agent message bus to Django Channels
for WebSocket broadcasting to connected clients.

Uses Django Channels' channel layer to send events to WebSocket consumers
that are listening for specific workflow updates.
"""

import logging
import json
from typing import Optional, Dict
from datetime import datetime
from contracts.event_types import Event


logger = logging.getLogger(__name__)


class EventForwarder:
    """
    Forwards events from message bus to Django Channels.
    
    This class bridges the multi-agent system's internal message bus
    with Django's WebSocket layer, enabling real-time event streaming
    to external clients (Textual CLI, web frontend, etc.).
    """
    
    def __init__(self, channel_layer=None):
        """
        Initialize the event forwarder.
        
        Args:
            channel_layer: Django Channels layer instance (imported when needed)
        """
        self.channel_layer = channel_layer
        self._channel_layer_imported = False
        
    def _ensure_channel_layer(self):
        """Lazy import of Django Channels layer to avoid import errors."""
        if not self._channel_layer_imported:
            try:
                from channels.layers import get_channel_layer
                if self.channel_layer is None:
                    self.channel_layer = get_channel_layer()
                self._channel_layer_imported = True
                logger.info("Django Channels layer loaded successfully")
            except ImportError:
                logger.warning(
                    "Django Channels not available. Events will not be forwarded to WebSocket. "
                    "Install channels: pip install channels channels-redis"
                )
                self._channel_layer_imported = True  # Don't try again
            except Exception as e:
                logger.error(f"Error loading Django Channels layer: {e}")
                
    async def forward_event(self, event: Event):
        """
        Forward an event to Django Channels for WebSocket broadcast.
        
        Args:
            event: Event object to forward
        """
        self._ensure_channel_layer()
        
        if self.channel_layer is None:
            # No channel layer available, skip forwarding
            return
            
        try:
            # Prepare event data for WebSocket transmission
            event_data = self._serialize_event(event)
            
            # Send to workflow-specific channel group
            workflow_group = f"workflow_{event.workflow_id}"
            
            await self.channel_layer.group_send(
                workflow_group,
                {
                    "type": "workflow.event",
                    "event": event_data
                }
            )
            
            logger.debug(
                f"Forwarded {event.event_type} to group {workflow_group}"
            )
            
            # Also send to user-specific channel if we have user context
            # This would require adding user_id to events or metadata
            user_id = event.metadata.get('user_id') if event.metadata else None
            if user_id:
                user_group = f"user_{user_id}"
                await self.channel_layer.group_send(
                    user_group,
                    {
                        "type": "workflow.event",
                        "event": event_data
                    }
                )
                logger.debug(f"Forwarded {event.event_type} to user {user_id}")
                
        except Exception as e:
            logger.error(f"Error forwarding event to Django Channels: {e}", exc_info=True)
            
    def _serialize_event(self, event: Event) -> Dict:
        """
        Serialize event to JSON-compatible dictionary.
        
        Args:
            event: Event object
            
        Returns:
            Dictionary ready for JSON serialization
        """
        return {
            "event_id": event.event_id,
            "event_type": event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type),
            "correlation_id": event.correlation_id,
            "workflow_id": event.workflow_id,
            "task_id": event.task_id,
            "timestamp": event.timestamp,
            "source": event.source,
            "data": event.data,
            "metadata": event.metadata or {}
        }
        
    async def send_heartbeat(self, workflow_id: str, status: str):
        """
        Send heartbeat message to WebSocket clients.
        
        Args:
            workflow_id: Target workflow
            status: Current workflow status
        """
        self._ensure_channel_layer()
        
        if self.channel_layer is None:
            return
            
        try:
            workflow_group = f"workflow_{workflow_id}"
            await self.channel_layer.group_send(
                workflow_group,
                {
                    "type": "workflow.heartbeat",
                    "heartbeat": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "workflow_status": status
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")
            
    async def send_error(self, workflow_id: str, error_code: int, message: str):
        """
        Send error message to WebSocket clients.
        
        Args:
            workflow_id: Target workflow (or None for connection-level errors)
            error_code: Error code (4xxx for WebSocket)
            message: Error message
        """
        self._ensure_channel_layer()
        
        if self.channel_layer is None:
            return
            
        try:
            if workflow_id:
                workflow_group = f"workflow_{workflow_id}"
            else:
                workflow_group = "broadcast"  # Connection-level errors
                
            await self.channel_layer.group_send(
                workflow_group,
                {
                    "type": "workflow.error",
                    "error": {
                        "code": error_code,
                        "message": message
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error sending error message: {e}")


# Singleton instance
_forwarder_instance: Optional[EventForwarder] = None


def get_event_forwarder() -> EventForwarder:
    """Get or create the global EventForwarder instance."""
    global _forwarder_instance
    if _forwarder_instance is None:
        _forwarder_instance = EventForwarder()
    return _forwarder_instance
