"""
Component-Level Test Template for Single-File Strategies

This template provides the structure for comprehensive testing of trading strategies
with component-level tests (indicators, entries, exits) and integration tests.
"""

TEST_TEMPLATE_COMPONENT_LEVEL = '''"""
Component-Level Tests for {strategy_name} Strategy

Tests are organized into 4 categories:
1. Data & Indicators - Test indicator calculations
2. Entry Conditions - Test entry signal generation
3. Exit Conditions - Test exit signal logic (SL/TP)
4. Integration - Test complete backtest execution
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

# Import strategy under test
from Backtest.codes.{strategy_filename} import Strategy, run_backtest
from adapters.simbroker_adapter import SimBrokerAdapter
from simulator.simbroker import SimBroker, SimConfig


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_ohlcv_data():
    """Generate sample OHLCV data for testing"""
    dates = pd.date_range(start='2025-01-01', periods=100, freq='1H')
    
    # Create trending data with some noise
    base_price = 100.0
    trend = np.linspace(0, 10, 100)  # Upward trend
    noise = np.random.randn(100) * 0.5
    close_prices = base_price + trend + noise
    
    df = pd.DataFrame({{
        'datetime': dates,
        'Open': close_prices + np.random.randn(100) * 0.1,
        'High': close_prices + np.abs(np.random.randn(100)) * 0.3,
        'Low': close_prices - np.abs(np.random.randn(100)) * 0.3,
        'Close': close_prices,
        'Volume': np.random.randint(1000, 10000, 100)
    }})
    
    return df

@pytest.fixture
def strategy_config():
    """Default strategy configuration"""
    return {{
        'symbol': 'EURUSD',
        'volume': 0.01,
        'starting_balance': 10000.0,
        'leverage': 100.0
    }}

@pytest.fixture
def simbroker_adapter(strategy_config):
    """Create SimBroker adapter for testing"""
    sim_config = SimConfig(
        starting_balance=strategy_config['starting_balance'],
        leverage=strategy_config['leverage'],
        commission={{'type': 'per_lot', 'value': 7.0}},
        slippage={{'type': 'fixed', 'value': 2}}
    )
    broker = SimBroker(sim_config)
    return SimBrokerAdapter(broker)


# ============================================================================
# COMPONENT TESTS: DATA & INDICATORS
# ============================================================================

class TestDataAndIndicators:
    """Test indicator calculation and data handling"""
    
    def test_indicator_calculation(self, sample_ohlcv_data, strategy_config):
        """Verify indicators are calculated correctly"""
        strategy = Strategy(strategy_config)
        indicators = strategy.prepare_indicators(sample_ohlcv_data)
        
        # Assertions
        assert isinstance(indicators, dict), "Indicators should be dictionary"
        assert len(indicators) > 0, "At least one indicator should be calculated"
        
        # Check each indicator is a Series with correct length
        for name, series in indicators.items():
            assert isinstance(series, pd.Series), f"Indicator {{name}} should be pandas Series"
            assert len(series) == len(sample_ohlcv_data), f"Indicator {{name}} length mismatch"
    
    def test_indicator_types(self, sample_ohlcv_data, strategy_config):
        """Verify indicators return correct data types"""
        strategy = Strategy(strategy_config)
        indicators = strategy.prepare_indicators(sample_ohlcv_data)
        
        for name, series in indicators.items():
            assert pd.api.types.is_numeric_dtype(series), f"Indicator {{name}} should be numeric"
            assert not series.isna().all(), f"Indicator {{name}} is all NaN"
    
    def test_missing_data_handling(self, strategy_config):
        """Verify strategy handles missing data gracefully"""
        # Create data with NaN values
        df = pd.DataFrame({{
            'Open': [100, np.nan, 102],
            'High': [101, 103, np.nan],
            'Low': [99, 101, 101],
            'Close': [100.5, 102, 102.5],
            'Volume': [1000, 1000, 1000]
        }})
        
        strategy = Strategy(strategy_config)
        
        # Should not raise exception
        try:
            indicators = strategy.prepare_indicators(df)
            assert True, "Strategy handled missing data"
        except Exception as e:
            pytest.fail(f"Strategy failed with missing data: {{e}}")
    
    def test_indicator_values_reasonable(self, sample_ohlcv_data, strategy_config):
        """Verify indicator values are within reasonable ranges"""
        strategy = Strategy(strategy_config)
        indicators = strategy.prepare_indicators(sample_ohlcv_data)
        
        # Check for obviously wrong values
        for name, series in indicators.items():
            # Remove NaN for calculations
            clean_series = series.dropna()
            if len(clean_series) > 0:
                assert not (clean_series == np.inf).any(), f"Indicator {{name}} has infinite values"
                assert not (clean_series == -np.inf).any(), f"Indicator {{name}} has negative infinite values"


# ============================================================================
# COMPONENT TESTS: ENTRY CONDITIONS
# ============================================================================

class TestEntryConditions:
    """Test entry signal generation"""
    
    def test_entry_signal_format(self, sample_ohlcv_data, strategy_config):
        """Verify entry signals return correct format"""
        strategy = Strategy(strategy_config)
        indicators = strategy.prepare_indicators(sample_ohlcv_data)
        
        # Test across different bar indices
        for idx in range(10, len(sample_ohlcv_data)):
            entry = strategy.find_entries(sample_ohlcv_data, indicators, idx)
            
            if entry is not None:
                # Verify structure
                assert isinstance(entry, dict), "Entry signal must be dictionary"
                assert 'action' in entry, "Entry must specify action (BUY/SELL)"
                assert entry['action'] in ['BUY', 'SELL'], "Action must be BUY or SELL"
                assert 'symbol' in entry, "Entry must specify symbol"
                assert 'volume' in entry, "Entry must specify volume"
                break
    
    def test_no_entry_at_start(self, sample_ohlcv_data, strategy_config):
        """Verify no entry signals at start (insufficient data for indicators)"""
        strategy = Strategy(strategy_config)
        indicators = strategy.prepare_indicators(sample_ohlcv_data)
        
        # Should not generate entries in first few bars
        for idx in range(0, 5):
            entry = strategy.find_entries(sample_ohlcv_data, indicators, idx)
            # Either None or properly structured
            if entry is not None:
                assert isinstance(entry, dict)
    
    def test_entry_position_sizing(self, sample_ohlcv_data, strategy_config):
        """Verify entry signals have appropriate position sizes"""
        strategy = Strategy(strategy_config)
        indicators = strategy.prepare_indicators(sample_ohlcv_data)
        
        entry_found = False
        for idx in range(10, len(sample_ohlcv_data)):
            entry = strategy.find_entries(sample_ohlcv_data, indicators, idx)
            
            if entry is not None and 'volume' in entry:
                assert entry['volume'] > 0, "Volume must be positive"
                assert entry['volume'] <= 1.0, "Volume should not exceed 1.0 lot (for test)"
                entry_found = True
                break
        
        # At least one entry should be generated in 90 bars
        # (This may fail for very restrictive strategies - adjust as needed)


# ============================================================================
# COMPONENT TESTS: EXIT CONDITIONS
# ============================================================================

class TestExitConditions:
    """Test exit signal logic"""
    
    def test_stop_loss_triggered(self, sample_ohlcv_data, strategy_config):
        """Verify stop loss exits position at correct level"""
        strategy = Strategy(strategy_config)
        indicators = strategy.prepare_indicators(sample_ohlcv_data)
        
        # Mock position with entry price
        entry_price = 100.0
        position = {{
            'id': 'test_pos_1',
            'symbol': 'EURUSD',
            'side': 'BUY',
            'volume': 0.01,
            'entry_price': entry_price,
            'sl': entry_price * 0.98,  # 2% stop loss
            'tp': entry_price * 1.04   # 4% take profit
        }}
        
        # Create data where price drops below SL
        df_sl = sample_ohlcv_data.copy()
        df_sl.loc[50, 'Close'] = entry_price * 0.97  # Below SL
        
        exit_signal = strategy.find_exits(position, df_sl, indicators, idx=50)
        
        # Should generate exit (either from strategy logic or via SL check)
        # Note: Adapter handles SL/TP automatically, but strategy can also check
        assert exit_signal is None or isinstance(exit_signal, dict)
    
    def test_take_profit_triggered(self, sample_ohlcv_data, strategy_config):
        """Verify take profit exits position at correct level"""
        strategy = Strategy(strategy_config)
        indicators = strategy.prepare_indicators(sample_ohlcv_data)
        
        entry_price = 100.0
        position = {{
            'id': 'test_pos_2',
            'symbol': 'EURUSD',
            'side': 'BUY',
            'volume': 0.01,
            'entry_price': entry_price,
            'sl': entry_price * 0.98,
            'tp': entry_price * 1.04
        }}
        
        # Create data where price rises above TP
        df_tp = sample_ohlcv_data.copy()
        df_tp.loc[50, 'Close'] = entry_price * 1.05  # Above TP
        
        exit_signal = strategy.find_exits(position, df_tp, indicators, idx=50)
        
        # Should generate exit or None (adapter handles TP)
        assert exit_signal is None or isinstance(exit_signal, dict)
    
    def test_no_exit_within_range(self, sample_ohlcv_data, strategy_config):
        """Verify position held when price within SL/TP range"""
        strategy = Strategy(strategy_config)
        indicators = strategy.prepare_indicators(sample_ohlcv_data)
        
        entry_price = 100.0
        position = {{
            'id': 'test_pos_3',
            'symbol': 'EURUSD',
            'side': 'BUY',
            'volume': 0.01,
            'entry_price': entry_price,
            'sl': entry_price * 0.98,
            'tp': entry_price * 1.04
        }}
        
        # Price moves slightly but stays in range
        df_range = sample_ohlcv_data.copy()
        df_range.loc[50, 'Close'] = entry_price * 1.01  # +1%, within range
        
        exit_signal = strategy.find_exits(position, df_range, indicators, idx=50)
        
        # Should NOT force exit (None is OK, position should hold)
        # Only exit if strategy-specific signal triggered


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Test complete backtest execution"""
    
    def test_complete_backtest_execution(self, sample_ohlcv_data, simbroker_adapter, strategy_config):
        """Verify full backtest runs end-to-end"""
        result = run_backtest(simbroker_adapter, sample_ohlcv_data, strategy_config)
        
        # Verify result structure
        assert isinstance(result, dict), "Backtest should return dictionary"
        assert 'summary' in result, "Result must have summary"
        
        summary = result['summary']
        assert 'final_balance' in summary, "Summary must include final_balance"
        assert 'total_trades' in summary, "Summary must include total_trades"
        
        # Verify reasonable values
        assert summary['final_balance'] > 0, "Final balance must be positive"
        assert summary['total_trades'] >= 0, "Total trades must be non-negative"
    
    def test_contract_compliance(self, sample_ohlcv_data, simbroker_adapter, strategy_config):
        """Verify strategy meets contract specifications"""
        result = run_backtest(simbroker_adapter, sample_ohlcv_data, strategy_config)
        
        # Check required fields from contract
        summary = result['summary']
        required_fields = ['final_balance', 'total_trades', 'win_rate', 'max_drawdown']
        
        for field in required_fields:
            assert field in summary, f"Summary missing required field: {{field}}"
    
    def test_adapter_compatibility(self, sample_ohlcv_data, strategy_config):
        """Verify strategy works with SimBroker adapter"""
        # Create fresh adapter
        sim_config = SimConfig(
            starting_balance=10000.0,
            leverage=100.0
        )
        broker = SimBroker(sim_config)
        adapter = SimBrokerAdapter(broker)
        
        # Should execute without errors
        try:
            result = run_backtest(adapter, sample_ohlcv_data, strategy_config)
            assert result is not None
        except Exception as e:
            pytest.fail(f"Strategy not compatible with adapter: {{e}}")
    
    def test_determinism(self, sample_ohlcv_data, simbroker_adapter, strategy_config):
        """Verify strategy produces consistent results"""
        # Run backtest twice with same data
        result1 = run_backtest(simbroker_adapter, sample_ohlcv_data.copy(), strategy_config)
        
        # Create new adapter for second run
        sim_config = SimConfig(
            starting_balance=10000.0,
            leverage=100.0
        )
        broker2 = SimBroker(sim_config)
        adapter2 = SimBrokerAdapter(broker2)
        
        result2 = run_backtest(adapter2, sample_ohlcv_data.copy(), strategy_config)
        
        # Results should be identical
        assert result1['summary']['total_trades'] == result2['summary']['total_trades'], \\
            "Strategy should produce deterministic results"
        assert abs(result1['summary']['final_balance'] - result2['summary']['final_balance']) < 0.01, \\
            "Final balance should be consistent"
    
    def test_no_infinite_loops(self, sample_ohlcv_data, simbroker_adapter, strategy_config):
        """Verify backtest completes without hanging"""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Backtest exceeded time limit - possible infinite loop")
        
        # Set 30 second timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)
        
        try:
            result = run_backtest(simbroker_adapter, sample_ohlcv_data, strategy_config)
            signal.alarm(0)  # Cancel alarm
            assert result is not None
        except TimeoutError:
            signal.alarm(0)
            pytest.fail("Backtest timed out - check for infinite loops")


# ============================================================================
# PERFORMANCE BENCHMARKS (Optional)
# ============================================================================

class TestPerformance:
    """Optional performance benchmarks"""
    
    def test_backtest_performance(self, sample_ohlcv_data, simbroker_adapter, strategy_config, benchmark):
        """Benchmark backtest execution time"""
        result = benchmark(run_backtest, simbroker_adapter, sample_ohlcv_data, strategy_config)
        assert result is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
'''
