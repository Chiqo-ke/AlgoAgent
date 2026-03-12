"""
Simple unit tests for Copilot authentication (no Django required)
"""

from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))
sys.path.insert(0, str(current_dir.parent.parent))

from fixtures.copilot_responses import (
    MOCK_TOKEN_RESPONSE,
    MOCK_DEVICE_CODE_RESPONSE,
    MockCopilotResponse
)


def test_auth_manager_import():
    """Test that CopilotAuthManager can be imported"""
    from algoagent_api.copilot_auth import CopilotAuthManager
    assert CopilotAuthManager is not None


@patch('algoagent_api.copilot_auth.requests.post')
def test_initiate_device_flow(mock_post):
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
    print("✓ Device flow initiation test passed")


@patch('algoagent_api.copilot_auth.requests.post')
def test_poll_for_token_success(mock_post):
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
    print("✓ Token polling test passed")


def test_token_validation():
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
    print("✓ Token validation test passed")


if __name__ == '__main__':
    test_auth_manager_import()
    test_initiate_device_flow()
    test_poll_for_token_success()
    test_token_validation()
    print("\n✅ All authentication tests passed!")
