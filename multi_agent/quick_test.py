"""
Quick Test Script - Demonstrates Multi-Agent System

Tests the complete flow from validation → planning → orchestration
"""

import sys
from pathlib import Path
import json

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from contracts.validate_contract import validate_todo_file
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()


def test_validation():
    """Test 1: Schema Validation"""
    console.print("\n[bold cyan]Test 1: Schema Validation[/bold cyan]")
    
    sample_file = Path(__file__).parent / "contracts" / "sample_todo_list.json"
    
    is_valid, errors = validate_todo_file(sample_file)
    
    if is_valid:
        console.print("[green]✅ Sample todo list is valid[/green]")
        return True
    else:
        console.print("[red]❌ Validation failed:[/red]")
        for error in errors:
            console.print(f"  - {error}")
        return False


def test_planner():
    """Test 2: Planner Service (requires API key)"""
    console.print("\n[bold cyan]Test 2: Planner Service[/bold cyan]")
    
    import os
    api_key = os.getenv('GOOGLE_API_KEY')
    
    if not api_key:
        console.print("[yellow]⚠️  GOOGLE_API_KEY not set - skipping planner test[/yellow]")
        return True
    
    try:
        from planner_service import PlannerService
        
        planner = PlannerService(api_key=api_key)
        
        # Simple test request
        todo_list = planner.create_plan(
            user_request="Create a simple moving average strategy",
            workflow_name="Test SMA Strategy"
        )
        
        console.print(f"[green]✅ Generated plan: {todo_list['todo_list_id']}[/green]")
        console.print(f"   Tasks: {len(todo_list['items'])}")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Planner test failed: {e}[/red]")
        return False


def test_orchestrator():
    """Test 3: Orchestrator Execution"""
    console.print("\n[bold cyan]Test 3: Orchestrator Execution[/bold cyan]")
    
    try:
        from orchestrator_service.orchestrator import MinimalOrchestrator
        
        orchestrator = MinimalOrchestrator(use_message_bus=False)
        
        # Load sample todo list
        sample_file = Path(__file__).parent / "contracts" / "sample_todo_list.json"
        todo_list_id = orchestrator.load_todo_list(sample_file)
        
        console.print(f"[green]✅ Loaded todo list: {todo_list_id}[/green]")
        
        # Create workflow
        workflow_id = orchestrator.create_workflow(todo_list_id)
        console.print(f"[green]✅ Created workflow: {workflow_id}[/green]")
        
        # Execute (simulated)
        console.print("   Executing workflow...")
        result = orchestrator.execute_workflow(workflow_id)
        
        # Check results
        if result['status'] == 'completed':
            console.print(f"[green]✅ Workflow completed in {result['duration_seconds']:.2f}s[/green]")
            
            for task_id, task_info in result['tasks'].items():
                status_icon = "✅" if task_info['status'] == 'completed' else "❌"
                console.print(f"   {status_icon} {task_id}: {task_info['status']}")
            
            return True
        else:
            console.print(f"[red]❌ Workflow failed: {result.get('error')}[/red]")
            return False
        
    except Exception as e:
        console.print(f"[red]❌ Orchestrator test failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False


def test_message_bus():
    """Test 4: Message Bus"""
    console.print("\n[bold cyan]Test 4: Message Bus[/bold cyan]")
    
    try:
        from contracts.message_bus import get_message_bus, reset_message_bus, Channels
        from contracts.event_types import Event, EventType
        
        # Reset to ensure clean state
        reset_message_bus()
        
        # Get in-memory bus
        bus = get_message_bus(use_redis=False)
        
        # Test pub/sub
        received_events = []
        
        def callback(event):
            received_events.append(event)
        
        bus.subscribe(Channels.WORKFLOW_EVENTS, callback)
        
        # Publish test event
        event = Event.create(
            event_type=EventType.WORKFLOW_CREATED,
            correlation_id="test_corr_001",
            workflow_id="test_wf_001",
            data={"test": "data"},
            source="test"
        )
        
        bus.publish(Channels.WORKFLOW_EVENTS, event)
        
        # Check received
        if len(received_events) == 1 and received_events[0].event_id == event.event_id:
            console.print("[green]✅ Message bus working (pub/sub successful)[/green]")
            return True
        else:
            console.print("[red]❌ Message bus failed (event not received)[/red]")
            return False
        
    except Exception as e:
        console.print(f"[red]❌ Message bus test failed: {e}[/red]")
        return False


def main():
    """Run all tests."""
    console.print(Panel.fit(
        "[bold]Multi-Agent System - Quick Test Suite[/bold]",
        border_style="cyan"
    ))
    
    results = []
    
    # Run tests
    results.append(("Schema Validation", test_validation()))
    results.append(("Message Bus", test_message_bus()))
    results.append(("Orchestrator", test_orchestrator()))
    results.append(("Planner (optional)", test_planner()))
    
    # Summary
    console.print("\n" + "="*60)
    console.print("[bold]Test Results Summary[/bold]")
    console.print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[green]✅ PASS[/green]" if result else "[red]❌ FAIL[/red]"
        console.print(f"{status}  {name}")
    
    console.print("="*60)
    console.print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        console.print("[bold green]🎉 All tests passed![/bold green]")
        return 0
    else:
        console.print(f"[bold yellow]⚠️  {total - passed} test(s) failed[/bold yellow]")
        return 1


if __name__ == '__main__':
    exit(main())
