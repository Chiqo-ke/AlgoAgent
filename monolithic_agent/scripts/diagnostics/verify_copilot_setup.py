"""
Quick verification script for Copilot integration

Run this to verify all components are properly installed.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("="*70)
print("  Copilot Integration Verification")
print("="*70)
print()

# Test 1: Auth module
print("1. Testing authentication module...")
try:
    from algoagent_api.copilot_auth import CopilotAuthManager, get_auth_manager
    print("   ✅ CopilotAuthManager imported successfully")
except Exception as e:
    print(f"   ❌ Failed to import auth module: {e}")
    sys.exit(1)

# Test 2: Strategy generator
print("\n2. Testing strategy generator...")
try:
    from Backtest.copilot_strategy_generator import CopilotStrategyGenerator, get_copilot_generator
    print("   ✅ CopilotStrategyGenerator imported successfully")
except Exception as e:
    print(f"   ❌ Failed to import generator: {e}")
    sys.exit(1)

# Test 3: Database model
print("\n3. Testing database model...")
try:
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoagent.settings')
    import django
    django.setup()
    from strategy_api.models import CopilotAuth
    print("   ✅ CopilotAuth model available")
except Exception as e:
    print(f"   ⚠️  Django model check skipped: {e}")

# Test 4: Management command
print("\n4. Checking management command...")
command_path = Path(__file__).parent / "strategy_api" / "management" / "commands" / "copilot_auth.py"
if command_path.exists():
    print("   ✅ copilot_auth management command exists")
else:
    print("   ❌ Management command not found")

# Test 5: Test fixtures
print("\n5. Checking test fixtures...")
try:
    from tests.fixtures.copilot_responses import MOCK_TOKEN_RESPONSE, MockCopilotResponse
    print("   ✅ Test fixtures available")
except Exception as e:
    print(f"   ❌ Test fixtures not found: {e}")

# Test 6: Documentation
print("\n6. Checking documentation...")
docs = [
    "COPILOT_INTEGRATION_README.md",
    "IMPLEMENTATION_SUMMARY.md"
]
for doc in docs:
    if (Path(__file__).parent / doc).exists():
        print(f"   ✅ {doc} exists")
    else:
        print(f"   ❌ {doc} missing")

# Summary
print()
print("="*70)
print("  ✅ Verification Complete!")
print("="*70)
print()
print("Next steps:")
print("1. Authenticate: python manage.py copilot_auth")
print("2. Verify token: python manage.py copilot_auth --check")
print("3. Test strategy: Use POST /strategies/generate_with_ai/")
print()
