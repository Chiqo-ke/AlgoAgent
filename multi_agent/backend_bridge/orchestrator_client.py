"""
Orchestrator Client

Provides a client interface for submitting workflows and monitoring status
from the Django backend or CLI applications.

This acts as the API layer between external clients and the orchestrator service.
"""

import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator_service.orchestrator import MinimalOrchestrator, WorkflowStatus, TaskStatus
from planner_service.planner import PlannerService
from contracts.event_types import Event, EventType
from contracts.message_bus import get_message_bus, Channels


logger = logging.getLogger(__name__)


class OrchestratorClient:
    """
    Client for interacting with the Orchestrator service.
    
    Provides high-level API for:
    - Submitting workflow requests (natural language → TodoList → execution)
    - Checking workflow status
    - Pausing/resuming/cancelling workflows
    - Retrieving workflow results and artifacts
    """
    
    def __init__(self, orchestrator: Optional[MinimalOrchestrator] = None):
        """
        Initialize the orchestrator client.
        
        Args:
            orchestrator: Orchestrator instance (created if not provided)
        """
        self.orchestrator = orchestrator or MinimalOrchestrator()
        self.planner = PlannerService()
        self.message_bus = get_message_bus()
        
    def submit_workflow(
        self,
        request: str,
        auto_execute: bool = True,
        auto_fix_mode: bool = True,
        max_branch_depth: int = 2,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submit a new workflow request.
        
        Args:
            request: Natural language strategy description
            auto_execute: Start execution immediately
            auto_fix_mode: Enable automatic failure recovery
            max_branch_depth: Maximum retry depth for auto-fix
            context: Additional context for strategy generation
            user_id: User identifier for multi-user support
            
        Returns:
            Dictionary with workflow_id, status, and todo_list
        """
        try:
            logger.info(f"Submitting workflow request: {request[:100]}...")
            
            # Generate TodoList from natural language request
            todo_list = self.planner.create_plan(
                user_request=request,
                repo_context=context or {},
                workflow_name=context.get("workflow_name") if context else None
            )
            
            if not todo_list:
                raise ValueError("Failed to generate TodoList from request")
                
            # Create workflow in orchestrator
            workflow_id = self.orchestrator.create_workflow(
                todo_list=todo_list,
                auto_fix_mode=auto_fix_mode,
                max_branch_depth=max_branch_depth
            )
            
            # Publish WORKFLOW_CREATED event
            correlation_id = f"corr_{workflow_id}"
            event = Event.create(
                event_type=EventType.WORKFLOW_CREATED,
                correlation_id=correlation_id,
                workflow_id=workflow_id,
                data={
                    "request": request,
                    "auto_execute": auto_execute,
                    "auto_fix_mode": auto_fix_mode,
                    "max_branch_depth": max_branch_depth,
                    "task_count": len(todo_list.get('tasks', []))
                },
                source="orchestrator_client",
                metadata={"user_id": user_id} if user_id else None
            )
            self.message_bus.publish(Channels.WORKFLOW_LIFECYCLE, event)
            
            # Auto-execute if requested
            if auto_execute:
                self.orchestrator.execute_workflow(workflow_id, correlation_id)
                
            logger.info(f"Workflow created: {workflow_id}, auto_execute={auto_execute}")
            
            return {
                "workflow_id": workflow_id,
                "status": "running" if auto_execute else "created",
                "created_at": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "todo_list": todo_list,
                "metadata": {
                    "planner_model": self.planner.get_model_info(),
                    "correlation_id": correlation_id
                }
            }
            
        except Exception as e:
            logger.error(f"Error submitting workflow: {e}", exc_info=True)
            raise
            
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get current status of a workflow.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Dictionary with detailed workflow status
        """
        try:
            workflow_state = self.orchestrator.get_workflow_state(workflow_id)
            
            if not workflow_state:
                raise ValueError(f"Workflow {workflow_id} not found")
                
            # Calculate progress
            total_tasks = len(workflow_state.tasks)
            completed_tasks = sum(
                1 for task in workflow_state.tasks.values()
                if task.status == TaskStatus.COMPLETED
            )
            progress = completed_tasks / total_tasks if total_tasks > 0 else 0.0
            
            # Serialize task states
            tasks = []
            for task_id, task_state in workflow_state.tasks.items():
                tasks.append({
                    "task_id": task_id,
                    "status": task_state.status.value,
                    "retry_count": task_state.retry_count,
                    "started_at": task_state.started_at,
                    "completed_at": task_state.completed_at,
                    "error": task_state.error,
                    "result": task_state.result
                })
                
            return {
                "workflow_id": workflow_id,
                "status": workflow_state.status.value,
                "progress": progress,
                "created_at": workflow_state.created_at,
                "tasks": tasks,
                "branch_todos": workflow_state.branch_todos,
                "auto_fix_mode": workflow_state.auto_fix_mode,
                "max_branch_depth": workflow_state.max_branch_depth
            }
            
        except Exception as e:
            logger.error(f"Error getting workflow status: {e}", exc_info=True)
            raise
            
    def pause_workflow(self, workflow_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Pause a running workflow.
        
        Args:
            workflow_id: Workflow identifier
            user_id: User requesting the pause
            
        Returns:
            Dictionary with updated status
        """
        try:
            logger.info(f"Pausing workflow {workflow_id}")
            
            workflow_state = self.orchestrator.get_workflow_state(workflow_id)
            if not workflow_state:
                raise ValueError(f"Workflow {workflow_id} not found")
                
            if workflow_state.status != WorkflowStatus.RUNNING:
                raise ValueError(
                    f"Cannot pause workflow in status {workflow_state.status.value}"
                )
                
            # Update status
            workflow_state.status = WorkflowStatus.PAUSED
            
            # Publish WORKFLOW_PAUSED event
            event = Event.create(
                event_type=EventType.WORKFLOW_PAUSED,
                correlation_id=f"corr_{workflow_id}",
                workflow_id=workflow_id,
                data={
                    "paused_by": user_id or "system",
                    "reason": "Manual pause request"
                },
                source="orchestrator_client"
            )
            self.message_bus.publish(Channels.WORKFLOW_LIFECYCLE, event)
            
            return {
                "workflow_id": workflow_id,
                "status": "paused",
                "message": "Workflow paused successfully",
                "paused_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error pausing workflow: {e}", exc_info=True)
            raise
            
    def resume_workflow(self, workflow_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Resume a paused workflow.
        
        Args:
            workflow_id: Workflow identifier
            user_id: User requesting the resume
            
        Returns:
            Dictionary with updated status
        """
        try:
            logger.info(f"Resuming workflow {workflow_id}")
            
            workflow_state = self.orchestrator.get_workflow_state(workflow_id)
            if not workflow_state:
                raise ValueError(f"Workflow {workflow_id} not found")
                
            if workflow_state.status != WorkflowStatus.PAUSED:
                raise ValueError(
                    f"Cannot resume workflow in status {workflow_state.status.value}"
                )
                
            # Update status and resume execution
            workflow_state.status = WorkflowStatus.RUNNING
            
            # Publish WORKFLOW_RESUMED event
            event = Event.create(
                event_type=EventType.WORKFLOW_RESUMED,
                correlation_id=f"corr_{workflow_id}",
                workflow_id=workflow_id,
                data={
                    "resumed_by": user_id or "system"
                },
                source="orchestrator_client"
            )
            self.message_bus.publish(Channels.WORKFLOW_LIFECYCLE, event)
            
            # Continue execution
            self.orchestrator.execute_workflow(workflow_id, f"corr_{workflow_id}")
            
            return {
                "workflow_id": workflow_id,
                "status": "running",
                "message": "Workflow resumed successfully",
                "resumed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error resuming workflow: {e}", exc_info=True)
            raise
            
    def cancel_workflow(self, workflow_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Cancel a workflow permanently.
        
        Args:
            workflow_id: Workflow identifier
            user_id: User requesting the cancellation
            
        Returns:
            Dictionary with cancellation confirmation
        """
        try:
            logger.info(f"Cancelling workflow {workflow_id}")
            
            workflow_state = self.orchestrator.get_workflow_state(workflow_id)
            if not workflow_state:
                raise ValueError(f"Workflow {workflow_id} not found")
                
            # Update status
            workflow_state.status = WorkflowStatus.CANCELLED
            
            # Identify incomplete tasks
            incomplete_tasks = [
                task_id for task_id, task_state in workflow_state.tasks.items()
                if task_state.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]
            ]
            
            # Publish WORKFLOW_CANCELLED event
            event = Event.create(
                event_type=EventType.WORKFLOW_CANCELLED,
                correlation_id=f"corr_{workflow_id}",
                workflow_id=workflow_id,
                data={
                    "cancelled_by": user_id or "system",
                    "incomplete_tasks": incomplete_tasks
                },
                source="orchestrator_client"
            )
            self.message_bus.publish(Channels.WORKFLOW_LIFECYCLE, event)
            
            return {
                "workflow_id": workflow_id,
                "status": "cancelled",
                "message": "Workflow cancelled successfully",
                "cancelled_at": datetime.utcnow().isoformat(),
                "incomplete_tasks": incomplete_tasks
            }
            
        except Exception as e:
            logger.error(f"Error cancelling workflow: {e}", exc_info=True)
            raise
            
    def list_workflows(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        List workflows (with optional filtering).
        
        Args:
            user_id: Filter by user (requires user tracking in workflow state)
            status: Filter by status (created, running, completed, failed)
            limit: Maximum number of results
            
        Returns:
            List of workflow summaries
        """
        try:
            all_workflows = self.orchestrator.get_all_workflows()
            
            # Filter by status if specified
            if status:
                status_enum = WorkflowStatus(status)
                all_workflows = [
                    wf for wf in all_workflows
                    if wf.status == status_enum
                ]
                
            # Apply limit
            workflows = all_workflows[:limit]
            
            # Create summaries
            summaries = []
            for workflow_state in workflows:
                total_tasks = len(workflow_state.tasks)
                completed_tasks = sum(
                    1 for task in workflow_state.tasks.values()
                    if task.status == TaskStatus.COMPLETED
                )
                
                summaries.append({
                    "workflow_id": workflow_state.workflow_id,
                    "status": workflow_state.status.value,
                    "progress": completed_tasks / total_tasks if total_tasks > 0 else 0.0,
                    "created_at": workflow_state.created_at,
                    "task_count": total_tasks,
                    "completed_tasks": completed_tasks
                })
                
            return summaries
            
        except Exception as e:
            logger.error(f"Error listing workflows: {e}", exc_info=True)
            raise


# Singleton instance
_client_instance: Optional[OrchestratorClient] = None


def get_orchestrator_client() -> OrchestratorClient:
    """Get or create the global OrchestratorClient instance."""
    global _client_instance
    if _client_instance is None:
        _client_instance = OrchestratorClient()
    return _client_instance
