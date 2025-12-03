"""
Bot Error Fixer - Automatically fix bot execution errors using AI
==================================================================

This module handles:
1. Reading bot execution errors from output logs
2. Extracting error messages and stack traces
3. Requesting AI agent to fix the issues
4. Re-running the bot to verify fixes
5. Tracking error resolution history

Features:
- Automatic error detection and classification
- AI-powered error fixing
- Iterative retry with improvements
- Error history and pattern tracking
- Detailed fix reports

Last updated: 2025-12-03
Version: 1.0.0
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)


@dataclass
class ErrorFixAttempt:
    """Record of an error fixing attempt"""
    attempt_number: int
    original_error: str
    error_type: str
    fix_description: str
    success: bool
    fixed_code: Optional[str] = None
    execution_result: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ErrorAnalyzer:
    """Analyze execution errors and classify them"""
    
    ERROR_PATTERNS = {
        'import_error': {
            'patterns': [r'ModuleNotFoundError', r'ImportError', r'cannot import'],
            'description': 'Missing or incorrect import',
            'severity': 'high'
        },
        'syntax_error': {
            'patterns': [r'SyntaxError', r'IndentationError'],
            'description': 'Code syntax error',
            'severity': 'high'
        },
        'attribute_error': {
            'patterns': [r"AttributeError", r"has no attribute"],
            'description': 'Invalid attribute or method call',
            'severity': 'medium'
        },
        'type_error': {
            'patterns': [r'TypeError', r'unsupported operand'],
            'description': 'Type mismatch or incompatible operation',
            'severity': 'medium'
        },
        'value_error': {
            'patterns': [r'ValueError', r'invalid literal'],
            'description': 'Invalid value provided',
            'severity': 'medium'
        },
        'index_error': {
            'patterns': [r'IndexError', r'list index out of range'],
            'description': 'Array/list index out of bounds',
            'severity': 'low'
        },
        'key_error': {
            'patterns': [r'KeyError', r'dict key'],
            'description': 'Missing dictionary key',
            'severity': 'medium'
        },
        'runtime_error': {
            'patterns': [r'RuntimeError', r'execution error'],
            'description': 'Runtime error during execution',
            'severity': 'high'
        },
        'timeout_error': {
            'patterns': [r'TimeoutExpired', r'timeout'],
            'description': 'Execution timeout',
            'severity': 'medium'
        },
        'file_error': {
            'patterns': [r'FileNotFoundError', r'file not found'],
            'description': 'File not found',
            'severity': 'high'
        },
    }
    
    @classmethod
    def classify_error(cls, error_output: str) -> Tuple[str, str, str]:
        """
        Classify error type from output
        
        Args:
            error_output: Error message and traceback
        
        Returns:
            Tuple of (error_type, description, severity)
        """
        for error_type, error_info in cls.ERROR_PATTERNS.items():
            for pattern in error_info['patterns']:
                if re.search(pattern, error_output, re.IGNORECASE):
                    return (
                        error_type,
                        error_info['description'],
                        error_info['severity']
                    )
        
        return 'unknown_error', 'Unknown error type', 'unknown'
    
    @classmethod
    def extract_error_message(cls, output: str, stderr: str) -> str:
        """
        Extract the most relevant error message
        
        Args:
            output: Standard output
            stderr: Standard error
        
        Returns:
            Formatted error message
        """
        combined = stderr + "\n" + output
        lines = combined.split('\n')
        
        # Get last 20 lines (usually contains the error)
        relevant_lines = lines[-20:] if len(lines) > 20 else lines
        relevant_output = '\n'.join(relevant_lines)
        
        return relevant_output.strip()


class BotErrorFixer:
    """Automatically fix bot execution errors using AI"""
    
    def __init__(self, strategy_generator=None, max_iterations: int = 3):
        """
        Initialize bot error fixer
        
        Args:
            strategy_generator: Instance of GeminiStrategyGenerator for fixing code
            max_iterations: Maximum number of fix attempts (default: 3)
        """
        self.strategy_generator = strategy_generator
        self.max_iterations = max_iterations
        self.fix_history: List[ErrorFixAttempt] = []
    
    def fix_bot_error(
        self,
        bot_file: Path,
        error_output: str,
        original_code: str,
        execution_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str, Optional[ErrorFixAttempt]]:
        """
        Attempt to fix bot execution error
        
        Args:
            bot_file: Path to the bot file
            error_output: Error message from execution
            original_code: Original bot code
            execution_context: Additional context (parameters, symbol, etc.)
        
        Returns:
            Tuple of (success, fixed_code, fix_attempt_record)
        """
        # Analyze the error
        error_type, error_desc, severity = ErrorAnalyzer.classify_error(error_output)
        error_message = ErrorAnalyzer.extract_error_message(error_output, "")
        
        logger.info(f"\n{'='*70}")
        logger.info(f"ERROR DETECTED: {error_type} (Severity: {severity})")
        logger.info(f"Description: {error_desc}")
        logger.info(f"{'='*70}")
        logger.info(f"Error Details:\n{error_message}")
        
        # Create fix attempt record (with success=False initially)
        fix_attempt = ErrorFixAttempt(
            attempt_number=len(self.fix_history) + 1,
            original_error=error_message,
            error_type=error_type,
            fix_description="",
            success=False
        )
        
        # If no strategy generator, we can only log the error
        if not self.strategy_generator:
            logger.warning("No strategy generator available. Cannot auto-fix.")
            fix_attempt.fix_description = "Auto-fix unavailable (no strategy generator)"
            self.fix_history.append(fix_attempt)
            return False, original_code, fix_attempt
        
        try:
            # Build fix request prompt
            fix_prompt = self._build_fix_prompt(
                original_code=original_code,
                error_message=error_message,
                error_type=error_type,
                bot_file=bot_file,
                execution_context=execution_context
            )
            
            logger.info(f"\nRequesting AI to fix {error_type}...")
            
            # Request AI to fix the code
            fixed_code = self.strategy_generator.generate_strategy(
                description=fix_prompt,
                strategy_name=bot_file.stem
            )
            
            if fixed_code:
                fix_attempt.success = True
                fix_attempt.fixed_code = fixed_code
                fix_attempt.fix_description = f"AI-generated fix for {error_type}"
                
                logger.info("✓ AI generated fixed code")
                logger.info(f"Fix: {fix_attempt.fix_description}")
                
                self.fix_history.append(fix_attempt)
                return True, fixed_code, fix_attempt
            else:
                fix_attempt.success = False
                fix_attempt.fix_description = "AI failed to generate fixed code"
                self.fix_history.append(fix_attempt)
                logger.error("AI failed to generate fixed code")
                return False, original_code, fix_attempt
        
        except Exception as e:
            fix_attempt.success = False
            fix_attempt.fix_description = f"Error during fix attempt: {str(e)}"
            self.fix_history.append(fix_attempt)
            logger.error(f"Failed to fix error: {e}")
            return False, original_code, fix_attempt
    
    def _build_fix_prompt(
        self,
        original_code: str,
        error_message: str,
        error_type: str,
        bot_file: Path,
        execution_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build a detailed prompt for AI to fix the code
        
        Args:
            original_code: Original bot code that failed
            error_message: Error message/traceback
            error_type: Type of error
            bot_file: Path to bot file
            execution_context: Execution context
        
        Returns:
            Detailed fix prompt for AI
        """
        context_str = ""
        if execution_context:
            context_str = f"\nExecution Context:\n"
            for key, value in execution_context.items():
                context_str += f"  - {key}: {value}\n"
        
        prompt = f"""
TASK: Fix the trading bot code that has an execution error.

ERROR TYPE: {error_type}
BOT FILE: {bot_file.name}

ORIGINAL ERROR:
```
{error_message}
```

ORIGINAL CODE:
```python
{original_code}
```
{context_str}

REQUIREMENTS FOR FIXING:
1. Identify the root cause of the {error_type}
2. Provide corrected code that resolves the error
3. Maintain all original functionality and strategy logic
4. Use pre-built indicators from data_api.indicators when available
5. Ensure the code runs without errors
6. Add comments explaining the fixes
7. Return ONLY the corrected Python code, no explanations

COMMON FIXES FOR {error_type}:
"""
        
        # Add error-specific guidance
        if error_type == 'import_error':
            prompt += """
- Verify all imports exist and module paths are correct
- Use relative imports if accessing parent modules
- Check that required dependencies are installed
- Use absolute paths from project root when needed
"""
        elif error_type == 'attribute_error':
            prompt += """
- Check that object attributes/methods exist
- Verify correct spelling of method/attribute names
- Ensure objects are initialized before use
- Check backtesting.py API documentation for correct attribute names
"""
        elif error_type == 'index_error':
            prompt += """
- Add bounds checking before array access
- Ensure index is within valid range
- Handle cases where data might be insufficient
- Check for minimum bars required in init() before accessing data
"""
        elif error_type == 'syntax_error':
            prompt += """
- Check for matching parentheses, brackets, braces
- Verify indentation is correct
- Check for missing colons in function/class definitions
- Ensure proper string formatting and quotes
"""
        elif error_type == 'runtime_error':
            prompt += """
- Add error handling with try/except blocks
- Verify all calculations are mathematically valid
- Check division by zero scenarios
- Ensure data types are compatible
"""
        
        return prompt
    
    def iterative_fix(
        self,
        bot_file: Path,
        bot_executor,
        max_attempts: int = None
    ) -> Tuple[bool, str, List[ErrorFixAttempt]]:
        """
        Iteratively fix bot errors until successful or max attempts reached
        
        Args:
            bot_file: Path to bot file
            bot_executor: BotExecutor instance to run the bot
            max_attempts: Maximum fix attempts (default: self.max_iterations)
        
        Returns:
            Tuple of (success, final_code, fix_history)
        """
        if max_attempts is None:
            max_attempts = self.max_iterations
        
        current_code = bot_file.read_text(encoding='utf-8')
        self.fix_history = []
        
        logger.info(f"\n{'='*70}")
        logger.info(f"STARTING ITERATIVE ERROR FIXING")
        logger.info(f"Max attempts: {max_attempts}")
        logger.info(f"{'='*70}\n")
        
        for attempt in range(max_attempts):
            logger.info(f"\n>>> ATTEMPT {attempt + 1}/{max_attempts}")
            
            # Execute the bot
            result = bot_executor.execute_bot(
                strategy_file=str(bot_file),
                save_results=False
            )
            
            if result.success:
                logger.info(f"\n✓ SUCCESS! Bot executed successfully on attempt {attempt + 1}")
                return True, current_code, self.fix_history
            
            if not result.error:
                logger.warning("Execution failed but no error details available")
                return False, current_code, self.fix_history
            
            # Try to fix the error
            output_log = result.output_log or ""
            success, fixed_code, fix_record = self.fix_bot_error(
                bot_file=bot_file,
                error_output=output_log,
                original_code=current_code,
                execution_context={
                    'symbol': result.test_symbol,
                    'period_days': result.test_period_days
                }
            )
            
            if not success:
                logger.error(f"Failed to fix error on attempt {attempt + 1}")
                break
            
            # Update code and write to file
            current_code = fixed_code
            bot_file.write_text(current_code, encoding='utf-8')
            logger.info(f"Updated bot file with fixes")
        
        logger.info(f"\n{'='*70}")
        logger.info(f"ERROR FIXING COMPLETE")
        logger.info(f"Total attempts: {len(self.fix_history)}")
        logger.info(f"Success: {'YES ✓' if any(f.success for f in self.fix_history) else 'NO ✗'}")
        logger.info(f"{'='*70}\n")
        
        return False, current_code, self.fix_history
    
    def get_fix_report(self) -> Dict[str, Any]:
        """Get a detailed report of all fix attempts"""
        return {
            'total_attempts': len(self.fix_history),
            'successful_fixes': sum(1 for f in self.fix_history if f.success),
            'error_types': list(set(f.error_type for f in self.fix_history)),
            'attempts': [
                {
                    'attempt': f.attempt_number,
                    'error_type': f.error_type,
                    'success': f.success,
                    'timestamp': f.timestamp.isoformat(),
                    'description': f.fix_description
                }
                for f in self.fix_history
            ]
        }


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test error analyzer
    test_error = """
Traceback (most recent call last):
  File "test.py", line 10, in <module>
    result = calculate_ema(data, 30)
AttributeError: 'list' object has no attribute 'ewm'
"""
    
    error_type, desc, severity = ErrorAnalyzer.classify_error(test_error)
    print(f"Error Type: {error_type}")
    print(f"Description: {desc}")
    print(f"Severity: {severity}")
