"""
Quick test to verify Strategy module imports work correctly
"""
import sys
from pathlib import Path

# Add paths like Django does
PARENT_DIR = Path(__file__).parent
STRATEGY_DIR = PARENT_DIR / "Strategy"

if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))
if str(STRATEGY_DIR) not in sys.path:
    sys.path.insert(0, str(STRATEGY_DIR))

print("Testing imports...")
print(f"Parent dir: {PARENT_DIR}")
print(f"Strategy dir: {STRATEGY_DIR}")
print(f"Strategy dir exists: {STRATEGY_DIR.exists()}")

try:
    print("\n1. Testing StrategyValidatorBot import...")
    from Strategy.strategy_validator import StrategyValidatorBot
    print("   ✓ StrategyValidatorBot imported successfully")
    
    print("\n2. Testing StrategyValidatorBot initialization...")
    bot = StrategyValidatorBot(username="test_user")
    print("   ✓ StrategyValidatorBot initialized successfully")
    
    print("\n3. Testing a simple validation...")
    result = bot.process_input("Buy when RSI < 30, sell when RSI > 70", "freetext")
    print(f"   ✓ Validation completed with status: {result.get('status')}")
    
    if result.get('status') == 'success':
        print(f"   ✓ Confidence: {result.get('confidence')}")
        print(f"   ✓ Steps: {len(result.get('canonicalized_steps', []))}")
        print("\n✅ ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print(f"   ⚠ Validation status: {result.get('status')}")
        print(f"   Message: {result.get('message')}")
        sys.exit(1)
        
except ImportError as e:
    print(f"\n❌ Import Error: {e}")
    print("\nPython path:")
    for p in sys.path[:5]:
        print(f"  - {p}")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
