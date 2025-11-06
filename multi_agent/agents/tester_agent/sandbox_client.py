"""Docker sandbox client for isolated test execution."""

import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Optional
import shutil

from .config import config
from .test_runner import TestRunner


class SandboxClient:
    """Execute tests in Docker sandbox with resource limits and network isolation."""
    
    def __init__(self):
        """Initialize sandbox client."""
        self.image_built = False
    
    def ensure_image_built(self) -> bool:
        """
        Build Docker image if not already built.
        
        Returns:
            True if image exists or was built successfully
        """
        # Check if image exists
        result = subprocess.run(
            ['docker', 'images', '-q', config.docker_image],
            capture_output=True,
            text=True
        )
        
        if result.stdout.strip():
            self.image_built = True
            return True
        
        # Build image
        print(f"Building Docker image: {config.docker_image}...")
        dockerfile_path = Path(config.dockerfile_path)
        
        if not dockerfile_path.exists():
            print(f"Error: Dockerfile not found at {dockerfile_path}")
            return False
        
        build_cmd = [
            'docker', 'build',
            '-t', config.docker_image,
            '-f', str(dockerfile_path),
            '.'
        ]
        
        try:
            result = subprocess.run(
                build_cmd,
                capture_output=True,
                text=True,
                timeout=config.docker_build_timeout
            )
            
            if result.returncode == 0:
                print(f"✓ Docker image built: {config.docker_image}")
                self.image_built = True
                return True
            else:
                print(f"✗ Docker build failed:\n{result.stderr}")
                return False
        
        except subprocess.TimeoutExpired:
            print(f"✗ Docker build timed out after {config.docker_build_timeout}s")
            return False
        except Exception as e:
            print(f"✗ Docker build error: {e}")
            return False
    
    def run_tests_in_sandbox(self, params: Dict) -> Dict:
        """
        Run tests inside Docker sandbox.
        
        Args:
            params: {
                "strategy": str,  # Path to strategy file
                "tests": List[str],  # Test file paths
                "fixtures": List[str],  # Fixture file paths
                "out_dir": str,  # Output directory
                "timeout": int,  # Timeout in seconds
                "seed": int  # RNG seed
            }
        
        Returns:
            {
                "exit_code": int,
                "duration_seconds": float,
                "artifacts": Dict[str, str],  # Artifact name -> path
                "failures": List[Dict]  # Failure details
            }
        """
        # Ensure image is built
        if not self.ensure_image_built():
            raise RuntimeError(f"Docker image {config.docker_image} not available")
        
        start_time = time.time()
        workspace = Path(params['out_dir'])
        workspace.mkdir(parents=True, exist_ok=True)
        
        # Build test script to run inside container
        test_script = self._build_test_script(params, workspace)
        script_path = workspace / 'run_tests.sh'
        
        with open(script_path, 'w') as f:
            f.write(test_script)
        
        # Make script executable
        script_path.chmod(0o755)
        
        # Run container
        docker_cmd = [
            'docker', 'run',
            '--rm' if config.remove_container else '',
            f'--network={config.network_mode}',
            f'--memory={config.memory_limit}',
            f'--cpus={config.cpu_limit}',
            '-v', f'{Path.cwd()}:/app',
            '-w', '/app',
            '-e', f'PYTHONPATH=/app',
            '-e', f'SEED={params.get("seed", 42)}',
            config.docker_image,
            'bash', str(script_path.relative_to(Path.cwd()))
        ]
        
        # Remove empty strings from command
        docker_cmd = [arg for arg in docker_cmd if arg]
        
        try:
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=params.get('timeout', config.default_timeout)
            )
            
            exit_code = result.returncode
            duration = time.time() - start_time
            
            # Parse outputs
            artifacts = self._collect_artifacts(workspace)
            failures = self._parse_failures(workspace, result) if exit_code != 0 else []
            
            return {
                'exit_code': exit_code,
                'duration_seconds': duration,
                'artifacts': artifacts,
                'failures': failures,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return {
                'exit_code': -1,
                'duration_seconds': duration,
                'artifacts': {},
                'failures': [{
                    'check': 'timeout',
                    'message': f'Test execution timed out after {params.get("timeout", config.default_timeout)}s'
                }]
            }
        
        except Exception as e:
            duration = time.time() - start_time
            return {
                'exit_code': -1,
                'duration_seconds': duration,
                'artifacts': {},
                'failures': [{
                    'check': 'docker',
                    'message': f'Docker execution failed: {str(e)}'
                }]
            }
    
    def _build_test_script(self, params: Dict, workspace: Path) -> str:
        """Build bash script to run all tests."""
        strategy = params['strategy']
        tests = ' '.join(params['tests'])
        report_path = workspace / 'test_report.json'
        
        script = f"""#!/bin/bash
set -e

echo "Starting test execution..."

# Run pytest
echo "Running pytest..."
pytest {tests} \\
    --json-report \\
    --json-report-file={report_path} \\
    --tb=short \\
    -v || exit 1

# Run mypy
echo "Running mypy..."
mypy --strict {strategy} || exit 2

# Run flake8
echo "Running flake8..."
flake8 --max-line-length=100 --extend-ignore=E203,W503 {strategy} || exit 3

# Run bandit (warnings only, don't fail on medium severity)
echo "Running bandit..."
bandit -r {strategy} -ll || true

echo "All checks passed!"
exit 0
"""
        return script
    
    def _collect_artifacts(self, workspace: Path) -> Dict[str, str]:
        """Collect artifact paths from workspace."""
        artifacts = {}
        
        for artifact_name in config.required_artifacts:
            artifact_path = workspace / artifact_name
            if artifact_path.exists():
                artifacts[artifact_name.replace('.', '_').replace('/', '_')] = str(artifact_path)
        
        return artifacts
    
    def _parse_failures(self, workspace: Path, result: subprocess.CompletedProcess) -> List[Dict]:
        """Parse failure information from outputs."""
        failures = []
        
        # Check exit code for specific failures
        if result.returncode == 1:
            failures.append({
                'check': 'pytest',
                'message': 'Test failures detected',
                'trace': result.stdout[-1000:] if result.stdout else result.stderr[-1000:]
            })
        elif result.returncode == 2:
            failures.append({
                'check': 'mypy',
                'message': 'Type checking errors',
                'trace': result.stdout[-1000:] if result.stdout else result.stderr[-1000:]
            })
        elif result.returncode == 3:
            failures.append({
                'check': 'flake8',
                'message': 'Style violations',
                'trace': result.stdout[-1000:] if result.stdout else result.stderr[-1000:]
            })
        else:
            failures.append({
                'check': 'unknown',
                'message': f'Exit code: {result.returncode}',
                'trace': result.stderr[-1000:] if result.stderr else result.stdout[-1000:]
            })
        
        return failures


# Public function for convenience
def run_tests_in_sandbox(params: Dict) -> Dict:
    """
    Run tests in Docker sandbox (convenience function).
    
    Args:
        params: Test execution parameters (see SandboxClient.run_tests_in_sandbox)
        
    Returns:
        Test execution results
    """
    client = SandboxClient()
    return client.run_tests_in_sandbox(params)
