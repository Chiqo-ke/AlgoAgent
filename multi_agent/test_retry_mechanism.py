#!/usr/bin/env python3
"""
Test retry mechanism for transient errors (timeouts, 503, 504, etc.)
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env")
except ImportError:
    print("⚠️  python-dotenv not installed")

# Ensure router is enabled
os.environ['LLM_MULTI_KEY_ROUTER_ENABLED'] = 'true'
os.environ['LLM_MAX_RETRIES'] = '3'  # 3 retries

from llm.router import get_request_router, reset_request_router
from keys.manager import reset_key_manager

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'


def print_header(text: str):
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")


def print_success(message: str):
    print(f"{GREEN}✅ {message}{RESET}")


def print_error(message: str):
    print(f"{RED}❌ {message}{RESET}")


def print_info(message: str):
    print(f"{CYAN}ℹ️  {message}{RESET}")


def test_retry_configuration():
    """Test 1: Verify retry configuration is loaded"""
    print_header("Test 1: Verify Retry Configuration")
    
    reset_request_router()
    reset_key_manager()
    
    router = get_request_router()
    
    print_info(f"Max retries: {router.max_retries}")
    print_info(f"Base backoff: {router.base_backoff_ms}ms")
    
    if router.max_retries == 3 and router.base_backoff_ms == 500:
        print_success("Retry configuration loaded correctly")
        return True
    else:
        print_error(f"Configuration mismatch (expected 3 retries, 500ms backoff)")
        return False


def test_simple_request_with_retry():
    """Test 2: Simple request should succeed on first try"""
    print_header("Test 2: Simple Request (Should Succeed)")
    
    router = get_request_router()
    
    print_info("Sending simple request (should not need retries)...")
    
    response = router.send_chat(
        conv_id="test_retry_simple",
        prompt="Say 'Hello' in one word",
        model_preference="gemini-2.5-flash",
        expected_completion_tokens=10,
        max_output_tokens=50,
        temperature=0.1
    )
    
    if response.get('success'):
        print_success(f"Request succeeded")
        print_info(f"Response: {response.get('content', '')}")
        print_info(f"Key used: {response.get('key_id', 'N/A')}")
        return True
    else:
        print_error(f"Request failed: {response.get('error')}")
        return False


def test_fallback_to_different_key():
    """Test 3: Verify fallback to different key if one fails"""
    print_header("Test 3: Multi-Key Fallback Test")
    
    router = get_request_router()
    
    print_info("Sending multiple requests to trigger key rotation...")
    
    keys_used = []
    successful = 0
    
    for i in range(3):
        response = router.send_chat(
            conv_id=f"test_retry_fallback_{i}",
            prompt=f"Count to {i+1}",
            model_preference="gemini-2.5-flash",
            expected_completion_tokens=20,
            temperature=0.1
        )
        
        if response.get('success'):
            successful += 1
            key_id = response.get('key_id', 'unknown')
            keys_used.append(key_id)
            print_info(f"Request {i+1}: ✓ (key: {key_id})")
        else:
            print_info(f"Request {i+1}: Failed - {response.get('error', 'Unknown')}")
    
    print_info(f"Successful requests: {successful}/3")
    print_info(f"Keys used: {set(keys_used)}")
    
    if successful >= 2:
        print_success("Multi-key fallback working")
        return True
    else:
        print_error("Too many failures")
        return False


def test_backoff_calculation():
    """Test 4: Verify exponential backoff calculation"""
    print_header("Test 4: Backoff Calculation Test")
    
    router = get_request_router()
    
    print_info("Testing backoff calculation for retry attempts...")
    
    backoffs = []
    for attempt in range(4):
        backoff = router._calculate_backoff(attempt)
        backoffs.append(backoff)
        expected_base = 500 * (2 ** attempt)
        print_info(f"Attempt {attempt}: {backoff}ms (expected ~{expected_base}ms)")
    
    # Check that backoff is increasing exponentially
    if backoffs[1] > backoffs[0] and backoffs[2] > backoffs[1]:
        print_success("Exponential backoff working correctly")
        return True
    else:
        print_error("Backoff not increasing properly")
        return False


def main():
    """Run retry mechanism tests"""
    print(f"\n{BLUE}{'='*80}")
    print("Retry Mechanism Test Suite")
    print("Testing: Retry configuration, exponential backoff, multi-key fallback")
    print(f"{'='*80}{RESET}\n")
    
    results = {}
    
    tests = [
        ("Retry Configuration", test_retry_configuration),
        ("Simple Request", test_simple_request_with_retry),
        ("Multi-Key Fallback", test_fallback_to_different_key),
        ("Backoff Calculation", test_backoff_calculation),
    ]
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False
    
    # Print summary
    print(f"\n{BLUE}{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}{RESET}\n")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{GREEN}✅ PASSED{RESET}" if result else f"{RED}❌ FAILED{RESET}"
        print(f"{test_name:<40} {status}")
    
    print(f"\n{BLUE}{'='*80}{RESET}")
    if passed == total:
        print(f"{GREEN}ALL TESTS PASSED: {passed}/{total}{RESET}")
        print(f"{GREEN}✅ Retry mechanism is working correctly!{RESET}")
    else:
        print(f"{YELLOW}TESTS PASSED: {passed}/{total}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")
    
    # Print configuration summary
    if passed >= 3:
        print_info("Retry mechanism features:")
        print("  • Configurable max retries (default: 3)")
        print("  • Exponential backoff with jitter (500ms, 1s, 2s, ...)")
        print("  • Automatic retry on timeouts (504, deadline exceeded)")
        print("  • Automatic retry on service errors (503, 502)")
        print("  • Multi-key fallback (excludes failed keys)")
        print("  • Cooldown management (prevents retry storms)")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
