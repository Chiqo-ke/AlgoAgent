# Strategy Naming System - Quick Reference

## Filename Format

```
{timestamp}_{workflow_id}_{task_id}_{descriptive_name}.py
20251121_143052_wf_abc123de_data_loading_rsi_strategy.py
```

## Common Operations

### Import Registry
```python
from agents.coder_agent.strategy_registry import StrategyRegistry
registry = StrategyRegistry()
```

### Parse Filename
```python
metadata = registry.parse_filename("20251121_143052_wf_abc123de_data_loading_rsi_strategy.py")
print(metadata.workflow_id)  # wf_abc123de
print(metadata.task_id)      # data_loading
print(metadata.timestamp)    # 2025-11-21 14:30:52
```

### Find by Workflow
```python
strategies = registry.get_by_workflow('wf_abc123de')
latest = registry.get_latest_by_workflow('wf_abc123de')
```

### Find by Task
```python
strategies = registry.get_by_task('data_loading')
latest = registry.get_latest_by_task('data_loading')
```

### Search
```python
strategies = registry.search_by_description('rsi')
```

### Date Range
```python
from datetime import datetime
strategies = registry.get_by_date_range(
    start_date=datetime(2025, 11, 21),
    end_date=datetime.now()
)
```

### Generate Inventory
```python
inventory = registry.generate_inventory(
    output_file=Path('inventory.json')
)
```

## CLI Commands

```bash
# Summary
python -m agents.coder_agent.strategy_registry

# Query by workflow
python -m agents.coder_agent.strategy_registry --workflow wf_abc123de

# Query by task
python -m agents.coder_agent.strategy_registry --task data_loading

# Search
python -m agents.coder_agent.strategy_registry --search rsi

# Generate inventory
python -m agents.coder_agent.strategy_registry --inventory --output inventory.json
```

## Common Patterns

### Test Only New Strategies
```python
workflow_strategies = registry.get_by_workflow(workflow_id)
new_strategies = [s for s in workflow_strategies if s.timestamp >= workflow_start_time]
for strategy in new_strategies:
    run_tests(strategy.filepath)
```

### Track Evolution
```python
history = registry.get_by_task('data_loading')
for s in sorted(history, key=lambda x: x.timestamp):
    print(f"{s.timestamp} - {s.filename}")
```

### Cleanup Old Files
```python
from datetime import timedelta
cutoff = datetime.now() - timedelta(days=30)
old_strategies = registry.get_by_date_range(end_date=cutoff)
for s in old_strategies:
    archive(s.filepath)
```

## Components

| Component | Description |
|-----------|-------------|
| **Timestamp** | `YYYYMMDD_HHMMSS` - Creation time |
| **Workflow ID** | `wf_{id}` - Shortened workflow identifier |
| **Task ID** | Task identifier from todo list |
| **Description** | Human-readable strategy description |

## Benefits

✅ Globally unique identifiers  
✅ Full workflow traceability  
✅ Chronologically sortable  
✅ Human-readable  
✅ Machine-parseable  
✅ History preserved  

## Documentation

- **STRATEGY_NAMING_CONVENTION.md** - Complete guide
- **STRATEGY_NAMING_IMPLEMENTATION.md** - Implementation details
- **strategy_registry.py** - Source code
- **test_strategy_naming.py** - Test suite
- **demo_strategy_naming.py** - Interactive demo
