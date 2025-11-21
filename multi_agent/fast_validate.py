"""Fast validation - checks files exist and syntax is valid."""
import sys
import py_compile
from pathlib import Path

print("="*70)
print("FAST VALIDATION (No Test Execution)")
print("="*70)
print()

# Find strategy files
strategies_dir = Path(__file__).parent / "Backtest" / "codes"
test_dir = Path(__file__).parent / "tests"

strategy_files = list(strategies_dir.glob("ai_strategy_*.py"))
print(f"✓ Found {len(strategy_files)} strategy files")

passed = 0
failed = 0

for strategy_file in strategy_files:
    strategy_name = strategy_file.stem
    test_file = test_dir / f"test_{strategy_name}.py"
    
    print(f"\n📄 {strategy_name}")
    print(f"   Strategy: {strategy_file.name}")
    print(f"   Test: {test_file.name if test_file.exists() else 'NOT FOUND'}")
    
    # Check test file exists
    if not test_file.exists():
        print(f"   ⚠️  Test file missing")
        continue
    
    # Validate Python syntax
    try:
        py_compile.compile(str(strategy_file), doraise=True)
        print(f"   ✓ Strategy syntax valid")
    except py_compile.PyCompileError as e:
        print(f"   ❌ Strategy syntax error: {e}")
        failed += 1
        continue
    
    try:
        py_compile.compile(str(test_file), doraise=True)
        print(f"   ✓ Test syntax valid")
        passed += 1
    except py_compile.PyCompileError as e:
        print(f"   ❌ Test syntax error: {e}")
        failed += 1

print(f"\n{'='*70}")
print(f"SUMMARY")
print(f"{'='*70}")
print(f"Total: {passed + failed}")
print(f"Valid: {passed} ✅")
print(f"Invalid: {failed} ❌")
print()

sys.exit(0 if failed == 0 else 1)
