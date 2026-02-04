"""
Test Diagnostic System via API
================================

This script tests the improved diagnostic system by creating a strategy
through direct API calls to the backend.

It will:
1. Validate a strategy description
2. Create the strategy
3. Generate the code with auto-execution enabled
4. Monitor the diagnostic/fix process
"""

import requests
import json
import time
from datetime import datetime

# Backend URL
BASE_URL = "http://localhost:8000"

# Test strategy description
STRATEGY_DESCRIPTION = """
Create a simple RSI momentum strategy:

• Use 14-period RSI indicator
• Buy when RSI crosses below 30 (oversold)
• Sell when RSI crosses above 70 (overbought)
• Risk 2% per trade
• Use a 2% stop loss

Test on AAPL with 1 year of data.
"""


def print_section(title):
    """Print a section header"""
    print(f"\n{'='*70}")
    print(f"{title}")
    print(f"{'='*70}\n")


def validate_strategy():
    """Step 1: Validate the strategy description"""
    print_section("STEP 1: Validate Strategy")
    
    url = f"{BASE_URL}/api/strategies/api/validate_strategy_with_ai/"
    payload = {
        "strategy_text": STRATEGY_DESCRIPTION,  # Changed from strategy_description
        "session_id": f"test_{int(time.time())}"
    }
    
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}\n")
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Validation Status: {data.get('status')}")
            print(f"  Valid: {data.get('is_valid')}")
            
            if data.get('suggestions'):
                print("\nSuggestions:")
                for i, suggestion in enumerate(data.get('suggestions', [])[:3], 1):
                    print(f"  {i}. {suggestion}")
            
            return True
        else:
            print(f"✗ Validation failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def create_strategy():
    """Step 2: Create the strategy"""
    print_section("STEP 2: Create Strategy")
    
    url = f"{BASE_URL}/api/strategies/api/create_strategy/"
    payload = {
        "name": f"RSI_Test_{int(time.time())}",
        "description": STRATEGY_DESCRIPTION,
        "strategy_type": "momentum",
        "risk_per_trade": 2.0,
        "stop_loss_pct": 2.0,
        "take_profit_pct": 4.0,
        "session_id": f"test_{int(time.time())}"
    }
    
    print(f"POST {url}")
    print(f"Strategy Name: {payload['name']}\n")
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            strategy_id = data.get('id')
            print(f"✓ Strategy created: ID {strategy_id}")
            print(f"  Name: {data.get('name')}")
            print(f"  Status: {data.get('status')}")
            return strategy_id
        else:
            print(f"✗ Creation failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return None


def generate_strategy(strategy_id):
    """Step 3: Generate strategy code with auto-execution"""
    print_section("STEP 3: Generate Code (Auto-Execute Enabled)")
    
    url = f"{BASE_URL}/api/strategies/api/generate_strategy_unified/"
    payload = {
        "strategy_id": strategy_id,
        "auto_execute": True,
        "auto_fix": True,
        "max_fix_attempts": 5,
        "test_symbol": "AAPL",
        "test_period": "1y"
    }
    
    print(f"POST {url}")
    print(f"Strategy ID: {strategy_id}")
    print(f"Auto-Execute: {payload['auto_execute']}")
    print(f"Auto-Fix: {payload['auto_fix']}")
    print(f"Max Fix Attempts: {payload['max_fix_attempts']}")
    print(f"\n⏳ This may take a few minutes...\n")
    
    start_time = time.time()
    
    try:
        response = requests.post(url, json=payload, timeout=600)  # 10 min timeout
        elapsed = time.time() - start_time
        
        print(f"Status: {response.status_code} (took {elapsed:.1f}s)")
        
        if response.status_code == 200:
            data = response.json()
            
            # Code generation result
            print(f"\n✓ Code Generation:")
            print(f"  Status: {data.get('status')}")
            print(f"  File: {data.get('file_path', 'N/A')}")
            
            # Execution result
            if data.get('execution_result'):
                exec_result = data['execution_result']
                print(f"\n📊 Execution Result:")
                print(f"  Success: {exec_result.get('success')}")
                print(f"  Duration: {exec_result.get('duration_seconds', 0):.1f}s")
                
                if exec_result.get('error'):
                    print(f"  Error: {exec_result['error'][:200]}")
                
                if exec_result.get('return_pct') is not None:
                    print(f"  Return: {exec_result['return_pct']:.2f}%")
                if exec_result.get('trades') is not None:
                    print(f"  Trades: {exec_result['trades']}")
            
            # Fix attempts
            if data.get('fix_attempts'):
                fix_attempts = data['fix_attempts']
                print(f"\n🔧 Fix Attempts: {len(fix_attempts)}")
                
                for i, attempt in enumerate(fix_attempts, 1):
                    print(f"\n  Attempt {i}:")
                    print(f"    Success: {attempt.get('success')}")
                    print(f"    Error Type: {attempt.get('error_type')}")
                    if attempt.get('error_message'):
                        print(f"    Error: {attempt['error_message'][:100]}")
                    
                    # Check if diagnostics were used
                    if 'diagnostic' in str(attempt).lower():
                        print(f"    🔍 Diagnostics: ENABLED")
            
            # Check for infinite loop detection
            if len(data.get('fix_attempts', [])) >= 3:
                print(f"\n⚠️ Multiple fix attempts detected")
                print(f"   Checking for loop detection...")
                
                errors = [a.get('error_message', '')[:50] for a in data.get('fix_attempts', [])]
                if len(errors) != len(set(errors)):
                    print(f"   ✓ Same errors detected - loop protection should have triggered")
            
            return data
            
        else:
            print(f"✗ Generation failed: {response.text[:500]}")
            return None
            
    except requests.Timeout:
        print(f"✗ Request timed out after 10 minutes")
        return None
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_strategy_details(strategy_id):
    """Get strategy details to verify final state"""
    print_section("STEP 4: Verify Final State")
    
    url = f"{BASE_URL}/api/strategies/{strategy_id}/"
    
    try:
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Strategy ID: {strategy_id}")
            print(f"Name: {data.get('name')}")
            print(f"Status: {data.get('status')}")
            print(f"Has Code: {'Yes' if data.get('strategy_code') else 'No'}")
            print(f"File Path: {data.get('file_path', 'N/A')}")
            
            if data.get('last_backtest_result'):
                result = data['last_backtest_result']
                print(f"\nLast Backtest:")
                print(f"  Return: {result.get('total_return_pct', 0):.2f}%")
                print(f"  Trades: {result.get('total_trades', 0)}")
                print(f"  Win Rate: {result.get('win_rate', 0):.1f}%")
            
            return True
        else:
            print(f"✗ Failed to get details: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    """Run the full test"""
    print_section("DIAGNOSTIC SYSTEM TEST")
    print(f"Testing diagnostic fixes with direct API calls")
    print(f"Backend: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Validate
    if not validate_strategy():
        print("\n❌ Test failed at validation step")
        return
    
    time.sleep(2)
    
    # Step 2: Create
    strategy_id = create_strategy()
    if not strategy_id:
        print("\n❌ Test failed at creation step")
        return
    
    time.sleep(2)
    
    # Step 3: Generate with auto-execute and auto-fix
    result = generate_strategy(strategy_id)
    if not result:
        print("\n❌ Test failed at generation step")
        return
    
    time.sleep(2)
    
    # Step 4: Verify final state
    get_strategy_details(strategy_id)
    
    # Summary
    print_section("TEST SUMMARY")
    
    if result:
        if result.get('execution_result', {}).get('success'):
            print("✅ SUCCESS - Strategy generated and executed successfully!")
            print(f"   Diagnostic system working as expected")
        elif result.get('fix_attempts'):
            print("⚠️  PARTIAL SUCCESS - Strategy generated with fixes")
            print(f"   Fix attempts: {len(result.get('fix_attempts', []))}")
            print(f"   Diagnostic system engaged")
            
            # Check if diagnostics were properly used/skipped
            fix_messages = str(result.get('fix_attempts', []))
            if 'Falling back' in fix_messages or 'disabling' in fix_messages:
                print("   ✓ Fallback mechanism activated (as expected)")
            if 'Same error' in fix_messages or 'loop' in fix_messages.lower():
                print("   ✓ Loop detection triggered (as expected)")
        else:
            print("❌ FAILED - Strategy did not execute successfully")
            print(f"   Error: {result.get('execution_result', {}).get('error', 'Unknown')}")
    else:
        print("❌ FAILED - Could not generate strategy")
    
    print(f"\nStrategy ID: {strategy_id}")
    print(f"View in browser: {BASE_URL}/strategies/{strategy_id}/")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
