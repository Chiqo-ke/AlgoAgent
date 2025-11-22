"""
Planner Service

Converts natural language requests into structured TodoList JSON.
"""

import os
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from llm.router import get_request_router
from contracts.validate_contract import SchemaValidator
from planner_service.planner_prompt_single_file import PLANNER_SYSTEM_PROMPT_SINGLE_FILE


logger = logging.getLogger(__name__)

# Use single-file strategy prompt (DO NOT OVERRIDE!)
PLANNER_SYSTEM_PROMPT = PLANNER_SYSTEM_PROMPT_SINGLE_FILE

# OLD 4-STEP PROMPT - DEPRECATED - DO NOT USE
_OLD_PLANNER_SYSTEM_PROMPT = """You are an expert software project planner for a multi-agent AI development system.

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

📋 CRITICAL JSON SCHEMA REQUIREMENTS:

Root TodoList Object:
- todo_list_id: string (pattern: ^[a-zA-Z0-9_-]+$)
- workflow_name: string
- created_at: string (ISO 8601 format)
- created_by: string (optional, use "planner_service")
- metadata: object (optional, include user_request, planner_version)
- items: array of TodoItem (minimum 1 item)

TodoItem Object (ALL fields required unless marked optional):
- id: string (pattern: ^task_[a-zA-Z0-9_-]+$) ⚠️ MUST start with "task_"
- title: string (5-200 characters)
- description: string (minimum 10 characters)
- agent_role: string (one of: "architect", "coder", "tester", "debugger", "optimizer")
- priority: integer (1-10, where 1 is highest)
- dependencies: array of strings (optional, each matching ^task_[a-zA-Z0-9_-]+$)
- max_retries: integer (0-10, default 3)
- timeout_seconds: integer (optional, default 300)
- acceptance_criteria: AcceptanceCriteria object (required)
- input_artifacts: array of strings (optional)
- output_artifacts: array of strings (optional)
- failure_routing: object (optional but recommended, maps failure types to agent roles)
- fixture_path: string (optional)

AcceptanceCriteria Object:
- tests: array of TestCommand objects (minimum 1 test required) ⚠️ CRITICAL
- expected_artifacts: array of strings (optional)
- metrics: object (optional)
- validation_rules: array of objects (optional)

TestCommand Object:
- cmd: string (required, the shell command to execute)
- timeout_seconds: integer (optional, default 60)
- expected_exit_code: integer (optional, default 0)
- fixture: string (optional but recommended for deterministic tests)

⚠️ COMMON MISTAKES TO AVOID:
1. ❌ Task IDs like "step_1" or "1" → ✅ Use "task_data_loading" or "task_001"
2. ❌ acceptance_criteria as string → ✅ Must be object with "tests" array
3. ❌ tests array with strings → ✅ Each test must be object with "cmd" field
4. ❌ id as integer → ✅ id must be string
5. ❌ Missing priority field → ✅ Always include priority (1-10)
6. ❌ Missing max_retries → ✅ Always include max_retries (typically 3)
7. ❌ agent_role = "coder_agent" → ✅ Use "coder" (no suffix)

EXAMPLE VALID TASK:
{
  "id": "task_data_loading",
  "title": "Implement Data Loading",
  "description": "Create fetch_and_prepare_data function...",
  "agent_role": "coder",
  "priority": 1,
  "dependencies": [],
  "max_retries": 3,
  "timeout_seconds": 300,
  "acceptance_criteria": {
    "tests": [
      {
        "cmd": "pytest tests/test_adapter.py::test_data_loading",
        "timeout_seconds": 60,
        "fixture": "fixtures/sample_aapl.csv"
      }
    ]
  },
  "output_artifacts": [
    "backtesting_adapter.py",
    "fixtures/sample_aapl.csv"
  ],
  "failure_routing": {
    "implementation_bug": "coder",
    "spec_mismatch": "architect"
  }
}

📚 COMPLETE EXAMPLE - RSI Strategy (ALL 4 TASKS):
```json
{
  "todo_list_id": "workflow_example_123",
  "workflow_name": "RSI Strategy Implementation",
  "created_at": "2025-11-08T10:00:00Z",
  "created_by": "planner_service",
  "metadata": {
    "user_request": "Create RSI strategy",
    "planner_version": "1.0.0"
  },
  "items": [
    {
      "id": "task_data_loading",
      "title": "Data Loading Integration",
      "description": "Implement fetch_and_prepare_data to load OHLCV data",
      "agent_role": "coder",
      "priority": 1,
      "dependencies": [],
      "max_retries": 3,
      "acceptance_criteria": {
        "tests": [
          {
            "cmd": "pytest tests/test_adapter.py",
            "fixture": "fixtures/sample_aapl.csv"
          }
        ]
      },
      "output_artifacts": ["backtesting_adapter.py", "fixtures/sample_aapl.csv"],
      "failure_routing": {"implementation_bug": "coder"}
    },
    {
      "id": "task_indicators",
      "title": "Indicator Loading - RSI",
      "description": "Implement compute_rsi function",
      "agent_role": "architect",
      "priority": 2,
      "dependencies": ["task_data_loading"],
      "max_retries": 3,
      "acceptance_criteria": {
        "tests": [
          {
            "cmd": "pytest tests/test_indicators.py",
            "fixture": "fixtures/rsi_expected.json"
          }
        ]
      },
      "output_artifacts": ["indicators/rsi.py", "fixtures/rsi_expected.json"],
      "failure_routing": {"implementation_bug": "coder"}
    },
    {
      "id": "task_entry",
      "title": "Entry Conditions - RSI < 30",
      "description": "Implement should_enter for RSI oversold signal",
      "agent_role": "coder",
      "priority": 3,
      "dependencies": ["task_indicators"],
      "max_retries": 3,
      "acceptance_criteria": {
        "tests": [
          {
            "cmd": "pytest tests/test_entry.py",
            "fixture": "fixtures/entry_scenarios.json"
          }
        ]
      },
      "output_artifacts": ["Backtest/codes/ai_strategy_entry.py"],
      "failure_routing": {"implementation_bug": "coder"}
    },
    {
      "id": "task_exit",
      "title": "Exit Conditions - RSI > 70 + SL/TP",
      "description": "Implement should_exit for RSI overbought and stop loss/take profit",
      "agent_role": "coder",
      "priority": 4,
      "dependencies": ["task_entry"],
      "max_retries": 3,
      "acceptance_criteria": {
        "tests": [
          {
            "cmd": "pytest tests/test_exit.py",
            "fixture": "fixtures/exit_scenarios.json"
          }
        ]
      },
      "output_artifacts": ["Backtest/codes/ai_strategy_exit.py"],
      "failure_routing": {"implementation_bug": "coder"}
    }
  ]
}
```

⚠️ CRITICAL: Follow this EXACT structure. Copy the pattern above and adapt for the user's strategy.

Be thorough. Output only valid JSON matching the schema above EXACTLY.
"""  # End of OLD_PLANNER_SYSTEM_PROMPT - This should NOT be used


class PlannerService:
    """Planner service that creates todo lists from natural language."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        """
        Initialize planner service.
        
        Args:
            api_key: Deprecated - kept for backward compatibility (ignored)
            model_name: Model name preference for router
        """
        # Use RequestRouter for multi-key management
        self.router = get_request_router()
        self.model_name = model_name
        self.validator = SchemaValidator()
        self.version = "1.0.0"
        self.conversation_id = f"planner_{uuid.uuid4().hex[:8]}"
        
        # Check if router is enabled
        self.use_router = os.getenv('LLM_MULTI_KEY_ROUTER_ENABLED', 'false').lower() == 'true'
        
        if self.use_router:
            logger.info(f"Initialized PlannerService with RequestRouter (model: {model_name})")
        else:
            logger.warning("RequestRouter disabled - falling back to direct API calls")
            # Fallback: initialize direct API
            import google.generativeai as genai
            
            # Get API key from parameter or environment
            api_key = api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
            if not api_key:
                logger.error("No API key found for fallback mode")
                self.fallback_model = None
            else:
                genai.configure(api_key=api_key)
                self.fallback_model = genai.GenerativeModel(model_name)
    
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
                # Use RequestRouter or fallback
                if self.use_router:
                    response_data = self.router.send_chat(
                        conv_id=self.conversation_id,
                        prompt=prompt,
                        model_preference=self.model_name,
                        expected_completion_tokens=2048,
                        max_output_tokens=4096,
                        temperature=0.3,
                        system_prompt=PLANNER_SYSTEM_PROMPT
                    )
                    
                    if not response_data.get('success'):
                        raise ValueError(f"Router error: {response_data.get('error', 'Unknown error')}")
                    
                    response_text = response_data['content']
                else:
                    # Fallback to direct API
                    response = self.fallback_model.generate_content(prompt)
                    response_text = response.text
                
                todo_list = self._parse_response(response_text)
                
                # Validate against schema
                is_valid, errors = self.validator.validate_todo_list(todo_list)
                if not is_valid:
                    logger.warning(f"Attempt {attempt + 1}: Invalid schema - {errors}")
                    if attempt < max_attempts - 1:
                        # Provide detailed feedback with examples
                        error_feedback = self._format_schema_errors(errors)
                        prompt += f"\n\n❌ SCHEMA VALIDATION FAILED:\n{error_feedback}\n\n✅ FIX INSTRUCTIONS:\nReview the JSON SCHEMA REQUIREMENTS section above and ensure:\n1. All task IDs start with 'task_' (not 'step_' or numbers)\n2. acceptance_criteria is an OBJECT with 'tests' array, not a string\n3. Each test in 'tests' array is an OBJECT with 'cmd' field, not a string\n4. Include 'priority' and 'max_retries' fields in every task\n5. 'id' field must be string, not integer\n\nGenerate corrected JSON:"
                        continue
                    raise ValueError(f"Generated invalid todo list: {errors}")
                
                # Validate dependencies
                is_valid, dep_errors = self.validator.validate_dependencies(todo_list)
                if not is_valid:
                    logger.warning(f"Attempt {attempt + 1}: Invalid dependencies - {dep_errors}")
                    if attempt < max_attempts - 1:
                        prompt += f"\n\n❌ DEPENDENCY VALIDATION FAILED:\n{dep_errors}\n\nEnsure all dependency task IDs exist and match the '^task_[a-zA-Z0-9_-]+$' pattern.\nGenerate corrected JSON:"
                        continue
                    raise ValueError(f"Invalid dependencies: {dep_errors}")
                
                # Skip 4-step template validation for single-file strategy approach
                # Single comprehensive task doesn't need multi-step validation
                
                logger.info(f"Created valid plan with {len(todo_list['items'])} tasks (single-file strategy)")
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
        
        # Extract strategy details for description hints
        strategy_hints = self._generate_strategy_hints(user_request)
        
        prompt = f"""{PLANNER_SYSTEM_PROMPT}

USER REQUEST:
{user_request}
{context_str}

STRATEGY DETAILS for this request:
{strategy_hints}

Create a TodoList with ONE comprehensive task following the SINGLE-FILE STRATEGY TEMPLATE:
- todo_list_id: "{todo_list_id}"
- workflow_name: "{workflow_name}"
- created_at: "{timestamp}"
- created_by: "planner_service"
- metadata.planner_version: "{self.version}"
- metadata.user_request: "{user_request}"
- metadata.strategy_type: "single_file_complete"
- metadata.auto_fix_mode: true
- metadata.max_branch_depth: 2
- metadata.max_debug_attempts: 3

REQUIREMENTS:
✅ ONE comprehensive task (id: "task_complete_strategy")
✅ Include ALL components: data loading + indicators + entry + exit + backtest
✅ Comprehensive test suite: component tests + integration tests
✅ Explicit loop termination conditions (max_iterations)
✅ Complete file path with workflow_id in filename
✅ Include failure_routing for all error types

Output valid JSON only:"""
        
        return prompt
    
    def _generate_strategy_hints(self, user_request: str) -> str:
        """Generate strategy implementation hints based on user request."""
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
            hints.append(f"Indicators: {', '.join(indicators)}")
        else:
            hints.append("Indicators: Determine from strategy logic")
        
        # Extract entry conditions
        entry_hints = []
        if "buy" in user_request.lower():
            entry_hints.append("buy signals")
        if "<" in user_request or "below" in user_request.lower() or "under" in user_request.lower():
            entry_hints.append("threshold-based entry")
        if "crossover" in user_request.lower() or "cross" in user_request.lower():
            entry_hints.append("crossover signals")
        
        if entry_hints:
            hints.append(f"Entry logic: {', '.join(entry_hints)}")
        else:
            hints.append("Entry logic: Define based on strategy requirements")
        
        # Extract exit conditions
        exit_hints = []
        if "sell" in user_request.lower():
            exit_hints.append("sell signals")
        if "stop loss" in user_request.lower() or "sl" in user_request.lower():
            exit_hints.append("stop loss")
        if "take profit" in user_request.lower() or "tp" in user_request.lower():
            exit_hints.append("take profit")
        if ">" in user_request or "above" in user_request.lower():
            exit_hints.append("threshold-based exit")
        
        if exit_hints:
            hints.append(f"Exit logic: {', '.join(exit_hints)}")
        else:
            hints.append("Exit logic: Stop loss + take profit + signal-based")
        
        # Extract stop loss/take profit values
        import re
        stop_loss = re.search(r'(\d+)%?\s*stop\s*loss', user_request.lower())
        take_profit = re.search(r'(\d+)%?\s*(take\s*profit|target|tp)', user_request.lower())
        
        if stop_loss:
            hints.append(f"Stop loss: {stop_loss.group(1)}%")
        if take_profit:
            hints.append(f"Take profit: {take_profit.group(1)}%")
        
        return "\n".join(f"- {hint}" for hint in hints) if hints else "- Standard momentum/mean-reversion strategy"
    
    def _generate_fixture_hints(self, user_request: str) -> str:
        """DEPRECATED: Use _generate_strategy_hints instead."""
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
    
    def _format_schema_errors(self, errors: List[str]) -> str:
        """Format schema validation errors with helpful guidance."""
        if not errors:
            return "Unknown schema error"
        
        formatted = []
        for error in errors[:10]:  # Show first 10 errors
            # Parse error message
            if "is a required property" in error:
                field = error.split("'")[1] if "'" in error else "unknown"
                formatted.append(f"  • Missing required field: '{field}'")
            elif "does not match" in error and "task_" in error:
                formatted.append(f"  • {error}")
                formatted.append(f"    → FIX: Task IDs must start with 'task_' (e.g., 'task_data_loading')")
            elif "is not of type 'object'" in error and "acceptance_criteria" in error:
                formatted.append(f"  • {error}")
                formatted.append(f"    → FIX: acceptance_criteria must be object like: {{'tests': [...]}} not a string")
            elif "is not of type 'object'" in error and "tests" in error:
                formatted.append(f"  • {error}")
                formatted.append(f"    → FIX: Each test must be object like: {{'cmd': '...', 'fixture': '...'}} not a string")
            elif "is not of type 'string'" in error:
                formatted.append(f"  • {error}")
                formatted.append(f"    → FIX: Field must be string (in quotes), not number or other type")
            else:
                formatted.append(f"  • {error}")
        
        if len(errors) > 10:
            formatted.append(f"  • ...and {len(errors) - 10} more errors")
        
        return "\n".join(formatted)
    
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
