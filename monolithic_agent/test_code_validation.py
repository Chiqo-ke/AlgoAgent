"""
Quick test to verify code validation logic
Tests the _validate_generated_code() function patterns
"""

import re

def validate_generated_code(code: str) -> tuple:
    """Validate that generated code contains actual trading logic"""
    
    # Check 1: Code must have broker.buy() or broker.sell() calls
    has_buy = bool(re.search(r'\bbroker\.buy\s*\(', code))
    has_sell = bool(re.search(r'\bbroker\.sell\s*\(', code))
    
    if not (has_buy or has_sell):
        return False, "Code does not contain any buy() or sell() calls - strategy won't trade"
    
    # Check 2: Code must have conditional logic INSIDE strategy (not just if __name__)
    # Look for if/elif statements that are NOT the main block
    conditional_patterns = [
        r'if\s+(?!__name__)',  # if not followed by __name__
        r'\belif\s+',  # elif statements
    ]
    has_conditionals = any(re.search(pattern, code) for pattern in conditional_patterns)
    
    if not has_conditionals:
        return False, "Code lacks conditional logic (if statements) - strategy needs decision logic"
    
    # Check 3: Code must have a main execution block
    has_main = bool(re.search(r'if\s+__name__\s*==\s*[\'"]__main__[\'"]', code))
    has_run = bool(re.search(r'\bbroker\.run\s*\(', code))
    has_run_backtest = bool(re.search(r'\brun_backtest\s*\(', code))
    
    if not has_main:
        return False, "Code missing if __name__ == '__main__' block"
    
    if not (has_run or has_run_backtest):
        return False, "Code missing execution call (broker.run() or run_backtest())"
    
    # Check 4: Code should have class or function definitions
    has_class = bool(re.search(r'class\s+\w+', code))
    has_function = bool(re.search(r'def\s+\w+\s*\(', code))
    
    if not (has_class or has_function):
        return False, "Code missing class or function definitions - needs proper structure"
    
    return True, ""


# Test cases
print("Testing Code Validation Logic\n" + "="*50)

# Test 1: Valid code with all requirements
valid_code = """
def ema_crossover_strategy(broker, market_data):
    data = market_data.get('data', [])
    if not data:
        return
    
    ema_fast = data[-1].get('EMA_12')
    ema_slow = data[-1].get('EMA_26')
    
    if ema_fast is not None and ema_slow is not None:
        if ema_fast > ema_slow and not broker.has_position():
            broker.buy(size=100)
        elif ema_fast < ema_slow and broker.has_position():
            broker.sell(size=100)

if __name__ == '__main__':
    broker.run()
"""

is_valid, error = validate_generated_code(valid_code)
print(f"Test 1 - Valid Code: {'PASS' if is_valid else 'FAIL'}")
if not is_valid:
    print(f"  Error: {error}")

# Test 2: Missing buy/sell calls
no_trades_code = """
def placeholder_strategy(broker, market_data):
    # TODO: Add trading logic
    pass

if __name__ == '__main__':
    broker.run()
"""

is_valid, error = validate_generated_code(no_trades_code)
print(f"\nTest 2 - No Buy/Sell Calls: {'FAIL (expected)' if not is_valid else 'UNEXPECTED PASS'}")
print(f"  Error: {error}")

# Test 3: Missing conditionals
no_logic_code = """
def bad_strategy(broker, market_data):
    broker.buy(size=100)
    broker.sell(size=100)

if __name__ == '__main__':
    broker.run()
"""

is_valid, error = validate_generated_code(no_logic_code)
print(f"\nTest 3 - No Conditional Logic: {'FAIL (expected)' if not is_valid else 'UNEXPECTED PASS'}")
print(f"  Error: {error}")

# Test 4: Missing main block
no_main_code = """
def my_strategy(broker, market_data):
    data = market_data.get('data', [])
    if data:
        broker.buy(size=100)

def run_backtest():
    broker.run()
"""

is_valid, error = validate_generated_code(no_main_code)
print(f"\nTest 4 - No Main Block: {'FAIL (expected)' if not is_valid else 'UNEXPECTED PASS'}")
print(f"  Error: {error}")

# Test 5: Missing run call (no broker.run or run_backtest)
no_run_code = """
def strategy(broker, market_data):
    data = market_data.get('data', [])
    if data:
        broker.buy(size=100)

if __name__ == '__main__':
    pass  # Missing broker.run() or run_backtest()
"""

is_valid, error = validate_generated_code(no_run_code)
print(f"\nTest 5 - No Run Call: {'FAIL (expected)' if not is_valid else 'UNEXPECTED PASS'}")
print(f"  Error: {error}")

# Test 6: Valid with run_backtest() instead of broker.run()
valid_with_backtest = """
def ema_strategy(broker, market_data):
    data = market_data.get('data', [])
    if not data:
        return
    
    current = data[-1]
    ema_fast = current.get('EMA_12')
    ema_slow = current.get('EMA_26')
    
    if ema_fast and ema_slow:
        if ema_fast > ema_slow and not broker.has_position():
            broker.buy(size=100)
        elif ema_fast < ema_slow and broker.has_position():
            broker.sell(size=100)

def run_backtest():
    # Backtest logic
    pass

if __name__ == '__main__':
    run_backtest()
"""

is_valid, error = validate_generated_code(valid_with_backtest)
print(f"\nTest 6 - Valid with run_backtest(): {'PASS' if is_valid else 'FAIL'}")
if not is_valid:
    print(f"  Error: {error}")

print("\n" + "="*50)
print("Validation Logic Test Complete!")
