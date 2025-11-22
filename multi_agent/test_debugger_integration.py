"""
Test Debugger Agent Integration

Verifies that the debugger agent can analyze failures and create fix tasks.
"""
import sys
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from cli import MultiAgentCLI


def test_debugger_task_execution():
    """Test that debugger agent can process a fix task."""
    print("\n" + "="*70)
    print("TEST: Debugger Agent Task Execution")
    print("="*70 + "\n")
    
    cli = MultiAgentCLI()
    
    # Create a mock failing strategy file
    test_strategy_path = cli.workspace_root / "multi_agent" / "Backtest" / "codes" / "test_failing_strategy.py"
    test_strategy_path.parent.mkdir(exist_ok=True, parents=True)
    
    failing_code = '''
"""Test failing strategy with syntax error"""
from typing import Dict
import pandas as pd

class Strategy:
    def __init__(self, config: Dict):
        self.config = config
    
    def prepare_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        # Missing closing parenthesis - syntax error
        df['ema_30'] = df['Close'].ewm(span=30.mean()
        return df
'''
    
    test_strategy_path.write_text(failing_code, encoding='utf-8')
    print(f"✓ Created test failing strategy: {test_strategy_path.name}\n")
    
    # Create a debugger task
    debugger_task = {
        'id': 'test_debug_syntax',
        'title': 'Fix syntax error in test strategy',
        'description': 'Test debugger agent functionality',
        'agent_role': 'debugger',
        'priority': 1,
        'dependencies': [],
        'metadata': {
            'fix_type': 'syntax_error',
            'target_file': 'Backtest/codes/test_failing_strategy.py',
            'error_details': 'SyntaxError: invalid syntax at line 11',
            'full_traceback': '''  File "test_failing_strategy.py", line 11
    df['ema_30'] = df['Close'].ewm(span=30.mean()
                                                 ^
SyntaxError: invalid syntax''',
            'workflow_id': 'test_workflow_001',
            'iteration': 0,
            'auto_fix': True
        }
    }
    
    # Execute the debugger task
    print("Executing debugger task...\n")
    result = cli._execute_debugger_task(debugger_task)
    
    # Verify results
    print(f"\n{'='*70}")
    print("RESULTS:")
    print(f"{'='*70}\n")
    print(f"Status: {result.get('status')}")
    print(f"Fix Task ID: {result.get('fix_task_id', 'N/A')}")
    print(f"Fix Strategy: {result.get('fix_strategy', 'N/A')}")
    print(f"Message: {result.get('message', 'N/A')}")
    
    # Check if fix task was created
    if result.get('status') == 'completed':
        print(f"\n✅ SUCCESS: Debugger agent created fix task successfully!")
        return True
    else:
        print(f"\n❌ FAILED: Debugger agent did not complete successfully")
        print(f"Error: {result.get('message', 'Unknown error')}")
        return False


def test_debugger_fix_types():
    """Test different fix types the debugger can handle."""
    print("\n" + "="*70)
    print("TEST: Debugger Fix Type Analysis")
    print("="*70 + "\n")
    
    cli = MultiAgentCLI()
    
    test_cases = [
        {
            'fix_type': 'syntax_error',
            'error': 'SyntaxError: invalid syntax',
            'expected_strategy': 'syntax_correction'
        },
        {
            'fix_type': 'import_error',
            'error': 'ModuleNotFoundError: No module named numpy',
            'expected_strategy': 'add_missing_imports'
        },
        {
            'fix_type': 'logic_error',
            'error': 'KeyError: Close',
            'expected_strategy': 'fix_runtime_logic'
        },
        {
            'fix_type': 'unknown_error',
            'error': 'Test timeout after 30 seconds',
            'expected_strategy': 'general_debug'
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['fix_type']}")
        print(f"{'─'*70}")
        
        fix_instructions = cli._analyze_failure_for_fix(
            strategy_code='# Test code',
            error_details=test_case['error'],
            full_traceback=f"Traceback: {test_case['error']}",
            fix_type=test_case['fix_type']
        )
        
        strategy = fix_instructions.get('strategy')
        print(f"Error: {test_case['error']}")
        print(f"Expected Strategy: {test_case['expected_strategy']}")
        print(f"Actual Strategy: {strategy}")
        
        if strategy == test_case['expected_strategy']:
            print(f"✓ PASSED")
        else:
            print(f"✗ FAILED - Strategy mismatch")
            all_passed = False
    
    print(f"\n{'='*70}")
    if all_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print(f"{'='*70}\n")
    
    return all_passed


if __name__ == '__main__':
    print("\n" + "="*70)
    print("DEBUGGER AGENT INTEGRATION TESTS")
    print("="*70)
    
    # Run tests
    test1_passed = test_debugger_fix_types()
    test2_passed = test_debugger_task_execution()
    
    # Final summary
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    print(f"Fix Type Analysis: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Task Execution: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED - Debugger Agent is working!")
        sys.exit(0)
    else:
        print("\n⚠️  SOME TESTS FAILED - Review output above")
        sys.exit(1)
