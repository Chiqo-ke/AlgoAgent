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
    
    is_valid = len(errors) == 0
    return ValidationReport(is_valid, errors, warnings)


def _validate_imports(code: str, errors: List[str], warnings: List[str]):
    """Check import statements"""
    
    # Required imports
    required = {
        'Backtest.sim_broker': r'from\s+Backtest\.sim_broker\s+import',
        'Backtest.config': r'from\s+Backtest\.config\s+import'
    }
    
    for name, pattern in required.items():
        if not re.search(pattern, code):
            errors.append(f"Missing required import: 'from {name} import ...'")
    
    # Forbidden patterns
    forbidden = [
        (r'from\s+simbroker\s+import', "Use 'from Backtest.sim_broker import'"),
        (r'from\s+sim_broker\s+import\s+(?!.*Backtest)', "Missing 'Backtest' prefix"),
        (r'import\s+simbroker\b', "Use 'from Backtest.sim_broker import SimBroker'"),
    ]
    
    for pattern, msg in forbidden:
        if re.search(pattern, code):
            errors.append(f"Forbidden import: {msg}")
    
    # Check path setup
    if 'parent.parent.parent' not in code:
        warnings.append("Missing path setup: parent_dir = Path(__file__).parent.parent.parent")
    
    # Check Django settings
    if 'DJANGO_SETTINGS_MODULE' not in code:
        warnings.append("Missing Django settings: os.environ['DJANGO_SETTINGS_MODULE'] = ...")


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
