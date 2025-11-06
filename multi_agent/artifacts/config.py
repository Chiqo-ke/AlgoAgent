"""
Artifact Store Configuration

Settings for git-based artifact versioning and storage.
"""

from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class ArtifactStoreConfig:
    """Configuration for artifact storage and git operations."""
    
    # Git repository settings
    repo_path: Path = field(default_factory=lambda: Path.cwd())
    remote_name: str = "origin"
    
    # Branch naming
    branch_prefix: str = "ai/generated"
    
    # Commit settings
    commit_author_name: str = "algo-agent-bot"
    commit_author_email: str = "algo-agent@example.com"
    
    # Security
    scan_for_secrets: bool = True
    secret_patterns: list = field(default_factory=lambda: [
        r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{20,})",
        r"(?i)(secret[_-]?key|secretkey)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{20,})",
        r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"]?([^\s'\"]{8,})",
        r"(?i)(token)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{20,})",
        r"sk_test_[0-9a-zA-Z]{24,}",  # Stripe test keys
        r"sk_live_[0-9a-zA-Z]{24,}",  # Stripe live keys
        r"aws_access_key_id\s*=\s*[A-Z0-9]{20}",
        r"aws_secret_access_key\s*=\s*[A-Za-z0-9/+=]{40}",
    ])
    
    # Metadata
    include_metadata: bool = True
    metadata_filename: str = "metadata.json"
    
    # Push settings
    auto_push: bool = True
    push_timeout: int = 30  # seconds
    
    # Rollback
    max_rollback_depth: int = 10  # Keep track of last N commits
    
    # Validation
    require_test_passed: bool = True
    require_correlation_id: bool = True
    
    def __post_init__(self):
        """Validate configuration."""
        if isinstance(self.repo_path, str):
            self.repo_path = Path(self.repo_path)
        
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {self.repo_path}")
        
        # Ensure .git directory exists
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            raise ValueError(f"Not a git repository: {self.repo_path}")
