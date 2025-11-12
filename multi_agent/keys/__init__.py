"""
Multi-key routing and rate limiting system.

This module provides:
- API key metadata storage and management
- Redis-backed atomic RPM/TPM enforcement
- Intelligent key selection with health tracking
- Cooldown management for rate-limited keys
"""

__version__ = "1.0.0"
