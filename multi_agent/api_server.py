"""
FastAPI Backend Server for Multi-Agent Workflow API

Implements REST API endpoints for workflow management.
Use for testing and debugging with Postman or other HTTP clients.

Run with: uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
"""

import logging
import sys
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from backend_bridge import OrchestratorClient, MessageBusListener, EventForwarder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Multi-Agent Workflow API",
    description="REST API for managing AI-driven trading strategy workflows",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For testing - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize backend bridge components
orchestrator_client = OrchestratorClient()
message_bus_listener = MessageBusListener()


# Pydantic models for request/response validation
class WorkflowCreateRequest(BaseModel):
    request: str = Field(..., description="Natural language strategy description")
    auto_execute: bool = Field(True, description="Auto-start workflow execution")
    auto_fix_mode: bool = Field(True, description="Enable automatic failure recovery")
    max_branch_depth: int = Field(2, ge=1, le=5, description="Maximum retry depth")
    context: Optional[dict] = Field(None, description="Additional context for generation")
    user_id: Optional[str] = Field(None, description="User identifier")


class WorkflowResponse(BaseModel):
    workflow_id: str
    status: str
    created_at: str
    user_id: Optional[str] = None
    todo_list: dict
    metadata: dict


class WorkflowStatusResponse(BaseModel):
    workflow_id: str
    status: str
    progress: float
    created_at: str
    tasks: List[dict]
    branch_todos: List[dict]
    auto_fix_mode: bool
    max_branch_depth: int


class WorkflowListItem(BaseModel):
    workflow_id: str
    status: str
    progress: float
    created_at: str
    task_count: int
    completed_tasks: int


class WorkflowControlResponse(BaseModel):
    workflow_id: str
    status: str
    message: str
    timestamp: str


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[dict] = None


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize backend services on startup."""
    logger.info("Starting Multi-Agent Workflow API server...")
    
    # Start message bus listener
    try:
        message_bus_listener.start()
        logger.info("✓ MessageBusListener started")
    except Exception as e:
        logger.error(f"Failed to start MessageBusListener: {e}")
    
    logger.info("✓ API server ready at http://localhost:8000")
    logger.info("✓ API docs available at http://localhost:8000/docs")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down API server...")
    message_bus_listener.stop()
    logger.info("✓ MessageBusListener stopped")


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "message_bus_listener": message_bus_listener.is_running,
            "orchestrator": True
        }
    }


# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """API information."""
    return {
        "name": "Multi-Agent Workflow API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# Workflow endpoints
@app.post(
    "/api/workflows/",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Workflows"]
)
async def create_workflow(request: WorkflowCreateRequest):
    """
    Submit a new strategy development workflow.
    
    The system will:
    1. Generate a TodoList from the natural language request
    2. Create a workflow with tasks for different agents
    3. Optionally auto-execute the workflow
    
    Returns workflow_id, status, and generated TodoList.
    """
    try:
        logger.info(f"Creating workflow: {request.request[:100]}...")
        
        result = orchestrator_client.submit_workflow(
            request=request.request,
            auto_execute=request.auto_execute,
            auto_fix_mode=request.auto_fix_mode,
            max_branch_depth=request.max_branch_depth,
            context=request.context,
            user_id=request.user_id
        )
        
        logger.info(f"✓ Workflow created: {result['workflow_id']}")
        return WorkflowResponse(**result)
        
    except Exception as e:
        logger.error(f"Error creating workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "WorkflowCreationError",
                "message": str(e)
            }
        )


@app.get(
    "/api/workflows/{workflow_id}/",
    response_model=WorkflowStatusResponse,
    tags=["Workflows"]
)
async def get_workflow_status(workflow_id: str):
    """
    Get detailed status of a workflow.
    
    Returns:
    - Current status (created, running, paused, completed, failed, cancelled)
    - Progress (0.0 to 1.0)
    - Task details with states
    - Branch todos (for auto-fix)
    """
    try:
        logger.info(f"Getting status for workflow: {workflow_id}")
        
        status_data = orchestrator_client.get_workflow_status(workflow_id)
        return WorkflowStatusResponse(**status_data)
        
    except ValueError as e:
        logger.warning(f"Workflow not found: {workflow_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "WorkflowNotFound",
                "message": f"Workflow with ID {workflow_id} not found"
            }
        )
    except Exception as e:
        logger.error(f"Error getting workflow status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "StatusRetrievalError",
                "message": str(e)
            }
        )


@app.get(
    "/api/workflows/",
    response_model=List[WorkflowListItem],
    tags=["Workflows"]
)
async def list_workflows(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100, description="Number of results")
):
    """
    List all workflows with optional filtering.
    
    Query parameters:
    - status: Filter by workflow status (created, running, completed, failed)
    - limit: Maximum number of results (1-100)
    """
    try:
        logger.info(f"Listing workflows (status={status}, limit={limit})")
        
        workflows = orchestrator_client.list_workflows(
            status=status,
            limit=limit
        )
        
        return [WorkflowListItem(**wf) for wf in workflows]
        
    except Exception as e:
        logger.error(f"Error listing workflows: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "ListError",
                "message": str(e)
            }
        )


@app.patch(
    "/api/workflows/{workflow_id}/pause/",
    response_model=WorkflowControlResponse,
    tags=["Workflows"]
)
async def pause_workflow(workflow_id: str, user_id: Optional[str] = None):
    """
    Pause a running workflow.
    
    Current task will complete before pausing.
    Returns updated status and timestamp.
    """
    try:
        logger.info(f"Pausing workflow: {workflow_id}")
        
        result = orchestrator_client.pause_workflow(workflow_id, user_id)
        result['timestamp'] = result.pop('paused_at')
        
        return WorkflowControlResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "InvalidStateTransition",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Error pausing workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "PauseError",
                "message": str(e)
            }
        )


@app.patch(
    "/api/workflows/{workflow_id}/resume/",
    response_model=WorkflowControlResponse,
    tags=["Workflows"]
)
async def resume_workflow(workflow_id: str, user_id: Optional[str] = None):
    """
    Resume a paused workflow.
    
    Continues execution from where it was paused.
    Returns updated status and timestamp.
    """
    try:
        logger.info(f"Resuming workflow: {workflow_id}")
        
        result = orchestrator_client.resume_workflow(workflow_id, user_id)
        result['timestamp'] = result.pop('resumed_at')
        
        return WorkflowControlResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "InvalidStateTransition",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Error resuming workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "ResumeError",
                "message": str(e)
            }
        )


@app.delete(
    "/api/workflows/{workflow_id}/",
    response_model=WorkflowControlResponse,
    tags=["Workflows"]
)
async def cancel_workflow(workflow_id: str, user_id: Optional[str] = None):
    """
    Cancel a workflow permanently.
    
    Cannot be undone. In-progress tasks will be terminated.
    Returns cancellation confirmation.
    """
    try:
        logger.info(f"Cancelling workflow: {workflow_id}")
        
        result = orchestrator_client.cancel_workflow(workflow_id, user_id)
        result['timestamp'] = result.pop('cancelled_at')
        
        return WorkflowControlResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "WorkflowNotFound",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Error cancelling workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "CancelError",
                "message": str(e)
            }
        )


@app.get(
    "/api/workflows/{workflow_id}/tasks/",
    tags=["Workflows"]
)
async def get_workflow_tasks(workflow_id: str):
    """
    Get detailed task information for a workflow.
    
    Returns all tasks with their current states, artifacts, and results.
    """
    try:
        logger.info(f"Getting tasks for workflow: {workflow_id}")
        
        status_data = orchestrator_client.get_workflow_status(workflow_id)
        
        return {
            "workflow_id": workflow_id,
            "tasks": status_data['tasks']
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "WorkflowNotFound",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Error getting tasks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "TaskRetrievalError",
                "message": str(e)
            }
        )


# System info endpoint
@app.get("/api/system/info", tags=["System"])
async def system_info():
    """Get system information and statistics."""
    stats = message_bus_listener.get_statistics()
    
    return {
        "api_version": "1.0.0",
        "message_bus": stats,
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 70)
    print("  Multi-Agent Workflow API Server")
    print("=" * 70)
    print(f"  Docs:   http://localhost:8000/docs")
    print(f"  Health: http://localhost:8000/health")
    print("=" * 70)
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
