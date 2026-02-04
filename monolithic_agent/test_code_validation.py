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
    
    # Check 3: Code must have a main method that calls broker.run()
    has_main = bool(re.search(r'if\s+__name__\s*==\s*[\'"]__main__[\'"]', code))
    has_run = bool(re.search(r'\bbroker\.run\s*\(', code))
    
    if not (has_main and has_run):
        return False, "Code missing main execution block with broker.run() call"
    
    # Check 4: Code should have strategy function definition
    has_strategy_func = bool(re.search(r'def\s+\w+_strategy\s*\(', code))
    
    if not has_strategy_func:
        return False, "Code missing strategy function definition"
    
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
def strategy(broker, market_data):
    data = market_data.get('data', [])
    if data:
        broker.buy(size=100)
"""

is_valid, error = validate_generated_code(no_main_code)
print(f"\nTest 4 - No Main Block: {'FAIL (expected)' if not is_valid else 'UNEXPECTED PASS'}")
print(f"  Error: {error}")

# Test 5: Missing strategy function
no_function_code = """
if data:
    broker.buy(size=100)

if __name__ == '__main__':
    broker.run()
"""

is_valid, error = validate_generated_code(no_function_code)
print(f"\nTest 5 - No Strategy Function: {'FAIL (expected)' if not is_valid else 'UNEXPECTED PASS'}")
print(f"  Error: {error}")

print("\n" + "="*50)
print("Validation Logic Test Complete!")
