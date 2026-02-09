import requests
import json

# API base URL
BASE_URL = "http://127.0.0.1:8000"

# Login credentials
LOGIN_URL = f"{BASE_URL}/api/auth/login/"
credentials = {
    "username": "algotrader",
    "password": "Trading@2024"
}

print("="*80)
print("STRATEGY 115 BACKTEST EXECUTION")
print("="*80)

# Step 1: Login
print("\n[1/3] Logging in...")
try:
    login_response = requests.post(LOGIN_URL, json=credentials)
    login_response.raise_for_status()
    token = login_response.json()["access"]
    print(f"✓ Login successful! Token obtained (length: {len(token)})")
except Exception as e:
    print(f"✗ Login failed: {e}")
    exit(1)

# Step 2: Execute backtest
print("\n[2/3] Triggering backtest execution...")
EXECUTE_URL = f"{BASE_URL}/api/strategies/strategies/115/execute/"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

backtest_params = {
    "test_symbol": "AAPL",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
}

print(f"  Symbol: {backtest_params['test_symbol']}")
print(f"  Period: {backtest_params['start_date']} to {backtest_params['end_date']}")

try:
    execute_response = requests.post(EXECUTE_URL, headers=headers, json=backtest_params)
    execute_response.raise_for_status()
    result = execute_response.json()
    
    print(f"\n✓ Backtest execution completed!")
    print("\n" + "="*80)
    print("BACKTEST RESULTS:")
    print("="*80)
    print(json.dumps(result, indent=2))
    
    # Step 3: Check for trades
    print("\n[3/3] Analyzing results...")
    if 'total_trades' in result:
        trades = result['total_trades']
        print(f"\n{'='*80}")
        print(f"TOTAL TRADES GENERATED: {trades}")
        print(f"{'='*80}")
        
        if trades > 0:
            print(f"✓ SUCCESS! Strategy generated {trades} trades with real market data")
            if 'win_rate' in result:
                print(f"  Win Rate: {result['win_rate']}%")
            if 'total_return' in result:
                print(f"  Total Return: {result['total_return']}%")
        else:
            print(f"⚠️  WARNING: 0 trades generated")
            print(f"  This could mean:")
            print(f"  - No trading patterns found in the data for this period")
            print(f"  - Strategy conditions are too strict")
            print(f"  - Need to check different symbol/timeframe")
    
except requests.exceptions.HTTPError as e:
    print(f"\n✗ Backtest execution failed: {e}")
    print(f"Response: {e.response.text}")
except Exception as e:
    print(f"\n✗ Error: {e}")
