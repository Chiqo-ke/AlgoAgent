"""
Simple API Integration Test
Tests the newly integrated backend endpoints
No authentication required (endpoints use AllowAny)
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/strategies"

def test_available_indicators():
    """Test indicator registry endpoint"""
    print("\n" + "="*80)
    print("TEST 1: Available Indicators Endpoint")
    print("="*80)
    
    try:
        url = f"{BASE_URL}/available_indicators/"
        print(f"GET {url}")
        
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            print(f"✅ SUCCESS: Found {count} available indicators")
            
            if count > 0:
                print("\nAvailable Indicators:")
                for ind in data.get('indicators', [])[:5]:
                    print(f"  - {ind['name']}: {ind['display_name']}")
                    print(f"    Parameters: {', '.join(ind.get('parameters', {}).keys())}")
            return True
        else:
            print(f"❌ FAILED: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_list_strategies():
    """Test listing strategies to get an ID for other tests"""
    print("\n" + "="*80)
    print("TEST 2: List Strategies")
    print("="*80)
    
    try:
        url = f"{BASE_URL}/"
        print(f"GET {url}")
        
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                count = len(data)
            else:
                count = data.get('count', 0)
                data = data.get('results', [])
            
            print(f"✅ SUCCESS: Found {count} strategies")
            
            if count > 0:
                strategy = data[0]
                strategy_id = strategy.get('id')
                print(f"\nFirst Strategy:")
                print(f"  - ID: {strategy_id}")
                print(f"  - Name: {strategy.get('name', 'N/A')}")
                print(f"  - Status: {strategy.get('status', 'N/A')}")
                return strategy_id
            else:
                print("⚠️  No strategies found - will skip execution tests")
                return None
        else:
            print(f"❌ FAILED: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return None

def test_execute_strategy(strategy_id):
    """Test strategy execution endpoint"""
    print("\n" + "="*80)
    print("TEST 3: Execute Strategy")
    print("="*80)
    
    if not strategy_id:
        print("⚠️  SKIPPED: No strategy ID available")
        return False
    
    try:
        url = f"{BASE_URL}/{strategy_id}/execute/"
        payload = {"symbol": "GOOG"}
        print(f"POST {url}")
        print(f"Payload: {json.dumps(payload)}")
        
        response = requests.post(url, json=payload, timeout=120)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS: Strategy executed")
            print(f"  - Success: {data.get('success')}")
            print(f"  - Return: {data.get('return_pct')}%")
            print(f"  - Trades: {data.get('num_trades')}")
            print(f"  - Win Rate: {data.get('win_rate')}")
            return True
        elif response.status_code == 404:
            print(f"⚠️  Endpoint not found - may not be implemented yet")
            return False
        else:
            print(f"❌ FAILED: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_fix_errors(strategy_id):
    """Test error fixing endpoint"""
    print("\n" + "="*80)
    print("TEST 4: Fix Strategy Errors")
    print("="*80)
    
    if not strategy_id:
        print("⚠️  SKIPPED: No strategy ID available")
        return False
    
    try:
        url = f"{BASE_URL}/{strategy_id}/fix_errors/"
        payload = {"max_attempts": 3}
        print(f"POST {url}")
        print(f"Payload: {json.dumps(payload)}")
        
        response = requests.post(url, json=payload, timeout=120)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS: Error fixing completed")
            print(f"  - Success: {data.get('success')}")
            print(f"  - Attempts: {data.get('attempts')}")
            
            for fix in data.get('fixes', []):
                print(f"  - Attempt {fix['attempt']}: {'✓' if fix['success'] else '✗'}")
            return True
        elif response.status_code == 404:
            print(f"⚠️  Endpoint not found - may not be implemented yet")
            return False
        else:
            print(f"❌ FAILED: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_execution_history(strategy_id):
    """Test execution history endpoint"""
    print("\n" + "="*80)
    print("TEST 5: Execution History")
    print("="*80)
    
    if not strategy_id:
        print("⚠️  SKIPPED: No strategy ID available")
        return False
    
    try:
        url = f"{BASE_URL}/{strategy_id}/execution_history/"
        print(f"GET {url}")
        
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS: Execution history retrieved")
            print(f"  - Total Executions: {data.get('total_executions', 0)}")
            
            executions = data.get('executions', [])
            if executions:
                print(f"\n  Latest Execution:")
                latest = executions[-1]
                print(f"    - Timestamp: {latest.get('timestamp')}")
                print(f"    - Success: {latest.get('success')}")
                print(f"    - Return: {latest.get('return_pct')}%")
            return True
        elif response.status_code == 404:
            print(f"⚠️  Endpoint not found - may not be implemented yet")
            return False
        else:
            print(f"❌ FAILED: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    print("\n" + "="*80)
    print("API BACKEND INTEGRATION TEST")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target: {BASE_URL}")
    print("="*80)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/api/", timeout=5)
        print(f"\n✅ Server is running (Status: {response.status_code})")
    except Exception as e:
        print(f"\n❌ ERROR: Server not responding - {e}")
        print("Make sure Django server is running: python manage.py runserver")
        return
    
    results = {}
    
    # Test 1: Indicator Registry (new endpoint)
    results['indicators'] = test_available_indicators()
    
    # Test 2: List strategies to get ID
    strategy_id = test_list_strategies()
    results['list'] = strategy_id is not None
    
    # Test 3-5: Endpoints that need strategy_id
    if strategy_id:
        results['execute'] = test_execute_strategy(strategy_id)
        results['fix_errors'] = test_fix_errors(strategy_id)
        results['history'] = test_execution_history(strategy_id)
    else:
        results['execute'] = None
        results['fix_errors'] = None
        results['history'] = None
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    for name, result in results.items():
        if result is True:
            print(f"✅ PASS - {name}")
        elif result is False:
            print(f"❌ FAIL - {name}")
        else:
            print(f"⚠️  SKIP - {name}")
    
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)
    
    print(f"\nResults: {passed} passed, {failed} failed, {skipped} skipped")
    print("="*80)

if __name__ == "__main__":
    main()
