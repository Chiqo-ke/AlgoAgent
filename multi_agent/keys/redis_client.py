"""
Redis client for atomic RPM/TPM reservations and cooldown management.

Uses Lua scripts for atomic operations to prevent race conditions
in distributed environments.
"""
import os
import time
import logging
from pathlib import Path
from typing import Optional
import redis
from redis import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class RedisRateLimiter:
    """Redis-backed rate limiting with atomic reservations."""
    
    def __init__(self, redis_client: Optional[Redis] = None):
        """
        Initialize Redis rate limiter.
        
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
        
        # Load Lua scripts
        script_dir = Path(__file__).parent
        
        with open(script_dir / 'rpm_reserve.lua', 'r') as f:
            rpm_lua = f.read()
        with open(script_dir / 'tpm_reserve.lua', 'r') as f:
            tpm_lua = f.read()
        
        self.rpm_script = self.redis.register_script(rpm_lua)
        self.tpm_script = self.redis.register_script(tpm_lua)
        
        logger.info("Redis rate limiter initialized with Lua scripts")
    
    def reserve_rpm_slot(self, key_id: str, rpm_limit: int) -> bool:
        """
        Atomically reserve an RPM slot for a key.
        
        Args:
            key_id: API key identifier
            rpm_limit: Requests per minute limit for this key
            
        Returns:
            True if slot reserved successfully, False if over limit
        """
        window = str(int(time.time()) // 60)  # Current minute
        redis_key = f"rpm:{key_id}"
        
        try:
            result = self.rpm_script(
                keys=[redis_key],
                args=[window, str(rpm_limit)]
            )
            success = bool(result)
            
            if success:
                logger.debug(f"Reserved RPM slot for {key_id}")
            else:
                logger.warning(f"RPM limit exceeded for {key_id}")
            
            return success
            
        except RedisError as e:
            logger.error(f"Redis error reserving RPM slot for {key_id}: {e}")
            # Fail open - allow request if Redis is down
            return True
    
    def reserve_token_budget(
        self,
        key_id: str,
        tpm_limit: int,
        tokens_required: int
    ) -> bool:
        """
        Atomically reserve token budget for a key.
        
        Args:
            key_id: API key identifier
            tpm_limit: Tokens per minute limit for this key
            tokens_required: Number of tokens needed for this request
            
        Returns:
            True if budget reserved successfully, False if over limit
        """
        window = str(int(time.time()) // 60)  # Current minute
        redis_key = f"tpm:{key_id}"
        
        try:
            result = self.tpm_script(
                keys=[redis_key],
                args=[window, str(tpm_limit), str(tokens_required)]
            )
            success = bool(result)
            
            if success:
                logger.debug(f"Reserved {tokens_required} tokens for {key_id}")
            else:
                logger.warning(f"TPM limit exceeded for {key_id} (needed {tokens_required})")
            
            return success
            
        except RedisError as e:
            logger.error(f"Redis error reserving token budget for {key_id}: {e}")
            # Fail open - allow request if Redis is down
            return True
    
    def get_rpm_usage(self, key_id: str) -> dict:
        """
        Get current RPM usage for a key.
        
        Returns:
            {'window': str, 'count': int, 'limit': int}
        """
        redis_key = f"rpm:{key_id}"
        try:
            data = self.redis.hgetall(redis_key)
            return {
                'window': data.get('window', 'unknown'),
                'count': int(data.get('count', 0)),
            }
        except RedisError as e:
            logger.error(f"Redis error getting RPM usage for {key_id}: {e}")
            return {'window': 'error', 'count': 0}
    
    def get_tpm_usage(self, key_id: str) -> dict:
        """
        Get current TPM usage for a key.
        
        Returns:
            {'window': str, 'used': int, 'limit': int}
        """
        redis_key = f"tpm:{key_id}"
        try:
            data = self.redis.hgetall(redis_key)
            return {
                'window': data.get('window', 'unknown'),
                'used': int(data.get('used', 0)),
            }
        except RedisError as e:
            logger.error(f"Redis error getting TPM usage for {key_id}: {e}")
            return {'window': 'error', 'used': 0}
    
    def set_cooldown(self, key_id: str, seconds: int):
        """
        Put a key in cooldown (temporarily disable).
        
        Args:
            key_id: API key identifier
            seconds: Cooldown duration in seconds
        """
        redis_key = f"key:cooldown:{key_id}"
        try:
            self.redis.setex(redis_key, seconds, 1)
            logger.warning(f"Key {key_id} in cooldown for {seconds}s")
        except RedisError as e:
            logger.error(f"Redis error setting cooldown for {key_id}: {e}")
    
    def is_in_cooldown(self, key_id: str) -> bool:
        """
        Check if a key is in cooldown.
        
        Returns:
            True if key is in cooldown, False otherwise
        """
        redis_key = f"key:cooldown:{key_id}"
        try:
            return self.redis.exists(redis_key) > 0
        except RedisError as e:
            logger.error(f"Redis error checking cooldown for {key_id}: {e}")
            return False
    
    def get_cooldown_ttl(self, key_id: str) -> Optional[int]:
        """
        Get remaining cooldown time for a key.
        
        Returns:
            Seconds remaining in cooldown, or None if not in cooldown
        """
        redis_key = f"key:cooldown:{key_id}"
        try:
            ttl = self.redis.ttl(redis_key)
            return ttl if ttl > 0 else None
        except RedisError as e:
            logger.error(f"Redis error getting cooldown TTL for {key_id}: {e}")
            return None
    
    def clear_cooldown(self, key_id: str):
        """Manually clear cooldown for a key."""
        redis_key = f"key:cooldown:{key_id}"
        try:
            self.redis.delete(redis_key)
            logger.info(f"Cleared cooldown for {key_id}")
        except RedisError as e:
            logger.error(f"Redis error clearing cooldown for {key_id}: {e}")
    
    def health_check(self) -> bool:
        """
        Check if Redis connection is healthy.
        
        Returns:
            True if Redis is accessible, False otherwise
        """
        try:
            self.redis.ping()
            return True
        except RedisError:
            return False


# Singleton instance for convenience
_redis_limiter: Optional[RedisRateLimiter] = None


def get_redis_limiter() -> RedisRateLimiter:
    """Get or create singleton Redis rate limiter instance."""
    global _redis_limiter
    if _redis_limiter is None:
        _redis_limiter = RedisRateLimiter()
    return _redis_limiter
