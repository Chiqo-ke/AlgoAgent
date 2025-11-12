"""
Terminal Command Executor
=========================

Executes Python scripts in the .venv environment and captures results.
Parses output for errors, warnings, and success indicators.

Features:
- Run scripts in .venv with proper path resolution
- Capture stdout/stderr with real-time streaming
- Parse errors and extract stack traces
- Identify common issues (import errors, syntax errors, runtime errors)
- Return structured results for AI processing

Version: 1.0.0
"""

import subprocess
import sys
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Execution status codes"""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    NOT_FOUND = "not_found"


@dataclass
class ExecutionResult:
    """Structured execution result"""
    status: ExecutionStatus
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    errors: List[Dict[str, Any]]
    warnings: List[str]
    summary: Dict[str, Any]


class TerminalExecutor:
    """
    Execute Python scripts in .venv and parse results
    """
    
    def __init__(self, project_root: Optional[Path] = None, venv_path: Optional[Path] = None):
        """
        Initialize Terminal Executor
        
        Args:
            project_root: Project root directory (defaults to AlgoAgent)
            venv_path: Virtual environment path (defaults to project_root/.venv)
        """
        self.project_root = project_root or Path(__file__).parent.parent
        self.venv_path = venv_path or (self.project_root / ".venv")
        
        # Python executable in venv
        if sys.platform == "win32":
            self.python_exe = self.venv_path / "Scripts" / "python.exe"
        else:
            self.python_exe = self.venv_path / "bin" / "python"
        
        if not self.python_exe.exists():
            raise FileNotFoundError(f"Python executable not found: {self.python_exe}")
        
        logger.info(f"TerminalExecutor initialized with venv: {self.venv_path}")
    
    def run_script(
        self,
        script_path: Path,
        args: Optional[List[str]] = None,
        cwd: Optional[Path] = None,
        timeout: Optional[int] = 300,
        capture_output: bool = True
    ) -> ExecutionResult:
        """
        Run a Python script in .venv environment
        
        Args:
            script_path: Path to Python script
            args: Optional command-line arguments
            cwd: Working directory (defaults to script's directory)
            timeout: Execution timeout in seconds (default 300)
            capture_output: Whether to capture stdout/stderr
        
        Returns:
            ExecutionResult with structured output
        """
        if not script_path.exists():
            return ExecutionResult(
                status=ExecutionStatus.NOT_FOUND,
                exit_code=-1,
                stdout="",
                stderr=f"Script not found: {script_path}",
                execution_time=0.0,
                errors=[{"type": "FileNotFoundError", "message": f"Script not found: {script_path}"}],
                warnings=[],
                summary={"status": "not_found"}
            )
        
        # Build command
        cmd = [str(self.python_exe), str(script_path)]
        if args:
            cmd.extend(args)
        
        # Set working directory
        if cwd is None:
            cwd = script_path.parent
        
        logger.info(f"Executing: {' '.join(cmd)}")
        logger.info(f"Working directory: {cwd}")
        
        # Execute
        import time
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(cwd),
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                env=self._get_env()
            )
            
            execution_time = time.time() - start_time
            
            # Parse output
            errors = self._parse_errors(result.stderr, result.stdout)
            warnings = self._parse_warnings(result.stderr, result.stdout)
            summary = self._create_summary(result, errors, warnings)
            
            status = ExecutionStatus.SUCCESS if result.returncode == 0 else ExecutionStatus.ERROR
            
            return ExecutionResult(
                status=status,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time=execution_time,
                errors=errors,
                warnings=warnings,
                summary=summary
            )
        
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return ExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                exit_code=-1,
                stdout="",
                stderr=f"Execution timed out after {timeout} seconds",
                execution_time=execution_time,
                errors=[{"type": "TimeoutError", "message": f"Execution timed out after {timeout}s"}],
                warnings=[],
                summary={"status": "timeout", "timeout": timeout}
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                execution_time=execution_time,
                errors=[{"type": type(e).__name__, "message": str(e)}],
                warnings=[],
                summary={"status": "error", "exception": str(e)}
            )
    
    def _get_env(self) -> Dict[str, str]:
        """Get environment variables for subprocess"""
        import os
        env = os.environ.copy()
        # Add venv to PATH
        if sys.platform == "win32":
            env["PATH"] = f"{self.venv_path / 'Scripts'};{env.get('PATH', '')}"
        else:
            env["PATH"] = f"{self.venv_path / 'bin'}:{env.get('PATH', '')}"
        return env
    
    def _parse_errors(self, stderr: str, stdout: str) -> List[Dict[str, Any]]:
        """
        Parse errors from output
        
        Returns:
            List of error dictionaries with type, message, file, line, traceback
        """
        errors = []
        combined = stderr + "\n" + stdout
        
        # Pattern: Traceback + Exception
        traceback_pattern = r"Traceback \(most recent call last\):(.*?)(?=\n\w+Error:|$)"
        exception_pattern = r"(\w+Error): (.+?)(?=\n|$)"
        
        # Find tracebacks
        for match in re.finditer(traceback_pattern, combined, re.DOTALL):
            traceback_text = match.group(1).strip()
            
            # Find associated exception
            remaining_text = combined[match.end():]
            exc_match = re.search(exception_pattern, remaining_text)
            
            if exc_match:
                error_type = exc_match.group(1)
                error_message = exc_match.group(2)
                
                # Extract file and line from traceback
                file_line_pattern = r'File "(.+?)", line (\d+)'
                file_matches = list(re.finditer(file_line_pattern, traceback_text))
                
                if file_matches:
                    last_match = file_matches[-1]
                    file_path = last_match.group(1)
                    line_number = int(last_match.group(2))
                else:
                    file_path = None
                    line_number = None
                
                errors.append({
                    "type": error_type,
                    "message": error_message,
                    "file": file_path,
                    "line": line_number,
                    "traceback": traceback_text
                })
        
        # Also catch simple errors without traceback
        if not errors:
            for match in re.finditer(exception_pattern, combined):
                errors.append({
                    "type": match.group(1),
                    "message": match.group(2),
                    "file": None,
                    "line": None,
                    "traceback": None
                })
        
        return errors
    
    def _parse_warnings(self, stderr: str, stdout: str) -> List[str]:
        """Parse warnings from output"""
        warnings = []
        combined = stderr + "\n" + stdout
        
        # Pattern: UserWarning, DeprecationWarning, etc.
        warning_pattern = r"(?:UserWarning|DeprecationWarning|FutureWarning|RuntimeWarning): (.+?)(?=\n|$)"
        
        for match in re.finditer(warning_pattern, combined):
            warnings.append(match.group(1).strip())
        
        # Also look for "Warning:" prefix
        for line in combined.split("\n"):
            if "warning:" in line.lower() and not any(w in line for w in warnings):
                warnings.append(line.strip())
        
        return warnings
    
    def _create_summary(
        self,
        result: subprocess.CompletedProcess,
        errors: List[Dict[str, Any]],
        warnings: List[str]
    ) -> Dict[str, Any]:
        """
        Create summary of execution results
        
        Extracts key metrics like returns, Sharpe ratio, trade count, etc.
        """
        summary = {
            "exit_code": result.returncode,
            "success": result.returncode == 0,
            "error_count": len(errors),
            "warning_count": len(warnings)
        }
        
        combined = result.stdout + "\n" + result.stderr
        
        # Extract backtest metrics if present
        metrics_patterns = {
            "return_pct": r"Return \[%\]:\s*([-\d.]+)",
            "sharpe_ratio": r"Sharpe Ratio:\s*([-\d.]+)",
            "max_drawdown_pct": r"Max\. Drawdown \[%\]:\s*([-\d.]+)",
            "win_rate_pct": r"Win Rate \[%\]:\s*([-\d.]+)",
            "trade_count": r"# Trades:\s*(\d+)",
            "final_equity": r"Final Equity:\s*\$?([\d,]+\.?\d*)",
        }
        
        for key, pattern in metrics_patterns.items():
            match = re.search(pattern, combined)
            if match:
                value_str = match.group(1).replace(",", "")
                try:
                    summary[key] = float(value_str)
                except ValueError:
                    summary[key] = value_str
        
        # Check for success indicators
        if "✅" in combined or "SUCCESS" in combined or "Backtest complete" in combined:
            summary["backtest_completed"] = True
        else:
            summary["backtest_completed"] = False
        
        # Extract symbol if present
        symbol_match = re.search(r"Symbol:\s*(\w+)", combined)
        if symbol_match:
            summary["symbol"] = symbol_match.group(1)
        
        return summary
    
    def run_command(
        self,
        command: str,
        cwd: Optional[Path] = None,
        timeout: Optional[int] = 300
    ) -> ExecutionResult:
        """
        Run arbitrary command in .venv (e.g., pip install, pytest)
        
        Args:
            command: Command to run (e.g., "pip list", "pytest test_file.py")
            cwd: Working directory
            timeout: Timeout in seconds
        
        Returns:
            ExecutionResult
        """
        cwd = cwd or self.project_root
        
        logger.info(f"Running command: {command}")
        
        import time
        start_time = time.time()
        
        try:
            # Parse command
            cmd_parts = command.split()
            
            # If it's a Python command, use venv Python
            if cmd_parts[0] == "python":
                cmd_parts[0] = str(self.python_exe)
            
            result = subprocess.run(
                cmd_parts,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=timeout,
                env=self._get_env()
            )
            
            execution_time = time.time() - start_time
            
            errors = self._parse_errors(result.stderr, result.stdout)
            warnings = self._parse_warnings(result.stderr, result.stdout)
            summary = self._create_summary(result, errors, warnings)
            
            status = ExecutionStatus.SUCCESS if result.returncode == 0 else ExecutionStatus.ERROR
            
            return ExecutionResult(
                status=status,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time=execution_time,
                errors=errors,
                warnings=warnings,
                summary=summary
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                execution_time=execution_time,
                errors=[{"type": type(e).__name__, "message": str(e)}],
                warnings=[],
                summary={"status": "error", "exception": str(e)}
            )


def run_script_in_venv(script_path: str, args: List[str] = None) -> ExecutionResult:
    """
    Convenience function to run a script in .venv
    
    Args:
        script_path: Path to script (relative to AlgoAgent or absolute)
        args: Optional command-line arguments
    
    Returns:
        ExecutionResult
    """
    executor = TerminalExecutor()
    
    # Resolve path
    script = Path(script_path)
    if not script.is_absolute():
        script = executor.project_root / script
    
    return executor.run_script(script, args=args)


if __name__ == "__main__":
    # Test the executor
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Testing TerminalExecutor...")
    print("="*80)
    
    # Test with the MA crossover strategy
    test_script = Path(__file__).parent / "codes" / "test_ma_crossover_backtesting_py.py"
    
    if test_script.exists():
        print(f"\nRunning test script: {test_script.name}")
        print("-"*80)
        
        executor = TerminalExecutor()
        result = executor.run_script(test_script)
        
        print(f"\nStatus: {result.status.value}")
        print(f"Exit Code: {result.exit_code}")
        print(f"Execution Time: {result.execution_time:.2f}s")
        print(f"\nErrors: {len(result.errors)}")
        for err in result.errors:
            print(f"  - {err['type']}: {err['message']}")
            if err.get('file'):
                print(f"    File: {err['file']}, Line: {err['line']}")
        
        print(f"\nWarnings: {len(result.warnings)}")
        for warn in result.warnings:
            print(f"  - {warn}")
        
        print(f"\nSummary:")
        for key, value in result.summary.items():
            print(f"  {key}: {value}")
        
        if result.status == ExecutionStatus.SUCCESS:
            print("\n✅ Execution successful!")
        else:
            print("\n❌ Execution failed")
            print("\nStderr:")
            print(result.stderr[:500])  # First 500 chars
    else:
        print(f"Test script not found: {test_script}")
        print("Create a test strategy first.")
