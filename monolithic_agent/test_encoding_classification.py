"""
Test encoding error classification bug
"""

from Backtest.bot_error_fixer import ErrorAnalyzer

# This is the actual error from the logs
test_error_stdout = """[OK] Strategy initialized: Algo34567545676789
"""

test_error_stderr = """c:\\Users\\nyaga\\Documents\\AlgoAgent\\.venv\\lib\\site-packages\\google\\api_core\\_python_version_support.py:266: FutureWarning: You are using a Python version (3.10.11) which Google will stop supporting in new releases of google.api_core once it reaches its end of life (2026-10-04). Please upgrade to the latest Python version, or at least Python 3.11, to continue receiving updates for google.api_core past that date.
  warnings.warn(message, FutureWarning)
Traceback (most recent call last):
  File "C:\\Users\\nyaga\\Documents\\AlgoAgent\\monolithic_agent\\Backtest\\codes\\algo34567545676789.py", line 377, in <module>
    metrics = run_backtest(symbol="AAPL", period="6mo", interval="1d")
  File "C:\\Users\\nyaga\\Documents\\AlgoAgent\\monolithic_agent\\Backtest\\codes\\algo34567545676789.py", line 287, in run_backtest
    print(f"[\\U0001f504] Loading data in STREAMING mode (sequential)...")
  File "C:\\Users\\nyaga\\AppData\\Local\\Programs\\Python\\Python310\\lib\\encodings\\cp1252.py", line 19, in encode
    return codecs.charmap_encode(input,self.errors,encoding_table)[0]
UnicodeEncodeError: 'charmap' codec can't encode character '\\U0001f504' in position 1: character maps to <undefined>
"""

print("=" * 70)
print("TEST 1: Classification with ONLY stdout (current bug)")
print("=" * 70)
error_type, desc, severity = ErrorAnalyzer.classify_error(test_error_stdout)
print(f"Result: {error_type} - {desc} (severity: {severity})")
print(f"Expected: encoding_error")
print(f"Status: {'✓ PASS' if error_type == 'encoding_error' else '✗ FAIL'}")

print("\n" + "=" * 70)
print("TEST 2: Classification with ONLY stderr (should work)")
print("=" * 70)
error_type, desc, severity = ErrorAnalyzer.classify_error(test_error_stderr)
print(f"Result: {error_type} - {desc} (severity: {severity})")
print(f"Expected: encoding_error")
print(f"Status: {'✓ PASS' if error_type == 'encoding_error' else '✗ FAIL'}")

print("\n" + "=" * 70)
print("TEST 3: Classification with stdout + stderr (should work)")
print("=" * 70)
combined = test_error_stdout + "\n" + test_error_stderr
error_type, desc, severity = ErrorAnalyzer.classify_error(combined)
print(f"Result: {error_type} - {desc} (severity: {severity})")
print(f"Expected: encoding_error")
print(f"Status: {'✓ PASS' if error_type == 'encoding_error' else '✗ FAIL'}")

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)
print("The bug: bot_error_fixer.py only receives STDOUT in output_log")
print("The error message is in STDERR, so classification fails")
print("Fix: Store and pass stderr to the error fixer")
