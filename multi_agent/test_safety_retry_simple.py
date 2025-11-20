"""
Simple test to verify safety retry mechanism configuration.
Tests that Pro keys are available for retry when Flash keys hit safety filters.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
import json

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

print("=" * 70)
print("SAFETY RETRY MECHANISM - CONFIGURATION TEST")
print("=" * 70)

# Test 1: Check environment variables
print("\n1. Environment Configuration:")
print("-" * 70)

router_enabled = os.getenv('LLM_MULTI_KEY_ROUTER_ENABLED', 'false').lower() == 'true'
print(f"✓ Router Enabled: {router_enabled}")

redis_url = os.getenv('REDIS_URL', 'not set')
print(f"✓ Redis URL: {redis_url}")

# Test 2: Check keys.json
print("\n2. Keys Configuration:")
print("-" * 70)

keys_file = Path(__file__).parent / 'keys.json'
if keys_file.exists():
    with open(keys_file) as f:
        keys_data = json.load(f)
    
    flash_keys = [k for k in keys_data['keys'] if 'flash' in k.get('model_name', '').lower()]
    pro_keys = [k for k in keys_data['keys'] if 'pro' in k.get('model_name', '').lower()]
    
    print(f"✓ Total Keys: {len(keys_data['keys'])}")
    print(f"✓ Flash Keys (fast, may hit safety filters): {len(flash_keys)}")
    print(f"  - {', '.join([k['key_id'] for k in flash_keys])}")
    print(f"✓ Pro Keys (backup, more permissive): {len(pro_keys)}")
    print(f"  - {', '.join([k['key_id'] for k in pro_keys])}")
    
    if len(pro_keys) > 0:
        print("\n✅ Pro keys available for safety filter retry!")
    else:
        print("\n⚠️  No Pro keys configured - will fall back to template mode")
else:
    print("✗ keys.json not found")

# Test 3: Check API key environment variables
print("\n3. API Keys in Environment:")
print("-" * 70)

key_ids = ['gemini_flash_01', 'gemini_flash_02', 'gemini_flash_03', 
           'gemini_pro_01', 'gemini_pro_02']

available_keys = []
for key_id in key_ids:
    env_var = f"API_KEY_{key_id}"
    api_key = os.getenv(env_var)
    
    if api_key:
        masked = api_key[:10] + "..." + api_key[-4:] if len(api_key) > 14 else "***"
        print(f"  ✓ {env_var}: {masked}")
        available_keys.append(key_id)
    else:
        print(f"  ✗ {env_var}: NOT FOUND")

# Test 4: Check Redis connection
print("\n4. Redis Connection:")
print("-" * 70)

try:
    import redis
    r = redis.from_url(redis_url)
    r.ping()
    print("  ✓ Redis connected: SUCCESS")
except ImportError:
    print("  ⚠️  Redis library not installed: pip install redis")
except Exception as e:
    print(f"  ✗ Redis connection failed: {e}")

# Test 5: Verify retry configuration
print("\n5. Retry Configuration:")
print("-" * 70)

max_retries = os.getenv('LLM_MAX_RETRIES', '3')
base_backoff = os.getenv('LLM_BASE_BACKOFF_MS', '500')

print(f"✓ Max Retries: {max_retries}")
print(f"✓ Base Backoff: {base_backoff}ms")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

all_checks = [
    router_enabled,
    len(available_keys) >= 3,
    len([k for k in available_keys if 'pro' in k]) > 0
]

if all(all_checks):
    print("✅ System configured for safety retry with Pro keys")
    print("\nRetry Flow:")
    print("  1. Request → Flash key (fast)")
    print("  2. Safety filter triggered → Retry with Pro key (more permissive)")
    print("  3. Pro fails → Fall back to template mode")
    print("\nTest it with: cd multi_agent && python cli.py")
else:
    print("⚠️  Configuration incomplete:")
    if not router_enabled:
        print("  - Enable router: Set LLM_MULTI_KEY_ROUTER_ENABLED=true")
    if len(available_keys) < 3:
        print("  - Add more API keys to .env")
    if len([k for k in available_keys if 'pro' in k]) == 0:
        print("  - Add at least one Pro key for safety retry")

print()
