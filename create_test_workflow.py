"""
Create a test workflow directly in the orchestrator for API testing.
"""
import sys
import json
from pathlib import Path

# Add multi_agent to path
sys.path.insert(0, str(Path(__file__).parent / "multi_agent"))

from orchestrator_service.orchestrator import MinimalOrchestrator

def main():
    # Load test todo list
    with open("test_todo_list.json") as f:
        todo_list = json.load(f)
    
    # Create orchestrator
    orchestrator = MinimalOrchestrator(use_message_bus=False)
    
    # Load the todo list into orchestrator
    todo_list_id = todo_list['todo_list_id']
    orchestrator.todo_lists[todo_list_id] = todo_list
    
    # Create workflow
    workflow_id = orchestrator.create_workflow(todo_list_id)
    
    print(f"✅ Created test workflow: {workflow_id}")
    print(f"   TodoList ID: {todo_list['todo_list_id']}")
    print(f"   Tasks: {len(todo_list['items'])}")
    
    # Get status
    status = orchestrator.get_workflow_status(workflow_id)
    print(f"\n📊 Workflow Status:")
    print(json.dumps(status, indent=2))
    
    return workflow_id

if __name__ == "__main__":
    wf_id = main()
