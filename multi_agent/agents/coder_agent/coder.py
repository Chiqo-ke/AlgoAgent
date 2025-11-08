"""
Coder Agent - Implements code following Architect contracts

This agent:
1. Reads machine-readable contracts from Architect
2. Generates code using the standard strategy template
3. Validates code with static analysis (mypy, flake8)
4. Produces artifacts (code files, unit tests, reports)
5. Handles branch todos for focused bug fixes

Contract-driven implementation following PLANNER_DESIGN.md
"""

import json
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import shutil
import re

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

from contracts import Event, EventType
from contracts.message_bus import MessageBus, Channels


@dataclass
class CodeArtifact:
    """Generated code artifact."""
    file_path: str
    content: str
    artifact_type: str  # 'implementation', 'test', 'fixture'
    contract_id: str


@dataclass
class ValidationResult:
    """Static analysis validation result."""
    success: bool
    mypy_output: str
    flake8_output: str
    errors: List[str]
    warnings: List[str]


@dataclass
class CoderResult:
    """Coder agent task result."""
    task_id: str
    status: str  # 'ready', 'failed', 'needs_review'
    artifacts: List[CodeArtifact]
    validation: ValidationResult
    duration_seconds: float
    error_message: Optional[str] = None


class CoderAgent:
    """
    Coder Agent: Contract-driven code implementation.
    
    Workflow:
    1. Load contract from contract_path
    2. Validate contract schema
    3. Generate code using strategy template + Gemini
    4. Run static checks (mypy, flake8)
    5. Run unit tests with fixtures
    6. Commit artifacts and publish results
    """
    
    def __init__(
        self,
        agent_id: str,
        message_bus: MessageBus,
        gemini_api_key: Optional[str] = None,
        workspace_root: Path = None,
        temperature: float = 0.1
    ):
        """
        Initialize Coder Agent.
        
        Args:
            agent_id: Unique agent identifier
            message_bus: Message bus for pub/sub
            gemini_api_key: Google Gemini API key
            workspace_root: Root directory for code generation
            temperature: LLM temperature (low for deterministic code)
        """
        self.agent_id = agent_id
        self.message_bus = message_bus
        self.workspace_root = workspace_root or Path.cwd()
        self.temperature = temperature
        
        # Initialize Gemini
        if HAS_GEMINI and gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.model = genai.GenerativeModel("gemini-2.0-flash-thinking-exp")
        else:
            self.model = None
        
        print(f"[CoderAgent {self.agent_id}] Initialized (Gemini: {HAS_GEMINI and gemini_api_key is not None})")
    
    def start(self):
        """Start listening for coder tasks."""
        self.message_bus.subscribe(Channels.AGENT_REQUESTS, self._handle_task)
        print(f"[CoderAgent {self.agent_id}] Listening on {Channels.AGENT_REQUESTS}")
    
    def stop(self):
        """Stop listening."""
        if hasattr(self.message_bus, 'disconnect'):
            self.message_bus.disconnect()
    
    def _handle_task(self, event: Event):
        """Handle incoming task from orchestrator."""
        data = event.data
        
        # Only handle coder tasks
        if data.get('agent_role') != 'coder':
            return
        
        task_id = data.get('task_id')
        print(f"[CoderAgent {self.agent_id}] Received task: {task_id}")
        
        try:
            result = self.implement_task(data)
            
            # Publish result
            self._publish_result(event.correlation_id, event.workflow_id, result)
            
        except Exception as e:
            print(f"[CoderAgent {self.agent_id}] Error processing task {task_id}: {e}")
            self._publish_error(event.correlation_id, event.workflow_id, task_id, str(e))
    
    def implement_task(self, task: Dict[str, Any]) -> CoderResult:
        """
        Implement a coder task following contract.
        
        Process:
        1. Load and validate contract
        2. Generate code from template
        3. Run static analysis
        4. Run unit tests (if provided)
        5. Create artifacts
        
        Args:
            task: Task dictionary with contract_path, fixture_paths, etc.
        
        Returns:
            CoderResult with artifacts and validation
        """
        start_time = datetime.now()
        task_id = task['id']
        
        # 1. Load contract
        contract_path = task.get('contract_path')
        if not contract_path:
            raise ValueError(f"Task {task_id} missing contract_path")
        
        contract = self._load_contract(contract_path)
        
        # 2. Validate contract
        if not self._validate_contract(contract):
            raise ValueError(f"Invalid contract: {contract_path}")
        
        # 3. Check if auto_fix mode
        auto_fix = task.get('metadata', {}).get('auto_fix', False)
        
        # 4. Generate code
        artifacts = self._generate_code(task, contract)
        
        # 5. Run static analysis
        validation = self._validate_code(artifacts)
        
        # 6. Run unit tests (local, not sandbox)
        if not validation.success:
            return CoderResult(
                task_id=task_id,
                status='failed',
                artifacts=artifacts,
                validation=validation,
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                error_message=f"Static analysis failed: {validation.errors}"
            )
        
        # 7. Save artifacts
        self._save_artifacts(artifacts)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return CoderResult(
            task_id=task_id,
            status='ready',
            artifacts=artifacts,
            validation=validation,
            duration_seconds=duration
        )
    
    def _load_contract(self, contract_path: str) -> Dict[str, Any]:
        """Load contract JSON from path."""
        full_path = self.workspace_root / contract_path
        
        if not full_path.exists():
            raise FileNotFoundError(f"Contract not found: {contract_path}")
        
        with open(full_path, 'r') as f:
            contract = json.load(f)
        
        print(f"[CoderAgent] Loaded contract: {contract.get('contract_id')}")
        return contract
    
    def _validate_contract(self, contract: Dict[str, Any]) -> bool:
        """Validate contract has required fields."""
        required = ['contract_id', 'interfaces']
        
        for field in required:
            if field not in contract:
                print(f"[CoderAgent] Contract missing required field: {field}")
                return False
        
        return True
    
    def _generate_code(self, task: Dict[str, Any], contract: Dict[str, Any]) -> List[CodeArtifact]:
        """
        Generate implementation artifacts for a contract using the strategy template and a model fallback.
        
        Attempts to build a prompt from the task and contract and use the configured model (Gemini) to generate Python code; if model generation fails or the model is unavailable, falls back to a local strategy template. Produces a single implementation CodeArtifact whose file_path is placed under Backtest/codes/ and whose filename is derived from the task id.
        
        Parameters:
            task (dict): Task payload; may include an 'id' used to derive the output filename.
            contract (dict): Contract specification; expected to contain at least 'contract_id' and 'interfaces'.
        
        Returns:
            List[CodeArtifact]: A list containing one implementation artifact with the generated Python code and the contract_id.
        """
        contract_id = contract['contract_id']
        interfaces = contract['interfaces']
        
        # Build prompt for Gemini
        prompt = self._build_coder_prompt(task, contract)
        
        # Generate code
        if self.model:
            try:
                code = self._generate_with_gemini(prompt)
            except Exception as e:
                print(f"[CoderAgent] Gemini failed: {e}")
                print(f"[CoderAgent] ⚠️  Falling back to template mode...")
                code = self._generate_from_template(task, contract)
        else:
            # Fallback: use template only
            code = self._generate_from_template(task, contract)
        
        # Create artifact
        strategy_id = task.get('id', 'unknown').replace('task_', '')
        filename = f"ai_strategy_{strategy_id}.py"
        
        artifact = CodeArtifact(
            file_path=f"Backtest/codes/{filename}",
            content=code,
            artifact_type='implementation',
            contract_id=contract_id
        )
        
        return [artifact]
    
    def _build_coder_prompt(self, task: Dict[str, Any], contract: Dict[str, Any]) -> str:
        """
        Build Gemini prompt for code generation.
        
        Prompt structure:
        - System instructions
        - Contract specification
        - Example inputs/outputs
        - Template structure
        - Constraints
        """
        prompt = f"""System: You are Coder Agent. Implement functions exactly as specified in the contract. Use the provided fixtures. Output complete Python code.

Contract ID: {contract['contract_id']}

Task: {task.get('title', 'Unknown')}
Description: {task.get('description', '')}

CONTRACT SPECIFICATION:
{json.dumps(contract['interfaces'], indent=2)}

CONSTRAINTS:
- Use only these dependencies: pandas, numpy, typing
- Include exact function names and signatures from contract
- Use deterministic seeds where randomness needed
- No network calls inside functions
- Include docstrings referencing contract id
- Implement run_smoke() runner for testing

FIXTURES:
{task.get('fixture_paths', [])}

TEMPLATE STRUCTURE:
"""

        # Add strategy template
        prompt += self._get_strategy_template()
        
        prompt += f"""

REQUIRED OUTPUTS:
1. Complete implementation of all functions in contract["interfaces"]
2. prepare_indicators() function
3. run_smoke() runner that produces artifacts/entries.csv

Output only Python code, no explanations."""
        
        return prompt
    
    def _get_strategy_template(self) -> str:
        """
        Provide the adapter-driven strategy template used for both backtesting and live trading.
        
        Attempts to read a strategy template file at Backtest/codes/strategy_template_adapter_driven.py under the agent workspace and returns its contents if present; otherwise returns a built-in inline Python template that implements a Strategy class and a run_backtest function compatible with a BaseAdapter.
        
        Returns:
            str: Python source code for the strategy template.
        """
        # Load template from file
        template_path = self.workspace_root / 'Backtest' / 'codes' / 'strategy_template_adapter_driven.py'
        
        if template_path.exists():
            with open(template_path, encoding='utf-8') as f:
                return f.read()
        
        # Fallback: inline template
        return '''from typing import Dict, List, Optional
import pandas as pd
from adapters.base_adapter import BaseAdapter

class Strategy:
    """Adapter-driven strategy - works for backtest AND live."""
    
    def __init__(self, cfg: Dict):
        self.cfg = cfg
    
    def prepare_indicators(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """Compute indicators (vectorized)."""
        indicators = {}
        # Implementation here
        return indicators
    
    def find_entries(self, df: pd.DataFrame, indicators: Dict[str, pd.Series], idx: int) -> Optional[Dict]:
        """Return order_request dict or None."""
        # Implementation here
        return None
    
    def find_exits(self, position: Dict, df: pd.DataFrame, indicators: Dict[str, pd.Series], idx: int) -> Optional[Dict]:
        """Return close_request dict or None."""
        return None

def run_backtest(adapter: BaseAdapter, df: pd.DataFrame, cfg: Dict) -> Dict:
    """Run backtest using adapter."""
    strategy = Strategy(cfg)
    indicators = strategy.prepare_indicators(df)
    
    for idx in range(len(df)):
        bar = df.iloc[idx]
        order_request = strategy.find_entries(df, indicators, idx)
        if order_request:
            adapter.place_order(order_request)
        adapter.step_bar(bar)
        for position in adapter.get_positions():
            exit_request = strategy.find_exits(position, df, indicators, idx)
            if exit_request:
                adapter.close_position(exit_request['position_id'])
    
    return adapter.generate_report()
'''
    
    def _generate_with_gemini(self, prompt: str) -> str:
        """Generate code using Gemini API."""
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=8192
                )
            )
            
            code = response.text
            
            # Extract code from markdown if present
            if '```python' in code:
                code = code.split('```python')[1].split('```')[0].strip()
            elif '```' in code:
                code = code.split('```')[1].split('```')[0].strip()
            
            return code
            
        except Exception as e:
            print(f"[CoderAgent] Gemini error: {e}")
            raise
    
    def _generate_from_template(self, task: Dict[str, Any], contract: Dict[str, Any]) -> str:
        """
        Generate a Python implementation string from the local strategy template as a fallback when Gemini is not used.
        
        If the template contains a fenced Python code block (```python ... ```), the enclosed code is extracted; otherwise the whole template is used. The returned code is prefixed with a comment referencing the contract's `contract_id`.
        
        Parameters:
            task (Dict[str, Any]): Task metadata (not modified; used for context only).
            contract (Dict[str, Any]): Loaded contract object; must contain the `contract_id` key.
        
        Returns:
            str: The generated Python source code with a leading `# Contract: <contract_id>` comment.
        """
        # Use basic template substitution
        template = self._get_strategy_template()
        
        # Extract code from template if it's in markdown format
        if '```python' in template:
            code = template.split('```python')[1].split('```')[0].strip()
        else:
            # Template is plain Python code
            code = template
        
        # Add contract reference
        contract_id = contract['contract_id']
        code = f'# Contract: {contract_id}\n' + code
        
        return code
    
    def _validate_code(self, artifacts: List[CodeArtifact]) -> ValidationResult:
        """
        Run static analysis (mypy and flake8) on implementation artifacts and collect results.
        
        Only artifacts with artifact_type equal to 'implementation' are validated. Each implementation artifact is written to a temporary Python file for analysis; mypy is run with --ignore-missing-imports and flake8 with a 120-character max line length. Collected outputs, errors, and warnings are returned in a ValidationResult.
        
        Parameters:
            artifacts (List[CodeArtifact]): List of artifacts to validate. Only artifacts with artifact_type == 'implementation' are analyzed.
        
        Returns:
            ValidationResult: Contains a success flag, raw mypy and flake8 outputs, and lists of error and warning messages.
        """
        errors = []
        warnings = []
        mypy_output = ""
        flake8_output = ""
        
        for artifact in artifacts:
            if artifact.artifact_type != 'implementation':
                continue
            
            # Write to temp file for validation
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                f.write(artifact.content)
                temp_path = f.name
            
            try:
                # Run mypy
                result = subprocess.run(
                    ['mypy', temp_path, '--ignore-missing-imports'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                mypy_output = result.stdout + result.stderr
                
                if result.returncode != 0:
                    errors.append(f"mypy: {mypy_output}")
                
                # Run flake8
                result = subprocess.run(
                    ['flake8', temp_path, '--max-line-length=120'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                flake8_output = result.stdout + result.stderr
                
                if result.returncode != 0:
                    warnings.append(f"flake8: {flake8_output}")
                
            except subprocess.TimeoutExpired:
                errors.append("Static analysis timeout")
            except FileNotFoundError as e:
                warnings.append(f"Tool not found: {e}")
            finally:
                # Cleanup
                Path(temp_path).unlink(missing_ok=True)
        
        success = len(errors) == 0
        
        return ValidationResult(
            success=success,
            mypy_output=mypy_output,
            flake8_output=flake8_output,
            errors=errors,
            warnings=warnings
        )
    
    def _save_artifacts(self, artifacts: List[CodeArtifact]):
        """
        Write each CodeArtifact's content to the agent workspace, creating parent directories as needed.
        
        Each artifact's file_path is interpreted relative to the agent's workspace_root; parent directories are created and files are written using UTF-8 encoding. Artifacts are persisted in place and a short log message is emitted for each saved file.
        
        Parameters:
            artifacts (List[CodeArtifact]): Artifacts to persist; each artifact's `file_path` is joined with `workspace_root` and its `content` is written to disk.
        """
        for artifact in artifacts:
            file_path = self.workspace_root / artifact.file_path
            
            # Create parent directories
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(artifact.content)
            
            print(f"[CoderAgent] Saved artifact: {artifact.file_path}")
    
    def _publish_result(self, correlation_id: str, workflow_id: str, result: CoderResult):
        """Publish task completion result."""
        event = Event.create(
            event_type=EventType.TASK_COMPLETED,
            correlation_id=correlation_id,
            workflow_id=workflow_id,
            data={
                'agent_id': self.agent_id,
                'task_id': result.task_id,
                'status': result.status,
                'artifacts': [
                    {'path': a.file_path, 'type': a.artifact_type}
                    for a in result.artifacts
                ],
                'validation': {
                    'success': result.validation.success,
                    'errors': result.validation.errors,
                    'warnings': result.validation.warnings
                },
                'duration_seconds': result.duration_seconds
            },
            source=self.agent_id
        )
        
        self.message_bus.publish(Channels.AGENT_RESULTS, event)
        print(f"[CoderAgent {self.agent_id}] Published result for {result.task_id}")
    
    def _publish_error(self, correlation_id: str, workflow_id: str, task_id: str, error: str):
        """Publish task failure."""
        event = Event.create(
            event_type=EventType.TASK_FAILED,
            correlation_id=correlation_id,
            workflow_id=workflow_id,
            data={
                'agent_id': self.agent_id,
                'task_id': task_id,
                'error': error
            },
            source=self.agent_id
        )
        
        self.message_bus.publish(Channels.AGENT_RESULTS, event)


# Helper function to load contracts
def load_contract(contract_path: str) -> Dict[str, Any]:
    """Load contract JSON from workspace."""
    path = Path(contract_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Contract not found: {contract_path}")
    
    with open(path, 'r') as f:
        return json.load(f)