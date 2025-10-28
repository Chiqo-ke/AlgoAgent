"""
Test script for AI-powered Strategy API endpoints
Tests the integration between Django API and Strategy validation module
"""

import requests
import json
from datetime import datetime


class AIStrategyAPITester:
    """Test the AI-powered strategy API endpoints"""
    
    def __init__(self, base_url="http://localhost:8000"):
        """Initialize the tester"""
        self.base_url = base_url
        self.token = None
        self.headers = {'Content-Type': 'application/json'}
    
    def print_section(self, title):
        """Print a section header"""
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80)
    
    def print_result(self, response):
        """Print API response in a readable format"""
        print(f"\nStatus Code: {response.status_code}")
        try:
            data = response.json()
            print(json.dumps(data, indent=2))
        except:
            print(response.text)
    
    def test_health_check(self):
        """Test the health endpoint"""
        self.print_section("1. Health Check")
        
        url = f"{self.base_url}/api/strategies/api/health/"
        response = requests.get(url)
        
        self.print_result(response)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Health check passed")
            print(f"  Validator available: {data.get('validator_available')}")
            print(f"  Generator available: {data.get('generator_available')}")
            return True
        else:
            print("\n❌ Health check failed")
            return False
    
    def test_validate_strategy(self):
        """Test AI validation endpoint"""
        self.print_section("2. AI Strategy Validation")
        
        # Example strategy from the interactive tester
        strategy_text = """
        1. Entry: Buy when 50 EMA crosses above 200 EMA
        2. Exit: Sell when 50 EMA crosses below 200 EMA
        3. Stop Loss: 2% below entry price
        4. Take Profit: 5% above entry price
        5. Position Size: Risk 1% of account per trade
        """
        
        payload = {
            "strategy_text": strategy_text,
            "input_type": "numbered",
            "use_gemini": True,
            "strict_mode": False
        }
        
        url = f"{self.base_url}/api/strategies/api/validate_strategy_with_ai/"
        print(f"\nPOST {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, headers=self.headers)
        self.print_result(response)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Validation successful")
            print(f"  Status: {data.get('status')}")
            print(f"  Confidence: {data.get('confidence')}")
            print(f"  Classification: {data.get('classification_detail', {}).get('type')}")
            print(f"  Risk Tier: {data.get('classification_detail', {}).get('risk_tier')}")
            
            recommendations = data.get('recommendations_list', [])
            if recommendations:
                print(f"\n  Top Recommendations:")
                for i, rec in enumerate(recommendations[:3], 1):
                    print(f"    {i}. {rec.get('title')}")
            
            return data
        else:
            print("\n❌ Validation failed")
            return None
    
    def test_create_strategy_with_ai(self):
        """Test creating a strategy with AI validation"""
        self.print_section("3. Create Strategy with AI")
        
        strategy_text = """
        RSI Mean Reversion Strategy:
        - Buy when RSI(14) drops below 30 (oversold)
        - Sell when RSI(14) rises above 70 (overbought)
        - Stop loss at 3% below entry
        - Position size: 2% of account per trade
        - Trade on 1-hour timeframe
        """
        
        payload = {
            "strategy_text": strategy_text,
            "input_type": "freetext",
            "name": "RSI Mean Reversion",
            "description": "Simple RSI-based mean reversion strategy",
            "tags": ["rsi", "mean-reversion", "momentum"],
            "use_gemini": True,
            "strict_mode": False,
            "save_to_backtest": True
        }
        
        url = f"{self.base_url}/api/strategies/api/create_strategy_with_ai/"
        print(f"\nPOST {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, headers=self.headers)
        self.print_result(response)
        
        if response.status_code == 201:
            data = response.json()
            print(f"\n✓ Strategy created successfully")
            print(f"  Strategy ID: {data['strategy']['id']}")
            print(f"  Name: {data['strategy']['name']}")
            print(f"  Risk Level: {data['strategy']['risk_level']}")
            
            if 'auto_created_template' in data:
                print(f"  Template ID: {data['auto_created_template']['id']}")
                print(f"  Template Name: {data['auto_created_template']['name']}")
            
            if 'saved_to_file' in data:
                print(f"  Saved to: {data['saved_to_file']['path']}")
            
            ai_validation = data.get('ai_validation', {})
            print(f"\n  AI Validation:")
            print(f"    Confidence: {ai_validation.get('confidence')}")
            print(f"    Warnings: {len(ai_validation.get('warnings', []))}")
            
            return data['strategy']['id']
        else:
            print("\n❌ Strategy creation failed")
            return None
    
    def test_update_strategy_with_ai(self, strategy_id):
        """Test updating a strategy with AI validation"""
        self.print_section("4. Update Strategy with AI")
        
        if not strategy_id:
            print("⚠ Skipping - no strategy ID provided")
            return False
        
        updated_strategy_text = """
        Enhanced RSI Mean Reversion Strategy:
        1. Entry: Buy when RSI(14) < 30 AND price is above 200 SMA
        2. Exit: Sell when RSI(14) > 70 OR price crosses below 200 SMA
        3. Stop Loss: 2.5% below entry (tightened)
        4. Take Profit: 6% above entry (added profit target)
        5. Position Size: Risk 1.5% per trade based on ATR
        """
        
        payload = {
            "strategy_text": updated_strategy_text,
            "input_type": "numbered",
            "use_gemini": True,
            "strict_mode": False,
            "update_description": "Added 200 SMA filter and tightened risk parameters"
        }
        
        url = f"{self.base_url}/api/strategies/api/{strategy_id}/update_strategy_with_ai/"
        print(f"\nPUT {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.put(url, json=payload, headers=self.headers)
        self.print_result(response)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Strategy updated successfully")
            print(f"  Message: {data.get('message')}")
            
            ai_validation = data.get('ai_validation', {})
            print(f"\n  AI Re-validation:")
            print(f"    Confidence: {ai_validation.get('confidence')}")
            print(f"    Warnings: {len(ai_validation.get('warnings', []))}")
            
            return True
        else:
            print("\n❌ Strategy update failed")
            return False
    
    def test_freetext_strategy(self):
        """Test with free-text strategy description"""
        self.print_section("5. Free-text Strategy Input")
        
        strategy_text = """
        I want to create a scalping strategy. Buy when price breaks above 
        the previous 15-minute high with volume confirmation. Exit after 
        10 points profit or 5 points loss. Use tight stops and scale in 
        with 3 positions. Only trade during high liquidity hours.
        """
        
        payload = {
            "strategy_text": strategy_text,
            "input_type": "freetext",
            "use_gemini": True,
            "strict_mode": False
        }
        
        url = f"{self.base_url}/api/strategies/api/validate_strategy_with_ai/"
        print(f"\nPOST {url}")
        
        response = requests.post(url, json=payload, headers=self.headers)
        self.print_result(response)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Free-text validation successful")
            
            # Show canonicalized steps
            steps = data.get('canonicalized_steps', [])
            if steps:
                print(f"\n  Canonicalized Steps ({len(steps)}):")
                for step in steps[:3]:  # Show first 3
                    print(f"    • {step}")
            
            return True
        else:
            print("\n❌ Free-text validation failed")
            return False
    
    def run_all_tests(self):
        """Run all test scenarios"""
        print("\n" + "🤖" * 40)
        print("  AI-POWERED STRATEGY API INTEGRATION TESTS")
        print("🤖" * 40)
        print(f"\nBase URL: {self.base_url}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        results = {}
        
        # Test 1: Health check
        results['health'] = self.test_health_check()
        
        if not results['health']:
            print("\n❌ Server not available. Stopping tests.")
            return results
        
        # Test 2: Validate strategy
        validation_result = self.test_validate_strategy()
        results['validation'] = validation_result is not None
        
        # Test 3: Create strategy with AI
        strategy_id = self.test_create_strategy_with_ai()
        results['creation'] = strategy_id is not None
        
        # Test 4: Update strategy with AI
        results['update'] = self.test_update_strategy_with_ai(strategy_id)
        
        # Test 5: Free-text input
        results['freetext'] = self.test_freetext_strategy()
        
        # Summary
        self.print_section("TEST SUMMARY")
        total = len(results)
        passed = sum(1 for v in results.values() if v)
        
        print(f"\nTests Passed: {passed}/{total}")
        for test_name, result in results.items():
            status = "✓ PASS" if result else "❌ FAIL"
            print(f"  {status} - {test_name}")
        
        return results


def main():
    """Main test runner"""
    import sys
    
    # Get base URL from command line or use default
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    tester = AIStrategyAPITester(base_url=base_url)
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if all(results.values()):
        print("\n✓ All tests passed!")
        sys.exit(0)
    else:
        print("\n⚠ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
