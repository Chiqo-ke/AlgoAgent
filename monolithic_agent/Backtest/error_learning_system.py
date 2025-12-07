"""
Error Learning System - Learn from execution failures to improve generation
===========================================================================

This module implements a feedback loop that:
1. Tracks execution failures and their causes
2. Learns common error patterns
3. Adjusts generation prompts based on learned patterns
4. Maintains error statistics and trends
5. Provides insights for improving code generation

Features:
- Persistent error database (SQLite)
- Pattern recognition and frequency analysis
- Dynamic prompt weight adjustment
- Error trend analysis
- Automatic recommendations

Last updated: 2025-12-05
Version: 1.0.0
"""

import json
import sqlite3
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import Counter
import re

logger = logging.getLogger(__name__)


@dataclass
class ErrorRecord:
    """Record of an execution error"""
    timestamp: datetime
    strategy_name: str
    error_type: str
    error_message: str
    code_snippet: Optional[str] = None
    fix_successful: bool = False
    fix_attempts: int = 0
    resolution_time_seconds: Optional[float] = None
    
    # Classification
    is_generation_error: bool = False  # Error in AI-generated code
    is_environment_error: bool = False  # System/environment error
    is_data_error: bool = False  # Data-related error
    
    # Context
    user_description: Optional[str] = None
    generated_params: Optional[Dict[str, Any]] = None


@dataclass
class ErrorPattern:
    """Learned error pattern"""
    pattern_id: str
    error_type: str
    description: str
    occurrence_count: int
    last_seen: datetime
    common_causes: List[str]
    recommended_fixes: List[str]
    prompt_adjustments: Dict[str, float]


class ErrorLearningSystem:
    """Learn from execution failures to improve code generation"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize error learning system
        
        Args:
            db_path: Path to SQLite database (default: Backtest/error_learning.db)
        """
        self.db_path = Path(db_path or "Backtest/error_learning.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Error weights (used to adjust generation prompts)
        self.error_weights = self._load_error_weights()
        
        # Pattern cache
        self.learned_patterns: Dict[str, ErrorPattern] = {}
        self._load_patterns()
        
        logger.info(f"ErrorLearningSystem initialized (DB: {self.db_path})")
    
    def _init_database(self):
        """Initialize SQLite database schema"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Create errors table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                strategy_name TEXT NOT NULL,
                error_type TEXT NOT NULL,
                error_message TEXT NOT NULL,
                code_snippet TEXT,
                fix_successful INTEGER NOT NULL,
                fix_attempts INTEGER NOT NULL,
                resolution_time_seconds REAL,
                is_generation_error INTEGER NOT NULL,
                is_environment_error INTEGER NOT NULL,
                is_data_error INTEGER NOT NULL,
                user_description TEXT,
                generated_params TEXT
            )
        ''')
        
        # Create patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patterns (
                pattern_id TEXT PRIMARY KEY,
                error_type TEXT NOT NULL,
                description TEXT NOT NULL,
                occurrence_count INTEGER NOT NULL,
                last_seen TEXT NOT NULL,
                common_causes TEXT NOT NULL,
                recommended_fixes TEXT NOT NULL,
                prompt_adjustments TEXT NOT NULL
            )
        ''')
        
        # Create weights table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS error_weights (
                error_category TEXT PRIMARY KEY,
                weight REAL NOT NULL,
                last_updated TEXT NOT NULL
            )
        ''')
        
        # Create indices for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_error_type ON errors(error_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON errors(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_strategy ON errors(strategy_name)')
        
        conn.commit()
        conn.close()
    
    def record_error(
        self,
        strategy_name: str,
        error_type: str,
        error_message: str,
        code_snippet: Optional[str] = None,
        fix_successful: bool = False,
        fix_attempts: int = 0,
        resolution_time_seconds: Optional[float] = None,
        user_description: Optional[str] = None,
        generated_params: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Record an execution error
        
        Args:
            strategy_name: Name of the strategy that failed
            error_type: Type of error (from ErrorAnalyzer)
            error_message: Full error message
            code_snippet: Relevant code snippet (optional)
            fix_successful: Whether error was fixed
            fix_attempts: Number of fix attempts
            resolution_time_seconds: Time to fix (if fixed)
            user_description: Original user description
            generated_params: Parameters used in generation
        
        Returns:
            Error record ID
        """
        # Classify error
        is_generation = self._is_generation_error(error_type, error_message)
        is_environment = self._is_environment_error(error_type, error_message)
        is_data = self._is_data_error(error_type, error_message)
        
        # Store in database
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO errors (
                timestamp, strategy_name, error_type, error_message,
                code_snippet, fix_successful, fix_attempts,
                resolution_time_seconds, is_generation_error,
                is_environment_error, is_data_error,
                user_description, generated_params
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            strategy_name,
            error_type,
            error_message,
            code_snippet,
            int(fix_successful),
            fix_attempts,
            resolution_time_seconds,
            int(is_generation),
            int(is_environment),
            int(is_data),
            user_description,
            json.dumps(generated_params) if generated_params else None
        ))
        
        error_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Update patterns and weights
        self._update_patterns(error_type, error_message, fix_successful)
        self._update_weights(error_type, is_generation)
        
        logger.info(f"Recorded error {error_id}: {error_type} ({strategy_name})")
        
        return error_id
    
    def _is_generation_error(self, error_type: str, error_message: str) -> bool:
        """Determine if error is from AI generation issues"""
        generation_indicators = [
            'sys.path', 'parent.parent', 'import path',
            'indicator naming', 'lowercase', 'uppercase',
            'compute_indicator', 'multiple ema',
            'charmap_encode', 'unicode', 'emoji'
        ]
        
        error_combined = f"{error_type} {error_message}".lower()
        return any(indicator in error_combined for indicator in generation_indicators)
    
    def _is_environment_error(self, error_type: str, error_message: str) -> bool:
        """Determine if error is environment-related"""
        return error_type in ['file_error', 'timeout_error', 'encoding_error']
    
    def _is_data_error(self, error_type: str, error_message: str) -> bool:
        """Determine if error is data-related"""
        data_indicators = ['no data', 'empty dataframe', 'nan values', 'missing column']
        error_combined = f"{error_type} {error_message}".lower()
        return any(indicator in error_combined for indicator in data_indicators)
    
    def _update_patterns(self, error_type: str, error_message: str, fix_successful: bool):
        """Update learned patterns based on new error"""
        # Extract key phrases from error message
        pattern_id = self._generate_pattern_id(error_type, error_message)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Check if pattern exists
        cursor.execute('SELECT * FROM patterns WHERE pattern_id = ?', (pattern_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing pattern
            occurrence_count = existing[3] + 1
            cursor.execute('''
                UPDATE patterns 
                SET occurrence_count = ?, last_seen = ?
                WHERE pattern_id = ?
            ''', (occurrence_count, datetime.now().isoformat(), pattern_id))
        else:
            # Create new pattern
            causes = self._extract_causes(error_message)
            fixes = self._suggest_fixes(error_type, error_message)
            adjustments = self._calculate_prompt_adjustments(error_type)
            
            cursor.execute('''
                INSERT INTO patterns (
                    pattern_id, error_type, description,
                    occurrence_count, last_seen,
                    common_causes, recommended_fixes, prompt_adjustments
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pattern_id,
                error_type,
                error_message[:200],  # First 200 chars
                1,
                datetime.now().isoformat(),
                json.dumps(causes),
                json.dumps(fixes),
                json.dumps(adjustments)
            ))
        
        conn.commit()
        conn.close()
    
    def _generate_pattern_id(self, error_type: str, error_message: str) -> str:
        """Generate unique pattern ID from error characteristics"""
        # Extract key phrases
        key_phrases = []
        
        # Look for specific patterns
        patterns = [
            r'parent\.parent\.parent',
            r'parent\.parent',
            r"'ema_\d+'",
            r"'EMA_\d+'",
            r'charmap_encode',
            r'ModuleNotFoundError',
            r'KeyError',
        ]
        
        for pattern in patterns:
            if re.search(pattern, error_message):
                key_phrases.append(pattern.replace('\\', ''))
        
        # Combine error type and key phrases
        pattern_str = f"{error_type}_{'_'.join(key_phrases)}" if key_phrases else error_type
        return pattern_str[:50]  # Limit length
    
    def _extract_causes(self, error_message: str) -> List[str]:
        """Extract probable causes from error message"""
        causes = []
        
        if 'parent.parent' in error_message and 'parent.parent.parent' not in error_message:
            causes.append("Wrong sys.path depth (2 levels instead of 3)")
        
        if 'EMA_' in error_message or 'SMA_' in error_message:
            causes.append("Uppercase indicator naming instead of lowercase")
        
        if 'charmap' in error_message or 'encode' in error_message:
            causes.append("Unicode/emoji characters in output")
        
        if 'KeyError' in error_message and 'ema_' in error_message.lower():
            causes.append("Indicator not found (wrong naming or not computed)")
        
        if not causes:
            causes.append("Unknown cause - requires investigation")
        
        return causes
    
    def _suggest_fixes(self, error_type: str, error_message: str) -> List[str]:
        """Suggest fixes based on error pattern"""
        fixes = []
        
        if 'parent.parent' in error_message:
            fixes.append("Use parent.parent.parent (3 levels) for sys.path")
        
        if 'EMA_' in error_message or 'uppercase' in error_message.lower():
            fixes.append("Use lowercase indicator names: ema_12 not EMA_12")
        
        if 'charmap' in error_message:
            fixes.append("Remove emoji/unicode characters from print statements")
        
        if 'compute_indicator' in error_message:
            fixes.append("Call compute_indicator separately for each indicator period")
        
        if not fixes:
            fixes.append("Review error message and generated code")
        
        return fixes
    
    def _calculate_prompt_adjustments(self, error_type: str) -> Dict[str, float]:
        """Calculate prompt weight adjustments"""
        adjustments = {}
        
        # Increase emphasis on specific requirements based on error type
        if error_type in ['import_error', 'encoding_error']:
            adjustments['import_path_emphasis'] = 0.2
        
        if error_type in ['key_error', 'attribute_error']:
            adjustments['indicator_naming_emphasis'] = 0.2
        
        if error_type == 'encoding_error':
            adjustments['unicode_warning_emphasis'] = 0.3
        
        return adjustments
    
    def _update_weights(self, error_type: str, is_generation_error: bool):
        """Update error category weights"""
        if not is_generation_error:
            return  # Only track generation errors
        
        category = self._categorize_error(error_type)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Get current weight
        cursor.execute('SELECT weight FROM error_weights WHERE error_category = ?', (category,))
        result = cursor.fetchone()
        
        if result:
            new_weight = min(result[0] + 0.1, 1.0)  # Max weight is 1.0
        else:
            new_weight = 0.1
        
        # Update or insert
        cursor.execute('''
            INSERT OR REPLACE INTO error_weights (error_category, weight, last_updated)
            VALUES (?, ?, ?)
        ''', (category, new_weight, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        # Update in-memory weights
        self.error_weights[category] = new_weight
    
    def _categorize_error(self, error_type: str) -> str:
        """Categorize error into broader category"""
        categories = {
            'import_errors': ['import_error', 'module_error'],
            'indicator_errors': ['key_error', 'attribute_error'],
            'encoding_errors': ['encoding_error', 'unicode_error'],
            'syntax_errors': ['syntax_error', 'indentation_error'],
            'runtime_errors': ['runtime_error', 'value_error', 'type_error'],
        }
        
        for category, types in categories.items():
            if error_type in types:
                return category
        
        return 'other_errors'
    
    def _load_error_weights(self) -> Dict[str, float]:
        """Load error weights from database"""
        weights = {}
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute('SELECT error_category, weight FROM error_weights')
            
            for row in cursor.fetchall():
                weights[row[0]] = row[1]
            
            conn.close()
        except Exception as e:
            logger.warning(f"Failed to load error weights: {e}")
        
        return weights
    
    def _load_patterns(self):
        """Load learned patterns from database"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM patterns ORDER BY occurrence_count DESC LIMIT 50')
            
            for row in cursor.fetchall():
                pattern = ErrorPattern(
                    pattern_id=row[0],
                    error_type=row[1],
                    description=row[2],
                    occurrence_count=row[3],
                    last_seen=datetime.fromisoformat(row[4]),
                    common_causes=json.loads(row[5]),
                    recommended_fixes=json.loads(row[6]),
                    prompt_adjustments=json.loads(row[7])
                )
                self.learned_patterns[pattern.pattern_id] = pattern
            
            conn.close()
            logger.info(f"Loaded {len(self.learned_patterns)} learned patterns")
        except Exception as e:
            logger.warning(f"Failed to load patterns: {e}")
    
    def get_generation_improvements(self) -> Dict[str, Any]:
        """
        Get recommended improvements for code generation
        
        Returns:
            Dictionary with improvement recommendations
        """
        recommendations = {
            'error_weights': self.error_weights.copy(),
            'top_patterns': [],
            'prompt_adjustments': {},
            'critical_reminders': []
        }
        
        # Get top 5 most frequent patterns
        sorted_patterns = sorted(
            self.learned_patterns.values(),
            key=lambda p: p.occurrence_count,
            reverse=True
        )[:5]
        
        for pattern in sorted_patterns:
            recommendations['top_patterns'].append({
                'error_type': pattern.error_type,
                'description': pattern.description,
                'occurrences': pattern.occurrence_count,
                'fixes': pattern.recommended_fixes
            })
            
            # Aggregate prompt adjustments
            for key, value in pattern.prompt_adjustments.items():
                recommendations['prompt_adjustments'][key] = \
                    recommendations['prompt_adjustments'].get(key, 0) + value
        
        # Generate critical reminders based on patterns
        if any('import' in p.error_type for p in sorted_patterns):
            recommendations['critical_reminders'].append(
                "CRITICAL: Use parent.parent.parent (3 levels) for sys.path"
            )
        
        if any('key_error' in p.error_type or 'naming' in p.description.lower() for p in sorted_patterns):
            recommendations['critical_reminders'].append(
                "CRITICAL: Use lowercase indicator names (ema_12, not EMA_12)"
            )
        
        if any('encoding' in p.error_type for p in sorted_patterns):
            recommendations['critical_reminders'].append(
                "CRITICAL: Do not use emoji/unicode characters in output"
            )
        
        return recommendations
    
    def get_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get error statistics for specified time period
        
        Args:
            days: Number of days to include (default: 7)
        
        Returns:
            Statistics dictionary
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Total errors
        cursor.execute(
            'SELECT COUNT(*) FROM errors WHERE timestamp > ?',
            (cutoff_date,)
        )
        total_errors = cursor.fetchone()[0]
        
        # Errors by type
        cursor.execute('''
            SELECT error_type, COUNT(*) 
            FROM errors 
            WHERE timestamp > ?
            GROUP BY error_type
            ORDER BY COUNT(*) DESC
        ''', (cutoff_date,))
        errors_by_type = dict(cursor.fetchall())
        
        # Fix success rate
        cursor.execute('''
            SELECT 
                SUM(fix_successful) as fixed,
                COUNT(*) as total
            FROM errors
            WHERE timestamp > ? AND fix_attempts > 0
        ''', (cutoff_date,))
        fix_stats = cursor.fetchone()
        fix_rate = (fix_stats[0] / fix_stats[1] * 100) if fix_stats[1] > 0 else 0
        
        # Generation errors
        cursor.execute('''
            SELECT COUNT(*) 
            FROM errors 
            WHERE timestamp > ? AND is_generation_error = 1
        ''', (cutoff_date,))
        generation_errors = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'period_days': days,
            'total_errors': total_errors,
            'generation_errors': generation_errors,
            'generation_error_rate': (generation_errors / total_errors * 100) if total_errors > 0 else 0,
            'errors_by_type': errors_by_type,
            'fix_success_rate': fix_rate,
            'top_error_types': list(errors_by_type.keys())[:3]
        }
    
    def print_report(self, days: int = 7):
        """Print human-readable error learning report"""
        stats = self.get_statistics(days)
        improvements = self.get_generation_improvements()
        
        print("\n" + "="*70)
        print(f"ERROR LEARNING REPORT ({days} days)")
        print("="*70)
        
        print(f"\nOVERVIEW:")
        print(f"  Total Errors: {stats['total_errors']}")
        print(f"  Generation Errors: {stats['generation_errors']} ({stats['generation_error_rate']:.1f}%)")
        print(f"  Fix Success Rate: {stats['fix_success_rate']:.1f}%")
        
        print(f"\nTOP ERROR TYPES:")
        for error_type, count in list(stats['errors_by_type'].items())[:5]:
            print(f"  {error_type}: {count} occurrences")
        
        print(f"\nLEARNED PATTERNS ({len(self.learned_patterns)} total):")
        for pattern_info in improvements['top_patterns']:
            print(f"\n  [{pattern_info['error_type']}] {pattern_info['description']}")
            print(f"    Occurrences: {pattern_info['occurrences']}")
            print(f"    Recommended Fixes:")
            for fix in pattern_info['fixes']:
                print(f"      - {fix}")
        
        print(f"\nCRITICAL REMINDERS:")
        for reminder in improvements['critical_reminders']:
            print(f"  [!] {reminder}")
        
        print(f"\nERROR WEIGHTS (Prompt Emphasis):")
        for category, weight in sorted(improvements['error_weights'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {category}: {weight:.2f}")
        
        print("\n" + "="*70 + "\n")
