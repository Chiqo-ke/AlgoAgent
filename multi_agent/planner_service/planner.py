"""
Planner Service

Converts natural language requests into structured TodoList JSON.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

import google.generativeai as genai

from contracts.validate_contract import SchemaValidator


logger = logging.getLogger(__name__)


PLANNER_SYSTEM_PROMPT = """You are an expert software project planner for a multi-agent AI development system.

Your job is to analyze user requests and break them down into independent, testable milestones.

Each milestone must:
1. Be a single, atomic task that can be completed independently
2. Have clear acceptance criteria (tests, artifacts, metrics)
3. Specify which agent role handles it (architect/coder/tester/debugger)
4. List dependencies on other tasks (if any)
5. Include estimated duration and retry limits

AGENT ROLES:
- architect: Designs contracts, interfaces, and test skeletons
- coder: Implements code following contracts
- tester: Runs tests in sandboxed environment
- debugger: Analyzes failures and suggests fixes
- optimizer: Improves performance and code quality

RULES:
- Prefer small tasks (< 5 minutes each)
- Architect tasks must come before coder tasks
- Coder tasks must come before tester tasks
- Always include at least one test command in acceptance_criteria
- Specify exact file paths for artifacts
- Add validation rules (lint, type check, security scan)

OUTPUT FORMAT:
Return valid JSON matching the TodoList schema. Include:
- todo_list_id (unique ID)
- workflow_name (descriptive name)
- created_at (ISO 8601 timestamp)
- metadata (user_request, planner_version)
- items (array of TodoItem objects)

Example task structure:
{
  "id": "task_architect_001",
  "title": "Design Strategy Contract",
  "description": "Create machine-readable contract...",
  "agent_role": "architect",
  "priority": 1,
  "dependencies": [],
  "expected_duration_seconds": 180,
  "max_retries": 3,
  "timeout_seconds": 300,
  "acceptance_criteria": {
    "tests": [
      {
        "cmd": "python -m contracts.validate_contract contract.json --type contract",
        "timeout_seconds": 30
      }
    ],
    "expected_artifacts": ["contract.json"],
    "validation_rules": [...]
  },
  "input_artifacts": [],
  "output_artifacts": ["contract.json"]
}

Be thorough but concise. Output only valid JSON.
"""


class PlannerService:
    """Planner service that creates todo lists from natural language."""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash-exp"):
        """
        Initialize planner service.
        
        Args:
            api_key: Google API key
            model_name: Gemini model name
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.validator = SchemaValidator()
        self.version = "1.0.0"
        
        logger.info(f"Initialized PlannerService with model {model_name}")
    
    def create_plan(
        self,
        user_request: str,
        repo_context: Optional[Dict[str, Any]] = None,
        workflow_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a todo list from a user request.
        
        Args:
            user_request: Natural language description of the work
            repo_context: Repository metadata
            workflow_name: Optional workflow name
            
        Returns:
            TodoList dictionary
            
        Raises:
            ValueError: If generated plan is invalid
        """
        logger.info(f"Creating plan for request: {user_request[:100]}...")
        
        # Generate workflow name if not provided
        if workflow_name is None:
            workflow_name = self._generate_workflow_name(user_request)
        
        # Build prompt
        prompt = self._build_prompt(user_request, repo_context, workflow_name)
        
        # Generate plan with retries
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                response = self.model.generate_content(prompt)
                todo_list = self._parse_response(response.text)
                
                # Validate against schema
                is_valid, errors = self.validator.validate_todo_list(todo_list)
                if not is_valid:
                    logger.warning(f"Attempt {attempt + 1}: Invalid schema - {errors}")
                    if attempt < max_attempts - 1:
                        prompt += f"\n\nPrevious attempt had errors: {errors}\nPlease fix and try again."
                        continue
                    raise ValueError(f"Generated invalid todo list: {errors}")
                
                # Validate dependencies
                is_valid, dep_errors = self.validator.validate_dependencies(todo_list)
                if not is_valid:
                    logger.warning(f"Attempt {attempt + 1}: Invalid dependencies - {dep_errors}")
                    if attempt < max_attempts - 1:
                        prompt += f"\n\nDependency errors: {dep_errors}\nPlease fix and try again."
                        continue
                    raise ValueError(f"Invalid dependencies: {dep_errors}")
                
                logger.info(f"Created valid plan with {len(todo_list['items'])} tasks")
                return todo_list
                
            except json.JSONDecodeError as e:
                logger.error(f"Attempt {attempt + 1}: JSON parse error - {e}")
                if attempt < max_attempts - 1:
                    prompt += "\n\nPrevious output was not valid JSON. Ensure you output ONLY valid JSON."
                    continue
                raise ValueError(f"Failed to parse JSON: {e}")
            
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}: Error - {e}")
                if attempt == max_attempts - 1:
                    raise
        
        raise ValueError(f"Failed to create valid plan after {max_attempts} attempts")
    
    def _build_prompt(
        self,
        user_request: str,
        repo_context: Optional[Dict[str, Any]],
        workflow_name: str
    ) -> str:
        """Build the prompt for the LLM."""
        timestamp = datetime.utcnow().isoformat() + "Z"
        todo_list_id = f"workflow_{uuid.uuid4().hex[:12]}"
        
        context_str = ""
        if repo_context:
            context_str = f"\n\nRepository Context:\n{json.dumps(repo_context, indent=2)}"
        
        prompt = f"""{PLANNER_SYSTEM_PROMPT}

USER REQUEST:
{user_request}
{context_str}

Create a TodoList with:
- todo_list_id: "{todo_list_id}"
- workflow_name: "{workflow_name}"
- created_at: "{timestamp}"
- created_by: "planner_service"
- metadata.planner_version: "{self.version}"
- metadata.user_request: "{user_request}"

Output valid JSON only:"""
        
        return prompt
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response and extract JSON."""
        # Clean response (remove markdown code blocks if present)
        text = response_text.strip()
        
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        
        if text.endswith("```"):
            text = text[:-3]
        
        text = text.strip()
        
        return json.loads(text)
    
    def _generate_workflow_name(self, user_request: str) -> str:
        """Generate a workflow name from the user request."""
        # Take first 50 chars and clean up
        name = user_request[:50].strip()
        # Remove special chars
        name = "".join(c if c.isalnum() or c.isspace() else " " for c in name)
        # Collapse whitespace
        name = " ".join(name.split())
        return name or "Workflow"
    
    def save_plan(self, todo_list: Dict[str, Any], output_dir: Path) -> Path:
        """
        Save todo list to file.
        
        Args:
            todo_list: TodoList dictionary
            output_dir: Directory to save to
            
        Returns:
            Path to saved file
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{todo_list['todo_list_id']}.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(todo_list, f, indent=2)
        
        logger.info(f"Saved plan to {filepath}")
        return filepath


def main():
    """CLI for planner service."""
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description='Create todo lists from natural language')
    parser.add_argument('request', type=str, help='Natural language request')
    parser.add_argument('--output', '-o', type=Path, default=Path('plans'),
                       help='Output directory for plan')
    parser.add_argument('--workflow-name', '-n', type=str, help='Workflow name')
    parser.add_argument('--api-key', type=str, help='Google API key (or use GOOGLE_API_KEY env var)')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get API key
    api_key = args.api_key or os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("Error: GOOGLE_API_KEY not set")
        return 1
    
    # Create planner
    planner = PlannerService(api_key=api_key)
    
    try:
        # Create plan
        todo_list = planner.create_plan(
            user_request=args.request,
            workflow_name=args.workflow_name
        )
        
        # Save plan
        filepath = planner.save_plan(todo_list, args.output)
        
        print(f"✅ Created plan: {filepath}")
        print(f"\nWorkflow: {todo_list['workflow_name']}")
        print(f"Tasks: {len(todo_list['items'])}")
        
        for item in todo_list['items']:
            print(f"  - {item['title']} ({item['agent_role']})")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error("Failed to create plan", exc_info=True)
        return 1


if __name__ == '__main__':
    exit(main())
