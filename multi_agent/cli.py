"""
Multi-Agent System Command-Line Interface

Interactive CLI for submitting strategy requests and monitoring workflows.

Usage:
    python cli.py                    # Interactive mode
    python cli.py --request "..."    # Single request mode
    python cli.py --status <workflow_id>  # Check workflow status
    python cli.py --list             # List all workflows
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
import os

env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    print(f"⚠️  Warning: .env file not found at {env_path}")

# Also check for GOOGLE_API_KEY mapping from GEMINI_API_KEY
if not os.getenv('GOOGLE_API_KEY') and os.getenv('GEMINI_API_KEY'):
    os.environ['GOOGLE_API_KEY'] = os.getenv('GEMINI_API_KEY')
    print(f"✓ Loaded GEMINI_API_KEY from .env")


class MultiAgentCLI:
    """Command-line interface for multi-agent system."""
    
    def __init__(self):
        # Lazy imports to speed up CLI startup
        from planner_service.planner import PlannerService
        from orchestrator_service.orchestrator import MinimalOrchestrator
        from contracts.message_bus import InMemoryMessageBus
        
        self.workspace_root = Path(__file__).parent.parent
        self.output_dir = self.workspace_root / "multi_agent" / "workflows"
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.message_bus = InMemoryMessageBus()
        
        # Initialize Planner with API key if available
        api_key = os.getenv('GOOGLE_API_KEY')
        if api_key:
            self.planner = PlannerService(api_key=api_key)
            self.ai_mode = True
            self.api_key = api_key
            print("🤖 AI Mode: ENABLED (using Gemini API)")
        else:
            # No Planner without API key, will use template mode
            self.planner = None
            self.ai_mode = False
            self.api_key = None
            print("📋 Template Mode: ENABLED (no AI API key)")
        
        # Initialize Orchestrator
        self.orchestrator = MinimalOrchestrator(use_message_bus=False)
        
        # Agent instances (lazy loaded)
        self.coder_agent = None
        self.architect_agent = None
        
        print(f"📁 Workspace: {self.workspace_root}")
        print(f"📂 Workflows: {self.output_dir}")
        print()
    
    def submit_request(self, user_request: str) -> Dict[str, Any]:
        """
        Submit a new strategy request.
        
        Args:
            user_request: Natural language strategy description
            
        Returns:
            Dictionary with workflow_id and status
        """
        print(f"📝 Request: {user_request}")
        print()
        
        # Step 1: Generate TodoList with Planner
        print("⏳ Step 1/3: Generating TodoList...")
        start_time = time.time()
        
        try:
            if self.ai_mode and self.planner:
                print("   Using AI (Gemini API)...")
                todo_list = self.planner.create_plan(
                    user_request=user_request,
                    workflow_name=f"CLI Request {datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
            else:
                print("   Using template mode...")
                todo_list = self._create_template_todolist(user_request)
            
            duration = time.time() - start_time
            print(f"   ✓ TodoList created in {duration:.2f}s")
            print(f"   ✓ Workflow ID: {todo_list['todo_list_id']}")
            print(f"   ✓ Tasks: {len(todo_list['items'])}")
            print()
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            if self.ai_mode:
                print("   ⚠️  Falling back to template mode...")
                todo_list = self._create_template_todolist(user_request)
                print(f"   ✓ TodoList created (template)")
                print()
        
        # Step 2: Save TodoList
        workflow_id = todo_list['todo_list_id']
        todo_path = self.output_dir / f"{workflow_id}_todolist.json"
        todo_path.write_text(json.dumps(todo_list, indent=2), encoding='utf-8')
        print(f"💾 Step 2/3: Saved TodoList to {todo_path.name}")
        print()
        
        # Step 3: Load workflow into Orchestrator
        print("⏳ Step 3/3: Loading workflow into Orchestrator...")
        try:
            # Load todo list and create workflow
            todo_list_id = self.orchestrator.load_todo_list(todo_path)
            workflow_id = self.orchestrator.create_workflow(todo_list_id)
            
            # Get workflow state
            workflow_state = self.orchestrator.workflows.get(workflow_id)
            
            print(f"   ✓ Workflow loaded: {workflow_id}")
            print(f"   ✓ Tasks queued: {len(workflow_state.tasks)}")
            print()
            
            # Show task summary
            print("📋 Task Summary:")
            todo_list = self.orchestrator.todo_lists[todo_list_id]
            for item in todo_list['items']:
                print(f"   - {item['id']}: {item['title']} ({item['agent_role']})")
            print()
            
            return {
                'workflow_id': workflow_id,
                'status': 'queued',
                'tasks': len(workflow_state.tasks),
                'todolist_path': str(todo_path)
            }
            
        except Exception as e:
            print(f"   ❌ Failed to load workflow: {e}")
            import traceback
            traceback.print_exc()
            return {
                'workflow_id': workflow_id,
                'status': 'failed',
                'error': str(e),
                'todolist_path': str(todo_path)
            }
    
    def execute_workflow(self, workflow_id: str, auto_execute: bool = True) -> Dict[str, Any]:
        """
        Execute a workflow by processing its tasks.
        
        Args:
            workflow_id: Workflow identifier
            auto_execute: If True, automatically execute coder tasks
            
        Returns:
            Dictionary with execution results
        """
        print(f"\n🔄 Executing workflow: {workflow_id}")
        print()
        
        # Get workflow state
        workflow_state = self.orchestrator.workflows.get(workflow_id)
        
        if not workflow_state:
            print(f"   ❌ Workflow not found: {workflow_id}")
            return {'status': 'error', 'message': 'Workflow not found'}
        
        # Get todo list for task details
        todo_list = self.orchestrator.todo_lists.get(workflow_state.todo_list_id)
        
        if not todo_list:
            print(f"   ❌ TodoList not found: {workflow_state.todo_list_id}")
            return {'status': 'error', 'message': 'TodoList not found'}
        
        results = {}
        
        # Process each task
        for task_id, task_state in workflow_state.tasks.items():
            # Find task details
            task_details = None
            for item in todo_list['items']:
                if item['id'] == task_id:
                    task_details = item
                    break
            
            if not task_details:
                print(f"   ⚠️  Task details not found: {task_id}")
                continue
            
            agent_role = task_details['agent_role']
            
            print(f"📋 Task: {task_id}")
            print(f"   Title: {task_details['title']}")
            print(f"   Agent: {agent_role}")
            print(f"   Status: {task_state.status.value}")
            print()
            
            # Only execute pending/ready tasks
            if task_state.status.value not in ['pending', 'ready']:
                print(f"   ⏭️  Skipping (status: {task_state.status.value})")
                print()
                continue
            
            # Execute based on agent role
            if agent_role == 'architect' and auto_execute:
                result = self._execute_architect_task(task_details)
                results[task_id] = result
            elif agent_role == 'coder' and auto_execute:
                result = self._execute_coder_task(task_details)
                results[task_id] = result
            elif agent_role == 'tester' and auto_execute:
                result = self._execute_tester_task(task_details)
                results[task_id] = result
            else:
                print(f"   ⏸️  Manual execution required or not implemented")
                results[task_id] = {'status': 'pending', 'message': 'Not executed'}
            
            print()
        
        return {
            'workflow_id': workflow_id,
            'status': 'completed',
            'results': results
        }
    
    def _execute_coder_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a coder agent task.
        
        Args:
            task: Task dictionary from TodoList
            
        Returns:
            Execution result
        """
        print(f"   ⏳ Executing Coder Agent...")
        
        if not self.api_key:
            print(f"   ⚠️  No API key - using template mode")
            return {
                'status': 'skipped',
                'message': 'No API key available for AI code generation'
            }
        
        try:
            # Lazy load Coder Agent
            if not self.coder_agent:
                from agents.coder_agent.coder import CoderAgent
                self.coder_agent = CoderAgent(
                    agent_id="cli_coder",
                    message_bus=self.message_bus,
                    gemini_api_key=self.api_key,
                    workspace_root=self.workspace_root / "multi_agent"
                )
                print(f"   ✓ Coder Agent initialized")
            
            # Create contract if missing
            if 'contract_path' not in task or not task['contract_path']:
                contract_id = f"contract_{task['id']}"
                contract = {
                    "contract_id": contract_id,
                    "description": task.get('description', 'Strategy implementation contract'),
                    "interfaces": {
                        "run_backtest": {
                            "description": "Execute backtesting strategy",
                            "inputs": ["adapter", "df with OHLCV", "config"],
                            "outputs": ["Backtest results with metrics"]
                        }
                    }
                }
                contract_path = self.output_dir / f"{contract_id}.json"
                contract_path.write_text(json.dumps(contract, indent=2))
                task['contract_path'] = str(contract_path)
                print(f"   ✓ Created contract: {contract_path.name}")
            
            # Execute the task
            start_time = time.time()
            result = self.coder_agent.implement_task(task)
            duration = time.time() - start_time
            
            print(f"   ✓ Execution completed in {duration:.2f}s")
            print(f"   ✓ Status: {result.status}")
            
            if result.status == 'ready':
                print(f"   ✓ Generated {len(result.artifacts)} artifact(s)")
                for artifact in result.artifacts:
                    print(f"      - {artifact.file_path}")
            elif result.status == 'failed':
                print(f"   ❌ Error: {result.error_message}")
            
            return {
                'status': result.status,
                'duration': duration,
                'artifacts': [a.file_path for a in result.artifacts] if result.artifacts else [],
                'error': result.error_message if result.error_message else None
            }
            
        except Exception as e:
            print(f"   ❌ Execution failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _execute_architect_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an architect agent task.
        
        Args:
            task: Task dictionary from TodoList
            
        Returns:
            Execution result
        """
        print(f"   ⏳ Executing Architect Agent...")
        
        try:
            # Lazy load Architect Agent
            if not self.architect_agent:
                from agents.architect_agent.architect import ArchitectAgent
                self.architect_agent = ArchitectAgent(
                    message_bus=self.message_bus,
                    api_key=self.api_key
                )
                print(f"   ✓ Architect Agent initialized")
            
            # Execute the task (async wrapped)
            start_time = time.time()
            import asyncio
            
            # Run async design_contract in sync context
            async def run_design():
                return await self.architect_agent._design_contract(
                    task_id=task.get('id', 'unknown'),
                    title=task.get('title', ''),
                    description=task.get('description', ''),
                    requirements=task
                )
            
            # Get or create event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            contract = loop.run_until_complete(run_design())
            duration = time.time() - start_time
            
            print(f"   ✓ Execution completed in {duration:.2f}s")
            print(f"   ✓ Contract: {contract.contract_id}")
            print(f"   ✓ Interfaces: {len(contract.interfaces)}")
            print(f"   ✓ Examples: {len(contract.examples)}")
            
            # Save contract to file
            contract_path = self.output_dir / f"{contract.contract_id}.json"
            contract_data = {
                "contract_id": contract.contract_id,
                "name": contract.name,
                "description": contract.description,
                "interfaces": contract.interfaces,
                "data_models": contract.data_models,
                "examples": contract.examples,
                "test_skeleton": contract.test_skeleton,
                "fixtures": contract.fixtures,
                "created_at": contract.created_at
            }
            contract_path.write_text(json.dumps(contract_data, indent=2))
            print(f"   ✓ Saved contract: {contract_path.name}")
            
            # Generate fixtures if any
            fixtures = []
            if contract.fixtures:
                print(f"   ✓ Generated {len(contract.fixtures)} fixture(s):")
                for fixture_name in contract.fixtures:
                    print(f"      - {fixture_name}")
                    fixtures.append(fixture_name)
            
            return {
                'status': 'ready',
                'duration': duration,
                'contract': contract_data,
                'fixtures': fixtures,
                'contract_path': str(contract_path)
            }
            
        except Exception as e:
            print(f"   ❌ Execution failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _execute_tester_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tester agent task.
        
        Runs tests in Docker sandbox, validates SimBroker results.
        
        Args:
            task: Task dictionary from TodoList
            
        Returns:
            Execution result with test metrics
        """
        print(f"   ⏳ Executing Tester Agent...")
        
        try:
            # Lazy load Tester Agent
            from agents.tester_agent.tester import TesterAgent
            
            tester = TesterAgent(use_redis=False)
            print(f"   ✓ Tester Agent initialized")
            
            # Get acceptance criteria (test commands to run)
            acceptance = task.get('acceptance_criteria', {})
            tests = acceptance.get('tests', [])
            
            if not tests:
                print(f"   ⚠️  No tests defined in acceptance criteria")
                return {
                    'status': 'skipped',
                    'message': 'No tests to execute'
                }
            
            print(f"   ⏳ Running {len(tests)} test(s) in Docker sandbox...")
            start_time = time.time()
            
            # Create test event (simulating orchestrator dispatch)
            from contracts import Event, EventType
            
            event = Event.create(
                event_type=EventType.TASK_DISPATCHED,
                correlation_id=f"cli_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                workflow_id=task.get('workflow_id', 'cli_workflow'),
                task_id=task.get('id', 'test_task'),
                data={'task': task},
                source='cli'
            )
            
            # Handle task (runs tests in sandbox)
            tester.handle_task(event)
            
            duration = time.time() - start_time
            
            print(f"   ✓ Tests completed in {duration:.2f}s")
            
            # Check for test results
            workspace = Path('artifacts') / event.correlation_id / event.task_id
            report_path = workspace / 'test_report.json'
            
            if report_path.exists():
                with open(report_path) as f:
                    report = json.load(f)
                
                summary = report.get('summary', {})
                
                print(f"   ✓ Test Report:")
                print(f"      Total Trades: {summary.get('total_trades', 0)}")
                print(f"      Win Rate: {summary.get('win_rate', 0):.2%}")
                print(f"      Net PnL: ${summary.get('net_pnl', 0):.2f}")
                print(f"      Max Drawdown: {summary.get('max_drawdown', 0):.2%}")
                
                # Check for artifacts
                trades_csv = workspace / 'trades.csv'
                equity_csv = workspace / 'equity_curve.csv'
                
                if trades_csv.exists():
                    print(f"   ✓ Trades saved: {trades_csv}")
                if equity_csv.exists():
                    print(f"   ✓ Equity curve saved: {equity_csv}")
                
                return {
                    'status': 'ready',
                    'duration': duration,
                    'metrics': summary,
                    'artifacts': {
                        'report': str(report_path),
                        'trades': str(trades_csv) if trades_csv.exists() else None,
                        'equity': str(equity_csv) if equity_csv.exists() else None
                    }
                }
            else:
                print(f"   ⚠️  No test report generated")
                return {
                    'status': 'completed',
                    'duration': duration,
                    'message': 'Tests completed but no report found'
                }
        
        except Exception as e:
            print(f"   ❌ Execution failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _create_template_todolist(self, user_request: str) -> Dict[str, Any]:
        """Create a template TodoList for fallback."""
        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create a simple contract for the task
        contract = {
            "contract_id": "contract_cli_strategy",
            "description": user_request,
            "interfaces": {
                "run_backtest": {
                    "description": "Execute backtesting strategy",
                    "inputs": ["adapter", "df with OHLCV", "config"],
                    "outputs": ["Backtest results with metrics"]
                }
            }
        }
        
        # Save contract
        contract_path = self.output_dir / "contract_cli_strategy.json"
        contract_path.write_text(json.dumps(contract, indent=2), encoding='utf-8')
        
        return {
            "todo_list_id": workflow_id,
            "workflow_name": f"CLI: {user_request[:50]}",
            "created_at": datetime.now().isoformat() + "Z",
            "created_by": "cli",
            "metadata": {
                "user_request": user_request,
                "mode": "template",
                "planner_version": "template-1.0.0"
            },
            "items": [
                {
                    "id": "task_coder_001",
                    "title": "Implement Strategy Code",
                    "description": user_request,
                    "agent_role": "coder",
                    "priority": 1,
                    "dependencies": [],
                    "expected_duration_seconds": 300,
                    "max_retries": 3,
                    "timeout_seconds": 600,
                    "contract_path": str(contract_path),  # Add contract path
                    "acceptance_criteria": {
                        "tests": [
                            {
                                "cmd": "python -m pytest tests/test_strategy.py",
                                "timeout_seconds": 60
                            }
                        ],
                        "expected_artifacts": ["Backtest/codes/strategy.py"],
                        "validation_rules": [
                            {
                                "type": "lint",
                                "command": "python -m py_compile Backtest/codes/strategy.py",
                                "expected_exit_code": 0
                            }
                        ]
                    },
                    "input_artifacts": [],
                    "output_artifacts": ["Backtest/codes/strategy.py"],
                    "tags": ["strategy", "cli"],
                    "failure_routing": {
                        "implementation_bug": "coder",
                        "spec_mismatch": "architect",
                        "timeout": "tester",
                        "missing_dependency": "coder",
                        "flaky_test": "tester"
                    }
                }
            ]
        }
    
    def get_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get workflow status.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Dictionary with workflow status and task details
        """
        print(f"🔍 Checking status: {workflow_id}")
        print()
        
        # Check if workflow exists in orchestrator
        workflow_state = self.orchestrator.workflows.get(workflow_id)
        
        if not workflow_state:
            print(f"   ❌ Workflow not found in orchestrator: {workflow_id}")
            print()
            
            # Check if TodoList file exists
            todo_files = list(self.output_dir.glob("*_todolist.json"))
            for todo_file in todo_files:
                try:
                    with open(todo_file, 'r', encoding='utf-8') as f:
                        todo_list = json.load(f)
                    if todo_list['todo_list_id'] == workflow_id:
                        print(f"   📄 Found TodoList: {todo_file.name}")
                        print(f"   ⚠️  Not loaded into Orchestrator yet")
                        return {
                            'workflow_id': workflow_id,
                            'status': 'not_loaded',
                            'todolist_exists': True
                        }
                except:
                    pass
            
            return {
                'workflow_id': workflow_id,
                'status': 'not_found'
            }
        
        # Show workflow details
        print(f"📊 Workflow: {workflow_id}")
        print(f"   Status: {workflow_state.status.value}")
        print(f"   Created: {workflow_state.metadata.get('created_at', 'unknown')}")
        print()
        
        # Get todo list for task details
        todo_list = self.orchestrator.todo_lists.get(workflow_state.todo_list_id)
        
        # Show task details
        print("📋 Tasks:")
        for task_id, task_state in workflow_state.tasks.items():
            status_icon = {
                'pending': '⏳',
                'ready': '🔄',
                'running': '🔄',
                'completed': '✅',
                'failed': '❌'
            }.get(task_state.status.value, '❓')
            
            # Find task details from todo list
            task_details = None
            if todo_list:
                for item in todo_list['items']:
                    if item['id'] == task_id:
                        task_details = item
                        break
            
            title = task_details['title'] if task_details else task_id
            agent = task_details['agent_role'] if task_details else 'unknown'
            
            print(f"   {status_icon} {task_id}: {title}")
            print(f"      Agent: {agent}")
            print(f"      Status: {task_state.status.value}")
            if task_state.retry_count > 0:
                print(f"      Retries: {task_state.retry_count}")
            print()
        
        return {
            'workflow_id': workflow_id,
            'status': workflow_state.status.value,
            'tasks': {k: v.status.value for k, v in workflow_state.tasks.items()}
        }
    
    def list_workflows(self) -> None:
        """List all workflows."""
        print("📂 Available Workflows:")
        print()
        
        # List TodoList files
        todo_files = list(self.output_dir.glob("*_todolist.json"))
        
        if not todo_files:
            print("   (No workflows found)")
            print()
            return
        
        for todo_file in sorted(todo_files, reverse=True):
            try:
                with open(todo_file, 'r', encoding='utf-8') as f:
                    todo_list = json.load(f)
                
                workflow_id = todo_list.get('todo_list_id', 'unknown')
                workflow_name = todo_list.get('workflow_name', 'Untitled')
                created = todo_list.get('created_at', 'unknown')
                num_tasks = len(todo_list.get('items', []))
                
                print(f"   📄 {workflow_id}")
                print(f"      Name: {workflow_name}")
                print(f"      Created: {created}")
                print(f"      Tasks: {num_tasks}")
                print()
                
            except Exception as e:
                print(f"   ❌ Error reading {todo_file.name}: {e}")
                print()
    
    def interactive_mode(self):
        """Run interactive CLI session."""
        print("="*70)
        print("   MULTI-AGENT SYSTEM - INTERACTIVE MODE")
        print("="*70)
        print()
        print("Commands:")
        print("  submit <request>  - Submit new strategy request")
        print("  execute <id>      - Execute workflow tasks")
        print("  status <id>       - Check workflow status")
        print("  list              - List all workflows")
        print("  help              - Show this help")
        print("  exit              - Exit CLI")
        print()
        print("="*70)
        print()
        
        while True:
            try:
                cmd = input(">>> ").strip()
                
                if not cmd:
                    continue
                
                parts = cmd.split(maxsplit=1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                
                if command == "exit" or command == "quit":
                    print("👋 Goodbye!")
                    break
                
                elif command == "help":
                    print("Commands:")
                    print("  submit <request>  - Submit new strategy request")
                    print("  execute <id>      - Execute workflow tasks")
                    print("  status <id>       - Check workflow status")
                    print("  list              - List all workflows")
                    print("  help              - Show this help")
                    print("  exit              - Exit CLI")
                    print()
                
                elif command == "submit":
                    if not args:
                        print("❌ Usage: submit <request>")
                        print()
                        continue
                    
                    result = self.submit_request(args)
                    print(f"✅ Submitted: {result['workflow_id']}")
                    print(f"   Status: {result['status']}")
                    print()
                
                elif command == "execute":
                    if not args:
                        print("❌ Usage: execute <workflow_id>")
                        print()
                        continue
                    
                    result = self.execute_workflow(args)
                    if result['status'] == 'completed':
                        print(f"✅ Execution complete")
                        if result.get('results'):
                            for task_id, task_result in result['results'].items():
                                print(f"   {task_id}: {task_result['status']}")
                    else:
                        print(f"❌ Execution failed: {result.get('message', 'Unknown error')}")
                    print()
                
                elif command == "status":
                    if not args:
                        print("❌ Usage: status <workflow_id>")
                        print()
                        continue
                    
                    self.get_status(args)
                
                elif command == "list":
                    self.list_workflows()
                
                else:
                    print(f"❌ Unknown command: {command}")
                    print("   Type 'help' for available commands")
                    print()
            
            except KeyboardInterrupt:
                print()
                print("👋 Goodbye!")
                break
            
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()
                print()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py
      Start interactive mode
  
  python cli.py --request "Create RSI strategy with buy<30, sell>70"
      Submit single request
  
  python cli.py --execute wf_08915b40866d
      Execute workflow tasks with AI agents
  
  python cli.py --status workflow_20251108_120000
      Check workflow status
  
  python cli.py --list
      List all workflows
        """
    )
    
    parser.add_argument(
        '--request', '-r',
        type=str,
        help='Submit a strategy request'
    )
    
    parser.add_argument(
        '--execute', '-e',
        type=str,
        help='Execute workflow tasks'
    )
    
    parser.add_argument(
        '--run',
        action='store_true',
        help='Execute workflow immediately after submit (use with --request)'
    )
    
    parser.add_argument(
        '--status', '-s',
        type=str,
        help='Check workflow status'
    )
    
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List all workflows'
    )
    
    args = parser.parse_args()
    
    # Initialize CLI
    cli = MultiAgentCLI()
    
    # Handle commands
    if args.request:
        result = cli.submit_request(args.request)
        print(f"✅ Workflow: {result['workflow_id']}")
        print(f"   Status: {result['status']}")
        
        # Execute immediately if --run flag is set
        if args.run and result['status'] == 'queued':
            print()
            print("🔄 Auto-executing workflow...")
            print()
            exec_result = cli.execute_workflow(result['workflow_id'])
            if exec_result['status'] == 'completed':
                print(f"✅ Execution complete!")
            else:
                print(f"❌ Execution failed: {exec_result.get('message', 'Unknown error')}")
        elif result['status'] == 'queued':
            print(f"   Use 'python cli.py --status {result['workflow_id']}' to check status")
            print(f"   Use 'python cli.py --execute {result['workflow_id']}' to run agents")
        sys.exit(0)
    
    elif args.execute:
        result = cli.execute_workflow(args.execute)
        if result['status'] == 'completed':
            print(f"✅ Execution complete for: {result['workflow_id']}")
        else:
            print(f"❌ Execution failed: {result.get('message', 'Unknown error')}")
        sys.exit(0)
    
    elif args.status:
        cli.get_status(args.status)
        sys.exit(0)
    
    elif args.list:
        cli.list_workflows()
        sys.exit(0)
    
    else:
        # Interactive mode
        cli.interactive_mode()
        sys.exit(0)


if __name__ == "__main__":
    main()
