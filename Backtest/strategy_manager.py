"""
Strategy Manager - Automatic Strategy Code Generation and Backtest Runner
==========================================================================

Manages the lifecycle of trading strategies:
1. Scans codes/ folder for JSON strategy definitions
2. Checks if corresponding Python code exists
3. Auto-generates missing Python strategies using Gemini
4. Provides interface to run backtests on strategies

Usage:
    # Check strategy status
    python strategy_manager.py --status
    
    # Generate missing strategies
    python strategy_manager.py --generate
    
    # Run backtest on specific strategy
    python strategy_manager.py --run <strategy_name>
    
    # Generate and run all
    python strategy_manager.py --generate --run-all

Version: 1.0.0
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import importlib.util

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
parent_dir = Path(__file__).parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import with error handling
try:
    from gemini_strategy_generator import GeminiStrategyGenerator
    GEMINI_AVAILABLE = True
except ImportError:
    GeminiStrategyGenerator = None
    GEMINI_AVAILABLE = False
    logger.warning("Gemini generator not available")


class StrategyManager:
    """
    Manages trading strategy definitions and their Python implementations
    """
    
    def __init__(self, codes_dir: Optional[Path] = None):
        """
        Initialize Strategy Manager
        
        Args:
            codes_dir: Directory containing strategy JSON and Python files
        """
        self.codes_dir = codes_dir or Path(__file__).parent / "codes"
        self.codes_dir.mkdir(exist_ok=True)
        
        # Initialize Gemini generator (lazy load)
        self._generator = None
        
        logger.info(f"StrategyManager initialized with codes_dir: {self.codes_dir}")
    
    @property
    def generator(self):
        """Lazy-load Gemini generator"""
        if self._generator is None:
            if GEMINI_AVAILABLE and GeminiStrategyGenerator:
                self._generator = GeminiStrategyGenerator()
            else:
                raise ImportError("Gemini generator not available. Install: pip install google-generativeai")
        return self._generator
    
    def get_json_strategy_files(self) -> List[Path]:
        """Get all JSON strategy files in codes directory"""
        json_files = list(self.codes_dir.glob("*.json"))
        # Filter out any metadata files
        json_files = [f for f in json_files if not f.name.startswith('_')]
        return sorted(json_files)
    
    def get_python_strategy_files(self) -> List[Path]:
        """Get all Python strategy files in codes directory"""
        py_files = list(self.codes_dir.glob("*.py"))
        # Filter out __init__.py and test files
        py_files = [f for f in py_files if f.name not in ['__init__.py', 'README.py']]
        return sorted(py_files)
    
    def derive_python_filename(self, json_path: Path) -> str:
        """
        Derive the expected Python filename from a JSON strategy file
        
        Args:
            json_path: Path to JSON file
            
        Returns:
            Expected Python filename (e.g., "strategy_name.py")
        """
        # Remove .json extension and add .py
        return json_path.stem + ".py"
    
    def load_json_strategy(self, json_path: Path) -> Optional[Dict]:
        """
        Load and parse a JSON strategy file
        
        Args:
            json_path: Path to JSON file
            
        Returns:
            Parsed strategy dictionary or None if invalid
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                strategy = json.load(f)
            return strategy
        except Exception as e:
            logger.error(f"Failed to load {json_path.name}: {e}")
            return None
    
    def extract_strategy_description(self, strategy_json: Dict) -> str:
        """
        Extract a natural language description from strategy JSON
        for code generation
        
        Args:
            strategy_json: Parsed strategy dictionary
            
        Returns:
            Natural language description for Gemini
        """
        title = strategy_json.get('title', 'Untitled Strategy')
        description = strategy_json.get('description', '')
        
        # Build description from steps
        steps_desc = []
        for step in strategy_json.get('steps', []):
            step_title = step.get('title', '')
            trigger = step.get('trigger', '')
            action = step.get('action', {})
            action_type = action.get('type', '')
            
            if trigger:
                steps_desc.append(f"- {step_title}: {trigger} -> {action_type}")
        
        # Combine everything
        full_desc = f"{title}"
        if description:
            full_desc += f"\n{description}"
        if steps_desc:
            full_desc += f"\nSteps:\n" + "\n".join(steps_desc)
        
        return full_desc
    
    def check_strategy_status(self) -> List[Dict]:
        """
        Check status of all strategies in codes directory
        
        Returns:
            List of strategy status dictionaries with keys:
            - json_file: Path to JSON file
            - python_file: Expected Python file path
            - has_python: Boolean indicating if Python file exists
            - strategy_id: Strategy ID from JSON
            - title: Strategy title
        """
        json_files = self.get_json_strategy_files()
        status_list = []
        
        for json_file in json_files:
            strategy = self.load_json_strategy(json_file)
            if not strategy:
                continue
            
            python_filename = self.derive_python_filename(json_file)
            python_file = self.codes_dir / python_filename
            
            status = {
                'json_file': json_file,
                'python_file': python_file,
                'has_python': python_file.exists(),
                'strategy_id': strategy.get('strategy_id', 'unknown'),
                'title': strategy.get('title', 'Untitled'),
                'created_at': strategy.get('metadata', {}).get('created_at', 'unknown')
            }
            status_list.append(status)
        
        return status_list
    
    def generate_missing_strategies(self, force: bool = False) -> List[Dict]:
        """
        Generate Python code for strategies that don't have implementations
        
        Args:
            force: If True, regenerate even if Python file exists
            
        Returns:
            List of generation results with keys:
            - json_file: Source JSON file
            - python_file: Generated Python file
            - success: Boolean indicating if generation succeeded
            - error: Error message if failed
        """
        status_list = self.check_strategy_status()
        results = []
        
        for status in status_list:
            # Skip if Python file exists and not forcing
            if status['has_python'] and not force:
                logger.info(f"✓ {status['python_file'].name} already exists (skipping)")
                continue
            
            logger.info(f"{'Regenerating' if force else 'Generating'} {status['python_file'].name}...")
            
            # Load JSON strategy
            strategy = self.load_json_strategy(status['json_file'])
            if not strategy:
                results.append({
                    'json_file': status['json_file'],
                    'python_file': status['python_file'],
                    'success': False,
                    'error': 'Failed to load JSON'
                })
                continue
            
            # Extract description
            description = self.extract_strategy_description(strategy)
            
            # Extract strategy name for class naming
            strategy_title = strategy.get('title', 'Strategy')
            # Clean up title for class name
            strategy_name = ''.join(word.capitalize() for word in strategy_title.split()[:3])
            if not strategy_name:
                strategy_name = "GeneratedStrategy"
            
            # Generate code using Gemini
            try:
                code = self.generator.generate_strategy(
                    description=description,
                    strategy_name=strategy_name
                )
                
                # Save to Python file
                with open(status['python_file'], 'w', encoding='utf-8') as f:
                    f.write(code)
                
                logger.info(f"✓ Generated {status['python_file'].name}")
                results.append({
                    'json_file': status['json_file'],
                    'python_file': status['python_file'],
                    'success': True,
                    'error': None
                })
            except Exception as e:
                logger.error(f"✗ Failed to generate {status['python_file'].name}: {e}")
                results.append({
                    'json_file': status['json_file'],
                    'python_file': status['python_file'],
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    def load_strategy_class(self, python_file: Path):
        """
        Dynamically load a strategy class from a Python file
        
        Args:
            python_file: Path to Python strategy file
            
        Returns:
            Strategy class or None if failed
        """
        try:
            # Load module
            spec = importlib.util.spec_from_file_location(
                f"strategy_{python_file.stem}",
                python_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find strategy class (look for class that's not SimBroker)
            strategy_class = None
            for name in dir(module):
                obj = getattr(module, name)
                if isinstance(obj, type) and name not in ['SimBroker', 'BacktestConfig']:
                    strategy_class = obj
                    break
            
            if strategy_class:
                logger.info(f"Loaded strategy class: {strategy_class.__name__}")
                return strategy_class
            else:
                logger.error(f"No strategy class found in {python_file.name}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to load {python_file.name}: {e}")
            return None
    
    def run_backtest(self, python_file: Path) -> bool:
        """
        Run backtest for a specific strategy
        
        Args:
            python_file: Path to Python strategy file
            
        Returns:
            True if backtest completed successfully
        """
        logger.info(f"{'='*70}")
        logger.info(f"Running backtest: {python_file.name}")
        logger.info(f"{'='*70}")
        
        try:
            # Check if the strategy has a run_backtest function
            spec = importlib.util.spec_from_file_location(
                f"strategy_{python_file.stem}",
                python_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, 'run_backtest'):
                # Run the strategy's own backtest function
                module.run_backtest()
                logger.info(f"✓ Backtest completed successfully")
                return True
            else:
                logger.warning(f"No run_backtest() function found in {python_file.name}")
                logger.info("You'll need to run the strategy manually")
                return False
                
        except Exception as e:
            logger.error(f"✗ Backtest failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def print_status_report(self):
        """Print a formatted status report of all strategies"""
        status_list = self.check_strategy_status()
        
        print("\n" + "="*80)
        print("STRATEGY STATUS REPORT")
        print("="*80)
        print(f"Codes Directory: {self.codes_dir}")
        print(f"Total Strategies: {len(status_list)}")
        print("="*80)
        
        if not status_list:
            print("\nNo strategies found in codes directory.")
            print("Add JSON strategy definitions to get started.")
            return
        
        # Count statuses
        implemented = sum(1 for s in status_list if s['has_python'])
        missing = len(status_list) - implemented
        
        print(f"\n✓ Implemented: {implemented}")
        print(f"✗ Missing Code: {missing}")
        print("\n" + "-"*80)
        
        # Print each strategy
        for i, status in enumerate(status_list, 1):
            marker = "✓" if status['has_python'] else "✗"
            print(f"\n{i}. {marker} {status['title']}")
            print(f"   JSON: {status['json_file'].name}")
            print(f"   Python: {status['python_file'].name} {'(exists)' if status['has_python'] else '(MISSING)'}")
            print(f"   Strategy ID: {status['strategy_id']}")
            print(f"   Created: {status['created_at']}")
        
        print("\n" + "="*80)


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description='Strategy Manager - Generate and run trading strategies'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show status of all strategies'
    )
    parser.add_argument(
        '--generate',
        action='store_true',
        help='Generate Python code for strategies missing implementations'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force regeneration of all strategies (use with --generate)'
    )
    parser.add_argument(
        '--run',
        type=str,
        metavar='STRATEGY',
        help='Run backtest for specific strategy (provide filename without .py)'
    )
    parser.add_argument(
        '--run-all',
        action='store_true',
        help='Run backtests for all implemented strategies'
    )
    parser.add_argument(
        '--codes-dir',
        type=str,
        help='Custom codes directory path'
    )
    
    args = parser.parse_args()
    
    # Initialize manager
    codes_dir = Path(args.codes_dir) if args.codes_dir else None
    manager = StrategyManager(codes_dir=codes_dir)
    
    # Show status
    if args.status or (not args.generate and not args.run and not args.run_all):
        manager.print_status_report()
    
    # Generate missing strategies
    if args.generate:
        print("\n" + "="*80)
        print("GENERATING MISSING STRATEGIES")
        print("="*80)
        results = manager.generate_missing_strategies(force=args.force)
        
        success_count = sum(1 for r in results if r['success'])
        print(f"\nGeneration complete: {success_count}/{len(results)} succeeded")
        
        # Show any failures
        failures = [r for r in results if not r['success']]
        if failures:
            print("\nFailed generations:")
            for f in failures:
                print(f"  ✗ {f['json_file'].name}: {f['error']}")
    
    # Run specific strategy
    if args.run:
        python_file = manager.codes_dir / f"{args.run}.py"
        if not python_file.exists():
            print(f"\n✗ Strategy not found: {python_file}")
            print(f"Available strategies:")
            for py_file in manager.get_python_strategy_files():
                print(f"  - {py_file.stem}")
            sys.exit(1)
        
        manager.run_backtest(python_file)
    
    # Run all strategies
    if args.run_all:
        print("\n" + "="*80)
        print("RUNNING ALL STRATEGY BACKTESTS")
        print("="*80)
        
        py_files = manager.get_python_strategy_files()
        if not py_files:
            print("\nNo Python strategy files found.")
            print("Run with --generate first to create strategy implementations.")
            sys.exit(1)
        
        results = []
        for py_file in py_files:
            success = manager.run_backtest(py_file)
            results.append((py_file.name, success))
            print()  # Blank line between backtests
        
        # Summary
        print("="*80)
        print("BACKTEST SUMMARY")
        print("="*80)
        success_count = sum(1 for _, success in results if success)
        print(f"Completed: {success_count}/{len(results)}")
        for name, success in results:
            marker = "✓" if success else "✗"
            print(f"  {marker} {name}")


if __name__ == "__main__":
    main()
