"""
Refresh GitHub Copilot Authentication
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoagent_api.settings')

import django
django.setup()

from algoagent_api.copilot_auth import get_auth_manager

def main():
    print("\n🔐 GitHub Copilot Authentication")
    print("=" * 50)
    
    manager = get_auth_manager()
    
    # Check current token
    print("\n📋 Checking current token status...")
    try:
        current_token = manager.get_valid_token()
        if current_token:
            print(f"✅ Current token is valid!")
            print("\nNo re-authentication needed.")
            return
    except Exception as e:
        print(f"❌ No valid token found: {e}")
    
    # Start authentication
    print("\n🔄 Starting authentication flow...")
    try:
        result = manager.authenticate()
        
        if result.get('success'):
            print("\n✅ Authentication successful!")
            print(f"   Token expires at: {result.get('expires_at')}")
            print(f"   Scopes: {result.get('scope', 'N/A')}")
            
            # Test the token
            print("\n🧪 Testing token with Copilot API...")
            from Backtest.copilot_strategy_generator import CopilotStrategyGenerator
            generator = CopilotStrategyGenerator()
            
            test_response = generator._call_copilot_api(
                "Generate a simple 'Hello World' comment",
                max_tokens=50
            )
            
            if test_response:
                print("✅ Token works! Copilot API responded:")
                print(f"   {test_response[:100]}...")
            else:
                print("⚠️  Token saved but API test failed")
        else:
            print("\n❌ Authentication failed!")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"\n❌ Error during authentication: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
