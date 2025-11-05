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

Your job is to analyze user requests and create trading strategy workflows following the **4-STEP TEMPLATE**.

🎯 MANDATORY 4-STEP TEMPLATE (ALWAYS USE):

ALL trading strategy workflows MUST follow these exact 4 steps in order:

STEP 1: Data Loading Integration
- Agent: coder
- Purpose: Implement fetch_and_prepare_data(symbol, start, end) → DataFrame
- Output: DataFrame with ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
- Tests: DataFrame structure validation, column checks
- Artifacts: backtesting_adapter.py, fixtures/sample_<symbol>.csv
- Fixture: deterministic OHLCV data (30+ rows)

STEP 2: Indicator & Candle Pattern Loading
- Agent: architect (contract) → coder (implementation)
- Purpose: Implement technical indicators and pattern detectors
- Examples: compute_rsi(series, period), is_engulfing(candle_window)
- Tests: Value comparisons against known fixtures
- Artifacts: contracts/indicator_contract.json, indicators/*.py
- Fixtures: expected values for RSI, MACD, etc. (fixtures/rsi_expected.json)

STEP 3: Entry Conditions Setup
- Agent: coder
- Purpose: Implement should_enter(bar, indicators, position) → bool
- Logic: Define buy signal conditions
- Tests: Scenarios that should/shouldn't trigger entry
- Artifacts: Backtest/codes/ai_strategy_entry.py
- Fixture: entry test cases (fixtures/entry_scenarios.json)

STEP 4: Exit Conditions Setup
- Agent: coder
- Purpose: Implement should_exit(bar, indicators, position) → bool
- Logic: Define sell signals, stop loss, take profit
- Tests: Stop loss, take profit, signal exit scenarios
- Artifacts: Backtest/codes/ai_strategy_exit.py
- Fixture: exit test cases (fixtures/exit_scenarios.json)

AGENT ROLES:
- architect: Designs contracts, interfaces, test skeletons
- coder: Implements code following contracts
- tester: Runs tests in sandboxed environment
- debugger: Analyzes failures and suggests fixes

CRITICAL RULES:
1. ✅ ALWAYS create exactly 4 tasks following the template above
2. ✅ ALWAYS include "fixture" field in test commands for deterministic tests
3. ✅ ALWAYS include "failure_routing" for each task
4. ✅ ALWAYS set dependencies: Step2 → Step1, Step3 → Step2, Step4 → Step3
5. ✅ Priority order: 1, 2, 3, 4
6. ✅ Include fixture artifacts in output_artifacts
7. ✅ Use pytest with --json-report for all tests

FAILURE ROUTING (required for each task):
{
  "failure_routing": {
    "implementation_bug": "coder",
    "spec_mismatch": "architect",
    "timeout": "tester",
    "missing_dependency": "coder",
    "flaky_test": "tester"
  }
}

FIXTURE GENERATION (include for each step):
- Step 1: fixtures/sample_<symbol>.csv (30 rows of OHLCV data)
- Step 2: fixtures/rsi_expected.json, fixtures/pattern_cases.json
- Step 3: fixtures/entry_scenarios.json (at least 5 test cases)
- Step 4: fixtures/exit_scenarios.json (stop loss, take profit cases)

OUTPUT FORMAT - TodoList with exactly 4 items:
{
  "todo_list_id": "...",
  "workflow_name": "...",
  "created_at": "...",
  "metadata": {
    "user_request": "...",
    "planner_version": "...",
    "auto_fix_mode": true,
    "max_branch_depth": 2,
    "max_debug_attempts": 3
  },
  "items": [
    {Step 1: Data Loading},
    {Step 2: Indicators},
    {Step 3: Entry Conditions},
    {Step 4: Exit Conditions}
  ]
}

Each task must include:
- Deterministic test commands with "fixture" field
- failure_routing object
- Expected fixture artifacts in output_artifacts
- Clear acceptance criteria with pytest commands

Be thorough. Output only valid JSON.
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
                
                # Validate 4-step template
                is_valid, template_errors = self._validate_4step_template(todo_list)
                if not is_valid:
                    logger.warning(f"Attempt {attempt + 1}: Template violations - {template_errors}")
                    if attempt < max_attempts - 1:
                        prompt += f"\n\n4-STEP TEMPLATE ERRORS: {template_errors}\nYou MUST follow the 4-step template exactly. Please fix and try again."
                        continue
                    raise ValueError(f"Template validation failed: {template_errors}")
                
                logger.info(f"Created valid plan with {len(todo_list['items'])} tasks following 4-step template")
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
        
        # Extract strategy details for fixture hints
        fixture_hints = self._generate_fixture_hints(user_request)
        
        prompt = f"""{PLANNER_SYSTEM_PROMPT}

USER REQUEST:
{user_request}
{context_str}

FIXTURE HINTS for this strategy:
{fixture_hints}

Create a TodoList following the 4-STEP TEMPLATE with:
- todo_list_id: "{todo_list_id}"
- workflow_name: "{workflow_name}"
- created_at: "{timestamp}"
- created_by: "planner_service"
- metadata.planner_version: "{self.version}"
- metadata.user_request: "{user_request}"
- metadata.auto_fix_mode: true
- metadata.max_branch_depth: 2
- metadata.max_debug_attempts: 3

REQUIREMENTS:
✅ Exactly 4 tasks (Data Loading → Indicators → Entry → Exit)
✅ Each test command includes "fixture" field
✅ Each task includes "failure_routing"
✅ Fixtures included in output_artifacts
✅ Tests use pytest with --json-report

Output valid JSON only:"""
        
        return prompt
    
    def _generate_fixture_hints(self, user_request: str) -> str:
        """Generate fixture hints based on strategy description."""
        hints = []
        
        # Extract mentioned indicators
        indicators = []
        if "rsi" in user_request.lower():
            indicators.append("RSI (14-period default)")
        if "macd" in user_request.lower():
            indicators.append("MACD (12, 26, 9)")
        if "sma" in user_request.lower() or "moving average" in user_request.lower():
            indicators.append("SMA (50-day, 200-day)")
        if "bollinger" in user_request.lower():
            indicators.append("Bollinger Bands (20, 2)")
        if "ema" in user_request.lower():
            indicators.append("EMA (12-day, 26-day)")
        
        if indicators:
            hints.append(f"Indicators to implement: {', '.join(indicators)}")
            hints.append(f"Fixture files needed: {', '.join([f'fixtures/{ind.split()[0].lower()}_expected.json' for ind in indicators])}")
        
        # Extract entry conditions
        if "buy" in user_request.lower() or "enter" in user_request.lower():
            hints.append("Entry fixtures: Create scenarios for buy signals (at least 5 test cases)")
        
        # Extract exit conditions
        if "sell" in user_request.lower() or "exit" in user_request.lower():
            hints.append("Exit fixtures: Include stop loss, take profit, and signal exit cases")
        
        # Extract stop loss/take profit
        import re
        stop_loss = re.search(r'(\d+)%?\s*stop\s*loss', user_request.lower())
        take_profit = re.search(r'(\d+)%?\s*(take\s*profit|target)', user_request.lower())
        
        if stop_loss:
            hints.append(f"Stop loss: {stop_loss.group(1)}% - include in exit fixtures")
        if take_profit:
            hints.append(f"Take profit: {take_profit.group(1)}% - include in exit fixtures")
        
        # Data fixture
        hints.append("Data fixture: fixtures/sample_aapl.csv (30+ rows of OHLCV data)")
        
        return "\n".join(f"- {hint}" for hint in hints) if hints else "- Standard fixtures for all 4 steps"
    
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
    
    def _validate_4step_template(self, todo_list: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate that todo list follows the 4-step template.
        
        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []
        items = todo_list.get('items', [])
        
        # Check: Must have exactly 4 tasks
        if len(items) != 4:
            errors.append(f"Must have exactly 4 tasks, found {len(items)}. Follow: Data Loading → Indicators → Entry → Exit")
            return False, errors
        
        # Expected titles/keywords for each step
        expected_steps = [
            {"keywords": ["data", "loading", "fetch", "prepare"], "agent": "coder", "name": "Data Loading"},
            {"keywords": ["indicator", "pattern", "rsi", "macd", "sma"], "agent": ["architect", "coder"], "name": "Indicators"},
            {"keywords": ["entry", "enter", "buy"], "agent": "coder", "name": "Entry Conditions"},
            {"keywords": ["exit", "sell", "stop", "target"], "agent": "coder", "name": "Exit Conditions"}
        ]
        
        for i, (item, expected) in enumerate(zip(items, expected_steps), 1):
            title = item.get('title', '').lower()
            description = item.get('description', '').lower()
            
            # Check keywords
            if not any(kw in title or kw in description for kw in expected['keywords']):
                errors.append(f"Step {i} ({expected['name']}): Title/description should mention {', '.join(expected['keywords'][:3])}")
            
            # Check agent role
            agent_role = item.get('agent_role', '')
            expected_agents = expected['agent'] if isinstance(expected['agent'], list) else [expected['agent']]
            if agent_role not in expected_agents:
                errors.append(f"Step {i} ({expected['name']}): Expected agent {'/'.join(expected_agents)}, got {agent_role}")
            
            # Check priority matches step number
            if item.get('priority') != i:
                errors.append(f"Step {i} ({expected['name']}): Priority should be {i}, got {item.get('priority')}")
            
            # Check dependencies
            if i == 1:
                if item.get('dependencies', []):
                    errors.append(f"Step 1 should have no dependencies, found {item.get('dependencies')}")
            else:
                expected_dep = items[i-2]['id']  # Previous task
                if expected_dep not in item.get('dependencies', []):
                    errors.append(f"Step {i} should depend on Step {i-1} ('{expected_dep}')")
            
            # Check for tests
            tests = item.get('acceptance_criteria', {}).get('tests', [])
            if not tests:
                errors.append(f"Step {i} ({expected['name']}): Must have at least one test command")
            else:
                # Check for fixture field
                has_fixture = any('fixture' in test for test in tests)
                if not has_fixture:
                    errors.append(f"Step {i} ({expected['name']}): At least one test should have 'fixture' field for deterministic testing")
            
            # Check for failure_routing
            if 'failure_routing' not in item:
                errors.append(f"Step {i} ({expected['name']}): Must include 'failure_routing' object")
            
            # Check for expected artifacts
            output_artifacts = item.get('output_artifacts', [])
            if not output_artifacts:
                errors.append(f"Step {i} ({expected['name']}): Must specify output_artifacts")
            
            # Check for fixture in output_artifacts
            has_fixture_artifact = any('fixture' in art.lower() for art in output_artifacts)
            if not has_fixture_artifact:
                errors.append(f"Step {i} ({expected['name']}): Should include fixture file in output_artifacts")
        
        # Check metadata
        metadata = todo_list.get('metadata', {})
        if 'auto_fix_mode' not in metadata:
            errors.append("Metadata should include 'auto_fix_mode'")
        if 'max_branch_depth' not in metadata:
            errors.append("Metadata should include 'max_branch_depth'")
        if 'max_debug_attempts' not in metadata:
            errors.append("Metadata should include 'max_debug_attempts'")
        
        return len(errors) == 0, errors
    
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
