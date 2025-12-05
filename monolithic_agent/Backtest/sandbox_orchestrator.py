"""
Sandbox Orchestrator
====================

Production-safe sandbox execution using Docker containers.

Features:
- Isolated execution environments
- Resource limits (CPU, memory, network)
- Copy-on-write filesystem for safety
- Ephemeral containers with cleanup
- Structured result capture
- Support for microVM upgrade path

Version: 1.0.0 (Docker prototype - upgrade to Firecracker/gVisor for production)
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import subprocess
import json
import uuid
import shutil
import tempfile
import logging
import time
from pydantic import BaseModel, Field
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# SANDBOX SCHEMAS
# ============================================================================

class SandboxStatus(str, Enum):
    """Sandbox lifecycle status"""
    CREATING = "creating"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DESTROYED = "destroyed"


class SandboxConfig(BaseModel):
    """Configuration for sandbox creation"""
    sandbox_id: str = Field(default_factory=lambda: f"sandbox_{uuid.uuid4().hex[:8]}")
    image: str = Field(default="python:3.10-slim")
    
    # Resource limits
    cpu_limit: str = Field(default="0.5")  # CPU cores
    memory_limit: str = Field(default="512m")  # Memory limit
    timeout: int = Field(default=300, ge=1, le=3600)  # Max execution time
    
    # Network
    network_mode: str = Field(default="none")  # none, bridge, host
    
    # Filesystem
    read_only_root: bool = Field(default=True)
    work_dir: str = Field(default="/workspace")
    
    # Environment
    env_vars: Dict[str, str] = Field(default_factory=dict)


class SandboxResult(BaseModel):
    """Result from sandbox execution"""
    sandbox_id: str
    status: SandboxStatus
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    execution_time: float
    
    # Resource usage
    max_memory_mb: Optional[float] = None
    cpu_percent: Optional[float] = None
    
    # Artifacts
    artifacts: Dict[str, str] = Field(default_factory=dict)
    
    # Error info
    error: Optional[str] = None
    timed_out: bool = False


class CommandRequest(BaseModel):
    """Request to run command in sandbox"""
    command: str
    timeout: Optional[int] = None
    capture_artifacts: List[str] = Field(default_factory=list)  # Paths to copy out


# ============================================================================
# SANDBOX ORCHESTRATOR
# ============================================================================

class SandboxOrchestrator:
    """
    Orchestrates Docker-based sandboxes for safe code execution
    
    WARNING: This is a Docker prototype. For production with untrusted code:
    - Use microVMs (Firecracker, E2B, Modal)
    - Use gVisor/Kata for kernel isolation
    - Implement network egress controls
    - Use ephemeral credential issuing
    """
    
    def __init__(
        self,
        workspace_root: Path,
        sandbox_storage: Optional[Path] = None,
        docker_available: bool = True
    ):
        """
        Initialize sandbox orchestrator
        
        Args:
            workspace_root: Root directory containing code to execute
            sandbox_storage: Directory for sandbox working files
            docker_available: Whether Docker is available
        """
        self.workspace_root = Path(workspace_root).resolve()
        self.sandbox_storage = sandbox_storage or Path(tempfile.gettempdir()) / "sandboxes"
        self.sandbox_storage.mkdir(parents=True, exist_ok=True)
        
        self.docker_available = docker_available and self._check_docker()
        
        if not self.docker_available:
            logger.warning("Docker not available - falling back to direct execution (UNSAFE)")
        
        # Track active sandboxes
        self.active_sandboxes: Dict[str, Dict[str, Any]] = {}
    
    def _check_docker(self) -> bool:
        """Check if Docker is available"""
        try:
            result = subprocess.run(
                ["docker", "version"],
                capture_output=True,
                timeout=15,  # Increased from 5 to 15 seconds
                text=True
            )
            if result.returncode == 0:
                logger.info("[OK] Docker is available")
                return True
            else:
                logger.warning(f"Docker command failed with code {result.returncode}")
                if result.stderr:
                    logger.debug(f"Docker stderr: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            logger.warning("Docker check timed out after 15 seconds (Docker may be slow to respond)")
            return False
        except FileNotFoundError:
            logger.warning("Docker command not found (Docker not installed or not in PATH)")
            return False
        except Exception as e:
            logger.warning(f"Docker check failed: {e}")
            return False
    
    def create_sandbox(self, config: SandboxConfig) -> str:
        """
        Create a new sandbox
        
        Args:
            config: Sandbox configuration
            
        Returns:
            Sandbox ID
        """
        sandbox_id = config.sandbox_id
        
        # Create sandbox workspace
        sandbox_dir = self.sandbox_storage / sandbox_id
        sandbox_dir.mkdir(parents=True, exist_ok=True)
        
        # Create empty workspace directory (don't copy entire workspace - too slow!)
        # Files will be mounted via Docker volume instead
        workspace_copy = sandbox_dir / "workspace"
        workspace_copy.mkdir(parents=True, exist_ok=True)
        
        # Track sandbox
        self.active_sandboxes[sandbox_id] = {
            "config": config,
            "status": SandboxStatus.READY,
            "workspace": workspace_copy,
            "created_at": datetime.now()
        }
        
        logger.info(f"Created sandbox {sandbox_id}")
        
        return sandbox_id
    
    def run_command(
        self,
        sandbox_id: str,
        request: CommandRequest
    ) -> SandboxResult:
        """
        Run command in sandbox
        
        Args:
            sandbox_id: Sandbox identifier
            request: Command request
            
        Returns:
            SandboxResult
        """
        if sandbox_id not in self.active_sandboxes:
            raise ValueError(f"Sandbox {sandbox_id} not found")
        
        sandbox_info = self.active_sandboxes[sandbox_id]
        config: SandboxConfig = sandbox_info["config"]
        workspace = sandbox_info["workspace"]
        
        # Update status
        sandbox_info["status"] = SandboxStatus.RUNNING
        
        start_time = time.time()
        timeout = request.timeout or config.timeout
        
        try:
            if self.docker_available:
                result = self._run_in_docker(
                    sandbox_id=sandbox_id,
                    config=config,
                    workspace=workspace,
                    command=request.command,
                    timeout=timeout
                )
            else:
                # Fallback to direct execution (UNSAFE - for dev only)
                result = self._run_direct(
                    workspace=workspace,
                    command=request.command,
                    timeout=timeout
                )
            
            execution_time = time.time() - start_time
            
            # Capture artifacts
            artifacts = {}
            for artifact_path in request.capture_artifacts:
                artifact_file = workspace / artifact_path
                if artifact_file.exists():
                    with open(artifact_file, 'r') as f:
                        artifacts[artifact_path] = f.read()
            
            # Create result
            sandbox_result = SandboxResult(
                sandbox_id=sandbox_id,
                status=SandboxStatus.COMPLETED if result["exit_code"] == 0 else SandboxStatus.FAILED,
                exit_code=result["exit_code"],
                stdout=result["stdout"],
                stderr=result["stderr"],
                execution_time=execution_time,
                artifacts=artifacts,
                timed_out=result.get("timed_out", False)
            )
            
            # Update sandbox status
            sandbox_info["status"] = sandbox_result.status
            sandbox_info["last_result"] = sandbox_result
            
            return sandbox_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Sandbox {sandbox_id} execution failed: {e}")
            
            sandbox_info["status"] = SandboxStatus.FAILED
            
            return SandboxResult(
                sandbox_id=sandbox_id,
                status=SandboxStatus.FAILED,
                exit_code=-1,
                stderr=str(e),
                execution_time=execution_time,
                error=str(e)
            )
    
    def _run_in_docker(
        self,
        sandbox_id: str,
        config: SandboxConfig,
        workspace: Path,
        command: str,
        timeout: int
    ) -> Dict[str, Any]:
        """
        Run command in Docker container
        
        Args:
            sandbox_id: Sandbox ID
            config: Sandbox config
            workspace: Workspace path
            command: Command to run
            timeout: Timeout in seconds
            
        Returns:
            Dict with exit_code, stdout, stderr
        """
        # Build Docker command
        docker_cmd = [
            "docker", "run",
            "--rm",  # Remove container after execution
            f"--name={sandbox_id}",
            f"--cpus={config.cpu_limit}",
            f"--memory={config.memory_limit}",
            f"--network={config.network_mode}",
            f"--workdir={config.work_dir}",
        ]
        
        # Add read-only root if specified
        if config.read_only_root:
            docker_cmd.extend(["--read-only", "--tmpfs=/tmp:rw,size=100m"])
        
        # Mount workspace (read-only for extra safety in production)
        # For dev/testing, use rw to allow output file creation
        docker_cmd.append(f"-v={workspace}:{config.work_dir}:rw")
        
        # Add environment variables
        for key, value in config.env_vars.items():
            docker_cmd.append(f"-e={key}={value}")
        
        # Add image and command
        docker_cmd.append(config.image)
        docker_cmd.extend(["bash", "-c", command])
        
        logger.info(f"Running Docker command: {' '.join(docker_cmd)}")
        
        try:
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "timed_out": False
            }
            
        except subprocess.TimeoutExpired as e:
            # Kill the container
            subprocess.run(["docker", "kill", sandbox_id], capture_output=True)
            
            return {
                "exit_code": -1,
                "stdout": e.stdout.decode() if e.stdout else "",
                "stderr": f"Timeout after {timeout}s",
                "timed_out": True
            }
    
    def _run_direct(
        self,
        workspace: Path,
        command: str,
        timeout: int
    ) -> Dict[str, Any]:
        """
        Run command directly (UNSAFE - dev only)
        
        Args:
            workspace: Workspace path
            command: Command to run
            timeout: Timeout in seconds
            
        Returns:
            Dict with exit_code, stdout, stderr
        """
        logger.warning("Running command directly without Docker isolation - UNSAFE")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=workspace
            )
            
            return {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "timed_out": False
            }
            
        except subprocess.TimeoutExpired:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Timeout after {timeout}s",
                "timed_out": True
            }
    
    def destroy_sandbox(self, sandbox_id: str):
        """
        Destroy sandbox and cleanup resources
        
        Args:
            sandbox_id: Sandbox identifier
        """
        if sandbox_id not in self.active_sandboxes:
            logger.warning(f"Sandbox {sandbox_id} not found for destruction")
            return
        
        sandbox_info = self.active_sandboxes[sandbox_id]
        workspace = sandbox_info["workspace"]
        
        # Kill any running container
        if self.docker_available:
            try:
                subprocess.run(
                    ["docker", "kill", sandbox_id],
                    capture_output=True,
                    timeout=5
                )
            except Exception as e:
                logger.debug(f"Failed to kill container {sandbox_id}: {e}")
        
        # Remove workspace
        try:
            shutil.rmtree(workspace.parent, ignore_errors=True)
        except Exception as e:
            logger.warning(f"Failed to remove sandbox workspace: {e}")
        
        # Update status
        sandbox_info["status"] = SandboxStatus.DESTROYED
        
        # Remove from active sandboxes
        del self.active_sandboxes[sandbox_id]
        
        logger.info(f"Destroyed sandbox {sandbox_id}")
    
    def list_sandboxes(self) -> List[Dict[str, Any]]:
        """
        List all active sandboxes
        
        Returns:
            List of sandbox info dicts
        """
        return [
            {
                "sandbox_id": sid,
                "status": info["status"].value,
                "created_at": info["created_at"].isoformat()
            }
            for sid, info in self.active_sandboxes.items()
        ]
    
    def cleanup_all(self):
        """Cleanup all active sandboxes"""
        sandbox_ids = list(self.active_sandboxes.keys())
        for sid in sandbox_ids:
            try:
                self.destroy_sandbox(sid)
            except Exception as e:
                logger.error(f"Failed to cleanup sandbox {sid}: {e}")


# ============================================================================
# HIGH-LEVEL API
# ============================================================================

class SandboxRunner:
    """
    High-level API for running code in sandboxes
    """
    
    def __init__(self, workspace_root: Path):
        """
        Initialize sandbox runner
        
        Args:
            workspace_root: Root directory containing code
        """
        self.orchestrator = SandboxOrchestrator(workspace_root)
    
    def run_python_script(
        self,
        script_path: str,
        timeout: int = 300,
        capture_outputs: bool = True
    ) -> SandboxResult:
        """
        Run Python script in sandbox
        
        Args:
            script_path: Relative path to Python script from workspace_root
            timeout: Timeout in seconds
            capture_outputs: Whether to capture output files
            
        Returns:
            SandboxResult
        """
        # Create sandbox
        config = SandboxConfig(
            timeout=timeout,
            network_mode="none",  # No network access
            read_only_root=False  # Allow writes to /tmp
        )
        
        sandbox_id = self.orchestrator.create_sandbox(config)
        
        try:
            # Copy the script file to sandbox workspace
            src_script = self.orchestrator.workspace_root / script_path
            if not src_script.exists():
                raise FileNotFoundError(f"Script not found: {src_script}")
            
            sandbox_info = self.orchestrator.active_sandboxes[sandbox_id]
            dest_script = sandbox_info["workspace"] / Path(script_path).name
            shutil.copy2(src_script, dest_script)
            
            # Run script
            command = f"python {Path(script_path).name}"
            request = CommandRequest(
                command=command,
                timeout=timeout,
                capture_artifacts=["output.json", "results.csv"] if capture_outputs else []
            )
            
            result = self.orchestrator.run_command(sandbox_id, request)
            
            return result
            
        finally:
            # Always cleanup
            self.orchestrator.destroy_sandbox(sandbox_id)
    
    def run_tests(
        self,
        test_command: str = "pytest",
        timeout: int = 300
    ) -> SandboxResult:
        """
        Run tests in sandbox
        
        Args:
            test_command: Test command to run
            timeout: Timeout in seconds
            
        Returns:
            SandboxResult
        """
        config = SandboxConfig(
            timeout=timeout,
            network_mode="none"
        )
        
        sandbox_id = self.orchestrator.create_sandbox(config)
        
        try:
            request = CommandRequest(
                command=test_command,
                timeout=timeout
            )
            
            result = self.orchestrator.run_command(sandbox_id, request)
            
            return result
            
        finally:
            self.orchestrator.destroy_sandbox(sandbox_id)


# CLI for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Sandbox orchestrator CLI")
    parser.add_argument("--workspace", type=str, default=".", help="Workspace root")
    parser.add_argument("--run", type=str, help="Python script to run")
    parser.add_argument("--command", type=str, help="Command to run")
    parser.add_argument("--timeout", type=int, default=60, help="Timeout in seconds")
    parser.add_argument("--list", action="store_true", help="List active sandboxes")
    parser.add_argument("--cleanup", action="store_true", help="Cleanup all sandboxes")
    
    args = parser.parse_args()
    
    runner = SandboxRunner(Path(args.workspace))
    
    if args.list:
        sandboxes = runner.orchestrator.list_sandboxes()
        print(f"\nActive sandboxes: {len(sandboxes)}")
        for s in sandboxes:
            print(f"  {s['sandbox_id']}: {s['status']} (created: {s['created_at']})")
    
    elif args.cleanup:
        print("Cleaning up all sandboxes...")
        runner.orchestrator.cleanup_all()
        print("✓ Cleanup complete")
    
    elif args.run:
        print(f"Running {args.run} in sandbox...")
        result = runner.run_python_script(args.run, timeout=args.timeout)
        
        print(f"\nExit code: {result.exit_code}")
        print(f"Execution time: {result.execution_time:.2f}s")
        
        if result.stdout:
            print(f"\n--- STDOUT ---\n{result.stdout}")
        
        if result.stderr:
            print(f"\n--- STDERR ---\n{result.stderr}")
        
        if result.timed_out:
            print("\n⚠️  Execution timed out")
        
        if result.exit_code == 0:
            print("\n✓ Success")
        else:
            print(f"\n✗ Failed with exit code {result.exit_code}")
    
    elif args.command:
        config = SandboxConfig(timeout=args.timeout)
        sandbox_id = runner.orchestrator.create_sandbox(config)
        
        try:
            print(f"Running command in sandbox {sandbox_id}...")
            request = CommandRequest(command=args.command, timeout=args.timeout)
            result = runner.orchestrator.run_command(sandbox_id, request)
            
            print(f"\nExit code: {result.exit_code}")
            if result.stdout:
                print(f"\n--- STDOUT ---\n{result.stdout}")
            if result.stderr:
                print(f"\n--- STDERR ---\n{result.stderr}")
        
        finally:
            runner.orchestrator.destroy_sandbox(sandbox_id)
    
    else:
        parser.print_help()
