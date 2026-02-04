"""
Diagnostic Logger - Add comprehensive logging to bot code for debugging
=======================================================================

This module injects diagnostic logging into bot code to help identify
issues before attempting fixes. It adds logging at strategic points:

1. Function entry/exit points
2. Variable assignments and state changes
3. Data processing steps
4. Indicator calculations
5. Trading logic decisions
6. Error-prone operations (file I/O, API calls, etc.)

The diagnostic logs help understand:
- Which parts of the code are actually executing
- What values variables have at each step
- Where the execution stops or fails
- What the state is before an error occurs

This enables targeted, intelligent fixes rather than blind attempts.

Version: 1.0.0
Last updated: 2026-01-28
"""

import ast
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DiagnosticInjectionPoint:
    """Represents a point where diagnostic logging should be injected"""
    line_number: int
    context: str  # 'function_entry', 'function_exit', 'variable_assignment', 'loop', 'condition', etc.
    code_snippet: str
    log_statement: str
    priority: int  # Higher priority = more important to log


class DiagnosticLogInjector:
    """Inject diagnostic logging into Python code"""
    
    def __init__(self, verbose: bool = True):
        """
        Initialize diagnostic log injector
        
        Args:
            verbose: Enable detailed logging during injection
        """
        self.verbose = verbose
        self.injection_points: List[DiagnosticInjectionPoint] = []
    
    def inject_logging(self, code: str, bot_name: str = "bot") -> str:
        """
        Inject diagnostic logging into bot code
        
        Args:
            code: Original bot code
            bot_name: Name of the bot (for log messages)
        
        Returns:
            Code with diagnostic logging injected
        """
        try:
            tree = ast.parse(code)
            self.injection_points = []
            
            # Analyze the AST to find injection points
            self._analyze_ast(tree, bot_name)
            
            # Inject logging statements
            logged_code = self._inject_logs_into_code(code, bot_name)
            
            # Validate the injected code can be parsed
            try:
                ast.parse(logged_code)
            except SyntaxError as validation_error:
                logger.error(f"Injected code has syntax error: {validation_error}")
                logger.warning("Returning original code without logging injection")
                return code
            
            if self.verbose:
                logger.info(f"Injected {len(self.injection_points)} diagnostic log points")
            
            return logged_code
            
        except SyntaxError as e:
            logger.error(f"Syntax error in code, cannot inject logging: {e}")
            return code
        except Exception as e:
            logger.error(f"Error injecting diagnostic logging: {e}")
            return code
    
    def _analyze_ast(self, tree: ast.AST, bot_name: str):
        """Analyze AST and identify injection points"""
        
        for node in ast.walk(tree):
            # Function definitions
            if isinstance(node, ast.FunctionDef):
                self._add_function_logging(node, bot_name)
            
            # Class definitions
            elif isinstance(node, ast.ClassDef):
                self._add_class_logging(node, bot_name)
            
            # Variable assignments
            elif isinstance(node, ast.Assign):
                self._add_assignment_logging(node, bot_name)
            
            # Loop statements
            elif isinstance(node, (ast.For, ast.While)):
                self._add_loop_logging(node, bot_name)
            
            # Conditional statements
            elif isinstance(node, ast.If):
                self._add_condition_logging(node, bot_name)
            
            # Try-except blocks
            elif isinstance(node, ast.Try):
                self._add_exception_logging(node, bot_name)
            
            # Function calls (especially important ones)
            elif isinstance(node, ast.Call):
                self._add_call_logging(node, bot_name)
    
    def _add_function_logging(self, node: ast.FunctionDef, bot_name: str):
        """Add logging for function entry/exit"""
        func_name = node.name
        
        # Skip dunder methods except __init__
        if func_name.startswith('__') and func_name != '__init__':
            return
        
        # Function entry
        entry_log = f'logger.info("[DIAG] Entering function: {func_name}")'
        self.injection_points.append(
            DiagnosticInjectionPoint(
                line_number=node.lineno,
                context='function_entry',
                code_snippet=f"def {func_name}(...)",
                log_statement=entry_log,
                priority=8
            )
        )
        
        # Function exit (for return statements)
        for child in ast.walk(node):
            if isinstance(child, ast.Return):
                exit_log = f'logger.info("[DIAG] Exiting function: {func_name} with return value")'
                self.injection_points.append(
                    DiagnosticInjectionPoint(
                        line_number=child.lineno,
                        context='function_exit',
                        code_snippet=f"return ...",
                        log_statement=exit_log,
                        priority=7
                    )
                )
    
    def _add_class_logging(self, node: ast.ClassDef, bot_name: str):
        """Add logging for class definition"""
        class_name = node.name
        log_stmt = f'logger.info("[DIAG] Initializing class: {class_name}")'
        
        self.injection_points.append(
            DiagnosticInjectionPoint(
                line_number=node.lineno,
                context='class_definition',
                code_snippet=f"class {class_name}:",
                log_statement=log_stmt,
                priority=6
            )
        )
    
    def _add_assignment_logging(self, node: ast.Assign, bot_name: str):
        """Add logging for important variable assignments"""
        # Only log assignments that look important
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id
                
                # Log data-related, indicator-related, or config-related assignments
                if any(keyword in var_name.lower() for keyword in 
                       ['data', 'df', 'price', 'indicator', 'signal', 'strategy', 
                        'params', 'config', 'result', 'trade', 'position']):
                    
                    log_stmt = f'logger.info(f"[DIAG] Assigned {{type({var_name})}} to variable: {var_name}")'
                    self.injection_points.append(
                        DiagnosticInjectionPoint(
                            line_number=node.lineno,
                            context='variable_assignment',
                            code_snippet=f"{var_name} = ...",
                            log_statement=log_stmt,
                            priority=5
                        )
                    )
    
    def _add_loop_logging(self, node: ast.For | ast.While, bot_name: str):
        """Add logging for loop entry"""
        loop_type = "for" if isinstance(node, ast.For) else "while"
        log_stmt = f'logger.info("[DIAG] Entering {loop_type} loop")'
        
        self.injection_points.append(
            DiagnosticInjectionPoint(
                line_number=node.lineno,
                context='loop_entry',
                code_snippet=f"{loop_type} ...",
                log_statement=log_stmt,
                priority=6
            )
        )
    
    def _add_condition_logging(self, node: ast.If, bot_name: str):
        """Add logging for conditional branches"""
        log_stmt = f'logger.info("[DIAG] Evaluating conditional statement")'
        
        self.injection_points.append(
            DiagnosticInjectionPoint(
                line_number=node.lineno,
                context='condition',
                code_snippet="if ...",
                log_statement=log_stmt,
                priority=4
            )
        )
    
    def _add_exception_logging(self, node: ast.Try, bot_name: str):
        """Add logging for try-except blocks"""
        log_stmt = f'logger.info("[DIAG] Entering try block")'
        
        self.injection_points.append(
            DiagnosticInjectionPoint(
                line_number=node.lineno,
                context='exception_handling',
                code_snippet="try:",
                log_statement=log_stmt,
                priority=9
            )
        )
    
    def _add_call_logging(self, node: ast.Call, bot_name: str):
        """Add logging for important function calls"""
        if isinstance(node.func, ast.Attribute):
            method_name = node.func.attr
            
            # Log calls to important methods
            if any(keyword in method_name.lower() for keyword in
                   ['load', 'fetch', 'calculate', 'compute', 'process', 
                    'execute', 'run', 'update', 'save']):
                
                log_stmt = f'logger.info("[DIAG] Calling method: {method_name}")'
                self.injection_points.append(
                    DiagnosticInjectionPoint(
                        line_number=node.lineno,
                        context='method_call',
                        code_snippet=f"...{method_name}(...)",
                        log_statement=log_stmt,
                        priority=7
                    )
                )
        
        elif isinstance(node.func, ast.Name):
            func_name = node.func.id
            
            # Log calls to important functions
            if any(keyword in func_name.lower() for keyword in
                   ['load', 'fetch', 'calculate', 'compute', 'process']):
                
                log_stmt = f'logger.info("[DIAG] Calling function: {func_name}")'
                self.injection_points.append(
                    DiagnosticInjectionPoint(
                        line_number=node.lineno,
                        context='function_call',
                        code_snippet=f"{func_name}(...)",
                        log_statement=log_stmt,
                        priority=7
                    )
                )
    
    def _inject_logs_into_code(self, code: str, bot_name: str) -> str:
        """
        Inject logging statements into the actual code
        
        Strategy:
        1. Add logging import at the top
        2. Insert log statements at identified points
        3. Maintain proper indentation
        """
        lines = code.split('\n')
        
        # Add logging import if not present
        if 'import logging' not in code:
            # Find first non-comment, non-docstring line
            insert_line = 0
            in_docstring = False
            
            for i, line in enumerate(lines):
                stripped = line.strip()
                if '"""' in stripped or "'''" in stripped:
                    in_docstring = not in_docstring
                    continue
                if not in_docstring and stripped and not stripped.startswith('#'):
                    insert_line = i
                    break
            
            lines.insert(insert_line, 'import logging')
            lines.insert(insert_line + 1, 'logger = logging.getLogger(__name__)')
            lines.insert(insert_line + 2, '')
        
        # Sort injection points by line number (reverse order to maintain line numbers)
        sorted_points = sorted(self.injection_points, key=lambda p: p.line_number, reverse=True)
        
        # Inject log statements
        for point in sorted_points:
            line_idx = point.line_number - 1  # Convert to 0-based index
            
            if line_idx < 0 or line_idx >= len(lines):
                continue
            
            # Get indentation of the target line
            target_line = lines[line_idx]
            indent = len(target_line) - len(target_line.lstrip())
            indent_str = ' ' * indent
            
            # For function entry, insert after the function definition line
            if point.context == 'function_entry':
                # Skip to next non-docstring line
                insert_idx = line_idx + 1
                while insert_idx < len(lines):
                    line = lines[insert_idx].strip()
                    if line and not line.startswith('"""') and not line.startswith("'''"):
                        # Check if this is inside a docstring
                        if '"""' not in line and "'''" not in line:
                            break
                    insert_idx += 1
                
                # Use indentation of next line
                if insert_idx < len(lines):
                    next_line = lines[insert_idx]
                    indent = len(next_line) - len(next_line.lstrip())
                    indent_str = ' ' * indent
                
                lines.insert(insert_idx, f"{indent_str}{point.log_statement}")
            
            # For other contexts, insert before the line
            else:
                lines.insert(line_idx, f"{indent_str}{point.log_statement}")
        
        return '\n'.join(lines)
    
    def get_injection_summary(self) -> Dict[str, Any]:
        """Get summary of injected logging points"""
        context_counts = {}
        for point in self.injection_points:
            context_counts[point.context] = context_counts.get(point.context, 0) + 1
        
        return {
            'total_points': len(self.injection_points),
            'by_context': context_counts,
            'high_priority_count': sum(1 for p in self.injection_points if p.priority >= 7)
        }


def create_diagnostic_version(
    bot_file: Path,
    output_file: Optional[Path] = None
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Create a diagnostic version of a bot file with logging injected
    
    Args:
        bot_file: Path to original bot file
        output_file: Optional path for diagnostic version (default: bot_file_diagnostic.py)
    
    Returns:
        Tuple of (success, diagnostic_file_path, injection_summary)
    """
    try:
        # Read original code
        original_code = bot_file.read_text(encoding='utf-8')
        
        # Inject logging
        injector = DiagnosticLogInjector(verbose=True)
        diagnostic_code = injector.inject_logging(original_code, bot_file.stem)
        
        # Determine output file
        if output_file is None:
            output_file = bot_file.parent / f"{bot_file.stem}_diagnostic.py"
        
        # Write diagnostic version
        output_file.write_text(diagnostic_code, encoding='utf-8')
        
        summary = injector.get_injection_summary()
        logger.info(f"Created diagnostic version: {output_file}")
        logger.info(f"Injection summary: {summary}")
        
        return True, str(output_file), summary
    
    except Exception as e:
        logger.error(f"Failed to create diagnostic version: {e}")
        return False, "", {}


if __name__ == "__main__":
    # Test the diagnostic logger
    test_code = """
import pandas as pd

class Strategy:
    def __init__(self, params):
        self.params = params
    
    def calculate_indicators(self, data):
        data['SMA'] = data['close'].rolling(window=20).mean()
        return data
    
    def generate_signals(self, data):
        for i in range(len(data)):
            if data['close'][i] > data['SMA'][i]:
                print("Buy signal")
        return data
"""
    
    injector = DiagnosticLogInjector(verbose=True)
    logged_code = injector.inject_logging(test_code, "test_strategy")
    
    print("Original code:")
    print("="*70)
    print(test_code)
    print("\n\nCode with diagnostic logging:")
    print("="*70)
    print(logged_code)
    print("\n\nInjection summary:")
    print("="*70)
    print(injector.get_injection_summary())
