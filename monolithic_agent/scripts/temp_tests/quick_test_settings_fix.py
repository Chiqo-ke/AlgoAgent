"""Quick test to verify settings.py now loads .env correctly"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoagent_api.settings')

print("Testing settings.py with load_dotenv fix...")
print(f"CWD: {Path.cwd()}")

# This import triggers settings.py which should now call load_dotenv
from django.conf import settings

keys = [k for k in os.environ if 'GEMINI_KEY' in k or (k.startswith('API_KEY') and 'gemini' in k.lower())]
print(f"\n✅ Keys loaded: {len(keys)}")
for k in sorted(keys)[:8]:
    val = os.environ[k]
    print(f"  {k}: {val[:20]}...")

if len(keys) >= 10:
    print("\n✅ SUCCESS: settings.py now loads .env correctly!")
else:
    print(f"\n❌ FAIL: Only {len(keys)} keys loaded (expected 10+)")
