"""
Git Patch Manager
=================

Safe code patching using git branches for isolation and rollback.

Features:
- Branch-based isolation for each generation/fix attempt
- Automatic commit of changes
- Diff generation for review
- Easy rollback on failures
- PR creation workflow support

Version: 1.0.0
"""

from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
import subprocess
import logging
import json
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# SCHEMAS
# ============================================================================

class GitBranch(BaseModel):
    """Git branch information"""
    name: str
    commit_hash: str
    created_at: datetime = Field(default_factory=datetime.now)
    parent_branch: str = "main"
    purpose: str  # generation, fix, test


class PatchInfo(BaseModel):
    """Information about a code patch"""
    patch_id: str
    branch_name: str
    files_changed: List[str]
    additions: int
    deletions: int
    diff: str
    commit_message: str
    created_at: datetime = Field(default_factory=datetime.now)


# ============================================================================
# GIT PATCH MANAGER
# ============================================================================

class GitPatchManager:
    """
    Manages safe code patching using git branches
    """
    
    def __init__(self, repo_path: Path):
        """
        Initialize git patch manager
        
        Args:
            repo_path: Path to git repository
        """
        self.repo_path = Path(repo_path).resolve()
        
        # Verify it's a git repo
        if not (self.repo_path / ".git").exists():
            raise ValueError(f"Not a git repository: {repo_path}")
        
        self._ensure_git_configured()
    
    def _ensure_git_configured(self):
        """Ensure git is configured for automated commits"""
        try:
            # Check if user.name is set
            result = self._run_git_command(["config", "user.name"])
            if not result["stdout"].strip():
                self._run_git_command(["config", "user.name", "AI Agent"])
            
            # Check if user.email is set
            result = self._run_git_command(["config", "user.email"])
            if not result["stdout"].strip():
                self._run_git_command(["config", "user.email", "ai-agent@localhost"])
        
        except Exception as e:
            logger.warning(f"Failed to configure git: {e}")
    
    def _run_git_command(
        self,
        args: List[str],
        check: bool = True
    ) -> Dict[str, Any]:
        """
        Run git command
        
        Args:
            args: Git command arguments
            check: Whether to raise on non-zero exit
            
        Returns:
            Dict with stdout, stderr, returncode
        """
        result = subprocess.run(
            ["git"] + args,
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )
        
        if check and result.returncode != 0:
            raise RuntimeError(f"Git command failed: {result.stderr}")
        
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    
    def get_current_branch(self) -> str:
        """Get name of current branch"""
        result = self._run_git_command(["branch", "--show-current"])
        return result["stdout"].strip()
    
    def create_work_branch(
        self,
        strategy_name: str,
        purpose: str = "generation",
        parent_branch: str = "main"
    ) -> GitBranch:
        """
        Create a new work branch for isolated changes
        
        Args:
            strategy_name: Name of strategy being worked on
            purpose: Purpose of branch (generation, fix, test)
            parent_branch: Parent branch to branch from
            
        Returns:
            GitBranch info
        """
        # Generate branch name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        branch_name = f"ai/{purpose}/{strategy_name}/{timestamp}"
        
        # Ensure we're on parent branch
        self._run_git_command(["checkout", parent_branch])
        
        # Create and checkout new branch
        self._run_git_command(["checkout", "-b", branch_name])
        
        # Get commit hash
        result = self._run_git_command(["rev-parse", "HEAD"])
        commit_hash = result["stdout"].strip()
        
        branch = GitBranch(
            name=branch_name,
            commit_hash=commit_hash,
            parent_branch=parent_branch,
            purpose=purpose
        )
        
        logger.info(f"Created work branch: {branch_name}")
        
        return branch
    
    def commit_changes(
        self,
        files: List[str],
        message: str
    ) -> str:
        """
        Commit changes to current branch
        
        Args:
            files: List of file paths to commit
            message: Commit message
            
        Returns:
            Commit hash
        """
        # Stage files
        for file_path in files:
            self._run_git_command(["add", str(file_path)])
        
        # Commit
        self._run_git_command(["commit", "-m", message])
        
        # Get commit hash
        result = self._run_git_command(["rev-parse", "HEAD"])
        commit_hash = result["stdout"].strip()
        
        logger.info(f"Committed changes: {commit_hash[:8]} - {message}")
        
        return commit_hash
    
    def get_diff(
        self,
        branch_a: str = "HEAD",
        branch_b: str = "main",
        file_path: Optional[str] = None
    ) -> str:
        """
        Get diff between branches or commits
        
        Args:
            branch_a: First branch/commit
            branch_b: Second branch/commit
            file_path: Optional specific file to diff
            
        Returns:
            Diff string
        """
        args = ["diff", branch_b, branch_a]
        if file_path:
            args.append("--")
            args.append(file_path)
        
        result = self._run_git_command(args, check=False)
        return result["stdout"]
    
    def get_patch_info(
        self,
        branch_name: Optional[str] = None
    ) -> PatchInfo:
        """
        Get information about changes in branch
        
        Args:
            branch_name: Branch to analyze (defaults to current)
            
        Returns:
            PatchInfo
        """
        if branch_name:
            original_branch = self.get_current_branch()
            self._run_git_command(["checkout", branch_name])
        else:
            branch_name = self.get_current_branch()
        
        try:
            # Get diff stats
            result = self._run_git_command(["diff", "--stat", "main"])
            stats_output = result["stdout"]
            
            # Parse stats
            files_changed = []
            additions = 0
            deletions = 0
            
            for line in stats_output.split('\n'):
                if '|' in line:
                    file_name = line.split('|')[0].strip()
                    files_changed.append(file_name)
                elif 'insertion' in line or 'deletion' in line:
                    parts = line.split(',')
                    for part in parts:
                        if 'insertion' in part:
                            additions = int(part.split()[0])
                        elif 'deletion' in part:
                            deletions = int(part.split()[0])
            
            # Get full diff
            diff = self.get_diff("HEAD", "main")
            
            # Get commit message
            result = self._run_git_command(["log", "-1", "--pretty=%B"])
            commit_message = result["stdout"].strip()
            
            patch = PatchInfo(
                patch_id=f"patch_{int(datetime.now().timestamp())}",
                branch_name=branch_name,
                files_changed=files_changed,
                additions=additions,
                deletions=deletions,
                diff=diff,
                commit_message=commit_message
            )
            
            return patch
            
        finally:
            if branch_name and branch_name != self.get_current_branch():
                self._run_git_command(["checkout", original_branch])
    
    def apply_patch(
        self,
        patch: str,
        target_branch: str = "main"
    ) -> bool:
        """
        Apply a patch to target branch
        
        Args:
            patch: Patch string (unified diff format)
            target_branch: Branch to apply patch to
            
        Returns:
            True if successful
        """
        # Checkout target branch
        original_branch = self.get_current_branch()
        self._run_git_command(["checkout", target_branch])
        
        try:
            # Apply patch
            process = subprocess.Popen(
                ["git", "apply"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.repo_path,
                text=True
            )
            
            stdout, stderr = process.communicate(input=patch)
            
            if process.returncode != 0:
                logger.error(f"Failed to apply patch: {stderr}")
                return False
            
            logger.info("Patch applied successfully")
            return True
            
        finally:
            self._run_git_command(["checkout", original_branch])
    
    def merge_branch(
        self,
        source_branch: str,
        target_branch: str = "main",
        strategy: str = "squash"
    ) -> bool:
        """
        Merge source branch into target
        
        Args:
            source_branch: Branch to merge from
            target_branch: Branch to merge into
            strategy: Merge strategy (merge, squash, rebase)
            
        Returns:
            True if successful
        """
        original_branch = self.get_current_branch()
        
        try:
            # Checkout target branch
            self._run_git_command(["checkout", target_branch])
            
            # Merge
            if strategy == "squash":
                result = self._run_git_command(
                    ["merge", "--squash", source_branch],
                    check=False
                )
                if result["returncode"] == 0:
                    self._run_git_command(["commit", "-m", f"Merge {source_branch}"])
            elif strategy == "rebase":
                self._run_git_command(["checkout", source_branch])
                self._run_git_command(["rebase", target_branch])
                self._run_git_command(["checkout", target_branch])
                self._run_git_command(["merge", source_branch])
            else:  # regular merge
                result = self._run_git_command(
                    ["merge", source_branch],
                    check=False
                )
            
            logger.info(f"Merged {source_branch} into {target_branch}")
            return True
            
        except Exception as e:
            logger.error(f"Merge failed: {e}")
            # Abort merge if in progress
            self._run_git_command(["merge", "--abort"], check=False)
            return False
            
        finally:
            self._run_git_command(["checkout", original_branch])
    
    def delete_branch(self, branch_name: str, force: bool = False):
        """
        Delete a branch
        
        Args:
            branch_name: Branch to delete
            force: Force deletion even if not merged
        """
        flag = "-D" if force else "-d"
        self._run_git_command(["branch", flag, branch_name])
        logger.info(f"Deleted branch: {branch_name}")
    
    def list_work_branches(self) -> List[str]:
        """
        List all AI work branches
        
        Returns:
            List of branch names
        """
        result = self._run_git_command(["branch", "--list", "ai/*"])
        branches = [line.strip().replace('* ', '') for line in result["stdout"].split('\n') if line.strip()]
        return branches
    
    def cleanup_old_branches(self, max_age_days: int = 7):
        """
        Cleanup old AI work branches
        
        Args:
            max_age_days: Max age in days before cleanup
        """
        import time
        
        branches = self.list_work_branches()
        current_time = time.time()
        
        for branch in branches:
            # Get branch age
            result = self._run_git_command([
                "log", "-1", "--format=%ct", branch
            ])
            
            if result["stdout"].strip():
                branch_time = int(result["stdout"].strip())
                age_days = (current_time - branch_time) / (24 * 3600)
                
                if age_days > max_age_days:
                    try:
                        self.delete_branch(branch, force=True)
                        logger.info(f"Cleaned up old branch: {branch} (age: {age_days:.1f} days)")
                    except Exception as e:
                        logger.warning(f"Failed to cleanup branch {branch}: {e}")


# ============================================================================
# WORKFLOW HELPERS
# ============================================================================

class PatchWorkflow:
    """
    High-level workflow for patch-based development
    """
    
    def __init__(self, repo_path: Path):
        """
        Initialize workflow
        
        Args:
            repo_path: Path to git repository
        """
        self.manager = GitPatchManager(repo_path)
    
    def start_generation(self, strategy_name: str) -> GitBranch:
        """Start new strategy generation workflow"""
        return self.manager.create_work_branch(strategy_name, "generation")
    
    def start_fix(self, strategy_name: str) -> GitBranch:
        """Start fix workflow"""
        return self.manager.create_work_branch(strategy_name, "fix")
    
    def commit_generation(
        self,
        strategy_name: str,
        file_path: str
    ) -> str:
        """
        Commit generated strategy code
        
        Args:
            strategy_name: Strategy name
            file_path: Path to generated file
            
        Returns:
            Commit hash
        """
        message = f"Generate strategy: {strategy_name}"
        return self.manager.commit_changes([file_path], message)
    
    def commit_fix(
        self,
        strategy_name: str,
        file_path: str,
        error_summary: str
    ) -> str:
        """
        Commit fix
        
        Args:
            strategy_name: Strategy name
            file_path: Path to fixed file
            error_summary: Summary of error that was fixed
            
        Returns:
            Commit hash
        """
        message = f"Fix strategy {strategy_name}: {error_summary}"
        return self.manager.commit_changes([file_path], message)
    
    def finalize_success(
        self,
        branch_name: str,
        target_branch: str = "main"
    ) -> bool:
        """
        Finalize successful generation/fix by merging to main
        
        Args:
            branch_name: Work branch to merge
            target_branch: Target branch (usually main)
            
        Returns:
            True if successful
        """
        success = self.manager.merge_branch(branch_name, target_branch, strategy="squash")
        
        if success:
            # Delete work branch
            self.manager.delete_branch(branch_name)
        
        return success
    
    def rollback_failure(self, branch_name: str):
        """
        Rollback failed attempt
        
        Args:
            branch_name: Branch to delete
        """
        # Just delete the branch - changes are isolated
        self.manager.delete_branch(branch_name, force=True)


# CLI for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Git patch manager CLI")
    parser.add_argument("--repo", type=str, default=".", help="Repository path")
    
    subparsers = parser.add_subparsers(dest="command")
    
    # Create branch
    create_parser = subparsers.add_parser("create", help="Create work branch")
    create_parser.add_argument("strategy", help="Strategy name")
    create_parser.add_argument("--purpose", default="generation", help="Branch purpose")
    
    # Commit
    commit_parser = subparsers.add_parser("commit", help="Commit changes")
    commit_parser.add_argument("files", nargs="+", help="Files to commit")
    commit_parser.add_argument("-m", "--message", required=True, help="Commit message")
    
    # Diff
    diff_parser = subparsers.add_parser("diff", help="Show diff")
    diff_parser.add_argument("--file", help="Specific file to diff")
    
    # List
    list_parser = subparsers.add_parser("list", help="List work branches")
    
    # Cleanup
    cleanup_parser = subparsers.add_parser("cleanup", help="Cleanup old branches")
    cleanup_parser.add_argument("--days", type=int, default=7, help="Max age in days")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        exit(0)
    
    manager = GitPatchManager(Path(args.repo))
    
    if args.command == "create":
        branch = manager.create_work_branch(args.strategy, args.purpose)
        print(f"✓ Created branch: {branch.name}")
    
    elif args.command == "commit":
        commit_hash = manager.commit_changes(args.files, args.message)
        print(f"✓ Committed: {commit_hash[:8]}")
    
    elif args.command == "diff":
        diff = manager.get_diff(file_path=args.file)
        if diff:
            print(diff)
        else:
            print("No changes")
    
    elif args.command == "list":
        branches = manager.list_work_branches()
        print(f"\nWork branches ({len(branches)}):")
        for branch in branches:
            print(f"  {branch}")
    
    elif args.command == "cleanup":
        manager.cleanup_old_branches(args.days)
        print(f"✓ Cleaned up branches older than {args.days} days")
