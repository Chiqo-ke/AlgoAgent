"""
Test Workflow Tracking Integration
Tests the complete workflow tracking system from Python backend to frontend display
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Backtest.ai_developer_agent import AIDeveloperAgent
from Backtest.workflow_tracker import (
    WorkflowTracker,
    create_strategy_generation_workflow,
    StepStatus
)

def test_workflow_creation():
    """Test creating a workflow"""
    print("\n" + "="*80)
    print("TEST 1: Workflow Creation")
    print("="*80)
    
    workflow = create_strategy_generation_workflow()
    
    assert workflow.workflow_name == "Strategy Generation"
    assert len(workflow.steps) == 8
    assert workflow.current_step_index == 0
    
    print("✅ Workflow created with 8 steps")
    
    # Check step names
    expected_steps = [
        "parse_request",
        "generate_code",
        "save_file",
        "initial_test",
        "error_analysis",
        "apply_fixes",
        "retest",
        "final_validation"
    ]
    
    actual_steps = [step.id for step in workflow.steps]
    assert actual_steps == expected_steps
    
    print(f"✅ Step IDs correct: {', '.join(actual_steps)}")
    
    return workflow


def test_workflow_progress():
    """Test workflow progress tracking"""
    print("\n" + "="*80)
    print("TEST 2: Workflow Progress Tracking")
    print("="*80)
    
    progress_updates = []
    
    def capture_progress(workflow):
        """Callback to capture progress"""
        summary = workflow.get_progress_summary()
        progress_updates.append({
            'percentage': summary['overall_percentage'],
            'step': workflow.steps[workflow.current_step_index].title,
            'status': workflow.steps[workflow.current_step_index].status
        })
        print(f"📊 {summary['overall_percentage']}% - {workflow.steps[workflow.current_step_index].title}")
    
    workflow = create_strategy_generation_workflow(on_update=capture_progress)
    
    # Simulate workflow execution
    print("\nSimulating workflow execution...\n")
    
    # Step 1: Parse request
    workflow.start_step("parse_request")
    workflow.update_step_progress("parse_request", 50, "Extracting parameters")
    workflow.complete_step("parse_request")
    
    # Step 2: Generate code
    workflow.start_step("generate_code")
    workflow.update_step_progress("generate_code", 30, "Building imports")
    workflow.update_step_progress("generate_code", 60, "Creating Strategy class")
    workflow.complete_step("generate_code")
    
    # Step 3: Save file
    workflow.start_step("save_file")
    workflow.update_step_progress("save_file", 50, "Writing to disk")
    workflow.complete_step("save_file")
    
    # Step 4: Initial test
    workflow.start_step("initial_test")
    workflow.update_step_progress("initial_test", 70, "Running backtest")
    workflow.complete_step("initial_test")
    
    # Skip error analysis and fixes (no errors)
    workflow.skip_step("error_analysis", "No errors found")
    workflow.skip_step("apply_fixes", "No fixes needed")
    workflow.skip_step("retest", "No retest needed")
    
    # Step 8: Final validation
    workflow.start_step("final_validation")
    workflow.update_step_progress("final_validation", 50, "Validating results")
    workflow.complete_step("final_validation")
    
    workflow.complete_workflow()
    
    print(f"\n✅ Captured {len(progress_updates)} progress updates")
    
    summary = workflow.get_progress_summary()
    assert summary['is_complete'] == True
    assert summary['completed_steps'] == 5  # 4 completed + 3 skipped
    assert summary['overall_percentage'] == 100
    
    print(f"✅ Workflow completed: {summary['completed_steps']}/{summary['total_steps']} steps")
    
    return workflow


def test_workflow_with_errors():
    """Test workflow with error handling"""
    print("\n" + "="*80)
    print("TEST 3: Workflow with Error Handling")
    print("="*80)
    
    workflow = create_strategy_generation_workflow()
    
    print("\nSimulating workflow with errors...\n")
    
    # Steps 1-3 complete normally
    workflow.start_step("parse_request")
    workflow.complete_step("parse_request")
    
    workflow.start_step("generate_code")
    workflow.complete_step("generate_code")
    
    workflow.start_step("save_file")
    workflow.complete_step("save_file")
    
    # Initial test fails
    workflow.start_step("initial_test")
    workflow.fail_step("initial_test", "ModuleNotFoundError: No module named 'pandas'")
    
    # Error analysis
    workflow.start_step("error_analysis")
    workflow.update_step_progress("error_analysis", 50, "Analyzing traceback")
    workflow.complete_step("error_analysis")
    
    # Apply fixes
    workflow.start_step("apply_fixes")
    workflow.update_step_progress("apply_fixes", 50, "Adding missing imports")
    workflow.complete_step("apply_fixes")
    
    # Retest succeeds
    workflow.start_step("retest")
    workflow.update_step_progress("retest", 70, "Running backtest again")
    workflow.complete_step("retest")
    
    # Final validation
    workflow.start_step("final_validation")
    workflow.complete_step("final_validation")
    
    workflow.complete_workflow()
    
    summary = workflow.get_progress_summary()
    assert summary['failed_steps'] == 1
    assert summary['completed_steps'] == 7
    
    print(f"✅ Workflow handled error: {summary['failed_steps']} failed, {summary['completed_steps']} completed")
    
    return workflow


def test_workflow_serialization():
    """Test workflow JSON serialization for frontend"""
    print("\n" + "="*80)
    print("TEST 4: Workflow JSON Serialization")
    print("="*80)
    
    workflow = create_strategy_generation_workflow()
    
    # Execute some steps
    workflow.start_step("parse_request")
    workflow.complete_step("parse_request")
    
    workflow.start_step("generate_code")
    workflow.update_step_progress("generate_code", 50, "Building Strategy class")
    
    # Convert to dict (as would be sent to frontend)
    workflow_dict = workflow.to_dict()
    
    # Verify structure
    assert 'workflow_name' in workflow_dict
    assert 'steps' in workflow_dict
    assert 'progress_summary' in workflow_dict
    
    print("✅ Workflow dictionary structure correct")
    
    # Convert to JSON
    workflow_json = json.dumps(workflow_dict, indent=2)
    
    print(f"\n✅ Serialized to JSON ({len(workflow_json)} bytes)")
    
    # Verify can be deserialized
    parsed = json.loads(workflow_json)
    assert parsed['workflow_name'] == "Strategy Generation"
    assert len(parsed['steps']) == 8
    
    print("✅ JSON can be parsed by frontend")
    
    # Print sample for visual inspection
    print("\n📋 Sample JSON for Frontend:")
    print("-" * 80)
    
    # Print first step details
    first_step = parsed['steps'][0]
    print(json.dumps({
        'step_example': first_step,
        'progress_summary': parsed['progress_summary']
    }, indent=2))
    
    return workflow_dict


def test_ai_agent_integration():
    """Test workflow tracking with AI developer agent"""
    print("\n" + "="*80)
    print("TEST 5: AI Agent Integration (Simulated)")
    print("="*80)
    
    print("\nNOTE: This test simulates AI agent behavior without API calls")
    print("To test with real AI, set GEMINI_API_KEY environment variable\n")
    
    workflow_states = []
    
    def capture_workflow(workflow):
        """Capture workflow state updates"""
        state = workflow.to_dict()
        workflow_states.append(state)
        
        summary = state['progress_summary']
        current_step = state['steps'][state['current_step_index']]
        
        print(f"📊 [{summary['overall_percentage']}%] {current_step['title']} - {current_step['status']}")
    
    # Simulate what the agent does
    print("Simulating generate_and_test_strategy() workflow:\n")
    
    workflow = create_strategy_generation_workflow(on_update=capture_workflow)
    
    # Simulate the full workflow
    workflow.start_step("parse_request")
    workflow.update_step_progress("parse_request", 50)
    workflow.complete_step("parse_request")
    
    workflow.start_step("generate_code")
    workflow.update_step_progress("generate_code", 30)
    workflow.update_step_progress("generate_code", 70)
    workflow.complete_step("generate_code")
    
    workflow.start_step("save_file")
    workflow.complete_step("save_file")
    
    workflow.start_step("initial_test")
    workflow.update_step_progress("initial_test", 80)
    workflow.complete_step("initial_test")
    
    workflow.skip_step("error_analysis", "No errors")
    workflow.skip_step("apply_fixes", "No fixes needed")
    workflow.skip_step("retest", "Not needed")
    
    workflow.start_step("final_validation")
    workflow.complete_step("final_validation")
    
    workflow.complete_workflow()
    
    print(f"\n✅ Captured {len(workflow_states)} workflow state updates")
    print(f"✅ Final state: {workflow.get_progress_summary()['overall_percentage']}% complete")
    
    return workflow_states


def test_frontend_compatibility():
    """Test that workflow format matches frontend expectations"""
    print("\n" + "="*80)
    print("TEST 6: Frontend Compatibility")
    print("="*80)
    
    workflow = create_strategy_generation_workflow()
    
    # Execute full workflow
    for step_id in ["parse_request", "generate_code", "save_file", "initial_test"]:
        workflow.start_step(step_id)
        workflow.complete_step(step_id)
    
    for step_id in ["error_analysis", "apply_fixes", "retest"]:
        workflow.skip_step(step_id, "Not needed")
    
    workflow.start_step("final_validation")
    workflow.complete_step("final_validation")
    workflow.complete_workflow()
    
    # Get workflow dict
    data = workflow.to_dict()
    
    # Verify frontend expected fields
    required_fields = [
        'workflow_name',
        'started_at',
        'completed_at',
        'steps',
        'current_step_index',
        'progress_summary'
    ]
    
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"
        print(f"✅ Field present: {field}")
    
    # Verify step structure
    step = data['steps'][0]
    step_fields = [
        'id', 'title', 'description', 'status',
        'started_at', 'completed_at', 'error_message',
        'substeps', 'current_substep', 'progress_percentage'
    ]
    
    for field in step_fields:
        assert field in step, f"Missing step field: {field}"
    
    print(f"✅ All step fields present")
    
    # Verify progress summary
    summary = data['progress_summary']
    summary_fields = [
        'workflow_name', 'total_steps', 'completed_steps',
        'failed_steps', 'in_progress_steps', 'overall_percentage',
        'current_step_index', 'is_complete', 'duration_seconds'
    ]
    
    for field in summary_fields:
        assert field in summary, f"Missing summary field: {field}"
    
    print(f"✅ All summary fields present")
    
    # Verify status values match frontend enum
    valid_statuses = ['pending', 'in_progress', 'completed', 'failed', 'skipped']
    
    for step in data['steps']:
        assert step['status'] in valid_statuses, f"Invalid status: {step['status']}"
    
    print(f"✅ All status values valid")
    
    print("\n✅ Workflow format is frontend-compatible!")
    
    return data


def run_all_tests():
    """Run all workflow tracking tests"""
    print("\n" + "="*80)
    print("WORKFLOW TRACKING INTEGRATION TEST SUITE")
    print("="*80)
    print("Testing complete workflow tracking system")
    print("="*80)
    
    tests = [
        test_workflow_creation,
        test_workflow_progress,
        test_workflow_with_errors,
        test_workflow_serialization,
        test_ai_agent_integration,
        test_frontend_compatibility
    ]
    
    results = []
    
    for test in tests:
        try:
            test()
            results.append((test.__name__, "PASSED", None))
        except Exception as e:
            results.append((test.__name__, "FAILED", str(e)))
            print(f"\n❌ Test failed: {e}")
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, status, _ in results if status == "PASSED")
    failed = sum(1 for _, status, _ in results if status == "FAILED")
    
    for name, status, error in results:
        icon = "✅" if status == "PASSED" else "❌"
        print(f"{icon} {name}: {status}")
        if error:
            print(f"   Error: {error}")
    
    print("\n" + "="*80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*80)
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Workflow tracking is ready to use.")
        print("\n📚 Next steps:")
        print("   1. Integrate with Django API (see WORKFLOW_TRACKING_INTEGRATION.md)")
        print("   2. Test with actual strategy generation")
        print("   3. Verify frontend displays workflow correctly")
        print("   4. Add real-time updates (optional)")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please fix before deploying.")
    
    return passed == len(tests)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
