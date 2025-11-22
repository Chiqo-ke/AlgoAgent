"""
Iterative Agent Loop - Continuously improve strategy until it works.

Flow:
1. Coder generates strategy
2. Tester validates and returns detailed report
3. If failed → Debugger analyzes + creates fix tasks
4. Coder/Architect implement fixes
5. Repeat until tests pass or max iterations reached
"""
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class IterativeLoop:
    """Manages iterative improvement loop for strategy development."""
    
    def __init__(
        self,
        cli,
        max_iterations: int = 5,
        auto_fix: bool = True
    ):
        """
        Initialize iterative loop.
        
        Args:
            cli: MultiAgentCLI instance
            max_iterations: Maximum fix attempts before giving up
            auto_fix: If True, automatically retry fixes
        """
        self.cli = cli
        self.max_iterations = max_iterations
        self.auto_fix = auto_fix
        self.iteration_history = []
    
    def run_until_success(
        self,
        workflow_id: str,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Execute workflow with automatic retries until success.
        
        Args:
            workflow_id: Workflow to execute
            verbose: Print detailed progress
            
        Returns:
            Final result with iteration history
        """
        print(f"\n{'='*70}")
        print(f"   ITERATIVE LOOP: {workflow_id}")
        print(f"   Max Iterations: {self.max_iterations}")
        print(f"   Auto-Fix: {'ENABLED' if self.auto_fix else 'DISABLED'}")
        print(f"{'='*70}\n")
        
        iteration = 0
        all_tests_passed = False
        
        while iteration < self.max_iterations and not all_tests_passed:
            iteration += 1
            
            print(f"\n{'─'*70}")
            print(f"🔄 ITERATION {iteration}/{self.max_iterations}")
            print(f"{'─'*70}\n")
            
            # CRITICAL: Record iteration start time BEFORE execution
            iteration_start_time = datetime.now()
            iteration_start = time.time()
            
            # Step 1: Execute workflow (Coder/Architect generate code)
            print(f"📝 Step 1: Executing workflow tasks...")
            print(f"   ⏰ Iteration started at: {iteration_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print()
            exec_result = self.cli.execute_workflow(workflow_id, auto_execute=True)
            
            if exec_result.get('status') != 'completed':
                print(f"   ❌ Workflow execution failed")
                self._record_iteration(iteration, 'execution_failed', exec_result)
                break
            
            print(f"   ✅ Workflow execution completed")
            print()
            
            # Step 2: Test generated code - ONLY test files created in THIS iteration
            print(f"🧪 Step 2: Testing NEW strategies from this iteration...")
            test_result = self.cli.test_workflow(workflow_id, iteration_start_time=iteration_start_time)
            
            summary = test_result.get('summary', {})
            total = summary.get('total', 0)
            passed = summary.get('passed', 0)
            failed = summary.get('failed', 0)
            
            iteration_duration = time.time() - iteration_start
            
            # Record iteration
            self._record_iteration(
                iteration,
                'completed',
                {
                    'execution': exec_result,
                    'tests': test_result,
                    'duration': iteration_duration
                }
            )
            
            # Check if all tests passed
            if failed == 0 and passed > 0:
                all_tests_passed = True
                print(f"\n{'='*70}")
                print(f"✅ SUCCESS! All tests passed in iteration {iteration}")
                print(f"{'='*70}\n")
                break
            
            print(f"\n📊 Test Results:")
            print(f"   Total: {total}")
            print(f"   Passed: {passed} ✅")
            print(f"   Failed: {failed} ❌")
            print()
            
            # Step 3: Analyze failures and create fix tasks
            if self.auto_fix and iteration < self.max_iterations:
                print(f"🔧 Step 3: Analyzing failures and generating fixes...")
                
                fix_tasks = self._analyze_and_create_fixes(
                    test_result,
                    workflow_id,
                    iteration
                )
                
                if fix_tasks:
                    print(f"   ✅ Created {len(fix_tasks)} fix task(s)")
                    # Add fix tasks to workflow
                    self._add_fix_tasks_to_workflow(workflow_id, fix_tasks)
                else:
                    print(f"   ℹ️  No new fix tasks generated")
                
                # Check if there are ANY pending tasks left to execute
                pending_tasks = self._get_pending_tasks(workflow_id)
                
                if not pending_tasks:
                    print(f"   ✅ No pending tasks remaining - iteration complete")
                    break
                
                print(f"   🔄 Continuing with {len(pending_tasks)} pending task(s)...")
            else:
                print(f"\n⚠️  Auto-fix disabled or max iterations reached")
                break
        
        # Final summary
        return self._generate_final_report(
            workflow_id,
            all_tests_passed,
            iteration
        )
    
    def _record_iteration(
        self,
        iteration: int,
        status: str,
        data: Dict[str, Any]
    ):
        """Record iteration results for history."""
        self.iteration_history.append({
            'iteration': iteration,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'data': data
        })
    
    def _analyze_and_create_fixes(
        self,
        test_result: Dict[str, Any],
        workflow_id: str,
        iteration: int
    ) -> List[Dict[str, Any]]:
        """
        Analyze test failures and create fix tasks.
        
        Args:
            test_result: Test results from Tester Agent
            workflow_id: Current workflow ID
            iteration: Current iteration number
            
        Returns:
            List of fix tasks to add to workflow
        """
        fix_tasks = []
        
        results = test_result.get('results', [])
        failed_tests = [r for r in results if r.get('status') != 'ready']
        
        if not failed_tests:
            return []
        
        print(f"\n   Analyzing {len(failed_tests)} failed test(s)...\n")
        
        for result in failed_tests:
            strategy_name = result.get('strategy', 'unknown')
            
            # Get detailed error information
            errors = result.get('errors', [])
            error_msg = result.get('error', 'Unknown error')
            strategy_file = result.get('strategy', 'unknown')
            
            # Use first error if available, otherwise use error field
            if errors:
                primary_error = errors[0]
                error_text = primary_error.get('message', error_msg)
                full_traceback = primary_error.get('full_traceback', '')
            else:
                error_text = error_msg
                # Get full output for better context
                full_traceback = result.get('full_output', result.get('output', ''))
            
            # Classify error type
            error_type = self._classify_error(error_text)
            
            print(f"   📝 {strategy_name}")
            print(f"      Type: {error_type}")
            print(f"      Error: {error_text[:150]}..." if len(error_text) > 150 else f"      Error: {error_text}")
                
            
            # Create appropriate fix task with clean, sanitized instructions
            if error_type == 'syntax_error':
                fix_task = {
                    'id': f"fix_syntax_{strategy_name}_iter{iteration}",
                    'title': f"Fix syntax error in {strategy_name}",
                    'description': """Fix syntax error in the strategy code.

**Task:** Review and correct Python syntax errors

**Fix Instructions:**
1. Check for common syntax issues:
   - Missing or extra parentheses, brackets, or braces
   - Unbalanced quotes (single or double)
   - Incorrect indentation (use 4 spaces per level)
   - Invalid Python keywords or operators
2. Fix the syntax error while preserving the original logic
3. Ensure code follows Python 3.11+ syntax
4. Validate all function definitions and classes are properly structured
""",
                    'agent_role': 'coder',
                    'priority': 1,
                    'dependencies': [],
                    'metadata': {
                        'fix_type': 'syntax',
                        'target_file': f"Backtest/codes/{strategy_file}",
                        'error_details': error_text,
                        'full_traceback': full_traceback[:2000],
                        'iteration': iteration,
                        'auto_fix': True
                    }
                }
                fix_tasks.append(fix_task)
            
            elif error_type == 'import_error':
                fix_task = {
                    'id': f"fix_imports_{strategy_name}_iter{iteration}",
                    'title': f"Fix import errors in {strategy_name}",
                    'description': """Fix missing import in the strategy.

**Task:** Add required import statements

**Required Imports:**
Ensure these imports are at the top of the file:
- from typing import Dict, List, Optional
- import pandas as pd
- import numpy as np
- from adapters.base_adapter import BaseAdapter

**Fix Instructions:**
1. Add the missing import statement
2. Verify all imports match the project structure
3. Check for typos in import names
4. Remove any unused imports to keep code clean
""",
                    'agent_role': 'coder',
                    'priority': 1,
                    'dependencies': [],
                    'metadata': {
                        'fix_type': 'imports',
                        'target_file': f"Backtest/codes/{strategy_file}",
                        'error_details': error_text,
                        'full_traceback': full_traceback[:2000],
                        'iteration': iteration,
                        'auto_fix': True
                    }
                }
                fix_tasks.append(fix_task)
            
            elif error_type == 'logic_error':
                fix_task = {
                    'id': f"fix_logic_{strategy_name}_iter{iteration}",
                    'title': f"Fix logic errors in {strategy_name}",
                    'description': """Fix runtime logic error in the strategy.

**Task:** Correct strategy logic to pass tests

**Common Issues:**
- AttributeError: Verify object has required attribute or method
- TypeError: Check function arguments match expected types
- KeyError: Ensure dictionary key exists before accessing
- IndexError: Validate list or array indices are within bounds
- ValueError: Add input validation for invalid values

**Fix Instructions:**
1. Review the code logic at the point of failure
2. Add defensive checks where needed
3. Add proper error handling where appropriate
4. Ensure data structures are initialized correctly
5. Validate function inputs before processing
""",
                    'agent_role': 'coder',  # Changed to coder for faster fixes
                    'priority': 2,
                    'dependencies': [],
                    'metadata': {
                        'fix_type': 'logic',
                        'target_file': f"Backtest/codes/{strategy_file}",
                        'error_details': error_text,
                        'full_traceback': full_traceback[:2000],
                        'iteration': iteration,
                        'test_output': full_traceback[:2000],
                        'auto_fix': True
                    }
                }
                fix_tasks.append(fix_task)
            
            elif error_type == 'contract_mismatch':
                fix_task = {
                    'id': f"fix_contract_{strategy_name}_iter{iteration}",
                    'title': f"Fix contract mismatch in {strategy_name}",
                    'description': """Fix contract or assertion mismatch.

**Task:** Ensure strategy meets contract specifications

**Fix Instructions:**
1. Review contract specifications carefully
2. Verify all required methods are implemented
3. Check function signatures match contract
4. Ensure return types are correct
5. Test edge cases and boundary conditions
""",
                    'agent_role': 'architect',
                    'priority': 1,
                    'dependencies': [],
                    'metadata': {
                        'fix_type': 'contract',
                        'target_file': f"Backtest/codes/{strategy_name}.py",
                        'error_details': error_text,
                        'iteration': iteration
                    }
                }
                fix_tasks.append(fix_task)
            else:
                # Unknown error - route to debugger
                fix_task = {
                    'id': f"fix_unknown_{strategy_name}_iter{iteration}",
                    'title': f"Debug {strategy_name} test failure",
                    'description': """Debug and fix the failing strategy.

**Task:** Analyze and resolve test failure

**Investigation Steps:**
1. Check if test timeout occurred (optimize performance)
2. Verify DataFrame has required columns
3. Review indicator calculations
4. Check entry and exit conditions
5. Add error handling where needed
6. Test with sample data
""",
                    'agent_role': 'debugger',
                    'priority': 3,
                    'dependencies': [],
                    'metadata': {
                        'fix_type': 'unknown',
                        'target_file': f"Backtest/codes/{strategy_name}.py",
                        'error_details': error_text,
                        'iteration': iteration,
                        'full_output': full_traceback
                    }
                }
                fix_tasks.append(fix_task)
        
        print()
        return fix_tasks
    
    def _classify_error(self, error_message: str) -> str:
        """Classify error type based on error message."""
        error_lower = error_message.lower()
        
        # Syntax errors
        if any(keyword in error_lower for keyword in ['syntaxerror', 'invalid syntax', 'indentationerror', 'unexpected indent']):
            return 'syntax_error'
        
        # Import errors
        elif any(keyword in error_lower for keyword in ['importerror', 'modulenotfounderror', 'no module named', 'cannot import']):
            return 'import_error'
        
        # Contract/interface violations (test assertions)
        elif any(keyword in error_lower for keyword in ['assertionerror', 'assert ', 'expected', 'should be', 'must be']):
            return 'contract_mismatch'
        
        # Logic errors (runtime exceptions)
        elif any(keyword in error_lower for keyword in ['attributeerror', 'typeerror', 'keyerror', 'valueerror', 'nameerror', 'indexerror']):
            return 'logic_error'
        
        else:
            return 'unknown_error'
    
    def _add_fix_tasks_to_workflow(
        self,
        workflow_id: str,
        fix_tasks: List[Dict[str, Any]]
    ):
        """Add fix tasks to existing workflow."""
        # Get workflow state
        workflow_state = self.cli.orchestrator.workflows.get(workflow_id)
        
        if not workflow_state:
            print(f"   ⚠️  Workflow not found: {workflow_id}")
            return
        
        # Get todo list
        todo_list = self.cli.orchestrator.todo_lists.get(workflow_state.todo_list_id)
        
        if not todo_list:
            print(f"   ⚠️  TodoList not found")
            return
        
        # Add fix tasks to todo list
        for fix_task in fix_tasks:
            todo_list['items'].append(fix_task)
            print(f"      + {fix_task['id']}: {fix_task['title']}")
        
        # Update todo list file
        todo_path = self.cli.output_dir / f"{workflow_state.todo_list_id}_todolist.json"
        todo_path.write_text(json.dumps(todo_list, indent=2), encoding='utf-8')
        
        print(f"   ✅ Updated TodoList with fix tasks")
        
        # CRITICAL: Immediately reload the workflow tasks so the orchestrator
        # knows about the new fix tasks for the next iteration
        self.cli.orchestrator.reload_workflow_tasks(workflow_id)
        print(f"   🔄 Orchestrator reloaded with {len(fix_tasks)} new fix task(s)")
    
    def _get_pending_tasks(self, workflow_id: str) -> List[Dict[str, Any]]:
        """
        Get all pending tasks for a workflow.
        
        Args:
            workflow_id: Workflow to check
            
        Returns:
            List of pending task dictionaries
        """
        workflow_state = self.cli.orchestrator.workflows.get(workflow_id)
        if not workflow_state:
            return []
        
        todo_list = self.cli.orchestrator.todo_lists.get(workflow_state.todo_list_id)
        if not todo_list:
            return []
        
        pending = []
        for task in todo_list.get('items', []):
            # Check task state in orchestrator
            task_state = workflow_state.tasks.get(task['id'])
            
            # Task is pending if:
            # 1. It exists in task_state and status is 'pending', OR
            # 2. It doesn't exist in task_state yet (newly added task)
            if task_state:
                if task_state.status.value == 'pending':
                    pending.append(task)
            else:
                # Newly added task not yet tracked in workflow state
                # Check if it has explicit status field
                task_status = task.get('status', 'pending')
                if task_status != 'completed':
                    pending.append(task)
        
        return pending
        
        return pending
    
    def _generate_final_report(
        self,
        workflow_id: str,
        success: bool,
        total_iterations: int
    ) -> Dict[str, Any]:
        """Generate final report with iteration history."""
        # Get the updated TodoList from the workflow
        workflow_state = self.cli.orchestrator.workflows.get(workflow_id)
        updated_todo_list = None
        if workflow_state:
            updated_todo_list = self.cli.orchestrator.todo_lists.get(workflow_state.todo_list_id)
        
        report = {
            'workflow_id': workflow_id,
            'success': success,
            'total_iterations': total_iterations,
            'max_iterations': self.max_iterations,
            'completed_at': datetime.now().isoformat(),
            'iteration_history': self.iteration_history,
            'updated_todo_list': updated_todo_list  # Add the updated TodoList
        }
        
        # Save report
        report_path = self.cli.output_dir / f"iteration_report_{workflow_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
        
        print(f"\n{'='*70}")
        print(f"📊 FINAL REPORT")
        print(f"{'='*70}")
        print(f"Status: {'✅ SUCCESS' if success else '❌ FAILED'}")
        print(f"Total Iterations: {total_iterations}/{self.max_iterations}")
        print(f"Report: {report_path.name}")
        print(f"{'='*70}\n")
        
        return report
