# Strategy File Naming Convention & Registry

**Version:** 2.0  
**Date:** November 21, 2025  
**Status:** Production Implementation

---

## Overview

The multi-agent system now uses a comprehensive unique identifier naming convention for all generated strategy files. This provides full traceability, lineage tracking, and chronological organization.

---

## Filename Format

### Structure

```
{timestamp}_{workflow_id}_{task_id}_{descriptive_name}.py
```

### Components

| Component | Format | Description | Example |
|-----------|--------|-------------|---------|
| **Timestamp** | `YYYYMMDD_HHMMSS` | Creation time for sorting | `20251121_143052` |
| **Workflow ID** | `wf_{id}` | Shortened workflow identifier | `wf_abc123de` |
| **Task ID** | Task identifier | Task from todo list | `data_loading` |
| **Descriptive Name** | Snake_case | Human-readable description | `rsi_strategy` |

### Complete Examples

```
20251121_143052_wf_abc123de_data_loading_rsi_strategy.py
20251121_150830_wf_xyz789fg_entry_logic_ema_crossover.py
20251122_093015_wf_def456hi_exit_logic_trailing_stop.py
```

---

## Benefits

### ✅ Unique Identification
- Every file has globally unique identifier
- No collisions even with similar strategy names
- Easy to reference in logs and reports

### ✅ Traceability
- Instant identification of workflow origin
- Links back to specific task in todo list
- Clear lineage from planner → coder → tester

### ✅ Chronological Organization
- Files sort naturally by timestamp
- Easy to find latest versions
- Clear progression of development

### ✅ Human Readability
- Descriptive name shows strategy purpose
- No need to open file to understand content
- Self-documenting file structure

### ✅ Automation Friendly
- Parseable by regex
- Extractable metadata
- Queryable by any component

---

## Comparison: Old vs New

### Old Naming (v1.0)

```python
ai_strategy_data_loading.py
ai_strategy_entry.py
ai_strategy_exit.py
```

**Problems:**
- ❌ No uniqueness - overwrites on regeneration
- ❌ No workflow linkage
- ❌ No timestamp information
- ❌ Loses history of iterations

### New Naming (v2.0)

```python
20251121_143052_wf_abc123de_data_loading_rsi_strategy.py
20251121_150830_wf_abc123de_entry_logic_rsi_strategy.py
20251121_163445_wf_abc123de_exit_logic_rsi_strategy.py
```

**Advantages:**
- ✅ Unique per generation
- ✅ Workflow linkage preserved
- ✅ Sortable by time
- ✅ Full history maintained

---

## Strategy Registry

### Overview

The `strategy_registry.py` module provides utilities for managing and querying uniquely named strategy files.

### Core Features

```python
from agents.coder_agent.strategy_registry import StrategyRegistry

registry = StrategyRegistry()

# Parse filename and extract metadata
metadata = registry.parse_filename(
    "20251121_143052_wf_abc123de_data_loading_rsi_strategy.py"
)
print(metadata.timestamp)      # 2025-11-21 14:30:52
print(metadata.workflow_id)    # wf_abc123de
print(metadata.task_id)        # data_loading
print(metadata.descriptive_name)  # rsi_strategy
```

### Query Methods

#### By Workflow

```python
# Get all strategies for a workflow
strategies = registry.get_by_workflow('wf_abc123de')

for s in strategies:
    print(f"{s.timestamp} - {s.filename}")

# Get latest strategy for workflow
latest = registry.get_latest_by_workflow('wf_abc123de')
```

#### By Task

```python
# Get all strategies for a task
strategies = registry.get_by_task('data_loading')

# Get latest strategy for task
latest = registry.get_latest_by_task('data_loading')
```

#### By Date Range

```python
from datetime import datetime

# Get strategies from last week
start = datetime(2025, 11, 15)
end = datetime.now()
strategies = registry.get_by_date_range(start, end)
```

#### By Description

```python
# Search by strategy description
strategies = registry.search_by_description('rsi')
# Returns all strategies with 'rsi' in descriptive name
```

### Generate Inventory

```python
# Generate comprehensive inventory
inventory = registry.generate_inventory(
    output_file=Path('artifacts/strategy_inventory.json')
)

print(f"Total strategies: {inventory['total_strategies']}")
print(f"Workflows: {len(inventory['by_workflow'])}")
```

**Inventory structure:**

```json
{
  "generated_at": "2025-11-21T14:30:52",
  "total_strategies": 42,
  "strategies": [
    {
      "filename": "20251121_143052_wf_abc123de_data_loading_rsi_strategy.py",
      "timestamp": "2025-11-21T14:30:52",
      "workflow_id": "wf_abc123de",
      "task_id": "data_loading",
      "descriptive_name": "rsi_strategy",
      "file_size": 5420
    }
  ],
  "by_workflow": {
    "wf_abc123de": [
      "20251121_143052_wf_abc123de_data_loading_rsi_strategy.py",
      "20251121_150830_wf_abc123de_entry_logic_rsi_strategy.py"
    ]
  },
  "by_task": {
    "data_loading": [...],
    "entry_logic": [...]
  },
  "by_date": {
    "2025-11-21": [...],
    "2025-11-22": [...]
  }
}
```

---

## CLI Usage

### Print Summary

```bash
python -m agents.coder_agent.strategy_registry
```

Output:
```
======================================================================
Strategy Registry Summary
======================================================================
Directory: c:\Users\nyaga\Documents\AlgoAgent\multi_agent\Backtest\codes
Total Strategies: 42

Workflows: 5
  wf_abc123de: 8 strategies
  wf_xyz789fg: 12 strategies
  wf_def456hi: 6 strategies

Recent Strategies (last 5):
  2025-11-21 16:34:45 - 20251121_163445_wf_def456hi_exit_logic_trailing_stop.py
  2025-11-21 15:08:30 - 20251121_150830_wf_abc123de_entry_logic_ema_crossover.py
  2025-11-21 14:30:52 - 20251121_143052_wf_abc123de_data_loading_rsi_strategy.py
======================================================================
```

### Query by Workflow

```bash
python -m agents.coder_agent.strategy_registry --workflow wf_abc123de
```

### Query by Task

```bash
python -m agents.coder_agent.strategy_registry --task data_loading
```

### Search by Description

```bash
python -m agents.coder_agent.strategy_registry --search rsi
```

### Generate Inventory

```bash
python -m agents.coder_agent.strategy_registry --inventory --output artifacts/inventory.json
```

---

## Integration with Coder Agent

### Automatic Filename Generation

The Coder Agent automatically generates unique filenames when creating strategies:

```python
# In coder.py
def _generate_unique_filename(self, task: Dict, contract: Dict) -> str:
    """Generate unique filename with comprehensive identifiers."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    workflow_id = contract.get('workflow_id', 'nowf')
    task_id = task.get('id', 'unknown')
    task_title = task.get('title', 'strategy')
    
    # Clean and format
    desc_name = clean_description(task_title)
    
    return f"{timestamp}_{workflow_id}_{task_id}_{desc_name}.py"
```

### Test File Naming

Test files automatically match strategy filenames:

```python
# Strategy file
20251121_143052_wf_abc123de_data_loading_rsi_strategy.py

# Corresponding test file
test_20251121_143052_wf_abc123de_data_loading_rsi_strategy.py
```

---

## Orchestrator Integration

### Workflow Tracking

The orchestrator uses filenames to track workflow progress:

```python
from agents.coder_agent.strategy_registry import StrategyRegistry

registry = StrategyRegistry()

# Get all strategies for current workflow
workflow_strategies = registry.get_by_workflow(workflow_id)

# Find strategies created after workflow start
new_strategies = [
    s for s in workflow_strategies 
    if s.timestamp >= workflow_start_time
]

# Test only new strategies
for strategy in new_strategies:
    test_strategy(strategy.filepath)
```

### Artifact Management

```python
# Create artifact commit with unique identifiers
def commit_artifacts(workflow_id: str, task_id: str):
    strategies = registry.get_by_task(task_id)
    latest = strategies[-1]  # Most recent
    
    # Git branch name includes unique identifiers
    branch_name = f"ai/generated/{workflow_id}/{task_id}/{latest.timestamp.strftime('%Y%m%d_%H%M%S')}"
    
    # Commit with metadata
    git.commit(
        files=[str(latest.filepath)],
        message=f"Generated strategy: {latest.descriptive_name}",
        metadata={
            'workflow_id': workflow_id,
            'task_id': task_id,
            'timestamp': latest.timestamp.isoformat(),
            'filename': latest.filename
        }
    )
```

---

## Tester Agent Integration

### Test Result Correlation

```python
# In tester_agent/tester.py
def run_tests(strategy_file: str):
    metadata = registry.parse_filename(strategy_file)
    
    # Run tests
    result = pytest.main([f"tests/test_{metadata.filename}"])
    
    # Publish result with full context
    publish_event({
        'event_type': 'test.completed',
        'strategy_file': strategy_file,
        'workflow_id': metadata.workflow_id,
        'task_id': metadata.task_id,
        'timestamp': metadata.timestamp.isoformat(),
        'result': 'passed' if result == 0 else 'failed'
    })
```

---

## Migration Guide

### From v1.0 to v2.0

#### Step 1: Archive Old Files

```bash
# Move old files to archive
mkdir -p Backtest/codes/archive
mv Backtest/codes/ai_strategy_*.py Backtest/codes/archive/
```

#### Step 2: Update Coder Agent

The updated coder agent automatically uses the new naming convention. No changes needed.

#### Step 3: Regenerate Strategies

```bash
# Run orchestrator with existing workflows
python -m orchestrator_service.orchestrator workflows/existing_workflow.json

# New strategies will use unique naming
```

#### Step 4: Update References

If you have hardcoded strategy references, update them:

```python
# Old
strategy_file = "ai_strategy_data_loading.py"

# New - query by task
registry = StrategyRegistry()
latest = registry.get_latest_by_task('data_loading')
strategy_file = latest.filename
```

---

## Best Practices

### ✅ DO

- **Use registry queries** instead of hardcoded filenames
- **Preserve all generated files** for history
- **Include workflow context** in all operations
- **Use timestamps** for chronological sorting
- **Generate inventories** regularly for auditing

### ❌ DON'T

- **Don't manually rename** generated files
- **Don't delete** old versions without archiving
- **Don't hardcode** filenames in code
- **Don't modify** timestamp components
- **Don't rely on** file modification times (use embedded timestamp)

---

## Troubleshooting

### Issue: Filename Too Long

**Problem:** Descriptive name makes filename exceed OS limits

**Solution:** The generator automatically truncates to 6 words max

```python
# Automatic truncation
"Create RSI Strategy with EMA Filter and Trailing Stop Loss"
→ "create_rsi_strategy_with_ema_filter"
```

### Issue: Can't Find Strategy

**Problem:** Looking for old naming convention

**Solution:** Use registry search

```python
# Find by description
strategies = registry.search_by_description('rsi')

# Or by workflow
strategies = registry.get_by_workflow('wf_abc123de')
```

### Issue: Multiple Versions Exist

**Problem:** Multiple strategies for same task

**Solution:** Use `get_latest_by_task()`

```python
# Always get latest version
latest = registry.get_latest_by_task('data_loading')
```

---

## API Reference

### StrategyMetadata

```python
@dataclass
class StrategyMetadata:
    filename: str
    filepath: Path
    timestamp: datetime
    workflow_id: str
    task_id: str
    descriptive_name: str
    file_size: int
    created_at: datetime
```

### StrategyRegistry Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `parse_filename(filename)` | Parse filename to metadata | `StrategyMetadata` |
| `scan_directory()` | Scan all strategies | `List[StrategyMetadata]` |
| `get_by_workflow(workflow_id)` | Get strategies for workflow | `List[StrategyMetadata]` |
| `get_by_task(task_id)` | Get strategies for task | `List[StrategyMetadata]` |
| `get_by_date_range(start, end)` | Get strategies in date range | `List[StrategyMetadata]` |
| `get_latest_by_workflow(workflow_id)` | Get latest for workflow | `Optional[StrategyMetadata]` |
| `get_latest_by_task(task_id)` | Get latest for task | `Optional[StrategyMetadata]` |
| `search_by_description(term)` | Search by description | `List[StrategyMetadata]` |
| `generate_inventory(output_file)` | Generate full inventory | `Dict` |
| `print_summary()` | Print readable summary | `None` |

---

## Examples

### Example 1: Find Latest Strategy for Workflow

```python
from agents.coder_agent.strategy_registry import StrategyRegistry

registry = StrategyRegistry()
latest = registry.get_latest_by_workflow('wf_abc123de')

print(f"Latest strategy: {latest.filename}")
print(f"Created: {latest.timestamp}")
print(f"Task: {latest.task_id}")
```

### Example 2: Generate Workflow Report

```python
workflow_id = 'wf_abc123de'
strategies = registry.get_by_workflow(workflow_id)

print(f"\nWorkflow Report: {workflow_id}")
print(f"Total Strategies: {len(strategies)}")
print(f"\nTimeline:")

for s in strategies:
    print(f"  {s.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {s.task_id} - {s.descriptive_name}")
```

### Example 3: Cleanup Old Strategies

```python
from datetime import datetime, timedelta

# Archive strategies older than 30 days
cutoff = datetime.now() - timedelta(days=30)
old_strategies = registry.get_by_date_range(end_date=cutoff)

archive_dir = Path('Backtest/codes/archive')
archive_dir.mkdir(exist_ok=True)

for s in old_strategies:
    s.filepath.rename(archive_dir / s.filename)
    print(f"Archived: {s.filename}")
```

---

## Related Documentation

- **ARCHITECTURE.md** - Overall system architecture
- **CODER_AGENT_SPEC.md** - Coder agent specification
- **ORCHESTRATOR_GUIDE.md** - Orchestrator workflow management
- **ARTIFACT_STORE.md** - Artifact storage and versioning

---

## Support

For issues or questions:
1. Check this documentation first
2. Review `strategy_registry.py` source code
3. Run registry with `--help` for CLI options
4. Refer to `ARCHITECTURE.md` for system design

---

**Status:** ✅ Production Implementation Complete  
**Version:** 2.0  
**Last Updated:** November 21, 2025
