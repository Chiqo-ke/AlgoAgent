"""
Enhanced Error Detection System
=================================

Detects whether errors originate from bot code or framework/system files,
enabling intelligent error handling and escalation.

Features:
- Framework vs bot code error source detection
- Encoding compatibility validation (Windows console)
- Case sensitivity validation for indicators
- Indicator extraction filter validation
- Import path validation
- Error escalation for framework issues

Created: December 7, 2025
Version: 1.0.0
"""

import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """Represents a validation issue found in code"""
    severity: str  # 'critical', 'high', 'medium', 'low'
    category: str  # 'encoding', 'case_sensitivity', 'filter', 'import', etc.
    line_number: Optional[int]
    message: str
    suggested_fix: Optional[str] = None
    auto_fixable: bool = False


@dataclass
class ErrorSource:
    """Information about error source location"""
    error_location: str  # 'bot_code', 'framework', 'system', 'unknown'
    file_path: str
    line_number: Optional[int]
    is_fixable_by_bot: bool
    requires_framework_fix: bool
    framework_component: Optional[str] = None  # 'Data', 'Backtest', 'Trade', etc.


class EnhancedErrorDetector:
    """Advanced error detection and classification"""
    
    # Framework directories
    FRAMEWORK_PATHS = ['Data/', 'Backtest/', 'Trade/', 'monolithic_agent/']
    BOT_PATHS = ['codes/', 'strategies/', 'Backtest/codes/']
    
    # System paths (Python stdlib, packages)
    SYSTEM_PATHS = ['site-packages/', 'lib/python', 'Python\\Lib\\']
    
    @classmethod
    def detect_error_source(cls, error_traceback: str) -> ErrorSource:
        """
        Determine if error originated in bot code, framework, or system
        
        Args:
            error_traceback: Full error traceback string
        
        Returns:
            ErrorSource with detailed location information
        """
        # Extract file path and line number from traceback
        # Pattern: File "path/to/file.py", line 123
        file_pattern = r'File\s+"([^"]+)",\s+line\s+(\d+)'
        matches = re.findall(file_pattern, error_traceback)
        
        if not matches:
            return ErrorSource(
                error_location='unknown',
                file_path='',
                line_number=None,
                is_fixable_by_bot=False,
                requires_framework_fix=False
            )
        
        # Get the last file in traceback (where error actually occurred)
        error_file, error_line = matches[-1]
        error_line = int(error_line)
        
        # Normalize path separators
        error_file_normalized = error_file.replace('\\', '/')
        
        # Check if error is in system/stdlib
        if any(path in error_file_normalized for path in cls.SYSTEM_PATHS):
            return ErrorSource(
                error_location='system',
                file_path=error_file,
                line_number=error_line,
                is_fixable_by_bot=False,
                requires_framework_fix=False
            )
        
        # Check if error is in bot code
        if any(path in error_file_normalized for path in cls.BOT_PATHS):
            return ErrorSource(
                error_location='bot_code',
                file_path=error_file,
                line_number=error_line,
                is_fixable_by_bot=True,
                requires_framework_fix=False
            )
        
        # Check if error is in framework
        for framework_path in cls.FRAMEWORK_PATHS:
            if framework_path in error_file_normalized:
                # Determine framework component
                component = framework_path.rstrip('/')
                
                return ErrorSource(
                    error_location='framework',
                    file_path=error_file,
                    line_number=error_line,
                    is_fixable_by_bot=False,
                    requires_framework_fix=True,
                    framework_component=component
                )
        
        # Unknown location (could be user code outside standard paths)
        return ErrorSource(
            error_location='unknown',
            file_path=error_file,
            line_number=error_line,
            is_fixable_by_bot=True,  # Assume fixable
            requires_framework_fix=False
        )
    
    @classmethod
    def validate_console_compatibility(cls, code: str, file_path: Optional[Path] = None) -> List[ValidationIssue]:
        """
        Check if code contains characters incompatible with Windows console (cp1252)
        
        Args:
            code: Source code to validate
            file_path: Optional file path for context
        
        Returns:
            List of encoding validation issues
        """
        issues = []
        
        for line_num, line in enumerate(code.split('\n'), 1):
            try:
                # Try to encode with cp1252 (Windows console encoding)
                line.encode('cp1252')
            except UnicodeEncodeError as e:
                # Get the problematic character
                char = e.object[e.start:e.end]
                char_code = ord(char)
                
                # Determine character type
                char_type = cls._get_character_type(char_code)
                
                # Build suggested fix
                suggested_fix = cls._suggest_encoding_fix(line, char)
                
                issue = ValidationIssue(
                    severity='critical',
                    category='encoding',
                    line_number=line_num,
                    message=(
                        f"Character '{char}' (U+{char_code:04X}, {char_type}) "
                        f"incompatible with Windows console. "
                        f"Will cause 'charmap_encode' error on execution."
                    ),
                    suggested_fix=suggested_fix,
                    auto_fixable=True
                )
                issues.append(issue)
        
        return issues
    
    @staticmethod
    def _get_character_type(char_code: int) -> str:
        """Get human-readable character type"""
        if 0x1F300 <= char_code <= 0x1F9FF:
            return "Emoji"
        elif 0x2000 <= char_code <= 0x2BFF:
            return "Symbol"
        elif char_code > 0x7F:
            return "Unicode"
        return "ASCII"
    
    @staticmethod
    def _suggest_encoding_fix(line: str, char: str) -> str:
        """Suggest ASCII replacement for non-compatible character"""
        # Common emoji replacements
        replacements = {
            '🔄': '[TALib]',
            '✓': '[OK]',
            '✅': '[SUCCESS]',
            '❌': '[ERROR]',
            '⚠️': '[WARNING]',
            '📊': '[DATA]',
            '🚀': '[START]',
            '🎯': '[TARGET]',
            '💰': '[PROFIT]',
            '📈': '[UP]',
            '📉': '[DOWN]',
        }
        
        replacement = replacements.get(char, '[?]')
        suggested_line = line.replace(char, replacement)
        
        return f'Replace: {line.strip()}\nWith: {suggested_line.strip()}'
    
    @classmethod
    def validate_indicator_access_consistency(
        cls,
        bot_code: str,
        indicator_requests: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """
        Validate that bot accesses indicators with correct case sensitivity
        
        Args:
            bot_code: Bot source code
            indicator_requests: Dict of requested indicators with params
        
        Returns:
            List of case sensitivity issues
        """
        issues = []
        
        if not indicator_requests:
            return issues
        
        # Generate expected column names for each indicator
        expected_columns = cls._generate_expected_columns(indicator_requests)
        
        # Find all indicator accesses in code
        access_patterns = [
            (r"indicators\.get\(['\"]([^'\"]+)['\"]\)", "indicators.get()"),
            (r"data\[['\"]([^'\"]+)['\"]\]", "data[]"),
            (r"symbol_data\.get\(['\"]([^'\"]+)['\"]\)", "symbol_data.get()"),
            (r"df\[['\"]([^'\"]+)['\"]\]", "df[]"),
        ]
        
        for pattern, access_method in access_patterns:
            matches = re.finditer(pattern, bot_code)
            
            for match in matches:
                accessed_name = match.group(1)
                line_num = bot_code[:match.start()].count('\n') + 1
                
                # Check if this looks like an indicator column
                # (starts with indicator name or has underscore pattern)
                base_name = accessed_name.split('_')[0].lower()
                
                # Check if base name matches any requested indicator
                for indicator_name in indicator_requests.keys():
                    if base_name == indicator_name.lower():
                        # Found a match - check if case is correct
                        if accessed_name not in expected_columns:
                            # Find the correct column name
                            correct_column = cls._find_correct_column(
                                accessed_name,
                                expected_columns
                            )
                            
                            if correct_column:
                                issue = ValidationIssue(
                                    severity='high',
                                    category='case_sensitivity',
                                    line_number=line_num,
                                    message=(
                                        f"Case mismatch: Code accesses '{accessed_name}' "
                                        f"but actual column is '{correct_column}'. "
                                        f"This will cause indicator to be None/missing."
                                    ),
                                    suggested_fix=f"Change '{accessed_name}' to '{correct_column}'",
                                    auto_fixable=True
                                )
                                issues.append(issue)
        
        return issues
    
    @staticmethod
    def _generate_expected_columns(indicator_requests: Dict[str, Any]) -> List[str]:
        """Generate list of expected indicator column names"""
        columns = []
        
        for indicator_name, params in indicator_requests.items():
            if isinstance(params, dict):
                # Check for multi-period format
                if 'periods' in params:
                    # Multi-period: SMA with periods=[20, 50] → ['SMA_20', 'SMA_50']
                    for period in params['periods']:
                        columns.append(f"{indicator_name}_{period}")
                elif 'timeperiod' in params:
                    # Single period: RSI with timeperiod=14 → 'rsi_14'
                    columns.append(f"{indicator_name.lower()}_{params['timeperiod']}")
                else:
                    # No period: Indicator name only (check registry for output format)
                    columns.append(indicator_name.lower())
            else:
                columns.append(indicator_name.lower())
        
        return columns
    
    @staticmethod
    def _find_correct_column(accessed_name: str, expected_columns: List[str]) -> Optional[str]:
        """Find the correct column name for an accessed name (case-insensitive)"""
        accessed_lower = accessed_name.lower()
        
        for column in expected_columns:
            if column.lower() == accessed_lower:
                return column
        
        return None
    
    @classmethod
    def validate_indicator_extraction_filter(
        cls,
        bot_code: str,
        indicator_requests: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """
        Validate that indicator extraction filter will capture all requested indicators
        
        Args:
            bot_code: Bot source code
            indicator_requests: Dict of requested indicators
        
        Returns:
            List of filter validation issues
        """
        issues = []
        
        if not indicator_requests:
            return issues
        
        # Find indicator extraction patterns
        # Pattern: {k: v for k, v in data.items() if k.startswith((...))}}
        filter_pattern = r"k\.startswith\(\(([^)]+)\)\)"
        matches = re.finditer(filter_pattern, bot_code)
        
        for match in matches:
            filter_str = match.group(1)
            line_num = bot_code[:match.start()].count('\n') + 1
            
            # Parse filter prefixes
            prefixes = [
                p.strip().strip("'\"")
                for p in filter_str.split(',')
            ]
            
            # Generate expected columns
            expected_columns = cls._generate_expected_columns(indicator_requests)
            
            # Check if filter will capture all expected columns
            uncaptured = []
            for column in expected_columns:
                if not any(column.startswith(prefix) for prefix in prefixes):
                    uncaptured.append(column)
            
            if uncaptured:
                # Suggest additional prefixes
                suggested_prefixes = set()
                for col in uncaptured:
                    prefix = col.split('_')[0] + '_'
                    suggested_prefixes.add(prefix)
                
                issue = ValidationIssue(
                    severity='critical',
                    category='filter',
                    line_number=line_num,
                    message=(
                        f"Indicator filter won't capture: {', '.join(uncaptured)}. "
                        f"These indicators will be missing from the indicators dict."
                    ),
                    suggested_fix=(
                        f"Add to filter prefixes: {', '.join(repr(p) for p in suggested_prefixes)}\n"
                        f"Current: ({filter_str})\n"
                        f"Suggested: ({filter_str}, {', '.join(repr(p) for p in suggested_prefixes)})"
                    ),
                    auto_fixable=True
                )
                issues.append(issue)
        
        return issues
    
    @classmethod
    def validate_import_paths(cls, bot_code: str) -> List[ValidationIssue]:
        """
        Validate import statements for common mistakes
        
        Args:
            bot_code: Bot source code
        
        Returns:
            List of import validation issues
        """
        issues = []
        
        # Common incorrect imports
        incorrect_imports = {
            'from Data.data_manager': 'from Backtest.data_loader',
            'from Trade.': 'Incorrect path - Trade module may not exist',
            'from backtesting import': 'Wrong library - use from Backtest.sim_broker import',
        }
        
        for incorrect, correction in incorrect_imports.items():
            if incorrect in bot_code:
                # Find line number
                pattern = re.escape(incorrect) + r'[^\n]*'
                match = re.search(pattern, bot_code)
                if match:
                    line_num = bot_code[:match.start()].count('\n') + 1
                    
                    issue = ValidationIssue(
                        severity='critical',
                        category='import',
                        line_number=line_num,
                        message=f"Incorrect import: '{incorrect}' will fail",
                        suggested_fix=f"Replace with: {correction}",
                        auto_fixable=True
                    )
                    issues.append(issue)
        
        return issues
    
    @classmethod
    def comprehensive_validation(
        cls,
        bot_code: str,
        indicator_requests: Optional[Dict[str, Any]] = None,
        file_path: Optional[Path] = None
    ) -> Tuple[List[ValidationIssue], Dict[str, int]]:
        """
        Run all validation checks
        
        Args:
            bot_code: Bot source code
            indicator_requests: Optional indicator requests dict
            file_path: Optional file path for context
        
        Returns:
            Tuple of (all_issues, summary_by_severity)
        """
        all_issues = []
        
        # Encoding validation (critical for Windows)
        all_issues.extend(cls.validate_console_compatibility(bot_code, file_path))
        
        # Import validation
        all_issues.extend(cls.validate_import_paths(bot_code))
        
        # Indicator validations (if indicators are used)
        if indicator_requests:
            all_issues.extend(
                cls.validate_indicator_access_consistency(bot_code, indicator_requests)
            )
            all_issues.extend(
                cls.validate_indicator_extraction_filter(bot_code, indicator_requests)
            )
        
        # Summarize by severity
        summary = {
            'critical': sum(1 for i in all_issues if i.severity == 'critical'),
            'high': sum(1 for i in all_issues if i.severity == 'high'),
            'medium': sum(1 for i in all_issues if i.severity == 'medium'),
            'low': sum(1 for i in all_issues if i.severity == 'low'),
        }
        
        return all_issues, summary


def format_validation_report(
    issues: List[ValidationIssue],
    summary: Dict[str, int]
) -> str:
    """
    Format validation issues into a readable report
    
    Args:
        issues: List of validation issues
        summary: Summary by severity
    
    Returns:
        Formatted report string
    """
    if not issues:
        return "✅ All validations passed - no issues found."
    
    report = f"\n{'='*70}\n"
    report += "CODE VALIDATION REPORT\n"
    report += f"{'='*70}\n\n"
    
    report += f"Total Issues: {len(issues)}\n"
    report += f"  Critical: {summary['critical']}\n"
    report += f"  High: {summary['high']}\n"
    report += f"  Medium: {summary['medium']}\n"
    report += f"  Low: {summary['low']}\n\n"
    
    # Group by category
    by_category = {}
    for issue in issues:
        if issue.category not in by_category:
            by_category[issue.category] = []
        by_category[issue.category].append(issue)
    
    # Report each category
    for category, category_issues in by_category.items():
        report += f"\n{category.upper()} ISSUES ({len(category_issues)}):\n"
        report += "-" * 70 + "\n"
        
        for i, issue in enumerate(category_issues, 1):
            report += f"\n{i}. [{issue.severity.upper()}] "
            if issue.line_number:
                report += f"Line {issue.line_number}: "
            report += f"{issue.message}\n"
            
            if issue.suggested_fix:
                report += f"   Suggested Fix:\n"
                for line in issue.suggested_fix.split('\n'):
                    report += f"   {line}\n"
    
    report += f"\n{'='*70}\n"
    
    return report


# Convenience function for quick validation
def validate_bot_code(
    bot_code: str,
    indicator_requests: Optional[Dict[str, Any]] = None
) -> str:
    """
    Quick validation function that returns formatted report
    
    Args:
        bot_code: Bot source code
        indicator_requests: Optional indicator requests
    
    Returns:
        Formatted validation report
    """
    issues, summary = EnhancedErrorDetector.comprehensive_validation(
        bot_code,
        indicator_requests
    )
    
    return format_validation_report(issues, summary)
