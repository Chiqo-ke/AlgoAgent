"""
Bot Dry Runner - Quick Validation with Limited Data
====================================================

Runs bot scripts with limited data (10-50 bars) for fast error detection.
This catches runtime errors without waiting for full backtest execution.

Author: AI Agent Improvement System
Created: 2026-02-02
"""

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class BotDryRunner:
    """
    Quick validation runner that tests bots with limited data.
    
    Executes bot scripts with only 10-50 bars of data to catch:
    - Import errors
    - Runtime exceptions
    - Key errors (indicator naming issues)
    - Logic errors in strategy code
    
    Much faster than full backtest while catching most errors.
    """
    
    def __init__(self, venv_python: str = None, timeout: int = 30):
        """
        Initialize dry runner.
        
        Args:
            venv_python: Path to Python executable (default: current Python)
            timeout: Maximum execution time in seconds (default: 30)
        """
        self.venv_python = venv_python or sys.executable
        self.timeout = timeout
    
    def dry_run(self, bot_file: Path, max_bars: int = 10) -> Tuple[bool, str, dict]:
        """
        Run bot with limited data for quick validation.
        
        Args:
            bot_file: Path to bot script
            max_bars: Process only this many bars (default: 10)
            
        Returns:
            Tuple of (success: bool, message: str, details: dict)
        """
        logger.info(f"[DRY-RUN] Testing {bot_file.name} with {max_bars} bars...")
        
        # Create wrapper script that limits data
        wrapper_code = self._create_wrapper_script(bot_file, max_bars)
        
        # Execute wrapper
        success, output, error = self._execute_wrapper(wrapper_code)
        
        # Analyze results
        details = self._analyze_output(output, error)
        
        if success:
            message = f"[OK] Dry run successful - processed {max_bars} bars without errors"
            logger.info(message)
        else:
            message = f"[ERROR] Dry run failed: {details.get('error_type', 'Unknown error')}"
            logger.error(message)
            logger.error(f"Details: {error}")
        
        return success, message, details
    
    def _create_wrapper_script(self, bot_file: Path, max_bars: int) -> str:
        """
        Create a wrapper script that monkey-patches data loading to limit bars.
        Fixed to work in exec() context without __file__.
        """
        wrapper = f'''
import sys
from pathlib import Path

# Add Backtest to path
backtest_dir = Path(r"{bot_file.parent.parent}")
if str(backtest_dir) not in sys.path:
    sys.path.insert(0, str(backtest_dir))

# Monkey-patch data_loader to return limited data
import data_loader

original_load_market_data = data_loader.load_market_data

def limited_load_market_data(*args, **kwargs):
    """Wrapper that limits data to {max_bars} bars"""
    
    # For streaming mode
    if kwargs.get('stream', False):
        print(f"[DRY-RUN] Limiting streaming data to {max_bars} bars...")
        count = 0
        for timestamp, market_data, progress in original_load_market_data(*args, **kwargs):
            if count >= {max_bars}:
                print(f"[DRY-RUN] Reached {max_bars} bar limit - stopping")
                break
            yield timestamp, market_data, progress
            count += 1
    else:
        # For batch mode - just use shorter period
        kwargs['period'] = '1mo'  # Limit to 1 month of data
        print(f"[DRY-RUN] Using 1 month of data for batch mode...")
        return original_load_market_data(*args, **kwargs)

# Replace data loader
data_loader.load_market_data = limited_load_market_data

# Read bot file
with open(r"{bot_file}", 'r', encoding='utf-8') as f:
    bot_code = f.read()

# Replace any __file__ references with the actual file path
bot_code = bot_code.replace('__file__', repr(r'{bot_file}'))

# Now execute the bot with proper context
print("[DRY-RUN] Starting bot execution with limited data...")
exec(bot_code, {{'__name__': '__main__', '__file__': r'{bot_file}'}})
print("[DRY-RUN] Bot execution completed successfully!")
'''
        return wrapper
    
    def _execute_wrapper(self, wrapper_code: str) -> Tuple[bool, str, str]:
        """
        Execute the wrapper script and capture output.
        
        Returns:
            Tuple of (success, stdout, stderr)
        """
        try:
            result = subprocess.run(
                [self.venv_python, '-c', wrapper_code],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=Path.cwd()
            )
            
            success = result.returncode == 0
            return success, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "", f"Timeout after {self.timeout}s - possible infinite loop"
        except Exception as e:
            return False, "", f"Execution failed: {str(e)}"
    
    def _analyze_output(self, stdout: str, stderr: str) -> dict:
        """
        Analyze output to determine error types and details.
        
        Returns:
            Dict with error classification and details
        """
        combined = stdout + stderr
        details = {
            'stdout': stdout,
            'stderr': stderr,
            'error_type': None,
            'error_details': None,
            'suggestions': []
        }
        
        # Check for common error patterns
        if "ImportError" in combined or "ModuleNotFoundError" in combined:
            details['error_type'] = 'Import Error'
            details['error_details'] = 'Missing or incorrect imports'
            details['suggestions'].append("Check import statements and path setup")
            
            if "Backtest" in combined:
                details['suggestions'].append("Ensure using direct imports, not 'from Backtest.*'")
        
        elif "django.core.exceptions.ImproperlyConfigured" in combined:
            details['error_type'] = 'Django Configuration Error'
            details['error_details'] = 'Django initialization without proper settings'
            details['suggestions'].append("Use direct imports instead of 'from Backtest.*'")
            details['suggestions'].append("Avoid importing from Backtest package root")
        
        elif "KeyError" in combined:
            details['error_type'] = 'Key Error'
            details['error_details'] = 'Indicator or data key not found'
            details['suggestions'].append("Check indicator key naming (uppercase vs lowercase)")
            details['suggestions'].append("Verify streaming mode uses lowercase: 'ema_12'")
            details['suggestions'].append("Verify batch mode uses uppercase: 'EMA_12'")
        
        elif "NoneType" in combined and ("Indicators not ready" in combined or ".get(" in combined):
            details['error_type'] = 'None Value Error'
            details['error_details'] = 'Indicators returning None'
            details['suggestions'].append("Indicator keys may not match data loader output")
            details['suggestions'].append("Check if using correct case: lowercase for streaming, uppercase for batch")
        
        elif "IndentationError" in combined or "SyntaxError" in combined:
            details['error_type'] = 'Syntax Error'
            details['error_details'] = 'Python syntax error in generated code'
            details['suggestions'].append("Check code indentation and syntax")
        
        elif "Timeout" in stderr:
            details['error_type'] = 'Timeout'
            details['error_details'] = 'Execution exceeded time limit'
            details['suggestions'].append("Possible infinite loop in strategy logic")
            details['suggestions'].append("Check for missing loop exit conditions")
        
        elif "Successfully" in stdout or "OK" in stdout:
            details['error_type'] = None  # Success
        
        else:
            details['error_type'] = 'Unknown Error'
            details['error_details'] = 'Unexpected error during execution'
        
        return details
    
    def get_dry_run_report(self, bot_file: Path, max_bars: int = 10) -> str:
        """
        Generate a comprehensive dry run report.
        
        Args:
            bot_file: Path to bot script
            max_bars: Number of bars to test with
            
        Returns:
            Formatted report string
        """
        success, message, details = self.dry_run(bot_file, max_bars)
        
        report = []
        report.append("=" * 70)
        report.append("BOT DRY RUN REPORT")
        report.append("=" * 70)
        report.append(f"File: {bot_file.name}")
        report.append(f"Test Size: {max_bars} bars")
        report.append(f"Timeout: {self.timeout}s")
        report.append("")
        
        if success:
            report.append("[OK] DRY RUN PASSED")
            report.append("Bot executed successfully with limited data")
            report.append("Ready for full backtest execution")
        else:
            report.append("[ERROR] DRY RUN FAILED")
            report.append(f"Error Type: {details['error_type']}")
            report.append(f"Details: {details['error_details']}")
            
            if details['suggestions']:
                report.append("")
                report.append("Suggestions:")
                for i, suggestion in enumerate(details['suggestions'], 1):
                    report.append(f"  {i}. {suggestion}")
            
            report.append("")
            report.append("Error Output:")
            report.append("-" * 70)
            report.append(details['stderr'][:500])  # Limit error output
        
        report.append("=" * 70)
        return "\n".join(report)


def dry_run_bot(bot_file: Path, max_bars: int = 10) -> Tuple[bool, str]:
    """
    Convenience function for quick bot validation.
    
    Args:
        bot_file: Path to bot script
        max_bars: Number of bars to test (default: 10)
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    runner = BotDryRunner()
    success, message, _ = runner.dry_run(bot_file, max_bars)
    return success, message


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run bot with limited data for quick validation')
    parser.add_argument('bot_file', type=Path, help='Path to bot script')
    parser.add_argument('--max-bars', type=int, default=10, help='Number of bars to process')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout in seconds')
    
    args = parser.parse_args()
    
    runner = BotDryRunner(timeout=args.timeout)
    report = runner.get_dry_run_report(args.bot_file, args.max_bars)
    
    print(report)
    
    success, _, _ = runner.dry_run(args.bot_file, args.max_bars)
    sys.exit(0 if success else 1)
