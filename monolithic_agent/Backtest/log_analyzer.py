"""
Log Analyzer - Analyze diagnostic logs to identify bot issues
==============================================================

This module analyzes diagnostic logs from instrumented bots to identify
specific issues and guide targeted fixes.

Features:
- Parse diagnostic logs
- Identify execution flow problems
- Detect data issues
- Spot logic errors
- Generate detailed diagnostic reports
- Suggest specific fixes based on findings

Last updated: 2026-02-01
Version: 1.0.0
"""

import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class IssueType(Enum):
    """Types of issues that can be identified"""
    IMPORT_ERROR = "import_error"
    DATA_FETCH_ERROR = "data_fetch_error"
    MISSING_DATA = "missing_data"
    CALCULATION_ERROR = "calculation_error"
    LOGIC_ERROR = "logic_error"
    RUNTIME_ERROR = "runtime_error"
    NO_EXECUTION = "no_execution"
    INCOMPLETE_EXECUTION = "incomplete_execution"
    FUNCTION_NOT_CALLED = "function_not_called"
    VARIABLE_ERROR = "variable_error"


class IssueSeverity(Enum):
    """Severity levels for identified issues"""
    CRITICAL = "critical"  # Bot cannot run
    HIGH = "high"  # Major functionality broken
    MEDIUM = "medium"  # Some features not working
    LOW = "low"  # Minor issues


@dataclass
class DiagnosticIssue:
    """Represents an identified issue from diagnostic logs"""
    issue_type: IssueType
    severity: IssueSeverity
    description: str
    evidence: List[str] = field(default_factory=list)  # Log lines that prove the issue
    line_number: Optional[int] = None
    function_name: Optional[str] = None
    suggested_fix: Optional[str] = None
    confidence: float = 0.0  # 0.0 to 1.0


@dataclass
class DiagnosticReport:
    """Complete diagnostic report from log analysis"""
    success: bool
    execution_completed: bool
    issues: List[DiagnosticIssue] = field(default_factory=list)
    execution_timeline: List[str] = field(default_factory=list)
    functions_executed: List[str] = field(default_factory=list)
    functions_not_executed: List[str] = field(default_factory=list)
    last_successful_line: Optional[int] = None
    error_message: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)


class LogAnalyzer:
    """Analyze diagnostic logs to identify bot issues"""
    
    def __init__(self, verbose: bool = True):
        """
        Initialize log analyzer
        
        Args:
            verbose: Enable detailed logging during analysis
        """
        self.verbose = verbose
        self.patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for log analysis"""
        return {
            'function_entry': re.compile(r'\[DIAG\] Entering function: (.+)'),
            'function_exit': re.compile(r'\[DIAG\] Exiting function: (.+)'),
            'import_error': re.compile(r'ImportError|ModuleNotFoundError|No module named'),
            'attribute_error': re.compile(r'AttributeError: (.+)'),
            'key_error': re.compile(r'KeyError: (.+)'),
            'type_error': re.compile(r'TypeError: (.+)'),
            'value_error': re.compile(r'ValueError: (.+)'),
            'name_error': re.compile(r'NameError: (.+)'),
            'index_error': re.compile(r'IndexError: (.+)'),
            'data_fetch': re.compile(r'\[DIAG\] Calling (method|function): (fetch|load|download|get_data)'),
            'calculation': re.compile(r'\[DIAG\] (Assigned|Calling).*?(calculate|compute|indicator)'),
            'variable_assign': re.compile(r'\[DIAG\] Assigned .+ to variable: (.+)'),
            'exception': re.compile(r'Exception: (.+)'),
            'traceback': re.compile(r'Traceback \(most recent call last\)'),
            'line_number': re.compile(r'line (\d+)'),
        }
    
    def analyze_log_file(self, log_file: Path) -> DiagnosticReport:
        """
        Analyze a diagnostic log file
        
        Args:
            log_file: Path to diagnostic log file
            
        Returns:
            Diagnostic report with identified issues
        """
        if not log_file.exists():
            logger.error(f"Log file not found: {log_file}")
            return DiagnosticReport(
                success=False,
                execution_completed=False,
                error_message=f"Log file not found: {log_file}"
            )
        
        # Read log content
        log_content = log_file.read_text(encoding='utf-8')
        
        return self.analyze_log_content(log_content)
    
    def analyze_log_content(self, log_content: str) -> DiagnosticReport:
        """
        Analyze log content
        
        Args:
            log_content: Content of diagnostic log
            
        Returns:
            Diagnostic report with identified issues
        """
        report = DiagnosticReport(success=True, execution_completed=False)
        log_lines = log_content.split('\n')
        
        # Track execution flow
        for line in log_lines:
            # Track function calls
            if match := self.patterns['function_entry'].search(line):
                func_name = match.group(1)
                report.functions_executed.append(func_name)
                report.execution_timeline.append(f"→ {func_name}")
            
            elif match := self.patterns['function_exit'].search(line):
                func_name = match.group(1)
                report.execution_timeline.append(f"← {func_name}")
        
        # Detect errors
        self._detect_import_errors(log_lines, report)
        self._detect_runtime_errors(log_lines, report)
        self._detect_data_issues(log_lines, report)
        self._detect_logic_issues(log_lines, report)
        self._detect_incomplete_execution(log_lines, report)
        
        # Generate recommendations
        self._generate_recommendations(report)
        
        # Determine overall success
        critical_issues = [i for i in report.issues if i.severity == IssueSeverity.CRITICAL]
        report.success = len(critical_issues) == 0
        
        if self.verbose:
            logger.info(f"Analysis complete: {len(report.issues)} issues found")
            for issue in report.issues:
                logger.info(f"  - [{issue.severity.value}] {issue.issue_type.value}: {issue.description}")
        
        return report
    
    def _detect_import_errors(self, log_lines: List[str], report: DiagnosticReport):
        """Detect import-related errors"""
        for i, line in enumerate(log_lines):
            if self.patterns['import_error'].search(line):
                # Extract module name
                module_name = None
                if "No module named" in line:
                    match = re.search(r"No module named ['\"](.+?)['\"]", line)
                    if match:
                        module_name = match.group(1)
                
                issue = DiagnosticIssue(
                    issue_type=IssueType.IMPORT_ERROR,
                    severity=IssueSeverity.CRITICAL,
                    description=f"Missing import: {module_name or 'unknown module'}",
                    evidence=[line.strip()],
                    suggested_fix=f"Install missing package: pip install {module_name}" if module_name else "Check import statements",
                    confidence=0.95
                )
                report.issues.append(issue)
    
    def _detect_runtime_errors(self, log_lines: List[str], report: DiagnosticReport):
        """Detect runtime errors (AttributeError, TypeError, etc.)"""
        error_types = [
            ('attribute_error', IssueType.RUNTIME_ERROR, "Attribute not found"),
            ('type_error', IssueType.RUNTIME_ERROR, "Type mismatch"),
            ('value_error', IssueType.RUNTIME_ERROR, "Invalid value"),
            ('name_error', IssueType.VARIABLE_ERROR, "Variable not defined"),
            ('key_error', IssueType.RUNTIME_ERROR, "Missing dictionary key"),
            ('index_error', IssueType.RUNTIME_ERROR, "Index out of range"),
        ]
        
        for i, line in enumerate(log_lines):
            for pattern_name, issue_type, base_desc in error_types:
                if match := self.patterns[pattern_name].search(line):
                    error_detail = match.group(1) if match.groups() else ""
                    
                    # Extract line number if available
                    line_num = None
                    if line_match := self.patterns['line_number'].search(line):
                        line_num = int(line_match.group(1))
                    
                    # Get context (lines around error)
                    context_lines = []
                    for j in range(max(0, i-2), min(len(log_lines), i+3)):
                        context_lines.append(log_lines[j].strip())
                    
                    issue = DiagnosticIssue(
                        issue_type=issue_type,
                        severity=IssueSeverity.HIGH,
                        description=f"{base_desc}: {error_detail}",
                        evidence=context_lines,
                        line_number=line_num,
                        suggested_fix=self._suggest_fix_for_error(pattern_name, error_detail),
                        confidence=0.85
                    )
                    report.issues.append(issue)
                    report.error_message = f"{base_desc}: {error_detail}"
    
    def _detect_data_issues(self, log_lines: List[str], report: DiagnosticReport):
        """Detect data fetching and processing issues"""
        data_fetch_attempted = False
        data_fetch_completed = False
        
        for line in log_lines:
            if self.patterns['data_fetch'].search(line):
                data_fetch_attempted = True
            
            # Look for signs of successful data fetch
            if 'DataFrame' in line or 'shape' in line:
                data_fetch_completed = True
        
        if data_fetch_attempted and not data_fetch_completed:
            issue = DiagnosticIssue(
                issue_type=IssueType.DATA_FETCH_ERROR,
                severity=IssueSeverity.CRITICAL,
                description="Data fetch attempted but no data received",
                evidence=["Data fetch function called but no DataFrame created"],
                suggested_fix="Check API connection, verify ticker symbol, ensure date range is valid",
                confidence=0.75
            )
            report.issues.append(issue)
    
    def _detect_logic_issues(self, log_lines: List[str], report: DiagnosticReport):
        """Detect logical issues in execution flow"""
        # Check for infinite loops (same function called many times)
        func_call_counts = {}
        for entry in report.execution_timeline:
            if entry.startswith('→'):
                func = entry[2:]
                func_call_counts[func] = func_call_counts.get(func, 0) + 1
        
        for func, count in func_call_counts.items():
            if count > 1000:
                issue = DiagnosticIssue(
                    issue_type=IssueType.LOGIC_ERROR,
                    severity=IssueSeverity.HIGH,
                    description=f"Possible infinite loop in function: {func}",
                    evidence=[f"Function called {count} times"],
                    function_name=func,
                    suggested_fix="Check loop conditions and break statements",
                    confidence=0.70
                )
                report.issues.append(issue)
    
    def _detect_incomplete_execution(self, log_lines: List[str], report: DiagnosticReport):
        """Detect if execution completed successfully"""
        # Look for common function names that should be called
        expected_functions = ['initialize', 'run', 'execute', 'backtest', 'main']
        
        for func in expected_functions:
            if any(func.lower() in f.lower() for f in report.functions_executed):
                report.execution_completed = True
                break
        
        # If we found errors but execution wasn't marked complete
        if not report.execution_completed and report.issues:
            issue = DiagnosticIssue(
                issue_type=IssueType.INCOMPLETE_EXECUTION,
                severity=IssueSeverity.HIGH,
                description="Bot execution did not complete",
                evidence=[f"Functions executed: {', '.join(report.functions_executed[:5])}"],
                suggested_fix="Fix errors preventing complete execution",
                confidence=0.80
            )
            report.issues.append(issue)
    
    def _suggest_fix_for_error(self, error_type: str, error_detail: str) -> str:
        """Suggest a fix based on error type"""
        suggestions = {
            'attribute_error': "Check object type and available attributes. Verify data structure.",
            'type_error': "Check variable types. Ensure operations match expected types.",
            'value_error': "Validate input values. Check for empty data or invalid ranges.",
            'name_error': "Define variable before use. Check for typos in variable names.",
            'key_error': "Verify dictionary keys exist. Add default values or check before access.",
            'index_error': "Check array bounds. Verify data is not empty before indexing.",
        }
        
        return suggestions.get(error_type, "Review code logic and fix error")
    
    def _generate_recommendations(self, report: DiagnosticReport):
        """Generate high-level recommendations based on identified issues"""
        if not report.issues:
            report.recommendations.append("✓ No issues detected. Bot appears to be working correctly.")
            return
        
        # Group issues by type
        issue_counts = {}
        for issue in report.issues:
            issue_type = issue.issue_type
            issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
        
        # Generate specific recommendations
        if IssueType.IMPORT_ERROR in issue_counts:
            report.recommendations.append(
                "🔧 Install missing dependencies using pip or conda"
            )
        
        if IssueType.DATA_FETCH_ERROR in issue_counts:
            report.recommendations.append(
                "📊 Check data source connection and verify ticker symbols"
            )
        
        if IssueType.RUNTIME_ERROR in issue_counts or IssueType.VARIABLE_ERROR in issue_counts:
            report.recommendations.append(
                "🐛 Fix runtime errors by checking variable types and object attributes"
            )
        
        if IssueType.LOGIC_ERROR in issue_counts:
            report.recommendations.append(
                "🔄 Review loop logic and conditional statements"
            )
        
        # Priority recommendations
        critical_issues = [i for i in report.issues if i.severity == IssueSeverity.CRITICAL]
        if critical_issues:
            report.recommendations.insert(0, 
                f"⚠️ Fix {len(critical_issues)} critical issue(s) first before running bot"
            )
    
    def generate_fix_prompt(self, report: DiagnosticReport, bot_code: str) -> str:
        """
        Generate a detailed prompt for AI to fix the bot based on diagnostic analysis
        
        Args:
            report: Diagnostic report from log analysis
            bot_code: Original bot code
            
        Returns:
            Detailed prompt for AI code fixer
        """
        prompt_parts = []
        
        prompt_parts.append("# Bot Code Fixing Task\n")
        prompt_parts.append("Based on diagnostic log analysis, the following issues were identified:\n")
        
        # List issues with details
        for i, issue in enumerate(report.issues, 1):
            prompt_parts.append(f"\n## Issue {i}: {issue.issue_type.value}")
            prompt_parts.append(f"- **Severity**: {issue.severity.value}")
            prompt_parts.append(f"- **Description**: {issue.description}")
            
            if issue.line_number:
                prompt_parts.append(f"- **Line**: {issue.line_number}")
            
            if issue.function_name:
                prompt_parts.append(f"- **Function**: {issue.function_name}")
            
            if issue.evidence:
                prompt_parts.append(f"- **Evidence**:")
                for evidence in issue.evidence[:3]:  # Limit to 3 lines
                    prompt_parts.append(f"  ```\n  {evidence}\n  ```")
            
            if issue.suggested_fix:
                prompt_parts.append(f"- **Suggested Fix**: {issue.suggested_fix}")
        
        # Add execution context
        if report.functions_executed:
            prompt_parts.append(f"\n## Execution Flow")
            prompt_parts.append("Functions that were successfully executed:")
            for func in report.functions_executed[:10]:
                prompt_parts.append(f"- {func}")
        
        # Add recommendations
        if report.recommendations:
            prompt_parts.append(f"\n## Recommendations")
            for rec in report.recommendations:
                prompt_parts.append(f"- {rec}")
        
        prompt_parts.append("\n## Task")
        prompt_parts.append("Please fix the bot code to address the issues identified above.")
        prompt_parts.append("Focus on the highest severity issues first.")
        prompt_parts.append("\n## Original Bot Code")
        prompt_parts.append("```python")
        prompt_parts.append(bot_code)
        prompt_parts.append("```")
        
        return "\n".join(prompt_parts)


def analyze_bot_execution(log_file: Path, bot_file: Path, verbose: bool = True) -> DiagnosticReport:
    """
    Convenience function to analyze bot execution
    
    Args:
        log_file: Path to diagnostic log
        bot_file: Path to bot source code
        verbose: Enable verbose output
        
    Returns:
        Diagnostic report
    """
    analyzer = LogAnalyzer(verbose=verbose)
    report = analyzer.analyze_log_file(log_file)
    
    if verbose:
        print("\n" + "="*70)
        print("DIAGNOSTIC REPORT")
        print("="*70)
        print(f"Success: {report.success}")
        print(f"Execution Completed: {report.execution_completed}")
        print(f"Issues Found: {len(report.issues)}")
        
        if report.issues:
            print("\nIdentified Issues:")
            for i, issue in enumerate(report.issues, 1):
                print(f"\n{i}. [{issue.severity.value.upper()}] {issue.description}")
                if issue.suggested_fix:
                    print(f"   Fix: {issue.suggested_fix}")
        
        if report.recommendations:
            print("\nRecommendations:")
            for rec in report.recommendations:
                print(f"  {rec}")
        
        print("="*70)
    
    return report


if __name__ == "__main__":
    # Test the analyzer
    test_log = """
2026-02-01 10:00:00 [INFO] ====================================================
2026-02-01 10:00:00 [INFO] DIAGNOSTIC MODE ENABLED
2026-02-01 10:00:00 [INFO] [DIAG] Entering function: initialize
2026-02-01 10:00:01 [INFO] [DIAG] Calling method: fetch
2026-02-01 10:00:02 [ERROR] AttributeError: 'NoneType' object has no attribute 'close'
2026-02-01 10:00:02 [ERROR]   File "bot.py", line 42, in initialize
"""
    
    analyzer = LogAnalyzer(verbose=True)
    report = analyzer.analyze_log_content(test_log)
    
    print("\nTest Analysis Results:")
    print(f"Issues found: {len(report.issues)}")
    for issue in report.issues:
        print(f"  - {issue.description}")
