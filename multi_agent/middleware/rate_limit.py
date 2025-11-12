"""
Per-user and global rate limiting middleware using token bucket algorithm.

Protects the system from:
- Individual user abuse
- Overall system overload
- DDoS attacks
"""
import os
import time
import logging
from typing import Optional
import redis
from redis import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str, retry_after: int):
        super().__init__(message)
        self.retry_after = retry_after  # Seconds


class TokenBucketRateLimiter:
    """
    Token bucket rate limiter with Redis backend.
    
    Supports:
    - Per-user rate limits
    - Global rate limits
    - Configurable refill rates
    - Burst capacity
    """
    
    def __init__(
        self,
        redis_client: Optional[Redis] = None,
        user_rpm: int = 10,
        user_burst: int = 20,
        global_rpm: int = 1000,
        global_burst: int = 2000
    ):
        """
        Initialize rate limiter.
        
        Args:
            redis_client: Redis client instance
            user_rpm: Requests per minute per user
            user_burst: Burst capacity per user
            global_rpm: Global requests per minute
            global_burst: Global burst capacity
        """
        if redis_client is None:
            redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
            redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_timeout=5
            )
        
        self.redis = redis_client
        
        # User limits
        self.user_rpm = user_rpm
        self.user_burst = user_burst
        self.user_refill_rate = user_rpm / 60.0  # tokens per second
        
        # Global limits
        self.global_rpm = global_rpm
        self.global_burst = global_burst
        self.global_refill_rate = global_rpm / 60.0
        
        # Load Lua script for atomic token bucket
        self.bucket_script = self._create_bucket_script()
        
        logger.info(
            f"Rate limiter initialized: user_rpm={user_rpm}, "
            f"global_rpm={global_rpm}"
        )
    
    def check_rate_limit(
        self,
        user_id: str,
        tokens_required: int = 1
    ) -> bool:
        """
        Check if request is within rate limits.
        
        Args:
            user_id: User identifier
            tokens_required: Number of tokens to consume (default 1)
            
        Returns:
            True if within limits, False otherwise
            
        Raises:
            RateLimitExceeded: If limits exceeded
        """
        # Check user limit
        user_ok, user_retry = self._check_bucket(
            f"rl:user:{user_id}",
            tokens_required,
            self.user_burst,
            self.user_refill_rate
        )
        
        if not user_ok:
            raise RateLimitExceeded(
                f"User rate limit exceeded for {user_id}",
                retry_after=user_retry
            )
        
        # Check global limit
        global_ok, global_retry = self._check_bucket(
            "rl:global",
            tokens_required,
            self.global_burst,
            self.global_refill_rate
        )
        
        if not global_ok:
            raise RateLimitExceeded(
                "Global rate limit exceeded",
                retry_after=global_retry
            )
        
        return True
    
    def _check_bucket(
        self,
        key: str,
        tokens_required: int,
        capacity: int,
        refill_rate: float
    ) -> tuple[bool, int]:
        """
        Check token bucket and consume tokens if available.
        
        Uses Lua script for atomic operation.
        
        Returns:
            (success: bool, retry_after_seconds: int)
        """
        try:
            now = time.time()
            
            result = self.bucket_script(
                keys=[key],
                args=[
                    str(capacity),
                    str(refill_rate),
                    str(tokens_required),
                    str(now)
                ]
            )
            
            # result: 1 = success, 0 = rate limited
            # If rate limited, calculate retry_after
            if result == 1:
                return True, 0
            else:
                # Estimate retry_after based on refill rate
                retry_after = int(tokens_required / refill_rate) + 1
                return False, retry_after
                
        except RedisError as e:
            logger.error(f"Redis error checking rate limit: {e}")
            # Fail open - allow request if Redis is down
            return True, 0
    
    def _create_bucket_script(self):
        """Create Lua script for atomic token bucket."""
        lua_script = """
        -- Token bucket implementation
        -- KEYS[1] = bucket key
        -- ARGV[1] = capacity
        -- ARGV[2] = refill_rate (tokens per second)
        -- ARGV[3] = tokens_required
        -- ARGV[4] = current_time
        
        local key = KEYS[1]
        local capacity = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local required = tonumber(ARGV[3])
        local now = tonumber(ARGV[4])
        
        -- Get current bucket state
        local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
        local tokens = tonumber(bucket[1]) or capacity
        local last_refill = tonumber(bucket[2]) or now
        
        -- Calculate refill
        local elapsed = now - last_refill
        local refill_amount = elapsed * refill_rate
        tokens = math.min(capacity, tokens + refill_amount)
        
        -- Check if we have enough tokens
        if tokens >= required then
            -- Consume tokens
            tokens = tokens - required
            redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
            redis.call('EXPIRE', key, 3600)  -- 1 hour TTL
            return 1
        else
            -- Not enough tokens
            redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
            redis.call('EXPIRE', key, 3600)
            return 0
        end
        """
        
        return self.redis.register_script(lua_script)
    
    def get_user_status(self, user_id: str) -> dict:
        """
        Get current rate limit status for user.
        
        Returns:
            {
                'available_tokens': float,
                'capacity': int,
                'refill_rate': float
            }
        """
        key = f"rl:user:{user_id}"
        try:
            data = self.redis.hmget(key, 'tokens', 'last_refill')
            tokens = float(data[0]) if data[0] else self.user_burst
            last_refill = float(data[1]) if data[1] else time.time()
            
            # Calculate current tokens with refill
            elapsed = time.time() - last_refill
            current_tokens = min(
                self.user_burst,
                tokens + (elapsed * self.user_refill_rate)
            )
            
            return {
                'available_tokens': current_tokens,
                'capacity': self.user_burst,
                'refill_rate': self.user_refill_rate
            }
            
        except RedisError as e:
            logger.error(f"Redis error getting user status: {e}")
            return {
                'available_tokens': 0,
                'capacity': self.user_burst,
                'refill_rate': self.user_refill_rate
            }
    
    def get_global_status(self) -> dict:
        """Get current global rate limit status."""
        key = "rl:global"
        try:
            data = self.redis.hmget(key, 'tokens', 'last_refill')
            tokens = float(data[0]) if data[0] else self.global_burst
            last_refill = float(data[1]) if data[1] else time.time()
            
            elapsed = time.time() - last_refill
            current_tokens = min(
                self.global_burst,
                tokens + (elapsed * self.global_refill_rate)
            )
            
            return {
                'available_tokens': current_tokens,
                'capacity': self.global_burst,
                'refill_rate': self.global_refill_rate
            }
            
        except RedisError as e:
            logger.error(f"Redis error getting global status: {e}")
            return {
                'available_tokens': 0,
                'capacity': self.global_burst,
                'refill_rate': self.global_refill_rate
            }
    
    def reset_user_limit(self, user_id: str):
        """Reset rate limit for a user (admin operation)."""
        key = f"rl:user:{user_id}"
        try:
            self.redis.delete(key)
            logger.info(f"Reset rate limit for user {user_id}")
        except RedisError as e:
            logger.error(f"Redis error resetting user limit: {e}")
    
    def health_check(self) -> bool:
        """Check if Redis connection is healthy."""
        try:
            self.redis.ping()
            return True
        except RedisError:
            return False


# Singleton instance
_rate_limiter: Optional[TokenBucketRateLimiter] = None


def get_rate_limiter() -> TokenBucketRateLimiter:
    """Get or create singleton rate limiter."""
    global _rate_limiter
    if _rate_limiter is None:
        # Load config from environment
        user_rpm = int(os.environ.get('USER_RPM_DEFAULT', 10))
        user_burst = int(os.environ.get('USER_BURST_DEFAULT', 20))
        global_rpm = int(os.environ.get('GLOBAL_RPM_MAX', 1000))
        global_burst = int(os.environ.get('GLOBAL_BURST_MAX', 2000))
        
        _rate_limiter = TokenBucketRateLimiter(
            user_rpm=user_rpm,
            user_burst=user_burst,
            global_rpm=global_rpm,
            global_burst=global_burst
        )
    return _rate_limiter


def reset_rate_limiter():
    """Reset singleton (for testing)."""
    global _rate_limiter
    _rate_limiter = None
