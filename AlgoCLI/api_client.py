"""
API Client for AlgoCLI
Handles all communication with the multi-agent backend API
"""

import httpx
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


class APIClient:
    """Async HTTP client for multi-agent workflow API"""
    
    def __init__(self, base_url: Optional[str] = None, timeout: int = 30):
        self.base_url = base_url or os.getenv("API_BASE_URL", "http://localhost:8000")
        self.timeout = timeout
        self.client: Optional[httpx.AsyncClient] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            follow_redirects=True
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.client:
            await self.client.aclose()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check API health status"""
        try:
            response = await self.client.get("/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # Workflow management
    async def create_workflow(
        self,
        request: str,
        auto_execute: bool = True,
        auto_fix_mode: bool = True,
        max_branch_depth: int = 2,
        context: Optional[Dict] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new workflow"""
        payload = {
            "request": request,
            "auto_execute": auto_execute,
            "auto_fix_mode": auto_fix_mode,
            "max_branch_depth": max_branch_depth,
        }
        
        if context:
            payload["context"] = context
        if user_id:
            payload["user_id"] = user_id
            
        response = await self.client.post("/api/workflows/", json=payload)
        response.raise_for_status()
        return response.json()
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get detailed workflow status"""
        response = await self.client.get(f"/api/workflows/{workflow_id}/")
        response.raise_for_status()
        return response.json()
    
    async def list_workflows(
        self,
        status: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """List all workflows with optional filtering"""
        params = {"limit": limit}
        if status:
            params["status"] = status
            
        response = await self.client.get("/api/workflows/", params=params)
        response.raise_for_status()
        return response.json()
    
    async def pause_workflow(
        self,
        workflow_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Pause a running workflow"""
        params = {}
        if user_id:
            params["user_id"] = user_id
            
        response = await self.client.patch(
            f"/api/workflows/{workflow_id}/pause/",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    async def resume_workflow(
        self,
        workflow_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Resume a paused workflow"""
        params = {}
        if user_id:
            params["user_id"] = user_id
            
        response = await self.client.patch(
            f"/api/workflows/{workflow_id}/resume/",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    async def cancel_workflow(
        self,
        workflow_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Cancel a workflow permanently"""
        params = {}
        if user_id:
            params["user_id"] = user_id
            
        response = await self.client.delete(
            f"/api/workflows/{workflow_id}/",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    async def get_workflow_tasks(self, workflow_id: str) -> Dict[str, Any]:
        """Get detailed task information for a workflow"""
        response = await self.client.get(f"/api/workflows/{workflow_id}/tasks/")
        response.raise_for_status()
        return response.json()
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information and statistics"""
        response = await self.client.get("/api/system/info")
        response.raise_for_status()
        return response.json()


# Convenience functions for non-async usage
def sync_health_check(base_url: Optional[str] = None) -> Dict[str, Any]:
    """Synchronous health check"""
    async def _check():
        async with APIClient(base_url=base_url) as client:
            return await client.health_check()
    
    return asyncio.run(_check())


def sync_create_workflow(
    request: str,
    auto_execute: bool = True,
    auto_fix_mode: bool = True,
    base_url: Optional[str] = None
) -> Dict[str, Any]:
    """Synchronous workflow creation"""
    async def _create():
        async with APIClient(base_url=base_url) as client:
            return await client.create_workflow(
                request=request,
                auto_execute=auto_execute,
                auto_fix_mode=auto_fix_mode
            )
    
    return asyncio.run(_create())


def sync_list_workflows(
    status: Optional[str] = None,
    limit: int = 20,
    base_url: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Synchronous workflow listing"""
    async def _list():
        async with APIClient(base_url=base_url) as client:
            return await client.list_workflows(status=status, limit=limit)
    
    return asyncio.run(_list())
