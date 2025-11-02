"""
Structured Output Validator
============================

Enforces structured output from Gemini code generation with AST validation.

Features:
- Pydantic schema enforcement for LLM responses
- AST parsing and syntax validation
- Code safety checking (no dangerous imports)
- Automatic code formatting (black, isort)
- Metadata extraction and validation

Version: 1.0.0
"""

import ast
import re
import json
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
import logging
from pydantic import BaseModel, Field, validator

# Try to import code formatters
try:
    import black
    BLACK_AVAILABLE = True
except ImportError:
    BLACK_AVAILABLE = False
    logging.warning("black not installed - code formatting disabled")

try:
    import isort
    ISORT_AVAILABLE = True
except ImportError:
    ISORT_AVAILABLE = False
    logging.warning("isort not installed - import sorting disabled")

from canonical_schema_v2 import GeneratedCode

logger = logging.getLogger(__name__)


# ============================================================================
# CODE SAFETY CHECKER
# ============================================================================

class CodeSafetyChecker:
    """
    Check generated code for dangerous patterns
    """
    
    # Dangerous imports that should be blocked
    DANGEROUS_IMPORTS = {
        'os.system', 'subprocess.Popen', 'eval', 'exec', 'compile',
        '__import__', 'importlib', 'sys.modules',
        'socket', 'urllib', 'requests',  # Network access
        'shutil.rmtree', 'os.remove', 'os.rmdir',  # Destructive ops
        'pickle', 'marshal',  # Serialization risks
    }
    
    # Allowed imports for trading strategies
    ALLOWED_IMPORTS = {
        'pandas', 'numpy', 'datetime', 'typing', 'dataclasses',
        'backtesting', 'backtesting.lib', 'backtesting.test',
        'Data.data_fetcher', 'Data.indicator_calculator',
        'Backtest', 'Strategy',
        'pathlib.Path', 'logging', 'json', 'math', 'statistics'
    }
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialize safety checker
        
        Args:
            strict_mode: If True, only allow whitelisted imports
        """
        self.strict_mode = strict_mode
        self.violations: List[str] = []
    
    def check(self, code: str) -> tuple[bool, List[str]]:
        """
        Check code safety
        
        Args:
            code: Python code to check
            
        Returns:
            Tuple of (is_safe, violations)
        """
        self.violations = []
        
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            self.violations.append(f"Syntax error: {e}")
            return False, self.violations
        
        # Walk AST and check for violations
        for node in ast.walk(tree):
            # Check imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self._check_import(alias.name)
            
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    full_name = f"{module}.{alias.name}" if module else alias.name
                    self._check_import(full_name)
            
            # Check function calls that could be dangerous
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['eval', 'exec', 'compile', '__import__']:
                        self.violations.append(f"Dangerous function call: {node.func.id}")
        
        return len(self.violations) == 0, self.violations
    
    def _check_import(self, import_name: str):
        """Check if import is safe"""
        # Check against dangerous imports
        for dangerous in self.DANGEROUS_IMPORTS:
            if dangerous in import_name:
                self.violations.append(f"Dangerous import: {import_name}")
                return
        
        # In strict mode, check against allowed imports
        if self.strict_mode:
            allowed = False
            for allowed_import in self.ALLOWED_IMPORTS:
                if import_name.startswith(allowed_import):
                    allowed = True
                    break
            
            if not allowed:
                self.violations.append(f"Import not in whitelist: {import_name}")


# ============================================================================
# AST ANALYZER
# ============================================================================

class ASTAnalyzer:
    """
    Analyze Python code AST for metadata extraction
    """
    
    def __init__(self, code: str):
        """
        Initialize analyzer
        
        Args:
            code: Python code to analyze
        """
        self.code = code
        try:
            self.tree = ast.parse(code)
            self.valid = True
        except SyntaxError as e:
            self.tree = None
            self.valid = False
            self.error = str(e)
    
    def extract_classes(self) -> List[str]:
        """Extract class names"""
        if not self.valid:
            return []
        
        classes = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
        return classes
    
    def extract_functions(self) -> List[str]:
        """Extract function names"""
        if not self.valid:
            return []
        
        functions = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
        return functions
    
    def extract_imports(self) -> List[str]:
        """Extract import statements"""
        if not self.valid:
            return []
        
        imports = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}" if module else alias.name)
        return imports
    
    def find_main_class(self) -> Optional[str]:
        """Find main strategy class (inherits from Strategy)"""
        if not self.valid:
            return None
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                # Check if inherits from Strategy
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == 'Strategy':
                        return node.name
        
        return None


# ============================================================================
# CODE FORMATTER
# ============================================================================

class CodeFormatter:
    """
    Format Python code using black and isort
    """
    
    @staticmethod
    def format(code: str) -> tuple[str, bool]:
        """
        Format code
        
        Args:
            code: Python code to format
            
        Returns:
            Tuple of (formatted_code, success)
        """
        formatted = code
        success = True
        
        # Apply black formatting
        if BLACK_AVAILABLE:
            try:
                formatted = black.format_str(formatted, mode=black.Mode())
            except Exception as e:
                logger.warning(f"Black formatting failed: {e}")
                success = False
        
        # Apply isort
        if ISORT_AVAILABLE:
            try:
                formatted = isort.code(formatted)
            except Exception as e:
                logger.warning(f"Isort failed: {e}")
                success = False
        
        return formatted, success


# ============================================================================
# OUTPUT VALIDATOR
# ============================================================================

class OutputValidator:
    """
    Validate LLM output against expected schema
    """
    
    def __init__(self, strict_safety: bool = False):
        """
        Initialize validator
        
        Args:
            strict_safety: Enable strict import whitelist
        """
        self.safety_checker = CodeSafetyChecker(strict_mode=strict_safety)
        self.formatter = CodeFormatter()
    
    def validate_generated_code(
        self,
        llm_response: str,
        expected_schema: type[BaseModel] = GeneratedCode
    ) -> tuple[Optional[GeneratedCode], List[str]]:
        """
        Validate LLM response as generated code
        
        Args:
            llm_response: Raw LLM response (should be JSON)
            expected_schema: Pydantic schema to validate against
            
        Returns:
            Tuple of (validated_code, errors)
        """
        errors = []
        
        # Try to parse as JSON first
        try:
            data = json.loads(llm_response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code block
            json_match = re.search(r'```json\n(.*?)\n```', llm_response, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                except json.JSONDecodeError as e:
                    errors.append(f"Failed to parse JSON from markdown: {e}")
                    return None, errors
            else:
                errors.append("Response is not valid JSON and contains no JSON code block")
                return None, errors
        
        # Validate against schema
        try:
            generated_code = expected_schema(**data)
        except Exception as e:
            errors.append(f"Schema validation failed: {e}")
            return None, errors
        
        # Validate code syntax
        try:
            ast.parse(generated_code.code)
        except SyntaxError as e:
            errors.append(f"Code syntax error: {e}")
            return None, errors
        
        # Safety check
        is_safe, violations = self.safety_checker.check(generated_code.code)
        if not is_safe:
            errors.extend([f"Safety violation: {v}" for v in violations])
            return None, errors
        
        # Format code
        formatted_code, format_success = self.formatter.format(generated_code.code)
        if format_success:
            generated_code.code = formatted_code
        else:
            errors.append("Code formatting partially failed (non-fatal)")
        
        # Extract metadata
        analyzer = ASTAnalyzer(generated_code.code)
        
        # Update metadata
        if not generated_code.metadata:
            generated_code.metadata = {}
        
        generated_code.metadata.update({
            "classes": analyzer.extract_classes(),
            "functions": analyzer.extract_functions(),
            "imports": analyzer.extract_imports(),
            "main_class": analyzer.find_main_class(),
            "lines_of_code": len(generated_code.code.split('\n'))
        })
        
        # Update entrypoint if not set
        if not generated_code.entrypoint:
            main_class = analyzer.find_main_class()
            if main_class:
                generated_code.entrypoint = main_class
        
        return generated_code, errors
    
    def validate_code_string(
        self,
        code: str,
        format_code: bool = True
    ) -> tuple[str, List[str]]:
        """
        Validate and optionally format raw code string
        
        Args:
            code: Python code string
            format_code: Whether to format the code
            
        Returns:
            Tuple of (validated_code, errors)
        """
        errors = []
        
        # Check syntax
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(f"Syntax error: {e}")
            return code, errors
        
        # Safety check
        is_safe, violations = self.safety_checker.check(code)
        if not is_safe:
            errors.extend([f"Safety violation: {v}" for v in violations])
        
        # Format if requested
        if format_code and not errors:
            formatted, success = self.formatter.format(code)
            if success:
                code = formatted
            else:
                errors.append("Formatting failed (non-fatal)")
        
        return code, errors


# ============================================================================
# RESPONSE SCHEMAS FOR GEMINI
# ============================================================================

def get_code_generation_prompt_schema() -> Dict[str, Any]:
    """
    Get JSON schema to include in Gemini prompt for structured output
    
    Returns:
        JSON schema dict
    """
    return {
        "type": "object",
        "required": ["code", "entrypoint", "dependencies"],
        "properties": {
            "code": {
                "type": "string",
                "description": "Complete Python code for the strategy"
            },
            "language": {
                "type": "string",
                "enum": ["python"],
                "default": "python"
            },
            "entrypoint": {
                "type": "string",
                "description": "Main class or function name (e.g., 'RSIStrategy')"
            },
            "dependencies": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of required packages (e.g., ['backtesting', 'pandas'])"
            },
            "files": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"}
                    }
                },
                "description": "Additional files if multi-file strategy"
            },
            "metadata": {
                "type": "object",
                "description": "Additional metadata about the generated code"
            }
        }
    }


def get_fix_generation_prompt_schema() -> Dict[str, Any]:
    """
    Get JSON schema for fix generation responses
    
    Returns:
        JSON schema dict
    """
    return {
        "type": "object",
        "required": ["fixed_code", "explanation"],
        "properties": {
            "fixed_code": {
                "type": "string",
                "description": "Complete fixed Python code"
            },
            "explanation": {
                "type": "string",
                "description": "Explanation of what was fixed and why"
            },
            "changes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "line_number": {"type": "integer"},
                        "old_code": {"type": "string"},
                        "new_code": {"type": "string"},
                        "reason": {"type": "string"}
                    }
                }
            }
        }
    }


# CLI for testing validation
if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Validate generated code")
    parser.add_argument("--file", type=str, help="Python file to validate")
    parser.add_argument("--json", type=str, help="JSON response to validate")
    parser.add_argument("--strict", action="store_true", help="Enable strict safety checks")
    parser.add_argument("--format", action="store_true", help="Format the code")
    parser.add_argument("--output", type=str, help="Output file for formatted code")
    
    args = parser.parse_args()
    
    validator = OutputValidator(strict_safety=args.strict)
    
    if args.file:
        # Validate Python file
        with open(args.file, 'r') as f:
            code = f.read()
        
        validated_code, errors = validator.validate_code_string(code, format_code=args.format)
        
        if errors:
            print(f"✗ Validation errors ({len(errors)}):")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
        else:
            print(f"✓ Code is valid")
            
            if args.format:
                if args.output:
                    with open(args.output, 'w') as f:
                        f.write(validated_code)
                    print(f"Formatted code written to {args.output}")
                else:
                    print("\n--- FORMATTED CODE ---")
                    print(validated_code)
    
    elif args.json:
        # Validate JSON response
        with open(args.json, 'r') as f:
            response = f.read()
        
        generated_code, errors = validator.validate_generated_code(response)
        
        if errors:
            print(f"✗ Validation errors ({len(errors)}):")
            for error in errors:
                print(f"  - {error}")
            
            if generated_code:
                print("\n⚠️  Partial validation - some non-fatal errors")
            else:
                sys.exit(1)
        else:
            print(f"✓ Generated code is valid")
        
        if generated_code:
            print(f"\nMetadata:")
            print(f"  Entrypoint: {generated_code.entrypoint}")
            print(f"  Dependencies: {', '.join(generated_code.dependencies)}")
            print(f"  Classes: {', '.join(generated_code.metadata.get('classes', []))}")
            print(f"  Functions: {', '.join(generated_code.metadata.get('functions', []))}")
            print(f"  Lines of code: {generated_code.metadata.get('lines_of_code', 0)}")
            
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(generated_code.code)
                print(f"\nCode written to {args.output}")
    
    else:
        parser.print_help()
