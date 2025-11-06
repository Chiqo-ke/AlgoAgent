"""
Sandbox Runner - Execute tests in isolated Docker container.

Security features:
- Network isolation (--network=none)
- Resource limits (memory, CPU)
- Non-root user
- Timeout enforcement

Usage:
    runner = SandboxRunner()
    result = runner.run_tests(
        strategy_file='codes/strategy.py',
        test_file='tests/test_strategy.py',
        timeout=300
    )
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
import tempfile
import shutil


@dataclass
class SandboxResult:
    """Result from sandbox test execution."""
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    test_report: Optional[Dict]
    artifacts: Dict[str, str]  # artifact_name -> file_path
    duration_seconds: float
    error_message: Optional[str] = None


class SandboxRunner:
    """
    Runs tests in isolated Docker sandbox.
    
    Security:
        - Network disabled
        - Memory limited (1GB default)
        - CPU limited (0.5 cores default)
        - Non-root user
        - Timeout enforced
    """
    
    def __init__(
        self,
        image_name: str = 'algo-sandbox',
        memory_limit: str = '1g',
        cpu_limit: str = '0.5',
        workspace_root: Path = None
    ):
        """
        Initialize sandbox runner.
        
        Args:
            image_name: Docker image name
            memory_limit: Memory limit (e.g., '1g', '512m')
            cpu_limit: CPU limit (e.g., '0.5' = 50% of one core)
            workspace_root: Root directory to mount in container
        """
        self.image_name = image_name
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit
        self.workspace_root = workspace_root or Path.cwd()
    
    def build_image(self, dockerfile_path: Path = None) -> bool:
        """
        Build sandbox Docker image.
        
        Args:
            dockerfile_path: Path to Dockerfile (default: sandbox_runner/Dockerfile.sandbox)
            
        Returns:
            True if build succeeded
        """
        if dockerfile_path is None:
            dockerfile_path = self.workspace_root / 'sandbox_runner' / 'Dockerfile.sandbox'
        
        print(f"Building sandbox image: {self.image_name}...")
        
        try:
            cmd = [
                'docker', 'build',
                '-t', self.image_name,
                '-f', str(dockerfile_path),
                str(self.workspace_root)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 min build timeout
            )
            
            if result.returncode == 0:
                print(f"✅ Image built successfully: {self.image_name}")
                return True
            else:
                print(f"❌ Image build failed:")
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Image build error: {e}")
            return False
    
    def run_tests(
        self,
        strategy_file: str,
        test_file: str,
        fixtures_dir: str = 'fixtures',
        output_dir: str = 'artifacts',
        timeout: int = 300
    ) -> SandboxResult:
        """
        Run tests in sandbox.
        
        Args:
            strategy_file: Path to strategy file (relative to workspace)
            test_file: Path to test file (relative to workspace)
            fixtures_dir: Directory with test fixtures
            output_dir: Directory for test artifacts
            timeout: Test timeout in seconds
            
        Returns:
            SandboxResult with test outcomes and artifacts
        """
        import time
        start_time = time.time()
        
        # Prepare output directory
        output_path = self.workspace_root / output_dir
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Build pytest command
        test_report_path = f"/app/{output_dir}/test_report.json"
        
        pytest_cmd = [
            'python', '-m', 'pytest',
            f'/app/{test_file}',
            '--json-report',
            f'--json-report-file={test_report_path}',
            '--tb=short',
            '--maxfail=1',
            '--disable-warnings',
            '-v'
        ]
        
        # Docker run command with security restrictions
        docker_cmd = [
            'docker', 'run',
            '--rm',
            '--network=none',  # Disable network
            f'--memory={self.memory_limit}',
            f'--cpus={self.cpu_limit}',
            '-v', f'{self.workspace_root}:/app',
            '-w', '/app',
            self.image_name
        ] + pytest_cmd
        
        print(f"Running tests in sandbox (timeout={timeout}s)...")
        print(f"  Strategy: {strategy_file}")
        print(f"  Tests: {test_file}")
        
        try:
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            duration = time.time() - start_time
            
            # Load test report
            test_report = None
            test_report_file = output_path / 'test_report.json'
            if test_report_file.exists():
                with open(test_report_file) as f:
                    test_report = json.load(f)
            
            # Collect artifacts
            artifacts = {}
            for artifact_file in output_path.glob('*'):
                if artifact_file.is_file():
                    artifacts[artifact_file.name] = str(artifact_file)
            
            success = result.returncode == 0
            
            return SandboxResult(
                success=success,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                test_report=test_report,
                artifacts=artifacts,
                duration_seconds=duration
            )
            
        except subprocess.TimeoutExpired as e:
            duration = time.time() - start_time
            return SandboxResult(
                success=False,
                exit_code=-1,
                stdout=e.stdout.decode() if e.stdout else '',
                stderr=e.stderr.decode() if e.stderr else '',
                test_report=None,
                artifacts={},
                duration_seconds=duration,
                error_message=f"Test timeout after {timeout}s"
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return SandboxResult(
                success=False,
                exit_code=-1,
                stdout='',
                stderr=str(e),
                test_report=None,
                artifacts={},
                duration_seconds=duration,
                error_message=f"Sandbox error: {e}"
            )
    
    def run_static_checks(
        self,
        strategy_file: str,
        timeout: int = 60
    ) -> Dict[str, SandboxResult]:
        """
        Run static analysis checks (mypy, flake8, bandit).
        
        Args:
            strategy_file: Path to strategy file
            timeout: Check timeout in seconds
            
        Returns:
            Dict of tool_name -> SandboxResult
        """
        results = {}
        
        checks = {
            'mypy': ['python', '-m', 'mypy', f'/app/{strategy_file}', '--strict'],
            'flake8': ['python', '-m', 'flake8', f'/app/{strategy_file}', '--max-line-length=100'],
            'bandit': ['python', '-m', 'bandit', '-r', f'/app/{strategy_file}']
        }
        
        for tool, cmd in checks.items():
            docker_cmd = [
                'docker', 'run',
                '--rm',
                '--network=none',
                f'--memory={self.memory_limit}',
                '-v', f'{self.workspace_root}:/app',
                '-w', '/app',
                self.image_name
            ] + cmd
            
            try:
                result = subprocess.run(
                    docker_cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                results[tool] = SandboxResult(
                    success=(result.returncode == 0),
                    exit_code=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    test_report=None,
                    artifacts={},
                    duration_seconds=0
                )
                
            except Exception as e:
                results[tool] = SandboxResult(
                    success=False,
                    exit_code=-1,
                    stdout='',
                    stderr=str(e),
                    test_report=None,
                    artifacts={},
                    duration_seconds=0,
                    error_message=f"{tool} error: {e}"
                )
        
        return results


def main():
    """CLI for sandbox runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run tests in sandbox')
    parser.add_argument('--build', action='store_true', help='Build sandbox image')
    parser.add_argument('--strategy', type=str, help='Strategy file path')
    parser.add_argument('--tests', type=str, help='Test file path')
    parser.add_argument('--timeout', type=int, default=300, help='Timeout in seconds')
    
    args = parser.parse_args()
    
    runner = SandboxRunner()
    
    if args.build:
        success = runner.build_image()
        exit(0 if success else 1)
    
    if args.strategy and args.tests:
        result = runner.run_tests(
            strategy_file=args.strategy,
            test_file=args.tests,
            timeout=args.timeout
        )
        
        print("\n" + "="*60)
        print("SANDBOX TEST RESULTS")
        print("="*60)
        print(f"Success: {result.success}")
        print(f"Exit code: {result.exit_code}")
        print(f"Duration: {result.duration_seconds:.2f}s")
        print(f"Artifacts: {len(result.artifacts)}")
        
        if result.test_report:
            print(f"Tests: {result.test_report.get('summary', {})}")
        
        if not result.success:
            print("\nErrors:")
            print(result.stderr)
        
        exit(0 if result.success else 1)


if __name__ == '__main__':
    main()
