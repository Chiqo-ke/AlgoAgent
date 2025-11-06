"""
Artifact Store - Git-Based Versioning for Generated Code

Manages versioning and storage of AI-generated strategy code and test artifacts
using git branches, commits, and tags.
"""

import json
import logging
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from artifacts.config import ArtifactStoreConfig


logger = logging.getLogger(__name__)


class ArtifactStoreError(Exception):
    """Base exception for artifact store operations."""
    pass


class SecretDetectedError(ArtifactStoreError):
    """Raised when hardcoded secrets are found in artifacts."""
    pass


class ArtifactStore:
    """
    Git-based artifact storage with versioning and rollback support.
    
    Creates branches for each workflow/task, commits artifacts with metadata,
    tags commits for easy retrieval, and supports rollback operations.
    """
    
    def __init__(self, config: Optional[ArtifactStoreConfig] = None):
        """
        Initialize artifact store.
        
        Args:
            config: Configuration settings (uses defaults if None)
        """
        self.config = config or ArtifactStoreConfig()
        self.repo_path = self.config.repo_path
        
        logger.info(f"Initialized ArtifactStore at {self.repo_path}")
    
    def commit_artifacts(
        self,
        workflow_id: str,
        task_id: str,
        files: List[Path],
        metadata: Dict,
        correlation_id: Optional[str] = None,
        prompt_hash: Optional[str] = None
    ) -> Dict:
        """
        Commit artifacts to git with proper branching and tagging.
        
        Workflow:
        1. Scan files for secrets (if enabled)
        2. Create branch: ai/generated/<workflow_id>/<task_id>
        3. Copy files to repo
        4. Create metadata.json
        5. Commit with descriptive message
        6. Tag with correlation_id and prompt_hash
        7. Push to remote (if enabled)
        
        Args:
            workflow_id: Workflow identifier
            task_id: Task identifier
            files: List of file paths to commit
            metadata: Additional metadata (test metrics, agent version, etc.)
            correlation_id: Correlation ID for tracing
            prompt_hash: Hash of original prompt
        
        Returns:
            {
                'success': bool,
                'branch': str,
                'commit_sha': str,
                'tags': List[str],
                'pushed': bool,
                'error': str (if failed)
            }
        
        Raises:
            SecretDetectedError: If secrets found in files
            ArtifactStoreError: If git operations fail
        """
        try:
            # Validate inputs
            if self.config.require_correlation_id and not correlation_id:
                raise ArtifactStoreError("correlation_id is required")
            
            # 1. Scan for secrets
            if self.config.scan_for_secrets:
                secrets_found = self._scan_files_for_secrets(files)
                if secrets_found:
                    raise SecretDetectedError(
                        f"Secrets detected in {len(secrets_found)} file(s): "
                        f"{', '.join(str(f) for f in secrets_found)}"
                    )
            
            # 2. Create branch
            branch_name = f"{self.config.branch_prefix}/{workflow_id}/{task_id}"
            self._create_branch(branch_name)
            
            # 3. Copy files to repo
            target_dir = self.repo_path / "Backtest" / "codes" / task_id
            target_dir.mkdir(parents=True, exist_ok=True)
            
            copied_files = []
            for file_path in files:
                if not file_path.exists():
                    logger.warning(f"File not found: {file_path}")
                    continue
                
                target_path = target_dir / file_path.name
                target_path.write_bytes(file_path.read_bytes())
                copied_files.append(target_path)
                logger.info(f"Copied {file_path.name} to {target_path}")
            
            # 4. Create metadata.json
            if self.config.include_metadata:
                metadata_content = {
                    "workflow_id": workflow_id,
                    "task_id": task_id,
                    "correlation_id": correlation_id,
                    "prompt_hash": prompt_hash,
                    "commit_timestamp": datetime.utcnow().isoformat(),
                    "agent_version": metadata.get("agent_version", "unknown"),
                    "llm_version": metadata.get("llm_version", "unknown"),
                    "test_metrics": metadata.get("test_metrics", {}),
                    "files": [str(f.relative_to(self.repo_path)) for f in copied_files]
                }
                
                metadata_path = target_dir / self.config.metadata_filename
                metadata_path.write_text(json.dumps(metadata_content, indent=2))
                copied_files.append(metadata_path)
            
            # 5. Stage and commit
            self._git_add(copied_files)
            
            commit_message = self._create_commit_message(
                workflow_id, task_id, correlation_id, metadata
            )
            commit_sha = self._git_commit(commit_message)
            
            # 6. Create tags
            tags = []
            if correlation_id:
                tag_name = f"corr_{correlation_id}"
                self._git_tag(tag_name, commit_sha)
                tags.append(tag_name)
            
            if prompt_hash:
                tag_name = f"prompt_{prompt_hash[:12]}"
                self._git_tag(tag_name, commit_sha)
                tags.append(tag_name)
            
            # 7. Push to remote
            pushed = False
            if self.config.auto_push:
                try:
                    self._git_push(branch_name, tags)
                    pushed = True
                except subprocess.CalledProcessError as e:
                    logger.warning(f"Push failed: {e}. Artifacts committed locally.")
            
            logger.info(
                f"Successfully committed artifacts: branch={branch_name}, "
                f"commit={commit_sha[:8]}, tags={tags}, pushed={pushed}"
            )
            
            return {
                "success": True,
                "branch": branch_name,
                "commit_sha": commit_sha,
                "tags": tags,
                "pushed": pushed,
                "files": [str(f.relative_to(self.repo_path)) for f in copied_files]
            }
        
        except SecretDetectedError:
            raise
        except Exception as e:
            logger.error(f"Failed to commit artifacts: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def revert_to_tag(self, tag: str, target_branch: str = "main") -> Dict:
        """
        Revert to a previous artifact version by tag.
        
        Args:
            tag: Git tag to revert to (e.g., "corr_abc123")
            target_branch: Branch to apply revert on
        
        Returns:
            {
                'success': bool,
                'commit_sha': str,
                'reverted_to': str,
                'error': str (if failed)
            }
        """
        try:
            # Verify tag exists
            if not self._git_tag_exists(tag):
                raise ArtifactStoreError(f"Tag not found: {tag}")
            
            # Checkout target branch
            self._git_checkout(target_branch)
            
            # Create revert commit
            commit_sha = self._git_revert_to_tag(tag)
            
            logger.info(f"Reverted {target_branch} to tag {tag}: {commit_sha[:8]}")
            
            return {
                "success": True,
                "commit_sha": commit_sha,
                "reverted_to": tag,
                "branch": target_branch
            }
        
        except Exception as e:
            logger.error(f"Failed to revert to tag {tag}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_artifacts(
        self,
        workflow_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        List committed artifacts with metadata.
        
        Args:
            workflow_id: Filter by workflow ID (None = all)
            limit: Maximum number of results
        
        Returns:
            List of artifact metadata dicts
        """
        try:
            branch_pattern = f"{self.config.branch_prefix}/"
            if workflow_id:
                branch_pattern += f"{workflow_id}/"
            
            branches = self._git_list_branches(branch_pattern)
            
            artifacts = []
            for branch in branches[:limit]:
                try:
                    metadata = self._read_branch_metadata(branch)
                    if metadata:
                        artifacts.append(metadata)
                except Exception as e:
                    logger.warning(f"Failed to read metadata for {branch}: {e}")
            
            return artifacts
        
        except Exception as e:
            logger.error(f"Failed to list artifacts: {e}")
            return []
    
    def get_artifact_by_correlation_id(self, correlation_id: str) -> Optional[Dict]:
        """
        Retrieve artifact metadata by correlation ID.
        
        Args:
            correlation_id: Correlation ID to search for
        
        Returns:
            Artifact metadata dict or None if not found
        """
        tag = f"corr_{correlation_id}"
        
        if not self._git_tag_exists(tag):
            return None
        
        try:
            commit_sha = self._git_tag_commit(tag)
            metadata = self._read_commit_metadata(commit_sha)
            return metadata
        except Exception as e:
            logger.error(f"Failed to get artifact for {correlation_id}: {e}")
            return None
    
    # Private helper methods
    
    def _scan_files_for_secrets(self, files: List[Path]) -> List[Path]:
        """Scan files for hardcoded secrets using regex patterns."""
        files_with_secrets = []
        
        for file_path in files:
            try:
                content = file_path.read_text()
                
                for pattern in self.config.secret_patterns:
                    if re.search(pattern, content):
                        files_with_secrets.append(file_path)
                        logger.warning(
                            f"Secret pattern detected in {file_path.name}: {pattern}"
                        )
                        break
            except Exception as e:
                logger.warning(f"Failed to scan {file_path}: {e}")
        
        return files_with_secrets
    
    def _create_branch(self, branch_name: str):
        """Create and checkout new branch."""
        try:
            # Check if branch exists
            result = subprocess.run(
                ["git", "rev-parse", "--verify", branch_name],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Branch exists, checkout
                logger.info(f"Branch {branch_name} exists, checking out")
                self._git_checkout(branch_name)
            else:
                # Create new branch
                logger.info(f"Creating new branch: {branch_name}")
                subprocess.run(
                    ["git", "checkout", "-b", branch_name],
                    cwd=self.repo_path,
                    check=True,
                    capture_output=True
                )
        except subprocess.CalledProcessError as e:
            raise ArtifactStoreError(f"Failed to create branch {branch_name}: {e}")
    
    def _git_checkout(self, branch: str):
        """Checkout branch."""
        try:
            subprocess.run(
                ["git", "checkout", branch],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            raise ArtifactStoreError(f"Failed to checkout {branch}: {e}")
    
    def _git_add(self, files: List[Path]):
        """Stage files for commit."""
        try:
            file_paths = [str(f.relative_to(self.repo_path)) for f in files]
            subprocess.run(
                ["git", "add"] + file_paths,
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            raise ArtifactStoreError(f"Failed to stage files: {e}")
    
    def _git_commit(self, message: str) -> str:
        """Create commit and return SHA."""
        try:
            # Set author
            env = {
                "GIT_AUTHOR_NAME": self.config.commit_author_name,
                "GIT_AUTHOR_EMAIL": self.config.commit_author_email,
                "GIT_COMMITTER_NAME": self.config.commit_author_name,
                "GIT_COMMITTER_EMAIL": self.config.commit_author_email,
            }
            
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.repo_path,
                env={**subprocess.os.environ, **env},
                check=True,
                capture_output=True
            )
            
            # Get commit SHA
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            
            return result.stdout.strip()
        
        except subprocess.CalledProcessError as e:
            raise ArtifactStoreError(f"Failed to commit: {e}")
    
    def _git_tag(self, tag_name: str, commit_sha: str):
        """Create annotated tag."""
        try:
            subprocess.run(
                ["git", "tag", "-a", tag_name, commit_sha, "-m", f"Tag {tag_name}"],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to create tag {tag_name}: {e}")
    
    def _git_push(self, branch: str, tags: List[str]):
        """Push branch and tags to remote."""
        try:
            # Push branch
            subprocess.run(
                ["git", "push", self.config.remote_name, branch],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                timeout=self.config.push_timeout
            )
            
            # Push tags
            if tags:
                subprocess.run(
                    ["git", "push", self.config.remote_name] + tags,
                    cwd=self.repo_path,
                    check=True,
                    capture_output=True,
                    timeout=self.config.push_timeout
                )
        except subprocess.CalledProcessError as e:
            raise ArtifactStoreError(f"Failed to push: {e}")
    
    def _git_tag_exists(self, tag: str) -> bool:
        """Check if tag exists."""
        try:
            result = subprocess.run(
                ["git", "tag", "-l", tag],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            return tag in result.stdout.strip()
        except Exception:
            return False
    
    def _git_tag_commit(self, tag: str) -> str:
        """Get commit SHA for tag."""
        try:
            result = subprocess.run(
                ["git", "rev-list", "-n", "1", tag],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise ArtifactStoreError(f"Failed to get commit for tag {tag}: {e}")
    
    def _git_revert_to_tag(self, tag: str) -> str:
        """Revert current branch to tagged commit."""
        try:
            commit_sha = self._git_tag_commit(tag)
            
            # Create revert commit
            subprocess.run(
                ["git", "revert", "--no-commit", f"{commit_sha}..HEAD"],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            
            message = f"Revert to {tag} ({commit_sha[:8]})"
            return self._git_commit(message)
        
        except subprocess.CalledProcessError as e:
            raise ArtifactStoreError(f"Failed to revert to {tag}: {e}")
    
    def _git_list_branches(self, pattern: str) -> List[str]:
        """List branches matching pattern."""
        try:
            result = subprocess.run(
                ["git", "branch", "-a", "--list", f"*{pattern}*"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            branches = []
            for line in result.stdout.strip().split('\n'):
                branch = line.strip().lstrip('* ').replace('remotes/origin/', '')
                if branch and pattern in branch:
                    branches.append(branch)
            
            return branches
        except Exception as e:
            logger.error(f"Failed to list branches: {e}")
            return []
    
    def _read_branch_metadata(self, branch: str) -> Optional[Dict]:
        """Read metadata.json from branch."""
        try:
            # Get file content from branch
            result = subprocess.run(
                ["git", "show", f"{branch}:Backtest/codes/*/metadata.json"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            return None
        except Exception:
            return None
    
    def _read_commit_metadata(self, commit_sha: str) -> Optional[Dict]:
        """Read metadata.json from commit."""
        try:
            result = subprocess.run(
                ["git", "show", f"{commit_sha}:Backtest/codes/*/metadata.json"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                metadata = json.loads(result.stdout)
                metadata['commit_sha'] = commit_sha
                return metadata
            return None
        except Exception:
            return None
    
    def _create_commit_message(
        self,
        workflow_id: str,
        task_id: str,
        correlation_id: Optional[str],
        metadata: Dict
    ) -> str:
        """Create descriptive commit message."""
        lines = [
            f"Add artifacts for {workflow_id}/{task_id}",
            "",
            f"Workflow: {workflow_id}",
            f"Task: {task_id}",
        ]
        
        if correlation_id:
            lines.append(f"Correlation: {correlation_id}")
        
        if "test_metrics" in metadata:
            metrics = metadata["test_metrics"]
            lines.append("")
            lines.append("Test Metrics:")
            for key, value in metrics.items():
                lines.append(f"  {key}: {value}")
        
        lines.append("")
        lines.append(f"Agent: {metadata.get('agent_version', 'unknown')}")
        lines.append(f"LLM: {metadata.get('llm_version', 'unknown')}")
        
        return "\n".join(lines)
