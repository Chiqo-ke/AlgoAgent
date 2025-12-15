"""
API Key Configuration Diagnostic Script
========================================

Checks current API key configuration and tests if rotation is properly enabled.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

print("=" * 80)
print("API KEY CONFIGURATION DIAGNOSTIC")
print("=" * 80)
print()

# Check key rotation setting
enable_rotation = os.getenv('ENABLE_KEY_ROTATION', 'false').lower() == 'true'
print(f"1. ENABLE_KEY_ROTATION: {os.getenv('ENABLE_KEY_ROTATION')} (Parsed as: {enable_rotation})")
print()

# Check single API key
single_key = os.getenv('GEMINI_API_KEY')
if single_key:
    print(f"2. GEMINI_API_KEY: SET ({single_key[:15]}...{single_key[-4:]})")
else:
    print("2. GEMINI_API_KEY: NOT SET")
print()

# Check for multiple keys in environment
gemini_keys = [k for k in os.environ if 'GEMINI_KEY' in k or 'API_KEY_gemini' in k]
print(f"3. Multiple Keys in .env: {len(gemini_keys)} keys found")
if gemini_keys:
    for key_name in gemini_keys[:10]:
        key_value = os.getenv(key_name)
        if key_value:
            print(f"   - {key_name}: {key_value[:15]}...{key_value[-4:]}")
        else:
            print(f"   - {key_name}: NOT SET")
print()

# Check keys.json
keys_json_path = Path(__file__).parent / "keys.json"
if keys_json_path.exists():
    import json
    with open(keys_json_path, 'r') as f:
        keys_config = json.load(f)
    
    print(f"4. keys.json Configuration: {len(keys_config.get('keys', []))} keys defined")
    
    # Check if secrets are mapped
    api_keys = keys_config.get('api_keys', {})
    secrets = keys_config.get('secrets', {})
    
    for key in keys_config.get('keys', []):
        key_id = key.get('key_id')
        model = key.get('model_name', 'unknown')
        rpm = key.get('rpm', 'N/A')
        
        # Check if secret is available
        secret_name = f"GEMINI_KEY_{key_id}" or f"API_KEY_gemini_{key_id}"
        has_secret = os.getenv(f"GEMINI_KEY_{key_id}") or os.getenv(f"API_KEY_gemini_{key_id}")
        
        status = "✅ SECRET FOUND" if has_secret else "❌ SECRET MISSING"
        print(f"   - {key_id} ({model}, {rpm} RPM): {status}")
else:
    print("4. keys.json: NOT FOUND")
print()

# Try to initialize key manager
print("5. Testing Key Rotation System:")
try:
    # Add Backtest directory to path
    backtest_dir = Path(__file__).parent / "Backtest"
    if backtest_dir not in sys.path:
        sys.path.insert(0, str(backtest_dir))
    
    from Backtest.key_rotation import get_key_manager
    
    manager = get_key_manager()
    print("   ✅ KeyManager initialized successfully")
    
    # Try to select a key
    key_info = manager.select_key(model_preference='gemini-2.0-flash')
    if key_info:
        print(f"   ✅ Key selected: {key_info['key_id']} (model: {key_info.get('model', 'N/A')})")
    else:
        print("   ❌ No key could be selected")
    
    # Check health
    health = manager.get_health_status()
    print(f"   ℹ️  Health monitoring: {len(health)} keys tracked")
    
except Exception as e:
    print(f"   ❌ Key rotation system error: {e}")
    import traceback
    print(f"   Details: {traceback.format_exc()[:200]}")
print()

# Test GeminiStrategyGenerator
print("6. Testing GeminiStrategyGenerator:")
try:
    # Add Backtest directory to path if not already there
    backtest_dir = Path(__file__).parent / "Backtest"
    if str(backtest_dir) not in sys.path:
        sys.path.insert(0, str(backtest_dir))
    
    from Backtest.gemini_strategy_generator import GeminiStrategyGenerator
    
    generator = GeminiStrategyGenerator(use_key_rotation=enable_rotation)
    print(f"   ✅ Generator initialized")
    print(f"   - use_key_rotation: {generator.use_key_rotation}")
    print(f"   - selected_key_id: {generator.selected_key_id}")
    print(f"   - key_manager: {'Enabled' if generator.key_manager else 'Disabled'}")
    
except Exception as e:
    print(f"   ❌ Generator initialization error: {e}")
    import traceback
    print(f"   Details: {traceback.format_exc()[:200]}")
print()

print("=" * 80)
print("DIAGNOSIS COMPLETE")
print("=" * 80)
print()

# Provide recommendations
print("RECOMMENDATIONS:")
print()

if not enable_rotation:
    print("⚠️  Key rotation is DISABLED")
    print("   To enable: Set ENABLE_KEY_ROTATION=true in .env")
    print()

if len(gemini_keys) == 0:
    print("⚠️  No multiple keys found in .env")
    print("   Keys should be named like: GEMINI_KEY_flash_01, GEMINI_KEY_flash_02, etc.")
    print()

if not keys_json_path.exists():
    print("⚠️  keys.json file not found")
    print("   Copy keys_example.json to keys.json and configure it")
    print()

missing_secrets = []
if keys_json_path.exists():
    import json
    with open(keys_json_path, 'r') as f:
        keys_config = json.load(f)
    
    for key in keys_config.get('keys', []):
        key_id = key.get('key_id')
        if not os.getenv(f"GEMINI_KEY_{key_id}") and not os.getenv(f"API_KEY_gemini_{key_id}"):
            missing_secrets.append(key_id)

if missing_secrets:
    print(f"⚠️  {len(missing_secrets)} keys defined in keys.json but secrets missing in .env:")
    for key_id in missing_secrets:
        print(f"   - Add GEMINI_KEY_{key_id}=<your-api-key> to .env")
    print()

# CRITICAL: Check if all keys are from same project
if len(gemini_keys) > 0:
    print()
    print("⚠️  CRITICAL CHECK: Are your API keys from DIFFERENT Google Cloud Projects?")
    print()
    print("   If all keys are from the SAME project, they share quotas!")
    print("   This means rotation won't help - they all hit the same limits.")
    print()
    print("   To verify:")
    print("   1. Go to: https://aistudio.google.com/apikey")
    print("   2. Check which project each key belongs to")
    print("   3. If they're all from one project, you need keys from different projects")
    print()
    print("   Solution: Create API keys in multiple different Google Cloud projects")
    print()
