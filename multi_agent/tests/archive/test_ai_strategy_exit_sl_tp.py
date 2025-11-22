"""
Test file for ai_strategy_exit_sl_tp.py

Tests:
1. test_backtest_runs - Verifies strategy executes without errors
2. test_report_structure - Validates SimBroker report format
3. test_trades_generated - Checks if strategy produces trades
4. test_metrics_present - Ensures key metrics are calculated
"""

import pytest
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from Backtest.codes.ai_strategy_exit_sl_tp import Strategy, run_backtest, main
from adapters.simbroker_adapter import SimBrokerAdapter
from simulator.simbroker import SimBroker, SimConfig


@pytest.fixture
def sample_data():
    """Load sample OHLCV data for testing."""
    # Try to load from fixtures
    fixture_path = Path('fixtures/sample_data.csv')
    if fixture_path.exists():
        return pd.read_csv(fixture_path)
    
    # Generate synthetic data if fixture doesn't exist
    dates = pd.date_range('2024-01-01', periods=100, freq='1H')
    df = pd.DataFrame({
        'timestamp': dates,
        'Open': 1.10 + pd.Series(range(100)) * 0.0001,
        'High': 1.102 + pd.Series(range(100)) * 0.0001,
        'Low': 1.098 + pd.Series(range(100)) * 0.0001,
        'Close': 1.101 + pd.Series(range(100)) * 0.0001,
        'Volume': 1000
    })
    return df


@pytest.fixture
def simbroker_adapter():
    """Create SimBroker adapter for testing."""
    config = SimConfig(
        starting_balance=10000.0,
        leverage=100.0,
        commission={'type': 'per_lot', 'value': 7.0},
        slippage={'type': 'fixed', 'value': 2}
    )
    broker = SimBroker(config)
    return SimBrokerAdapter(broker)


def test_backtest_runs(sample_data, simbroker_adapter):
    """Test that backtest executes without errors."""
    cfg = {'symbol': 'EURUSD', 'volume': 1.0}
    
    # Should not raise exception
    report = run_backtest(simbroker_adapter, sample_data, cfg)
    
    assert report is not None
    assert isinstance(report, dict)


def test_report_structure(sample_data, simbroker_adapter):
    """Test that SimBroker report has expected structure."""
    cfg = {'symbol': 'EURUSD', 'volume': 1.0}
    report = run_backtest(simbroker_adapter, sample_data, cfg)
    
    # Check summary section exists
    assert 'summary' in report
    summary = report['summary']
    
    # Validate key fields
    assert 'starting_balance' in summary
    assert 'final_balance' in summary
    assert 'total_trades' in summary
    assert isinstance(summary['total_trades'], (int, float))


def test_trades_generated(sample_data, simbroker_adapter):
    """Test that strategy attempts to generate trades."""
    cfg = {'symbol': 'EURUSD', 'volume': 1.0}
    report = run_backtest(simbroker_adapter, sample_data, cfg)
    
    # Strategy should at least attempt trades (could be 0 if no signals)
    assert 'total_trades' in report['summary']
    trades_count = report['summary']['total_trades']
    
    # Log for debugging
    print(f"Total trades generated: {trades_count}")
    
    # Just verify the field exists and is a number
    assert isinstance(trades_count, (int, float))


def test_metrics_present(sample_data, simbroker_adapter):
    """Test that key performance metrics are present."""
    cfg = {'symbol': 'EURUSD', 'volume': 1.0}
    report = run_backtest(simbroker_adapter, sample_data, cfg)
    
    summary = report['summary']
    
    # Check for common metrics (SimBroker should provide these)
    expected_metrics = [
        'starting_balance',
        'final_balance',
        'total_trades',
        'win_rate',
        'profit_factor',
        'max_drawdown'
    ]
    
    for metric in expected_metrics:
        assert metric in summary, f"Missing metric: {metric}"


def test_strategy_initialization():
    """Test that Strategy class initializes correctly."""
    cfg = {'symbol': 'EURUSD', 'volume': 1.0}
    strategy = Strategy(cfg)
    
    assert strategy.cfg == cfg
    assert strategy.symbol == 'EURUSD'
    assert strategy.volume == 1.0


def test_indicators_computation(sample_data):
    """Test that prepare_indicators returns valid data."""
    cfg = {'symbol': 'EURUSD', 'volume': 1.0}
    strategy = Strategy(cfg)
    
    indicators = strategy.prepare_indicators(sample_data)
    
    assert isinstance(indicators, dict)
    # Indicators dict might be empty if strategy doesn't use any
    # But it should be a dict
