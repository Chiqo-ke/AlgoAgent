"""
Simple API Test for AlgoAgent Django Integration
===============================================

Basic test to verify API endpoints are accessible.
"""

import sys
import subprocess
import time

def test_api_simple():
    """Simple test using curl commands"""
    print("🧪 Testing AlgoAgent Django API Integration\n")
    
    # Test basic endpoints
    endpoints = [
        ("API Root", "/api/"),
        ("Data API Health", "/api/data/api/health/"),
        ("Strategy API Health", "/api/strategies/api/health/"),
        ("Backtest API Health", "/api/backtests/api/health/"),
        ("Data Symbols", "/api/data/symbols/"),
        ("Strategy List", "/api/strategies/strategies/"),
        ("Backtest Configs", "/api/backtests/configs/")
    ]
    
    base_url = "http://127.0.0.1:8000"
    
    for name, endpoint in endpoints:
        try:
            # Use python requests to test
            import requests
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: SUCCESS (200)")
            else:
                print(f"⚠️ {name}: HTTP {response.status_code}")
        except ImportError:
            print(f"📦 Installing requests package...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests'])
            import requests
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: SUCCESS (200)")
            else:
                print(f"⚠️ {name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: ERROR - {str(e)[:50]}...")
    
    print(f"\n🌐 API is running at: {base_url}")
    print(f"📚 Browse APIs at: {base_url}/api/data/ (for browsable API)")
    print(f"👤 Admin interface: {base_url}/admin/")

if __name__ == "__main__":
    test_api_simple()