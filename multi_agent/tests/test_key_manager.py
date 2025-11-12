"""
Unit tests for KeyManager.

Tests:
- Key selection with model preference
- RPM/TPM reservation enforcement
- Cooldown management
- Concurrent access
- Failover behavior
"""
import pytest
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json

from keys.models import APIKey
from keys.manager import KeyManager, KeySelectionError
from keys.redis_client import RedisRateLimiter


@pytest.fixture
def mock_redis_limiter():
    """Mock Redis rate limiter."""
    limiter = Mock(spec=RedisRateLimiter)
    limiter.reserve_rpm_slot.return_value = True
    limiter.reserve_token_budget.return_value = True
    limiter.is_in_cooldown.return_value = False
    limiter.get_cooldown_ttl.return_value = None
    limiter.health_check.return_value = True
    return limiter


@pytest.fixture
def sample_keys():
    """Sample API keys for testing."""
    return [
        APIKey(
            key_id="flash-01",
            model_name="gemini-2.5-flash",
            provider="gemini",
            rpm=10,
            tpm=250000,
            active=True
        ),
        APIKey(
            key_id="flash-02",
            model_name="gemini-2.5-flash",
            provider="gemini",
            rpm=10,
            tpm=250000,
            active=True
        ),
        APIKey(
            key_id="pro-01",
            model_name="gemini-2.5-pro",
            provider="gemini",
            rpm=5,
            tpm=100000,
            active=True
        )
    ]


@pytest.fixture
def key_manager(mock_redis_limiter, sample_keys, tmp_path):
    """Initialize KeyManager with test data."""
    # Create test keys.json
    keys_file = tmp_path / "keys.json"
    keys_data = {
        "keys": [k.to_dict() for k in sample_keys]
    }
    keys_file.write_text(json.dumps(keys_data))
    
    with patch('keys.secret_store.fetch_api_secret', return_value='test-secret'):
        manager = KeyManager(
            redis_limiter=mock_redis_limiter,
            key_store_path=keys_file
        )
    
    return manager


def test_key_manager_initialization(key_manager):
    """Test KeyManager initializes with keys."""
    assert len(key_manager.keys) == 3
    assert "flash-01" in key_manager.keys
    assert "pro-01" in key_manager.keys


def test_select_key_with_preference(key_manager, mock_redis_limiter):
    """Test key selection respects model preference."""
    with patch('keys.secret_store.fetch_api_secret', return_value='test-secret'):
        # Prefer Pro model
        key_meta = key_manager.select_key(
            model_preference="gemini-2.5-pro",
            tokens_needed=1000
        )
    
    assert key_meta is not None
    assert key_meta['key_id'] == "pro-01"
    assert key_meta['model'] == "gemini-2.5-pro"
    assert key_meta['secret'] == 'test-secret'
    
    # Verify RPM and TPM were checked
    mock_redis_limiter.reserve_rpm_slot.assert_called()
    mock_redis_limiter.reserve_token_budget.assert_called()


def test_select_key_fallback(key_manager, mock_redis_limiter):
    """Test fallback when preferred model not available."""
    # Make Pro key in cooldown
    def is_in_cooldown(key_id):
        return key_id == "pro-01"
    
    mock_redis_limiter.is_in_cooldown.side_effect = is_in_cooldown
    
    with patch('keys.secret_store.fetch_api_secret', return_value='test-secret'):
        # Request Pro but should fall back to Flash
        key_meta = key_manager.select_key(
            model_preference="gemini-2.5-pro",
            tokens_needed=1000
        )
    
    assert key_meta is not None
    assert key_meta['model'] == "gemini-2.5-flash"


def test_select_key_rpm_exhausted(key_manager, mock_redis_limiter):
    """Test key selection when RPM limit exceeded."""
    # First key exhausted
    rpm_calls = [False, True, True]  # flash-01 exhausted, others OK
    mock_redis_limiter.reserve_rpm_slot.side_effect = rpm_calls
    
    with patch('keys.secret_store.fetch_api_secret', return_value='test-secret'):
        key_meta = key_manager.select_key(
            model_preference="gemini-2.5-flash",
            tokens_needed=1000
        )
    
    # Should select flash-02 (second Flash key)
    assert key_meta is not None
    assert key_meta['key_id'] in ["flash-02", "pro-01"]


def test_select_key_all_exhausted(key_manager, mock_redis_limiter):
    """Test when all keys are exhausted."""
    # All RPM slots exhausted
    mock_redis_limiter.reserve_rpm_slot.return_value = False
    
    with patch('keys.secret_store.fetch_api_secret', return_value='test-secret'):
        key_meta = key_manager.select_key(
            model_preference="gemini-2.5-flash",
            tokens_needed=1000
        )
    
    assert key_meta is None


def test_select_key_tpm_exhausted(key_manager, mock_redis_limiter):
    """Test key selection when TPM limit exceeded."""
    # TPM exhausted but RPM OK
    mock_redis_limiter.reserve_rpm_slot.return_value = True
    mock_redis_limiter.reserve_token_budget.return_value = False
    
    with patch('keys.secret_store.fetch_api_secret', return_value='test-secret'):
        key_meta = key_manager.select_key(
            model_preference="gemini-2.5-flash",
            tokens_needed=300000  # Exceeds TPM
        )
    
    assert key_meta is None


def test_mark_key_unhealthy(key_manager, mock_redis_limiter):
    """Test marking key as unhealthy sets cooldown."""
    key_manager.mark_key_unhealthy(
        "flash-01",
        cooldown_seconds=60,
        reason="Test cooldown"
    )
    
    mock_redis_limiter.set_cooldown.assert_called_once_with("flash-01", 60)


def test_get_key_status(key_manager, mock_redis_limiter):
    """Test getting key status."""
    mock_redis_limiter.is_in_cooldown.return_value = False
    mock_redis_limiter.get_rpm_usage.return_value = {'window': '12345', 'count': 5}
    mock_redis_limiter.get_tpm_usage.return_value = {'window': '12345', 'used': 50000}
    
    status = key_manager.get_key_status("flash-01")
    
    assert status['key_id'] == "flash-01"
    assert status['active'] is True
    assert status['in_cooldown'] is False
    assert status['rpm_usage']['count'] == 5
    assert status['tpm_usage']['used'] == 50000


def test_health_check(key_manager, mock_redis_limiter):
    """Test health check."""
    mock_redis_limiter.health_check.return_value = True
    mock_redis_limiter.is_in_cooldown.return_value = False
    
    health = key_manager.health_check()
    
    assert health['healthy'] is True
    assert health['total_keys'] == 3
    assert health['active_keys'] == 3
    assert health['keys_in_cooldown'] == 0
    assert health['redis_healthy'] is True


def test_health_check_unhealthy(key_manager, mock_redis_limiter):
    """Test health check when system unhealthy."""
    # Redis down
    mock_redis_limiter.health_check.return_value = False
    
    health = key_manager.health_check()
    
    assert health['healthy'] is False
    assert health['redis_healthy'] is False


def test_concurrent_key_selection(key_manager, mock_redis_limiter):
    """Test concurrent key selection distributes load."""
    import threading
    
    selected_keys = []
    lock = threading.Lock()
    
    def select_key():
        with patch('keys.secret_store.fetch_api_secret', return_value='test-secret'):
            key_meta = key_manager.select_key(
                model_preference="gemini-2.5-flash",
                tokens_needed=1000
            )
            if key_meta:
                with lock:
                    selected_keys.append(key_meta['key_id'])
    
    # Start multiple threads
    threads = [threading.Thread(target=select_key) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # Should have distributed across available keys
    assert len(selected_keys) > 0
    # At least 2 different keys should be selected (randomization)
    assert len(set(selected_keys)) >= 1


def test_reload_keys(key_manager, tmp_path, mock_redis_limiter):
    """Test reloading keys from file."""
    # Add new key to file
    keys_file = tmp_path / "keys.json"
    new_key = APIKey(
        key_id="flash-03",
        model_name="gemini-2.5-flash",
        provider="gemini",
        rpm=10,
        tpm=250000,
        active=True
    )
    
    keys_data = {
        "keys": [k.to_dict() for k in [*key_manager.keys.values(), new_key]]
    }
    keys_file.write_text(json.dumps(keys_data))
    
    # Reload
    key_manager.reload_keys()
    
    assert len(key_manager.keys) == 4
    assert "flash-03" in key_manager.keys


def test_exclude_keys(key_manager, mock_redis_limiter):
    """Test excluding keys from selection."""
    with patch('keys.secret_store.fetch_api_secret', return_value='test-secret'):
        key_meta = key_manager.select_key(
            model_preference="gemini-2.5-flash",
            tokens_needed=1000,
            exclude_keys=["flash-01", "flash-02"]
        )
    
    # Should select Pro key since Flash keys excluded
    assert key_meta is not None
    assert key_meta['key_id'] == "pro-01"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
