"""
Debugger Agent - Analyzes test failures and creates branch todos for automated fixes

Responsibilities:
- Subscribes to test failure events from Tester Agent
- Analyzes error tracebacks and classifies failure type
- Routes failures to appropriate agents via failure_routing config
- Creates branch todos with debug_instructions
- Enforces branch depth and debug attempt limits
"""

import json
import re
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import traceback

from contracts.event_types import EventType, Event
from contracts.message_bus import MessageBus, Channels


@dataclass
class FailureAnalysis:
    """Result of failure analysis"""
    failure_type: str  # Maps to branch_reason enum
    target_agent: str  # Where to route the fix
    confidence: float  # 0.0-1.0
    debug_summary: str
    traceback_snippet: str
    suggested_fixes: List[str]


class DebuggerAgent:
    """
    Debugger Agent that analyzes failures and creates targeted branch todos
    
    Workflow:
    1. Receives test failure event
    2. Analyzes traceback/error output
    3. Classifies failure type (implementation_bug, spec_mismatch, timeout, flaky_test)
    4. Looks up failure_routing from parent task config
    5. Creates branch todo with debug_instructions
    6. Publishes to orchestrator for execution
    """
    
    def __init__(self, message_bus: MessageBus):
        self.message_bus = message_bus
        self.agent_id = "debugger-001"
        self.running = False
        
    async def start(self):
        """Start listening for failure events"""
        self.running = True
        
        # Subscribe to test failure events (sync for InMemoryMessageBus)
        self.message_bus.subscribe(
            Channels.TEST_RESULTS,
            self._handle_test_result
        )
        
        print(f"[Debugger] Agent {self.agent_id} started")
        
    async def stop(self):
        """Stop the agent"""
        self.running = False
        # Disconnect if method exists (Redis backend)
        if hasattr(self.message_bus, 'disconnect'):
            if asyncio.iscoroutinefunction(self.message_bus.disconnect):
                await self.message_bus.disconnect()
            else:
                self.message_bus.disconnect()
        
    async def _handle_test_result(self, event: Dict[str, Any]):
        """Process test result events and handle failures"""
        if event.get("event_type") != EventType.TEST_FAILED.value:
            return
            
        payload = event.get("payload", {})
        test_result = payload.get("test_result", {})
        
        # Only process failures
        if test_result.get("status") == "passed":
            return
            
        print(f"[Debugger] Processing test failure for task {payload.get('task_id')}")
        
        # Analyze the failure
        analysis = await self._analyze_failure(test_result, payload)
        
        # Create branch todo
        branch_todo = await self._create_branch_todo(
            parent_task_id=payload.get("task_id"),
            parent_workflow_id=payload.get("workflow_id"),
            analysis=analysis,
            failure_routing=payload.get("failure_routing", {}),
            parent_context=payload
        )
        
        # Publish branch todo for orchestrator
        await self._publish_branch_todo(branch_todo)
        
    async def _analyze_failure(
        self, 
        test_result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> FailureAnalysis:
        """
        Analyze test failure and classify the issue
        
        Failure Classification Logic:
        - implementation_bug: Exception in user code (syntax, runtime errors)
        - spec_mismatch: Assertion failures (expected != actual)
        - timeout: Execution exceeds time limit
        - flaky_test: Passes sometimes, fails sometimes (requires multiple runs)
        - missing_dependency: Import errors, module not found
        """
        
        error_message = test_result.get("error_message", "")
        traceback_text = test_result.get("traceback", "")
        failed_tests = test_result.get("failed_tests", [])
        
        # Timeout detection with enhanced analysis
        if "timeout" in error_message.lower() or test_result.get("timed_out"):
            # Check if tester provided timeout analysis
            timeout_analysis = test_result.get("root_cause")
            fix_strategies = test_result.get("fix_strategy", [])
            last_line = test_result.get("last_line", "")
            
            if timeout_analysis:
                # Use enhanced timeout analysis from tester
                suggested_fixes = fix_strategies if fix_strategies else [
                    "Add execution time validation",
                    "Profile code to identify bottleneck",
                    "Add progress logging"
                ]
                
                debug_summary = (
                    f"Test timeout detected. Root causes: {', '.join(timeout_analysis)}. "
                    f"Last executing line: {last_line[:100]}"
                )
            else:
                # Fallback to generic timeout handling
                suggested_fixes = [
                    "Increase timeout_seconds in test config",
                    "Optimize slow operations",
                    "Check for infinite loops"
                ]
                debug_summary = "Test execution exceeded timeout limit"
            
            return FailureAnalysis(
                failure_type="timeout",
                target_agent="coder",  # Coder must fix slow code, not just increase timeout
                confidence=0.95,
                debug_summary=debug_summary,
                traceback_snippet=traceback_text[:500],
                suggested_fixes=suggested_fixes
            )
        
        # Missing dependency detection
        if any(x in traceback_text.lower() for x in ["modulenotfounderror", "importerror", "no module named"]):
            return FailureAnalysis(
                failure_type="missing_dependency",
                target_agent="coder",
                confidence=0.90,
                debug_summary="Missing module or import error",
                traceback_snippet=traceback_text[:500],
                suggested_fixes=[
                    "Install missing package",
                    "Fix import statement",
                    "Check requirements.txt"
                ]
            )
        
        # Spec mismatch detection (assertion failures)
        if any(x in traceback_text.lower() for x in ["assertionerror", "expected", "assert"]):
            return FailureAnalysis(
                failure_type="spec_mismatch",
                target_agent="architect",  # Spec may need clarification
                confidence=0.85,
                debug_summary="Assertion failure - behavior doesn't match expectations",
                traceback_snippet=traceback_text[:500],
                suggested_fixes=[
                    "Review contract specifications",
                    "Verify expected behavior in examples",
                    "Check if spec is ambiguous"
                ]
            )
        
        # Implementation bug (most common default)
        return FailureAnalysis(
            failure_type="implementation_bug",
            target_agent="coder",
            confidence=0.80,
            debug_summary=f"Runtime error: {error_message[:200]}",
            traceback_snippet=traceback_text[:500],
            suggested_fixes=[
                "Fix syntax or logic error",
                "Handle edge cases",
                "Add error handling"
            ]
        )
    
    async def _create_branch_todo(
        self,
        parent_task_id: str,
        parent_workflow_id: str,
        analysis: FailureAnalysis,
        failure_routing: Dict[str, str],
        parent_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a branch todo for fixing the failure
        
        Branch todos are temporary, focused tasks with:
        - parent_id: Link to original task
        - branch_reason: Classified failure type
        - debug_instructions: Full diagnostic info
        - is_temporary: True (will be cleaned up after success)
        - target agent from failure_routing config
        """
        
        # Get target agent from routing config
        target_agent = failure_routing.get(
            analysis.failure_type,
            analysis.target_agent  # Fallback to analyzed agent
        )
        
        # Generate branch task ID
        branch_id = f"{parent_task_id}_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Build debug instructions
        debug_instructions = f"""
=== FAILURE ANALYSIS ===
Failure Type: {analysis.failure_type}
Confidence: {analysis.confidence:.2f}
Summary: {analysis.debug_summary}

=== TRACEBACK ===
{analysis.traceback_snippet}

=== SUGGESTED FIXES ===
{chr(10).join(f'- {fix}' for fix in analysis.suggested_fixes)}

=== PARENT TASK CONTEXT ===
Task ID: {parent_task_id}
Workflow: {parent_workflow_id}
Original Goal: {parent_context.get('task_title', 'N/A')}
"""
        
        branch_todo = {
            "id": branch_id,
            "title": f"Fix {analysis.failure_type} in {parent_task_id}",
            "description": f"Debug and fix {analysis.failure_type} detected in test execution",
            "agent_role": target_agent,
            "priority": 1,  # High priority - blocking parent task
            "dependencies": [],  # No dependencies for branch todos
            "parent_id": parent_task_id,
            "branch_reason": analysis.failure_type,
            "debug_instructions": debug_instructions.strip(),
            "is_temporary": True,
            "max_debug_attempts": 3,
            "max_retries": 3,
            "timeout_seconds": 600,
            "acceptance_criteria": {
                "tests": parent_context.get("original_tests", []),
                "expected_artifacts": parent_context.get("expected_artifacts", [])
            },
            "fixture_path": parent_context.get("fixture_path"),  # Use same fixture
            "failure_routing": failure_routing  # Inherit routing config
        }
        
        return branch_todo
    
    async def _publish_branch_todo(self, branch_todo: Dict[str, Any]):
        """Publish branch todo to orchestrator for execution"""
        
        event = Event(
            event_id=f"evt_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            event_type=EventType.WORKFLOW_BRANCH_CREATED,
            timestamp=datetime.now().isoformat(),
            source_agent=self.agent_id,
            correlation_id=branch_todo["parent_id"],
            payload={
                "branch_todo": branch_todo,
                "parent_task_id": branch_todo["parent_id"],
                "branch_reason": branch_todo["branch_reason"]
            }
        )
        
        await self.message_bus.publish(
            Channels.WORKFLOW_EVENTS,
            event.__dict__
        )
        
        print(f"[Debugger] Published branch todo {branch_todo['id']} -> {branch_todo['agent_role']}")


# CLI for testing
async def main():
    """Test debugger agent with mock failure"""
    from contracts.message_bus import InMemoryMessageBus
    
    bus = InMemoryMessageBus()
    debugger = DebuggerAgent(bus)
    
    await debugger.start()
    
    # Simulate test failure event
    test_failure_event = {
        "event_id": "test_evt_001",
        "event_type": EventType.TEST_COMPLETED.value,
        "timestamp": datetime.now().isoformat(),
        "source_agent": "tester-001",
        "payload": {
            "task_id": "task_t2_indicators",
            "workflow_id": "wf_momentum_strategy",
            "task_title": "Implement RSI and MACD indicators",
            "test_result": {
                "status": "failed",
                "error_message": "AssertionError: Expected RSI value 45.2, got 42.8",
                "traceback": "Traceback (most recent call last):\n  File 'test_indicators.py', line 45, in test_rsi\n    assert rsi == 45.2\nAssertionError",
                "failed_tests": ["test_rsi"],
                "timed_out": False
            },
            "failure_routing": {
                "implementation_bug": "coder",
                "spec_mismatch": "architect",
                "timeout": "tester"
            },
            "original_tests": [{"cmd": "pytest test_indicators.py::test_rsi"}],
            "expected_artifacts": ["strategies/indicators.py"],
            "fixture_path": "fixtures/sample_ohlcv_data.csv"
        }
    }
    
    await bus.publish(Channels.TEST_RESULTS, test_failure_event)
    
    # Wait for processing
    await asyncio.sleep(1)
    
    await debugger.stop()
    print("[Debugger] Test complete")


if __name__ == "__main__":
    asyncio.run(main())
