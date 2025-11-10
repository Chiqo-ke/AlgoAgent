"""
AI Developer Agent - Step Progress Tracker
===========================================

Tracks the progress of AI development workflow with detailed steps.
Provides real-time feedback on what's being done and what remains.

Version: 1.0.0
"""

from dataclasses import dataclass
from typing import List, Optional, Callable
from datetime import datetime
from enum import Enum


class StepStatus(Enum):
    """Status of a workflow step"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """A single step in the AI workflow"""
    id: str
    title: str
    description: str
    status: StepStatus = StepStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    substeps: List[str] = None
    current_substep: Optional[str] = None
    progress_percentage: int = 0
    
    def start(self):
        """Mark step as started"""
        self.status = StepStatus.IN_PROGRESS
        self.started_at = datetime.now()
        self.progress_percentage = 10
    
    def complete(self):
        """Mark step as completed"""
        self.status = StepStatus.COMPLETED
        self.completed_at = datetime.now()
        self.progress_percentage = 100
    
    def fail(self, error: str):
        """Mark step as failed"""
        self.status = StepStatus.FAILED
        self.completed_at = datetime.now()
        self.error_message = error
    
    def skip(self, reason: str):
        """Mark step as skipped"""
        self.status = StepStatus.SKIPPED
        self.completed_at = datetime.now()
        self.error_message = reason
    
    def update_progress(self, percentage: int, substep: Optional[str] = None):
        """Update progress within a step"""
        self.progress_percentage = min(100, max(0, percentage))
        if substep:
            self.current_substep = substep
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "substeps": self.substeps,
            "current_substep": self.current_substep,
            "progress_percentage": self.progress_percentage
        }


class WorkflowTracker:
    """
    Tracks the overall workflow progress
    """
    
    def __init__(self, workflow_name: str, on_update: Optional[Callable] = None):
        """
        Initialize workflow tracker
        
        Args:
            workflow_name: Name of the workflow
            on_update: Callback function called on each update (receives tracker state)
        """
        self.workflow_name = workflow_name
        self.steps: List[WorkflowStep] = []
        self.current_step_index = -1
        self.started_at = datetime.now()
        self.completed_at: Optional[datetime] = None
        self.on_update = on_update
    
    def add_step(
        self,
        step_id: str,
        title: str,
        description: str,
        substeps: Optional[List[str]] = None
    ) -> WorkflowStep:
        """Add a step to the workflow"""
        step = WorkflowStep(
            id=step_id,
            title=title,
            description=description,
            substeps=substeps or []
        )
        self.steps.append(step)
        return step
    
    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Get a step by ID"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None
    
    def start_step(self, step_id: str) -> WorkflowStep:
        """Start a specific step"""
        step = self.get_step(step_id)
        if step:
            step.start()
            self.current_step_index = self.steps.index(step)
            self._notify_update()
        return step
    
    def complete_step(self, step_id: str):
        """Complete a specific step"""
        step = self.get_step(step_id)
        if step:
            step.complete()
            self._notify_update()
    
    def fail_step(self, step_id: str, error: str):
        """Mark a step as failed"""
        step = self.get_step(step_id)
        if step:
            step.fail(error)
            self._notify_update()
    
    def skip_step(self, step_id: str, reason: str):
        """Skip a step"""
        step = self.get_step(step_id)
        if step:
            step.skip(reason)
            self._notify_update()
    
    def update_step_progress(
        self,
        step_id: str,
        percentage: int,
        substep: Optional[str] = None
    ):
        """Update progress within a step"""
        step = self.get_step(step_id)
        if step:
            step.update_progress(percentage, substep)
            self._notify_update()
    
    def complete_workflow(self):
        """Mark entire workflow as complete"""
        self.completed_at = datetime.now()
        self._notify_update()
    
    def get_progress_summary(self) -> dict:
        """Get overall progress summary"""
        total_steps = len(self.steps)
        completed = sum(1 for s in self.steps if s.status == StepStatus.COMPLETED)
        failed = sum(1 for s in self.steps if s.status == StepStatus.FAILED)
        in_progress = sum(1 for s in self.steps if s.status == StepStatus.IN_PROGRESS)
        
        overall_percentage = 0
        if total_steps > 0:
            # Calculate weighted progress
            for i, step in enumerate(self.steps):
                if step.status == StepStatus.COMPLETED:
                    overall_percentage += 100 / total_steps
                elif step.status == StepStatus.IN_PROGRESS:
                    overall_percentage += (step.progress_percentage / total_steps)
        
        return {
            "workflow_name": self.workflow_name,
            "total_steps": total_steps,
            "completed_steps": completed,
            "failed_steps": failed,
            "in_progress_steps": in_progress,
            "overall_percentage": int(overall_percentage),
            "current_step_index": self.current_step_index,
            "is_complete": self.completed_at is not None,
            "duration_seconds": (
                (self.completed_at or datetime.now()) - self.started_at
            ).total_seconds()
        }
    
    def to_dict(self) -> dict:
        """Convert entire workflow to dictionary"""
        return {
            "workflow_name": self.workflow_name,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "steps": [step.to_dict() for step in self.steps],
            "current_step_index": self.current_step_index,
            "progress_summary": self.get_progress_summary()
        }
    
    def _notify_update(self):
        """Notify callback of update"""
        if self.on_update:
            try:
                self.on_update(self)  # Pass the tracker object, not dict
            except Exception as e:
                print(f"Error in update callback: {e}")
    
    def print_progress(self):
        """Print progress to console"""
        summary = self.get_progress_summary()
        print(f"\n{'='*80}")
        print(f"Workflow: {self.workflow_name}")
        print(f"Progress: {summary['overall_percentage']}% complete")
        print(f"Steps: {summary['completed_steps']}/{summary['total_steps']} completed")
        if summary['failed_steps'] > 0:
            print(f"⚠️  {summary['failed_steps']} steps failed")
        print(f"{'='*80}\n")
        
        for i, step in enumerate(self.steps):
            status_icon = {
                StepStatus.PENDING: "⏳",
                StepStatus.IN_PROGRESS: "🔄",
                StepStatus.COMPLETED: "✅",
                StepStatus.FAILED: "❌",
                StepStatus.SKIPPED: "⏭️"
            }.get(step.status, "❓")
            
            print(f"{status_icon} Step {i+1}: {step.title}")
            
            if step.status == StepStatus.IN_PROGRESS:
                print(f"   Progress: {step.progress_percentage}%")
                if step.current_substep:
                    print(f"   Current: {step.current_substep}")
            
            if step.status == StepStatus.FAILED and step.error_message:
                print(f"   Error: {step.error_message}")
            
            if step.status == StepStatus.SKIPPED and step.error_message:
                print(f"   Reason: {step.error_message}")
        
        print()


def create_strategy_generation_workflow(on_update: Optional[Callable] = None) -> WorkflowTracker:
    """
    Create a workflow tracker for strategy generation process
    
    Args:
        on_update: Callback for progress updates
    
    Returns:
        Configured WorkflowTracker
    """
    tracker = WorkflowTracker("Strategy Generation & Testing", on_update)
    
    # Step 1: Parse user request
    tracker.add_step(
        "parse_request",
        "Understanding Your Request",
        "Analyzing your strategy description and extracting key requirements",
        substeps=[
            "Reading strategy description",
            "Identifying indicators and conditions",
            "Extracting risk parameters",
            "Validating completeness"
        ]
    )
    
    # Step 2: Generate strategy code
    tracker.add_step(
        "generate_code",
        "Generating Strategy Code",
        "Creating Python code using backtesting.py framework",
        substeps=[
            "Setting up imports and structure",
            "Implementing indicators",
            "Adding entry/exit logic",
            "Configuring risk management",
            "Adding documentation"
        ]
    )
    
    # Step 3: Save strategy file
    tracker.add_step(
        "save_file",
        "Saving Strategy File",
        "Writing code to disk with proper naming",
        substeps=[
            "Creating file name",
            "Writing code to file",
            "Setting file permissions"
        ]
    )
    
    # Step 4: Run initial test
    tracker.add_step(
        "initial_test",
        "Running Initial Test",
        "Testing the strategy in .venv environment",
        substeps=[
            "Loading Python environment",
            "Executing strategy code",
            "Capturing output",
            "Parsing results"
        ]
    )
    
    # Step 5: Error analysis (conditional)
    tracker.add_step(
        "error_analysis",
        "Analyzing Errors",
        "Examining any errors or issues found during testing",
        substeps=[
            "Parsing error messages",
            "Identifying error types",
            "Finding relevant code lines",
            "Determining fix strategy"
        ]
    )
    
    # Step 6: Apply fixes (conditional, can repeat)
    tracker.add_step(
        "apply_fixes",
        "Applying Fixes",
        "Correcting identified issues in the code",
        substeps=[
            "Generating fix patches",
            "Applying code changes",
            "Validating syntax",
            "Saving updated code"
        ]
    )
    
    # Step 7: Retest (conditional, can repeat)
    tracker.add_step(
        "retest",
        "Retesting Strategy",
        "Running tests again after applying fixes",
        substeps=[
            "Re-executing strategy",
            "Comparing with previous results",
            "Checking for new errors"
        ]
    )
    
    # Step 8: Final validation
    tracker.add_step(
        "final_validation",
        "Final Validation",
        "Confirming strategy is ready for use",
        substeps=[
            "Verifying all tests passed",
            "Extracting performance metrics",
            "Generating summary report"
        ]
    )
    
    return tracker


# Example usage
if __name__ == "__main__":
    def update_callback(state: dict):
        """Example callback to handle updates"""
        summary = state['progress_summary']
        print(f"Update: {summary['overall_percentage']}% - {summary['completed_steps']}/{summary['total_steps']} steps")
    
    # Create tracker
    tracker = create_strategy_generation_workflow(on_update=update_callback)
    
    # Simulate workflow
    import time
    
    # Step 1
    tracker.start_step("parse_request")
    tracker.update_step_progress("parse_request", 30, "Identifying indicators")
    time.sleep(0.5)
    tracker.update_step_progress("parse_request", 70, "Extracting risk parameters")
    time.sleep(0.5)
    tracker.complete_step("parse_request")
    
    # Step 2
    tracker.start_step("generate_code")
    for i, substep in enumerate(["imports", "indicators", "logic", "risk", "docs"]):
        tracker.update_step_progress("generate_code", (i + 1) * 20, f"Working on {substep}")
        time.sleep(0.3)
    tracker.complete_step("generate_code")
    
    # Step 3
    tracker.start_step("save_file")
    tracker.update_step_progress("save_file", 50, "Writing code to file")
    time.sleep(0.2)
    tracker.complete_step("save_file")
    
    # Step 4
    tracker.start_step("initial_test")
    tracker.update_step_progress("initial_test", 40, "Executing strategy code")
    time.sleep(0.5)
    tracker.update_step_progress("initial_test", 80, "Parsing results")
    time.sleep(0.3)
    # Simulate error
    tracker.fail_step("initial_test", "ModuleNotFoundError: No module named 'Backtest'")
    
    # Step 5
    tracker.start_step("error_analysis")
    tracker.update_step_progress("error_analysis", 60, "Determining fix strategy")
    time.sleep(0.3)
    tracker.complete_step("error_analysis")
    
    # Step 6
    tracker.start_step("apply_fixes")
    tracker.update_step_progress("apply_fixes", 70, "Applying code changes")
    time.sleep(0.3)
    tracker.complete_step("apply_fixes")
    
    # Step 7 - Retest
    tracker.start_step("retest")
    tracker.update_step_progress("retest", 50, "Re-executing strategy")
    time.sleep(0.5)
    tracker.complete_step("retest")
    
    # Step 8
    tracker.start_step("final_validation")
    tracker.update_step_progress("final_validation", 80, "Generating summary report")
    time.sleep(0.3)
    tracker.complete_step("final_validation")
    
    tracker.complete_workflow()
    
    # Print final state
    tracker.print_progress()
    
    # Print JSON
    import json
    print("\nJSON Output:")
    print(json.dumps(tracker.to_dict(), indent=2))
