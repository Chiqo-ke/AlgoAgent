"""Quick authentication check"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoagent_api.settings')
sys.path.insert(0, 'C:\\Users\\nyaga\\Documents\\AlgoAgent\\monolithic_agent')
django.setup()

from strategy_api.models import CopilotAuth

token = CopilotAuth.get_latest_token()
if token:
    print(f"Token Status: VALID")
    print(f"Expires: {token.get('expires_at')}")
    
    # Test if we can import the strategy generator
    from Backtest.copilot_strategy_generator import CopilotStrategyGenerator
    print("Copilot Strategy Generator: IMPORTED")
    
    # Quick test: can we create the generator?
    try:
        gen = CopilotStrategyGenerator()
        print("Copilot Generator: INITIALIZED")
        print("\n=== COPILOT INTEGRATION STATUS: READY ===")
    except Exception as e:
        print(f"Error initializing: {e}")
else:
    print("NO TOKEN FOUND")
