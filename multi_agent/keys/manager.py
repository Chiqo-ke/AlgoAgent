"""
KeyManager service for intelligent API key selection and management.

Responsibilities:
- Maintain in-memory cache of active keys
- Select optimal key based on model preference and capacity
- Enforce RPM/TPM limits through atomic Redis reservations
- Track key health and cooldown status
- Handle failover and load distribution
"""
import random
import logging
from typing import Optional, Dict, List, Any
from pathlib import Path
import json

from .models import APIKey
from .secret_store import fetch_api_secret, SecretStoreError
from .redis_client import RedisRateLimiter, get_redis_limiter

logger = logging.getLogger(__name__)


class KeySelectionError(Exception):
    """Raised when no suitable key can be selected."""
    pass


class KeyManager:
    """
    Manages API key selection, capacity tracking, and health monitoring.
    
    Thread-safe for concurrent access (atomicity provided by Redis).
    """
    
    def __init__(
        self,
        redis_limiter: Optional[RedisRateLimiter] = None,
        key_store_path: Optional[Path] = None
    ):
        """
        Initialize KeyManager.
        
        Args:
            redis_limiter: Redis rate limiter instance
            key_store_path: Path to JSON file with key metadata (if not using Django)
        """
        self.redis_limiter = redis_limiter or get_redis_limiter()
        self.key_store_path = key_store_path
        self.keys: Dict[str, APIKey] = {}
        
        # Configuration
        self.max_retries = 3
        self.enable_fallback = True
        
        # Load keys
        self.reload_keys()
        
        logger.info(f"KeyManager initialized with {len(self.keys)} active keys")
    
    def reload_keys(self):
        """
        Reload API keys from storage.
        
        For Django: queries APIKey model
        For standalone: loads from JSON file
        """
        if self.key_store_path:
            self._load_keys_from_file()
        else:
            self._load_keys_from_django()
    
    def _load_keys_from_file(self):
        """Load keys from JSON file (standalone mode)."""
        if not self.key_store_path or not self.key_store_path.exists():
            logger.warning(f"Key store file not found: {self.key_store_path}")
            return
        
        try:
            with open(self.key_store_path, 'r') as f:
                data = json.load(f)
            
            self.keys = {}
            for key_data in data.get('keys', []):
                key = APIKey.from_dict(key_data)
                if key.active:
                    self.keys[key.key_id] = key
            
            logger.info(f"Loaded {len(self.keys)} keys from {self.key_store_path}")
            
        except Exception as e:
            logger.error(f"Error loading keys from file: {e}")
    
    def _load_keys_from_django(self):
        """Load keys from Django model."""
        try:
            # For Django integration, uncomment:
            # from .models import APIKey as DjangoAPIKey
            # queryset = DjangoAPIKey.objects.filter(active=True)
            # self.keys = {k.key_id: k for k in queryset}
            
            # For now, use empty dict (standalone mode)
            logger.debug("Django model loading not available in standalone mode")
            
        except Exception as e:
            logger.error(f"Error loading keys from Django: {e}")
    
    def select_key(
        self,
        model_preference: Optional[str] = None,
        tokens_needed: int = 1000,
        exclude_keys: Optional[List[str]] = None,
        workload: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Select an API key with available capacity.
        
        Selection algorithm:
        1. Filter by workload type (light/medium/heavy) if specified
        2. Filter by model preference (if specified)
        3. Shuffle to distribute load
        4. Check cooldown status
        5. Atomically reserve RPM and TPM capacity
        6. Fetch secret from vault
        7. Return key metadata + secret
        
        Args:
            model_preference: Preferred model name (e.g., "gemini-2.5-pro")
            tokens_needed: Estimated tokens for this request
            exclude_keys: List of key_ids to exclude (e.g., already tried)
            workload: Workload type - "light" (flash), "medium" (pro), "heavy" (pro-preview)
            
        Returns:
            {
                'key_id': str,
                'secret': str,
                'model': str,
                'provider': str
            }
            or None if no suitable key found
        """
        if not self.keys:
            logger.error("No active keys available")
            return None
        
        exclude_keys = exclude_keys or []
        
        # Get candidates
        candidates = [
            k for k in self.keys.values()
            if k.active and k.key_id not in exclude_keys
        ]
        
        if not candidates:
            logger.warning("No candidate keys after filtering")
            return None
        
        # Filter by workload if specified
        if workload:
            workload_candidates = [
                k for k in candidates
                if k.tags.get('workload') == workload
            ]
            if workload_candidates:
                candidates = workload_candidates
                logger.debug(f"Filtered to {len(candidates)} keys with workload={workload}")
        
        # Sort by preference: exact model match first, then others
        # Add randomness to distribute load
        candidates.sort(
            key=lambda k: (
                k.model_name != model_preference if model_preference else 0,
                k.tags.get('priority', 999),
                random.random()
            )
        )
        
        # Try each candidate
        for key in candidates:
            result = self._try_reserve_key(key, tokens_needed)
            if result:
                return result
        
        # No key available - try fallback strategies
        if self.enable_fallback:
            # Try without workload filter
            if workload:
                logger.info(f"Fallback: retrying without workload filter ({workload})")
                return self.select_key(
                    model_preference=model_preference,
                    tokens_needed=tokens_needed,
                    exclude_keys=exclude_keys,
                    workload=None
                )
            # Try without model preference
            elif model_preference:
                logger.info(f"Fallback: retrying without model preference {model_preference}")
                return self.select_key(
                    model_preference=None,
                    tokens_needed=tokens_needed,
                    exclude_keys=exclude_keys,
                    workload=None
                )
        
        logger.warning("No keys with available capacity")
        return None
    
    def _try_reserve_key(
        self,
        key: APIKey,
        tokens_needed: int
    ) -> Optional[Dict[str, Any]]:
        """
        Try to reserve capacity on a specific key.
        
        Returns:
            Key metadata dict if successful, None otherwise
        """
        key_id = key.key_id
        
        # Check cooldown
        if self.redis_limiter.is_in_cooldown(key_id):
            ttl = self.redis_limiter.get_cooldown_ttl(key_id)
            logger.debug(f"Key {key_id} in cooldown (TTL: {ttl}s)")
            return None
        
        # Reserve RPM slot
        if not self.redis_limiter.reserve_rpm_slot(key_id, key.rpm):
            logger.debug(f"Key {key_id} RPM limit exceeded")
            return None
        
        # Reserve token budget
        if not self.redis_limiter.reserve_token_budget(key_id, key.tpm, tokens_needed):
            logger.debug(f"Key {key_id} TPM limit exceeded (needed {tokens_needed})")
            return None
        
        # Fetch secret
        try:
            secret = fetch_api_secret(key_id)
        except SecretStoreError as e:
            logger.error(f"Failed to fetch secret for {key_id}: {e}")
            # Put key in short cooldown to avoid repeated failures
            self.redis_limiter.set_cooldown(key_id, 60)
            return None
        
        logger.info(f"Selected key {key_id} (model: {key.model_name}, tokens: {tokens_needed})")
        
        return {
            'key_id': key_id,
            'secret': secret,
            'model': key.model_name,
            'provider': key.provider,
            'tags': key.tags
        }
    
    def mark_key_unhealthy(
        self,
        key_id: str,
        cooldown_seconds: int = 60,
        reason: str = "unknown"
    ):
        """
        Mark a key as unhealthy and put in cooldown.
        
        Args:
            key_id: Key identifier
            cooldown_seconds: Duration of cooldown
            reason: Reason for marking unhealthy (for logging)
        """
        self.redis_limiter.set_cooldown(key_id, cooldown_seconds)
        logger.warning(f"Key {key_id} marked unhealthy: {reason} (cooldown: {cooldown_seconds}s)")
    
    def get_key_status(self, key_id: str) -> Dict[str, Any]:
        """
        Get current status of a key.
        
        Returns:
            {
                'key_id': str,
                'active': bool,
                'in_cooldown': bool,
                'cooldown_ttl': int or None,
                'rpm_usage': dict,
                'tpm_usage': dict,
                'model': str
            }
        """
        key = self.keys.get(key_id)
        
        if not key:
            return {'key_id': key_id, 'error': 'Key not found'}
        
        in_cooldown = self.redis_limiter.is_in_cooldown(key_id)
        cooldown_ttl = self.redis_limiter.get_cooldown_ttl(key_id) if in_cooldown else None
        
        return {
            'key_id': key_id,
            'active': key.active,
            'model': key.model_name,
            'provider': key.provider,
            'in_cooldown': in_cooldown,
            'cooldown_ttl': cooldown_ttl,
            'rpm_usage': self.redis_limiter.get_rpm_usage(key_id),
            'tpm_usage': self.redis_limiter.get_tpm_usage(key_id),
            'rpm_limit': key.rpm,
            'tpm_limit': key.tpm
        }
    
    def get_all_key_statuses(self) -> List[Dict[str, Any]]:
        """Get status of all active keys."""
        return [self.get_key_status(k.key_id) for k in self.keys.values()]
    
    def add_key(self, key: APIKey):
        """Add or update a key in the cache."""
        if key.active:
            self.keys[key.key_id] = key
            logger.info(f"Added key {key.key_id}")
        else:
            logger.debug(f"Skipped inactive key {key.key_id}")
    
    def remove_key(self, key_id: str):
        """Remove a key from the cache."""
        if key_id in self.keys:
            del self.keys[key_id]
            logger.info(f"Removed key {key_id}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on KeyManager.
        
        Returns:
            {
                'healthy': bool,
                'total_keys': int,
                'active_keys': int,
                'redis_healthy': bool,
                'keys_in_cooldown': int
            }
        """
        active_keys = [k for k in self.keys.values() if k.active]
        keys_in_cooldown = sum(
            1 for k in active_keys
            if self.redis_limiter.is_in_cooldown(k.key_id)
        )
        redis_healthy = self.redis_limiter.health_check()
        
        healthy = (
            len(active_keys) > 0 and
            redis_healthy and
            keys_in_cooldown < len(active_keys)  # At least one key not in cooldown
        )
        
        return {
            'healthy': healthy,
            'total_keys': len(self.keys),
            'active_keys': len(active_keys),
            'keys_in_cooldown': keys_in_cooldown,
            'redis_healthy': redis_healthy
        }


# Singleton instance
_key_manager: Optional[KeyManager] = None


def get_key_manager(
    redis_limiter: Optional[RedisRateLimiter] = None,
    key_store_path: Optional[Path] = None
) -> KeyManager:
    """
    Get or create singleton KeyManager instance.
    
    Args:
        redis_limiter: Redis limiter (used only on first call)
        key_store_path: Path to key store JSON (used only on first call)
                        Defaults to keys.json in current directory
    """
    global _key_manager
    if _key_manager is None:
        # Default to keys.json in current directory if not specified
        if key_store_path is None:
            key_store_path = Path('keys.json')
        
        _key_manager = KeyManager(
            redis_limiter=redis_limiter,
            key_store_path=key_store_path
        )
    return _key_manager


def reset_key_manager():
    """Reset singleton (for testing)."""
    global _key_manager
    _key_manager = None
