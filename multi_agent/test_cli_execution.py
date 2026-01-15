"""
Quick test to verify CLI can execute a coder task with RequestRouter.
"""
import sys
import json
from pathlib import Path

# Add multi_agent to path
sys.path.insert(0, str(Path(__file__).parent))

from cli import MultiAgentCLI

def test_cli_coder_execution():
    """Test that CLI can execute coder tasks with RequestRouter enabled."""
    print("\n" + "=" * 70)
    print("  TESTING CLI CODER EXECUTION WITH REQUESTROUTER")
    print("=" * 70 + "\n")
    
    # Initialize CLI
    cli = MultiAgentCLI()
    
    # Verify CLI state
    print(f"✓ CLI Initialized")
    print(f"  AI Mode: {cli.ai_mode}")
    print(f"  Use Router: {cli.use_router}")
    print(f"  API Key Flag: {cli.api_key}")
    
    assert cli.ai_mode, "CLI should have AI capability"
    assert cli.use_router, "CLI should use RequestRouter"
    assert cli.api_key == "ROUTER_MODE", "API key should be ROUTER_MODE flag"
    
    # Create a simple task
    task = {
        'id': 'test_task_001',
        'title': 'Test Code Generation',
        'agent_role': 'coder',
        'description': 'Generate a simple EMA crossover strategy',
        'contract_path': None  # Will be auto-created
    }
    
    print(f"\n✓ Created test task: {task['title']}")
    
    # Execute the task
    print(f"\n⏳ Executing coder task...")
    try:
        result = cli._execute_coder_task(task)
        
        print(f"\n✓ Task execution completed!")
        print(f"  Status: {result.get('status', 'unknown')}")
        
        if result.get('status') == 'skipped':
            print(f"\n❌ FAILED: Task was skipped!")
            print(f"  Message: {result.get('message')}")
            return False
        
        if result.get('status') in ['ready', 'needs_review']:
            print(f"\n✅ SUCCESS: Code generation worked!")
            print(f"  Artifacts: {len(result.get('artifacts', []))}")
            return True
        
        print(f"\n⚠️  Unexpected status: {result.get('status')}")
        return False
        
    except Exception as e:
        print(f"\n❌ FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_cli_coder_execution()
    
    print("\n" + "=" * 70)
    if success:
        print("  ✅ CLI CODER EXECUTION TEST PASSED")
    else:
        print("  ❌ CLI CODER EXECUTION TEST FAILED")
    print("=" * 70 + "\n")
    
    sys.exit(0 if success else 1)
