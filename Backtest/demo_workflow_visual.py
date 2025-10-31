"""
Visual Demo of Workflow Progress Tracking
Simulates the user experience with colored output
"""

import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from Backtest.workflow_tracker import create_strategy_generation_workflow


def print_colored(text, color_code):
    """Print with ANSI color codes"""
    print(f"\033[{color_code}m{text}\033[0m")


def demo_workflow_progress():
    """Demo the workflow with visual progress"""
    
    print("\n" + "="*80)
    print_colored("AI DEVELOPER AGENT - STRATEGY GENERATION", "1;36")  # Cyan bold
    print("="*80 + "\n")
    
    print("User Request: 'Create a moving average crossover strategy'\n")
    time.sleep(1)
    
    def show_progress(workflow):
        """Display progress updates"""
        summary = workflow.get_progress_summary()
        current_step = workflow.steps[workflow.current_step_index]
        
        # Progress bar
        bar_length = 50
        filled = int(bar_length * summary['overall_percentage'] / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        # Clear line and print
        print(f"\r{bar} {summary['overall_percentage']}%", end="", flush=True)
        
        # If step status changed, print on new line
        if current_step.progress_percentage in [0, 100]:
            print()  # New line
            
            # Status icon
            if current_step.status == "completed":
                icon = "✅"
                color = "32"  # Green
            elif current_step.status == "in_progress":
                icon = "🔄"
                color = "34"  # Blue
            elif current_step.status == "failed":
                icon = "❌"
                color = "31"  # Red
            elif current_step.status == "skipped":
                icon = "⏭️ "
                color = "90"  # Gray
            else:
                icon = "⏳"
                color = "37"  # White
            
            print_colored(
                f"{icon} {current_step.title}: {current_step.description}",
                color
            )
            
            if current_step.current_substep:
                print(f"   └─ {current_step.current_substep}")
    
    # Create workflow
    workflow = create_strategy_generation_workflow(on_update=show_progress)
    
    print_colored("\n🚀 Starting strategy generation...\n", "1;33")  # Yellow bold
    time.sleep(0.5)
    
    # Step 1: Parse Request
    workflow.start_step("parse_request")
    time.sleep(0.3)
    workflow.update_step_progress("parse_request", 30, "Extracting indicators")
    time.sleep(0.3)
    workflow.update_step_progress("parse_request", 70, "Validating parameters")
    time.sleep(0.3)
    workflow.complete_step("parse_request")
    time.sleep(0.2)
    
    # Step 2: Generate Code
    workflow.start_step("generate_code")
    time.sleep(0.4)
    workflow.update_step_progress("generate_code", 20, "Building imports")
    time.sleep(0.4)
    workflow.update_step_progress("generate_code", 50, "Creating Strategy class")
    time.sleep(0.4)
    workflow.update_step_progress("generate_code", 80, "Implementing next() method")
    time.sleep(0.4)
    workflow.complete_step("generate_code")
    time.sleep(0.2)
    
    # Step 3: Save File
    workflow.start_step("save_file")
    time.sleep(0.3)
    workflow.update_step_progress("save_file", 50, "Writing to disk")
    time.sleep(0.3)
    workflow.complete_step("save_file")
    time.sleep(0.2)
    
    # Step 4: Initial Test
    workflow.start_step("initial_test")
    time.sleep(0.5)
    workflow.update_step_progress("initial_test", 30, "Loading data")
    time.sleep(0.5)
    workflow.update_step_progress("initial_test", 60, "Running backtest")
    time.sleep(0.8)
    workflow.update_step_progress("initial_test", 90, "Collecting results")
    time.sleep(0.3)
    
    # Simulate error
    print()
    print_colored("\n⚠️  Test failed: ModuleNotFoundError: No module named 'pandas_ta'", "33")
    time.sleep(1)
    workflow.fail_step("initial_test", "ModuleNotFoundError: No module named 'pandas_ta'")
    time.sleep(0.5)
    
    # Step 5: Error Analysis
    workflow.start_step("error_analysis")
    time.sleep(0.4)
    workflow.update_step_progress("error_analysis", 40, "Parsing traceback")
    time.sleep(0.4)
    workflow.update_step_progress("error_analysis", 80, "Identifying fix")
    time.sleep(0.3)
    workflow.complete_step("error_analysis")
    time.sleep(0.2)
    
    # Step 6: Apply Fixes
    workflow.start_step("apply_fixes")
    time.sleep(0.3)
    workflow.update_step_progress("apply_fixes", 30, "Adding import: import pandas_ta")
    time.sleep(0.4)
    workflow.update_step_progress("apply_fixes", 70, "Updating code")
    time.sleep(0.3)
    workflow.complete_step("apply_fixes")
    time.sleep(0.2)
    
    # Step 7: Retest
    workflow.start_step("retest")
    time.sleep(0.5)
    workflow.update_step_progress("retest", 30, "Loading data")
    time.sleep(0.5)
    workflow.update_step_progress("retest", 60, "Running backtest")
    time.sleep(0.8)
    workflow.update_step_progress("retest", 90, "Collecting results")
    time.sleep(0.3)
    workflow.complete_step("retest")
    time.sleep(0.2)
    
    print()
    print_colored("\n✅ Backtest completed successfully!", "32")
    time.sleep(0.5)
    
    # Step 8: Final Validation
    workflow.start_step("final_validation")
    time.sleep(0.3)
    workflow.update_step_progress("final_validation", 50, "Validating outputs")
    time.sleep(0.3)
    workflow.update_step_progress("final_validation", 90, "Confirming success")
    time.sleep(0.3)
    workflow.complete_step("final_validation")
    
    workflow.complete_workflow()
    
    # Final summary
    print("\n" + "="*80)
    print_colored("🎉 STRATEGY GENERATION COMPLETE!", "1;32")  # Green bold
    print("="*80)
    
    summary = workflow.get_progress_summary()
    print(f"\n📊 Summary:")
    print(f"   Total Steps: {summary['total_steps']}")
    print(f"   Completed: {summary['completed_steps']}")
    print(f"   Failed: {summary['failed_steps']}")
    print(f"   Duration: {summary['duration_seconds']:.1f} seconds")
    print(f"   Overall Progress: {summary['overall_percentage']}%")
    
    print(f"\n💾 Strategy saved to: strategies/ma_crossover.py")
    print(f"📈 Backtest results: Return: 45.2%, Sharpe: 1.8")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    try:
        demo_workflow_progress()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
