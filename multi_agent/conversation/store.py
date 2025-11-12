"""
Redis-backed conversation store for maintaining chat history.

Conversation state is independent of API keys, allowing seamless
key rotation without losing context.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import redis
from redis import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class ConversationStore:
    """
    Redis-backed conversation history storage.
    
    Uses Redis data structures:
    - conv:messages:<conv_id> - List of JSON-encoded messages
    - conv:meta:<conv_id> - Hash for metadata
    """
    
    def __init__(self, redis_client: Optional[Redis] = None):
        """
        Initialize conversation store.
        
        Args:
            redis_client: Redis client instance. If None, creates from environment.
        """
        if redis_client is None:
            redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
            redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
        
        self.redis = redis_client
        self.default_ttl = int(os.environ.get('CONVERSATION_TTL_SECONDS', 86400))  # 24 hours
        
        logger.info("Conversation store initialized")
    
    def create_conversation(
        self,
        conv_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create a new conversation.
        
        Args:
            conv_id: Unique conversation identifier
            metadata: Optional metadata (user_id, model, tags, etc.)
            
        Returns:
            True if created, False if already exists
        """
        meta_key = f"conv:meta:{conv_id}"
        
        try:
            # Check if exists
            if self.redis.exists(meta_key):
                logger.debug(f"Conversation {conv_id} already exists")
                return False
            
            # Initialize metadata
            meta = metadata or {}
            meta['created_at'] = datetime.utcnow().isoformat()
            meta['updated_at'] = meta['created_at']
            meta['message_count'] = 0
            meta['total_tokens'] = 0
            
            self.redis.hset(meta_key, mapping=self._flatten_meta(meta))
            self.redis.expire(meta_key, self.default_ttl)
            
            logger.info(f"Created conversation {conv_id}")
            return True
            
        except RedisError as e:
            logger.error(f"Redis error creating conversation {conv_id}: {e}")
            return False
    
    def append_message(
        self,
        conv_id: str,
        role: str,
        content: str,
        tokens: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Append a message to conversation history.
        
        Args:
            conv_id: Conversation identifier
            role: Message role ('user', 'assistant', 'system')
            content: Message content
            tokens: Token count (optional)
            metadata: Additional metadata (model, key_id, etc.)
        """
        msg_key = f"conv:messages:{conv_id}"
        meta_key = f"conv:meta:{conv_id}"
        
        try:
            # Create message
            message = {
                'role': role,
                'content': content,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if tokens is not None:
                message['tokens'] = tokens
            
            if metadata:
                message['metadata'] = metadata
            
            # Append to list
            self.redis.rpush(msg_key, json.dumps(message))
            self.redis.expire(msg_key, self.default_ttl)
            
            # Update metadata
            self.redis.hincrby(meta_key, 'message_count', 1)
            if tokens:
                self.redis.hincrby(meta_key, 'total_tokens', tokens)
            self.redis.hset(meta_key, 'updated_at', datetime.utcnow().isoformat())
            
            if metadata and metadata.get('model'):
                self.redis.hset(meta_key, 'last_model', metadata['model'])
            
            logger.debug(f"Appended {role} message to {conv_id}")
            
        except RedisError as e:
            logger.error(f"Redis error appending message to {conv_id}: {e}")
    
    def get_history(
        self,
        conv_id: str,
        limit: Optional[int] = None,
        include_metadata: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history.
        
        Args:
            conv_id: Conversation identifier
            limit: Max number of recent messages to return (None = all)
            include_metadata: Include message metadata in response
            
        Returns:
            List of messages in chronological order
        """
        msg_key = f"conv:messages:{conv_id}"
        
        try:
            # Get messages
            if limit:
                # Get last N messages
                raw_messages = self.redis.lrange(msg_key, -limit, -1)
            else:
                # Get all messages
                raw_messages = self.redis.lrange(msg_key, 0, -1)
            
            messages = []
            for raw in raw_messages:
                msg = json.loads(raw)
                
                if not include_metadata:
                    # Return only role and content for LLM API
                    messages.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })
                else:
                    messages.append(msg)
            
            return messages
            
        except RedisError as e:
            logger.error(f"Redis error getting history for {conv_id}: {e}")
            return []
    
    def get_metadata(self, conv_id: str) -> Dict[str, Any]:
        """
        Get conversation metadata.
        
        Returns:
            Metadata dict or empty dict if not found
        """
        meta_key = f"conv:meta:{conv_id}"
        
        try:
            data = self.redis.hgetall(meta_key)
            if not data:
                return {}
            
            return self._unflatten_meta(data)
            
        except RedisError as e:
            logger.error(f"Redis error getting metadata for {conv_id}: {e}")
            return {}
    
    def truncate_history(
        self,
        conv_id: str,
        keep_last_n: int = 20
    ):
        """
        Truncate conversation history to most recent N messages.
        
        Useful for managing context window size and costs.
        
        Args:
            conv_id: Conversation identifier
            keep_last_n: Number of recent messages to keep
        """
        msg_key = f"conv:messages:{conv_id}"
        meta_key = f"conv:meta:{conv_id}"
        
        try:
            # Get current count
            total = self.redis.llen(msg_key)
            
            if total <= keep_last_n:
                logger.debug(f"Conversation {conv_id} already has {total} messages")
                return
            
            # Keep only last N messages
            # Use LTRIM to keep range [-keep_last_n, -1]
            self.redis.ltrim(msg_key, -keep_last_n, -1)
            
            # Update metadata
            self.redis.hset(meta_key, 'message_count', keep_last_n)
            self.redis.hset(meta_key, 'updated_at', datetime.utcnow().isoformat())
            
            logger.info(f"Truncated {conv_id}: {total} -> {keep_last_n} messages")
            
        except RedisError as e:
            logger.error(f"Redis error truncating {conv_id}: {e}")
    
    def delete_conversation(self, conv_id: str):
        """Delete a conversation and all its messages."""
        msg_key = f"conv:messages:{conv_id}"
        meta_key = f"conv:meta:{conv_id}"
        
        try:
            self.redis.delete(msg_key, meta_key)
            logger.info(f"Deleted conversation {conv_id}")
        except RedisError as e:
            logger.error(f"Redis error deleting {conv_id}: {e}")
    
    def list_conversations(
        self,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[str]:
        """
        List conversation IDs.
        
        Args:
            user_id: Filter by user_id (if stored in metadata)
            limit: Max number of conversations to return
            
        Returns:
            List of conversation IDs
        """
        try:
            # Scan for conv:meta:* keys
            pattern = "conv:meta:*"
            conv_ids = []
            
            for key in self.redis.scan_iter(match=pattern, count=100):
                conv_id = key.replace("conv:meta:", "")
                
                # Filter by user_id if specified
                if user_id:
                    meta = self.get_metadata(conv_id)
                    if meta.get('user_id') != user_id:
                        continue
                
                conv_ids.append(conv_id)
                
                if len(conv_ids) >= limit:
                    break
            
            return conv_ids
            
        except RedisError as e:
            logger.error(f"Redis error listing conversations: {e}")
            return []
    
    def health_check(self) -> bool:
        """Check if Redis connection is healthy."""
        try:
            self.redis.ping()
            return True
        except RedisError:
            return False
    
    def _flatten_meta(self, meta: Dict[str, Any]) -> Dict[str, str]:
        """Convert metadata to Redis hash format (string values only)."""
        flat = {}
        for key, value in meta.items():
            if isinstance(value, (dict, list)):
                flat[key] = json.dumps(value)
            else:
                flat[key] = str(value)
        return flat
    
    def _unflatten_meta(self, data: Dict[str, str]) -> Dict[str, Any]:
        """Convert Redis hash data back to metadata dict."""
        meta = {}
        for key, value in data.items():
            # Try to parse JSON
            if value.startswith('{') or value.startswith('['):
                try:
                    meta[key] = json.loads(value)
                except json.JSONDecodeError:
                    meta[key] = value
            # Convert numeric strings
            elif value.isdigit():
                meta[key] = int(value)
            else:
                meta[key] = value
        return meta


# Singleton instance
_conversation_store: Optional[ConversationStore] = None


def get_conversation_store(redis_client: Optional[Redis] = None) -> ConversationStore:
    """Get or create singleton conversation store."""
    global _conversation_store
    if _conversation_store is None:
        _conversation_store = ConversationStore(redis_client)
    return _conversation_store


def reset_conversation_store():
    """Reset singleton (for testing)."""
    global _conversation_store
    _conversation_store = None
