"""Simple script to run E2E test and capture output"""
import sys
import subprocess
from pathlib import Path

# Run the strategy file
strategy_file = Path(__file__).parent / "Backtest" / "codes" / "e2e_test_strategy_20260120_231456.py"

print("="*80)
print("RUNNING E2E TEST STRATEGY")
print("="*80)
print(f"Strategy file: {strategy_file}")
print()

result = subprocess.run(
    [sys.executable, str(strategy_file)],
    capture_output=True,
    text=True,
    timeout=60
)

print("STDOUT:")
print(result.stdout)
print()
print("STDERR:")
print(result.stderr)
print()
print(f"Return code: {result.returncode}")

if result.returncode == 0:
    # Check for trades in output
    if "Total Trades:" in result.stdout:
        import re
        match = re.search(r'Total Trades:\s+(\d+)', result.stdout)
        if match:
            num_trades = int(match.group(1))
            print()
            print("="*80)
            if num_trades >= 1:
                print("PASSED: Strategy executed", num_trades, "trade(s)")
            else:
                print("FAILED: No trades executed")
            print("="*80)
    else:
        print("Could not find trade information in output")
else:
    print("Strategy execution failed")
