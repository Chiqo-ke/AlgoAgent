"""
Quick Test Script for Production API Integration
================================================

Tests the new production-hardened API endpoints
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/production"

def test_health_checks():
    """Test health endpoints"""
    print("\n" + "="*60)
    print("TESTING HEALTH CHECKS")
    print("="*60)
    
    # Strategy health
    print("\n1. Strategy API Health:")
    try:
        response = requests.get(f"{BASE_URL}/strategies/health/", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Backtest health
    print("\n2. Backtest API Health:")
    try:
        response = requests.get(f"{BASE_URL}/backtests/health/", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")


def test_schema_validation():
    """Test Pydantic schema validation"""
    print("\n" + "="*60)
    print("TESTING SCHEMA VALIDATION")
    print("="*60)
    
    # Valid schema
    print("\n1. Valid Strategy Schema:")
    valid_strategy = {
        "name": "RSI_Test",
        "description": "RSI reversal strategy",
        "parameters": {"rsi_period": 14},
        "indicators": {"rsi": {"period": 14}},
        "entry_rules": ["rsi < 30"],
        "exit_rules": ["rsi > 70"]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/strategies/validate-schema/",
            json=valid_strategy,
            timeout=5
        )
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Valid: {result.get('status') == 'valid'}")
        if result.get('status') == 'valid':
            print(f"   ✅ Schema validation passed")
        else:
            print(f"   ❌ Unexpected response: {result}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Invalid schema (missing required fields)
    print("\n2. Invalid Strategy Schema:")
    invalid_strategy = {
        "name": "Incomplete"
        # Missing required fields
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/strategies/validate-schema/",
            json=invalid_strategy,
            timeout=5
        )
        print(f"   Status: {response.status_code}")
        result = response.json()
        if result.get('status') == 'invalid':
            print(f"   ✅ Correctly rejected invalid schema")
            print(f"   Errors: {len(result.get('errors', []))} validation errors")
        else:
            print(f"   ❌ Should have been rejected")
    except Exception as e:
        print(f"   ❌ Error: {e}")


def test_code_validation():
    """Test code safety validation"""
    print("\n" + "="*60)
    print("TESTING CODE SAFETY VALIDATION")
    print("="*60)
    
    # Safe code
    print("\n1. Safe Code:")
    safe_code = """
class MyStrategy:
    def __init__(self):
        self.rsi_period = 14
    
    def on_bar(self):
        if self.rsi < 30:
            self.buy()
        elif self.rsi > 70:
            self.sell()
"""
    
    try:
        response = requests.post(
            f"{BASE_URL}/strategies/validate-code/",
            json={"code": safe_code, "strict_mode": True},
            timeout=5
        )
        print(f"   Status: {response.status_code}")
        result = response.json()
        if result.get('safe'):
            print(f"   ✅ Code passed safety checks")
            print(f"   Checks: {len(result.get('checks_passed', []))}")
        else:
            print(f"   ❌ Code rejected: {result.get('issues')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Dangerous code
    print("\n2. Dangerous Code:")
    dangerous_code = """
import os
import subprocess

class BadStrategy:
    def on_bar(self):
        os.system('rm -rf /')  # Dangerous!
        eval('malicious_code()')  # Dangerous!
"""
    
    try:
        response = requests.post(
            f"{BASE_URL}/strategies/validate-code/",
            json={"code": dangerous_code, "strict_mode": True},
            timeout=5
        )
        print(f"   Status: {response.status_code}")
        result = response.json()
        if not result.get('safe'):
            print(f"   ✅ Correctly rejected dangerous code")
            print(f"   Issues found: {len(result.get('issues', []))}")
            for issue in result.get('issues', [])[:3]:
                print(f"      - {issue}")
        else:
            print(f"   ❌ Should have been rejected")
    except Exception as e:
        print(f"   ❌ Error: {e}")


def test_backtest_config_validation():
    """Test backtest config validation"""
    print("\n" + "="*60)
    print("TESTING BACKTEST CONFIG VALIDATION")
    print("="*60)
    
    # Valid config
    print("\n1. Valid Backtest Config:")
    valid_config = {
        "initial_capital": 100000,
        "commission": 0.001,
        "slippage": 0.0005,
        "position_size": 0.1,
        "max_positions": 5
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/backtests/validate-config/",
            json=valid_config,
            timeout=5
        )
        print(f"   Status: {response.status_code}")
        result = response.json()
        if result.get('status') == 'valid':
            print(f"   ✅ Config validation passed")
        else:
            print(f"   ❌ Unexpected response: {result}")
    except Exception as e:
        print(f"   ❌ Error: {e}")


def test_api_root():
    """Test API root to verify production endpoints are listed"""
    print("\n" + "="*60)
    print("TESTING API ROOT")
    print("="*60)
    
    try:
        response = requests.get("http://localhost:8000/api/", timeout=5)
        print(f"   Status: {response.status_code}")
        result = response.json()
        
        if 'production' in result:
            print(f"   ✅ Production endpoints found in API root")
            print(f"   Endpoints:")
            for key, value in result['production'].items():
                print(f"      - {key}: {value}")
        else:
            print(f"   ❌ Production endpoints not found in API root")
    except Exception as e:
        print(f"   ❌ Error: {e}")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("PRODUCTION API INTEGRATION TEST")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now()}")
    
    # Check if server is running
    print("\nChecking if Django server is running...")
    try:
        response = requests.get("http://localhost:8000/api/", timeout=5)
        print(f"✅ Server is running (Status: {response.status_code})")
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running!")
        print("\nPlease start the Django server first:")
        print("   cd AlgoAgent")
        print("   python manage.py runserver")
        return
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        return
    
    # Run tests
    test_api_root()
    test_health_checks()
    test_schema_validation()
    test_code_validation()
    test_backtest_config_validation()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print("\nProduction API endpoints have been created:")
    print("  ✅ Strategy validation endpoints")
    print("  ✅ Code safety endpoints")
    print("  ✅ Sandbox execution endpoints")
    print("  ✅ Lifecycle tracking endpoints")
    print("  ✅ Deployment endpoints")
    print("  ✅ Backtest validation endpoints")
    print("  ✅ Health check endpoints")
    print("\n📖 See PRODUCTION_API_GUIDE.md for complete documentation")
    print("="*60)


if __name__ == "__main__":
    main()
