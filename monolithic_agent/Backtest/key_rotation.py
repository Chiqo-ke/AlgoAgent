"""
Key Rotation Manager for Monolithic Agent

Provides intelligent API key selection, rotation, and capacity management
for the monolithic strategy generation system.

Features:
- Load distribution across multiple keys
- Rate limiting (RPM/TPM)
- Automatic failover and cooldown
- Health tracking
- Redis-backed atomic operations
"""

import os
import json
import logging
import time
import threading
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


@dataclass
class APIKeyMetadata:
    """Metadata for an API key"""
    key_id: str
    model_name: str
    provider: str
    rpm: int  # Requests per minute
    tpm: int  # Tokens per minute
    rpd: Optional[int] = None  # Requests per day
    burst_capacity: Optional[int] = None  # Burst capacity for rate limiting
    priority: Optional[int] = None  # Priority for key selection (lower = higher priority)
    workload_type: Optional[str] = None  # Workload type: light, heavy, etc.
    active: bool = True
    tags: Dict[str, Any] = None
    created_at: str = None
    updated_at: str = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'APIKeyMetadata':
        return cls(**data)


class KeyRotationError(Exception):
    """Raised when key rotation fails"""
    pass


class KeyManager:
    """
    Manages API key selection and rotation for the monolithic agent.
    
    Supports:
    - Single key mode (simple setup)
    - Multi-key mode with Redis rate limiting (advanced)
    - Automatic failover
    - Health tracking and cooldown
    """
    
    def __init__(self, key_store_path: Optional[Path] = None):
        """
        Initialize KeyManager.
        
        Args:
            key_store_path: Path to keys.json file (optional)
        """
        # Load environment variables
        load_dotenv()
        
        self.enabled = os.getenv('ENABLE_KEY_ROTATION', 'false').lower() == 'true'
        self.key_store_path = key_store_path or Path(__file__).parent.parent / 'keys.json'
        self.keys: Dict[str, APIKeyMetadata] = {}
        self.key_secrets: Dict[str, str] = {}
        self.key_health: Dict[str, Dict[str, Any]] = {}
        self.redis_limiter = None
        
        # Thread safety
        self._lock = threading.Lock()
        self._health_lock = threading.Lock()
        
        # Round-robin rotation tracking
        self.key_rotation_queues: Dict[str, List[str]] = {}  # Per-model queues
        self.last_used_key: Optional[str] = None
        self.current_index = 0  # Global round-robin index
        
        # Cooldown configuration
        self.cooldown_duration = int(os.getenv('KEY_COOLDOWN_DURATION', '60'))  # seconds
        
        # Model compatibility mapping for cross-model fallback
        # When a model is exhausted, try compatible models in order
        self.model_compatibility = {
            'gemini-2.0-flash': ['gemini-2.0-flash-exp', 'gemini-2.5-pro', 'gemini-2.5-flash'],
            'gemini-2.0-flash-exp': ['gemini-2.0-flash', 'gemini-2.5-pro', 'gemini-2.5-flash'],
            'gemini-2.5-pro': ['gemini-2.5-flash', 'gemini-2.0-flash-exp', 'gemini-2.0-flash'],
            'gemini-2.5-flash': ['gemini-2.0-flash', 'gemini-2.0-flash-exp', 'gemini-2.5-pro'],
        }
        
        if self.enabled:
            self._init_redis()
        
        self._load_keys()
        self._init_rotation_queues()
        logger.info(f"KeyManager initialized (rotation: {'enabled' if self.enabled else 'disabled'})")
    
    def _init_rotation_queues(self):
        """Initialize round-robin queues for each model type."""
        # Group keys by model
        model_keys = {}
        for key_id, metadata in self.keys.items():
            if not metadata.active:
                continue
            model = metadata.model_name
            if model not in model_keys:
                model_keys[model] = []
            model_keys[model].append(key_id)
        
        # Create rotation queue for each model (sorted by priority)
        for model, key_ids in model_keys.items():
            # Sort by priority (lower number = higher priority)
            sorted_keys = sorted(
                key_ids,
                key=lambda kid: (self.keys[kid].priority or 999, kid)
            )
            self.key_rotation_queues[model] = sorted_keys.copy()
        
        logger.info(f"Initialized rotation queues for {len(self.key_rotation_queues)} models")
    
    def _init_redis(self):
        """Initialize Redis for rate limiting"""
        try:
            import redis
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            self.redis_limiter = redis.from_url(redis_url, decode_responses=True)
            self.redis_limiter.ping()
            logger.info("Redis connection established for key rotation")
        except ImportError:
            logger.warning("Redis not installed - disabling key rotation")
            self.enabled = False
        except Exception as e:
            logger.warning(f"Redis connection failed - disabling key rotation: {e}")
            self.enabled = False
    
    def _load_keys(self):
        """Load API keys from environment or keys.json"""
        secret_store_type = os.getenv('SECRET_STORE_TYPE', 'env')
        
        # Load from keys.json if it exists
        if self.key_store_path.exists():
            self._load_from_keys_file()
        
        # Load secrets from environment
        if secret_store_type == 'env':
            self._load_from_env()
        elif secret_store_type == 'vault':
            self._load_from_vault()
        elif secret_store_type == 'aws':
            self._load_from_aws()
        elif secret_store_type == 'azure':
            self._load_from_azure()
        
        # Always check for single GEMINI_API_KEY
        single_key = os.getenv('GEMINI_API_KEY')
        if single_key and not self.key_secrets:
            self.key_secrets['default'] = single_key
            if 'default' not in self.keys:
                self.keys['default'] = APIKeyMetadata(
                    key_id='default',
                    model_name='gemini-2.5-flash',
                    provider='gemini',
                    rpm=60,
                    tpm=1000000
                )
    
    def _load_from_keys_file(self):
        """Load key metadata from keys.json"""
        try:
            with open(self.key_store_path, 'r') as f:
                data = json.load(f)
            
            for key_data in data.get('keys', []):
                key_id = key_data.get('key_id')
                if key_id:
                    self.keys[key_id] = APIKeyMetadata.from_dict(key_data)
                    # Initialize health tracking
                    self.key_health[key_id] = {
                        'last_used': None,
                        'error_count': 0,
                        'cooldown_until': None,
                        'success_count': 0
                    }
            
            logger.info(f"Loaded {len(self.keys)} keys from {self.key_store_path}")
        
        except Exception as e:
            logger.warning(f"Failed to load keys.json: {e}")
    
    def _load_from_env(self):
        """Load secrets from environment variables"""
        # New format: GEMINI_API_KEYS (comma-separated)
        gemini_keys_str = os.getenv('GEMINI_API_KEYS', '')
        if gemini_keys_str:
            api_keys = [k.strip() for k in gemini_keys_str.split(',') if k.strip()]
            logger.info(f"Loaded {len(api_keys)} API keys from GEMINI_API_KEYS")
            
            # Create metadata for each key if keys.json doesn't exist
            if not self.keys:
                for idx, key in enumerate(api_keys):
                    key_id = f"key_{idx + 1:02d}"
                    self.keys[key_id] = APIKeyMetadata(
                        key_id=key_id,
                        model_name='gemini-2.0-flash',  # Default, but can be used with any model
                        provider='gemini',
                        rpm=60,
                        tpm=1000000,
                        priority=idx + 1
                    )
                    self.key_secrets[key_id] = key
                    self.key_health[key_id] = {
                        'last_used': None,
                        'error_count': 0,
                        'cooldown_until': None,
                        'success_count': 0
                    }
            else:
                # Map keys to existing metadata (by priority order)
                sorted_key_ids = sorted(self.keys.keys(), key=lambda k: self.keys[k].priority or 999)
                for key_id, key in zip(sorted_key_ids, api_keys):
                    self.key_secrets[key_id] = key
        else:
            # Fallback: Try old format for backward compatibility
            for key_id in self.keys.keys():
                env_var_underscore = f"GEMINI_KEY_{key_id.replace('-', '_')}"
                env_var_hyphen = f"GEMINI_KEY_{key_id}"
                env_var_alt = f"API_KEY_{key_id.replace('-', '_')}"
                
                secret = (
                    os.getenv(env_var_underscore) or
                    os.getenv(env_var_hyphen) or
                    os.getenv(env_var_alt)
                )
                
                if secret:
                    self.key_secrets[key_id] = secret
                    logger.info(f"Loaded secret for key {key_id}")
    
    def _load_from_vault(self):
        """Load secrets from HashiCorp Vault"""
        try:
            import hvac  # type: ignore
            vault_addr = os.getenv('VAULT_ADDR')
            vault_token = os.getenv('VAULT_TOKEN')
            vault_path = os.getenv('VAULT_SECRET_PATH', 'secret/algoagent')
            
            if not vault_addr or not vault_token:
                logger.warning("VAULT_ADDR or VAULT_TOKEN not set")
                return
            
            client = hvac.Client(url=vault_addr, token=vault_token)
            
            for key_id in self.keys.keys():
                try:
                    secret_response = client.secrets.kv.read_secret_version(
                        path=f"{vault_path}/{key_id}"
                    )
                    secret = secret_response['data']['data'].get('value')
                    if secret:
                        self.key_secrets[key_id] = secret
                        logger.debug(f"Loaded secret for {key_id} from Vault")
                except Exception as e:
                    logger.warning(f"Failed to load {key_id} from Vault: {e}")
        
        except ImportError:
            logger.warning("hvac not installed - cannot load from Vault")
    
    def _load_from_aws(self):
        """Load secrets from AWS Secrets Manager"""
        try:
            import boto3  # type: ignore
            region = os.getenv('AWS_REGION', 'us-east-1')
            prefix = os.getenv('AWS_SECRET_PREFIX', 'algoagent/')
            
            client = boto3.client('secretsmanager', region_name=region)
            
            for key_id in self.keys.keys():
                try:
                    secret_name = f"{prefix}{key_id}"
                    response = client.get_secret_value(SecretId=secret_name)
                    secret = response.get('SecretString')
                    if secret:
                        self.key_secrets[key_id] = secret
                        logger.debug(f"Loaded secret for {key_id} from AWS")
                except Exception as e:
                    logger.warning(f"Failed to load {key_id} from AWS: {e}")
        
        except ImportError:
            logger.warning("boto3 not installed - cannot load from AWS")
    
    def _load_from_azure(self):
        """Load secrets from Azure Key Vault"""
        try:
            from azure.identity import DefaultAzureCredential  # type: ignore
            from azure.keyvault.secrets import SecretClient  # type: ignore
            
            vault_url = os.getenv('AZURE_VAULT_URL')
            if not vault_url:
                logger.warning("AZURE_VAULT_URL not set")
                return
            
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=vault_url, credential=credential)
            
            for key_id in self.keys.keys():
                try:
                    secret = client.get_secret(key_id).value
                    if secret:
                        self.key_secrets[key_id] = secret
                        logger.debug(f"Loaded secret for {key_id} from Azure")
                except Exception as e:
                    logger.warning(f"Failed to load {key_id} from Azure: {e}")
        
        except ImportError:
            logger.warning("azure-identity/azure-keyvault not installed - cannot load from Azure")
    
    def select_key(
        self,
        model_preference: Optional[str] = None,
        tokens_needed: int = 1000,
        exclude_keys: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Select an API key with available capacity (thread-safe).
        
        Selection algorithm:
        1. Get all available keys (not in cooldown, not excluded)
        2. Use round-robin to ensure load balancing
        3. Check capacity if Redis is enabled
        4. Return first suitable key
        
        Args:
            model_preference: Preferred model (e.g., "gemini-2.5-flash")
            tokens_needed: Estimated tokens required
            exclude_keys: List of key_ids to exclude (already tried)
            
        Returns:
            {
                'key_id': str,
                'secret': str,
                'model': str,
                'provider': str
            }
            or None if no suitable key found
        """
        with self._lock:
            exclude_keys = exclude_keys or []
            
            # Get all available candidates
            candidates = []
            for key_id, metadata in self.keys.items():
                if key_id in exclude_keys:
                    continue
                if not metadata.active:
                    continue
                
                # Check cooldown
                with self._health_lock:
                    health = self.key_health.get(key_id, {})
                    cooldown_until = health.get('cooldown_until')
                    if cooldown_until and datetime.fromisoformat(cooldown_until) > datetime.utcnow():
                        logger.debug(f"Key {key_id} is in cooldown")
                        continue
                
                candidates.append((key_id, metadata))
            
            if not candidates:
                logger.error(f"No keys available (all in cooldown or excluded)")
                return None
            
            # Sort by priority for round-robin
            candidates.sort(key=lambda x: (x[1].priority or 999, x[0]))
            
            # Use round-robin to select next key
            start_index = self.current_index % len(candidates)
            
            # Try each candidate starting from current index
            for i in range(len(candidates)):
                idx = (start_index + i) % len(candidates)
                key_id, metadata = candidates[idx]
                
                # Check capacity if Redis is enabled
                if self.enabled and self.redis_limiter:
                    if not self._check_capacity(key_id, metadata, tokens_needed):
                        continue
                
                # Get secret
                secret = self.key_secrets.get(key_id)
                if not secret:
                    logger.warning(f"No secret found for key {key_id}")
                    continue
                
                # Update usage
                self._update_usage(key_id)
                
                # Move to next key for next request
                self.current_index = (idx + 1) % len(candidates)
                
                logger.debug(f"Selected key {key_id} (round-robin index: {idx})")
                
                return {
                    'key_id': key_id,
                    'secret': secret,
                    'model': model_preference or metadata.model_name,
                    'provider': metadata.provider
                }
            
            # No suitable keys found
            logger.error(f"No keys available with sufficient capacity (checked {len(candidates)} candidates)")
            return None
    
    def _rotate_key_queue(self, model: str, used_key_id: str):
        """Rotate the key queue to move the used key to the end.
        
        This ensures round-robin distribution and prevents consecutive reuse.
        
        Args:
            model: Model name for the queue
            used_key_id: Key ID that was just used
        """
        queue = self.key_rotation_queues.get(model)
        if not queue:
            return
        
        # If used key is at front of queue, rotate it to back
        if queue and queue[0] == used_key_id:
            queue.append(queue.pop(0))
            logger.debug(f"Rotated {model} queue: {used_key_id} moved to end")
        # If used key is elsewhere in queue, move it to back
        elif used_key_id in queue:
            queue.remove(used_key_id)
            queue.append(used_key_id)
            logger.debug(f"Rotated {model} queue: {used_key_id} moved to end")
    
    def _check_capacity(self, key_id: str, metadata: APIKeyMetadata, tokens: int) -> bool:
        """Check if key has available RPM/TPM capacity"""
        if not self.redis_limiter:
            return True
        
        try:
            # Check RPM
            rpm_key = f"rpm:{key_id}"
            window = str(int(time.time()) // 60)
            rpm_key_with_window = f"{rpm_key}:{window}"
            
            current_rpm = int(self.redis_limiter.get(rpm_key_with_window) or 0)
            if current_rpm >= metadata.rpm:
                logger.debug(f"Key {key_id} at RPM limit ({current_rpm}/{metadata.rpm})")
                return False
            
            # Check TPM
            tpm_key = f"tpm:{key_id}"
            current_tpm = int(self.redis_limiter.get(tpm_key) or 0)
            if current_tpm + tokens > metadata.tpm:
                logger.debug(f"Key {key_id} would exceed TPM ({current_tpm + tokens}/{metadata.tpm})")
                return False
            
            return True
        
        except Exception as e:
            logger.warning(f"Error checking capacity for {key_id}: {e}")
            # Fail open
            return True
    
    def _update_usage(self, key_id: str):
        """Update usage tracking for a key"""
        if key_id not in self.key_health:
            self.key_health[key_id] = {
                'last_used': None,
                'error_count': 0,
                'cooldown_until': None,
                'success_count': 0
            }
        
        self.key_health[key_id]['last_used'] = datetime.utcnow().isoformat()
        self.key_health[key_id]['success_count'] = self.key_health[key_id].get('success_count', 0) + 1
        
        if self.redis_limiter and self.enabled:
            # Increment counters
            rpm_key = f"rpm:{key_id}:{int(time.time()) // 60}"
            self.redis_limiter.incr(rpm_key)
            self.redis_limiter.expire(rpm_key, 60)
    
    def report_error(self, key_id: str, error_type: str = 'generic'):
        """
        Report an error for a key and implement immediate cooldown (thread-safe).
        
        Args:
            key_id: Key that had the error
            error_type: Type of error (rate_limit, auth, network, etc.)
        """
        with self._health_lock:
            if key_id not in self.key_health:
                self.key_health[key_id] = {
                    'last_used': None,
                    'error_count': 0,
                    'cooldown_until': None,
                    'success_count': 0
                }
            
            error_count = self.key_health[key_id].get('error_count', 0) + 1
            self.key_health[key_id]['error_count'] = error_count
            
            # Immediate cooldown on first error (for rate limits especially)
            cooldown_until = datetime.utcnow() + timedelta(seconds=self.cooldown_duration)
            self.key_health[key_id]['cooldown_until'] = cooldown_until.isoformat()
            
            logger.warning(
                f"Key {key_id} entered {self.cooldown_duration}s cooldown after {error_type} error "
                f"(total errors: {error_count})"
            )
    
    def report_success(self, key_id: str):
        """
        Report successful API call for a key (resets error count).
        
        Args:
            key_id: Key that succeeded
        """
        with self._health_lock:
            if key_id in self.key_health:
                self.key_health[key_id]['error_count'] = 0
                self.key_health[key_id]['success_count'] = self.key_health[key_id].get('success_count', 0) + 1
                logger.debug(f"Key {key_id} reported success (total: {self.key_health[key_id]['success_count']})")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all keys"""
        status = {}
        for key_id, metadata in self.keys.items():
            health = self.key_health.get(key_id, {})
            status[key_id] = {
                'model': metadata.model_name,
                'active': metadata.active,
                'last_used': health.get('last_used'),
                'success_count': health.get('success_count', 0),
                'error_count': health.get('error_count', 0),
                'in_cooldown': bool(health.get('cooldown_until')),
                'cooldown_until': health.get('cooldown_until')
            }
        return status
    
    def save_keys(self, path: Optional[Path] = None):
        """Save key metadata to file"""
        path = path or self.key_store_path
        data = {
            'keys': [metadata.to_dict() for metadata in self.keys.values()]
        }
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved key metadata to {path}")


# Global instance
_key_manager = None


def get_key_manager() -> KeyManager:
    """Get or create global KeyManager instance"""
    global _key_manager
    if _key_manager is None:
        _key_manager = KeyManager()
    return _key_manager


def select_api_key(
    model_preference: Optional[str] = None,
    tokens_needed: int = 1000
) -> Optional[str]:
    """
    Convenience function to select and return just the API key secret.
    
    Args:
        model_preference: Preferred model name
        tokens_needed: Estimated tokens for this request
        
    Returns:
        API key string or None
    """
    manager = get_key_manager()
    key_info = manager.select_key(
        model_preference=model_preference,
        tokens_needed=tokens_needed
    )
    return key_info['secret'] if key_info else None
