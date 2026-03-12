"""
Test Strategy Generation Endpoint with Copilot
"""
import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000"
ENDPOINT = f"{BASE_URL}/api/strategies/api/generate_code/"

# Test payload
payload = {
    "strategy_description": "Create a simple RSI strategy with 14-period RSI, buy below 30, sell above 70. with take profit 40 pips from entry and stop loss 15 pips from entry",
    "ai_provider": "copilot",
    "use_gemini": False,
    "parameters": {}
}

print("=" * 80)
print("TESTING COPILOT STRATEGY GENERATION ENDPOINT")
print("=" * 80)
print(f"\nEndpoint: {ENDPOINT}")
print(f"\nPayload:")
print(json.dumps(payload, indent=2))
print("\n" + "=" * 80)
print("Sending request (this may take 30-60 seconds)...")
print("=" * 80 + "\n")

start_time = time.time()

try:
    response = requests.post(
        ENDPOINT,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=120
    )
    
    elapsed = time.time() - start_time
    
    print(f"\n✓ Response received in {elapsed:.1f} seconds")
    print(f"Status Code: {response.status_code}\n")
    
    if response.status_code == 200:
        data = response.json()
        
        print("=" * 80)
        print("SUCCESS - CODE GENERATED")
        print("=" * 80)
        print(f"AI Provider:    {data.get('metadata', {}).get('ai_provider', 'unknown')}")
        print(f"Strategy Name:  {data.get('strategy_name', 'N/A')}")
        print(f"Description:    {data.get('description', 'N/A')[:80]}...")
        print(f"Code Length:    {len(data.get('generated_code', ''))} characters")
        print("=" * 80)
        
        code = data.get('generated_code', '')
        
        # Show first 1000 characters
        print("\nGENERATED CODE (first 1000 chars):")
        print("-" * 80)
        print(code[:1000])
        print("-" * 80)
        
        # Save to file
        output_file = "test_generated_strategy.py"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(code)
        print(f"\n✓ Full code saved to: {output_file}")
        
        # Check for key patterns
        print("\nCODE VALIDATION:")
        checks = {
            "Copilot imports": "from Backtest.sim_broker import SimBroker" in code,
            "BacktestConfig": "BacktestConfig" in code,
            "Signal schema": "'signal_id'" in code and "'timestamp'" in code,
            "RSI calculation": "rsi" in code.lower() or "RSI" in code,
            "Buy condition": "30" in code,  # RSI threshold
            "Sell condition": "70" in code,  # RSI threshold
        }
        
        for check, passed in checks.items():
            status = "✓" if passed else "✗"
            print(f"  {status} {check}")
        
        all_passed = all(checks.values())
        print("\n" + "=" * 80)
        if all_passed:
            print("✓ ALL VALIDATION CHECKS PASSED")
        else:
            print("⚠ SOME VALIDATION CHECKS FAILED")
        print("=" * 80)
        
    else:
        print("=" * 80)
        print(f"ERROR - Status {response.status_code}")
        print("=" * 80)
        print(response.text)
        
except requests.exceptions.Timeout:
    print("\n✗ ERROR: Request timed out after 120 seconds")
    print("   The server may be processing the request. Check server logs.")
    
except requests.exceptions.ConnectionError:
    print("\n✗ ERROR: Could not connect to server")
    print(f"   Is the Django server running on {BASE_URL}?")
    
except Exception as e:
    print(f"\n✗ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
