"""
Test suite for unique strategy naming convention

Validates:
- Filename generation produces unique identifiers
- Registry can parse and extract metadata
- Query methods work correctly
- Integration with coder agent
"""

import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

from agents.coder_agent.strategy_registry import (
    StrategyRegistry,
    StrategyMetadata
)


@pytest.fixture
def temp_codes_dir():
    """Create temporary codes directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    codes_dir = temp_dir / 'codes'
    codes_dir.mkdir(parents=True)
    
    yield codes_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_strategies(temp_codes_dir):
    """Create sample strategy files for testing."""
    strategies = [
        "20251121_143052_wf_abc123de_data_loading_rsi_strategy.py",
        "20251121_150830_wf_abc123de_entry_logic_ema_crossover.py",
        "20251121_163445_wf_def456hi_exit_logic_trailing_stop.py",
        "20251122_093015_wf_xyz789fg_data_loading_momentum_strategy.py",
    ]
    
    for filename in strategies:
        filepath = temp_codes_dir / filename
        filepath.write_text(f"# Strategy: {filename}\n")
    
    return strategies


def test_filename_parsing():
    """Test that filenames are correctly parsed."""
    registry = StrategyRegistry()
    
    filename = "20251121_143052_wf_abc123de_data_loading_rsi_strategy.py"
    metadata = registry.parse_filename(filename)
    
    assert metadata is not None
    assert metadata.filename == filename
    assert metadata.timestamp == datetime(2025, 11, 21, 14, 30, 52)
    assert metadata.workflow_id == "wf_abc123de"
    assert metadata.task_id == "data_loading"
    assert metadata.descriptive_name == "rsi_strategy"


def test_invalid_filename_parsing():
    """Test that invalid filenames return None."""
    registry = StrategyRegistry()
    
    invalid_filenames = [
        "ai_strategy_old_format.py",
        "random_file.py",
        "20251121_wf_abc_missing_parts.py"
    ]
    
    for filename in invalid_filenames:
        metadata = registry.parse_filename(filename)
        assert metadata is None


def test_scan_directory(temp_codes_dir, sample_strategies):
    """Test directory scanning finds all strategies."""
    registry = StrategyRegistry(temp_codes_dir)
    
    strategies = registry.scan_directory()
    
    assert len(strategies) == len(sample_strategies)
    assert all(isinstance(s, StrategyMetadata) for s in strategies)


def test_get_by_workflow(temp_codes_dir, sample_strategies):
    """Test filtering by workflow ID."""
    registry = StrategyRegistry(temp_codes_dir)
    
    strategies = registry.get_by_workflow('wf_abc123de')
    
    assert len(strategies) == 2
    assert all(s.workflow_id == 'wf_abc123de' for s in strategies)
    
    # Should be sorted by timestamp
    assert strategies[0].timestamp < strategies[1].timestamp


def test_get_by_task(temp_codes_dir, sample_strategies):
    """Test filtering by task ID."""
    registry = StrategyRegistry(temp_codes_dir)
    
    strategies = registry.get_by_task('data_loading')
    
    assert len(strategies) == 2
    assert all(s.task_id == 'data_loading' for s in strategies)


def test_get_latest_by_workflow(temp_codes_dir, sample_strategies):
    """Test getting latest strategy for workflow."""
    registry = StrategyRegistry(temp_codes_dir)
    
    latest = registry.get_latest_by_workflow('wf_abc123de')
    
    assert latest is not None
    assert latest.workflow_id == 'wf_abc123de'
    assert latest.filename == "20251121_150830_wf_abc123de_entry_logic_ema_crossover.py"


def test_get_latest_by_task(temp_codes_dir, sample_strategies):
    """Test getting latest strategy for task."""
    registry = StrategyRegistry(temp_codes_dir)
    
    latest = registry.get_latest_by_task('data_loading')
    
    assert latest is not None
    assert latest.task_id == 'data_loading'
    # Should be the one from 2025-11-22
    assert latest.filename == "20251122_093015_wf_xyz789fg_data_loading_momentum_strategy.py"


def test_get_by_date_range(temp_codes_dir, sample_strategies):
    """Test filtering by date range."""
    registry = StrategyRegistry(temp_codes_dir)
    
    # Get only strategies from 2025-11-21
    start = datetime(2025, 11, 21)
    end = datetime(2025, 11, 21, 23, 59, 59)
    
    strategies = registry.get_by_date_range(start, end)
    
    assert len(strategies) == 3
    assert all(s.timestamp.date() == start.date() for s in strategies)


def test_search_by_description(temp_codes_dir, sample_strategies):
    """Test searching by descriptive name."""
    registry = StrategyRegistry(temp_codes_dir)
    
    strategies = registry.search_by_description('rsi')
    
    assert len(strategies) == 1
    assert strategies[0].descriptive_name == 'rsi_strategy'
    
    strategies = registry.search_by_description('strategy')
    assert len(strategies) == 2  # rsi_strategy and momentum_strategy


def test_generate_inventory(temp_codes_dir, sample_strategies):
    """Test inventory generation."""
    registry = StrategyRegistry(temp_codes_dir)
    
    inventory = registry.generate_inventory()
    
    assert inventory['total_strategies'] == len(sample_strategies)
    assert 'strategies' in inventory
    assert 'by_workflow' in inventory
    assert 'by_task' in inventory
    assert 'by_date' in inventory
    
    # Check groupings
    assert len(inventory['by_workflow']) == 3  # 3 unique workflows
    assert len(inventory['by_task']) == 3  # 3 unique tasks
    assert len(inventory['by_date']) == 2  # 2 unique dates


def test_coder_agent_filename_generation():
    """Test Coder Agent's filename generation."""
    from agents.coder_agent.coder import CoderAgent
    from contracts.message_bus import MessageBus
    
    message_bus = MessageBus()
    coder = CoderAgent(
        agent_id='test_coder',
        message_bus=message_bus,
        workspace_root=Path.cwd()
    )
    
    task = {
        'id': 'task_data_loading',
        'title': 'Implement RSI Strategy with Data Loading'
    }
    
    contract = {
        'workflow_id': 'workflow_abc123def456',
        'contract_id': 'contract_001'
    }
    
    filename = coder._generate_unique_filename(task, contract)
    
    # Verify format
    assert filename.endswith('.py')
    assert '_wf_' in filename
    assert '_data_loading_' in filename or 'data_loading' in filename
    assert 'rsi' in filename.lower() or 'strategy' in filename.lower()
    
    # Verify parseable
    registry = StrategyRegistry()
    metadata = registry.parse_filename(filename)
    assert metadata is not None
    assert metadata.task_id == 'data_loading'


def test_unique_filenames_for_same_task():
    """Test that multiple generations produce unique filenames."""
    from agents.coder_agent.coder import CoderAgent
    from contracts.message_bus import MessageBus
    import time
    
    message_bus = MessageBus()
    coder = CoderAgent(
        agent_id='test_coder',
        message_bus=message_bus,
        workspace_root=Path.cwd()
    )
    
    task = {
        'id': 'task_data_loading',
        'title': 'RSI Strategy'
    }
    
    contract = {
        'workflow_id': 'workflow_test',
        'contract_id': 'contract_001'
    }
    
    # Generate two filenames
    filename1 = coder._generate_unique_filename(task, contract)
    time.sleep(0.01)  # Small delay to ensure different timestamp
    filename2 = coder._generate_unique_filename(task, contract)
    
    # Should be different due to timestamp
    assert filename1 != filename2


def test_test_file_naming():
    """Test that test files match strategy files."""
    strategy_file = "20251121_143052_wf_abc123de_data_loading_rsi_strategy.py"
    test_file = f"test_{strategy_file}"
    
    # Test file should be parseable by removing 'test_' prefix
    strategy_from_test = test_file.replace('test_', '')
    assert strategy_from_test == strategy_file


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
