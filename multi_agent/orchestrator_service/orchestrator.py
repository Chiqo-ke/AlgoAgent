"""
Minimal Orchestrator Implementation

Executes todo lists by dispatching tasks to agents and tracking state.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from contracts.event_types import Event, EventType, Channels
from contracts.message_bus import get_message_bus
from contracts.validate_contract import SchemaValidator


logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Workflow execution status."""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    READY = "ready"
    DISPATCHED = "dispatched"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class TaskState:
    """State of a task in the workflow."""
    task_id: str
    status: TaskStatus
    retry_count: int = 0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    artifacts: List[str] = field(default_factory=list)
    test_report_id: Optional[str] = None


@dataclass
class WorkflowState:
    """State of a workflow execution."""
    workflow_id: str
    todo_list_id: str
    correlation_id: str
    status: WorkflowStatus
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    tasks: Dict[str, TaskState] = field(default_factory=dict)
    error: Optional[str] = None


class MinimalOrchestrator:
    """
    Minimal orchestrator for executing todo lists.
    
    This is a simple in-memory implementation. In production, this would
    use a database for durable state and a task queue for scalability.
    """
    
    def __init__(self, use_message_bus: bool = False):
        """
        Initialize orchestrator.
        
        Args:
            use_message_bus: Enable message bus integration
        """
        self.workflows: Dict[str, WorkflowState] = {}
        self.todo_lists: Dict[str, Dict[str, Any]] = {}
        self.validator = SchemaValidator()
        self.use_message_bus = use_message_bus
        
        if use_message_bus:
            self.message_bus = get_message_bus(use_redis=False)  # In-memory for now
            self._setup_subscriptions()
        
        logger.info("Initialized MinimalOrchestrator")
    
    def _setup_subscriptions(self):
        """Setup message bus subscriptions."""
        if self.use_message_bus:
            self.message_bus.subscribe(Channels.AGENT_RESULTS, self._handle_agent_result)
            logger.info("Subscribed to agent result channel")
    
    def load_todo_list(self, filepath: Path) -> str:
        """
        Load and validate a todo list.
        
        Args:
            filepath: Path to todo list JSON
            
        Returns:
            todo_list_id
            
        Raises:
            ValueError: If todo list is invalid
        """
        with open(filepath, 'r') as f:
            todo_list = json.load(f)
        
        # Validate
        is_valid, errors = self.validator.validate_todo_list(todo_list)
        if not is_valid:
            raise ValueError(f"Invalid todo list: {errors}")
        
        is_valid, dep_errors = self.validator.validate_dependencies(todo_list)
        if not is_valid:
            raise ValueError(f"Invalid dependencies: {dep_errors}")
        
        todo_list_id = todo_list['todo_list_id']
        self.todo_lists[todo_list_id] = todo_list
        
        logger.info(f"Loaded todo list: {todo_list_id}")
        return todo_list_id
    
    def create_workflow(self, todo_list_id: str) -> str:
        """
        Create a new workflow from a todo list.
        
        Args:
            todo_list_id: ID of loaded todo list
            
        Returns:
            workflow_id
            
        Raises:
            ValueError: If todo list not found
        """
        if todo_list_id not in self.todo_lists:
            raise ValueError(f"Todo list not found: {todo_list_id}")
        
        todo_list = self.todo_lists[todo_list_id]
        
        workflow_id = f"wf_{uuid.uuid4().hex[:12]}"
        correlation_id = f"corr_{uuid.uuid4().hex[:12]}"
        
        # Initialize task states
        tasks = {}
        for item in todo_list['items']:
            tasks[item['id']] = TaskState(
                task_id=item['id'],
                status=TaskStatus.PENDING
            )
        
        # Create workflow state
        workflow = WorkflowState(
            workflow_id=workflow_id,
            todo_list_id=todo_list_id,
            correlation_id=correlation_id,
            status=WorkflowStatus.CREATED,
            created_at=datetime.utcnow().isoformat(),
            tasks=tasks
        )
        
        self.workflows[workflow_id] = workflow
        
        # Publish event
        if self.use_message_bus:
            event = Event.create(
                event_type=EventType.WORKFLOW_CREATED,
                correlation_id=correlation_id,
                workflow_id=workflow_id,
                data={
                    "todo_list_id": todo_list_id,
                    "workflow_name": todo_list.get('workflow_name', 'Unknown'),
                    "total_tasks": len(todo_list['items'])
                },
                source="orchestrator"
            )
            self.message_bus.publish(Channels.WORKFLOW_EVENTS, event)
        
        logger.info(f"Created workflow: {workflow_id}")
        return workflow_id
    
    def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Execute a workflow (synchronous for now).
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Workflow execution summary
            
        Raises:
            ValueError: If workflow not found
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        workflow = self.workflows[workflow_id]
        todo_list = self.todo_lists[workflow.todo_list_id]
        
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.utcnow().isoformat()
        
        logger.info(f"Executing workflow: {workflow_id}")
        
        # Get execution order (topological sort)
        execution_order = self._get_execution_order(todo_list)
        
        # Execute tasks in order
        for task_id in execution_order:
            task_item = next(item for item in todo_list['items'] if item['id'] == task_id)
            task_state = workflow.tasks[task_id]
            
            logger.info(f"Executing task: {task_id} - {task_item['title']}")
            
            # Check if ready (dependencies satisfied)
            if not self._are_dependencies_satisfied(task_item, workflow):
                logger.error(f"Dependencies not satisfied for {task_id}")
                task_state.status = TaskStatus.FAILED
                task_state.error = "Dependencies not satisfied"
                workflow.status = WorkflowStatus.FAILED
                break
            
            # Execute task with retries
            success = self._execute_task(workflow_id, task_id, task_item, task_state)
            
            if not success:
                logger.error(f"Task failed: {task_id}")
                workflow.status = WorkflowStatus.FAILED
                workflow.error = f"Task {task_id} failed"
                break
        
        # Check if all tasks completed
        if all(t.status == TaskStatus.COMPLETED for t in workflow.tasks.values()):
            workflow.status = WorkflowStatus.COMPLETED
            logger.info(f"Workflow completed: {workflow_id}")
        
        workflow.completed_at = datetime.utcnow().isoformat()
        
        # Publish completion event
        if self.use_message_bus:
            event = Event.create(
                event_type=EventType.WORKFLOW_COMPLETED if workflow.status == WorkflowStatus.COMPLETED else EventType.WORKFLOW_FAILED,
                correlation_id=workflow.correlation_id,
                workflow_id=workflow_id,
                data={
                    "status": workflow.status.value,
                    "completed_tasks": sum(1 for t in workflow.tasks.values() if t.status == TaskStatus.COMPLETED),
                    "failed_tasks": sum(1 for t in workflow.tasks.values() if t.status == TaskStatus.FAILED),
                    "duration_seconds": self._calculate_duration(workflow)
                },
                source="orchestrator"
            )
            self.message_bus.publish(Channels.WORKFLOW_EVENTS, event)
        
        return self.get_workflow_status(workflow_id)
    
    def _execute_task(
        self,
        workflow_id: str,
        task_id: str,
        task_item: Dict[str, Any],
        task_state: TaskState
    ) -> bool:
        """
        Execute a single task.
        
        Args:
            workflow_id: Workflow ID
            task_id: Task ID
            task_item: Task definition from todo list
            task_state: Task state
            
        Returns:
            True if successful, False otherwise
        """
        max_retries = task_item.get('max_retries', 3)
        
        for attempt in range(max_retries + 1):
            if attempt > 0:
                task_state.status = TaskStatus.RETRYING
                task_state.retry_count = attempt
                logger.info(f"Retrying task {task_id} (attempt {attempt + 1}/{max_retries + 1})")
            
            task_state.status = TaskStatus.RUNNING
            task_state.started_at = datetime.utcnow().isoformat()
            
            # In a real system, this would dispatch to an agent via message bus
            # For now, we just simulate success/failure
            logger.info(f"[STUB] Dispatching {task_id} to {task_item['agent_role']} agent")
            
            # Simulate task execution
            # In production, this would wait for agent response
            success = True  # Placeholder
            
            if success:
                task_state.status = TaskStatus.COMPLETED
                task_state.completed_at = datetime.utcnow().isoformat()
                task_state.artifacts = task_item.get('output_artifacts', [])
                logger.info(f"Task completed: {task_id}")
                return True
            else:
                task_state.error = "Task execution failed"
                logger.warning(f"Task failed: {task_id} (attempt {attempt + 1})")
        
        # All retries exhausted
        task_state.status = TaskStatus.FAILED
        logger.error(f"Task failed after {max_retries + 1} attempts: {task_id}")
        return False
    
    def _get_execution_order(self, todo_list: Dict[str, Any]) -> List[str]:
        """
        Get task execution order using topological sort.
        
        Args:
            todo_list: Todo list dictionary
            
        Returns:
            List of task IDs in execution order
        """
        items = todo_list['items']
        
        # Build dependency graph
        graph: Dict[str, List[str]] = {}
        in_degree: Dict[str, int] = {}
        
        for item in items:
            task_id = item['id']
            graph[task_id] = []
            in_degree[task_id] = 0
        
        for item in items:
            task_id = item['id']
            for dep in item.get('dependencies', []):
                graph[dep].append(task_id)
                in_degree[task_id] += 1
        
        # Kahn's algorithm for topological sort
        queue = [tid for tid in in_degree if in_degree[tid] == 0]
        result = []
        
        while queue:
            # Sort by priority (lower number = higher priority)
            item_dict = {item['id']: item for item in items}
            queue.sort(key=lambda tid: item_dict[tid].get('priority', 5))
            
            current = queue.pop(0)
            result.append(current)
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result
    
    def _are_dependencies_satisfied(
        self,
        task_item: Dict[str, Any],
        workflow: WorkflowState
    ) -> bool:
        """Check if all dependencies are satisfied."""
        dependencies = task_item.get('dependencies', [])
        
        for dep_id in dependencies:
            if dep_id not in workflow.tasks:
                return False
            
            dep_state = workflow.tasks[dep_id]
            if dep_state.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    def _calculate_duration(self, workflow: WorkflowState) -> float:
        """Calculate workflow duration in seconds."""
        if workflow.started_at and workflow.completed_at:
            start = datetime.fromisoformat(workflow.started_at)
            end = datetime.fromisoformat(workflow.completed_at)
            return (end - start).total_seconds()
        return 0.0
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get workflow status summary.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Status dictionary
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        workflow = self.workflows[workflow_id]
        
        task_summary = {}
        for task_id, task_state in workflow.tasks.items():
            task_summary[task_id] = {
                "status": task_state.status.value,
                "retry_count": task_state.retry_count,
                "artifacts": task_state.artifacts,
                "error": task_state.error
            }
        
        return {
            "workflow_id": workflow.workflow_id,
            "todo_list_id": workflow.todo_list_id,
            "status": workflow.status.value,
            "created_at": workflow.created_at,
            "started_at": workflow.started_at,
            "completed_at": workflow.completed_at,
            "duration_seconds": self._calculate_duration(workflow),
            "tasks": task_summary,
            "error": workflow.error
        }
    
    def _handle_agent_result(self, event: Event):
        """Handle agent result events from message bus."""
        logger.info(f"Received agent result: {event.event_id}")
        # TODO: Update task state based on agent result


def main():
    """CLI for orchestrator."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Execute todo lists')
    parser.add_argument('todo_list', type=Path, help='Path to todo list JSON')
    parser.add_argument('--message-bus', action='store_true', help='Enable message bus')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Create orchestrator
        orchestrator = MinimalOrchestrator(use_message_bus=args.message_bus)
        
        # Load todo list
        todo_list_id = orchestrator.load_todo_list(args.todo_list)
        print(f"✅ Loaded todo list: {todo_list_id}")
        
        # Create workflow
        workflow_id = orchestrator.create_workflow(todo_list_id)
        print(f"✅ Created workflow: {workflow_id}")
        
        # Execute workflow
        print(f"\n🚀 Executing workflow...")
        result = orchestrator.execute_workflow(workflow_id)
        
        # Print results
        print(f"\n{'='*60}")
        print(f"Workflow Status: {result['status']}")
        print(f"Duration: {result['duration_seconds']:.2f}s")
        print(f"\nTasks:")
        
        for task_id, task_info in result['tasks'].items():
            status_icon = "✅" if task_info['status'] == 'completed' else "❌"
            print(f"  {status_icon} {task_id}: {task_info['status']}")
            if task_info['error']:
                print(f"     Error: {task_info['error']}")
        
        print(f"{'='*60}\n")
        
        return 0 if result['status'] == 'completed' else 1
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error("Orchestrator failed", exc_info=True)
        return 1


if __name__ == '__main__':
    exit(main())
