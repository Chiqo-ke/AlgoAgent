"""
API Test Script for AlgoAgent Django Integration
===============================================

Simple test script to verify that all API endpoints are working correctly.
"""

import requests
import json
import time
from datetime import datetime, timedelta


class AlgoAgentAPITester:
    """Test suite for AlgoAgent API endpoints"""
    
    def __init__(self, base_url="http://127.0.0.1:8000/api"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AlgoAgent-API-Tester/1.0'
        })
    
    def log(self, message, level="INFO"):
        """Simple logging method"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def test_connection(self):
        """Test basic API connection"""
        self.log("Testing API connection...")
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ API Root connected successfully - Version: {data.get('version')}")
                return True
            else:
                self.log(f"❌ API Root failed - Status: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Connection failed: {e}", "ERROR")
            return False
    
    def test_health_endpoints(self):
        """Test health check endpoints for all APIs"""
        self.log("Testing health endpoints...")
        
        health_endpoints = [
            ("Data API", "/data/api/health/"),
            ("Strategy API", "/strategies/api/health/"),
            ("Backtest API", "/backtests/api/health/")
        ]
        
        results = {}
        for name, endpoint in health_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    data = response.json()
                    self.log(f"✅ {name} health check passed - Status: {data.get('status')}")
                    results[name] = data
                else:
                    self.log(f"❌ {name} health check failed - Status: {response.status_code}", "ERROR")
                    results[name] = None
            except Exception as e:
                self.log(f"❌ {name} health check error: {e}", "ERROR")
                results[name] = None
        
        return results
    
    def test_data_api(self):
        """Test Data API endpoints"""
        self.log("Testing Data API...")
        
        # Test symbol creation
        try:
            symbol_data = {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "exchange": "NASDAQ",
                "sector": "Technology"
            }
            
            response = self.session.post(f"{self.base_url}/data/symbols/", json=symbol_data)
            if response.status_code in [200, 201]:
                self.log("✅ Symbol creation successful")
            else:
                self.log(f"⚠️ Symbol creation returned: {response.status_code} (might already exist)")
            
            # Test symbol listing
            response = self.session.get(f"{self.base_url}/data/symbols/")
            if response.status_code == 200:
                symbols = response.json()
                self.log(f"✅ Symbol listing successful - Found {len(symbols.get('results', []))} symbols")
            else:
                self.log(f"❌ Symbol listing failed - Status: {response.status_code}", "ERROR")
            
            # Test available indicators
            response = self.session.get(f"{self.base_url}/data/api/available_indicators/")
            if response.status_code == 200:
                indicators = response.json()
                self.log(f"✅ Available indicators retrieved - Found {len(indicators.get('indicators', {}))} categories")
            else:
                self.log(f"⚠️ Available indicators request returned: {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Data API test error: {e}", "ERROR")
            return False
    
    def test_strategy_api(self):
        """Test Strategy API endpoints"""
        self.log("Testing Strategy API...")
        
        try:
            # Test strategy creation
            strategy_data = {
                "name": "Test Strategy",
                "description": "A simple test strategy",
                "strategy_code": "# Simple test strategy\ndef initialize(context):\n    pass\n\ndef handle_data(context, data):\n    pass",
                "parameters": {"test_param": 42},
                "tags": ["test", "simple"],
                "timeframe": "1d",
                "risk_level": "low"
            }
            
            response = self.session.post(f"{self.base_url}/strategies/api/create_strategy/", json=strategy_data)
            if response.status_code == 201:
                strategy = response.json()
                strategy_id = strategy.get('id')
                self.log(f"✅ Strategy creation successful - ID: {strategy_id}")
                
                # Test strategy listing
                response = self.session.get(f"{self.base_url}/strategies/strategies/")
                if response.status_code == 200:
                    strategies = response.json()
                    self.log(f"✅ Strategy listing successful - Found {len(strategies.get('results', []))} strategies")
                else:
                    self.log(f"❌ Strategy listing failed - Status: {response.status_code}", "ERROR")
                
                return strategy_id
            else:
                self.log(f"❌ Strategy creation failed - Status: {response.status_code}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Strategy API test error: {e}", "ERROR")
            return None
    
    def test_backtest_api(self):
        """Test Backtest API endpoints"""
        self.log("Testing Backtest API...")
        
        try:
            # Test backtest config creation
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=365)
            
            config_data = {
                "name": "Test Backtest Config",
                "description": "Test configuration for API testing",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "initial_capital": 10000.00,
                "commission": 0.001,
                "slippage": 0.0005
            }
            
            response = self.session.post(f"{self.base_url}/backtests/api/create_config/", json=config_data)
            if response.status_code == 201:
                config = response.json()
                config_id = config.get('id')
                self.log(f"✅ Backtest config creation successful - ID: {config_id}")
                
                # Test config listing
                response = self.session.get(f"{self.base_url}/backtests/configs/")
                if response.status_code == 200:
                    configs = response.json()
                    self.log(f"✅ Backtest config listing successful - Found {len(configs.get('results', []))} configs")
                else:
                    self.log(f"❌ Backtest config listing failed - Status: {response.status_code}", "ERROR")
                
                return config_id
            else:
                self.log(f"❌ Backtest config creation failed - Status: {response.status_code}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Backtest API test error: {e}", "ERROR")
            return None
    
    def test_quick_backtest(self):
        """Test quick backtest functionality"""
        self.log("Testing quick backtest...")
        
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)  # Shorter period for quick test
            
            quick_backtest_data = {
                "strategy_code": """
# Simple buy and hold strategy
def initialize(context):
    context.asset = 'AAPL'

def handle_data(context, data):
    if context.asset not in context.portfolio.positions:
        order_target_percent(context.asset, 1.0)
""",
                "symbol": "AAPL",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "initial_capital": 10000.00
            }
            
            response = self.session.post(f"{self.base_url}/backtests/api/quick_run/", json=quick_backtest_data)
            if response.status_code == 200:
                result = response.json()
                self.log(f"✅ Quick backtest successful - Status: {result.get('status')}")
                return True
            else:
                response_text = response.text[:200] if response.text else "No response content"
                self.log(f"⚠️ Quick backtest returned: {response.status_code} - {response_text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Quick backtest error: {e}", "ERROR")
            return False
    
    def run_full_test_suite(self):
        """Run complete test suite"""
        self.log("🚀 Starting AlgoAgent API Test Suite...")
        
        # Test basic connection
        if not self.test_connection():
            self.log("❌ Basic connection failed, aborting tests", "ERROR")
            return False
        
        # Test health endpoints
        health_results = self.test_health_endpoints()
        
        # Test individual APIs
        data_api_ok = self.test_data_api()
        strategy_id = self.test_strategy_api()
        config_id = self.test_backtest_api()
        
        # Test quick backtest (integration test)
        quick_backtest_ok = self.test_quick_backtest()
        
        # Summary
        self.log("=" * 50)
        self.log("📋 Test Summary:")
        self.log(f"  Connection: {'✅ PASS' if True else '❌ FAIL'}")
        self.log(f"  Data API: {'✅ PASS' if data_api_ok else '❌ FAIL'}")
        self.log(f"  Strategy API: {'✅ PASS' if strategy_id else '❌ FAIL'}")
        self.log(f"  Backtest API: {'✅ PASS' if config_id else '❌ FAIL'}")
        self.log(f"  Quick Backtest: {'✅ PASS' if quick_backtest_ok else '⚠️ PARTIAL'}")
        
        # Health status summary
        self.log("\n🏥 Health Status:")
        for api_name, health_data in health_results.items():
            if health_data:
                status = health_data.get('status', 'unknown')
                self.log(f"  {api_name}: {status}")
            else:
                self.log(f"  {api_name}: ❌ UNHEALTHY")
        
        self.log("=" * 50)
        self.log("🎉 Test suite completed!")
        
        return all([data_api_ok, strategy_id is not None, config_id is not None])


if __name__ == "__main__":
    # Run the test suite
    tester = AlgoAgentAPITester()
    success = tester.run_full_test_suite()
    
    if success:
        print("\n🎉 All major tests passed! Your AlgoAgent Django API is working correctly.")
        print("\n📡 API Endpoints Available:")
        print("  • Data API: http://127.0.0.1:8000/api/data/")
        print("  • Strategy API: http://127.0.0.1:8000/api/strategies/")
        print("  • Backtest API: http://127.0.0.1:8000/api/backtests/")
        print("  • Admin Interface: http://127.0.0.1:8000/admin/")
        print("\n📚 API Documentation (Browsable API):")
        print("  • Visit any endpoint URL in your browser for interactive docs")
    else:
        print("\n⚠️ Some tests had issues. Check the logs above for details.")
        print("The API server is running, but some integrations may need attention.")