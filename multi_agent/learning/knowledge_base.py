"""
Knowledge Base for Error-Fix Mappings

Stores and retrieves learnings from past iterations to help agents
avoid repeating mistakes and apply successful fixes.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import hashlib


@dataclass
class ErrorPattern:
    """Represents an error pattern and its successful fix."""
    error_type: str
    error_signature: str  # Hash of normalized error message
    error_message: str
    fix_description: str
    fix_code_snippet: Optional[str]
    success_count: int
    last_used: str
    workflow_ids: List[str]
    tags: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ErrorPattern':
        return ErrorPattern(**data)


class KnowledgeBase:
    """
    Persistent storage for error-fix mappings.
    
    Features:
    - Store successful fixes with metadata
    - Search for similar errors
    - Track fix success rates
    - Export/import knowledge
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize knowledge base.
        
        Args:
            storage_path: Path to JSON storage file. Defaults to multi_agent/learning/knowledge.json
        """
        if storage_path is None:
            storage_path = Path(__file__).parent / "knowledge.json"
        
        self.storage_path = storage_path
        self.patterns: Dict[str, ErrorPattern] = {}
        
        # Load existing knowledge
        self._load()
    
    def _load(self):
        """Load knowledge from disk."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.patterns = {
                        sig: ErrorPattern.from_dict(pattern_data)
                        for sig, pattern_data in data.items()
                    }
                print(f"[KnowledgeBase] Loaded {len(self.patterns)} error patterns")
            except Exception as e:
                print(f"[KnowledgeBase] Error loading knowledge: {e}")
                self.patterns = {}
        else:
            print(f"[KnowledgeBase] No existing knowledge found, starting fresh")
            self.patterns = {}
    
    def _save(self):
        """Save knowledge to disk."""
        try:
            # Ensure directory exists
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert patterns to dict
            data = {
                sig: pattern.to_dict()
                for sig, pattern in self.patterns.items()
            }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            print(f"[KnowledgeBase] Saved {len(self.patterns)} patterns")
        except Exception as e:
            print(f"[KnowledgeBase] Error saving knowledge: {e}")
    
    @staticmethod
    def _normalize_error(error_message: str) -> str:
        """
        Normalize error message for better matching.
        
        Removes:
        - Line numbers
        - File paths
        - Variable names in some cases
        - Timestamps
        """
        import re
        
        # Remove file paths
        normalized = re.sub(r'[A-Za-z]:\\[^:]+\.\w+', '<FILE>', error_message)
        normalized = re.sub(r'/[\w/]+\.\w+', '<FILE>', normalized)
        
        # Remove line numbers
        normalized = re.sub(r'line \d+', 'line <N>', normalized)
        normalized = re.sub(r':\d+:', ':<N>:', normalized)
        
        # Remove timestamps
        normalized = re.sub(r'\d{4}-\d{2}-\d{2}', '<DATE>', normalized)
        normalized = re.sub(r'\d{2}:\d{2}:\d{2}', '<TIME>', normalized)
        
        # Remove specific variable names (keep pattern)
        # e.g., "NameError: name 'data' is not defined" -> "NameError: name '<VAR>' is not defined"
        normalized = re.sub(r"name '(\w+)' is not defined", "name '<VAR>' is not defined", normalized)
        
        return normalized.strip()
    
    @staticmethod
    def _hash_error(normalized_error: str) -> str:
        """Create hash signature for error pattern."""
        return hashlib.md5(normalized_error.encode()).hexdigest()[:12]
    
    def record_fix(
        self,
        error_type: str,
        error_message: str,
        fix_description: str,
        fix_code_snippet: Optional[str] = None,
        workflow_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ):
        """
        Record a successful fix in the knowledge base.
        
        Args:
            error_type: Type of error (e.g., 'NameError', 'timeout', 'import_error')
            error_message: Full error message
            fix_description: Description of the fix that worked
            fix_code_snippet: Optional code snippet showing the fix
            workflow_id: Workflow where this fix was successful
            tags: Tags for categorization (e.g., ['data_loading', 'pandas'])
        """
        normalized = self._normalize_error(error_message)
        signature = self._hash_error(normalized)
        
        if signature in self.patterns:
            # Update existing pattern
            pattern = self.patterns[signature]
            pattern.success_count += 1
            pattern.last_used = datetime.now().isoformat()
            if workflow_id and workflow_id not in pattern.workflow_ids:
                pattern.workflow_ids.append(workflow_id)
            print(f"[KnowledgeBase] ✅ Updated pattern {signature} (success_count: {pattern.success_count})")
        else:
            # Create new pattern
            pattern = ErrorPattern(
                error_type=error_type,
                error_signature=signature,
                error_message=normalized,
                fix_description=fix_description,
                fix_code_snippet=fix_code_snippet,
                success_count=1,
                last_used=datetime.now().isoformat(),
                workflow_ids=[workflow_id] if workflow_id else [],
                tags=tags or []
            )
            self.patterns[signature] = pattern
            print(f"[KnowledgeBase] 📝 Recorded new pattern {signature}")
        
        self._save()
    
    def search_similar_errors(
        self,
        error_message: str,
        error_type: Optional[str] = None,
        limit: int = 5
    ) -> List[ErrorPattern]:
        """
        Search for similar errors in knowledge base.
        
        Args:
            error_message: Error message to search for
            error_type: Optional filter by error type
            limit: Maximum number of results
            
        Returns:
            List of similar error patterns, sorted by relevance
        """
        normalized = self._normalize_error(error_message)
        signature = self._hash_error(normalized)
        
        # Exact match
        if signature in self.patterns:
            exact_match = self.patterns[signature]
            print(f"[KnowledgeBase] 🎯 Found exact match: {signature}")
            return [exact_match]
        
        # Fuzzy matching
        candidates = []
        for pattern in self.patterns.values():
            if error_type and pattern.error_type != error_type:
                continue
            
            # Simple similarity: check word overlap
            error_words = set(normalized.lower().split())
            pattern_words = set(pattern.error_message.lower().split())
            
            if len(error_words) == 0:
                continue
            
            overlap = len(error_words & pattern_words)
            similarity = overlap / len(error_words)
            
            if similarity > 0.5:  # At least 50% word overlap
                candidates.append((similarity, pattern))
        
        # Sort by similarity (descending) and success count
        candidates.sort(key=lambda x: (x[0], x[1].success_count), reverse=True)
        
        results = [pattern for _, pattern in candidates[:limit]]
        
        if results:
            print(f"[KnowledgeBase] 🔍 Found {len(results)} similar patterns")
        else:
            print(f"[KnowledgeBase] ❌ No similar patterns found")
        
        return results
    
    def get_top_fixes(self, limit: int = 10) -> List[ErrorPattern]:
        """Get most successful fixes."""
        sorted_patterns = sorted(
            self.patterns.values(),
            key=lambda p: p.success_count,
            reverse=True
        )
        return sorted_patterns[:limit]
    
    def get_recent_fixes(self, limit: int = 10) -> List[ErrorPattern]:
        """Get most recently used fixes."""
        sorted_patterns = sorted(
            self.patterns.values(),
            key=lambda p: p.last_used,
            reverse=True
        )
        return sorted_patterns[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        if not self.patterns:
            return {
                'total_patterns': 0,
                'error_types': {},
                'total_successes': 0,
                'most_successful': None
            }
        
        error_types = {}
        total_successes = 0
        
        for pattern in self.patterns.values():
            error_types[pattern.error_type] = error_types.get(pattern.error_type, 0) + 1
            total_successes += pattern.success_count
        
        most_successful = max(self.patterns.values(), key=lambda p: p.success_count)
        
        return {
            'total_patterns': len(self.patterns),
            'error_types': error_types,
            'total_successes': total_successes,
            'most_successful': {
                'error_type': most_successful.error_type,
                'signature': most_successful.error_signature,
                'success_count': most_successful.success_count,
                'fix': most_successful.fix_description
            }
        }
