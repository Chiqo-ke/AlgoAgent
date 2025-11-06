"""
Comprehensive test suite for Tester Agent implementation.

Tests:
1. Config module - configuration and defaults
2. Validators module - schema validation, secret scanning, artifact validation
3. Test runner - pytest/mypy/flake8 execution (mock)
4. Sandbox client - Docker wrapper (mock)
5. Main tester agent - message bus integration, event handling
"""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.tester_agent.config import TesterConfig, config
from agents.tester_agent.validators import (
    validate_test_report_schema,
    scan_for_secrets,
    validate_artifacts,
    _validate_trades_csv,
    _validate_equity_curve
)


class TestResults:
    """Track test results."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def record_pass(self, test_name: str):
        self.passed += 1
        print(f"  ✓ {test_name}")
    
    def record_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append((test_name, error))
        print(f"  ✗ {test_name}: {error}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*70}")
        print(f"Test Summary: {self.passed}/{total} passed")
        if self.failed > 0:
            print(f"\nFailed tests:")
            for test_name, error in self.errors:
                print(f"  - {test_name}: {error}")
        print(f"{'='*70}")
        return self.failed == 0


results = TestResults()


def test_config_module():
    """Test TesterConfig dataclass and defaults."""
    print("\n[Test 1] Config Module")
    print("-" * 70)
    
    try:
        # Test default config
        cfg = TesterConfig()
        
        # Check default values
        assert cfg.default_timeout == 300, "Default timeout should be 300s"
        results.record_pass("Default timeout is 300s")
        
        assert cfg.memory_limit == "1g", "Memory limit should be 1g"
        results.record_pass("Memory limit is 1g")
        
        assert cfg.cpu_limit == "0.5", "CPU limit should be 0.5"
        results.record_pass("CPU limit is 0.5")
        
        assert cfg.docker_image == "algo-sandbox", "Docker image should be algo-sandbox"
        results.record_pass("Docker image name correct")
        
        assert cfg.network_mode == "none", "Network mode should be 'none'"
        results.record_pass("Network isolation enabled")
        
        assert cfg.enable_secret_scanning is True, "Secret scanning should be enabled"
        results.record_pass("Secret scanning enabled")
        
        # Check required artifacts
        assert 'test_report.json' in cfg.required_artifacts
        assert 'trades.csv' in cfg.required_artifacts
        assert 'equity_curve.csv' in cfg.required_artifacts
        assert 'events.log' in cfg.required_artifacts
        results.record_pass("Required artifacts list correct")
        
        # Check secret patterns exist
        assert len(cfg.secret_patterns) > 0, "Should have secret patterns"
        results.record_pass("Secret patterns configured")
        
        # Test global config instance
        assert config.default_timeout == 300
        results.record_pass("Global config instance accessible")
        
    except AssertionError as e:
        results.record_fail("Config defaults", str(e))
    except Exception as e:
        results.record_fail("Config module", str(e))


def test_validators_module():
    """Test validator functions."""
    print("\n[Test 2] Validators Module")
    print("-" * 70)
    
    # Test schema validation
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Test 2.1: Valid test report
        try:
            valid_report = {
                "summary": {
                    "total_trades": 10,
                    "net_pnl": 100.0,
                    "win_rate": 0.6,
                    "max_drawdown": 50.0
                },
                "tests": [
                    {"name": "test_example", "outcome": "passed"}
                ]
            }
            
            report_path = tmpdir / "test_report.json"
            with open(report_path, 'w') as f:
                json.dump(valid_report, f)
            
            # This will use basic validation if schema doesn't exist
            validate_test_report_schema(report_path)
            results.record_pass("Valid test report accepted")
            
        except Exception as e:
            results.record_fail("Valid test report", str(e))
        
        # Test 2.2: Invalid test report (missing required keys)
        try:
            invalid_report = {"tests": []}  # Missing 'summary'
            
            report_path = tmpdir / "invalid_report.json"
            with open(report_path, 'w') as f:
                json.dump(invalid_report, f)
            
            try:
                validate_test_report_schema(report_path)
                results.record_fail("Invalid report validation", "Should have raised error")
            except ValueError:
                results.record_pass("Invalid test report rejected")
            
        except Exception as e:
            results.record_fail("Invalid report test", str(e))
        
        # Test 2.3: Secret scanning
        try:
            secrets_file = tmpdir / "logs.txt"
            with open(secrets_file, 'w') as f:
                f.write("Normal log line\n")
                f.write("API_KEY=sk_test_1234567890abcdefghij\n")
                f.write("Another normal line\n")
                f.write("password=mysecretpass123\n")
            
            secrets = scan_for_secrets(secrets_file)
            assert len(secrets) > 0, "Should detect secrets"
            results.record_pass("Secret scanning detects secrets")
            
        except Exception as e:
            results.record_fail("Secret scanning", str(e))
        
        # Test 2.4: Clean file (no secrets)
        try:
            clean_file = tmpdir / "clean.txt"
            with open(clean_file, 'w') as f:
                f.write("Just normal log lines\n")
                f.write("No secrets here\n")
            
            secrets = scan_for_secrets(clean_file)
            assert len(secrets) == 0, "Should not detect false positives"
            results.record_pass("Secret scanning - no false positives")
            
        except Exception as e:
            results.record_fail("Clean file scanning", str(e))
        
        # Test 2.5: Artifact validation
        try:
            # Create valid artifacts
            (tmpdir / "test_report.json").write_text(json.dumps(valid_report))
            
            # Valid trades.csv
            trades_csv = tmpdir / "trades.csv"
            trades_csv.write_text("time,symbol,action,volume,price,pnl\n2025-11-07,EURUSD,BUY,1.0,1.1000,10.0\n")
            
            # Valid equity_curve.csv
            equity_csv = tmpdir / "equity_curve.csv"
            equity_csv.write_text("time,balance,equity\n2025-11-07,10000,10010\n")
            
            # Events log
            (tmpdir / "events.log").write_text('{"event": "test"}\n')
            
            success, errors = validate_artifacts(tmpdir)
            assert success, f"Artifacts should be valid: {errors}"
            results.record_pass("Valid artifacts accepted")
            
        except Exception as e:
            results.record_fail("Artifact validation", str(e))
        
        # Test 2.6: Missing artifacts
        try:
            empty_dir = tmpdir / "empty"
            empty_dir.mkdir()
            
            success, errors = validate_artifacts(empty_dir)
            assert not success, "Should fail with missing artifacts"
            assert len(errors) > 0, "Should report errors"
            results.record_pass("Missing artifacts detected")
            
        except Exception as e:
            results.record_fail("Missing artifacts test", str(e))
        
        # Test 2.7: Trades CSV validation
        try:
            valid_trades = tmpdir / "valid_trades.csv"
            valid_trades.write_text("time,symbol,action,volume,price\n2025-11-07,EURUSD,BUY,1.0,1.1000\n")
            
            assert _validate_trades_csv(valid_trades), "Should accept valid trades.csv"
            results.record_pass("Valid trades.csv accepted")
            
            invalid_trades = tmpdir / "invalid_trades.csv"
            invalid_trades.write_text("wrong,headers\n1,2\n")
            
            assert not _validate_trades_csv(invalid_trades), "Should reject invalid trades.csv"
            results.record_pass("Invalid trades.csv rejected")
            
        except Exception as e:
            results.record_fail("Trades CSV validation", str(e))
        
        # Test 2.8: Equity curve validation
        try:
            valid_equity = tmpdir / "valid_equity.csv"
            valid_equity.write_text("time,balance,equity\n2025-11-07,10000,10010\n")
            
            assert _validate_equity_curve(valid_equity), "Should accept valid equity_curve.csv"
            results.record_pass("Valid equity_curve.csv accepted")
            
            invalid_equity = tmpdir / "invalid_equity.csv"
            invalid_equity.write_text("wrong,columns\n1,2\n")
            
            assert not _validate_equity_curve(invalid_equity), "Should reject invalid equity_curve.csv"
            results.record_pass("Invalid equity_curve.csv rejected")
            
        except Exception as e:
            results.record_fail("Equity curve validation", str(e))


def test_message_bus_integration():
    """Test Tester Agent message bus integration."""
    print("\n[Test 3] Message Bus Integration")
    print("-" * 70)
    
    try:
        from agents.tester_agent.tester import TesterAgent
        from contracts.message_bus import get_message_bus, Event
        
        # Test 3.1: Agent initialization
        try:
            agent = TesterAgent(use_redis=False)
            results.record_pass("TesterAgent initializes successfully")
        except Exception as e:
            results.record_fail("Agent initialization", str(e))
            return
        
        # Test 3.2: Task filtering (only handle tester tasks)
        try:
            # Create non-tester task
            non_tester_event = Event.create(
                event_type="task.dispatched",
                correlation_id="test_corr",
                workflow_id="test_wf",
                task_id="test_task",
                data={"task": {"agent_role": "coder"}},  # Not tester
                source="test"
            )
            
            # Should not process non-tester tasks (won't raise error, just ignores)
            agent.handle_task(non_tester_event)
            results.record_pass("Non-tester tasks ignored correctly")
            
        except Exception as e:
            results.record_fail("Task filtering", str(e))
        
        # Test 3.3: Extract metrics function
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                report = {
                    "summary": {
                        "total_trades": 15,
                        "net_pnl": 250.75,
                        "win_rate": 0.65,
                        "max_drawdown": 75.5
                    }
                }
                
                report_path = Path(tmpdir) / "test_report.json"
                with open(report_path, 'w') as f:
                    json.dump(report, f)
                
                metrics = agent.extract_metrics(report_path)
                
                assert metrics['total_trades'] == 15
                assert metrics['net_pnl'] == 250.75
                assert metrics['win_rate'] == 0.65
                assert metrics['max_drawdown'] == 75.5
                
                results.record_pass("Metrics extraction works correctly")
        
        except Exception as e:
            results.record_fail("Metrics extraction", str(e))
        
        # Test 3.4: Event publishers (check they don't crash)
        try:
            agent.publish_test_started("corr1", "wf1", "task1")
            results.record_pass("TEST_STARTED event published")
            
            agent.publish_test_passed("corr1", "wf1", "task1", {}, {}, 10.0)
            results.record_pass("TEST_PASSED event published")
            
            agent.publish_test_failed("corr1", "wf1", "task1", [], Path("."))
            results.record_pass("TEST_FAILED event published")
            
            agent.request_debug_branch("corr1", "wf1", "task1", Path("."), "test", "details")
            results.record_pass("Branch todo request published")
            
        except Exception as e:
            results.record_fail("Event publishing", str(e))
        
    except ImportError as e:
        results.record_fail("Import TesterAgent", str(e))
    except Exception as e:
        results.record_fail("Message bus integration", str(e))


def test_sandbox_client():
    """Test sandbox client (without actual Docker)."""
    print("\n[Test 4] Sandbox Client (Mock)")
    print("-" * 70)
    
    try:
        from agents.tester_agent.sandbox_client import SandboxClient
        
        # Test 4.1: Client initialization
        try:
            client = SandboxClient()
            assert client.image_built == False, "Image should not be marked as built initially"
            results.record_pass("SandboxClient initializes correctly")
        except Exception as e:
            results.record_fail("Client initialization", str(e))
            return
        
        # Test 4.2: Build test script generation
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                params = {
                    "strategy": "test_strategy.py",
                    "tests": ["test_1.py", "test_2.py"],
                    "fixtures": ["fixture.csv"],
                    "out_dir": tmpdir,
                    "timeout": 300,
                    "seed": 42
                }
                
                workspace = Path(tmpdir)
                script = client._build_test_script(params, workspace)
                
                assert "pytest" in script, "Script should contain pytest command"
                assert "mypy" in script, "Script should contain mypy command"
                assert "flake8" in script, "Script should contain flake8 command"
                assert "bandit" in script, "Script should contain bandit command"
                assert "test_strategy.py" in script, "Script should reference strategy"
                
                results.record_pass("Test script generation correct")
        
        except Exception as e:
            results.record_fail("Test script generation", str(e))
        
        # Test 4.3: Artifact collection
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                workspace = Path(tmpdir)
                
                # Create dummy artifacts
                (workspace / "test_report.json").write_text("{}")
                (workspace / "trades.csv").write_text("header\n")
                (workspace / "equity_curve.csv").write_text("header\n")
                (workspace / "events.log").write_text("log\n")
                
                artifacts = client._collect_artifacts(workspace)
                
                assert "test_report_json" in artifacts, "Should collect test_report.json"
                assert "trades_csv" in artifacts, "Should collect trades.csv"
                assert "equity_curve_csv" in artifacts, "Should collect equity_curve.csv"
                assert "events_log" in artifacts, "Should collect events.log"
                
                results.record_pass("Artifact collection works correctly")
        
        except Exception as e:
            results.record_fail("Artifact collection", str(e))
        
    except ImportError as e:
        results.record_fail("Import SandboxClient", str(e))
    except Exception as e:
        results.record_fail("Sandbox client", str(e))


def test_test_runner():
    """Test the test runner module."""
    print("\n[Test 5] Test Runner Module")
    print("-" * 70)
    
    try:
        from agents.tester_agent.test_runner import TestRunner
        
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            
            # Test 5.1: TestRunner initialization
            try:
                runner = TestRunner(workspace)
                assert runner.workspace == workspace
                assert workspace.exists()
                results.record_pass("TestRunner initializes correctly")
            except Exception as e:
                results.record_fail("TestRunner initialization", str(e))
                return
            
            # Test 5.2: Parse failures function
            try:
                failures = runner.parse_failures(
                    pytest_exit=1, pytest_stdout="Test failed", pytest_stderr="Error",
                    mypy_exit=0, mypy_stdout="", 
                    flake8_exit=0, flake8_stdout="",
                    bandit_exit=0, bandit_stdout=""
                )
                
                assert len(failures) == 1, "Should have 1 pytest failure"
                assert failures[0]['check'] == 'pytest'
                results.record_pass("Failure parsing - pytest failure detected")
            except Exception as e:
                results.record_fail("Failure parsing", str(e))
            
            # Test 5.3: Multiple failures
            try:
                failures = runner.parse_failures(
                    pytest_exit=1, pytest_stdout="Test failed", pytest_stderr="",
                    mypy_exit=1, mypy_stdout="Type error", 
                    flake8_exit=1, flake8_stdout="Style error",
                    bandit_exit=0, bandit_stdout=""
                )
                
                assert len(failures) == 3, "Should have 3 failures"
                checks = [f['check'] for f in failures]
                assert 'pytest' in checks
                assert 'mypy' in checks
                assert 'flake8' in checks
                results.record_pass("Multiple failures parsed correctly")
            except Exception as e:
                results.record_fail("Multiple failures", str(e))
    
    except ImportError as e:
        results.record_fail("Import TestRunner", str(e))
    except Exception as e:
        results.record_fail("Test runner module", str(e))


def main():
    """Run all tests."""
    print("="*70)
    print("TESTER AGENT COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    test_config_module()
    test_validators_module()
    test_message_bus_integration()
    test_sandbox_client()
    test_test_runner()
    
    # Print summary
    success = results.summary()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
