"""Tester Agent - Main implementation for Docker sandbox test execution."""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

from contracts.message_bus import get_message_bus, Channels
from contracts.event_types import EventType, TaskEvent

from .config import config
from .sandbox_client import run_tests_in_sandbox
from .validators import (
    validate_test_report_schema,
    validate_artifacts,
    scan_for_secrets
)


class TesterAgent:
    """
    Tester Agent executes tests in isolated Docker sandbox.
    
    Responsibilities:
    - Listen for tester tasks on message bus
    - Run tests in Docker sandbox with network isolation
    - Execute pytest, mypy, flake8, bandit
    - Run determinism checks
    - Validate test_report.json schema
    - Collect artifacts
    - Publish TEST_PASSED/TEST_FAILED events
    - Create branch todos on failure
    """
    
    def __init__(self, use_redis: bool = False):
        """
        Initialize Tester Agent.
        
        Args:
            use_redis: Whether to use Redis message bus (vs in-memory)
        """
        self.bus = get_message_bus(use_redis=use_redis)
        self.agent_id = "tester_agent"
        
        print(f"[{self.agent_id}] Initializing...")
        
        # Subscribe to agent requests
        self.bus.subscribe(Channels.AGENT_REQUESTS, self.handle_task)
        
        print(f"[{self.agent_id}] Ready. Listening for tester tasks...")
    
    def handle_task(self, event: TaskEvent):
        """
        Handle incoming task event.
        
        Args:
            event: Task dispatch event from orchestrator
        """
        # Extract task data
        task_data = event.data.get('task', event.data)
        agent_role = task_data.get('agent_role', '')
        
        # Only handle tester tasks
        if agent_role != 'tester':
            return
        
        print(f"\n[{self.agent_id}] Received task: {event.task_id}")
        
        corr_id = event.correlation_id
        wf_id = event.workflow_id
        task_id = event.task_id
        task = task_data.get('task', task_data)
        
        # Publish TEST_STARTED
        self.publish_test_started(corr_id, wf_id, task_id)
        
        # Execute tests
        try:
            self._execute_tests(corr_id, wf_id, task_id, task)
        except Exception as e:
            print(f"[{self.agent_id}] Fatal error: {e}")
            self.publish_test_failed(
                corr_id, wf_id, task_id,
                [{"check": "fatal", "message": str(e)}],
                Path(config.artifacts_base_dir) / corr_id / task_id
            )
    
    def _execute_tests(
        self,
        corr_id: str,
        wf_id: str,
        task_id: str,
        task: Dict
    ):
        """Execute tests and handle results."""
        # 1. Prepare workspace
        workspace = Path(config.artifacts_base_dir) / corr_id / task_id
        workspace.mkdir(parents=True, exist_ok=True)
        
        print(f"[{self.agent_id}] Workspace: {workspace}")
        
        # 2. Build sandbox parameters
        sandbox_params = {
            "strategy": task.get('artifact_path', ''),
            "tests": task.get('tests', []),
            "fixtures": task.get('fixtures', []),
            "out_dir": str(workspace),
            "timeout": task.get('timeout_seconds', config.default_timeout),
            "seed": task.get('rng_seed', 42)
        }
        
        print(f"[{self.agent_id}] Running tests in Docker sandbox...")
        print(f"  Strategy: {sandbox_params['strategy']}")
        print(f"  Tests: {sandbox_params['tests']}")
        print(f"  Timeout: {sandbox_params['timeout']}s")
        
        # 3. Run tests in sandbox
        try:
            result = run_tests_in_sandbox(sandbox_params)
        except Exception as e:
            print(f"[{self.agent_id}] ✗ Sandbox error: {e}")
            self.publish_test_failed(
                corr_id, wf_id, task_id,
                [{"check": "sandbox", "message": str(e)}],
                workspace
            )
            self.request_debug_branch(
                corr_id, wf_id, task_id, workspace,
                "sandbox_error", str(e)
            )
            return
        
        print(f"[{self.agent_id}] Test execution completed in {result['duration_seconds']:.1f}s")
        
        # 4. Check exit code
        if result['exit_code'] != 0:
            print(f"[{self.agent_id}] ✗ Tests failed (exit code: {result['exit_code']})")
            self.publish_test_failed(
                corr_id, wf_id, task_id,
                result.get('failures', []),
                workspace
            )
            self.request_debug_branch(
                corr_id, wf_id, task_id, workspace,
                "test_failures", result['failures']
            )
            return
        
        # 5. Validate test_report.json schema
        report_path = workspace / 'test_report.json'
        if not report_path.exists():
            print(f"[{self.agent_id}] ✗ test_report.json not found")
            self.publish_test_failed(
                corr_id, wf_id, task_id,
                [{"check": "report_missing", "message": "test_report.json not found"}],
                workspace
            )
            self.request_debug_branch(
                corr_id, wf_id, task_id, workspace,
                "artifact_missing", "test_report.json not created"
            )
            return
        
        try:
            validate_test_report_schema(report_path)
            print(f"[{self.agent_id}] ✓ test_report.json schema valid")
        except Exception as e:
            print(f"[{self.agent_id}] ✗ test_report.json schema invalid: {e}")
            self.publish_test_failed(
                corr_id, wf_id, task_id,
                [{"check": "report_schema", "message": str(e)}],
                workspace
            )
            self.request_debug_branch(
                corr_id, wf_id, task_id, workspace,
                "schema_invalid", str(e)
            )
            return
        
        # 6. Validate artifacts
        artifacts_ok, artifact_errors = validate_artifacts(workspace)
        if not artifacts_ok:
            print(f"[{self.agent_id}] ✗ Artifact validation failed:")
            for error in artifact_errors:
                print(f"    {error}")
            self.publish_test_failed(
                corr_id, wf_id, task_id,
                [{"check": "artifacts", "message": "; ".join(artifact_errors)}],
                workspace
            )
            self.request_debug_branch(
                corr_id, wf_id, task_id, workspace,
                "invalid_artifacts", artifact_errors
            )
            return
        
        print(f"[{self.agent_id}] ✓ All artifacts valid")
        
        # 7. Secret scanning
        if config.enable_secret_scanning:
            secrets_found = scan_for_secrets(workspace / 'events.log')
            if secrets_found:
                print(f"[{self.agent_id}] ✗ Secrets detected in logs!")
                self.publish_test_failed(
                    corr_id, wf_id, task_id,
                    [{
                        "check": "secrets",
                        "message": f"Found {len(secrets_found)} potential secrets in logs"
                    }],
                    workspace
                )
                self.request_debug_branch(
                    corr_id, wf_id, task_id, workspace,
                    "secrets_detected", secrets_found
                )
                return
            
            print(f"[{self.agent_id}] ✓ No secrets detected")
        
        # 8. Run determinism check (optional, requires second run)
        # TODO: Implement determinism check in tools/check_determinism.py
        # For now, skip determinism check
        
        # 9. SUCCESS - Extract metrics and publish TEST_PASSED
        print(f"[{self.agent_id}] ✓ All checks passed!")
        metrics = self.extract_metrics(report_path)
        self.publish_test_passed(
            corr_id, wf_id, task_id,
            metrics, result['artifacts'], result['duration_seconds']
        )
    
    def extract_metrics(self, report_path: Path) -> Dict:
        """
        Extract key metrics from test_report.json.
        
        Args:
            report_path: Path to test_report.json
            
        Returns:
            Dict with metrics (total_trades, net_pnl, win_rate, max_drawdown)
        """
        try:
            with open(report_path, 'r') as f:
                report = json.load(f)
            
            summary = report.get('summary', {})
            
            return {
                "total_trades": summary.get('total_trades', 0),
                "net_pnl": summary.get('net_pnl', 0),
                "win_rate": summary.get('win_rate', 0),
                "max_drawdown": summary.get('max_drawdown', 0)
            }
        except Exception as e:
            print(f"[{self.agent_id}] Warning: Could not extract metrics: {e}")
            return {
                "total_trades": 0,
                "net_pnl": 0,
                "win_rate": 0,
                "max_drawdown": 0
            }
    
    # Event publishers
    
    def publish_test_started(self, corr_id: str, wf_id: str, task_id: str):
        """Publish TEST_STARTED event."""
        evt = TaskEvent.create(
            event_type=EventType.TEST_STARTED,
            correlation_id=corr_id,
            workflow_id=wf_id,
            task_id=task_id,
            data={},
            source=self.agent_id
        )
        self.bus.publish(Channels.TEST_RESULTS, evt)
    
    def publish_test_passed(
        self,
        corr_id: str,
        wf_id: str,
        task_id: str,
        metrics: Dict,
        artifacts: Dict,
        duration: float
    ):
        """Publish TEST_PASSED event."""
        evt = TaskEvent.create(
            event_type=EventType.TEST_PASSED,
            correlation_id=corr_id,
            workflow_id=wf_id,
            task_id=task_id,
            data={
                "metrics": metrics,
                "artifacts": artifacts,
                "duration_seconds": duration
            },
            source=self.agent_id
        )
        self.bus.publish(Channels.TEST_RESULTS, evt)
        self.bus.publish(Channels.AGENT_RESULTS, evt)  # Also publish to orchestrator
        
        print(f"[{self.agent_id}] ✓ TEST_PASSED published")
        print(f"  Metrics: {metrics}")
    
    def publish_test_failed(
        self,
        corr_id: str,
        wf_id: str,
        task_id: str,
        failures: List[Dict],
        workspace: Path
    ):
        """Publish TEST_FAILED event."""
        evt = TaskEvent.create(
            event_type=EventType.TEST_FAILED,
            correlation_id=corr_id,
            workflow_id=wf_id,
            task_id=task_id,
            data={
                "failures": failures,
                "artifacts_dir": str(workspace)
            },
            source=self.agent_id
        )
        self.bus.publish(Channels.TEST_RESULTS, evt)
        self.bus.publish(Channels.AGENT_RESULTS, evt)  # Also publish to orchestrator
        
        print(f"[{self.agent_id}] ✗ TEST_FAILED published")
        print(f"  Failures: {len(failures)}")
    
    def request_debug_branch(
        self,
        corr_id: str,
        wf_id: str,
        task_id: str,
        workspace: Path,
        reason: str,
        details: any
    ):
        """
        Request Debugger to create branch todo.
        
        Args:
            corr_id: Correlation ID
            wf_id: Workflow ID
            task_id: Task ID
            workspace: Workspace path with artifacts
            reason: Failure classification (e.g., "test_failures")
            details: Detailed failure information
        """
        # Collect attachments (logs, fixtures)
        attachments = []
        for artifact in ['traceback.txt', 'events.log']:
            path = workspace / artifact
            if path.exists():
                attachments.append(str(path))
        
        # Build branch todo
        branch_todo = {
            "title": f"Debug: {task_id} failed ({reason})",
            "description": f"Auto-generated from tester. Reason: {reason}. Details: {details}",
            "attachments": attachments[:10],  # Limit to 10 files
            "target_agent": "debugger",
            "failure_classification": reason,
            "reproduce_command": f"docker run --rm -v $(pwd):/app algo-sandbox pytest tests/"
        }
        
        evt = TaskEvent.create(
            event_type=EventType.WORKFLOW_BRANCH_CREATED,
            correlation_id=corr_id,
            workflow_id=wf_id,
            task_id=task_id,
            data={"branch_todo": branch_todo, "origin_task": task_id},
            source=self.agent_id
        )
        
        self.bus.publish(Channels.DEBUGGER_REQUESTS, evt)
        print(f"[{self.agent_id}] → Branch todo requested for Debugger")
    
    def run(self):
        """Keep agent running (for standalone execution)."""
        print(f"[{self.agent_id}] Running... (Ctrl+C to stop)")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n[{self.agent_id}] Shutting down...")


def main():
    """Entry point for running Tester Agent standalone."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Tester Agent - Docker sandbox test execution")
    parser.add_argument('--redis', action='store_true', help='Use Redis message bus')
    args = parser.parse_args()
    
    agent = TesterAgent(use_redis=args.redis)
    agent.run()


if __name__ == '__main__':
    main()
