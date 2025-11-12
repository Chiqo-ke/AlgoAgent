"""
APIKey model for storing key metadata.

Actual secrets are stored in external secret manager (Vault/AWS Secrets Manager).
This model only stores configuration and capacity information.
"""
from typing import Dict, Any
import json
from datetime import datetime


class APIKey:
    """
    API Key metadata model.
    
    For Django integration, this would be a Django model.
    For standalone use, this is a simple dataclass-like structure.
    """
    
    def __init__(
        self,
        key_id: str,
        model_name: str,
        provider: str,
        rpm: int,
        tpm: int,
        rpd: int = None,
        active: bool = True,
        tags: Dict[str, Any] = None,
        created_at: datetime = None,
        updated_at: datetime = None
    ):
        """
        Initialize API key metadata.
        
        Args:
            key_id: Unique identifier for this key (internal use)
            model_name: Model this key is for (e.g., "gemini-2.5-flash")
            provider: Provider name (e.g., "gemini", "openai")
            rpm: Requests per minute capacity
            tpm: Tokens per minute capacity
            rpd: Requests per day capacity (optional)
            active: Whether this key is currently active
            tags: Additional metadata (e.g., {"role": "flash_pool"})
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self.key_id = key_id
        self.model_name = model_name
        self.provider = provider
        self.rpm = rpm
        self.tpm = tpm
        self.rpd = rpd
        self.active = active
        self.tags = tags or {}
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'key_id': self.key_id,
            'model_name': self.model_name,
            'provider': self.provider,
            'rpm': self.rpm,
            'tpm': self.tpm,
            'rpd': self.rpd,
            'active': self.active,
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'APIKey':
        """Create APIKey from dictionary."""
        data = data.copy()
        if isinstance(data.get('created_at'), str):
            # Handle ISO format with 'Z' suffix
            date_str = data['created_at'].replace('Z', '+00:00')
            data['created_at'] = datetime.fromisoformat(date_str)
        if isinstance(data.get('updated_at'), str):
            # Handle ISO format with 'Z' suffix
            date_str = data['updated_at'].replace('Z', '+00:00')
            data['updated_at'] = datetime.fromisoformat(date_str)
        return cls(**data)
    
    def __str__(self):
        return f"{self.key_id} ({self.model_name})"
    
    def __repr__(self):
        return f"APIKey(key_id='{self.key_id}', model='{self.model_name}', rpm={self.rpm}, tpm={self.tpm})"


# For Django integration, uncomment and use this version:
"""
from django.db import models
from django.contrib.auth import get_user_model

class APIKey(models.Model):
    '''API Key metadata - secrets stored in external vault.'''
    
    key_id = models.CharField(max_length=128, unique=True, db_index=True)
    model_name = models.CharField(max_length=64, db_index=True)
    provider = models.CharField(max_length=64, default='gemini')
    rpm = models.IntegerField(help_text="Requests per minute capacity")
    tpm = models.IntegerField(help_text="Tokens per minute capacity")
    rpd = models.IntegerField(null=True, blank=True, help_text="Requests per day capacity (optional)")
    active = models.BooleanField(default=True, db_index=True)
    tags = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['active', 'model_name']),
            models.Index(fields=['provider', 'active']),
        ]
    
    def __str__(self):
        return f"{self.key_id} ({self.model_name})"
"""
