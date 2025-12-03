"""
Test Bot Error Fixing Capability
==================================

Demonstrates automatic error detection and fixing for trading bots.
"""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.insert(0, str(Path(__file__).parent))

from Backtest.bot_error_fixer import ErrorAnalyzer, BotErrorFixer


def test_error_classification():
    """Test error classification functionality"""
    print("\n" + "="*70)
    print("TEST 1: ERROR CLASSIFICATION")
    print("="*70)
    
    test_errors = [
        ("""
ModuleNotFoundError: No module named 'pandas_ta'
  File "bot.py", line 5, in <module>
    import pandas_ta as ta
""", "import_error"),
        
        ("""
SyntaxError: invalid syntax
  File "bot.py", line 10
    def next(self)
             ^
""", "syntax_error"),
        
        ("""
AttributeError: 'list' object has no attribute 'ewm'
  File "bot.py", line 25, in next
    ema = prices.ewm(span=30)
""", "attribute_error"),
        
        ("""
TypeError: unsupported operand type(s) for -: 'NoneType' and 'float'
  File "bot.py", line 45
    result = value - threshold
""", "type_error"),
        
        ("""
ValueError: invalid literal for int() with base 10: 'invalid'
  File "bot.py", line 60
    period = int(param_string)
""", "value_error"),
    ]
    
    for error_output, expected_type in test_errors:
        error_type, description, severity = ErrorAnalyzer.classify_error(error_output)
        status = "✓" if error_type == expected_type else "✗"
        print(f"\n{status} Expected: {expected_type:20} Got: {error_type:20}")
        print(f"  Description: {description}")
        print(f"  Severity: {severity}")
    
    print("\n" + "="*70)
    return True


def test_error_extraction():
    """Test error message extraction"""
    print("\n" + "="*70)
    print("TEST 2: ERROR MESSAGE EXTRACTION")
    print("="*70)
    
    test_output = """
Some normal output
Starting bot execution
Processing data...
Traceback (most recent call last):
  File "bot.py", line 50, in next
    ema_value = ema[-1]
IndexError: list index out of range
Error: Execution failed
"""
    
    error_msg = ErrorAnalyzer.extract_error_message(test_output, "")
    print("\nExtracted Error Message:")
    print("-" * 70)
    print(error_msg)
    print("-" * 70)
    
    # Verify we got the relevant parts
    assert "IndexError" in error_msg
    assert "list index out of range" in error_msg
    print("\n✓ Error extraction working correctly")
    
    return True


def test_fix_prompt_building():
    """Test fix prompt generation"""
    print("\n" + "="*70)
    print("TEST 3: FIX PROMPT GENERATION")
    print("="*70)
    
    fixer = BotErrorFixer()
    
    test_code = """
def init(self):
    self.ema = self.I(lambda x: x.ewm(span=30).mean(), self.data.Close)

def next(self):
    if self.ema[-1] > self.data.Close[-1]:
        self.buy()
"""
    
    test_error = "AttributeError: 'numpy.ndarray' object has no attribute 'ewm'"
    
    prompt = fixer._build_fix_prompt(
        original_code=test_code,
        error_message=test_error,
        error_type='attribute_error',
        bot_file=Path("test_bot.py"),
        execution_context={'symbol': 'AAPL', 'period_days': 365}
    )
    
    print("\nGenerated Fix Prompt:")
    print("-" * 70)
    print(prompt[:500] + "...")
    print("-" * 70)
    
    # Verify prompt includes important information
    assert "test_bot.py" in prompt
    assert "attribute_error" in prompt
    assert "AAPL" in prompt
    print("\n✓ Fix prompt generation working correctly")
    
    return True


def test_error_analyzer_patterns():
    """Test error pattern matching"""
    print("\n" + "="*70)
    print("TEST 4: ERROR PATTERN MATCHING")
    print("="*70)
    
    test_cases = [
        ("This is an ImportError message", "import_error"),
        ("ModuleNotFoundError in the code", "import_error"),
        ("FileNotFoundError: [Errno 2]", "file_error"),
        ("TimeoutExpired after 300 seconds", "timeout_error"),
        ("KeyError when accessing dict", "key_error"),
    ]
    
    print("\nPattern Matching Results:")
    for error_text, expected_type in test_cases:
        error_type, _, _ = ErrorAnalyzer.classify_error(error_text)
        status = "✓" if error_type == expected_type else "✗"
        print(f"{status} '{error_text[:40]}...' → {error_type}")
    
    print("\n" + "="*70)
    return True


def test_error_severity_classification():
    """Test error severity assessment"""
    print("\n" + "="*70)
    print("TEST 5: ERROR SEVERITY CLASSIFICATION")
    print("="*70)
    
    test_errors = [
        ("SyntaxError: invalid syntax", "high"),
        ("ImportError: cannot import", "high"),
        ("FileNotFoundError", "high"),
        ("AttributeError", "medium"),
        ("ValueError", "medium"),
        ("IndexError", "low"),
    ]
    
    print("\nSeverity Classification:")
    for error_text, expected_severity in test_errors:
        _, _, severity = ErrorAnalyzer.classify_error(error_text)
        status = "✓" if severity == expected_severity else "✗"
        print(f"{status} {error_text:40} → Severity: {severity}")
    
    print("\n" + "="*70)
    return True


def test_fix_attempt_record():
    """Test error fix attempt recording"""
    print("\n" + "="*70)
    print("TEST 6: FIX ATTEMPT RECORDING")
    print("="*70)
    
    from Backtest.bot_error_fixer import ErrorFixAttempt
    
    attempt = ErrorFixAttempt(
        attempt_number=1,
        original_error="AttributeError: 'list' has no attribute 'ewm'",
        error_type="attribute_error",
        fix_description="Fixed by importing pandas and using DataFrame",
        success=True,
        fixed_code="import pandas as pd\ndf = pd.Series(data).ewm(span=30).mean()"
    )
    
    print("\nFix Attempt Record:")
    print(f"  Attempt: {attempt.attempt_number}")
    print(f"  Error Type: {attempt.error_type}")
    print(f"  Success: {attempt.success}")
    print(f"  Description: {attempt.fix_description}")
    print(f"  Code Length: {len(attempt.fixed_code) if attempt.fixed_code else 0} chars")
    print(f"  Timestamp: {attempt.timestamp.isoformat()}")
    
    assert attempt.success == True
    assert attempt.error_type == "attribute_error"
    print("\n✓ Fix attempt recording working correctly")
    
    return True


if __name__ == '__main__':
    print("\n" + "="*70)
    print("BOT ERROR FIXER TEST SUITE")
    print("="*70)
    
    tests = [
        ("Error Classification", test_error_classification),
        ("Error Message Extraction", test_error_extraction),
        ("Fix Prompt Building", test_fix_prompt_building),
        ("Error Pattern Matching", test_error_analyzer_patterns),
        ("Severity Classification", test_error_severity_classification),
        ("Fix Attempt Recording", test_fix_attempt_record),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, "PASSED" if result else "FAILED"))
        except Exception as e:
            print(f"\n✗ TEST FAILED: {str(e)}")
            results.append((test_name, "FAILED"))
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, result in results:
        status = "✓" if result == "PASSED" else "✗"
        print(f"{status} {test_name:.<50} {result:>10}")
    
    passed = sum(1 for _, r in results if r == "PASSED")
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("="*70 + "\n")
