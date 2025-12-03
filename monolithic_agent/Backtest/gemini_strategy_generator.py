"""
Gemini Strategy Generator for SimBroker
========================================

Integrates Gemini AI to generate trading strategies that use the SimBroker API.

Features:
- Generate strategy code from natural language descriptions
- Ensures generated code uses stable SimBroker API
- Validates generated strategies
- Includes system prompt for proper API usage

Last updated: 2025-10-16
Version: 1.0.0
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import logging

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "Strategy"))

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-generativeai not installed. Run: pip install google-generativeai")

from dotenv import load_dotenv

# Import key rotation module
try:
    from key_rotation import get_key_manager, KeyRotationError
    KEY_ROTATION_AVAILABLE = True
except ImportError:
    KEY_ROTATION_AVAILABLE = False

# Import bot executor module
try:
    from bot_executor import BotExecutor, get_bot_executor
    BOT_EXECUTOR_AVAILABLE = True
except ImportError:
    try:
        # Fallback: try from current directory
        import sys
        current_dir = Path(__file__).parent
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))
        from bot_executor import BotExecutor, get_bot_executor
        BOT_EXECUTOR_AVAILABLE = True
    except ImportError:
        BOT_EXECUTOR_AVAILABLE = False

# Import indicator registry
try:
    from indicator_registry import format_registry_for_prompt
    INDICATOR_REGISTRY_AVAILABLE = True
except ImportError:
    try:
        # Fallback: try from current directory
        import sys
        current_dir = Path(__file__).parent
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))
        from indicator_registry import format_registry_for_prompt
        INDICATOR_REGISTRY_AVAILABLE = True
    except ImportError:
        INDICATOR_REGISTRY_AVAILABLE = False
        def format_registry_for_prompt():
            return ""  # Fallback empty registry

# Import bot error fixer
try:
    from bot_error_fixer import BotErrorFixer
    BOT_ERROR_FIXER_AVAILABLE = True
except ImportError:
    try:
        # Fallback: try from current directory
        import sys
        current_dir = Path(__file__).parent
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))
        from bot_error_fixer import BotErrorFixer
        BOT_ERROR_FIXER_AVAILABLE = True
    except ImportError:
        BOT_ERROR_FIXER_AVAILABLE = False


logger = logging.getLogger(__name__)


class GeminiStrategyGenerator:
    """
    Generates SimBroker-compatible trading strategies using Gemini AI
    
    Supports:
    - Single API key mode (GEMINI_API_KEY environment variable)
    - Multi-key rotation mode (ENABLE_KEY_ROTATION=true with keys.json)
    """
    
    def __init__(self, api_key: Optional[str] = None, use_key_rotation: Optional[bool] = None):
        """
        Initialize Gemini Strategy Generator
        
        Args:
            api_key: Gemini API key (if None, loads from environment)
            use_key_rotation: Enable key rotation (if None, auto-detect from env)
        """
        # Load environment variables
        load_dotenv()
        
        # Determine if we should use key rotation
        if use_key_rotation is None:
            use_key_rotation = os.getenv('ENABLE_KEY_ROTATION', 'false').lower() == 'true'
        
        self.use_key_rotation = use_key_rotation and KEY_ROTATION_AVAILABLE
        self.key_manager = None
        
        # Get API key
        if self.use_key_rotation:
            try:
                self.key_manager = get_key_manager()
                key_info = self.key_manager.select_key(
                    model_preference='gemini-2.5-flash',
                    tokens_needed=5000
                )
                if not key_info:
                    raise ValueError("No API keys available for selection")
                self.api_key = key_info['secret']
                self.selected_key_id = key_info['key_id']
                logger.info(f"Using key rotation (selected key: {self.selected_key_id})")
            except Exception as e:
                logger.warning(f"Key rotation failed, falling back to single key: {e}")
                self.use_key_rotation = False
                self.api_key = api_key or os.getenv('GEMINI_API_KEY')
                self.selected_key_id = 'default'
        else:
            self.api_key = api_key or os.getenv('GEMINI_API_KEY')
            self.selected_key_id = 'default'
        
        if not self.api_key:
            raise ValueError(
                "Gemini API key not found. Set GEMINI_API_KEY environment variable "
                "or enable key rotation with ENABLE_KEY_ROTATION=true and configure keys.json"
            )
        
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai package not installed. "
                "Run: pip install google-generativeai"
            )
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        # Use gemini-2.0-flash (fast, stable, suitable for code generation)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Framework selection (default to backtesting.py)
        self.use_backtesting_py = True
        
        # Load system prompt
        self.system_prompt = self._load_system_prompt(use_backtesting_py=self.use_backtesting_py)
        
        logger.info(
            f"GeminiStrategyGenerator initialized "
            f"(Framework: {'backtesting.py' if self.use_backtesting_py else 'SimBroker'}, "
            f"Key Rotation: {'enabled' if self.use_key_rotation else 'disabled'})"
        )
    
    def _load_system_prompt(self, use_backtesting_py: bool = True) -> str:
        """
        Load the system prompt for strategy generation
        
        Args:
            use_backtesting_py: If True, use backtesting.py framework (default)
                              If False, use legacy SimBroker framework
        """
        if use_backtesting_py:
            prompt_file = Path(__file__).parent / "SYSTEM_PROMPT_BACKTESTING_PY.md"
        else:
            prompt_file = Path(__file__).parent / "SYSTEM_PROMPT.md"
        
        if prompt_file.exists():
            with open(prompt_file, 'r', encoding='utf-8') as f:
                base_prompt = f.read()
        else:
            # Fallback minimal prompt
            base_prompt = """
# MUST NOT EDIT SimBroker

Generate trading strategy code using SimBroker API.

Required imports:
```python
# Add parent directory to path for imports
import sys
from pathlib import Path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig
from Backtest.canonical_schema import create_signal, OrderSide, OrderAction, OrderType
```

Strategy must:
1. Use only SimBroker stable API
2. Emit signals using create_signal()
3. Call broker.step_to() for each bar
4. Export results with compute_metrics()
5. NOT modify SimBroker internals
"""
        
        # Add indicator registry information if available
        if INDICATOR_REGISTRY_AVAILABLE:
            indicator_info = format_registry_for_prompt()
            if indicator_info:
                base_prompt = base_prompt + "\n\n" + indicator_info
        
        return base_prompt
    
    def generate_strategy(
        self,
        description: str,
        strategy_name: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a trading strategy from natural language description
        
        Args:
            description: Natural language description of the strategy
            strategy_name: Optional name for the strategy class
            parameters: Optional strategy parameters
        
        Returns:
            Generated Python code as string
            
        Raises:
            Exception: If generation fails after all retries
        """
        if not strategy_name:
            # Generate name from description
            strategy_name = "AIGeneratedStrategy"
        
        # Build the prompt
        prompt = f"""
{self.system_prompt}

---

Generate a complete, runnable Python trading strategy with the following requirements:

**Strategy Description:** {description}

**Strategy Name:** {strategy_name}

**Parameters:** {parameters or "Use sensible defaults"}

**Requirements:**
1. Import from sim_broker package (DO NOT modify SimBroker)
2. Create a strategy class with __init__ and on_bar methods
3. Use create_signal() to emit trading signals
4. Include a run_backtest() function
5. Export results and print metrics
6. Include complete code with no placeholders
7. Add docstrings and comments
8. Handle edge cases (no position, empty data, etc.)

**Code Structure:**
```python
# MUST NOT EDIT SimBroker
\"\"\"
Strategy: {strategy_name}
Description: {description}
\"\"\"

# Add parent directory to path for imports
import sys
from pathlib import Path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig
from Backtest.canonical_schema import create_signal, OrderSide, OrderAction, OrderType
from datetime import datetime
import pandas as pd

class {strategy_name}:
    def __init__(self, broker: SimBroker):
        # Initialize strategy
        pass
    
    def on_bar(self, timestamp: datetime, data: dict):
        # Strategy logic here
        pass

def run_backtest():
    # Complete backtest runner
    pass

if __name__ == "__main__":
    run_backtest()
```

Generate the complete, working code:
"""
        
        try:
            # Generate strategy
            logger.info(f"Generating strategy: {strategy_name} (key: {self.selected_key_id})")
            response = self.model.generate_content(prompt)
            
            # Extract code from response
            code = self._extract_code(response.text)
            
            logger.info("Strategy generated successfully")
            
            # Report success to key manager if using rotation
            if self.use_key_rotation and self.key_manager:
                # Update usage stats
                self.key_manager._update_usage(self.selected_key_id)
            
            return code
            
        except Exception as e:
            # Report error to key manager if using rotation
            if self.use_key_rotation and self.key_manager:
                error_type = 'api_error' if 'API' in str(e) else 'generation_error'
                self.key_manager.report_error(self.selected_key_id, error_type=error_type)
                logger.warning(f"Reported error for key {self.selected_key_id}")
                
                # Try to select another key
                try:
                    key_info = self.key_manager.select_key(
                        model_preference='gemini-2.5-flash',
                        tokens_needed=5000,
                        exclude_keys=[self.selected_key_id]
                    )
                    if key_info:
                        logger.info(f"Retrying with key {key_info['key_id']}")
                        self.api_key = key_info['secret']
                        self.selected_key_id = key_info['key_id']
                        genai.configure(api_key=self.api_key)
                        return self.generate_strategy(description, strategy_name, parameters)
                except Exception as retry_error:
                    logger.error(f"Failed to retry with alternate key: {retry_error}")
            
            logger.error(f"Failed to generate strategy: {e}")
            raise
    
    def _extract_code(self, response: str) -> str:
        """Extract Python code from Gemini response"""
        # Remove markdown code blocks
        if "```python" in response:
            parts = response.split("```python")
            if len(parts) > 1:
                code = parts[1].split("```")[0]
                return code.strip()
        
        if "```" in response:
            parts = response.split("```")
            if len(parts) >= 3:
                return parts[1].strip()
        
        # Return as-is if no code blocks
        return response.strip()
    
    def generate_and_save(
        self,
        description: str,
        output_path: str,
        strategy_name: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        execute_after_generation: bool = False,
        test_symbol: str = "AAPL",
        test_period_days: int = 365
    ) -> Tuple[Path, Optional['BotExecutionResult']]:
        """
        Generate strategy, save to file, and optionally execute it
        
        Args:
            description: Strategy description
            output_path: Path to save generated code
            strategy_name: Optional strategy name
            parameters: Optional parameters
            execute_after_generation: Run bot immediately after generation (default: False)
            test_symbol: Symbol for testing (default: AAPL)
            test_period_days: Days of historical data for testing (default: 365)
        
        Returns:
            Tuple of (Path to saved file, BotExecutionResult or None)
        """
        code = self.generate_strategy(description, strategy_name, parameters)
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        logger.info(f"Strategy saved to {output_file}")
        
        # Optionally execute the generated bot
        execution_result = None
        if execute_after_generation and BOT_EXECUTOR_AVAILABLE:
            try:
                logger.info("\nAuto-executing generated bot...")
                executor = get_bot_executor()
                execution_result = executor.execute_bot(
                    strategy_file=str(output_file),
                    strategy_name=strategy_name or output_file.stem,
                    description=description,
                    parameters=parameters,
                    test_symbol=test_symbol,
                    test_period_days=test_period_days
                )
                
                if execution_result.success:
                    logger.info(f"\n✓ Bot executed successfully!")
                    logger.info(f"  Return: {execution_result.return_pct:.2f}%" if execution_result.return_pct else "")
                    logger.info(f"  Trades: {execution_result.trades}" if execution_result.trades else "")
                else:
                    logger.warning(f"\n⚠ Bot execution completed with errors")
                    if execution_result.error:
                        logger.warning(f"  Error: {execution_result.error}")
            
            except Exception as e:
                logger.warning(f"Failed to auto-execute bot: {e}")
        
        return output_file, execution_result
    
    def validate_generated_code(self, code: str) -> Dict[str, Any]:
        """
        Validate that generated code uses SimBroker API correctly
        
        Args:
            code: Generated Python code
        
        Returns:
            Dictionary with validation results
        """
        issues = []
        warnings = []
        
        # Check for required imports
        if "from Backtest.sim_broker import SimBroker" not in code and "from sim_broker import SimBroker" not in code:
            issues.append("Missing import: from Backtest.sim_broker import SimBroker")
        
        if "from Backtest.canonical_schema import" not in code and "from canonical_schema import" not in code:
            issues.append("Missing canonical_schema imports")
        
        # Check for header comment
        if "# MUST NOT EDIT SimBroker" not in code:
            warnings.append("Missing header comment: # MUST NOT EDIT SimBroker")
        
        # Check for stable API usage
        if "broker.submit_signal" not in code:
            warnings.append("Strategy may not submit any signals")
        
        if "broker.step_to" not in code:
            warnings.append("Strategy may not advance simulation")
        
        if "broker.compute_metrics" not in code:
            warnings.append("Strategy may not compute metrics")
        
        # Check for forbidden patterns
        if "broker.order_manager" in code or "broker.execution_simulator" in code:
            issues.append("Code accesses SimBroker internals (forbidden)")
        
        if "SimBroker." in code and "SimBroker(" not in code:
            issues.append("Code may be modifying SimBroker class")
        
        # Check for signal creation
        if "create_signal" not in code and "Signal(" not in code:
            warnings.append("Strategy may not create signals properly")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'has_required_imports': len([i for i in issues if 'import' in i]) == 0,
            'uses_stable_api': "broker.submit_signal" in code and "broker.step_to" in code
        }
    
    def fix_bot_errors_iteratively(
        self,
        strategy_file: str,
        max_iterations: int = 3,
        test_symbol: str = "AAPL",
        test_period_days: int = 365
    ) -> Tuple[bool, Path, List[Dict[str, Any]]]:
        """
        Automatically detect and fix bot execution errors iteratively
        
        Args:
            strategy_file: Path to bot file to fix
            max_iterations: Maximum error fixing attempts (default: 3)
            test_symbol: Symbol for testing (default: AAPL)
            test_period_days: Days of historical data for testing (default: 365)
        
        Returns:
            Tuple of (success, final_file_path, fix_history)
        """
        if not BOT_ERROR_FIXER_AVAILABLE:
            logger.warning("BotErrorFixer not available. Cannot auto-fix errors.")
            return False, Path(strategy_file), []
        
        if not BOT_EXECUTOR_AVAILABLE:
            logger.warning("BotExecutor not available. Cannot test fixes.")
            return False, Path(strategy_file), []
        
        strategy_file = Path(strategy_file)
        fixer = BotErrorFixer(strategy_generator=self, max_iterations=max_iterations)
        executor = get_bot_executor()
        
        logger.info(f"\n{'='*70}")
        logger.info(f"STARTING ITERATIVE ERROR FIXING")
        logger.info(f"Bot: {strategy_file.name}")
        logger.info(f"Max iterations: {max_iterations}")
        logger.info(f"{'='*70}\n")
        
        success, final_code, fix_history = fixer.iterative_fix(
            bot_file=strategy_file,
            bot_executor=executor,
            max_attempts=max_iterations
        )
        
        if fix_history:
            report = fixer.get_fix_report()
            logger.info(f"\nFix Report:")
            logger.info(f"  Total attempts: {report['total_attempts']}")
            logger.info(f"  Successful fixes: {report['successful_fixes']}")
            logger.info(f"  Error types encountered: {', '.join(report['error_types'])}")
        
        return success, strategy_file, [f.__dict__ for f in fix_history] if fix_history else []
    
    def improve_strategy(
        self,
        existing_code: str,
        improvement_request: str
    ) -> str:
        """
        Improve an existing strategy based on feedback
        
        Args:
            existing_code: Current strategy code
            improvement_request: What to improve
        
        Returns:
            Improved strategy code
        """
        prompt = f"""
{self.system_prompt}

---

Improve the following trading strategy based on this request:

**Improvement Request:** {improvement_request}

**Current Strategy Code:**
```python
{existing_code}
```

**Instructions:**
1. Keep using SimBroker stable API (DO NOT modify SimBroker)
2. Make the requested improvements
3. Maintain all existing functionality unless explicitly changed
4. Return complete, working code
5. Add comments explaining changes

Generate the improved code:
"""
        
        try:
            response = self.model.generate_content(prompt)
            improved_code = self._extract_code(response.text)
            logger.info("Strategy improved successfully")
            return improved_code
        except Exception as e:
            logger.error(f"Failed to improve strategy: {e}")
            raise


def generate_strategy_from_description(description: str, output_file: str = None):
    """
    Convenience function to generate a strategy from description
    
    Args:
        description: Natural language description
        output_file: Optional path to save generated code
    
    Returns:
        Generated code as string
    """
    generator = GeminiStrategyGenerator()
    code = generator.generate_strategy(description)
    
    if output_file:
        Path(output_file).write_text(code, encoding='utf-8')
        print(f"Strategy saved to {output_file}")
    
    return code


if __name__ == "__main__":
    import argparse
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description='Generate trading strategies with Gemini AI')
    parser.add_argument('description', help='Natural language strategy description')
    parser.add_argument('-o', '--output', help='Output file path (relative to codes/ folder)', default='generated_strategy.py')
    parser.add_argument('-n', '--name', help='Strategy class name', default=None)
    parser.add_argument('--validate', action='store_true', help='Validate generated code')
    parser.add_argument('--execute', action='store_true', help='Execute bot immediately after generation')
    parser.add_argument('--symbol', default='AAPL', help='Test symbol for execution (default: AAPL)')
    parser.add_argument('--days', type=int, default=365, help='Test period in days (default: 365)')
    
    args = parser.parse_args()
    
    try:
        # Generate strategy
        print(f"Generating strategy: {args.description}")
        generator = GeminiStrategyGenerator()
        
        code = generator.generate_strategy(
            description=args.description,
            strategy_name=args.name
        )
        
        # Validate if requested
        if args.validate:
            print("\nValidating generated code...")
            validation = generator.validate_generated_code(code)
            
            print(f"Valid: {validation['valid']}")
            if validation['issues']:
                print("\nIssues:")
                for issue in validation['issues']:
                    print(f"  ❌ {issue}")
            if validation['warnings']:
                print("\nWarnings:")
                for warning in validation['warnings']:
                    print(f"  ⚠️  {warning}")
        
        # Save to codes folder
        codes_dir = Path(__file__).parent / "codes"
        codes_dir.mkdir(exist_ok=True)
        
        # Handle both absolute and relative paths
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = codes_dir / output_path
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(code, encoding='utf-8')
        
        print(f"\n✅ Strategy generated and saved to {output_path}")
        
        # Execute if requested
        if args.execute:
            if BOT_EXECUTOR_AVAILABLE:
                print(f"\n{'='*70}")
                print("Executing generated bot...")
                print(f"{'='*70}")
                
                executor = get_bot_executor()
                result = executor.execute_bot(
                    strategy_file=str(output_path),
                    strategy_name=args.name or output_path.stem,
                    description=args.description,
                    test_symbol=args.symbol,
                    test_period_days=args.days
                )
                
                print(f"\n{'='*70}")
                print("EXECUTION RESULTS")
                print(f"{'='*70}")
                print(f"Status: {'SUCCESS ✓' if result.success else 'FAILED ✗'}")
                print(f"Duration: {result.duration_seconds:.2f}s")
                
                if result.error:
                    print(f"Error: {result.error}")
                else:
                    if result.return_pct is not None:
                        print(f"Return: {result.return_pct:.2f}%")
                    if result.trades is not None:
                        print(f"Trades: {result.trades}")
                    if result.win_rate is not None:
                        print(f"Win Rate: {result.win_rate:.1%}")
                    if result.max_drawdown is not None:
                        print(f"Max Drawdown: {result.max_drawdown:.2f}%")
                    if result.sharpe_ratio is not None:
                        print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
                
                print(f"\nResults saved to: {result.results_file}")
            else:
                print("\n⚠️  BotExecutor not available. Skipping execution.")
        else:
            print("\nTo run the strategy:")
            print(f"  python {output_path}")
            print(f"\nOr to auto-execute after generation:")
            print(f"  python gemini_strategy_generator.py '{args.description}' --execute")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
