"""
Test the updated validator with SimBroker code
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "Backtest"))

from strategy_validator import StrategyValidator

# Read the algo1111000999 code
code_path = Path(__file__).parent / "Backtest" / "codes" / "algo1111000999.py"
with open(code_path, 'r') as f:
    strategy_code = f.read()

print("=" * 70)
print("TESTING VALIDATOR WITH SIMBROKER CODE")
print("=" * 70)

validator = StrategyValidator()

# Test component checking
print("\n1. Testing _check_required_components:")
errors = validator._check_required_components(strategy_code)
if errors:
    print(f"   [X] Found {len(errors)} errors:")
    for err in errors:
        print(f"     - {err}")
else:
    print("   [OK] No component errors found!")

# Test full validation
print("\n2. Testing full validation:")
result = validator.validate_strategy_code(
    strategy_code=strategy_code,
    strategy_name="algo1111000999",
    test_symbol="AAPL",
    test_period_days=365
)

print(f"   Valid: {result['valid']}")
print(f"   Errors: {len(result['errors'])}")
print(f"   Warnings: {len(result['warnings'])}")
print(f"   Trades: {result['trades_executed']}")

if result['errors']:
    print("\n   Errors found:")
    for err in result['errors']:
        print(f"     - {err}")

if result['warnings']:
    print("\n   Warnings:")
    for warn in result['warnings']:
        print(f"     - {warn}")

print("\n" + "=" * 70)
