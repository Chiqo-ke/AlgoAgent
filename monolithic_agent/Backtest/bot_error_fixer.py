"""
Bot Error Fixer - Automatically fix bot execution errors using AI
==================================================================

This module handles:
1. Reading bot execution errors from output logs
2. Extracting error messages and stack traces
3. Requesting AI agent to fix the issues
4. Re-running the bot to verify fixes
5. Tracking error resolution history
6. Learning from execution failures (feedback loop)
7. Detecting framework vs bot code errors (NEW)
8. Pre-execution validation (NEW)

Features:
- Automatic error detection and classification
- AI-powered error fixing
- Iterative retry with improvements
- Error history and pattern tracking
- Detailed fix reports
- Feedback loop integration
- Framework error detection and escalation (NEW)
- Pre-execution validation for encoding, case sensitivity, filters (NEW)

Last updated: 2025-12-07
Version: 3.0.0
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
import time

logger = logging.getLogger(__name__)

# Import enhanced error detection
try:
    from .enhanced_error_detector import (
        EnhancedErrorDetector,
        ValidationIssue,
        ErrorSource,
        format_validation_report
    )
    ENHANCED_DETECTION_AVAILABLE = True
except ImportError:
    ENHANCED_DETECTION_AVAILABLE = False
    logger.warning("Enhanced error detection not available - using basic mode")
    
    # Create dummy types for compatibility
    class ValidationIssue:
        pass
    
    class ErrorSource:
        pass


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
        'encoding_error': {
            'patterns': [r'charmap_encode', r'UnicodeEncodeError', r'codec can\'t encode', r'encoding_table'],
            'description': 'Character encoding error (emoji/unicode in output)',
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
    """Automatically fix bot execution errors using AI with enhanced detection"""
    
    def __init__(self, strategy_generator=None, max_iterations: int = 5, learning_system=None):
        """
        Initialize bot error fixer
        
        Args:
            strategy_generator: Instance of GeminiStrategyGenerator for fixing code
            max_iterations: Maximum number of fix attempts (default: 5)
            learning_system: Instance of ErrorLearningSystem for feedback loop (optional)
        """
        self.strategy_generator = strategy_generator
        self.max_iterations = max_iterations
        self.fix_history: List[ErrorFixAttempt] = []
        self.learning_system = learning_system
        self.use_enhanced_detection = ENHANCED_DETECTION_AVAILABLE
        
        if self.learning_system:
            logger.info("Error learning system enabled (feedback loop active)")
        else:
            logger.debug("Error learning system not provided (feedback loop disabled)")
        
        if self.use_enhanced_detection:
            logger.info("✅ Enhanced error detection enabled (framework error detection, pre-validation)")
        else:
            logger.warning("⚠️  Enhanced error detection disabled (basic mode only)")
    
    def fix_bot_error_intelligently(
        self,
        bot_file: Path,
        error_output: str,
        original_code: str,
        execution_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str, Optional[ErrorFixAttempt]]:
        """
        Intelligently fix errors with enhanced detection
        
        Uses:
        1. Framework vs bot error detection
        2. Pre-execution validation
        3. Error source analysis
        4. Targeted fixing strategies
        
        Args:
            bot_file: Path to bot file
            error_output: Error message from execution
            original_code: Original bot code
            execution_context: Additional context (indicators, params, etc.)
        
        Returns:
            Tuple of (success, fixed_code, fix_attempt_record)
        """
        if not self.use_enhanced_detection:
            # Fall back to standard fix method
            return self.fix_bot_error(bot_file, error_output, original_code, execution_context)
        
        # Step 1: Detect error source
        error_source = EnhancedErrorDetector.detect_error_source(error_output)
        error_type, error_desc, severity = ErrorAnalyzer.classify_error(error_output)
        
        logger.info(f"\n{'='*70}")
        logger.info(f"ERROR DETECTED: {error_type} (Severity: {severity})")
        logger.info(f"Error Location: {error_source.error_location}")
        logger.info(f"File: {error_source.file_path}:{error_source.line_number or '?'}")
        logger.info(f"{'='*70}")
        
        # Step 2: Check if error is in framework (not bot code)
        if error_source.error_location == 'framework':
            logger.error("❌ ERROR IS IN FRAMEWORK CODE, NOT BOT CODE!")
            logger.error(f"   Framework Component: {error_source.framework_component}")
            logger.error(f"   File: {error_source.file_path}")
            logger.error(f"   Line: {error_source.line_number}")
            logger.error("")
            logger.error("This error CANNOT be fixed by modifying bot code.")
            logger.error("Framework file must be fixed manually.")
            logger.error("")
            
            # Generate framework fix suggestion
            fix_suggestion = self._suggest_framework_fix(
                error_output,
                error_source,
                error_type
            )
            
            logger.error("SUGGESTED FRAMEWORK FIX:")
            logger.error(fix_suggestion)
            
            # Record as failed attempt
            fix_attempt = ErrorFixAttempt(
                attempt_number=len(self.fix_history) + 1,
                original_error=error_output,
                error_type=f"{error_type} (framework)",
                fix_description="Framework error - cannot fix bot code",
                success=False
            )
            self.fix_history.append(fix_attempt)
            
            return False, original_code, fix_attempt
        
        # Step 3: Run pre-execution validation
        indicator_requests = execution_context.get('indicator_requests', {}) if execution_context else {}
        
        validation_issues, summary = EnhancedErrorDetector.comprehensive_validation(
            original_code,
            indicator_requests,
            bot_file
        )
        
        if validation_issues:
            logger.warning(f"\n⚠️  PRE-VALIDATION FOUND {len(validation_issues)} ISSUES:")
            logger.warning(format_validation_report(validation_issues, summary))
            
            # Attempt to auto-fix validation issues
            fixed_code = self._auto_fix_validation_issues(original_code, validation_issues)
            
            if fixed_code != original_code:
                logger.info("✅ Auto-fixed validation issues")
                
                fix_attempt = ErrorFixAttempt(
                    attempt_number=len(self.fix_history) + 1,
                    original_error=error_output,
                    error_type=error_type,
                    fix_description=f"Auto-fixed {len(validation_issues)} validation issues",
                    success=True,
                    fixed_code=fixed_code
                )
                self.fix_history.append(fix_attempt)
                
                return True, fixed_code, fix_attempt
        
        # Step 4: Use standard AI fix for bot code errors
        return self.fix_bot_error(bot_file, error_output, original_code, execution_context)
    
    def _suggest_framework_fix(
        self,
        error_output: str,
        error_source: ErrorSource,
        error_type: str
    ) -> str:
        """Generate framework fix suggestion"""
        
        fix_suggestions = {
            'encoding_error': """
Framework Fix Required:
1. Open file: {file_path}
2. Go to line: {line_number}
3. Remove all emoji/unicode characters from print() statements
4. Replace with ASCII alternatives:
   - 🔄 → [TALib] or [INFO]
   - ✅ → [OK] or [SUCCESS]
   - ❌ → [ERROR] or [FAILED]
   - ⚠️ → [WARNING]

Example:
  Before: print("🔄 Auto-discovering all TALib indicators...")
  After:  print("[TALib] Auto-discovering all TALib indicators...")
""",
            'import_error': """
Framework Fix Required:
1. Check if required module is installed
2. Verify import path is correct in framework
3. May need to install missing dependency
4. Check for circular import issues
""",
            'default': """
Framework Fix Required:
1. Open file: {file_path}
2. Go to line: {line_number}
3. Investigate error cause in framework code
4. Apply appropriate fix to framework
"""
        }
        
        template = fix_suggestions.get(error_type, fix_suggestions['default'])
        
        return template.format(
            file_path=error_source.file_path,
            line_number=error_source.line_number or '?'
        )
    
    def _auto_fix_validation_issues(
        self,
        code: str,
        issues: List[ValidationIssue]
    ) -> str:
        """Attempt to automatically fix validation issues"""
        
        fixed_code = code
        
        for issue in issues:
            if not issue.auto_fixable or not issue.suggested_fix:
                continue
            
            # Try to apply fix
            try:
                if issue.category == 'encoding':
                    # Fix encoding issues
                    fixed_code = self._fix_encoding_issue(fixed_code, issue)
                elif issue.category == 'case_sensitivity':
                    # Fix case sensitivity
                    fixed_code = self._fix_case_sensitivity(fixed_code, issue)
                elif issue.category == 'filter':
                    # Fix indicator filter
                    fixed_code = self._fix_indicator_filter(fixed_code, issue)
            except Exception as e:
                logger.warning(f"Could not auto-fix issue: {issue.message} - {e}")
        
        return fixed_code
    
    def _fix_encoding_issue(self, code: str, issue: ValidationIssue) -> str:
        """Fix encoding issue by replacing non-ASCII characters"""
        lines = code.split('\n')
        
        if issue.line_number and issue.suggested_fix:
            # Extract replacement from suggested fix
            if 'Replace:' in issue.suggested_fix and 'With:' in issue.suggested_fix:
                parts = issue.suggested_fix.split('With:')
                if len(parts) == 2:
                    old_line = parts[0].replace('Replace:', '').strip()
                    new_line = parts[1].strip()
                    
                    # Replace the line
                    line_idx = issue.line_number - 1
                    if 0 <= line_idx < len(lines):
                        lines[line_idx] = lines[line_idx].replace(old_line, new_line)
        
        return '\n'.join(lines)
    
    def _fix_case_sensitivity(self, code: str, issue: ValidationIssue) -> str:
        """Fix case sensitivity issue"""
        if issue.suggested_fix:
            # Extract old and new names from suggestion
            match = re.search(r"Change '([^']+)' to '([^']+)'", issue.suggested_fix)
            if match:
                old_name, new_name = match.groups()
                # Replace all occurrences
                code = code.replace(f"'{old_name}'", f"'{new_name}'")
                code = code.replace(f'"{old_name}"', f'"{new_name}"')
        
        return code
    
    def _fix_indicator_filter(self, code: str, issue: ValidationIssue) -> str:
        """Fix indicator filter to include missing prefixes"""
        if issue.suggested_fix and 'Suggested:' in issue.suggested_fix:
            # Extract suggested filter
            parts = issue.suggested_fix.split('Suggested:')
            if len(parts) == 2:
                suggested_filter = parts[1].strip()
                
                # Find and replace filter in code
                old_filter_pattern = r"k\.startswith\(\([^)]+\)\)"
                code = re.sub(old_filter_pattern, f"k.startswith({suggested_filter})", code, count=1)
        
        return code
    
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
                
                logger.info("[OK] AI generated fixed code")
                logger.info(f"Fix: {fix_attempt.fix_description}")
                
                self.fix_history.append(fix_attempt)
                
                # Record in learning system if available
                if self.learning_system and execution_context:
                    self.learning_system.record_error(
                        strategy_name=bot_file.stem,
                        error_type=error_type,
                        error_message=error_message,
                        code_snippet=original_code[:500],  # First 500 chars
                        fix_successful=True,
                        fix_attempts=1,
                        user_description=execution_context.get('user_description'),
                        generated_params=execution_context.get('params')
                    )
                
                return True, fixed_code, fix_attempt
            else:
                fix_attempt.success = False
                fix_attempt.fix_description = "AI failed to generate fixed code"
                self.fix_history.append(fix_attempt)
                logger.error("AI failed to generate fixed code")
                
                # Record failure in learning system
                if self.learning_system:
                    self.learning_system.record_error(
                        strategy_name=bot_file.stem,
                        error_type=error_type,
                        error_message=error_message,
                        code_snippet=original_code[:500],
                        fix_successful=False,
                        fix_attempts=1
                    )
                
                return False, original_code, fix_attempt
        
        except Exception as e:
            fix_attempt.success = False
            fix_attempt.fix_description = f"Error during fix attempt: {str(e)}"
            self.fix_history.append(fix_attempt)
            logger.error(f"Failed to fix error: {e}")
            
            # Record exception in learning system
            if self.learning_system:
                self.learning_system.record_error(
                    strategy_name=bot_file.stem,
                    error_type=error_type,
                    error_message=f"{error_message}\n\nFix Exception: {str(e)}",
                    code_snippet=original_code[:500],
                    fix_successful=False,
                    fix_attempts=1
                )
            
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
        
        # Add specific instructions for encoding errors
        encoding_hint = ""
        if error_type == 'encoding_error' or 'charmap' in error_message.lower():
            encoding_hint = """

**CRITICAL FIX FOR ENCODING ERROR:**
The error 'charmap_encode' means there are emoji or unicode characters in print() statements.

FIND AND REPLACE ALL:
- ✓ → [OK] or SUCCESS
- ✅ → [OK] or SUCCESS
- ❌ → [ERROR] or FAILED
- ⚠️ → [WARNING]
- Any other emoji/unicode → Plain ASCII text

Search the ENTIRE file for print() statements and remove ALL emojis.
"""
        
        prompt = f"""
TASK: Fix the trading bot code that has an execution error.

ERROR TYPE: {error_type}
BOT FILE: {bot_file.name}

ORIGINAL ERROR:
```
{error_message}
```
{encoding_hint}

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
- CRITICAL: NEVER use 'from Data.data_manager' or 'from Trade.' - these are WRONG paths
- CORRECT imports for data loading:
  * from Backtest.data_loader import fetch_market_data, add_indicators
- CORRECT imports for SimBroker:
  * from Backtest.sim_broker import SimBroker
  * from Backtest.config import BacktestConfig
  * from Backtest.canonical_schema import create_signal, OrderSide, OrderAction, OrderType
- NEVER import from 'backtesting' or 'backtesting.py' library
- Add parent directory to path:
  ```python
  import sys
  from pathlib import Path
  parent_dir = Path(__file__).parent.parent
  if str(parent_dir) not in sys.path:
      sys.path.insert(0, str(parent_dir))
  ```
- Use fetch_market_data() to load market data dynamically
- Verify all imports exist and module paths are correct
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
        start_time = time.time()
        
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
                logger.info(f"\n[OK] SUCCESS! Bot executed successfully on attempt {attempt + 1}")
                
                # Record successful resolution in learning system
                if self.learning_system and self.fix_history:
                    resolution_time = time.time() - start_time
                    last_error = self.fix_history[-1]
                    self.learning_system.record_error(
                        strategy_name=bot_file.stem,
                        error_type=last_error.error_type,
                        error_message=last_error.original_error,
                        fix_successful=True,
                        fix_attempts=attempt + 1,
                        resolution_time_seconds=resolution_time
                    )
                
                return True, current_code, self.fix_history
            
            if not result.error:
                logger.warning("Execution failed but no error details available")
                return False, current_code, self.fix_history
            
            # Try to fix the error
            output_log = result.output_log or ""
            stderr_log = result.stderr_log or ""
            # Combine stdout and stderr for proper error classification
            combined_output = output_log + "\n" + stderr_log
            success, fixed_code, fix_record = self.fix_bot_error(
                bot_file=bot_file,
                error_output=combined_output,
                original_code=current_code,
                execution_context={
                    'symbol': result.test_symbol,
                    'period_days': result.test_period_days
                }
            )
            
            if not success:
                logger.error(f"Failed to fix error on attempt {attempt + 1}")
                
                # Record final failure in learning system
                if self.learning_system and self.fix_history:
                    resolution_time = time.time() - start_time
                    last_error = self.fix_history[-1]
                    self.learning_system.record_error(
                        strategy_name=bot_file.stem,
                        error_type=last_error.error_type,
                        error_message=last_error.original_error,
                        fix_successful=False,
                        fix_attempts=attempt + 1,
                        resolution_time_seconds=resolution_time
                    )
                
                break
            
            # Update code and write to file
            current_code = fixed_code
            bot_file.write_text(current_code, encoding='utf-8')
            logger.info(f"Updated bot file with fixes")
        
        logger.info(f"\n{'='*70}")
        logger.info(f"ERROR FIXING COMPLETE")
        logger.info(f"Total attempts: {len(self.fix_history)}")
        logger.info(f"Success: {'YES' if any(f.success for f in self.fix_history) else 'NO'}")
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
