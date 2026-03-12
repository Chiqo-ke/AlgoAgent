"""
Test Bot Verification API
=========================
Test the bot verification endpoint with algo9999999888877 (known working bot)
"""

import requests
import json
from datetime import datetime

# API Configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/strategies"

def get_strategy_by_bot_file(bot_filename: str):
    """Find strategy that uses this bot file"""
    try:
        response = requests.get(f"{API_URL}/strategies/")
        response.raise_for_status()
        data = response.json()
        
        # Handle both list and dict with 'results' key
        if isinstance(data, dict):
            strategies = data.get('results', [])
        else:
            strategies = data
        
        print(f"Found {len(strategies)} strategies in database")
        
        # Look for strategy with matching bot file in strategy_code or file_path
        for strategy in strategies:
            strategy_code = strategy.get('strategy_code', '')
            file_path = strategy.get('file_path', '')
            name = strategy.get('name', '')
            
            if bot_filename in str(strategy_code) or bot_filename in str(file_path) or bot_filename in str(name):
                return strategy
        
        return None
    except Exception as e:
        print(f"Error fetching strategies: {e}")
        import traceback
        traceback.print_exc()
        return None

def verify_bot(strategy_id: int):
    """Verify a bot by running a test backtest"""
    print(f"\n{'='*80}")
    print(f"Testing Bot Verification API")
    print(f"{'='*80}")
    print(f"Strategy ID: {strategy_id}")
    print(f"Bot: algo9999999888877")
    print(f"Timestamp: {datetime.now().isoformat()}\n")
    
    # Verification request
    verification_data = {
        "strategy_id": strategy_id,
        "symbol": "AAPL",
        "start_date": "2024-01-01",
        "end_date": "2024-12-01",
        "timeframe": "1h",
        "initial_balance": 10000,
        "commission": 0.002
    }
    
    print(f"Sending verification request...")
    print(f"Config: {json.dumps(verification_data, indent=2)}\n")
    
    try:
        response = requests.post(
            f"{API_URL}/bot-performance/verify_bot/",
            json=verification_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ VERIFICATION SUCCESSFUL!")
            print(f"\nResults:")
            print(json.dumps(result, indent=2))
            
            # Extract key metrics
            if 'performance' in result:
                perf = result['performance']
                print(f"\n{'='*80}")
                print(f"PERFORMANCE SUMMARY")
                print(f"{'='*80}")
                print(f"Verified: {perf.get('is_verified', False)}")
                print(f"Total Trades: {perf.get('total_trades', 0)}")
                print(f"Win Rate: {perf.get('win_rate', 0)}%")
                print(f"Total Return: {perf.get('total_return', 0)}%")
                print(f"Max Drawdown: {perf.get('max_drawdown', 0)}%")
                print(f"Sharpe Ratio: {perf.get('sharpe_ratio', 0)}")
                print(f"Status: {perf.get('verification_status', 'unknown')}")
                print(f"{'='*80}")
        else:
            print(f"\n❌ VERIFICATION FAILED")
            print(f"Error: {response.text}")
            
        return response
        
    except Exception as e:
        print(f"\n❌ Request failed: {e}")
        return None

def get_verified_bots():
    """Get list of all verified bots"""
    print(f"\n{'='*80}")
    print(f"Fetching Verified Bots")
    print(f"{'='*80}\n")
    
    try:
        response = requests.get(f"{API_URL}/bot-performance/verified_bots/")
        response.raise_for_status()
        
        result = response.json()
        count = result.get('count', 0)
        bots = result.get('verified_bots', [])
        
        print(f"Found {count} verified bots:\n")
        
        for i, bot in enumerate(bots, 1):
            print(f"{i}. {bot['strategy']['name']}")
            print(f"   Return: {bot['total_return']}%")
            print(f"   Win Rate: {bot['win_rate']}%")
            print(f"   Trades: {bot['total_trades']}")
            print(f"   Last Tested: {bot['last_tested_at']}")
            print()
        
        return result
        
    except Exception as e:
        print(f"Error fetching verified bots: {e}")
        return None

def main():
    print(f"\n{'='*80}")
    print(f"BOT VERIFICATION API TEST")
    print(f"{'='*80}\n")
    
    # Check for command line argument
    import sys
    if len(sys.argv) > 1:
        strategy_id = int(sys.argv[1])
        print(f"Using provided strategy ID: {strategy_id}")
        
        # Verify the bot
        print("\nStep 1: Verifying bot...")
        verify_bot(strategy_id)
        
        # Check verified bots list
        print("\nStep 2: Checking verified bots list...")
        get_verified_bots()
        return
    
    # First, try to find the strategy for algo9999999888877
    print("Step 1: Looking for algo9999999888877 strategy...")
    strategy = get_strategy_by_bot_file("algo9999999888877")
    
    if strategy:
        print(f"✅ Found strategy: {strategy.get('name')} (ID: {strategy.get('id')})")
        
        # Verify the bot
        print("\nStep 2: Verifying bot...")
        verify_bot(strategy['id'])
        
        # Check verified bots list
        print("\nStep 3: Checking verified bots list...")
        get_verified_bots()
    else:
        print("❌ Strategy not found in database")
        print("\nNote: You may need to create a strategy record for algo9999999888877")
        print("The bot file exists and works, but needs a Strategy model instance.")
        print("\nRun: python create_working_bot_strategy.py")
        
        # Still show verification endpoint format
        print("\n" + "="*80)
        print("MANUAL VERIFICATION EXAMPLE")
        print("="*80)
        print("\nIf you have a strategy ID, you can verify it with:")
        print(f"\nPOST {API_URL}/bot-performance/verify_bot/")
        print(json.dumps({
            "strategy_id": 1,  # Replace with actual ID
            "symbol": "AAPL",
            "start_date": "2024-01-01",
            "end_date": "2024-12-01",
            "timeframe": "1h",
            "initial_balance": 10000,
            "commission": 0.002
        }, indent=2))

if __name__ == '__main__':
    main()
