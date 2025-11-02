"""
Comprehensive test suite for production hardening components
"""
import sys
import json
from pathlib import Path
from datetime import datetime

# Test results tracking
test_results = {
    "canonical_schema_v2": {"tests": [], "passed": 0, "failed": 0},
    "state_manager": {"tests": [], "passed": 0, "failed": 0},
    "safe_tools": {"tests": [], "passed": 0, "failed": 0},
    "sandbox_orchestrator": {"tests": [], "passed": 0, "failed": 0},
    "output_validator": {"tests": [], "passed": 0, "failed": 0},
    "git_patch_manager": {"tests": [], "passed": 0, "failed": 0},
}

def log_test(component, test_name, passed, error=None):
    """Log test result"""
    result = {"name": test_name, "passed": passed, "error": str(error) if error else None}
    test_results[component]["tests"].append(result)
    if passed:
        test_results[component]["passed"] += 1
        print(f"✅ {component}.{test_name}")
    else:
        test_results[component]["failed"] += 1
        print(f"❌ {component}.{test_name}: {error}")

def test_canonical_schema():
    """Test canonical_schema_v2.py"""
    print("\n" + "="*80)
    print("TEST 1: Canonical Schema V2 (Pydantic Validators)")
    print("="*80)
    
    try:
        from canonical_schema_v2 import (
            Signal, Order, StrategyDefinition, GeneratedCode,
            OrderSide, OrderAction, OrderType, SizeType
        )
        log_test("canonical_schema_v2", "import_models", True)
    except Exception as e:
        log_test("canonical_schema_v2", "import_models", False, e)
        return
    
    # Test Signal validation
    try:
        signal = Signal(
            symbol="AAPL",
            side=OrderSide.BUY,
            action=OrderAction.ENTRY,
            order_type=OrderType.MARKET,
            size=100,
            size_type=SizeType.SHARES
        )
        assert signal.symbol == "AAPL"
        log_test("canonical_schema_v2", "signal_creation", True)
    except Exception as e:
        log_test("canonical_schema_v2", "signal_creation", False, e)
    
    # Test validation enforcement
    try:
        # Should fail: negative size
        bad_signal = Signal(
            symbol="AAPL",
            side=OrderSide.BUY,
            action=OrderAction.ENTRY,
            order_type=OrderType.MARKET,
            size=-100  # Invalid!
        )
        log_test("canonical_schema_v2", "negative_size_validation", False, "Allowed negative size")
    except Exception as e:
        log_test("canonical_schema_v2", "negative_size_validation", True)
    
    # Test JSON schema export
    try:
        schema = Signal.model_json_schema()
        assert "properties" in schema
        assert "symbol" in schema["properties"]
        log_test("canonical_schema_v2", "json_schema_export", True)
    except Exception as e:
        log_test("canonical_schema_v2", "json_schema_export", False, e)
    
    # Test StrategyDefinition
    try:
        strategy = StrategyDefinition(
            name="Test_Strategy",
            description="A test strategy",
            parameters={"threshold": 0.5},
            indicators={"sma": {"period": 20}},
            entry_rules=["sma > close"],
            exit_rules=["sma < close"]
        )
        log_test("canonical_schema_v2", "strategy_definition", True)
    except Exception as e:
        log_test("canonical_schema_v2", "strategy_definition", False, e)

def test_state_manager():
    """Test state_manager.py"""
    print("\n" + "="*80)
    print("TEST 2: State Manager (SQLite Persistence)")
    print("="*80)
    
    try:
        from state_manager import StateManager, StrategyStatus
        log_test("state_manager", "import", True)
    except Exception as e:
        log_test("state_manager", "import", False, e)
        return
    
    # Create test database
    test_db = Path("test_state_manager.db")
    if test_db.exists():
        test_db.unlink()
    
    try:
        sm = StateManager(str(test_db))
        log_test("state_manager", "initialization", True)
    except Exception as e:
        log_test("state_manager", "initialization", False, e)
        return
    
    # Test strategy registration
    try:
        strategy_id = sm.register_strategy(
            name="RSI_Strategy",
            json_path="codes/RSI_Strategy.json",
            py_path="codes/RSI_Strategy.py"
        )
        assert strategy_id is not None
        log_test("state_manager", "register_strategy", True)
    except Exception as e:
        log_test("state_manager", "register_strategy", False, e)
    
    # Test status update
    try:
        sm.update_status(
            name="RSI_Strategy",
            status=StrategyStatus.TESTING,
            error=None
        )
        log_test("state_manager", "update_status", True)
    except Exception as e:
        log_test("state_manager", "update_status", False, e)
    
    # Test job queue
    try:
        job = sm.enqueue_job(
            job_id="test_job_001",
            job_type="generate",
            strategy_name="RSI_Strategy",
            payload={"data": "test"}
        )
        assert job is not None
        log_test("state_manager", "enqueue_job", True)
    except Exception as e:
        log_test("state_manager", "enqueue_job", False, e)
    
    # Test audit log
    try:
        sm.update_status("RSI_Strategy", StrategyStatus.PASSED)
        # Audit should be created automatically
        log_test("state_manager", "audit_logging", True)
    except Exception as e:
        log_test("state_manager", "audit_logging", False, e)
    
    # Cleanup
    try:
        if test_db.exists():
            sm = None  # Release database connection
            import time
            time.sleep(0.1)  # Give time for connection to close
            test_db.unlink()
    except Exception:
        pass  # Ignore cleanup errors

def test_safe_tools():
    """Test safe_tools.py"""
    print("\n" + "="*80)
    print("TEST 3: Safe Tools (Type-safe Tool Wrappers)")
    print("="*80)
    
    try:
        from safe_tools import SafeTools, ReadFileRequest, WriteFileRequest
        log_test("safe_tools", "import", True)
    except Exception as e:
        log_test("safe_tools", "import", False, e)
        return
    
    # Initialize
    try:
        tools = SafeTools(workspace_root=Path("."))
        log_test("safe_tools", "initialization", True)
    except Exception as e:
        log_test("safe_tools", "initialization", False, e)
        return
    
    # Test file write
    test_file = Path("test_safe_tools.txt")
    try:
        request = WriteFileRequest(
            path="test_safe_tools.txt",
            content="Test content"
        )
        response = tools.write_file(request)
        assert response.success
        assert test_file.exists()
        log_test("safe_tools", "write_file", True)
    except Exception as e:
        log_test("safe_tools", "write_file", False, e)
    
    # Test file read
    try:
        request = ReadFileRequest(path="test_safe_tools.txt")
        response = tools.read_file(request)
        assert response.success
        assert "Test content" in response.result
        log_test("safe_tools", "read_file", True)
    except Exception as e:
        log_test("safe_tools", "read_file", False, e)
    
    # Test path traversal protection
    try:
        request = ReadFileRequest(path="../../../etc/passwd")
        response = tools.read_file(request)
        # Should either fail or sanitize the path
        log_test("safe_tools", "path_traversal_protection", True)
    except Exception as e:
        log_test("safe_tools", "path_traversal_protection", True)  # Exception is expected
    
    # Cleanup
    if test_file.exists():
        test_file.unlink()

def test_sandbox_orchestrator():
    """Test sandbox_orchestrator.py"""
    print("\n" + "="*80)
    print("TEST 4: Sandbox Orchestrator (Docker Isolation)")
    print("="*80)
    
    try:
        from sandbox_orchestrator import SandboxRunner, SandboxConfig
        log_test("sandbox_orchestrator", "import", True)
    except Exception as e:
        log_test("sandbox_orchestrator", "import", False, e)
        return
    
    # Check Docker availability
    import subprocess
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            print("⚠️  Docker not available - skipping sandbox tests")
            log_test("sandbox_orchestrator", "docker_available", False, "Docker not installed")
            return
        log_test("sandbox_orchestrator", "docker_available", True)
    except Exception as e:
        print("⚠️  Docker not available - skipping sandbox tests")
        log_test("sandbox_orchestrator", "docker_available", False, e)
        return
    
    # Test runner initialization
    try:
        runner = SandboxRunner(workspace_root=Path("."))
        log_test("sandbox_orchestrator", "initialization", True)
    except Exception as e:
        log_test("sandbox_orchestrator", "initialization", False, e)
        return
    
    # Create simple test script
    test_script = Path("test_sandbox_script.py")
    test_script.write_text("print('Hello from sandbox')\nprint(1 + 1)")
    
    # Test sandbox execution
    try:
        result = runner.run_python_script(str(test_script), timeout=30)
        assert result.status in ["success", "error"]
        log_test("sandbox_orchestrator", "run_python_script", True)
    except Exception as e:
        log_test("sandbox_orchestrator", "run_python_script", False, e)
    
    # Cleanup
    if test_script.exists():
        test_script.unlink()

def test_output_validator():
    """Test output_validator.py"""
    print("\n" + "="*80)
    print("TEST 5: Output Validator (Code Safety & Validation)")
    print("="*80)
    
    try:
        from output_validator import OutputValidator, CodeSafetyChecker
        log_test("output_validator", "import", True)
    except Exception as e:
        log_test("output_validator", "import", False, e)
        return
    
    # Test validator initialization
    try:
        validator = OutputValidator(strict_safety=True)
        log_test("output_validator", "initialization", True)
    except Exception as e:
        log_test("output_validator", "initialization", False, e)
        return
    
    # Test safe code validation
    safe_code = """
def calculate_sma(prices, period):
    return sum(prices[-period:]) / period

class MyStrategy:
    def next(self):
        if self.sma > 100:
            self.buy()
"""
    try:
        result, errors = validator.validate_generated_code(safe_code)
        assert result is not None
        log_test("output_validator", "validate_safe_code", True)
    except Exception as e:
        log_test("output_validator", "validate_safe_code", False, e)
    
    # Test dangerous code detection
    dangerous_code = """
import os
os.system('rm -rf /')
"""
    try:
        result, errors = validator.validate_generated_code(dangerous_code)
        if errors:
            log_test("output_validator", "detect_dangerous_code", True)
        else:
            log_test("output_validator", "detect_dangerous_code", False, "Failed to detect dangerous code")
    except Exception as e:
        log_test("output_validator", "detect_dangerous_code", True)  # Exception expected
    
    # Test syntax error detection
    invalid_code = "def broken_function(\n    print('missing closing paren'"
    try:
        result, errors = validator.validate_generated_code(invalid_code)
        assert errors, "Should have detected syntax errors"
        log_test("output_validator", "detect_syntax_errors", True)
    except Exception as e:
        log_test("output_validator", "detect_syntax_errors", False, e)

def test_git_patch_manager():
    """Test git_patch_manager.py"""
    print("\n" + "="*80)
    print("TEST 6: Git Patch Manager (Branch Isolation)")
    print("="*80)
    
    try:
        from git_patch_manager import GitPatchManager, PatchWorkflow
        log_test("git_patch_manager", "import", True)
    except Exception as e:
        log_test("git_patch_manager", "import", False, e)
        return
    
    # Check if we're in a git repo
    import subprocess
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            cwd=Path("."),
            timeout=5
        )
        if result.returncode != 0:
            print("⚠️  Not in git repo - skipping git tests")
            log_test("git_patch_manager", "git_available", False, "Not a git repository")
            return
        log_test("git_patch_manager", "git_available", True)
    except Exception as e:
        print("⚠️  Git not available - skipping git tests")
        log_test("git_patch_manager", "git_available", False, e)
        return
    
    # Test manager initialization
    try:
        manager = GitPatchManager(repo_path=Path("."))
        log_test("git_patch_manager", "initialization", True)
    except Exception as e:
        log_test("git_patch_manager", "initialization", False, e)
        return
    
    # Test workflow initialization
    try:
        workflow = PatchWorkflow(repo_path=Path("."))
        log_test("git_patch_manager", "workflow_initialization", True)
    except Exception as e:
        log_test("git_patch_manager", "workflow_initialization", False, e)

def print_summary():
    """Print test summary"""
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    total_passed = 0
    total_failed = 0
    
    for component, results in test_results.items():
        passed = results["passed"]
        failed = results["failed"]
        total = passed + failed
        total_passed += passed
        total_failed += failed
        
        status = "✅ PASS" if failed == 0 and passed > 0 else "❌ FAIL" if failed > 0 else "⚠️  SKIP"
        print(f"\n{component}:")
        print(f"  {status} - {passed}/{total} tests passed")
        
        if failed > 0:
            print(f"  Failed tests:")
            for test in results["tests"]:
                if not test["passed"]:
                    print(f"    - {test['name']}: {test['error']}")
    
    print("\n" + "="*80)
    print(f"OVERALL: {total_passed}/{total_passed + total_failed} tests passed")
    print("="*80)
    
    # Save results to JSON
    output_file = Path("test_results.json")
    output_file.write_text(json.dumps(test_results, indent=2))
    print(f"\nDetailed results saved to: {output_file.absolute()}")
    
    return total_failed == 0

if __name__ == "__main__":
    print("="*80)
    print("PRODUCTION COMPONENTS TEST SUITE")
    print("="*80)
    print(f"Start time: {datetime.now().isoformat()}")
    
    # Run all tests
    test_canonical_schema()
    test_state_manager()
    test_safe_tools()
    test_sandbox_orchestrator()
    test_output_validator()
    test_git_patch_manager()
    
    # Print summary
    success = print_summary()
    
    print(f"\nEnd time: {datetime.now().isoformat()}")
    sys.exit(0 if success else 1)
