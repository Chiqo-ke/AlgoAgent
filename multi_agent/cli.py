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
        """
        Initialize the CLI instance, configure core services, and prepare workspace/output directories.
        
        Sets up these instance attributes:
        - workspace_root: repository root Path for the project.
        - output_dir: Path for saved workflows (created if missing).
        - message_bus: in-memory message bus instance.
        - planner: PlannerService instance when a Google API key is present, otherwise None.
        - ai_mode: True when planner is enabled, False when running in template mode.
        - api_key: the Google API key string when available, otherwise None.
        - orchestrator: MinimalOrchestrator instance.
        - coder_agent, architect_agent: placeholders for lazily initialized agent instances.
        
        Also prints brief status lines indicating workspace/output paths and whether AI or template mode is active.
        """
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
        Submit a new strategy request, generate and persist a TodoList, and load it into the orchestrator to create a workflow.
        
        Parameters:
            user_request (str): Natural-language description of the requested strategy or task.
        
        Returns:
            dict: Workflow summary containing:
                - workflow_id (str): Identifier of the created workflow (or the TodoList id on failure).
                - status (str): 'queued' when loaded successfully, 'failed' on error.
                - tasks (int): Number of tasks queued (present on success).
                - todolist_path (str): Filesystem path to the saved TodoList JSON.
                - error (str, optional): Error message when status is 'failed'.
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
        Process and (optionally) execute all pending tasks for a workflow.
        
        Retrieves the workflow state and its associated todo list, iterates task entries, skips tasks that are not in 'pending' or 'ready' status, and for tasks with agent_role 'architect' or 'coder' will invoke the corresponding executor when auto_execute is True. Missing workflows or todo lists produce an error result entry; task-level execution results are collected per task id.
        
        Parameters:
            workflow_id (str): Identifier of the workflow to execute.
            auto_execute (bool): If True, automatically run architect and coder tasks; otherwise tasks remain pending.
        
        Returns:
            dict: {
                'workflow_id': str,
                'status': 'completed' | 'error',
                'results': Dict[str, Any]  # mapping of task_id to execution result dict
            }
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
        Execute a coder task using the configured CoderAgent and return execution details.
        
        Attempts to initialize a CoderAgent (lazy), ensure a contract exists for the task, invoke the agent to implement the task, and collect resulting artifacts and status.
        
        Parameters:
            task (Dict[str, Any]): TodoList task entry. Expected keys include `id`, `title`, `description`, and optionally `contract_path`; the task dictionary may contain other task-specific fields required by the CoderAgent.
        
        Returns:
            Dict[str, Any]: Execution summary with keys:
                - `status` (str): One of `'skipped'` (no API key), `'ready'` (successful), `'failed'` (agent-reported failure), or `'error'` (exception during execution).
                - `duration` (float, optional): Time taken in seconds for agent execution (present when execution was attempted).
                - `artifacts` (List[str], optional): List of artifact file paths produced by the agent (present when available).
                - `error` (str|null, optional): Agent error message if present.
                - `message` (str, optional): Human-readable message for skipped or error outcomes.
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
        Execute an architect-role task to produce and persist a contract specification.
        
        Parameters:
            task (Dict[str, Any]): Task entry from a TodoList containing keys such as
                'id', 'title', 'description', and other requirement details used to
                drive contract design.
        
        Returns:
            Dict[str, Any]: On success, a dictionary with:
                - 'status' (str): 'ready'
                - 'duration' (float): execution time in seconds
                - 'contract' (dict): serialized contract fields including
                  'contract_id', 'name', 'description', 'interfaces', 'data_models',
                  'examples', 'test_skeleton', 'fixtures', and 'created_at'
                - 'fixtures' (List[str]): names of any generated fixtures
                - 'contract_path' (str): filesystem path to the saved contract JSON
              On failure, a dictionary with:
                - 'status' (str): 'error'
                - 'message' (str): error message describing the failure
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
                """
                Request the architect agent to produce a contract specification for the current task.
                
                Returns:
                    contract_data (dict): The contract/design produced by the architect agent, containing contract metadata, interfaces, examples, and any auxiliary fixtures or artifacts.
                """
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
    
    def _create_template_todolist(self, user_request: str) -> Dict[str, Any]:
        """
        Create a fallback TodoList and a minimal contract derived from a free-form user request.
        
        Generates a timestamped workflow id, writes a simple contract JSON to the CLI output directory, and returns a TodoList structure containing metadata and a single coder task prepared for execution. The returned task includes a `contract_path`, acceptance criteria, artifact expectations, timeouts, retry policy, and failure routing.
        
        Parameters:
            user_request (str): Natural-language description of the desired strategy or task.
        
        Returns:
            dict: A TodoList dictionary with the following top-level keys:
                - todo_list_id: Generated workflow identifier.
                - workflow_name: Short display name derived from the request.
                - created_at: ISO8601 timestamp of creation.
                - created_by: Source identifier ("cli").
                - metadata: Additional metadata including the original user_request and mode.
                - items: List of task dictionaries (in this template a single coder task) containing fields such as
                    `id`, `title`, `description`, `agent_role`, `priority`, `dependencies`,
                    `expected_duration_seconds`, `max_retries`, `timeout_seconds`, `contract_path`,
                    `acceptance_criteria`, `input_artifacts`, `output_artifacts`, `tags`, and `failure_routing`.
        """
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
        Show and return a status snapshot for the given workflow.
        
        If the workflow is not present in the orchestrator this will search saved TodoList files and return
        'not_loaded' when a matching TodoList exists or 'not_found' otherwise.
        
        Parameters:
            workflow_id (str): Identifier of the workflow to inspect.
        
        Returns:
            dict: A snapshot containing:
                - 'workflow_id' (str): The provided workflow identifier.
                - 'status' (str): One of 'not_found', 'not_loaded', or the workflow's current status string.
                - 'todolist_exists' (bool, optional): Present when status is 'not_loaded' to indicate a local TodoList was found.
                - 'tasks' (dict, optional): Mapping of task_id to task status strings when the workflow is loaded.
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
        """
        Print a concise summary of workflows stored in the CLI output directory.
        
        Searches for files matching "*_todolist.json" in the configured output directory and prints each workflow's id, name, creation timestamp, and number of tasks. If no workflows are present or a todo list file cannot be read, prints an informational or error message.
        """
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
    """
    Parse command-line arguments and dispatch CLI commands for the Multi-Agent System.
    
    Supports submitting a strategy request (--request), executing a workflow (--execute), auto-running after submit (--run), checking workflow status (--status), listing saved workflows (--list), or entering interactive mode when no arguments are provided.
    """
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