"""
Test Key Rotation Integration

Tests the key rotation system with mock keys and various failure scenarios.
"""

import os
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from Backtest.key_rotation import (
    APIKeyMetadata, KeyManager, KeyRotationError,
    get_key_manager
)


class TestAPIKeyMetadata:
    """Test API key metadata"""
    
    def test_metadata_creation(self):
        """Test creating key metadata"""
        meta = APIKeyMetadata(
            key_id='test_key',
            model_name='gemini-2.5-flash',
            provider='gemini',
            rpm=60,
            tpm=1000000
        )
        
        assert meta.key_id == 'test_key'
        assert meta.model_name == 'gemini-2.5-flash'
        assert meta.rpm == 60
        assert meta.tpm == 1000000
        assert meta.active is True
    
    def test_metadata_to_dict(self):
        """Test metadata serialization"""
        meta = APIKeyMetadata(
            key_id='test_key',
            model_name='gemini-2.5-flash',
            provider='gemini',
            rpm=60,
            tpm=1000000,
            tags={'test': True}
        )
        
        data = meta.to_dict()
        assert data['key_id'] == 'test_key'
        assert data['tags'] == {'test': True}
    
    def test_metadata_from_dict(self):
        """Test metadata deserialization"""
        data = {
            'key_id': 'test_key',
            'model_name': 'gemini-2.5-flash',
            'provider': 'gemini',
            'rpm': 60,
            'tpm': 1000000,
            'tags': {'test': True}
        }
        
        meta = APIKeyMetadata.from_dict(data)
        assert meta.key_id == 'test_key'
        assert meta.tags == {'test': True}


class TestKeyManager:
    """Test KeyManager functionality"""
    
    def test_single_key_from_env(self, monkeypatch):
        """Test loading single key from environment"""
        monkeypatch.setenv('GEMINI_API_KEY', 'test-key-123')
        monkeypatch.setenv('ENABLE_KEY_ROTATION', 'false')
        
        manager = KeyManager()
        key_info = manager.select_key()
        
        assert key_info is not None
        assert key_info['key_id'] == 'default'
        assert key_info['secret'] == 'test-key-123'
    
    def test_key_manager_init_single_key(self, monkeypatch):
        """Test initialization with single key"""
        monkeypatch.setenv('GEMINI_API_KEY', 'sk-test-123')
        monkeypatch.setenv('ENABLE_KEY_ROTATION', 'false')
        
        manager = KeyManager()
        
        assert not manager.enabled
        assert 'default' in manager.key_secrets
        assert manager.key_secrets['default'] == 'sk-test-123'
    
    def test_key_selection_with_model_preference(self, monkeypatch, tmp_path):
        """Test key selection with model preference"""
        monkeypatch.setenv('ENABLE_KEY_ROTATION', 'false')
        
        # Create test keys.json
        keys_file = tmp_path / 'keys.json'
        keys_data = {
            'keys': [
                {
                    'key_id': 'flash_01',
                    'model_name': 'gemini-2.5-flash',
                    'provider': 'gemini',
                    'rpm': 60,
                    'tpm': 1000000,
                    'active': True
                },
                {
                    'key_id': 'pro_01',
                    'model_name': 'gemini-2.5-pro',
                    'provider': 'gemini',
                    'rpm': 10,
                    'tpm': 4000000,
                    'active': True
                }
            ]
        }
        keys_file.write_text(json.dumps(keys_data))
        
        # Set up environment
        monkeypatch.setenv('GEMINI_KEY_flash_01', 'key-flash')
        monkeypatch.setenv('GEMINI_KEY_pro_01', 'key-pro')
        
        # Create manager
        manager = KeyManager(key_store_path=keys_file)
        
        # Select flash key
        key_info = manager.select_key(model_preference='gemini-2.5-flash')
        assert key_info is not None
        assert key_info['key_id'] == 'flash_01'
        assert key_info['model'] == 'gemini-2.5-flash'
    
    def test_exclude_keys(self, monkeypatch):
        """Test excluding keys from selection"""
        monkeypatch.setenv('ENABLE_KEY_ROTATION', 'false')
        monkeypatch.setenv('GEMINI_API_KEY', 'default-key')
        
        manager = KeyManager()
        
        # Exclude default key
        key_info = manager.select_key(exclude_keys=['default'])
        assert key_info is None
    
    def test_health_tracking(self, monkeypatch):
        """Test key health tracking"""
        monkeypatch.setenv('GEMINI_API_KEY', 'test-key')
        monkeypatch.setenv('ENABLE_KEY_ROTATION', 'false')
        
        manager = KeyManager()
        manager.select_key()
        
        health = manager.get_health_status()
        assert 'default' in health
        assert health['default']['success_count'] == 1
        assert health['default']['error_count'] == 0
    
    def test_error_reporting(self, monkeypatch):
        """Test error reporting and cooldown"""
        monkeypatch.setenv('GEMINI_API_KEY', 'test-key')
        monkeypatch.setenv('ENABLE_KEY_ROTATION', 'false')
        
        manager = KeyManager()
        
        # Report errors
        manager.report_error('default', error_type='api_error')
        manager.report_error('default', error_type='api_error')
        manager.report_error('default', error_type='api_error')
        
        health = manager.get_health_status()
        assert health['default']['error_count'] == 3
        assert health['default']['in_cooldown'] is True
    
    def test_key_not_available_during_cooldown(self, monkeypatch):
        """Test that key is skipped during cooldown"""
        monkeypatch.setenv('GEMINI_API_KEY', 'test-key')
        monkeypatch.setenv('ENABLE_KEY_ROTATION', 'false')
        
        manager = KeyManager()
        
        # Put key in cooldown
        manager.report_error('default')
        manager.report_error('default')
        manager.report_error('default')
        
        # Try to select key
        key_info = manager.select_key()
        assert key_info is None
    
    def test_load_from_keys_file(self, monkeypatch, tmp_path):
        """Test loading keys from keys.json"""
        keys_file = tmp_path / 'keys.json'
        keys_data = {
            'keys': [
                {
                    'key_id': 'flash_01',
                    'model_name': 'gemini-2.5-flash',
                    'provider': 'gemini',
                    'rpm': 60,
                    'tpm': 1000000,
                    'active': True,
                    'created_at': '2024-01-01T00:00:00',
                    'updated_at': '2024-01-01T00:00:00'
                }
            ]
        }
        keys_file.write_text(json.dumps(keys_data))
        
        monkeypatch.setenv('ENABLE_KEY_ROTATION', 'false')
        monkeypatch.setenv('GEMINI_KEY_flash_01', 'test-secret')
        
        manager = KeyManager(key_store_path=keys_file)
        
        assert 'flash_01' in manager.keys
        assert 'flash_01' in manager.key_health
    
    def test_multi_key_distribution(self, monkeypatch, tmp_path):
        """Test load distribution across multiple keys"""
        keys_file = tmp_path / 'keys.json'
        keys_data = {
            'keys': [
                {
                    'key_id': f'key_{i}',
                    'model_name': 'gemini-2.5-flash',
                    'provider': 'gemini',
                    'rpm': 60,
                    'tpm': 1000000,
                    'active': True
                }
                for i in range(3)
            ]
        }
        keys_file.write_text(json.dumps(keys_data))
        
        monkeypatch.setenv('ENABLE_KEY_ROTATION', 'false')
        for i in range(3):
            monkeypatch.setenv(f'GEMINI_KEY_key_{i}', f'secret_{i}')
        
        manager = KeyManager(key_store_path=keys_file)
        
        # Select multiple times and verify distribution
        selected = set()
        for _ in range(10):
            key_info = manager.select_key()
            if key_info:
                selected.add(key_info['key_id'])
        
        # Should use multiple keys (stochastic)
        assert len(selected) > 1


class TestGeminiStrategyGeneratorIntegration:
    """Test GeminiStrategyGenerator with key rotation"""
    
    def test_generator_without_rotation(self, monkeypatch):
        """Test generator in single-key mode"""
        monkeypatch.setenv('GEMINI_API_KEY', 'test-key-123')
        monkeypatch.setenv('ENABLE_KEY_ROTATION', 'false')
        
        from Backtest.gemini_strategy_generator import GeminiStrategyGenerator
        
        # Should not raise error on init
        try:
            generator = GeminiStrategyGenerator()
            assert not generator.use_key_rotation
            assert generator.selected_key_id == 'default'
        except ImportError:
            # google-generativeai not installed, skip
            pytest.skip("google-generativeai not installed")
    
    def test_generator_with_rotation_disabled(self, monkeypatch):
        """Test generator when rotation is disabled"""
        monkeypatch.setenv('GEMINI_API_KEY', 'test-key')
        monkeypatch.setenv('ENABLE_KEY_ROTATION', 'false')
        
        from Backtest.gemini_strategy_generator import GeminiStrategyGenerator
        
        try:
            generator = GeminiStrategyGenerator(use_key_rotation=False)
            assert not generator.use_key_rotation
        except ImportError:
            pytest.skip("google-generativeai not installed")


# Fixtures for pytest


@pytest.fixture
def clean_env(monkeypatch):
    """Clean environment for tests"""
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    monkeypatch.delenv('ENABLE_KEY_ROTATION', raising=False)
    monkeypatch.delenv('REDIS_URL', raising=False)
    return monkeypatch


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
