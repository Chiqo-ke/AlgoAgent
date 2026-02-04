"""
Quick Diagnostic Test - Minimal Strategy
==========================================

Quick test to verify diagnostic fixes work.
Uses a very simple strategy to minimize execution time.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def quick_test():
    print("\n" + "="*70)
    print("QUICK DIAGNOSTIC TEST")
    print("="*70 + "\n")
    
    # Create strategy
    print("1. Creating strategy...")
    create_url = f"{BASE_URL}/api/strategies/api/create_strategy/"
    
    payload = {
        "name": f"QuickTest_{int(time.time())}",
        "description": "Simple SMA crossover: buy when SMA(10) > SMA(20), sell when SMA(10) < SMA(20)",
        "strategy_type": "trend_following",
        "risk_per_trade": 1.0,
        "stop_loss_pct": 1.0,
        "session_id": f"quick_{int(time.time())}"
    }
    
    response = requests.post(create_url, json=payload, timeout=30)
    
    if response.status_code != 201:
        print(f"❌ Failed to create: {response.status_code}")
        print(response.text[:200])
        return
    
    strategy_id = response.json()['id']
    print(f"✓ Created strategy ID: {strategy_id}\n")
    
    # Generate with auto-execute
    print("2. Generating code (auto-execute enabled)...")
    print("   This will test the diagnostic system...")
    print("   ⏳ Please wait...\n")
    
    gen_url = f"{BASE_URL}/api/strategies/api/generate_strategy_unified/"
    gen_payload = {
        "strategy_id": strategy_id,
        "auto_execute": True,
        "auto_fix": True,
        "max_fix_attempts": 5,
        "test_symbol": "AAPL",
        "test_period": "3mo"  # Shorter period for faster execution
    }
    
    start = time.time()
    response = requests.post(gen_url, json=gen_payload, timeout=600)
    elapsed = time.time() - start
    
    print(f"\n3. Response received ({elapsed:.1f}s)")
    print(f"   Status: {response.status_code}\n")
    
    if response.status_code == 200:
        data = response.json()
        
        # Check execution result
        exec_result = data.get('execution_result', {})
        print(f"📊 Execution:")
        print(f"   Success: {exec_result.get('success')}")
        
        if exec_result.get('error'):
            print(f"   Error: {exec_result['error'][:150]}")
        
        if exec_result.get('trades') is not None:
            print(f"   Trades: {exec_result['trades']}")
        
        # Check fix attempts
        fix_attempts = data.get('fix_attempts', [])
        if fix_attempts:
            print(f"\n🔧 Fix Attempts: {len(fix_attempts)}")
            
            for i, attempt in enumerate(fix_attempts[:3], 1):
                print(f"\n   #{i}: {attempt.get('error_type', 'unknown')}")
                
                # Look for diagnostic indicators
                attempt_str = json.dumps(attempt)
                if 'diagnostic' in attempt_str.lower():
                    print(f"       🔍 Used diagnostics")
                if 'fallback' in attempt_str.lower() or 'disabling' in attempt_str.lower():
                    print(f"       ⚠️  Diagnostic fallback triggered")
                if 'loop' in attempt_str.lower():
                    print(f"       🔁 Loop detection active")
        
        # Final result
        print(f"\n" + "="*70)
        if exec_result.get('success'):
            print("✅ TEST PASSED - Strategy executed successfully!")
            print(f"   Diagnostic system is working correctly")
        elif fix_attempts:
            print("⚠️  TEST PARTIAL - Strategy generated with fixes")
            print(f"   Diagnostic system engaged ({len(fix_attempts)} attempts)")
            
            # Check if our fixes worked
            last_errors = [a.get('error_message', '')[:50] for a in fix_attempts[-3:]]
            if len(set(last_errors)) < len(last_errors):
                print(f"   ⚠️  Repeated errors detected")
                if len(fix_attempts) < 5:
                    print(f"   ✓ Loop detection stopped infinite loop")
                else:
                    print(f"   ❌ Loop detection may not have triggered")
        else:
            print("❌ TEST FAILED - No execution or fixes")
        
        print(f"\nStrategy ID: {strategy_id}")
        
    else:
        print(f"❌ Failed: {response.text[:300]}")

if __name__ == "__main__":
    try:
        quick_test()
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
