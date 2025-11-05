"""
Message Bus Implementation

Provides pub/sub messaging for multi-agent communication with Redis backend.
"""

import json
import logging
import asyncio
from typing import Dict, Any, Callable, List, Optional
from abc import ABC, abstractmethod
import redis
from threading import Thread
import time

from contracts.event_types import Event, EventType


logger = logging.getLogger(__name__)


class MessageBus(ABC):
    """Abstract message bus interface."""
    
    @abstractmethod
    def publish(self, channel: str, event: Event):
        """Publish an event to a channel."""
        pass
    
    @abstractmethod
    def subscribe(self, channel: str, callback: Callable[[Event], None]):
        """Subscribe to a channel with a callback."""
        pass
    
    @abstractmethod
    def unsubscribe(self, channel: str):
        """Unsubscribe from a channel."""
        pass


class RedisMessageBus(MessageBus):
    """Redis-based message bus implementation."""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        """
        Initialize Redis message bus.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
        """
        self.redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        self.pubsub = self.redis_client.pubsub()
        self.subscriptions: Dict[str, Callable] = {}
        self.listener_thread: Optional[Thread] = None
        self.running = False
        
        logger.info(f"Initialized Redis message bus at {host}:{port}")
    
    def publish(self, channel: str, event: Event):
        """
        Publish an event to a channel.
        
        Args:
            channel: Channel name
            event: Event to publish
        """
        message = json.dumps(event.to_dict())
        self.redis_client.publish(channel, message)
        logger.debug(f"Published event {event.event_id} to {channel}")
    
    def subscribe(self, channel: str, callback: Callable[[Event], None]):
        """
        Subscribe to a channel with a callback.
        
        Args:
            channel: Channel name
            callback: Function to call when event received
        """
        self.subscriptions[channel] = callback
        self.pubsub.subscribe(channel)
        logger.info(f"Subscribed to channel: {channel}")
        
        # Start listener thread if not already running
        if not self.running:
            self._start_listener()
    
    def unsubscribe(self, channel: str):
        """
        Unsubscribe from a channel.
        
        Args:
            channel: Channel name
        """
        if channel in self.subscriptions:
            self.pubsub.unsubscribe(channel)
            del self.subscriptions[channel]
            logger.info(f"Unsubscribed from channel: {channel}")
    
    def _start_listener(self):
        """Start the message listener thread."""
        self.running = True
        self.listener_thread = Thread(target=self._listen, daemon=True)
        self.listener_thread.start()
        logger.info("Started message listener thread")
    
    def _listen(self):
        """Listen for messages in a background thread."""
        logger.info("Message listener started")
        
        try:
            for message in self.pubsub.listen():
                if not self.running:
                    break
                
                if message['type'] == 'message':
                    channel = message['channel']
                    data = message['data']
                    
                    try:
                        event_dict = json.loads(data)
                        event = Event.from_dict(event_dict)
                        
                        if channel in self.subscriptions:
                            callback = self.subscriptions[channel]
                            callback(event)
                        
                    except Exception as e:
                        logger.error(f"Error processing message: {e}", exc_info=True)
        
        except Exception as e:
            logger.error(f"Listener thread error: {e}", exc_info=True)
        
        finally:
            logger.info("Message listener stopped")
    
    def stop(self):
        """Stop the message bus."""
        self.running = False
        if self.listener_thread:
            self.listener_thread.join(timeout=5)
        self.pubsub.close()
        self.redis_client.close()
        logger.info("Message bus stopped")


class InMemoryMessageBus(MessageBus):
    """In-memory message bus for testing (no Redis required)."""
    
    def __init__(self):
        """Initialize in-memory message bus."""
        self.channels: Dict[str, List[Callable]] = {}
        logger.info("Initialized in-memory message bus")
    
    def publish(self, channel: str, event: Any):
        """
        Publish an event to a channel.
        
        Args:
            channel: Channel name
            event: Event to publish (Event object or dict)
        """
        if channel in self.channels:
            for callback in self.channels[channel]:
                try:
                    # Handle both sync and async callbacks
                    result = callback(event)
                    if asyncio.iscoroutine(result):
                        # If callback is async, we need to schedule it
                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                asyncio.create_task(result)
                            else:
                                asyncio.run(result)
                        except RuntimeError:
                            # No event loop, try to run it
                            asyncio.run(result)
                except Exception as e:
                    logger.error(f"Error in callback: {e}", exc_info=True)
        
        event_id = event.event_id if hasattr(event, 'event_id') else event.get('event_id', 'unknown')
        logger.debug(f"Published event {event_id} to {channel}")
    
    def subscribe(self, channel: str, callback: Callable[[Event], None]):
        """
        Subscribe to a channel with a callback.
        
        Args:
            channel: Channel name
            callback: Function to call when event received
        """
        if channel not in self.channels:
            self.channels[channel] = []
        
        self.channels[channel].append(callback)
        logger.info(f"Subscribed to channel: {channel}")
    
    def unsubscribe(self, channel: str):
        """
        Unsubscribe from a channel.
        
        Args:
            channel: Channel name
        """
        if channel in self.channels:
            del self.channels[channel]
            logger.info(f"Unsubscribed from channel: {channel}")


# Predefined channels
class Channels:
    """Standard message bus channels."""
    
    AGENT_REQUESTS = "agent.requests"
    AGENT_RESULTS = "agent.results"
    WORKFLOW_EVENTS = "workflow.events"
    TASK_EVENTS = "task.events"
    TEST_RESULTS = "test.results"
    AUDIT_LOGS = "audit.logs"
    APPROVALS = "approvals"
    ARTIFACTS = "artifacts"


# Global message bus instance (singleton)
_message_bus: Optional[MessageBus] = None


def get_message_bus(use_redis: bool = True, **kwargs) -> MessageBus:
    """
    Get or create the global message bus instance.
    
    Args:
        use_redis: Use Redis backend (True) or in-memory (False)
        **kwargs: Additional arguments for Redis connection
        
    Returns:
        MessageBus instance
    """
    global _message_bus
    
    if _message_bus is None:
        if use_redis:
            _message_bus = RedisMessageBus(**kwargs)
        else:
            _message_bus = InMemoryMessageBus()
    
    return _message_bus


def reset_message_bus():
    """Reset the global message bus (for testing)."""
    global _message_bus
    
    if _message_bus is not None:
        if isinstance(_message_bus, RedisMessageBus):
            _message_bus.stop()
        _message_bus = None
