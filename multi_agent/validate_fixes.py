"""
Quick validation script to verify Priority A-D fixes are properly integrated.

Checks:
1. SafetyBlockError can be imported
2. Router has _sanitize_prompt method
3. Tester has timeout analysis methods
4. Debugger handles timeout analysis
5. Coder prompt includes performance constraints

Run this before running full test suite.
"""

import sys
from pathlib import Path

# Add multi_agent to path
sys.path.insert(0, str(Path(__file__).parent))

def validate_priority_a():
    """Validate Priority A: Safety propagation."""
    print("✓ Checking Priority A: Safety propagation...")
    
    try:
        from llm.providers import SafetyBlockError, ProviderError, RateLimitError
        print("  ✓ SafetyBlockError imported successfully")
        
        # Verify it's a proper exception
        assert issubclass(SafetyBlockError, ProviderError)
        print("  ✓ SafetyBlockError inherits from ProviderError")
        
        # Test creation
        error = SafetyBlockError("test", safety_ratings=[{"category": "TEST"}])
        assert error.safety_ratings == [{"category": "TEST"}]
        print("  ✓ SafetyBlockError stores safety ratings")
        
        return True
    except Exception as e:
        print(f"  ✗ Priority A validation failed: {e}")
        return False


def validate_priority_b():
    """Validate Priority B: Router safety block handling."""
    print("\n✓ Checking Priority B: Router safety handling...")
    
    try:
        from llm.router import RequestRouter
        print("  ✓ RequestRouter imported successfully")
        
        router = RequestRouter()
        
        # Check _sanitize_prompt exists
        assert hasattr(router, '_sanitize_prompt')
        assert callable(router._sanitize_prompt)
        print("  ✓ Router has _sanitize_prompt method")
        
        # Test sanitization
        messages = [
            {"role": "user", "content": "Test ```python\ncode\n``` block"}
        ]
        sanitized = router._sanitize_prompt(messages)
        assert '[CODE_BLOCK_REMOVED]' in sanitized[0]["content"]
        print("  ✓ Prompt sanitization works")
        
        return True
    except Exception as e:
        print(f"  ✗ Priority B validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_priority_c():
    """Validate Priority C: Timeout analysis."""
    print("\n✓ Checking Priority C: Timeout analysis...")
    
    try:
        from agents.tester_agent.tester import TesterAgent
        print("  ✓ TesterAgent imported successfully")
        
        agent = TesterAgent(use_redis=False)
        
        # Check methods exist
        assert hasattr(agent, '_analyze_timeout_error')
        assert callable(agent._analyze_timeout_error)
        print("  ✓ TesterAgent has _analyze_timeout_error method")
        
        assert hasattr(agent, '_extract_last_execution_line')
        assert callable(agent._extract_last_execution_line)
        print("  ✓ TesterAgent has _extract_last_execution_line method")
        
        assert hasattr(agent, '_get_timeout_fix_strategy')
        assert callable(agent._get_timeout_fix_strategy)
        print("  ✓ TesterAgent has _get_timeout_fix_strategy method")
        
        # Test timeout analysis
        logs = "while True:\n    process()"
        analysis = agent._analyze_timeout_error(logs)
        assert analysis["error_type"] == "timeout"
        assert "infinite_loop" in analysis["root_cause"]
        print("  ✓ Timeout analysis detects infinite loops")
        
        return True
    except Exception as e:
        print(f"  ✗ Priority C validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_priority_c_debugger():
    """Validate debugger timeout handling."""
    print("\n✓ Checking Priority C: Debugger timeout handling...")
    
    try:
        from agents.debugger_agent.debugger import DebuggerAgent
        from contracts.message_bus import InMemoryMessageBus
        print("  ✓ DebuggerAgent imported successfully")
        
        bus = InMemoryMessageBus()
        agent = DebuggerAgent(bus)
        
        # Check _analyze_failure exists
        assert hasattr(agent, '_analyze_failure')
        print("  ✓ DebuggerAgent has _analyze_failure method")
        
        return True
    except Exception as e:
        print(f"  ✗ Priority C (debugger) validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_priority_d():
    """Validate Priority D: Coder performance constraints."""
    print("\n✓ Checking Priority D: Coder performance constraints...")
    
    try:
        from agents.coder_agent.coder import CoderAgent
        from contracts.message_bus import InMemoryMessageBus
        print("  ✓ CoderAgent imported successfully")
        
        bus = InMemoryMessageBus()
        agent = CoderAgent(agent_id="test-coder", message_bus=bus)
        
        # Check _build_llm_prompt exists
        assert hasattr(agent, '_build_llm_prompt')
        print("  ✓ CoderAgent has _build_llm_prompt method")
        
        # Test prompt content
        task = {"title": "Test", "description": "Test", "fixture_paths": []}
        contract = {"contract_id": "test", "interfaces": {}}
        
        prompt = agent._build_llm_prompt(task, contract)
        
        # Check for key performance requirements
        checks = {
            "<10 seconds": "<10 seconds" in prompt or "<10s" in prompt,
            "MAX_ITERATIONS": "MAX_ITERATIONS" in prompt,
            "vectorized": "vectorized" in prompt.lower(),
            "df.iterrows()": "df.iterrows()" in prompt,
            "time.time()": "time.time()" in prompt,
            "gc.collect()": "gc.collect()" in prompt,
        }
        
        for check_name, result in checks.items():
            if result:
                print(f"  ✓ Prompt includes: {check_name}")
            else:
                print(f"  ⚠ Prompt missing: {check_name}")
        
        all_passed = all(checks.values())
        return all_passed
    except Exception as e:
        print(f"  ✗ Priority D validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validations."""
    print("=" * 60)
    print("VALIDATING PRIORITY A-D FIXES")
    print("=" * 60)
    
    results = {
        "Priority A (Safety)": validate_priority_a(),
        "Priority B (Router)": validate_priority_b(),
        "Priority C (Tester)": validate_priority_c(),
        "Priority C (Debugger)": validate_priority_c_debugger(),
        "Priority D (Coder)": validate_priority_d(),
    }
    
    print("\n" + "=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)
    
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL VALIDATIONS PASSED")
        print("\nNext steps:")
        print("1. Run unit tests: pytest tests/test_priority_fixes.py -v")
        print("2. Run E2E test: python test_e2e_real_llm.py --simple")
    else:
        print("✗ SOME VALIDATIONS FAILED")
        print("\nPlease review error messages above and fix imports/syntax.")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
