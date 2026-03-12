"""
Test if Django can load API keys from environment.
Diagnoses why keys aren't being detected by the running server.
"""
import os
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoagent_api.settings')

print("=" * 80)
print("DJANGO KEY LOADING DIAGNOSTIC")
print("=" * 80)

# Test 1: Check .env file locations
print("\n1. Checking .env file locations:")
root_env = Path(__file__).parent.parent / ".env"
monolithic_env = Path(__file__).parent / ".env"
print(f"   Root .env: {root_env} -> EXISTS: {root_env.exists()}")
print(f"   Monolithic .env: {monolithic_env} -> EXISTS: {monolithic_env.exists()}")

# Test 2: Load dotenv and check keys
print("\n2. Loading environment variables:")
from dotenv import load_dotenv

# Try loading from root
if root_env.exists():
    load_dotenv(dotenv_path=root_env, override=True)
    print(f"   Loaded from: {root_env}")
elif monolithic_env.exists():
    load_dotenv(dotenv_path=monolithic_env, override=True)
    print(f"   Loaded from: {monolithic_env}")
else:
    load_dotenv()
    print("   Loaded from default search")

# Test 3: Check what keys are visible
print("\n3. Checking visible API keys:")
gemini_keys = [k for k in os.environ if 'GEMINI_KEY' in k or (k.startswith('API_KEY') and 'gemini' in k.lower())]
print(f"   Found {len(gemini_keys)} Gemini-related keys")
for k in sorted(gemini_keys)[:10]:
    val = os.environ[k]
    safe = f"{val[:15]}..." if len(val) > 15 else val
    print(f"   - {k}: {safe}")

# Test 4: Check if key rotation is enabled
print("\n4. Checking key rotation config:")
enable_rotation = os.getenv('ENABLE_KEY_ROTATION', 'false')
print(f"   ENABLE_KEY_ROTATION: {enable_rotation}")

# Test 5: Try to initialize Django and check settings
print("\n5. Testing Django settings import:")
try:
    import django
    django.setup()
    from django.conf import settings
    print(f"   ✅ Django initialized successfully")
    print(f"   DEBUG: {settings.DEBUG}")
    print(f"   SECRET_KEY exists: {bool(settings.SECRET_KEY)}")
except Exception as e:
    print(f"   ⚠ Django initialization skipped: {e}")
    print("   (This is okay for key testing)")

# Test 6: Try to import and initialize GeminiStrategyGenerator
print("\n6. Testing GeminiStrategyGenerator:")
try:
    from Backtest.gemini_strategy_generator import GeminiStrategyGenerator
    
    # Try with key rotation
    try:
        gen = GeminiStrategyGenerator(use_key_rotation=True)
        print(f"   ✅ Generator initialized with key rotation")
        print(f"   Selected key: {gen.selected_key_id}")
        print(f"   Has API key: {bool(gen.api_key)}")
    except Exception as e:
        print(f"   ❌ Key rotation failed: {e}")
        
        # Try without key rotation
        try:
            gen = GeminiStrategyGenerator(use_key_rotation=False)
            print(f"   ✅ Generator initialized without key rotation")
            print(f"   Has API key: {bool(gen.api_key)}")
        except Exception as e2:
            print(f"   ❌ Fallback also failed: {e2}")
            
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    import traceback
    traceback.print_exc()

# Test 7: Check keys.json
print("\n7. Checking keys.json:")
keys_json = Path(__file__).parent / "keys.json"
if keys_json.exists():
    import json
    try:
        data = json.loads(keys_json.read_text())
        keys_count = len(data.get('keys', []))
        print(f"   ✅ keys.json exists with {keys_count} keys")
        for key_info in data.get('keys', [])[:3]:
            print(f"   - {key_info.get('key_id')}: {key_info.get('model_name')}")
    except Exception as e:
        print(f"   ❌ Error parsing keys.json: {e}")
else:
    print(f"   ⚠ keys.json not found at {keys_json}")

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)
