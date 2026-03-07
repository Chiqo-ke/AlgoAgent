"""
Test script to diagnose key rotation issue
"""
import os
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent / "Backtest"))

# Load environment
from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("KEY ROTATION DIAGNOSIS")
print("=" * 60)

# 1. Check environment variables
print("\n1. Environment Variables:")
print(f"   ENABLE_KEY_ROTATION = {os.getenv('ENABLE_KEY_ROTATION', 'NOT SET')}")
print(f"   Expected: 'true' (lowercase)")
print(f"   Actual check: {os.getenv('ENABLE_KEY_ROTATION', 'false').lower() == 'true'}")

# 2. Check Redis
print("\n2. Redis Connection:")
try:
    import redis
    print("   ✓ Redis module installed")
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    print(f"   Redis URL: {redis_url}")
    r = redis.from_url(redis_url, decode_responses=True)
    r.ping()
    print("   ✓ Redis connection successful")
except ImportError:
    print("   ✗ Redis module NOT installed")
except Exception as e:
    print(f"   ✗ Redis connection failed: {e}")

# 3. Check key_rotation module import
print("\n3. Key Rotation Module:")
try:
    from key_rotation import get_key_manager, KeyRotationError
    print("   ✓ key_rotation module imported successfully")
    KEY_ROTATION_AVAILABLE = True
except ImportError as e:
    print(f"   ✗ key_rotation import failed: {e}")
    KEY_ROTATION_AVAILABLE = False

print(f"   KEY_ROTATION_AVAILABLE = {KEY_ROTATION_AVAILABLE}")

# 4. Check keys.json file
print("\n4. Keys Configuration:")
keys_file = Path(__file__).parent / 'keys.json'
print(f"   Keys file path: {keys_file}")
print(f"   Keys file exists: {keys_file.exists()}")
if keys_file.exists():
    import json
    with open(keys_file) as f:
        keys_data = json.load(f)
    print(f"   Number of keys: {len(keys_data.get('keys', []))}")
    for key in keys_data.get('keys', []):
        print(f"      - {key.get('key_id')}: {key.get('model_name')} (active: {key.get('active', True)})")

# 5. Try to initialize KeyManager
print("\n5. KeyManager Initialization:")
if KEY_ROTATION_AVAILABLE:
    try:
        from key_rotation import KeyManager
        km = KeyManager()
        print(f"   ✓ KeyManager initialized")
        print(f"   Enabled: {km.enabled}")
        print(f"   Number of keys loaded: {len(km.keys)}")
        print(f"   Number of secrets loaded: {len(km.key_secrets)}")
        print(f"   Redis limiter: {km.redis_limiter is not None}")
        
        if not km.enabled:
            print("\n   ⚠️  KeyManager initialized but NOT ENABLED")
            print("   Checking why...")
            if km.redis_limiter is None:
                print("   → Redis limiter is None (Redis connection failed)")
    except Exception as e:
        print(f"   ✗ KeyManager initialization failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print("   ✗ Cannot test - key_rotation module not available")

# 6. Try to initialize GeminiStrategyGenerator
print("\n6. GeminiStrategyGenerator Initialization:")
try:
    sys.path.insert(0, str(Path(__file__).parent / "Backtest"))
    from gemini_strategy_generator import GeminiStrategyGenerator
    
    print(f"   Creating generator with use_key_rotation=True...")
    generator = GeminiStrategyGenerator(use_key_rotation=True)
    print(f"   ✓ Generator initialized")
    print(f"   use_key_rotation: {generator.use_key_rotation}")
    print(f"   selected_key_id: {generator.selected_key_id}")
    print(f"   key_manager: {generator.key_manager is not None}")
    
except Exception as e:
    print(f"   ✗ Generator initialization failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("DIAGNOSIS COMPLETE")
print("=" * 60)
