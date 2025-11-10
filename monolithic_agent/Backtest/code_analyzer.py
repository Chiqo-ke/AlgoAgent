"""
Code Analyzer and Auto-Fixer
=============================

Analyzes Python code errors and suggests/applies fixes automatically.

Features:
- Pattern-based error detection
- Common fix templates
- AST-based code analysis
- Automatic import fixing
- Syntax error correction

Version: 1.0.0
"""

import ast
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class CodeFix:
    """Represents a code fix"""
    error_type: str
    original_line: str
    fixed_line: str
    line_number: Optional[int]
    explanation: str


class CodeAnalyzer:
    """
    Analyze code and suggest fixes for common errors
    """
    
    def __init__(self):
        # Common fix patterns
        self.fix_patterns = self._load_fix_patterns()
    
    def _load_fix_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load common error patterns and their fixes"""
        return {
            "ModuleNotFoundError": [
                {
                    "pattern": r"No module named '(Backtest|Data|Strategy)'",
                    "fix_template": """# Add parent directory to path
import sys
from pathlib import Path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
""",
                    "insert_location": "top",
                    "explanation": "Add parent directory to sys.path for module imports"
                },
                {
                    "pattern": r"No module named 'backtesting'",
                    "fix_template": "# Install: pip install backtesting\n",
                    "insert_location": "comment",
                    "explanation": "Install backtesting.py package"
                }
            ],
            "NameError": [
                {
                    "pattern": r"name '(\w+)' is not defined",
                    "suggestions": [
                        "Check if variable is initialized",
                        "Check for typos in variable name",
                        "Verify import statements"
                    ]
                }
            ],
            "AttributeError": [
                {
                    "pattern": r"'(\w+)' object has no attribute '(\w+)'",
                    "suggestions": [
                        "Check object type",
                        "Verify attribute name spelling",
                        "Check documentation for correct attribute"
                    ]
                }
            ],
            "TypeError": [
                {
                    "pattern": r"Cannot index by location index with a non-integer key",
                    "fix_template": "df.columns = df.columns.get_level_values(0)",
                    "explanation": "Flatten MultiIndex columns from yfinance"
                },
                {
                    "pattern": r"unsupported operand type",
                    "suggestions": [
                        "Check data types of operands",
                        "Convert types explicitly (int(), float(), str())"
                    ]
                }
            ],
            "KeyError": [
                {
                    "pattern": r"'(Open|High|Low|Close|Volume)'",
                    "fix_template": """# Rename columns to uppercase OHLCV
df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
""",
                    "explanation": "Standardize OHLCV column names"
                }
            ],
            "SyntaxError": [
                {
                    "pattern": r"invalid syntax",
                    "suggestions": [
                        "Check for missing colons (:)",
                        "Check for unmatched parentheses/brackets",
                        "Verify indentation"
                    ]
                }
            ],
            "IndentationError": [
                {
                    "pattern": r"unexpected indent|unindent",
                    "suggestions": [
                        "Check for mixed tabs and spaces",
                        "Verify consistent indentation (4 spaces recommended)"
                    ]
                }
            ]
        }
    
    def analyze_error(self, error_dict: Dict[str, Any]) -> List[CodeFix]:
        """
        Analyze an error and suggest fixes
        
        Args:
            error_dict: Error dictionary from ExecutionResult
                {type, message, file, line, traceback}
        
        Returns:
            List of possible CodeFix objects
        """
        error_type = error_dict.get("type", "")
        error_message = error_dict.get("message", "")
        
        fixes = []
        
        # Check patterns for this error type
        if error_type in self.fix_patterns:
            for pattern_info in self.fix_patterns[error_type]:
                pattern = pattern_info.get("pattern", "")
                
                if re.search(pattern, error_message):
                    # Found matching pattern
                    fix_template = pattern_info.get("fix_template")
                    
                    if fix_template:
                        fixes.append(CodeFix(
                            error_type=error_type,
                            original_line="",
                            fixed_line=fix_template,
                            line_number=error_dict.get("line"),
                            explanation=pattern_info.get("explanation", "")
                        ))
                    else:
                        # Just suggestions
                        suggestions = pattern_info.get("suggestions", [])
                        logger.info(f"Suggestions for {error_type}: {suggestions}")
        
        return fixes
    
    def auto_fix_code(self, code: str, errors: List[Dict[str, Any]]) -> Tuple[str, List[CodeFix]]:
        """
        Automatically fix code based on error analysis
        
        Args:
            code: Original source code
            errors: List of error dictionaries
        
        Returns:
            (fixed_code, applied_fixes)
        """
        applied_fixes = []
        lines = code.split('\n')
        
        # Analyze each error
        for error in errors:
            fixes = self.analyze_error(error)
            
            for fix in fixes:
                # Apply fix based on type
                if "sys.path" in fix.fixed_line:
                    # Add import fix at top
                    if not self._has_path_setup(code):
                        lines = fix.fixed_line.split('\n') + [''] + lines
                        applied_fixes.append(fix)
                
                elif "df.columns = df.columns.get_level_values" in fix.fixed_line:
                    # Add after data fetching
                    insert_pos = self._find_data_fetch_line(lines)
                    if insert_pos >= 0:
                        lines.insert(insert_pos + 1, fix.fixed_line)
                        lines.insert(insert_pos + 2, '')
                        applied_fixes.append(fix)
                
                elif "df.columns = ['Open'" in fix.fixed_line:
                    # Add after data loading
                    insert_pos = self._find_data_fetch_line(lines)
                    if insert_pos >= 0:
                        lines.insert(insert_pos + 1, fix.fixed_line)
                        lines.insert(insert_pos + 2, '')
                        applied_fixes.append(fix)
        
        fixed_code = '\n'.join(lines)
        return fixed_code, applied_fixes
    
    def _has_path_setup(self, code: str) -> bool:
        """Check if sys.path setup already exists"""
        return "sys.path" in code and "parent" in code
    
    def _find_data_fetch_line(self, lines: List[str]) -> int:
        """Find line where data is fetched/loaded"""
        patterns = [
            r"fetch_and_prepare_data",
            r"fetch_historical_data",
            r"yf\.download",
            r"pd\.read_csv"
        ]
        
        for i, line in enumerate(lines):
            for pattern in patterns:
                if re.search(pattern, line):
                    return i
        
        return -1
    
    def check_syntax(self, code: str) -> Tuple[bool, Optional[str]]:
        """
        Check if code has syntax errors
        
        Returns:
            (is_valid, error_message)
        """
        try:
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            return False, f"Line {e.lineno}: {e.msg}"
        except Exception as e:
            return False, str(e)
    
    def suggest_improvements(self, code: str) -> List[str]:
        """
        Suggest code improvements (style, best practices)
        
        Returns:
            List of suggestions
        """
        suggestions = []
        
        # Check for common issues
        if "import *" in code:
            suggestions.append("Avoid wildcard imports (import *), use specific imports")
        
        if re.search(r"except:", code) and "except Exception" not in code:
            suggestions.append("Use specific exception types instead of bare except:")
        
        if "print(" in code and "logger" not in code:
            suggestions.append("Consider using logging instead of print() for production code")
        
        if not re.search(r'""".*?"""', code, re.DOTALL):
            suggestions.append("Add docstrings to document your code")
        
        # Check for hardcoded values
        if re.search(r'\d+\.\d+', code) and "=" not in code[:100]:
            suggestions.append("Consider making magic numbers into named constants")
        
        return suggestions
    
    def extract_imports(self, code: str) -> List[str]:
        """Extract all import statements from code"""
        imports = []
        
        for line in code.split('\n'):
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                imports.append(line)
        
        return imports
    
    def validate_strategy_structure(self, code: str) -> Dict[str, Any]:
        """
        Validate backtesting.py strategy structure
        
        Returns:
            {valid: bool, issues: List[str], has_required: Dict[str, bool]}
        """
        issues = []
        has_required = {
            "Strategy_import": False,
            "Strategy_class": False,
            "init_method": False,
            "next_method": False,
            "run_function": False
        }
        
        # Check imports
        if "from backtesting import" in code and "Strategy" in code:
            has_required["Strategy_import"] = True
        else:
            issues.append("Missing: from backtesting import Backtest, Strategy")
        
        # Check Strategy class
        if re.search(r"class \w+\(Strategy\):", code):
            has_required["Strategy_class"] = True
        else:
            issues.append("Missing: Strategy class definition")
        
        # Check init method
        if re.search(r"def init\(self\):", code):
            has_required["init_method"] = True
        else:
            issues.append("Missing: init() method in Strategy class")
        
        # Check next method
        if re.search(r"def next\(self\):", code):
            has_required["next_method"] = True
        else:
            issues.append("Missing: next() method in Strategy class")
        
        # Check run function
        if re.search(r"def run_backtest\(\):", code):
            has_required["run_function"] = True
        else:
            issues.append("Missing: run_backtest() function")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "has_required": has_required
        }


def analyze_and_fix(code: str, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Convenience function to analyze and fix code
    
    Args:
        code: Source code
        errors: List of error dictionaries
    
    Returns:
        {
            fixed_code: str,
            applied_fixes: List[CodeFix],
            remaining_issues: List[str],
            suggestions: List[str]
        }
    """
    analyzer = CodeAnalyzer()
    
    # Auto-fix
    fixed_code, applied_fixes = analyzer.auto_fix_code(code, errors)
    
    # Check syntax
    is_valid, syntax_error = analyzer.check_syntax(fixed_code)
    
    # Get suggestions
    suggestions = analyzer.suggest_improvements(fixed_code)
    
    # Validate structure
    structure = analyzer.validate_strategy_structure(fixed_code)
    
    return {
        "fixed_code": fixed_code,
        "applied_fixes": applied_fixes,
        "syntax_valid": is_valid,
        "syntax_error": syntax_error,
        "structure_issues": structure["issues"],
        "suggestions": suggestions
    }


if __name__ == "__main__":
    # Test the analyzer
    logging.basicConfig(level=logging.INFO)
    
    print("Testing CodeAnalyzer...")
    print("="*80)
    
    # Test error analysis
    test_errors = [
        {
            "type": "ModuleNotFoundError",
            "message": "No module named 'Backtest'",
            "file": "test.py",
            "line": 5
        },
        {
            "type": "TypeError",
            "message": "Cannot index by location index with a non-integer key",
            "file": "test.py",
            "line": 20
        }
    ]
    
    test_code = """
from backtesting import Backtest, Strategy

class MyStrategy(Strategy):
    def init(self):
        self.sma = self.I(SMA, self.data.Close, 20)
    
    def next(self):
        if not self.position:
            self.buy()

def run_backtest():
    df = fetch_and_prepare_data('AAPL', '2020-01-01', '2024-01-01')
    bt = Backtest(df, MyStrategy, cash=10000)
    stats = bt.run()
    print(stats)
"""
    
    result = analyze_and_fix(test_code, test_errors)
    
    print("\nOriginal code:")
    print("-"*80)
    print(test_code)
    
    print("\n\nFixed code:")
    print("-"*80)
    print(result["fixed_code"])
    
    print("\n\nApplied fixes:")
    print("-"*80)
    for fix in result["applied_fixes"]:
        print(f"  - {fix.error_type}: {fix.explanation}")
    
    print("\n\nSuggestions:")
    print("-"*80)
    for suggestion in result["suggestions"]:
        print(f"  - {suggestion}")
    
    print("\n\nStructure issues:")
    print("-"*80)
    for issue in result["structure_issues"]:
        print(f"  - {issue}")
