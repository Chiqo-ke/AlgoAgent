"""
Test Request Throttling Implementation
=======================================

Tests that the request throttling is working correctly to prevent rate limit errors.
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Add Backtest to path
sys.path.insert(0, str(Path(__file__).parent / "Backtest"))

print("=" * 80)
print("REQUEST THROTTLING TEST")
print("=" * 80)
print()

# Check configuration
delay = os.getenv('GEMINI_REQUEST_DELAY', '5')
max_concurrent = os.getenv('MAX_CONCURRENT_REQUESTS', '1')

print(f"Configuration:")
print(f"  GEMINI_REQUEST_DELAY: {delay} seconds")
print(f"  MAX_CONCURRENT_REQUESTS: {max_concurrent}")
print()

print("Testing throttling with 3 consecutive requests...")
print("(This should take at least 10 seconds with 5-second delay)")
print()

try:
    from Backtest.gemini_strategy_generator import GeminiStrategyGenerator
    
    generator = GeminiStrategyGenerator(use_key_rotation=True)
    print(f"✅ Generator initialized")
    print(f"   Key rotation: {generator.use_key_rotation}")
    print(f"   Selected key: {generator.selected_key_id}")
    print()
    
    # Test throttling with simple prompts
    test_prompts = [
        "Create a simple moving average crossover strategy",
        "Create an RSI-based strategy",
        "Create a MACD strategy"
    ]
    
    start_time = time.time()
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"Request {i}/3: {prompt[:50]}...")
        request_start = time.time()
        
        try:
            # This will trigger throttling
            result = generator.generate_strategy(
                description=prompt,
                strategy_name=f"test_strategy_{i}"
            )
            request_duration = time.time() - request_start
            print(f"  ✅ Completed in {request_duration:.1f}s")
            print(f"  Generated {len(result)} characters of code")
            
        except Exception as e:
            request_duration = time.time() - request_start
            print(f"  ❌ Error after {request_duration:.1f}s: {str(e)[:100]}")
            
            # If it's a rate limit error, that's expected without throttling
            if "429" in str(e) or "quota" in str(e).lower():
                print(f"  ⚠️  Rate limit hit - throttling should prevent this")
        
        print()
    
    total_time = time.time() - start_time
    expected_time = int(delay) * (len(test_prompts) - 1)  # Delay between requests
    
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"Total time: {total_time:.1f}s")
    print(f"Expected minimum time: {expected_time}s (with {delay}s delay)")
    print()
    
    if total_time >= expected_time:
        print("✅ PASS - Throttling is working!")
        print(f"   Requests were properly delayed by ~{delay}s between each call")
    else:
        print("❌ FAIL - Throttling may not be working correctly")
        print(f"   Expected at least {expected_time}s but only took {total_time:.1f}s")
    
    print()
    print("Benefits of throttling:")
    print(f"  • Prevents hitting 15 RPM rate limit")
    print(f"  • With {delay}s delay: max ~{60 // int(delay)} requests/minute")
    print(f"  • Allows smooth operation without 429 errors")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    print(traceback.format_exc())

print()
print("=" * 80)
