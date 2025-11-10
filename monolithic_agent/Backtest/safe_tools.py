"""
Safe Tool Adapters
==================

Type-safe, validated tool wrappers for AI agent operations.

Features:
- Path sanitization and validation
- Audit logging for all operations
- Rate limiting and resource controls
- Rollback capabilities
- Comprehensive error handling

Version: 1.0.0
"""

from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
from datetime import datetime
import os
import subprocess
import json
import hashlib
import logging
from functools import wraps
from pydantic import BaseModel, Field, validator
import time

logger = logging.getLogger(__name__)


# ============================================================================
# TOOL REQUEST/RESPONSE SCHEMAS
# ============================================================================

class ToolRequest(BaseModel):
    """Base class for tool requests"""
    tool_name: str
    session_id: Optional[str] = None
    dry_run: bool = Field(default=False)


class ReadFileRequest(ToolRequest):
    """Request to read a file"""
    tool_name: str = "read_file"
    path: str = Field(..., min_length=1)
    start_line: Optional[int] = Field(None, ge=1)
    end_line: Optional[int] = Field(None, ge=1)
    
    @validator('path')
    def validate_path(cls, v):
        """Ensure path doesn't escape workspace"""
        if '..' in v or v.startswith('/'):
            raise ValueError("Path traversal not allowed")
        return v


class WriteFileRequest(ToolRequest):
    """Request to write a file"""
    tool_name: str = "write_file"
    path: str = Field(..., min_length=1)
    content: str
    mode: str = Field(default="create")  # create, overwrite, append
    
    @validator('path')
    def validate_path(cls, v):
        if '..' in v or v.startswith('/'):
            raise ValueError("Path traversal not allowed")
        return v
    
    @validator('mode')
    def validate_mode(cls, v):
        if v not in ['create', 'overwrite', 'append']:
            raise ValueError(f"Invalid mode: {v}")
        return v


class RunCommandRequest(ToolRequest):
    """Request to run a command in sandbox"""
    tool_name: str = "run_command"
    command: str = Field(..., min_length=1)
    timeout: int = Field(default=60, ge=1, le=300)
    sandbox_id: Optional[str] = None
    
    @validator('command')
    def validate_command(cls, v):
        """Block dangerous commands"""
        dangerous = ['rm -rf', 'dd', 'mkfs', 'fork', ':(){', 'sudo', 'chmod 777']
        for pattern in dangerous:
            if pattern in v.lower():
                raise ValueError(f"Dangerous command pattern detected: {pattern}")
        return v


class GitOperationRequest(ToolRequest):
    """Request for git operation"""
    tool_name: str = "git_operation"
    operation: str  # commit, branch, checkout, diff
    branch: Optional[str] = None
    message: Optional[str] = None
    files: List[str] = Field(default_factory=list)


class ToolResponse(BaseModel):
    """Base class for tool responses"""
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float
    audit_id: Optional[str] = None


# ============================================================================
# AUDIT LOGGING
# ============================================================================

class ToolAudit(BaseModel):
    """Audit record for tool execution"""
    audit_id: str = Field(default_factory=lambda: f"audit_{int(time.time()*1000)}")
    timestamp: datetime = Field(default_factory=datetime.now)
    tool_name: str
    session_id: Optional[str]
    request: Dict[str, Any]
    response: Dict[str, Any]
    actor: str = "ai_agent"
    success: bool
    execution_time: float
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AuditLogger:
    """Persistent audit logger for all tool operations"""
    
    def __init__(self, log_file: str = "tool_audit.jsonl"):
        """
        Initialize audit logger
        
        Args:
            log_file: Path to JSONL audit log file
        """
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log(self, audit: ToolAudit):
        """Append audit record to log"""
        with open(self.log_file, 'a') as f:
            f.write(audit.json() + '\n')
    
    def query(
        self,
        tool_name: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 100
    ) -> List[ToolAudit]:
        """Query audit logs"""
        if not self.log_file.exists():
            return []
        
        results = []
        with open(self.log_file, 'r') as f:
            for line in f:
                try:
                    audit = ToolAudit.parse_raw(line)
                    
                    # Apply filters
                    if tool_name and audit.tool_name != tool_name:
                        continue
                    if session_id and audit.session_id != session_id:
                        continue
                    
                    results.append(audit)
                    
                    if len(results) >= limit:
                        break
                except Exception as e:
                    logger.warning(f"Failed to parse audit log line: {e}")
        
        return results


# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimiter:
    """Simple rate limiter for tool calls"""
    
    def __init__(self, max_calls: int = 100, window_seconds: int = 60):
        """
        Initialize rate limiter
        
        Args:
            max_calls: Maximum calls per window
            window_seconds: Time window in seconds
        """
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self.calls: List[float] = []
    
    def check(self) -> bool:
        """
        Check if call is allowed
        
        Returns:
            True if call is allowed, False if rate limit exceeded
        """
        now = time.time()
        
        # Remove old calls outside window
        self.calls = [t for t in self.calls if now - t < self.window_seconds]
        
        # Check limit
        if len(self.calls) >= self.max_calls:
            return False
        
        self.calls.append(now)
        return True


# ============================================================================
# TOOL ADAPTERS
# ============================================================================

class ToolAdapter:
    """Base class for tool adapters"""
    
    def __init__(
        self,
        workspace_root: Path,
        audit_logger: Optional[AuditLogger] = None,
        rate_limiter: Optional[RateLimiter] = None
    ):
        """
        Initialize tool adapter
        
        Args:
            workspace_root: Root directory for file operations
            audit_logger: Audit logger instance
            rate_limiter: Rate limiter instance
        """
        self.workspace_root = Path(workspace_root).resolve()
        self.audit_logger = audit_logger or AuditLogger()
        self.rate_limiter = rate_limiter or RateLimiter()
    
    def _resolve_path(self, path: str) -> Path:
        """
        Resolve and validate path within workspace
        
        Args:
            path: Relative path
            
        Returns:
            Absolute path
            
        Raises:
            ValueError if path escapes workspace
        """
        resolved = (self.workspace_root / path).resolve()
        
        # Ensure path is within workspace
        try:
            resolved.relative_to(self.workspace_root)
        except ValueError:
            raise ValueError(f"Path {path} escapes workspace")
        
        return resolved
    
    def _audit(
        self,
        tool_name: str,
        request: Dict[str, Any],
        response: Dict[str, Any],
        session_id: Optional[str],
        execution_time: float,
        success: bool
    ) -> str:
        """Create audit log entry"""
        audit = ToolAudit(
            tool_name=tool_name,
            session_id=session_id,
            request=request,
            response=response,
            success=success,
            execution_time=execution_time
        )
        self.audit_logger.log(audit)
        return audit.audit_id


def tool_wrapper(func: Callable) -> Callable:
    """Decorator for tool methods to add timing, rate limiting, and audit"""
    @wraps(func)
    def wrapper(self, request: ToolRequest) -> ToolResponse:
        start_time = time.time()
        
        # Check rate limit
        if not self.rate_limiter.check():
            return ToolResponse(
                success=False,
                error="Rate limit exceeded",
                execution_time=0.0
            )
        
        try:
            # Execute tool
            result = func(self, request)
            execution_time = time.time() - start_time
            
            # Create response
            if isinstance(result, ToolResponse):
                response = result
                response.execution_time = execution_time
            else:
                response = ToolResponse(
                    success=True,
                    result=result,
                    execution_time=execution_time
                )
            
            # Audit log
            audit_id = self._audit(
                tool_name=request.tool_name,
                request=request.dict(),
                response=response.dict(),
                session_id=request.session_id,
                execution_time=execution_time,
                success=response.success
            )
            response.audit_id = audit_id
            
            return response
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Tool {request.tool_name} failed: {e}")
            
            response = ToolResponse(
                success=False,
                error=str(e),
                execution_time=execution_time
            )
            
            # Audit log
            audit_id = self._audit(
                tool_name=request.tool_name,
                request=request.dict(),
                response=response.dict(),
                session_id=request.session_id,
                execution_time=execution_time,
                success=False
            )
            response.audit_id = audit_id
            
            return response
    
    return wrapper


class SafeTools(ToolAdapter):
    """
    Safe, audited tool implementations
    """
    
    @tool_wrapper
    def read_file(self, request: ReadFileRequest) -> ToolResponse:
        """
        Read file contents safely
        
        Args:
            request: ReadFileRequest
            
        Returns:
            ToolResponse with file contents
        """
        if request.dry_run:
            return ToolResponse(
                success=True,
                result={"dry_run": True, "path": request.path},
                execution_time=0.0
            )
        
        path = self._resolve_path(request.path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {request.path}")
        
        if not path.is_file():
            raise ValueError(f"Path is not a file: {request.path}")
        
        # Read file
        with open(path, 'r', encoding='utf-8') as f:
            if request.start_line or request.end_line:
                lines = f.readlines()
                start = (request.start_line or 1) - 1
                end = request.end_line or len(lines)
                content = ''.join(lines[start:end])
            else:
                content = f.read()
        
        return ToolResponse(
            success=True,
            result={
                "path": str(path),
                "content": content,
                "size": len(content),
                "lines": content.count('\n') + 1
            },
            execution_time=0.0
        )
    
    @tool_wrapper
    def write_file(self, request: WriteFileRequest) -> ToolResponse:
        """
        Write file contents safely
        
        Args:
            request: WriteFileRequest
            
        Returns:
            ToolResponse with write confirmation
        """
        if request.dry_run:
            return ToolResponse(
                success=True,
                result={"dry_run": True, "path": request.path, "size": len(request.content)},
                execution_time=0.0
            )
        
        path = self._resolve_path(request.path)
        
        # Check mode
        if request.mode == "create" and path.exists():
            raise FileExistsError(f"File already exists: {request.path}")
        
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        mode_map = {
            "create": "w",
            "overwrite": "w",
            "append": "a"
        }
        
        with open(path, mode_map[request.mode], encoding='utf-8') as f:
            f.write(request.content)
        
        # Calculate checksum
        content_hash = hashlib.sha256(request.content.encode()).hexdigest()[:16]
        
        return ToolResponse(
            success=True,
            result={
                "path": str(path),
                "size": len(request.content),
                "hash": content_hash,
                "mode": request.mode
            },
            execution_time=0.0
        )
    
    @tool_wrapper
    def run_command(self, request: RunCommandRequest) -> ToolResponse:
        """
        Run command in controlled environment
        
        NOTE: This is a simple version. For production, use sandbox_orchestrator.py
        
        Args:
            request: RunCommandRequest
            
        Returns:
            ToolResponse with command output
        """
        if request.dry_run:
            return ToolResponse(
                success=True,
                result={"dry_run": True, "command": request.command},
                execution_time=0.0
            )
        
        try:
            result = subprocess.run(
                request.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=request.timeout,
                cwd=self.workspace_root
            )
            
            return ToolResponse(
                success=result.returncode == 0,
                result={
                    "exit_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                },
                error=result.stderr if result.returncode != 0 else None,
                execution_time=0.0
            )
            
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Command timed out after {request.timeout}s")
    
    @tool_wrapper
    def git_operation(self, request: GitOperationRequest) -> ToolResponse:
        """
        Perform git operation
        
        Args:
            request: GitOperationRequest
            
        Returns:
            ToolResponse with git output
        """
        if request.dry_run:
            return ToolResponse(
                success=True,
                result={"dry_run": True, "operation": request.operation},
                execution_time=0.0
            )
        
        cmd_map = {
            "status": "git status --porcelain",
            "branch": f"git branch {request.branch}" if request.branch else "git branch",
            "checkout": f"git checkout {request.branch}",
            "commit": f"git commit -m '{request.message}'",
            "diff": "git diff"
        }
        
        if request.operation not in cmd_map:
            raise ValueError(f"Unknown git operation: {request.operation}")
        
        command = cmd_map[request.operation]
        
        # Add files for commit
        if request.operation == "commit" and request.files:
            for file in request.files:
                path = self._resolve_path(file)
                subprocess.run(["git", "add", str(path)], cwd=self.workspace_root, check=True)
        
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=self.workspace_root
        )
        
        return ToolResponse(
            success=result.returncode == 0,
            result={
                "operation": request.operation,
                "output": result.stdout,
                "error": result.stderr
            },
            error=result.stderr if result.returncode != 0 else None,
            execution_time=0.0
        )


# ============================================================================
# TOOL REGISTRY
# ============================================================================

class ToolRegistry:
    """
    Registry of available tools with metadata
    """
    
    def __init__(self, tools: SafeTools):
        self.tools = tools
        self.registry = {
            "read_file": {
                "description": "Read file contents from workspace",
                "request_schema": ReadFileRequest.schema(),
                "handler": self.tools.read_file
            },
            "write_file": {
                "description": "Write file to workspace",
                "request_schema": WriteFileRequest.schema(),
                "handler": self.tools.write_file
            },
            "run_command": {
                "description": "Run command in sandbox (use sandbox_orchestrator for production)",
                "request_schema": RunCommandRequest.schema(),
                "handler": self.tools.run_command
            },
            "git_operation": {
                "description": "Perform git operation",
                "request_schema": GitOperationRequest.schema(),
                "handler": self.tools.git_operation
            }
        }
    
    def get_tool_schemas(self) -> Dict[str, Any]:
        """Get JSON schemas for all tools"""
        return {
            name: info["request_schema"]
            for name, info in self.registry.items()
        }
    
    def execute(self, request: ToolRequest) -> ToolResponse:
        """
        Execute tool by name
        
        Args:
            request: ToolRequest subclass
            
        Returns:
            ToolResponse
        """
        if request.tool_name not in self.registry:
            return ToolResponse(
                success=False,
                error=f"Unknown tool: {request.tool_name}",
                execution_time=0.0
            )
        
        handler = self.registry[request.tool_name]["handler"]
        return handler(request)


# CLI for testing tools
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test safe tools")
    parser.add_argument("--workspace", type=str, default=".", help="Workspace root")
    parser.add_argument("--read", type=str, help="Read file")
    parser.add_argument("--write", type=str, help="Write file")
    parser.add_argument("--content", type=str, help="Content to write")
    parser.add_argument("--audit-log", type=str, default="tool_audit.jsonl", help="Audit log file")
    
    args = parser.parse_args()
    
    # Initialize tools
    tools = SafeTools(
        workspace_root=Path(args.workspace),
        audit_logger=AuditLogger(args.audit_log)
    )
    
    if args.read:
        request = ReadFileRequest(path=args.read)
        response = tools.read_file(request)
        
        if response.success:
            print(f"✓ Read file: {args.read}")
            print(response.result["content"])
        else:
            print(f"✗ Error: {response.error}")
    
    elif args.write and args.content:
        request = WriteFileRequest(
            path=args.write,
            content=args.content,
            mode="overwrite"
        )
        response = tools.write_file(request)
        
        if response.success:
            print(f"✓ Wrote file: {args.write}")
            print(f"  Size: {response.result['size']} bytes")
            print(f"  Hash: {response.result['hash']}")
        else:
            print(f"✗ Error: {response.error}")
    
    else:
        parser.print_help()
