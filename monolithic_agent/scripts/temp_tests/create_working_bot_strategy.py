"""
Create Strategy Record for algo9999999888877
============================================
Creates a Strategy model instance for the known working bot
"""

import requests
import json
from pathlib import Path

# API Configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/strategies"

# Read the bot code
bot_file = Path(__file__).parent / "Backtest" / "codes" / "algo9999999888877.py"
with open(bot_file, 'r', encoding='utf-8') as f:
    strategy_code = f.read()

# Read the bot config
bot_config_file = bot_file.with_suffix('.json')
with open(bot_config_file, 'r', encoding='utf-8') as f:
    config = json.load(f)

# Create strategy
strategy_data = {
    "name": "Algo9999999888877 - Price Action Strategy",
    "description": "Verified working bot - Trading strategy based on price action with RSI and EMA indicators. Successfully executed 8 trades with 2.44% return.",
    "strategy_code": strategy_code,
    "parameters": {
        "symbol": config.get("symbol", "AAPL"),
        "timeframe": config.get("timeframe", "1h"),
        "indicators": ["RSI_14", "EMA_20", "EMA_50"]
    },
    "timeframe": config.get("timeframe", "1h"),
    "risk_level": "medium",
    "tags": ["price_action", "rsi", "ema", "verified_bot"],
    "status": "active",
    "file_path": "Backtest/codes/algo9999999888877.py"
}

print("Checking if strategy already exists...")
print(f"\nStrategy Name: {strategy_data['name']}")
print(f"Description: {strategy_data['description']}")
print(f"File Path: {strategy_data['file_path']}")
print(f"Parameters: {json.dumps(strategy_data['parameters'], indent=2)}")

# Check if strategy ID already exists
existing_id = None
try:
    with open('algo9999999888877_strategy_id.txt', 'r') as f:
        existing_id = int(f.read().strip())
        print(f"\n📋 Found existing strategy ID: {existing_id}")
except FileNotFoundError:
    pass

try:
    # First, try to create new strategy
    if not existing_id:
        print("\n🔄 Creating new strategy...")
        response = requests.post(
            f"{API_URL}/strategies/",
            json=strategy_data,
            headers={"Content-Type": "application/json"}
        )
    else:
        # Try to update existing strategy
        print(f"\n🔄 Updating existing strategy ID {existing_id}...")
        response = requests.put(
            f"{API_URL}/strategies/{existing_id}/",
            json=strategy_data,
            headers={"Content-Type": "application/json"}
        )
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"\n✅ Strategy saved successfully!")
        print(f"Strategy ID: {result['id']}")
        print(f"Name: {result['name']}")
        print(f"Status: {result['status']}")
        print(f"Has Code: {bool(result.get('strategy_code'))}")
        
        # Save the ID for verification
        with open('algo9999999888877_strategy_id.txt', 'w') as f:
            f.write(str(result['id']))
        
        print(f"\nStrategy ID saved to: algo9999999888877_strategy_id.txt")
        print(f"\n✅ You can now test this strategy in the frontend!")
        print(f"   Strategy ID: {result['id']}")
        print(f"   Navigate to: http://localhost:5173/strategy")
        
    elif response.status_code == 400 and "unique" in response.text.lower():
        # Strategy exists but we don't have the ID, try to find it
        print(f"\n⚠️  Strategy already exists, searching for it...")
        search_response = requests.get(
            f"{API_URL}/strategies/",
            headers={"Content-Type": "application/json"}
        )
        
        if search_response.status_code == 200:
            strategies = search_response.json()
            results = strategies.get('results', strategies) if isinstance(strategies, dict) else strategies
            
            # Find strategy by name
            for strat in results:
                if strat['name'] == strategy_data['name']:
                    print(f"✅ Found existing strategy: ID {strat['id']}")
                    
                    # Update it with the code
                    print(f"🔄 Updating strategy {strat['id']} with code...")
                    update_response = requests.patch(
                        f"{API_URL}/strategies/{strat['id']}/",
                        json={"strategy_code": strategy_code, "status": "active"},
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if update_response.status_code in [200, 201]:
                        updated = update_response.json()
                        print(f"✅ Strategy updated successfully!")
                        print(f"   Has Code: {bool(updated.get('strategy_code'))}")
                        
                        # Save the ID
                        with open('algo9999999888877_strategy_id.txt', 'w') as f:
                            f.write(str(strat['id']))
                        
                        print(f"\n✅ Ready to test!")
                        print(f"   Strategy ID: {strat['id']}")
                        print(f"   Navigate to: http://localhost:5173/strategy")
                    else:
                        print(f"❌ Failed to update: {update_response.text}")
                    break
            else:
                print(f"❌ Could not find strategy with name: {strategy_data['name']}")
        else:
            print(f"❌ Failed to search strategies: {search_response.text}")
    else:
        print(f"\n❌ Failed to save strategy")
        print(f"Status: {response.status_code}")
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
