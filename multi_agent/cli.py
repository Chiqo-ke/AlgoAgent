# -*- coding: utf-8 -*-
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

# Fix Windows console encoding issues
if sys.platform == 'win32':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
    except:
        pass  # If reconfiguration fails, continue anyway

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
    print(f"[OK] Loaded GEMINI_API_KEY from .env")

print("[DEBUG] About to import StrategyRegistry...")
# Import strategy registry for testing
from agents.coder_agent.strategy_registry import StrategyRegistry
print("[DEBUG] StrategyRegistry imported successfully")


class MultiAgentCLI:
    """Command-line interface for multi-agent system."""
    
    def __init__(self):
        # Lazy imports to speed up CLI startup
        from planner_service.planner import PlannerService
        from orchestrator_service.orchestrator import MinimalOrchestrator
        from contracts.message_bus import InMemoryMessageBus
        
        print("[DEBUG] Initializing CLI...")
        
        self.workspace_root = Path(__file__).parent.parent
        self.output_dir = self.workspace_root / "multi_agent" / "workflows"
        self.output_dir.mkdir(exist_ok=True)
        
        print("[DEBUG] Creating message bus...")
        # Initialize components
        self.message_bus = InMemoryMessageBus()
        
        print("[DEBUG] Checking for API key...")
        # Initialize Planner with API key if available
        api_key = os.getenv('GOOGLE_API_KEY')
        if api_key:
            print("[DEBUG] Initializing Planner with API key...")
            self.planner = PlannerService(api_key=api_key)
            self.ai_mode = True
            self.api_key = api_key
            print("[AI] AI Mode: ENABLED (using Gemini API)")
        else:
            # No Planner without API key, will use template mode
            self.planner = None
            self.ai_mode = False
            self.api_key = None
            print("[TEMPLATE] Template Mode: ENABLED (no AI API key)")
        
        print("[DEBUG] Initializing Orchestrator...")
        # Initialize Orchestrator
        self.orchestrator = MinimalOrchestrator(use_message_bus=False)
        
        # Agent instances (lazy loaded)
        self.coder_agent = None
        self.architect_agent = None
        
        print(f"[Workspace] {self.workspace_root}")
        print(f"[Workflows] {self.output_dir}")
        print("[DEBUG] Initialization complete!")
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
            
            # Inject workflow_id into task metadata for agent identification
            if 'metadata' not in task_details:
                task_details['metadata'] = {}
            task_details['metadata']['workflow_id'] = workflow_id
            
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
                # Update task status after execution
                if result.get('status') in ['ready', 'completed']:
                    from orchestrator_service.orchestrator import TaskStatus
                    task_state.status = TaskStatus.COMPLETED
            elif agent_role == 'coder' and auto_execute:
                result = self._execute_coder_task(task_details)
                results[task_id] = result
                # Update task status after execution
                if result.get('status') in ['ready', 'completed']:
                    from orchestrator_service.orchestrator import TaskStatus
                    task_state.status = TaskStatus.COMPLETED
            elif agent_role == 'tester' and auto_execute:
                result = self._execute_tester_task(task_details)
                results[task_id] = result
                # Update task status after execution
                if result.get('status') in ['ready', 'completed']:
                    from orchestrator_service.orchestrator import TaskStatus
                    task_state.status = TaskStatus.COMPLETED
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
            from contracts import TaskEvent, EventType
            
            event = TaskEvent.create(
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
    
    def test_workflow(self, workflow_id: str, iteration_start_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Test generated artifacts from a workflow using unique naming convention.
        
        Args:
            workflow_id: Workflow identifier
            iteration_start_time: If provided, only test strategies created after this time
            
        Returns:
            Dictionary with test results
        """
        print(f"\n🧪 Testing workflow: {workflow_id}")
        print()
        
        # Initialize registry
        artifacts_dir = self.workspace_root / "multi_agent" / "Backtest" / "codes"
        test_dir = self.workspace_root / "multi_agent" / "tests"
        
        if not artifacts_dir.exists():
            print(f"   ❌ Artifacts directory not found: {artifacts_dir}")
            return {'status': 'error', 'message': 'Artifacts directory not found'}
        
        registry = StrategyRegistry(artifacts_dir)
        
        # Get all strategies for this workflow
        workflow_strategies = registry.get_by_workflow(workflow_id)
        
        # Filter by iteration start time (prioritized) or workflow creation time
        if iteration_start_time:
            # CRITICAL: Only test NEW files from current iteration
            strategy_files = [
                s for s in workflow_strategies 
                if s.timestamp >= iteration_start_time
            ]
            print(f"📂 Testing {len(strategy_files)} NEW strategies from current iteration")
            print(f"   (Total {len(workflow_strategies)} strategies exist for this workflow)")
        else:
            # Fallback: Use workflow creation time
            workflow_time = None
            todolist_file = self.output_dir / f"{workflow_id}_todolist.json"
            if todolist_file.exists():
                workflow_time = todolist_file.stat().st_mtime
                print(f"📅 Workflow created: {datetime.fromtimestamp(workflow_time).strftime('%Y-%m-%d %H:%M:%S')}")
            
            if workflow_time:
                strategy_files = [
                    s for s in workflow_strategies 
                    if s.timestamp.timestamp() >= workflow_time
                ]
                print(f"📂 Found {len(strategy_files)} strategies for workflow (filtered by time)")
            else:
                strategy_files = workflow_strategies
                print(f"📂 Found {len(strategy_files)} strategies for workflow")
        
        if not strategy_files:
            print(f"   ⚠️  No strategies found for workflow: {workflow_id}")
            print(f"   Tip: Strategies should use naming format:")
            print(f"        {{timestamp}}_{{workflow_id}}_{{task_id}}_{{description}}.py")
            return {'status': 'skipped', 'message': 'No strategy files to test'}
        
        print(f"📁 Strategies to test:")
        for metadata in strategy_files:
            print(f"   - {metadata.filename}")
            print(f"     Task: {metadata.task_id}")
            print(f"     Created: {metadata.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Run tests for each strategy
        results = []
        passed = 0
        failed = 0
        
        for metadata in strategy_files:
            strategy_file = metadata.filepath
            strategy_name = metadata.filename.replace('.py', '')
            test_file = test_dir / f"test_{strategy_name}.py"
            
            print(f"🧪 Testing: {strategy_name}")
            print(f"   Strategy: {strategy_file.name}")
            print(f"   Test: {test_file.name if test_file.exists() else 'NOT FOUND'}")
            
            if not test_file.exists():
                print(f"   ⚠️  Test file not found, skipping...")
                print()
                results.append({
                    'strategy': strategy_name,
                    'status': 'skipped',
                    'message': 'Test file not found'
                })
                continue
            
            # Create test task for Tester Agent
            task = {
                "id": f"test_{strategy_name}",
                "title": f"Test {strategy_name}",
                "description": f"Validate {strategy_file.name} implementation",
                "agent_role": "tester",
                "dependencies": [],
                "metadata": {
                    "strategy_file": str(strategy_file),
                    "test_file": str(test_file),
                    "workflow_id": workflow_id
                },
                "acceptance_criteria": {
                    "tests": [
                        {
                            "cmd": f"python -m pytest {test_file} -v",
                            "timeout_seconds": 60
                        }
                    ]
                }
            }
            
            try:
                print(f"   ⏳ Running tests...")
                start_time = time.time()
                
                # Run pytest with JSON report for detailed error extraction
                import subprocess
                import sys
                json_report = test_dir / f".pytest_{strategy_name}.json"
                
                # Use the same Python executable that's running this script
                result = subprocess.run(
                    [
                        sys.executable, "-m", "pytest",
                        str(test_file),
                        "-v",
                        "--tb=short",
                        "--json-report",
                        f"--json-report-file={json_report}",
                        "--json-report-indent=2"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=str(self.workspace_root / "multi_agent")
                )
                
                duration = time.time() - start_time
                
                # Parse JSON report for detailed errors
                test_errors = []
                if json_report.exists():
                    try:
                        with open(json_report, 'r') as f:
                            report = json.load(f)
                        
                        # Extract failed test details
                        for test in report.get("tests", []):
                            if test.get("outcome") in ["failed", "error"]:
                                call_info = test.get("call", {})
                                longrepr = call_info.get("longrepr", "")
                                
                                # Extract error type and message
                                error_lines = longrepr.split('\n') if longrepr else []
                                error_msg = error_lines[-1] if error_lines else "Unknown error"
                                
                                test_errors.append({
                                    "test_name": test.get("nodeid", ""),
                                    "message": error_msg,
                                    "full_traceback": longrepr
                                })
                    except Exception as e:
                        print(f"      ⚠️  Could not parse JSON report: {e}")
                
                if result.returncode == 0:
                    print(f"   ✅ PASSED ({duration:.2f}s)")
                    passed += 1
                    
                    # Try to extract metrics from output
                    if "passed" in result.stdout:
                        import re
                        match = re.search(r'(\d+) passed', result.stdout)
                        if match:
                            print(f"      Tests: {match.group(1)} passed")
                else:
                    print(f"   ❌ FAILED ({duration:.2f}s)")
                    failed += 1
                    
                    # Show first error message
                    if test_errors:
                        print(f"      Error: {test_errors[0]['message'][:100]}")
                    elif result.stdout:
                        lines = result.stdout.split('\n')[:3]
                        for line in lines:
                            if line.strip() and not line.startswith('='):
                                print(f"      {line[:100]}")
                
                # Capture full output but limit to reasonable size for analysis
                full_output = result.stdout if result.stdout else ''
                full_error = result.stderr if result.stderr else ''
                
                # For error analysis, capture more context (up to 5000 chars)
                error_context = test_errors[0]['message'] if test_errors else full_output
                if len(error_context) > 5000:
                    error_context = error_context[:5000] + "\n... (output truncated for brevity)"
                
                results.append({
                    'strategy': strategy_name,
                    'status': 'ready' if result.returncode == 0 else 'error',
                    'duration': duration,
                    'exit_code': result.returncode,
                    'output': full_output[:2000] if full_output else None,  # Preview for display
                    'full_output': full_output,  # Complete output for analysis
                    'stderr': full_error,
                    'errors': test_errors,
                    'error': error_context  # Full context for debugger
                })
                
            except subprocess.TimeoutExpired:
                print(f"   ❌ TIMEOUT (>30s)")
                failed += 1
                results.append({
                    'strategy': strategy_name,
                    'status': 'timeout',
                    'error': 'Test execution timed out after 30 seconds'
                })
            except Exception as e:
                print(f"   ❌ EXCEPTION: {e}")
                failed += 1
                results.append({
                    'strategy': strategy_name,
                    'status': 'error',
                    'error': str(e)
                })
            
            print()
        
        # Summary
        total = len(results)
        print("="*70)
        print(f"📊 TEST SUMMARY")
        print("="*70)
        print(f"   Total: {total}")
        print(f"   Passed: {passed} ✅")
        print(f"   Failed: {failed} ❌")
        print(f"   Success Rate: {passed/total*100:.0f}%" if total > 0 else "   No tests run")
        print()
        
        # Save detailed report
        report_file = self.output_dir / f"test_report_{workflow_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_data = {
            "workflow_id": workflow_id,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "success_rate": passed/total if total > 0 else 0
            },
            "results": results
        }
        report_file.write_text(json.dumps(report_data, indent=2))
        print(f"💾 Detailed report saved: {report_file.name}")
        print()
        
        return report_data
    
    def interactive_mode(self):
        """Run interactive CLI session."""
        print("="*70)
        print("   MULTI-AGENT SYSTEM - INTERACTIVE MODE")
        print("="*70)
        print()
        print("Commands:")
        print("  submit <request>  - Submit new strategy request")
        print("  execute <id>      - Execute workflow tasks")
        print("  test <id>         - Test generated strategy artifacts")
        print("  iterate <id>      - Run iterative loop until tests pass")
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
                    print("  test <id>         - Test generated strategy artifacts")
                    print("  iterate <id>      - Run iterative loop until tests pass")
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
                
                elif command == "test":
                    if not args:
                        print("❌ Usage: test <workflow_id>")
                        print()
                        continue
                    
                    result = self.test_workflow(args)
                    if result.get('status') != 'error':
                        summary = result.get('summary', {})
                        print(f"✅ Testing complete: {summary.get('passed', 0)}/{summary.get('total', 0)} passed")
                    else:
                        print(f"❌ Testing failed: {result.get('message', 'Unknown error')}")
                    print()
                
                elif command == "iterate":
                    if not args:
                        print("❌ Usage: iterate <workflow_id> [max_iterations]")
                        print()
                        continue
                    
                    # Parse args
                    parts = args.split()
                    workflow_id = parts[0]
                    max_iterations = int(parts[1]) if len(parts) > 1 else 5
                    
                    if workflow_id in self.orchestrator.workflows:
                        from iterative_loop import IterativeLoop
                        
                        # Initialize the loop
                        loop = IterativeLoop(cli=self, max_iterations=max_iterations, auto_fix=True)
                        
                        # Run the iterative loop (use run_until_success method)
                        result = loop.run_until_success(workflow_id, verbose=True)
                        
                        # After the loop, check if a new TodoList was generated
                        # and update the orchestrator's state.
                        if result and result.get("updated_todo_list"):
                            new_todo_list = result["updated_todo_list"]
                            
                            # Get workflow to access todo_list_id
                            workflow = self.orchestrator.workflows[workflow_id]
                            
                            # Update the orchestrator's internal todolist
                            self.orchestrator.todo_lists[workflow.todo_list_id] = new_todo_list
                            
                            # Reload the workflow tasks to reflect the new "fix" tasks
                            self.orchestrator.reload_workflow_tasks(workflow_id)
                            
                            print(f"✓ Orchestrator updated with new fix tasks.")
                            
                        if result.get('success'):
                            print(f"✅ Strategy perfected in {result.get('total_iterations')} iterations!")
                        else:
                            print(f"⚠️  Max iterations ({max_iterations}) reached without full success")
                        print()
                    else:
                        print(f"❌ Workflow not found: {workflow_id}")
                        print()
                
                elif command == "status":
                    if not args:
                        print("❌ Usage: status <workflow_id>")
                        print()
                        continue
                    
                    result = self.get_status(args)
                    if result.get('workflow_id'):
                        print(f"Status for {result['workflow_id']}:")
                        print(f"  Status: {result['status']}")
                        print(f"  Tasks: {result.get('completed_tasks', 0)}/{result.get('total_tasks', 0)}")
                        print()
                    else:
                        print(f"❌ Workflow not found: {args}")
                        print()
                
                elif command == "list":
                    result = self.list_workflows()
                    if result.get('workflows'):
                        print(f"Workflows ({len(result['workflows'])}):")
                        for wf in result['workflows']:
                            print(f"  - {wf['id']}: {wf['status']}")
                        print()
                    else:
                        print("No workflows found.")
                        print()
                
                else:
                    print(f"❌ Unknown command: {command}")
                    print("   Type 'help' for available commands")
                    print()
            
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                print()


def main():
    cli = MultiAgentCLI()
    cli.interactive_mode()

if __name__ == '__main__':
    main()
