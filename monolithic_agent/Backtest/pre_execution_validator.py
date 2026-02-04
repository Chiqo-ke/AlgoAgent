"""
Pre-Execution Strategy Validator
=================================

Static code analysis to catch common API errors BEFORE execution.
This prevents runtime errors by validating against SimBroker API specifications.

Usage:
    from pre_execution_validator import validate_strategy, ValidationReport
    
    # Validate file
    report = validate_strategy('path/to/strategy.py')
    if not report.is_valid:
        for error in report.errors:
            print(f"ERROR: {error}")
"""

import re
from typing import List, Tuple
from dataclasses import dataclass, field


@dataclass
class ValidationReport:
    """Validation results"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def __str__(self):
        lines = ["=" * 70, "STRATEGY VALIDATION REPORT", "=" * 70]
        lines.append("[PASSED]" if self.is_valid else "[FAILED]")
        
        if self.errors:
            lines.append(f"\nERRORS ({len(self.errors)}):")
            for i, err in enumerate(self.errors, 1):
                lines.append(f"  {i}. {err}")
        
        if self.warnings:
            lines.append(f"\nWARNINGS ({len(self.warnings)}):")
            for i, warn in enumerate(self.warnings, 1):
                lines.append(f"  {i}. {warn}")
        
        lines.append("=" * 70)
        return "\n".join(lines)


def validate_strategy(file_path: str = None, code: str = None) -> ValidationReport:
    """
    Validate strategy against SimBroker API specifications
    
    Args:
        file_path: Path to strategy file (mutually exclusive with code)
        code: Code string (mutually exclusive with file_path)
        
    Returns:
        ValidationReport with errors and warnings
    """
    if file_path:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
        except Exception as e:
            return ValidationReport(False, [f"Failed to read file: {e}"])
    
    if not code:
        return ValidationReport(False, ["No code provided"])
    
    errors = []
    warnings = []
    
    # 1. Validate imports
    _validate_imports(code, errors, warnings)
    
    # 2. Validate broker initialization
    _validate_broker_init(code, errors, warnings)
    
    # 3. Validate signal schema
    _validate_signals(code, errors, warnings)
    
    # 4. Validate method calls
    _validate_methods(code, errors, warnings)
    
    # 5. Validate market data
    _validate_market_data(code, errors, warnings)
    
    # 6. Validate indicator keys
    _validate_indicator_keys(code, errors, warnings)
    
    # 7. Validate comment-code consistency
    _validate_comment_consistency(code, errors, warnings)
    
    is_valid = len(errors) == 0
    return ValidationReport(is_valid, errors, warnings)


def _validate_imports(code: str, errors: List[str], warnings: List[str]):
    """Check import statements"""
    
    # Check for Django-triggering imports (FORBIDDEN)
    if re.search(r'from\s+Backtest\.', code):
        errors.append(
            "CRITICAL: Found 'from Backtest.*' imports which trigger Django initialization. "
            "Use direct imports: 'from sim_broker import SimBroker'"
        )
    
    # Required direct imports
    required_direct_imports = {
        'sim_broker': r'from\s+sim_broker\s+import\s+SimBroker',
        'config': r'from\s+config\s+import\s+BacktestConfig',
        'canonical_schema': r'from\s+canonical_schema\s+import',
        'data_loader': r'from\s+data_loader\s+import',
    }
    
    for name, pattern in required_direct_imports.items():
        if not re.search(pattern, code):
            warnings.append(f"Missing recommended import: 'from {name} import ...'")
    
    # Check path setup (should be parent.parent for codes/ directory)
    if 'parent.parent.parent' in code:
        errors.append(
            "CRITICAL: Wrong path depth! Use parent.parent (2 levels), not parent.parent.parent (3 levels)"
        )
    
    if 'parent.parent' not in code and 'parent.parent.parent' not in code:
        warnings.append("Missing path setup: parent_dir = Path(__file__).parent.parent")
    
    # Django settings not needed for direct imports
    if 'DJANGO_SETTINGS_MODULE' in code:
        warnings.append("Django settings found - may not be needed with direct imports")


def _validate_broker_init(code: str, errors: List[str], warnings: List[str]):
    """Check SimBroker initialization"""
    
    # Old API (direct parameters)
    if re.search(r'SimBroker\s*\(\s*symbol\s*=', code):
        errors.append(
            "Old API detected: SimBroker(symbol=...). "
            "Use: config = BacktestConfig(...); broker = SimBroker(config)"
        )
    
    # Check for BacktestConfig usage
    if 'BacktestConfig' not in code:
        warnings.append("BacktestConfig not found - ensure proper initialization")


def _validate_signals(code: str, errors: List[str], warnings: List[str]):
    """Check signal schema compliance"""
    
    # Invalid parameter names
    invalid_params = {
        'quantity': 'size',
        'reason': "meta: {'reason': ...}"
    }
    
    for invalid, correct in invalid_params.items():
        if re.search(rf"['\"]({invalid})['\"]\\s*:", code):
            errors.append(f"Invalid signal field '{invalid}' - use '{correct}'")
    
    # Invalid enum values
    invalid_sides = ['LONG', 'SHORT', 'OPEN', 'CLOSE']
    for side in invalid_sides:
        if re.search(rf"['\"]side['\"]\\s*:\\s*['\"]({side})['\"]", code):
            errors.append(f"Invalid side '{side}' - use 'BUY' or 'SELL'")
    
    invalid_actions = ['BUY', 'SELL', 'OPEN', 'CLOSE']
    for action in invalid_actions:
        if re.search(rf"['\"]action['\"]\\s*:\\s*['\"]({action})['\"]", code):
            errors.append(f"Invalid action '{action}' - use 'ENTRY' or 'EXIT'")
    
    # Check for signal_id
    if re.search(r"signal\s*=\s*{", code):
        if not re.search(r"['\"]signal_id['\"]\\s*:", code):
            warnings.append("Signals may be missing 'signal_id' field")


def _validate_methods(code: str, errors: List[str], warnings: List[str]):
    """Check method calls"""
    
    # Incorrect method names
    if 'get_metrics(' in code:
        errors.append(
            "Method 'get_metrics()' doesn't exist - use 'get_statistics()'"
        )
    
    # Check for signal submission
    if 'signal' in code.lower() and 'submit_signal' not in code:
        warnings.append("Signals created but not submitted - call broker.submit_signal()")


def _validate_market_data(code: str, errors: List[str], warnings: List[str]):
    """Check market data format"""
    
    # Look for step_to calls
    if 'step_to' in code:
        # Check for nested dict pattern
        if not re.search(r"{\s*['\"][A-Z]+['\"]\\s*:\\s*{", code):
            warnings.append(
                "Market data may not be nested dict - "
                "use: {'SYMBOL': {'open': ..., 'close': ...}}"
            )


def _validate_indicator_keys(code: str, errors: List[str], warnings: List[str]):
    """Validate indicator key access patterns"""
    
    # Detect mode
    is_streaming = 'stream=True' in code or ('load_market_data' in code and 'stream=False' not in code)
    
    if is_streaming:
        # Streaming mode: should use lowercase keys
        if re.search(r"\.get\(['\"]([A-Z]+_\d+)['\"]\)", code):
            errors.append(
                "CRITICAL: STREAMING mode detected but code uses UPPERCASE indicator keys. "
                "Data loader converts to lowercase in streaming mode. "
                "Use: symbol_data.get('ema_12') NOT symbol_data.get('EMA_12')"
            )
    else:
        # Batch mode: should use uppercase keys
        if re.search(r"\.get\(['\"]([a-z]+_\d+)['\"]\)", code):
            warnings.append(
                "BATCH mode detected but code uses lowercase indicator keys. "
                "DataFrame columns are UPPERCASE in batch mode. "
                "Use: df['EMA_12'] NOT df['ema_12']"
            )


def _validate_comment_consistency(code: str, errors: List[str], warnings: List[str]):
    """Check if comments match code implementation"""
    
    lines = code.split('\n')
    
    for i, line in enumerate(lines):
        if '#' not in line:
            continue
        
        # Check for uppercase/lowercase mentions
        if 'uppercase' in line.lower():
            # Check next few lines for contradictory lowercase usage
            next_lines = lines[i+1:min(i+6, len(lines))]
            for j, next_line in enumerate(next_lines):
                if '.get(' in next_line:
                    match = re.search(r"\.get\(['\"]([a-z_]+_\d+)['\"]\)", next_line)
                    if match:
                        warnings.append(
                            f"Line {i+1}: Comment says 'uppercase' but code uses lowercase: {next_line.strip()}"
                        )
        
        elif 'lowercase' in line.lower():
            # Check next few lines for contradictory uppercase usage
            next_lines = lines[i+1:min(i+6, len(lines))]
            for j, next_line in enumerate(next_lines):
                if '.get(' in next_line:
                    match = re.search(r"\.get\(['\"]([A-Z_]+_\d+)['\"]\)", next_line)
                    if match:
                        warnings.append(
                            f"Line {i+1}: Comment says 'lowercase' but code uses uppercase: {next_line.strip()}"
                        )
        
        # Check for FIX/TODO comments
        if 'FIX:' in line or 'TODO:' in line:
            warnings.append(
                f"Line {i+1}: Found FIX/TODO comment - code may be incomplete"
            )


# Convenience function for E2E test integration
def validate_generated_code(code: str) -> Tuple[bool, List[str]]:
    """
    Simple validation for integration with existing code
    
    Returns:
        Tuple of (is_valid, error_messages)
    """
    report = validate_strategy(code=code)
    return report.is_valid, report.errors


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python pre_execution_validator.py <file.py>")
        sys.exit(1)
    
    report = validate_strategy(sys.argv[1])
    print(report)
    sys.exit(0 if report.is_valid else 1)
