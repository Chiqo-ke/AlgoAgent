"""
Test GitHub Copilot Integration

Tests:
1. Authentication module
2. Strategy generator
3. API endpoints
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os
from pathlib import Path

# Django setup for tests - must be before importing Django models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoagent.settings')

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import test fixtures
from tests.fixtures.copilot_responses import (
    MOCK_TOKEN_RESPONSE,
    MOCK_DEVICE_CODE_RESPONSE,
    MOCK_STRATEGY_GENERATION_RESPONSE,
    MockCopilotResponse,
    get_mock_token_data
)


class TestCopilotAuth:
    """Test Copilot authentication module"""
    
    @patch('algoagent_api.copilot_auth.requests.post')
    def test_initiate_device_flow(self, mock_post):
        """Test device flow initiation"""
        from algoagent_api.copilot_auth import CopilotAuthManager
        
        # Mock response
        mock_post.return_value = MockCopilotResponse(MOCK_DEVICE_CODE_RESPONSE)
        
        # Initialize and test
        manager = CopilotAuthManager()
        device_data = manager.initiate_device_flow()
        
        assert device_data['user_code'] == 'TEST-CODE'
        assert device_data['device_code'] == 'test_device_code_1234567890'
        assert mock_post.called
    
    @patch('algoagent_api.copilot_auth.requests.post')
    def test_poll_for_token_success(self, mock_post):
        """Test successful token polling"""
        from algoagent_api.copilot_auth import CopilotAuthManager
        
        # Mock response
        mock_post.return_value = MockCopilotResponse(MOCK_TOKEN_RESPONSE)
        
        # Initialize and test
        manager = CopilotAuthManager()
        token_data = manager.poll_for_token(
            device_code='test_device_code',
            interval=1,
            timeout=5
        )
        
        assert token_data['access_token'] == MOCK_TOKEN_RESPONSE['access_token']
        assert token_data['refresh_token'] == MOCK_TOKEN_RESPONSE['refresh_token']
    
    def test_token_validation(self):
        """Test token validity checking"""
        from algoagent_api.copilot_auth import CopilotAuthManager
        
        manager = CopilotAuthManager()
        
        # Valid token
        valid_token = {
            'access_token': 'test_token',
            'expires_at': datetime.now() + timedelta(hours=2)
        }
        assert manager.is_token_valid(valid_token) is True
        
        # Expired token
        expired_token = {
            'access_token': 'test_token',
            'expires_at': datetime.now() - timedelta(hours=1)
        }
        assert manager.is_token_valid(expired_token) is False


class TestCopilotStrategyGenerator:
    """Test Copilot strategy generator"""
    
    @patch('Backtest.copilot_strategy_generator.requests.post')
    @patch('Backtest.copilot_strategy_generator.CopilotAuth')
    def test_generate_strategy_code(self, mock_auth_model, mock_post):
        """Test strategy code generation"""
        from Backtest.copilot_strategy_generator import CopilotStrategyGenerator
        
        # Mock authentication
        mock_auth_model.get_latest_token.return_value = get_mock_token_data()
        
        # Mock API response
        mock_post.return_value = MockCopilotResponse(MOCK_STRATEGY_GENERATION_RESPONSE)
        
        # Initialize and test
        generator = CopilotStrategyGenerator()
        code = generator.generate_strategy_code("Create a simple moving average strategy")
        
        assert code is not None
        assert 'SimBroker' in code
        assert 'def run_strategy' in code
        assert mock_post.called
    
    @patch('Backtest.copilot_strategy_generator.requests.post')
    @patch('Backtest.copilot_strategy_generator.CopilotAuth')
    def test_api_call_headers(self, mock_auth_model, mock_post):
        """Test API call includes correct headers"""
        from Backtest.copilot_strategy_generator import CopilotStrategyGenerator
        
        # Mock authentication
        mock_auth_model.get_latest_token.return_value = get_mock_token_data()
        
        # Mock API response
        mock_post.return_value = MockCopilotResponse(MOCK_STRATEGY_GENERATION_RESPONSE)
        
        # Initialize and test
        generator = CopilotStrategyGenerator()
        generator.generate_strategy_code("Test strategy")
        
        # Verify headers
        call_args = mock_post.call_args
        headers = call_args[1]['headers']
        
        assert 'Authorization' in headers
        assert headers['Authorization'].startswith('Bearer ')
        assert headers['User-Agent'] == 'AlgoAgent/2.0'
        assert headers['X-Initiator'] == 'user'


class TestCopilotIntegrationE2E:
    """End-to-end integration tests"""
    
    @patch('requests.post')
    @patch('strategy_api.models.CopilotAuth')
    def test_full_generation_flow(self, mock_auth_model, mock_post):
        """Test complete generation workflow"""
        from Backtest.copilot_strategy_generator import CopilotStrategyGenerator
        
        # Mock authentication
        mock_auth_model.get_latest_token.return_value = get_mock_token_data()
        
        # Mock API response
        mock_post.return_value = MockCopilotResponse(MOCK_STRATEGY_GENERATION_RESPONSE)
        
        # Initialize generator
        generator = CopilotStrategyGenerator()
        
        # Generate and save strategy
        file_path, execution_result = generator.generate_and_save(
            description="Create RSI momentum strategy",
            execute_after_generation=False
        )
        
        assert file_path is not None
        assert Path(file_path).exists()
        
        # Cleanup
        Path(file_path).unlink(missing_ok=True)


@pytest.mark.django_db
class TestCopilotDatabaseIntegration:
    """Test database integration"""
    
    def test_save_and_retrieve_token(self):
        """Test saving and retrieving Copilot tokens"""
        from strategy_api.models import CopilotAuth
        from datetime import datetime
        
        # Save token
        expires_at = datetime.now() + timedelta(hours=8)
        CopilotAuth.save_token(
            access_token='test_access_token',
            refresh_token='test_refresh_token',
            expires_at=expires_at,
            github_user='testuser',
            client_id='test_client_id'
        )
        
        # Retrieve token
        token_data = CopilotAuth.get_latest_token()
        
        assert token_data is not None
        assert token_data['access_token'] == 'test_access_token'
        assert token_data['refresh_token'] == 'test_refresh_token'
    
    def test_token_replacement(self):
        """Test that saving new token replaces old one"""
        from strategy_api.models import CopilotAuth
        from datetime import datetime
        
        # Save first token
        CopilotAuth.save_token(
            access_token='old_token',
            refresh_token='old_refresh',
            expires_at=datetime.now() + timedelta(hours=8)
        )
        
        # Save second token
        CopilotAuth.save_token(
            access_token='new_token',
            refresh_token='new_refresh',
            expires_at=datetime.now() + timedelta(hours=8)
        )
        
        # Should only have one token
        assert CopilotAuth.objects.count() == 1
        
        # Should be the new token
        token_data = CopilotAuth.get_latest_token()
        assert token_data['access_token'] == 'new_token'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
