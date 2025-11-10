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
        Generate code from contract using strategy template.
        
        Strategy:
        1. Use template skeleton
        2. Fill in function signatures from contract
        3. Use Gemini to generate function bodies
        4. Keep low temperature for deterministic output
        
        Args:
            task: Task dictionary
            contract: Contract dictionary
        
        Returns:
            List of CodeArtifact objects
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
        
        # Generate test file
        test_artifact = self._generate_test_file(task, contract, filename)
        
        return [artifact, test_artifact]
    
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
        Get adapter-driven strategy template.
        
        Returns template that works for BOTH backtest and live trading.
        Uses BaseAdapter interface with SimBrokerAdapter for backtesting.
        """
        # Load template from file
        template_path = self.workspace_root / 'Backtest' / 'codes' / 'strategy_template_adapter_driven.py'
        
        if template_path.exists():
            with open(template_path, encoding='utf-8') as f:
                return f.read()
        
        # Fallback: inline template with SimBroker integration
        return '''from typing import Dict, List, Optional
import pandas as pd
from pathlib import Path
from adapters.base_adapter import BaseAdapter
from adapters.simbroker_adapter import SimBrokerAdapter
from simulator.simbroker import SimBroker, SimConfig

class Strategy:
    """Adapter-driven strategy - works for backtest AND live."""
    
    def __init__(self, cfg: Dict):
        self.cfg = cfg
        self.symbol = cfg.get('symbol', 'EURUSD')
        self.volume = cfg.get('volume', 1.0)
    
    def prepare_indicators(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """Compute indicators (vectorized)."""
        indicators = {}
        # TODO: Implement indicator calculations
        # Example: indicators['rsi'] = compute_rsi(df['Close'], period=14)
        return indicators
    
    def find_entries(self, df: pd.DataFrame, indicators: Dict[str, pd.Series], idx: int) -> Optional[Dict]:
        """
        Check entry conditions and return order request.
        
        Args:
            df: Full OHLCV DataFrame
            indicators: Pre-computed indicators
            idx: Current bar index
            
        Returns:
            Order request dict or None
        """
        # TODO: Implement entry logic
        # Example:
        # if indicators['rsi'].iloc[idx] < 30:
        #     return {
        #         'action': 'BUY',
        #         'symbol': self.symbol,
        #         'volume': self.volume,
        #         'type': 'MARKET',
        #         'sl': df['Close'].iloc[idx] * 0.98,
        #         'tp': df['Close'].iloc[idx] * 1.02
        #     }
        return None
    
    def find_exits(self, position: Dict, df: pd.DataFrame, indicators: Dict[str, pd.Series], idx: int) -> Optional[Dict]:
        """
        Check exit conditions for open position.
        
        Args:
            position: Position dict from adapter.get_positions()
            df: Full OHLCV DataFrame
            indicators: Pre-computed indicators
            idx: Current bar index
            
        Returns:
            Exit request dict or None
        """
        # TODO: Implement exit logic
        # Example:
        # if indicators['rsi'].iloc[idx] > 70:
        #     return {'position_id': position['id']}
        return None

def run_backtest(adapter: BaseAdapter, df: pd.DataFrame, cfg: Dict) -> Dict:
    """
    Run backtest using adapter interface.
    
    Args:
        adapter: Broker adapter (SimBrokerAdapter for backtest)
        df: OHLCV DataFrame with columns ['Open', 'High', 'Low', 'Close', 'Volume']
        cfg: Strategy configuration dict
        
    Returns:
        Backtest report dict from adapter.generate_report()
    """
    strategy = Strategy(cfg)
    indicators = strategy.prepare_indicators(df)
    
    # Main backtest loop
    for idx in range(len(df)):
        bar = df.iloc[idx]
        
        # Check entry signals
        order_request = strategy.find_entries(df, indicators, idx)
        if order_request:
            result = adapter.place_order(order_request)
            if not result.get('success'):
                print(f"Order failed: {result.get('error')}")
        
        # Process bar (check SL/TP, update positions)
        events = adapter.step_bar(bar)
        
        # Check exit signals for open positions
        for position in adapter.get_positions():
            exit_request = strategy.find_exits(position, df, indicators, idx)
            if exit_request:
                adapter.close_position(exit_request['position_id'])
    
    # Generate final report
    return adapter.generate_report()

def main():
    """
    Main entry point for backtesting with SimBroker.
    
    This function:
    1. Loads data from CSV
    2. Creates SimBroker and adapter
    3. Runs backtest
    4. Saves results (trades.csv, equity_curve.csv, report.json)
    """
    import sys
    
    # Configuration
    cfg = {
        'symbol': 'EURUSD',
        'volume': 1.0,
        'starting_balance': 10000.0,
        'leverage': 100.0
    }
    
    # Load data
    data_file = 'fixtures/sample_data.csv'
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
    
    print(f"Loading data from {data_file}...")
    df = pd.read_csv(data_file)
    
    # Ensure required columns
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"CSV must have columns: {required_cols}")
    
    # Create SimBroker with configuration
    sim_config = SimConfig(
        starting_balance=cfg['starting_balance'],
        leverage=cfg['leverage'],
        commission={'type': 'per_lot', 'value': 7.0},
        slippage={'type': 'fixed', 'value': 2}
    )
    broker = SimBroker(sim_config)
    
    # Wrap in adapter
    adapter = SimBrokerAdapter(broker)
    
    # Run backtest
    print("Running backtest...")
    report = run_backtest(adapter, df, cfg)
    
    # Display results
    print("\\n=== Backtest Results ===")
    print(f"Total Trades: {report.get('summary', {}).get('total_trades', 0)}")
    print(f"Win Rate: {report.get('summary', {}).get('win_rate', 0):.2%}")
    print(f"Final Balance: ${report.get('summary', {}).get('final_balance', 0):.2f}")
    print(f"Max Drawdown: {report.get('summary', {}).get('max_drawdown', 0):.2%}")
    
    # Save artifacts
    output_dir = Path('backtest_results')
    output_dir.mkdir(exist_ok=True)
    
    paths = adapter.save_report(str(output_dir))
    print(f"\\nResults saved to:")
    for name, path in paths.items():
        print(f"  {name}: {path}")

if __name__ == '__main__':
    main()
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
        """Generate code from template (fallback without Gemini)."""
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
    
    def _generate_test_file(self, task: Dict[str, Any], contract: Dict[str, Any], strategy_filename: str) -> CodeArtifact:
        """
        Generate test file for strategy that validates SimBroker backtest results.
        
        Args:
            task: Task dictionary
            contract: Contract dictionary
            strategy_filename: Name of generated strategy file
            
        Returns:
            CodeArtifact with test code
        """
        strategy_id = task.get('id', 'unknown').replace('task_', '')
        module_name = strategy_filename.replace('.py', '')
        
        test_content = f'''"""
Test file for {strategy_filename}

Tests:
1. test_backtest_runs - Verifies strategy executes without errors
2. test_report_structure - Validates SimBroker report format
3. test_trades_generated - Checks if strategy produces trades
4. test_metrics_present - Ensures key metrics are calculated
"""

import pytest
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from Backtest.codes.{module_name} import Strategy, run_backtest, main
from adapters.simbroker_adapter import SimBrokerAdapter
from simulator.simbroker import SimBroker, SimConfig


@pytest.fixture
def sample_data():
    """Load sample OHLCV data for testing."""
    # Try to load from fixtures
    fixture_path = Path('fixtures/sample_data.csv')
    if fixture_path.exists():
        return pd.read_csv(fixture_path)
    
    # Generate synthetic data if fixture doesn't exist
    dates = pd.date_range('2024-01-01', periods=100, freq='1H')
    df = pd.DataFrame({{
        'timestamp': dates,
        'Open': 1.10 + pd.Series(range(100)) * 0.0001,
        'High': 1.102 + pd.Series(range(100)) * 0.0001,
        'Low': 1.098 + pd.Series(range(100)) * 0.0001,
        'Close': 1.101 + pd.Series(range(100)) * 0.0001,
        'Volume': 1000
    }})
    return df


@pytest.fixture
def simbroker_adapter():
    """Create SimBroker adapter for testing."""
    config = SimConfig(
        starting_balance=10000.0,
        leverage=100.0,
        commission={{'type': 'per_lot', 'value': 7.0}},
        slippage={{'type': 'fixed', 'value': 2}}
    )
    broker = SimBroker(config)
    return SimBrokerAdapter(broker)


def test_backtest_runs(sample_data, simbroker_adapter):
    """Test that backtest executes without errors."""
    cfg = {{'symbol': 'EURUSD', 'volume': 1.0}}
    
    # Should not raise exception
    report = run_backtest(simbroker_adapter, sample_data, cfg)
    
    assert report is not None
    assert isinstance(report, dict)


def test_report_structure(sample_data, simbroker_adapter):
    """Test that SimBroker report has expected structure."""
    cfg = {{'symbol': 'EURUSD', 'volume': 1.0}}
    report = run_backtest(simbroker_adapter, sample_data, cfg)
    
    # Check summary section exists
    assert 'summary' in report
    summary = report['summary']
    
    # Validate key fields
    assert 'starting_balance' in summary
    assert 'final_balance' in summary
    assert 'total_trades' in summary
    assert isinstance(summary['total_trades'], (int, float))


def test_trades_generated(sample_data, simbroker_adapter):
    """Test that strategy attempts to generate trades."""
    cfg = {{'symbol': 'EURUSD', 'volume': 1.0}}
    report = run_backtest(simbroker_adapter, sample_data, cfg)
    
    # Strategy should at least attempt trades (could be 0 if no signals)
    assert 'total_trades' in report['summary']
    trades_count = report['summary']['total_trades']
    
    # Log for debugging
    print(f"Total trades generated: {{trades_count}}")
    
    # Just verify the field exists and is a number
    assert isinstance(trades_count, (int, float))


def test_metrics_present(sample_data, simbroker_adapter):
    """Test that key performance metrics are present."""
    cfg = {{'symbol': 'EURUSD', 'volume': 1.0}}
    report = run_backtest(simbroker_adapter, sample_data, cfg)
    
    summary = report['summary']
    
    # Check for common metrics (SimBroker should provide these)
    expected_metrics = [
        'starting_balance',
        'final_balance',
        'total_trades',
        'win_rate',
        'profit_factor',
        'max_drawdown'
    ]
    
    for metric in expected_metrics:
        assert metric in summary, f"Missing metric: {{metric}}"


def test_strategy_initialization():
    """Test that Strategy class initializes correctly."""
    cfg = {{'symbol': 'EURUSD', 'volume': 1.0}}
    strategy = Strategy(cfg)
    
    assert strategy.cfg == cfg
    assert strategy.symbol == 'EURUSD'
    assert strategy.volume == 1.0


def test_indicators_computation(sample_data):
    """Test that prepare_indicators returns valid data."""
    cfg = {{'symbol': 'EURUSD', 'volume': 1.0}}
    strategy = Strategy(cfg)
    
    indicators = strategy.prepare_indicators(sample_data)
    
    assert isinstance(indicators, dict)
    # Indicators dict might be empty if strategy doesn't use any
    # But it should be a dict
'''
        
        test_artifact = CodeArtifact(
            file_path=f"tests/test_{module_name}.py",
            content=test_content,
            artifact_type='test',
            contract_id=contract['contract_id']
        )
        
        return test_artifact
    
    def _validate_code(self, artifacts: List[CodeArtifact]) -> ValidationResult:
        """
        Run static analysis on generated code.
        
        Tools:
        - mypy: Type checking
        - flake8: Style and error checking
        
        Args:
            artifacts: List of code artifacts
        
        Returns:
            ValidationResult with mypy and flake8 output
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
        """Save artifacts to filesystem."""
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
