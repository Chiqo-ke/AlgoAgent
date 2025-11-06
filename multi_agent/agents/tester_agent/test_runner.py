"""Test runner for executing tests locally or in Docker sandbox."""

import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class TestRunner:
    """Execute tests using pytest, mypy, flake8, and bandit."""
    
    def __init__(self, workspace: Path):
        """
        Initialize test runner.
        
        Args:
            workspace: Path to workspace directory for output
        """
        self.workspace = workspace
        self.workspace.mkdir(parents=True, exist_ok=True)
    
    def run_pytest(
        self,
        tests: List[str],
        report_path: Path,
        timeout: int = 300
    ) -> Tuple[int, str, str]:
        """
        Run pytest with JSON report output.
        
        Args:
            tests: List of test file paths
            report_path: Path to save test_report.json
            timeout: Timeout in seconds
            
        Returns:
            (exit_code, stdout, stderr)
        """
        cmd = [
            'pytest',
            *tests,
            '--json-report',
            f'--json-report-file={report_path}',
            '--tb=short',
            '-v'
        ]
        
        return self._run_command(cmd, timeout)
    
    def run_mypy(
        self,
        strategy_path: str,
        timeout: int = 60
    ) -> Tuple[int, str, str]:
        """
        Run mypy type checking.
        
        Args:
            strategy_path: Path to strategy file
            timeout: Timeout in seconds
            
        Returns:
            (exit_code, stdout, stderr)
        """
        cmd = [
            'mypy',
            '--strict',
            '--no-error-summary',
            strategy_path
        ]
        
        return self._run_command(cmd, timeout)
    
    def run_flake8(
        self,
        strategy_path: str,
        timeout: int = 60
    ) -> Tuple[int, str, str]:
        """
        Run flake8 style checking.
        
        Args:
            strategy_path: Path to strategy file
            timeout: Timeout in seconds
            
        Returns:
            (exit_code, stdout, stderr)
        """
        cmd = [
            'flake8',
            '--max-line-length=100',
            '--extend-ignore=E203,W503',
            strategy_path
        ]
        
        return self._run_command(cmd, timeout)
    
    def run_bandit(
        self,
        strategy_path: str,
        timeout: int = 60
    ) -> Tuple[int, str, str]:
        """
        Run bandit security scanning.
        
        Args:
            strategy_path: Path to strategy file
            timeout: Timeout in seconds
            
        Returns:
            (exit_code, stdout, stderr)
        """
        cmd = [
            'bandit',
            '-r',
            strategy_path,
            '-f', 'json',
            '-o', str(self.workspace / 'bandit_report.json')
        ]
        
        return self._run_command(cmd, timeout)
    
    def _run_command(
        self,
        cmd: List[str],
        timeout: int
    ) -> Tuple[int, str, str]:
        """
        Run a command with timeout.
        
        Args:
            cmd: Command and arguments
            timeout: Timeout in seconds
            
        Returns:
            (exit_code, stdout, stderr)
        """
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=Path.cwd()
            )
            return (result.returncode, result.stdout, result.stderr)
        
        except subprocess.TimeoutExpired:
            return (-1, '', f'Command timed out after {timeout}s: {" ".join(cmd)}')
        
        except Exception as e:
            return (-1, '', f'Command failed: {e}')
    
    def parse_failures(
        self,
        pytest_exit: int,
        pytest_stdout: str,
        pytest_stderr: str,
        mypy_exit: int,
        mypy_stdout: str,
        flake8_exit: int,
        flake8_stdout: str,
        bandit_exit: int,
        bandit_stdout: str
    ) -> List[Dict]:
        """
        Parse test outputs and extract failure information.
        
        Returns:
            List of failure dicts with check, message, trace
        """
        failures = []
        
        # pytest failures
        if pytest_exit != 0:
            failures.append({
                'check': 'pytest',
                'message': 'Test failures detected',
                'trace': pytest_stdout[-1000:] if pytest_stdout else pytest_stderr[-1000:]
            })
        
        # mypy failures
        if mypy_exit != 0:
            failures.append({
                'check': 'mypy',
                'message': 'Type checking errors',
                'trace': mypy_stdout[-1000:] if mypy_stdout else mypy_stderr[-1000:]
            })
        
        # flake8 failures
        if flake8_exit != 0:
            failures.append({
                'check': 'flake8',
                'message': 'Style violations detected',
                'trace': flake8_stdout[-1000:] if flake8_stdout else flake8_stderr[-1000:]
            })
        
        # bandit failures (exit code 1 = issues found)
        if bandit_exit == 1:
            bandit_report_path = self.workspace / 'bandit_report.json'
            if bandit_report_path.exists():
                try:
                    with open(bandit_report_path) as f:
                        bandit_data = json.load(f)
                    
                    high_severity = [
                        r for r in bandit_data.get('results', [])
                        if r.get('issue_severity') == 'HIGH'
                    ]
                    
                    if high_severity:
                        failures.append({
                            'check': 'bandit',
                            'message': f'{len(high_severity)} high-severity security issues',
                            'trace': json.dumps(high_severity[:3], indent=2)
                        })
                except Exception:
                    pass
        
        return failures
