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
from typing import Dict, Any, Optional
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


logger = logging.getLogger(__name__)


class GeminiStrategyGenerator:
    """
    Generates SimBroker-compatible trading strategies using Gemini AI
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini Strategy Generator
        
        Args:
            api_key: Gemini API key (if None, loads from environment)
        """
        # Load environment variables
        load_dotenv()
        
        # Get API key
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "Gemini API key not found. Set GEMINI_API_KEY environment variable "
                "or pass api_key parameter."
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
        
        # Load system prompt
        self.system_prompt = self._load_system_prompt()
        
        logger.info("GeminiStrategyGenerator initialized")
    
    def _load_system_prompt(self) -> str:
        """Load the system prompt for strategy generation"""
        prompt_file = Path(__file__).parent / "SYSTEM_PROMPT.md"
        
        if prompt_file.exists():
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read()
        
        # Fallback minimal prompt
        return """
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
            logger.info(f"Generating strategy: {strategy_name}")
            response = self.model.generate_content(prompt)
            
            # Extract code from response
            code = self._extract_code(response.text)
            
            logger.info("Strategy generated successfully")
            return code
            
        except Exception as e:
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
        parameters: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Generate strategy and save to file
        
        Args:
            description: Strategy description
            output_path: Path to save generated code
            strategy_name: Optional strategy name
            parameters: Optional parameters
        
        Returns:
            Path to saved file
        """
        code = self.generate_strategy(description, strategy_name, parameters)
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        logger.info(f"Strategy saved to {output_file}")
        return output_file
    
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
        print("\nTo run the strategy:")
        print(f"  python {output_path}")
        print(f"\nOr from codes directory:")
        print(f"  cd codes")
        print(f"  python {output_path.name}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
