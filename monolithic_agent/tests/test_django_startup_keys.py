"""
Test Django server startup with API key loading.
Simulates exactly what happens when Django starts.
"""
import os
import sys
from pathlib import Path

print("=" * 80)
print("DJANGO SERVER STARTUP API KEY TEST")
print("=" * 80)

# Step 1: Simulate Django startup WITHOUT dotenv
print("\n1. Current working directory:")
print(f"   {Path.cwd()}")

print("\n2. Environment before any loading:")
gemini_keys_before = [k for k in os.environ if 'GEMINI' in k or (k.startswith('API_KEY') and 'gemini' in k.lower())]
print(f"   Gemini keys visible: {len(gemini_keys_before)}")

# Step 3: Set Django settings and see if keys appear
print("\n3. Setting DJANGO_SETTINGS_MODULE:")
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoagent_api.settings')
print("   ✅ DJANGO_SETTINGS_MODULE set")

# Step 4: Import settings and check
print("\n4. Importing Django settings (WITHOUT load_dotenv):")
try:
    from django.conf import settings
    print("   ✅ Settings imported")
    gemini_keys_after = [k for k in os.environ if 'GEMINI' in k or (k.startswith('API_KEY') and 'gemini' in k.lower())]
    print(f"   Gemini keys visible: {len(gemini_keys_after)}")
except Exception as e:
    print(f"   ❌ Import failed: {e}")

# Step 5: NOW load dotenv and check difference
print("\n5. NOW loading .env explicitly:")
from dotenv import load_dotenv
root_env = Path(__file__).parent.parent / ".env"
if root_env.exists():
    load_dotenv(dotenv_path=root_env, override=True)
    print(f"   ✅ Loaded from {root_env}")
else:
    load_dotenv()
    print("   ⚠ Loaded from default search")

gemini_keys_final = [k for k in os.environ if 'GEMINI' in k or (k.startswith('API_KEY') and 'gemini' in k.lower())]
print(f"   Gemini keys NOW visible: {len(gemini_keys_final)}")
for k in sorted(gemini_keys_final)[:5]:
    val = os.environ[k]
    print(f"   - {k}: {val[:15]}...")

# Step 6: Try to initialize GeminiStrategyGenerator
print("\n6. Testing GeminiStrategyGenerator AFTER manual dotenv load:")
try:
    from Backtest.gemini_strategy_generator import GeminiStrategyGenerator
    gen = GeminiStrategyGenerator(use_key_rotation=True)
    print(f"   ✅ Generator initialized")
    print(f"   Selected key: {gen.selected_key_id}")
    print(f"   Has API key: {bool(gen.api_key)}")
except Exception as e:
    print(f"   ❌ Failed: {e}")

print("\n" + "=" * 80)
print("CONCLUSION:")
print("=" * 80)
print("settings.py does NOT call load_dotenv()!")
print("This is why Django server can't see API keys even after restart.")
print("\nFIX: Add load_dotenv() at the TOP of settings.py")
print("=" * 80)
