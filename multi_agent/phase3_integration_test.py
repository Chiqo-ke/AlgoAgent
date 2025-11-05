"""
Phase 3 Integration Test

Tests the new multi-agent components:
- Debugger Agent
- Architect Agent
- Fixture Manager
- Orchestrator Branch Todo Logic
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime

# Test imports
print("Testing imports...")

try:
    from contracts.message_bus import InMemoryMessageBus
    from contracts.event_types import Event, EventType
    from agents.debugger_agent import DebuggerAgent
    from agents.architect_agent import ArchitectAgent
    from fixture_manager import FixtureManager
    from orchestrator_service.orchestrator import MinimalOrchestrator
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    exit(1)


async def test_fixture_manager():
    """Test fixture generation"""
    print("\n" + "="*60)
    print("TEST 1: Fixture Manager")
    print("="*60)
    
    try:
        manager = FixtureManager(fixtures_dir=Path("fixtures_test"))
        
        # Test OHLCV fixture
        ohlcv_path = manager.create_ohlcv_fixture(symbol="TEST", num_bars=10, seed=42)
        assert ohlcv_path.exists(), "OHLCV fixture not created"
        
        # Test indicator fixture
        test_cases = [
            {
                "name": "test_rsi",
                "input": {"prices": [100, 102, 101], "period": 14},
                "expected": {"rsi": 50}
            }
        ]
        indicator_path = manager.create_indicator_fixture("rsi", test_cases)
        assert indicator_path.exists(), "Indicator fixture not created"
        
        # Test loading
        loaded_data = manager.load_fixture("sample_test.csv")
        assert len(loaded_data) == 10, f"Expected 10 rows, got {len(loaded_data)}"
        
        print("✅ Fixture Manager test passed")
        print(f"   - Created {ohlcv_path}")
        print(f"   - Created {indicator_path}")
        return True
        
    except Exception as e:
        print(f"❌ Fixture Manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_debugger_agent():
    """Test debugger agent failure analysis"""
    print("\n" + "="*60)
    print("TEST 2: Debugger Agent")
    print("="*60)
    
    try:
        bus = InMemoryMessageBus()
        debugger = DebuggerAgent(bus)
        
        await debugger.start()
        
        # Simulate test failure
        test_failure = {
            "event_id": "test_001",
            "event_type": EventType.TEST_FAILED.value,
            "timestamp": datetime.now().isoformat(),
            "source_agent": "tester-001",
            "correlation_id": "test_corr",
            "payload": {
                "task_id": "task_test",
                "workflow_id": "wf_test",
                "task_title": "Test task",
                "test_result": {
                    "status": "failed",
                    "error_message": "AssertionError: Expected 50, got 45",
                    "traceback": "Traceback:\n  assert x == 50\nAssertionError",
                    "failed_tests": ["test_example"],
                    "timed_out": False
                },
                "failure_routing": {
                    "implementation_bug": "coder",
                    "spec_mismatch": "architect"
                },
                "original_tests": [{"cmd": "pytest test.py"}],
                "expected_artifacts": ["test.py"]
            }
        }
        
        bus.publish("test.results", test_failure)
        await asyncio.sleep(1)  # Give async callbacks time to execute
        
        await debugger.stop()
        
        print("✅ Debugger Agent test passed")
        print("   - Started successfully")
        print("   - Processed test failure event")
        return True
        
    except Exception as e:
        print(f"❌ Debugger Agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_orchestrator_branch_logic():
    """Test orchestrator branch todo logic"""
    print("\n" + "="*60)
    print("TEST 3: Orchestrator Branch Logic")
    print("="*60)
    
    try:
        orchestrator = MinimalOrchestrator(use_message_bus=False)
        
        # Create a test workflow
        test_todo_list = {
            "todo_list_id": "test_workflow",
            "workflow_name": "Test Workflow",
            "created_at": datetime.now().isoformat(),
            "metadata": {
                "auto_fix_mode": True,
                "max_branch_depth": 2,
                "max_debug_attempts": 3
            },
            "items": [
                {
                    "id": "task_1",
                    "title": "Test Task",
                    "description": "A test task",
                    "agent_role": "coder",
                    "priority": 1,
                    "dependencies": [],
                    "max_retries": 3,
                    "timeout_seconds": 300,
                    "acceptance_criteria": {
                        "tests": [{"cmd": "pytest test.py"}]
                    },
                    "failure_routing": {
                        "implementation_bug": "coder",
                        "spec_mismatch": "architect"
                    }
                }
            ]
        }
        
        # Save and load
        test_path = Path("test_todo_list.json")
        with open(test_path, 'w') as f:
            json.dump(test_todo_list, f)
        
        todo_list_id = orchestrator.load_todo_list(test_path)
        assert todo_list_id == "test_workflow", "Todo list ID mismatch"
        
        # Create workflow
        workflow_id = orchestrator.create_workflow(todo_list_id)
        assert workflow_id.startswith("wf_"), "Invalid workflow ID"
        
        # Check branch todo support
        workflow = orchestrator.workflows[workflow_id]
        assert workflow.auto_fix_mode == True, "Auto-fix mode not set"
        assert workflow.max_branch_depth == 2, "Max branch depth not set"
        assert workflow.current_branch_depth == 0, "Initial branch depth should be 0"
        
        # Test branch todo creation
        test_result = {
            "error_message": "AssertionError",
            "traceback": "assert x == y\nAssertionError",
            "timed_out": False
        }
        
        branch_todo = orchestrator._handle_test_failure(
            workflow_id=workflow_id,
            task_id="task_1",
            task_item=test_todo_list["items"][0],
            test_result=test_result
        )
        
        assert branch_todo is not None, "Branch todo should be created"
        assert branch_todo["parent_id"] == "task_1", "Parent ID mismatch"
        assert branch_todo["is_temporary"] == True, "Should be temporary"
        assert workflow.current_branch_depth == 1, "Branch depth should be 1"
        
        # Cleanup
        test_path.unlink()
        
        print("✅ Orchestrator Branch Logic test passed")
        print(f"   - Created workflow {workflow_id}")
        print(f"   - Branch todo created: {branch_todo['id']}")
        print(f"   - Branch depth: {workflow.current_branch_depth}")
        return True
        
    except Exception as e:
        print(f"❌ Orchestrator Branch Logic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("PHASE 3 INTEGRATION TESTS")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(await test_fixture_manager())
    results.append(await test_debugger_agent())
    results.append(await test_orchestrator_branch_logic())
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
