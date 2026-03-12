"""
Test complete Django startup with key loading
"""
import os
import sys
from pathlib import Path

print("=" * 70)
print("COMPLETE DJANGO STARTUP TEST WITH KEY ROTATION")
print("=" * 70)

# Step 1: Check environment before any imports
print("\n1. Environment BEFORE Django import:")
gemini_keys_before = [k for k in os.environ.keys() if 'GEMINI' in k.upper()]
print(f"   Keys found: {len(gemini_keys_before)}")

# Step 2: Import Django settings (triggers settings.py dotenv loading)
sys.path.insert(0, '.')
print("\n2. Importing Django settings...")
try:
    from algoagent_api import settings
    print("   ✅ Django settings imported successfully")
except Exception as e:
    print(f"   ❌ Failed to import settings: {e}")
    sys.exit(1)

# Step 3: Check environment after settings import
print("\n3. Environment AFTER Django import:")
gemini_keys_after = [k for k in os.environ.keys() if 'GEMINI' in k.upper()]
print(f"   Keys found: {len(gemini_keys_after)}")
print(f"   ENABLE_KEY_ROTATION: {os.getenv('ENABLE_KEY_ROTATION')}")

# Step 4: Try to initialize key rotation system
print("\n4. Testing KeyManager initialization:")
try:
    from Backtest.key_rotation import get_key_manager
    key_manager = get_key_manager()
    print(f"   ✅ KeyManager initialized")
    print(f"   Enabled: {key_manager.enabled}")
    print(f"   Keys loaded: {len(key_manager.keys)}")
    print(f"   Secrets loaded: {len(key_manager.key_secrets)}")
    
    # List keys
    print("\n   Key Details:")
    for key_id, metadata in key_manager.keys.items():
        has_secret = '✅' if key_id in key_manager.key_secrets else '❌'
        print(f"     {has_secret} {key_id}: {metadata.model_name}")
    
except Exception as e:
    print(f"   ❌ KeyManager initialization failed: {e}")
    import traceback
    traceback.print_exc()

# Step 5: Try to select a key
print("\n5. Testing key selection:")
try:
    from Backtest.key_rotation import get_key_manager
    key_manager = get_key_manager()
    
    # Try gemini-2.0-flash (what keys.json has)
    key_info = key_manager.select_key(
        model_preference='gemini-2.0-flash',
        tokens_needed=1000
    )
    
    if key_info:
        print(f"   ✅ Selected key: {key_info['key_id']}")
        print(f"   Model: {key_info['model_name']}")
        print(f"   Has secret: {'✅' if key_info.get('secret') else '❌'}")
    else:
        print("   ❌ No key selected")
    
except Exception as e:
    print(f"   ❌ Key selection failed: {e}")
    import traceback
    traceback.print_exc()

# Step 6: Try to initialize GeminiStrategyGenerator
print("\n6. Testing GeminiStrategyGenerator:")
try:
    from Backtest.gemini_strategy_generator import GeminiStrategyGenerator
    generator = GeminiStrategyGenerator(use_key_rotation=True)
    print(f"   ✅ Generator initialized")
    print(f"   Using key rotation: {generator.use_key_rotation}")
    print(f"   Selected key: {generator.selected_key_id}")
    
except Exception as e:
    print(f"   ❌ Generator initialization failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
