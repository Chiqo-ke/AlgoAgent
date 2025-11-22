# Artifact Store - Git-Based Versioning System

**Status:** Production Ready  
**Version:** 1.0  
**Date:** November 7, 2025

---

## Overview

The Artifact Store provides git-based versioning and storage for AI-generated strategy code and test artifacts. It integrates with the Tester Agent to automatically commit tested code to version-controlled branches with proper tagging and metadata.

### Key Features

✅ **Git-Based Versioning** - Each workflow/task gets its own branch  
✅ **Automatic Tagging** - Correlation IDs and prompt hashes as git tags  
✅ **Metadata Tracking** - Test metrics, agent versions, timestamps  
✅ **Security Scanning** - Prevents committing hardcoded secrets  
✅ **Rollback Support** - Revert to any previous version by tag  
✅ **Remote Push** - Optional automatic push to remote repository  
✅ **Audit Trail** - Complete git history of all generated artifacts  

---

## Architecture

### Branch Naming Convention

```
ai/generated/<workflow_id>/<task_id>
```

**Examples:**
- `ai/generated/wf_rsi_strategy/task_coder_001`
- `ai/generated/wf_macd_backtest/task_coder_002`

### Tag Convention

```
corr_<correlation_id>      # Workflow correlation
prompt_<hash>              # Original prompt hash
```

**Examples:**
- `corr_abc123def456`
- `prompt_7a8b9c0d1e2f`

### Directory Structure

```
Backtest/
└─ codes/
   └─ <task_id>/
      ├─ strategy.py          # Generated strategy code
      ├─ test_report.json     # Test results
      ├─ trades.csv           # Backtest trades
      ├─ equity_curve.csv     # Performance curve
      ├─ events.log           # Execution log
      └─ metadata.json        # Artifact metadata
```

---

## Usage

### Basic Usage

```python
from artifacts import ArtifactStore, ArtifactStoreConfig

# Initialize with default config
store = ArtifactStore()

# Or with custom config
config = ArtifactStoreConfig(
    repo_path=Path("/path/to/repo"),
    auto_push=True,
    scan_for_secrets=True
)
store = ArtifactStore(config)

# Commit artifacts
result = store.commit_artifacts(
    workflow_id="wf_rsi_strategy",
    task_id="task_coder_001",
    files=[
        Path("Backtest/codes/rsi_strategy.py"),
        Path("artifacts/test_report.json"),
        Path("artifacts/trades.csv"),
        Path("artifacts/equity_curve.csv"),
        Path("artifacts/events.log")
    ],
    metadata={
        "agent_version": "coder-v1.0",
        "llm_version": "gpt-4",
        "test_metrics": {
            "total_trades": 12,
            "net_pnl": 120.5,
            "win_rate": 0.58,
            "max_drawdown": 45.2
        }
    },
    correlation_id="corr_abc123",
    prompt_hash="7a8b9c0d1e2f3a4b"
)

if result['success']:
    print(f"Committed to branch: {result['branch']}")
    print(f"Commit SHA: {result['commit_sha']}")
    print(f"Tags: {result['tags']}")
else:
    print(f"Failed: {result['error']}")
```

### Rollback to Previous Version

```python
# Revert to specific correlation ID
result = store.revert_to_tag(
    tag="corr_abc123",
    target_branch="main"
)

if result['success']:
    print(f"Reverted to {result['reverted_to']}: {result['commit_sha']}")
```

### List Artifacts

```python
# List all artifacts
artifacts = store.list_artifacts(limit=50)

# Filter by workflow
artifacts = store.list_artifacts(
    workflow_id="wf_rsi_strategy",
    limit=10
)

for artifact in artifacts:
    print(f"{artifact['workflow_id']}/{artifact['task_id']}")
    print(f"  Correlation: {artifact['correlation_id']}")
    print(f"  Test Metrics: {artifact['test_metrics']}")
```

### Retrieve by Correlation ID

```python
artifact = store.get_artifact_by_correlation_id("corr_abc123")

if artifact:
    print(f"Found artifact: {artifact['task_id']}")
    print(f"Files: {artifact['files']}")
    print(f"Metrics: {artifact['test_metrics']}")
```

---

## Orchestrator Integration

### Event Handler Example

```python
from contracts.event_types import EventType
from contracts.message_bus import RedisMessageBus
from artifacts import ArtifactStore

class OrchestratorService:
    def __init__(self):
        self.bus = RedisMessageBus()
        self.artifact_store = ArtifactStore()
        self.bus.subscribe(Channels.TEST_RESULTS, self.handle_test_result)
    
    def handle_test_result(self, event):
        """Handle TEST_PASSED event from Tester Agent."""
        if event.event_type != EventType.TEST_PASSED:
            return
        
        # Extract event data
        correlation_id = event.correlation_id
        workflow_id = event.workflow_id
        task_id = event.task_id
        artifacts = event.data['artifacts']
        metrics = event.data['metrics']
        
        # Collect files to commit
        files = [
            Path(artifacts['test_report']),
            Path(artifacts['trades']),
            Path(artifacts['equity_curve']),
            Path(artifacts['events_log'])
        ]
        
        # Add strategy file
        strategy_file = Path(f"Backtest/codes/{task_id}.py")
        if strategy_file.exists():
            files.append(strategy_file)
        
        # Commit to artifact store
        result = self.artifact_store.commit_artifacts(
            workflow_id=workflow_id,
            task_id=task_id,
            files=files,
            metadata={
                "agent_version": "tester-v1.0",
                "llm_version": "gpt-4",
                "test_metrics": metrics
            },
            correlation_id=correlation_id
        )
        
        if result['success']:
            # Publish ARTIFACT_COMMITTED event
            self.bus.publish(
                Channels.WORKFLOW_EVENTS,
                Event.create(
                    event_type=EventType.ARTIFACT_COMMITTED,
                    correlation_id=correlation_id,
                    workflow_id=workflow_id,
                    data={
                        "branch": result['branch'],
                        "commit_sha": result['commit_sha'],
                        "tags": result['tags'],
                        "pushed": result['pushed']
                    },
                    source="orchestrator"
                )
            )
            logger.info(f"Artifacts committed: {result['branch']}")
        else:
            logger.error(f"Failed to commit artifacts: {result['error']}")
            # Handle failure (retry, alert, etc.)
```

---

## Configuration

### ArtifactStoreConfig Options

```python
@dataclass
class ArtifactStoreConfig:
    # Git repository settings
    repo_path: Path = Path.cwd()
    remote_name: str = "origin"
    
    # Branch naming
    branch_prefix: str = "ai/generated"
    
    # Commit settings
    commit_author_name: str = "algo-agent-bot"
    commit_author_email: str = "algo-agent@example.com"
    
    # Security
    scan_for_secrets: bool = True
    secret_patterns: list = [...]  # Regex patterns
    
    # Metadata
    include_metadata: bool = True
    metadata_filename: str = "metadata.json"
    
    # Push settings
    auto_push: bool = True
    push_timeout: int = 30  # seconds
    
    # Rollback
    max_rollback_depth: int = 10
    
    # Validation
    require_test_passed: bool = True
    require_correlation_id: bool = True
```

### Environment Variables (Optional)

```bash
# Override git author for commits
export GIT_AUTHOR_NAME="algo-agent-bot"
export GIT_AUTHOR_EMAIL="algo-agent@example.com"

# Git remote settings
export GIT_REMOTE_NAME="origin"
export GIT_PUSH_TIMEOUT="30"
```

---

## Security

### Secret Scanning

The Artifact Store automatically scans files for hardcoded secrets before committing. If secrets are detected, the commit is aborted and a `SecretDetectedError` is raised.

**Scanned Patterns:**
- API keys (`api_key`, `apikey`)
- Secret keys (`secret_key`, `secretkey`)
- Passwords (`password`, `passwd`, `pwd`)
- Tokens (`token`)
- Stripe keys (`sk_test_*`, `sk_live_*`)
- AWS credentials (`aws_access_key_id`, `aws_secret_access_key`)

**Example:**

```python
try:
    result = store.commit_artifacts(...)
except SecretDetectedError as e:
    logger.error(f"Secrets detected: {e}")
    # Remove secrets and retry
```

### Access Control

**Recommendations:**
1. Use a **deploy key** or **service account** with restricted permissions
2. Limit push access to `ai/generated/*` branches only
3. Require **protected branches** for main/production
4. Enable **signed commits** for audit trail
5. Set up **branch protection rules** to prevent force pushes

### Git Configuration

```bash
# Set up deploy key (read/write for ai/generated/* branches)
ssh-keygen -t ed25519 -C "algo-agent-bot@example.com" -f ~/.ssh/algo_agent_deploy_key

# Add to GitHub/GitLab as deploy key with write access

# Configure git to use deploy key
git config core.sshCommand "ssh -i ~/.ssh/algo_agent_deploy_key"
```

---

## Metadata Schema

### metadata.json Format

```json
{
  "workflow_id": "wf_rsi_strategy",
  "task_id": "task_coder_001",
  "correlation_id": "corr_abc123",
  "prompt_hash": "7a8b9c0d1e2f3a4b",
  "commit_timestamp": "2025-11-07T14:30:00Z",
  "agent_version": "coder-v1.0",
  "llm_version": "gpt-4",
  "test_metrics": {
    "total_trades": 12,
    "net_pnl": 120.5,
    "win_rate": 0.58,
    "max_drawdown": 45.2,
    "duration_seconds": 34.2
  },
  "files": [
    "Backtest/codes/task_coder_001/rsi_strategy.py",
    "Backtest/codes/task_coder_001/test_report.json",
    "Backtest/codes/task_coder_001/trades.csv",
    "Backtest/codes/task_coder_001/equity_curve.csv",
    "Backtest/codes/task_coder_001/events.log",
    "Backtest/codes/task_coder_001/metadata.json"
  ]
}
```

---

## Error Handling

### Common Errors

**SecretDetectedError**
```python
try:
    result = store.commit_artifacts(...)
except SecretDetectedError as e:
    # Secret found in files - must be removed before commit
    logger.error(f"Secrets detected: {e}")
    # Handle: scan files, remove secrets, retry
```

**ArtifactStoreError**
```python
try:
    result = store.commit_artifacts(...)
except ArtifactStoreError as e:
    # Git operation failed (network, permissions, etc.)
    logger.error(f"Git operation failed: {e}")
    # Handle: check git status, permissions, network
```

**Validation Errors**
```python
# Missing correlation_id
config = ArtifactStoreConfig(require_correlation_id=True)
store = ArtifactStore(config)

result = store.commit_artifacts(
    workflow_id="wf_test",
    task_id="task_001",
    files=[...],
    metadata={},
    correlation_id=None  # Will raise ArtifactStoreError
)
```

---

## Rollback Procedures

### Scenario 1: Revert to Previous Version

```python
# Find correlation ID from logs or database
correlation_id = "corr_abc123"

# Revert main branch to that version
result = store.revert_to_tag(
    tag=f"corr_{correlation_id}",
    target_branch="main"
)

if result['success']:
    print(f"Reverted to {correlation_id}")
    # Deploy reverted version
```

### Scenario 2: Compare Versions

```bash
# List all tagged versions
git tag -l "corr_*"

# Compare two versions
git diff corr_abc123 corr_def456

# Show specific version
git show corr_abc123:Backtest/codes/task_001/rsi_strategy.py
```

### Scenario 3: Emergency Rollback

```bash
# Manual git rollback (if Artifact Store unavailable)
git checkout main
git revert <commit_sha>
git push origin main

# Or reset to previous commit (use with caution)
git reset --hard corr_abc123
git push --force origin main  # Requires admin permissions
```

---

## Best Practices

### 1. Always Use Correlation IDs
```python
# DO: Always provide correlation_id
result = store.commit_artifacts(
    ...,
    correlation_id=event.correlation_id
)

# DON'T: Skip correlation_id (unless disabled in config)
```

### 2. Include Complete Metadata
```python
# DO: Provide comprehensive metadata
metadata = {
    "agent_version": "coder-v1.0",
    "llm_version": "gpt-4",
    "test_metrics": {...},
    "prompt": "Generate RSI strategy",
    "parameters": {...}
}

# DON'T: Minimal metadata
metadata = {}
```

### 3. Handle Push Failures Gracefully
```python
result = store.commit_artifacts(...)

if result['success'] and not result['pushed']:
    # Commit succeeded locally but push failed
    logger.warning("Artifacts committed locally but not pushed")
    # Schedule retry or manual push
```

### 4. Verify Artifacts Before Commit
```python
# DO: Verify files exist and are valid
for file in files:
    if not file.exists():
        raise FileNotFoundError(f"Missing: {file}")
    if file.stat().st_size == 0:
        raise ValueError(f"Empty file: {file}")

result = store.commit_artifacts(...)
```

### 5. Use Branch Cleanup
```bash
# Periodically clean up old branches (manual or automated)
git branch -D $(git branch --list 'ai/generated/*' --merged main)

# Or archive branches older than N days
git for-each-ref --format='%(refname:short)' refs/heads/ai/generated/ | \
  xargs -I {} git branch -D {}
```

---

## Testing

### Unit Tests

```python
import unittest
from pathlib import Path
from artifacts import ArtifactStore, ArtifactStoreConfig

class TestArtifactStore(unittest.TestCase):
    def setUp(self):
        self.config = ArtifactStoreConfig(
            repo_path=Path("/tmp/test_repo"),
            auto_push=False
        )
        self.store = ArtifactStore(self.config)
    
    def test_commit_artifacts(self):
        result = self.store.commit_artifacts(
            workflow_id="wf_test",
            task_id="task_001",
            files=[Path("test_strategy.py")],
            metadata={"test": "data"},
            correlation_id="corr_test123"
        )
        
        self.assertTrue(result['success'])
        self.assertIn("ai/generated/wf_test/task_001", result['branch'])
        self.assertIn("corr_test123", result['tags'])
    
    def test_secret_detection(self):
        # Create file with secret
        test_file = Path("/tmp/test_secret.py")
        test_file.write_text("API_KEY = 'sk_live_1234567890abcdef'")
        
        with self.assertRaises(SecretDetectedError):
            self.store.commit_artifacts(
                workflow_id="wf_test",
                task_id="task_002",
                files=[test_file],
                metadata={},
                correlation_id="corr_test456"
            )
```

### Integration Test

```bash
# Test end-to-end workflow
python -m pytest tests/test_artifact_store_integration.py -v
```

---

## Troubleshooting

### Issue: Push fails with "Permission denied"

**Solution:**
1. Check deploy key permissions
2. Verify git remote URL: `git remote -v`
3. Test SSH connection: `ssh -T git@github.com`
4. Check branch protection rules

### Issue: "Not a git repository" error

**Solution:**
```python
# Ensure repo_path points to git repository root
config = ArtifactStoreConfig(
    repo_path=Path("/path/to/repo")  # Must contain .git directory
)
```

### Issue: Secrets detected but none exist

**Solution:**
```python
# Disable secret scanning temporarily (not recommended for production)
config = ArtifactStoreConfig(scan_for_secrets=False)

# Or adjust secret patterns to reduce false positives
config = ArtifactStoreConfig(
    secret_patterns=[
        r"sk_live_[0-9a-zA-Z]{24,}",  # Only real API keys
    ]
)
```

### Issue: Branch already exists

**Behavior:** Artifact Store will checkout existing branch and add new commit

**To force new branch:**
```bash
# Manually delete branch first
git branch -D ai/generated/wf_test/task_001
git push origin --delete ai/generated/wf_test/task_001
```

---

## API Reference

### ArtifactStore Class

**Methods:**

- `commit_artifacts(workflow_id, task_id, files, metadata, correlation_id, prompt_hash) -> Dict`
  - Commit artifacts to git with branching and tagging
  - Returns: `{'success', 'branch', 'commit_sha', 'tags', 'pushed'}`

- `revert_to_tag(tag, target_branch='main') -> Dict`
  - Revert branch to tagged commit
  - Returns: `{'success', 'commit_sha', 'reverted_to', 'branch'}`

- `list_artifacts(workflow_id=None, limit=50) -> List[Dict]`
  - List committed artifacts with metadata
  - Returns: List of metadata dicts

- `get_artifact_by_correlation_id(correlation_id) -> Optional[Dict]`
  - Retrieve artifact by correlation ID
  - Returns: Metadata dict or None

### ArtifactStoreConfig Class

**Attributes:** See Configuration section above

---

## Migration Guide

### From Manual Commits to Artifact Store

**Before (manual git):**
```bash
git checkout -b ai/generated/wf_test/task_001
cp artifacts/* Backtest/codes/task_001/
git add Backtest/codes/task_001/
git commit -m "Add artifacts"
git tag corr_abc123
git push origin ai/generated/wf_test/task_001
```

**After (Artifact Store):**
```python
result = store.commit_artifacts(
    workflow_id="wf_test",
    task_id="task_001",
    files=list(Path("artifacts").glob("*")),
    metadata={...},
    correlation_id="corr_abc123"
)
```

---

## Roadmap

### Future Enhancements

- [ ] **Artifact compression** - Compress large CSV files before commit
- [ ] **Delta commits** - Only commit changed files
- [ ] **Multi-repo support** - Commit to separate artifact repo
- [ ] **Signed commits** - GPG signature for audit trail
- [ ] **Approval workflow** - Require approval before push
- [ ] **Webhook integration** - Trigger CI/CD on artifact commit
- [ ] **Artifact expiration** - Auto-archive old branches
- [ ] **Conflict resolution** - Handle concurrent commits

---

## Support & Contributing

### Reporting Issues

1. Check existing issues in repository
2. Provide git log output: `git log --oneline --graph --all`
3. Include Artifact Store logs
4. Describe expected vs actual behavior

### Contributing

1. Fork repository
2. Create feature branch: `git checkout -b feature/artifact-enhancement`
3. Add tests for new functionality
4. Submit pull request with description

---

**Last Updated:** November 7, 2025  
**Version:** 1.0  
**Status:** Production Ready ✅
