"""
Quick test to verify KeyManager and GeminiStrategyGenerator integration
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoagent_api.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

print("=" * 70)
print("TESTING KEY MANAGER AND GEMINI INTEGRATION")
print("=" * 70)

# Test 1: Import and initialize KeyManager
try:
    from Backtest.key_rotation import get_key_manager
    km = get_key_manager()
    print(f"\n✓ KeyManager initialized")
    print(f"  - Keys loaded: {len(km.keys)}")
    print(f"  - Secrets loaded: {len(km.key_secrets)}")
    print(f"  - Rotation enabled: {km.enabled}")
except Exception as e:
    print(f"\n✗ KeyManager failed: {e}")
    sys.exit(1)

# Test 2: Select a key
try:
    key_info = km.select_key(model_preference='gemini-2.0-flash')
    if key_info:
        print(f"\n✓ Key selection successful")
        print(f"  - Selected key ID: {key_info['key_id']}")
        print(f"  - Provider: {key_info['provider']}")
        print(f"  - Model: {key_info['model']}")
    else:
        print(f"\n✗ No key available")
        sys.exit(1)
except Exception as e:
    print(f"\n✗ Key selection failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Initialize Gemini model
try:
    import google.generativeai as genai
    genai.configure(api_key=key_info['secret'])
    model = genai.GenerativeModel('gemini-2.0-flash')
    print(f"\n✓ Gemini model configured successfully")
except Exception as e:
    print(f"\n✗ Gemini configuration failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Initialize GeminiStrategyGenerator
try:
    from Backtest.gemini_strategy_generator import GeminiStrategyGenerator
    generator = GeminiStrategyGenerator(model=model)
    print(f"\n✓ GeminiStrategyGenerator initialized")
except Exception as e:
    print(f"\n✗ GeminiStrategyGenerator failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Simple generation test (optional - will use API quota)
try:
    print(f"\n✓ Testing simple code generation...")
    result = generator.generate_strategy(
        description="A simple moving average crossover strategy",
        strategy_name="TestStrategy"
    )
    if result and len(result) > 100:
        print(f"✓ Code generation successful ({len(result)} characters)")
    else:
        print(f"⚠ Code generation returned short result: {len(result) if result else 0} characters")
except Exception as e:
    print(f"\n⚠ Code generation test skipped or failed: {e}")

print("\n" + "=" * 70)
print("ALL CRITICAL TESTS PASSED ✓")
print("=" * 70)
