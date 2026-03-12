"""
Verify the fix for encoding error detection
"""

from Backtest.bot_executor import BotExecutionResult
from Backtest.bot_error_fixer import ErrorAnalyzer
from datetime import datetime

print("=" * 70)
print("SIMULATING BotExecutionResult with stderr_log")
print("=" * 70)

# Simulate what the executor now stores
result = BotExecutionResult(
    strategy_name="test_algo",
    file_path="/path/to/algo.py",
    execution_timestamp=datetime.now(),
    success=False,
    duration_seconds=10.0,
    output_log="[OK] Strategy initialized: Algo34567545676789\n",
    stderr_log="""Traceback (most recent call last):
  File "algo.py", line 287, in run_backtest
    print(f"[\\U0001f504] Loading data...")
  File "cp1252.py", line 19, in encode
    return codecs.charmap_encode(input,self.errors,encoding_table)[0]
UnicodeEncodeError: 'charmap' codec can't encode character '\\U0001f504' in position 1: character maps to <undefined>
"""
)

print(f"output_log length: {len(result.output_log)} chars")
print(f"stderr_log length: {len(result.stderr_log)} chars")

# Simulate what bot_error_fixer now does
output_log = result.output_log or ""
stderr_log = result.stderr_log or ""
combined_output = output_log + "\\n" + stderr_log

print(f"\\nCombined output length: {len(combined_output)} chars")
print(f"\\nClassifying error from combined output...")

error_type, desc, severity = ErrorAnalyzer.classify_error(combined_output)

print(f"\\nResult: {error_type}")
print(f"Description: {desc}")
print(f"Severity: {severity}")
print(f"\\n{'✓ SUCCESS' if error_type == 'encoding_error' else '✗ FAILED'}")

# Check if encoding hint would be triggered
if error_type == 'encoding_error' or 'charmap' in combined_output.lower():
    print("\\n✓ Encoding hint would be provided to AI")
else:
    print("\\n✗ No encoding hint would be provided")
