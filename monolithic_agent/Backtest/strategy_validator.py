"""
Strategy Code Validator
Automatically tests generated strategy code before user backtesting
"""

import sys
import logging
import traceback
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)8s | %(message)s',
    handlers=[
        logging.FileHandler('strategy_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class StrategyValidator:
    """
    Validates generated strategy code by running quick backtests
    and checking for common issues
    """
    
    def __init__(self):
        self.validation_results = {}
        
    def validate_strategy_code(
        self,
        strategy_code: str,
        strategy_name: str = "GeneratedStrategy",
        test_symbol: str = "AAPL",
        test_period_days: int = 365  # Use 1 year by default
    ) -> Dict:
        """
        Validate strategy code by running a quick backtest
        
        Args:
            strategy_code: Python code string for the strategy
            strategy_name: Name of the strategy
            test_symbol: Symbol to test with
            test_period_days: Number of days to test (default: 365 for 1 year)
            
        Returns:
            Validation result dictionary with 'valid' only True if at least 1 trade executed
        """
        logger.info(f"=" * 70)
        logger.info(f"Validating Strategy: {strategy_name}")
        logger.info(f"Test Period: {test_period_days} days (~{test_period_days/365:.1f} years)")
        logger.info(f"=" * 70)
        
        result = {
            "strategy_name": strategy_name,
            "valid": False,
            "errors": [],
            "warnings": [],
            "suggestions": [],
            "test_results": None,
            "execution_time": None,
            "trades_executed": 0,
            "indicators_initialized": False
        }
        
        start_time = datetime.now()
        
        try:
            # Step 1: Check for common code issues
            logger.info("[1/5] Checking code syntax...")
            syntax_issues = self._check_syntax(strategy_code)
            if syntax_issues:
                result["errors"].extend(syntax_issues)
                logger.error(f"Syntax errors found: {len(syntax_issues)}")
                return result
            logger.info("[OK] Syntax check passed")
            
            # Step 2: Check for required components
            logger.info("[2/5] Checking required components...")
            component_issues = self._check_required_components(strategy_code)
            if component_issues:
                result["errors"].extend(component_issues)
                logger.error(f"Missing required components: {len(component_issues)}")
                return result
            logger.info("[OK] Component check passed")
            
            # Step 3: Execute strategy in sandbox
            logger.info("[3/5] Testing strategy execution...")
            exec_result = self._execute_strategy_test(
                strategy_code,
                strategy_name,
                test_symbol,
                test_period_days
            )
            
            if exec_result["success"]:
                logger.info("[OK] Strategy executed successfully")
                result["test_results"] = exec_result["results"]
                result["trades_executed"] = exec_result["trades"]
                result["indicators_initialized"] = exec_result["indicators_ok"]
            else:
                result["errors"].append(exec_result["error"])
                logger.error(f"Execution failed: {exec_result['error']}")
                return result
            
            # Step 4: Validate results
            logger.info("[4/5] Validating backtest results...")
            validation_issues = self._validate_results(exec_result)
            result["warnings"].extend(validation_issues["warnings"])
            result["suggestions"].extend(validation_issues["suggestions"])
            
            # Check for critical errors (like zero trades)
            if validation_issues["critical_errors"]:
                result["errors"].extend(validation_issues["critical_errors"])
                logger.error(f"Critical validation errors: {len(validation_issues['critical_errors'])}")
                for error in validation_issues["critical_errors"]:
                    logger.error(f"  - {error}")
                return result
            
            if validation_issues["warnings"]:
                logger.warning(f"Warnings: {len(validation_issues['warnings'])}")
                for warning in validation_issues["warnings"]:
                    logger.warning(f"  - {warning}")
            else:
                logger.info("[OK] Results validation passed")
            
            # Step 5: Generate recommendations
            logger.info("[5/5] Generating recommendations...")
            recommendations = self._generate_recommendations(exec_result)
            result["suggestions"].extend(recommendations)
            
            # Mark as valid if no errors
            result["valid"] = len(result["errors"]) == 0
            result["execution_time"] = (datetime.now() - start_time).total_seconds()
            
            logger.info("=" * 70)
            if result["valid"]:
                logger.info(f"[SUCCESS] Strategy validation PASSED!")
                logger.info(f"  [OK] At least 1 trade executed: {result['trades_executed']} trades")
                logger.info(f"  [OK] Code compiles and runs successfully")
                logger.info(f"  [OK] Execution time: {result['execution_time']:.2f}s")
                logger.info(f"  Strategy is APPROVED for user backtesting")
            else:
                logger.error(f"[FAILED] Strategy validation FAILED")
                logger.error(f"  [X] Errors: {len(result['errors'])}")
                logger.error(f"  Strategy is REJECTED - cannot be used for backtesting")
            logger.info("=" * 70)
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            logger.error(traceback.format_exc())
            result["errors"].append(f"Validation exception: {str(e)}")
        
        return result
    
    def _check_syntax(self, code: str) -> list:
        """Check for syntax errors"""
        errors = []
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
        except Exception as e:
            errors.append(f"Code compilation error: {str(e)}")
        return errors
    
    def _check_required_components(self, code: str) -> list:
        """Check for required strategy components"""
        errors = []
        
        required_patterns = [
            ("class.*Strategy.*:", "Strategy class definition"),
            ("def init\\(self\\):", "init() method"),
            ("def next\\(self\\):", "next() method"),
        ]
        
        for pattern, description in required_patterns:
            import re
            if not re.search(pattern, code):
                errors.append(f"Missing required component: {description}")
        
        return errors
    
    def _execute_strategy_test(
        self,
        strategy_code: str,
        strategy_name: str,
        test_symbol: str,
        test_period_days: int
    ) -> Dict:
        """Execute strategy in a test environment"""
        result = {
            "success": False,
            "error": None,
            "results": None,
            "trades": 0,
            "indicators_ok": False
        }
        
        try:
            # Import required modules
            from backtesting import Strategy, Backtest
            from backtesting.lib import crossover
            from backtesting.test import SMA
            from backtesting_adapter import fetch_and_prepare_data
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=test_period_days)
            
            logger.info(f"Fetching test data: {test_symbol} from {start_date.date()} to {end_date.date()}")
            
            # Fetch test data
            data = fetch_and_prepare_data(
                symbol=test_symbol,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                interval="1d"
            )
            
            logger.info(f"Loaded {len(data)} bars for testing")
            
            # Execute strategy code to get the class (avoid running main block)
            namespace = {
                'Strategy': Strategy,
                'crossover': crossover,
                'SMA': SMA,
                'pd': pd,
                'np': np,
                'logger': logger,
                'print': lambda *args, **kwargs: None,  # Suppress prints during class definition
                '__file__': '<validator>',  # Mock __file__ for strategies that reference it
                '__name__': '<validator>',  # Prevent __main__ block from running
                'Path': Path,
                'sys': sys
            }
            
            exec(strategy_code, namespace)
            
            # Find the strategy class
            strategy_class = None
            for item in namespace.values():
                if (isinstance(item, type) and 
                    issubclass(item, Strategy) and 
                    item is not Strategy):
                    strategy_class = item
                    break
            
            if not strategy_class:
                result["error"] = "No Strategy class found in code"
                return result
            
            logger.info(f"Found strategy class: {strategy_class.__name__}")
            
            # Run backtest
            bt = Backtest(
                data=data,
                strategy=strategy_class,
                cash=10000,
                commission=0.002,
                exclusive_orders=True
            )
            
            logger.info("Running backtest...")
            stats = bt.run()
            
            # Extract results
            result["success"] = True
            result["results"] = {
                "return": float(stats['Return [%]']),
                "trades": int(stats['# Trades']),
                "win_rate": float(stats['Win Rate [%]']) if not pd.isna(stats['Win Rate [%]']) else 0,
                "sharpe": float(stats['Sharpe Ratio']) if not pd.isna(stats['Sharpe Ratio']) else 0,
                "max_drawdown": float(stats['Max. Drawdown [%]'])
            }
            result["trades"] = result["results"]["trades"]
            result["indicators_ok"] = True  # If we got here, indicators worked
            
            logger.info(f"Backtest completed: {result['trades']} trades, {result['results']['return']:.2f}% return")
            
        except Exception as e:
            logger.error(f"Strategy execution failed: {e}")
            logger.error(traceback.format_exc())
            result["error"] = str(e)
        
        return result
    
    def _validate_results(self, exec_result: Dict) -> Dict:
        """Validate backtest results for common issues"""
        validation = {
            "warnings": [],
            "suggestions": [],
            "critical_errors": []  # Errors that make strategy invalid
        }
        
        if not exec_result["success"]:
            return validation
        
        results = exec_result["results"]
        
        # CRITICAL: Check for zero trades - this makes strategy INVALID
        if results["trades"] == 0:
            validation["critical_errors"].append(
                "VALIDATION FAILED: No trades executed in 1-year test period. "
                "Strategy must execute at least 1 trade to be approved."
            )
            validation["suggestions"].append(
                "Check that entry/exit conditions can be triggered with the current parameters"
            )
            validation["suggestions"].append(
                "Verify indicators are calculating correctly and not all NaN"
            )
        
        # Check for excessive trades
        elif results["trades"] > 100:
            validation["warnings"].append(
                f"Very high number of trades ({results['trades']}) - may indicate overtrading"
            )
            validation["suggestions"].append(
                "Consider adding filters or increasing signal thresholds"
            )
        
        # Check for negative returns
        if results["return"] < -10:
            validation["warnings"].append(
                f"Large negative return ({results['return']:.2f}%) in test period"
            )
            validation["suggestions"].append(
                "Review strategy logic and risk management"
            )
        
        # Check for low win rate
        if results["trades"] > 0 and results["win_rate"] < 30:
            validation["warnings"].append(
                f"Low win rate ({results['win_rate']:.1f}%) - strategy may need refinement"
            )
        
        # Check for extreme drawdown
        if abs(results["max_drawdown"]) > 30:
            validation["warnings"].append(
                f"High maximum drawdown ({abs(results['max_drawdown']):.1f}%)"
            )
            validation["suggestions"].append(
                "Consider adding stop-loss or position sizing rules"
            )
        
        return validation
    
    def _generate_recommendations(self, exec_result: Dict) -> list:
        """Generate optimization recommendations"""
        recommendations = []
        
        if not exec_result["success"]:
            return recommendations
        
        results = exec_result["results"]
        
        # Positive recommendations
        if results["trades"] > 5 and results["win_rate"] > 50:
            recommendations.append("Strategy shows good trade frequency and win rate")
        
        if results["sharpe"] > 1.0:
            recommendations.append("Good risk-adjusted returns (Sharpe > 1.0)")
        
        if abs(results["max_drawdown"]) < 15:
            recommendations.append("Drawdown is within acceptable range")
        
        return recommendations


def validate_strategy_file(file_path: str) -> Dict:
    """
    Validate a strategy file
    
    Args:
        file_path: Path to the strategy Python file
        
    Returns:
        Validation result dictionary
    """
    validator = StrategyValidator()
    
    # Read strategy code
    with open(file_path, 'r') as f:
        strategy_code = f.read()
    
    # Extract strategy name from file
    strategy_name = Path(file_path).stem
    
    # Validate
    return validator.validate_strategy_code(strategy_code, strategy_name)


def validate_strategy_string(strategy_code: str, strategy_name: str = "GeneratedStrategy") -> Dict:
    """
    Validate strategy code string
    
    Args:
        strategy_code: Python code string
        strategy_name: Name for the strategy
        
    Returns:
        Validation result dictionary
    """
    validator = StrategyValidator()
    return validator.validate_strategy_code(strategy_code, strategy_name)


if __name__ == "__main__":
    # Example: Test the EMA strategy
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        logger.info(f"Validating strategy file: {file_path}")
        result = validate_strategy_file(file_path)
    else:
        # Test with BBand strategy
        logger.info("Testing with BBand strategy...")
        result = validate_strategy_file("codes/bband.py")
    
    # Print summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    print(f"Strategy: {result['strategy_name']}")
    print(f"Valid: {result['valid']}")
    print(f"Trades: {result['trades_executed']}")
    exec_time = result.get('execution_time')
    if exec_time is not None:
        print(f"Execution Time: {exec_time:.2f}s")
    else:
        print("Execution Time: N/A")
    
    if result['errors']:
        print(f"\nERRORS ({len(result['errors'])}):")
        for error in result['errors']:
            print(f"  ❌ {error}")
    
    if result['warnings']:
        print(f"\nWARNINGS ({len(result['warnings'])}):")
        for warning in result['warnings']:
            print(f"  ⚠️  {warning}")
    
    if result['suggestions']:
        print(f"\nSUGGESTIONS ({len(result['suggestions'])}):")
        for suggestion in result['suggestions']:
            print(f"  💡 {suggestion}")
    
    print("=" * 70)
