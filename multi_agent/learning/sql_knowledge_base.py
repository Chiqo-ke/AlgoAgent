"""
SQL-backed Knowledge Base for Error-Fix Learning

Stores and retrieves learnings from iterations with full traceability
and analytics capabilities.
"""

import sqlite3
import json
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from contextlib import contextmanager


@dataclass
class ErrorLearning:
    """Represents a learned error pattern and its fix."""
    id: Optional[int]
    error_type: str
    error_signature: str
    error_message: str
    normalized_error: str
    fix_description: str
    fix_code_snippet: Optional[str]
    success_count: int
    failure_count: int
    first_seen: str
    last_used: str
    avg_fix_time: float  # seconds
    workflow_ids: str  # JSON array
    tags: str  # JSON array
    confidence_score: float  # 0.0 to 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # Parse JSON fields
        data['workflow_ids'] = json.loads(self.workflow_ids) if isinstance(self.workflow_ids, str) else self.workflow_ids
        data['tags'] = json.loads(self.tags) if isinstance(self.tags, str) else self.tags
        return data
    
    @staticmethod
    def from_row(row: tuple) -> 'ErrorLearning':
        """Create ErrorLearning from database row."""
        return ErrorLearning(*row)


@dataclass
class IterationLog:
    """Logs each iteration attempt for analytics."""
    id: Optional[int]
    workflow_id: str
    iteration_number: int
    timestamp: str
    error_type: str
    error_signature: str
    fix_attempted: str
    success: bool
    duration: float
    error_details: str  # JSON
    fix_details: str  # JSON
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['error_details'] = json.loads(self.error_details) if isinstance(self.error_details, str) else self.error_details
        data['fix_details'] = json.loads(self.fix_details) if isinstance(self.fix_details, str) else self.fix_details
        return data


class SQLKnowledgeBase:
    """
    SQL-backed knowledge base for persistent learning.
    
    Features:
    - Store error patterns and successful fixes
    - Track iteration history with full details
    - Search similar errors with confidence scoring
    - Analytics: success rates, common errors, fix effectiveness
    - Export/import for sharing learnings
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize SQL knowledge base.
        
        Args:
            db_path: Path to SQLite database. Defaults to multi_agent/learning/knowledge.db
        """
        if db_path is None:
            db_path = Path(__file__).parent / "knowledge.db"
        
        self.db_path = db_path
        self._init_database()
        print(f"[SQLKnowledgeBase] Initialized at {db_path}")
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_database(self):
        """Create database schema if not exists."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Error patterns table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS error_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_type TEXT NOT NULL,
                    error_signature TEXT UNIQUE NOT NULL,
                    error_message TEXT NOT NULL,
                    normalized_error TEXT NOT NULL,
                    fix_description TEXT NOT NULL,
                    fix_code_snippet TEXT,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    first_seen TEXT NOT NULL,
                    last_used TEXT NOT NULL,
                    avg_fix_time REAL DEFAULT 0.0,
                    workflow_ids TEXT DEFAULT '[]',
                    tags TEXT DEFAULT '[]',
                    confidence_score REAL DEFAULT 0.5,
                    UNIQUE(error_signature)
                )
            """)
            
            # Iteration logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS iteration_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT NOT NULL,
                    iteration_number INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    error_type TEXT NOT NULL,
                    error_signature TEXT NOT NULL,
                    fix_attempted TEXT NOT NULL,
                    success INTEGER NOT NULL,
                    duration REAL NOT NULL,
                    error_details TEXT NOT NULL,
                    fix_details TEXT NOT NULL,
                    FOREIGN KEY (error_signature) REFERENCES error_patterns(error_signature)
                )
            """)
            
            # Error type statistics (for quick analytics)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS error_type_stats (
                    error_type TEXT PRIMARY KEY,
                    total_occurrences INTEGER DEFAULT 0,
                    total_fixes INTEGER DEFAULT 0,
                    avg_iterations_to_fix REAL DEFAULT 0.0,
                    last_occurrence TEXT
                )
            """)
            
            # Create indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_error_type 
                ON error_patterns(error_type)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_confidence 
                ON error_patterns(confidence_score DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_workflow 
                ON iteration_logs(workflow_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON iteration_logs(timestamp)
            """)
            
            print("[SQLKnowledgeBase] Database schema initialized")
    
    @staticmethod
    def normalize_error(error_message: str) -> str:
        """
        Normalize error message for better matching.
        
        Removes:
        - File paths (keeps structure)
        - Line numbers (keeps position indicators)
        - Variable names (keeps patterns)
        - Timestamps
        """
        # Remove file paths
        normalized = re.sub(r'[A-Za-z]:\\[^:]+\.\w+', '<FILE>', error_message)
        normalized = re.sub(r'/[\w/]+\.\w+', '<FILE>', normalized)
        
        # Remove line numbers but keep "line" keyword
        normalized = re.sub(r'line \d+', 'line <N>', normalized)
        normalized = re.sub(r':\d+:', ':<N>:', normalized)
        
        # Remove timestamps
        normalized = re.sub(r'\d{4}-\d{2}-\d{2}', '<DATE>', normalized)
        normalized = re.sub(r'\d{2}:\d{2}:\d{2}', '<TIME>', normalized)
        
        # Remove specific variable/function names but keep patterns
        normalized = re.sub(r"name '(\w+)' is not defined", "name '<VAR>' is not defined", normalized)
        normalized = re.sub(r"'(\w+)' object has no attribute", "'<OBJ>' object has no attribute", normalized)
        normalized = re.sub(r"missing \d+ required", "missing <N> required", normalized)
        
        # Normalize whitespace
        normalized = ' '.join(normalized.split())
        
        return normalized.strip()
    
    @staticmethod
    def hash_error(normalized_error: str) -> str:
        """Create hash signature for error pattern."""
        return hashlib.sha256(normalized_error.encode()).hexdigest()[:16]
    
    @staticmethod
    def classify_error_advanced(error_message: str) -> str:
        """
        Advanced error classification with regex patterns.
        
        Returns specific error type instead of generic 'unknown_error'.
        """
        error_lower = error_message.lower()
        
        # Syntax errors
        if re.search(r'syntaxerror|invalid syntax|indentationerror|unexpected indent|unexpected eof', error_lower):
            return 'syntax_error'
        
        # Import errors
        elif re.search(r'importerror|modulenotfounderror|no module named|cannot import', error_lower):
            return 'import_error'
        
        # Attribute errors (object has no attribute)
        elif re.search(r'attributeerror|has no attribute|object.*no attribute', error_lower):
            return 'attribute_error'
        
        # Type errors
        elif re.search(r'typeerror|expected.*got|takes.*positional|missing.*required', error_lower):
            return 'type_error'
        
        # Name errors (undefined variables)
        elif re.search(r'nameerror|name.*not defined|undefined', error_lower):
            return 'name_error'
        
        # Key errors (dict key missing)
        elif re.search(r'keyerror|key.*not found', error_lower):
            return 'key_error'
        
        # Index errors (list/array out of bounds)
        elif re.search(r'indexerror|index out of|out of bounds', error_lower):
            return 'index_error'
        
        # Value errors
        elif re.search(r'valueerror|invalid value|cannot convert', error_lower):
            return 'value_error'
        
        # File/IO errors
        elif re.search(r'filenotfounderror|ioerror|permission denied|no such file', error_lower):
            return 'file_error'
        
        # Timeout errors
        elif re.search(r'timeout|timed out|time limit exceeded', error_lower):
            return 'timeout_error'
        
        # Memory errors
        elif re.search(r'memoryerror|out of memory|memory limit', error_lower):
            return 'memory_error'
        
        # Assertion errors (test failures)
        elif re.search(r'assertionerror|assertion failed|expected.*but|should.*but', error_lower):
            return 'assertion_error'
        
        # Connection/Network errors
        elif re.search(r'connectionerror|connection refused|network|socket', error_lower):
            return 'connection_error'
        
        # Permission errors
        elif re.search(r'permissionerror|access denied|forbidden', error_lower):
            return 'permission_error'
        
        # Runtime errors (generic)
        elif re.search(r'runtimeerror|runtime error', error_lower):
            return 'runtime_error'
        
        # Zero division
        elif re.search(r'zerodivisionerror|division by zero', error_lower):
            return 'zero_division_error'
        
        # Recursion errors
        elif re.search(r'recursionerror|maximum recursion', error_lower):
            return 'recursion_error'
        
        # If still no match, try to extract error class name
        else:
            # Look for XxxError pattern
            match = re.search(r'(\w+error)', error_lower)
            if match:
                return match.group(1)
            
            # Look for failure indicators
            if re.search(r'failed|failure|error|exception', error_lower):
                return 'general_error'
            
            return 'unclassified_error'
    
    def record_iteration(
        self,
        workflow_id: str,
        iteration_number: int,
        error_type: str,
        error_message: str,
        fix_attempted: str,
        success: bool,
        duration: float,
        error_details: Optional[Dict] = None,
        fix_details: Optional[Dict] = None
    ) -> int:
        """
        Record an iteration attempt in the database.
        
        Args:
            workflow_id: Workflow identifier
            iteration_number: Iteration count
            error_type: Classified error type
            error_message: Full error message
            fix_attempted: Description of fix attempted
            success: Whether the fix succeeded
            duration: Time taken for this iteration
            error_details: Additional error context (dict)
            fix_details: Additional fix context (dict)
            
        Returns:
            Iteration log ID
        """
        normalized = self.normalize_error(error_message)
        signature = self.hash_error(normalized)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO iteration_logs 
                (workflow_id, iteration_number, timestamp, error_type, error_signature,
                 fix_attempted, success, duration, error_details, fix_details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                workflow_id,
                iteration_number,
                datetime.now().isoformat(),
                error_type,
                signature,
                fix_attempted,
                1 if success else 0,
                duration,
                json.dumps(error_details or {}),
                json.dumps(fix_details or {})
            ))
            
            log_id = cursor.lastrowid
            
            # Update error type stats
            cursor.execute("""
                INSERT INTO error_type_stats (error_type, total_occurrences, last_occurrence)
                VALUES (?, 1, ?)
                ON CONFLICT(error_type) DO UPDATE SET
                    total_occurrences = total_occurrences + 1,
                    last_occurrence = ?
            """, (error_type, datetime.now().isoformat(), datetime.now().isoformat()))
            
            if success:
                cursor.execute("""
                    UPDATE error_type_stats 
                    SET total_fixes = total_fixes + 1
                    WHERE error_type = ?
                """, (error_type,))
            
            print(f"[SQLKnowledgeBase] 📊 Recorded iteration {iteration_number} for {workflow_id}")
            
            return log_id
    
    def record_successful_fix(
        self,
        error_type: str,
        error_message: str,
        fix_description: str,
        fix_code_snippet: Optional[str] = None,
        workflow_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        fix_time: float = 0.0
    ):
        """
        Record a successful fix in the knowledge base.
        
        Args:
            error_type: Type of error fixed
            error_message: Original error message
            fix_description: Description of the successful fix
            fix_code_snippet: Optional code snippet showing the fix
            workflow_id: Workflow where this fix succeeded
            tags: Tags for categorization
            fix_time: Time taken to fix (seconds)
        """
        normalized = self.normalize_error(error_message)
        signature = self.hash_error(normalized)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if pattern exists
            cursor.execute("""
                SELECT * FROM error_patterns WHERE error_signature = ?
            """, (signature,))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing pattern
                old_success = existing['success_count']
                new_success = old_success + 1
                old_avg_time = existing['avg_fix_time']
                
                # Calculate new average fix time
                new_avg_time = ((old_avg_time * old_success) + fix_time) / new_success
                
                # Update confidence score (success rate)
                total_attempts = new_success + existing['failure_count']
                confidence = new_success / total_attempts if total_attempts > 0 else 0.5
                
                # Merge workflow IDs
                old_workflows = json.loads(existing['workflow_ids'])
                if workflow_id and workflow_id not in old_workflows:
                    old_workflows.append(workflow_id)
                
                cursor.execute("""
                    UPDATE error_patterns SET
                        success_count = ?,
                        last_used = ?,
                        avg_fix_time = ?,
                        workflow_ids = ?,
                        confidence_score = ?
                    WHERE error_signature = ?
                """, (
                    new_success,
                    datetime.now().isoformat(),
                    new_avg_time,
                    json.dumps(old_workflows),
                    confidence,
                    signature
                ))
                
                print(f"[SQLKnowledgeBase] ✅ Updated pattern {signature[:8]}... (success: {new_success}, confidence: {confidence:.2f})")
            else:
                # Create new pattern
                cursor.execute("""
                    INSERT INTO error_patterns 
                    (error_type, error_signature, error_message, normalized_error,
                     fix_description, fix_code_snippet, success_count, failure_count,
                     first_seen, last_used, avg_fix_time, workflow_ids, tags, confidence_score)
                    VALUES (?, ?, ?, ?, ?, ?, 1, 0, ?, ?, ?, ?, ?, 0.8)
                """, (
                    error_type,
                    signature,
                    error_message[:500],  # Truncate for storage
                    normalized,
                    fix_description,
                    fix_code_snippet,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    fix_time,
                    json.dumps([workflow_id] if workflow_id else []),
                    json.dumps(tags or [])
                ))
                
                print(f"[SQLKnowledgeBase] 📝 Recorded new pattern {signature[:8]}... ({error_type})")
    
    def record_failed_fix(
        self,
        error_type: str,
        error_message: str,
        fix_attempted: str
    ):
        """
        Record a failed fix attempt to improve confidence scores.
        
        Args:
            error_type: Type of error
            error_message: Error message
            fix_attempted: Description of fix that failed
        """
        normalized = self.normalize_error(error_message)
        signature = self.hash_error(normalized)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM error_patterns WHERE error_signature = ?
            """, (signature,))
            
            existing = cursor.fetchone()
            
            if existing:
                new_failure_count = existing['failure_count'] + 1
                total_attempts = existing['success_count'] + new_failure_count
                confidence = existing['success_count'] / total_attempts if total_attempts > 0 else 0.3
                
                cursor.execute("""
                    UPDATE error_patterns SET
                        failure_count = ?,
                        confidence_score = ?
                    WHERE error_signature = ?
                """, (new_failure_count, confidence, signature))
                
                print(f"[SQLKnowledgeBase] ⚠️  Updated failed attempt for {signature[:8]}... (confidence: {confidence:.2f})")
    
    def search_similar_errors(
        self,
        error_message: str,
        error_type: Optional[str] = None,
        limit: int = 5,
        min_confidence: float = 0.3
    ) -> List[ErrorLearning]:
        """
        Search for similar errors with fixes.
        
        Args:
            error_message: Error to search for
            error_type: Optional filter by error type
            limit: Maximum results
            min_confidence: Minimum confidence score (0.0 to 1.0)
            
        Returns:
            List of ErrorLearning objects sorted by relevance
        """
        normalized = self.normalize_error(error_message)
        signature = self.hash_error(normalized)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # First try exact match
            cursor.execute("""
                SELECT * FROM error_patterns 
                WHERE error_signature = ? AND confidence_score >= ?
            """, (signature, min_confidence))
            
            exact_match = cursor.fetchone()
            
            if exact_match:
                print(f"[SQLKnowledgeBase] 🎯 Found exact match for error (confidence: {exact_match['confidence_score']:.2f})")
                return [ErrorLearning.from_row(tuple(exact_match))]
            
            # Try similar errors by type
            query = """
                SELECT * FROM error_patterns 
                WHERE confidence_score >= ?
            """
            params = [min_confidence]
            
            if error_type:
                query += " AND error_type = ?"
                params.append(error_type)
            
            query += """
                ORDER BY confidence_score DESC, success_count DESC
                LIMIT ?
            """
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            if rows:
                print(f"[SQLKnowledgeBase] 🔍 Found {len(rows)} similar error patterns")
                return [ErrorLearning.from_row(tuple(row)) for row in rows]
            else:
                print(f"[SQLKnowledgeBase] ❌ No similar errors found")
                return []
    
    def get_analytics(self) -> Dict[str, Any]:
        """
        Get analytics about learnings and error patterns.
        
        Returns:
            Dictionary with analytics data
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Total patterns
            cursor.execute("SELECT COUNT(*) FROM error_patterns")
            total_patterns = cursor.fetchone()[0]
            
            # Total iterations logged
            cursor.execute("SELECT COUNT(*) FROM iteration_logs")
            total_iterations = cursor.fetchone()[0]
            
            # Success rate
            cursor.execute("SELECT SUM(success) FROM iteration_logs")
            total_successes = cursor.fetchone()[0] or 0
            success_rate = (total_successes / total_iterations * 100) if total_iterations > 0 else 0
            
            # Error type stats
            cursor.execute("""
                SELECT error_type, total_occurrences, total_fixes, 
                       CASE WHEN total_occurrences > 0 
                            THEN CAST(total_fixes AS REAL) / total_occurrences * 100
                            ELSE 0 END as fix_rate
                FROM error_type_stats
                ORDER BY total_occurrences DESC
                LIMIT 10
            """)
            error_stats = [dict(row) for row in cursor.fetchall()]
            
            # Top fixes by confidence
            cursor.execute("""
                SELECT error_type, error_signature, fix_description, 
                       success_count, confidence_score
                FROM error_patterns
                ORDER BY confidence_score DESC, success_count DESC
                LIMIT 10
            """)
            top_fixes = [dict(row) for row in cursor.fetchall()]
            
            return {
                'total_patterns': total_patterns,
                'total_iterations': total_iterations,
                'total_successes': total_successes,
                'success_rate': round(success_rate, 2),
                'error_type_stats': error_stats,
                'top_fixes': top_fixes
            }
    
    def export_knowledge(self, export_path: Path):
        """Export all learnings to JSON file."""
        analytics = self.get_analytics()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get all patterns
            cursor.execute("SELECT * FROM error_patterns")
            patterns = [dict(row) for row in cursor.fetchall()]
            
            # Get recent iterations
            cursor.execute("""
                SELECT * FROM iteration_logs 
                ORDER BY timestamp DESC 
                LIMIT 100
            """)
            recent_iterations = [dict(row) for row in cursor.fetchall()]
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'analytics': analytics,
            'patterns': patterns,
            'recent_iterations': recent_iterations
        }
        
        # Ensure parent directory exists (but don't try to create if it already exists)
        try:
            if not export_path.parent.exists():
                export_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass  # Directory might already exist in concurrent scenarios
        
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"[SQLKnowledgeBase] 💾 Exported {len(patterns)} patterns to {export_path}")


# Singleton instance
_instance = None


def get_knowledge_base() -> SQLKnowledgeBase:
    """Get or create singleton knowledge base instance."""
    global _instance
    if _instance is None:
        _instance = SQLKnowledgeBase()
    return _instance
