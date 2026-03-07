"""
Test Fixtures and Mocks for GitHub Copilot Integration

Provides mock responses for:
- OAuth token authentication
- Chat completion API calls
- Error scenarios
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any


# Mock OAuth Token Response
MOCK_TOKEN_RESPONSE = {
    "access_token": "ghu_test_mock_access_token_1234567890abcdef",
    "refresh_token": "ghr_test_mock_refresh_token_0987654321fedcba",
    "expires_in": 28800,  # 8 hours
    "token_type": "bearer",
    "scope": "read:user"
}


# Mock Device Code Response
MOCK_DEVICE_CODE_RESPONSE = {
    "device_code": "test_device_code_1234567890",
    "user_code": "TEST-CODE",
    "verification_uri": "https://github.com/login/device",
    "expires_in": 900,
    "interval": 5
}


# Mock Strategy Generation Response
MOCK_STRATEGY_GENERATION_RESPONSE = {
    "id": "chatcmpl-test123456",
    "object": "chat.completion",
    "created": 1705776000,
    "model": "gpt-4o",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": """```python
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from Backtest.simbroker import SimBroker

def run_strategy():
    '''Simple moving average crossover strategy'''
    broker = SimBroker(
        symbol='AAPL',
        timeframe='1d',
        period='1y',
        initial_balance=10000,
        commission=0.001
    )
    
    # Get data
    data = broker.get_data()
    
    # Calculate indicators
    data['SMA_20'] = data['Close'].rolling(window=20).mean()
    data['SMA_50'] = data['Close'].rolling(window=50).mean()
    
    # Trading logic
    for i in range(50, len(data)):
        if data['SMA_20'].iloc[i] > data['SMA_50'].iloc[i] and data['SMA_20'].iloc[i-1] <= data['SMA_50'].iloc[i-1]:
            broker.buy(data.index[i], data['Close'].iloc[i], shares=10)
        elif data['SMA_20'].iloc[i] < data['SMA_50'].iloc[i] and data['SMA_20'].iloc[i-1] >= data['SMA_50'].iloc[i-1]:
            broker.sell(data.index[i], data['Close'].iloc[i], shares=10)
    
    # Get results
    results = broker.get_results()
    broker.print_summary()
    
    return results

if __name__ == '__main__':
    run_strategy()
```"""
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 450,
        "completion_tokens": 320,
        "total_tokens": 770
    }
}


# Mock Error Fix Response
MOCK_ERROR_FIX_RESPONSE = {
    "id": "chatcmpl-test789012",
    "object": "chat.completion",
    "created": 1705776100,
    "model": "gpt-4o",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": """```python
# Fixed version with proper error handling
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from Backtest.simbroker import SimBroker

def run_strategy():
    '''Fixed simple moving average crossover strategy'''
    try:
        broker = SimBroker(
            symbol='AAPL',
            timeframe='1d',
            period='1y',
            initial_balance=10000,
            commission=0.001
        )
        
        data = broker.get_data()
        
        # Ensure sufficient data
        if len(data) < 50:
            print("Insufficient data for strategy")
            return None
        
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        
        for i in range(50, len(data)):
            if data['SMA_20'].iloc[i] > data['SMA_50'].iloc[i] and data['SMA_20'].iloc[i-1] <= data['SMA_50'].iloc[i-1]:
                broker.buy(data.index[i], data['Close'].iloc[i], shares=10)
            elif data['SMA_20'].iloc[i] < data['SMA_50'].iloc[i] and data['SMA_20'].iloc[i-1] >= data['SMA_50'].iloc[i-1]:
                broker.sell(data.index[i], data['Close'].iloc[i], shares=10)
        
        results = broker.get_results()
        broker.print_summary()
        
        return results
        
    except Exception as e:
        print(f"Strategy execution error: {e}")
        return None

if __name__ == '__main__':
    run_strategy()
```"""
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 520,
        "completion_tokens": 380,
        "total_tokens": 900
    }
}


# Mock Error Responses
MOCK_401_RESPONSE = {
    "error": {
        "message": "Invalid authentication credentials",
        "type": "invalid_request_error",
        "code": "invalid_api_key"
    }
}

MOCK_429_RESPONSE = {
    "error": {
        "message": "Rate limit exceeded",
        "type": "rate_limit_error",
        "code": "rate_limit_exceeded"
    }
}


class MockCopilotResponse:
    """Mock requests.Response object for testing"""
    
    def __init__(self, json_data: Dict[str, Any], status_code: int = 200):
        self.json_data = json_data
        self.status_code = status_code
        self.text = json.dumps(json_data)
        self.ok = 200 <= status_code < 300
    
    def json(self):
        return self.json_data
    
    def raise_for_status(self):
        if not self.ok:
            from requests.exceptions import HTTPError
            raise HTTPError(f"HTTP {self.status_code}")


def get_mock_token_data():
    """Get mock token data for database storage"""
    return {
        "access_token": MOCK_TOKEN_RESPONSE["access_token"],
        "refresh_token": MOCK_TOKEN_RESPONSE["refresh_token"],
        "expires_at": datetime.now() + timedelta(seconds=MOCK_TOKEN_RESPONSE["expires_in"]),
        "obtained_at": datetime.now()
    }


def mock_copilot_api_call(prompt: str, error_type: str = None) -> MockCopilotResponse:
    """
    Generate mock Copilot API response
    
    Args:
        prompt: Request prompt (to determine response type)
        error_type: Optional error to simulate ('401', '429', etc.)
    
    Returns:
        MockCopilotResponse object
    """
    if error_type == '401':
        return MockCopilotResponse(MOCK_401_RESPONSE, 401)
    elif error_type == '429':
        return MockCopilotResponse(MOCK_429_RESPONSE, 429)
    elif 'fix' in prompt.lower() or 'error' in prompt.lower():
        return MockCopilotResponse(MOCK_ERROR_FIX_RESPONSE)
    else:
        return MockCopilotResponse(MOCK_STRATEGY_GENERATION_RESPONSE)


def mock_device_flow_auth():
    """Mock complete device flow authentication"""
    return {
        "device_code_response": MOCK_DEVICE_CODE_RESPONSE,
        "token_response": MOCK_TOKEN_RESPONSE
    }
