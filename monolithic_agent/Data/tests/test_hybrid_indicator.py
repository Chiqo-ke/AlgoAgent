import pandas as pd
import numpy as np
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from indicator_calculator import compute_indicator, describe_indicator, validate_inputs
from registry import list_indicators, register, REGISTRY

# Create a fixture for sample data
@pytest.fixture
def sample_data():
    data = {
        'Open': np.random.rand(100) * 100,
        'High': np.random.rand(100) * 100 + 1,
        'Low': np.random.rand(100) * 100 - 1,
        'Close': np.random.rand(100) * 100,
        'Volume': np.random.randint(100000, 1000000, 100)
    }
    df = pd.DataFrame(data)
    df.index = pd.to_datetime(pd.date_range(start='2023-01-01', periods=100, freq='D'))
    return df

# Clear the registry before each test to ensure isolation
@pytest.fixture(autouse=True)
def clear_registry():
    REGISTRY.clear()
    # Register a dummy indicator for testing
    def dummy_sma(df, params):
        timeperiod = params.get("timeperiod", 30)
        return pd.DataFrame({f"SMA_{timeperiod}": df["Close"].rolling(window=timeperiod).mean()})

    register("SMA", dummy_sma, ["Close"], ["SMA"], {"timeperiod": 30})
    yield
    REGISTRY.clear()


def test_compute_indicator_valid(sample_data):
    # Test a simple indicator
    result_df, metadata = compute_indicator("SMA", sample_data, {"timeperiod": 10})
    assert result_df is not None
    assert not result_df.empty
    # The output column name is not guaranteed to be SMA_10, it depends on the implementation.
    # Let's check if the column name is in the metadata
    assert metadata["outputs"][0] in result_df.columns
    assert metadata is not None
    assert "source_hint" in metadata
    assert metadata["params"]["timeperiod"] == 10

def test_compute_indicator_invalid(sample_data):
    # Test with an indicator that doesn't exist
    with pytest.raises(ValueError, match="Indicator 'NONEXISTENT' not registered."):
        compute_indicator("NONEXISTENT", sample_data)

def test_describe_indicator_valid():
    # Test describing a valid indicator
    description = describe_indicator("SMA")
    assert description is not None
    assert "inputs" in description
    assert "outputs" in description
    assert "defaults" in description

def test_describe_indicator_invalid():
    # Test describing an invalid indicator
    with pytest.raises(ValueError, match="Indicator 'NONEXISTENT' not registered."):
        describe_indicator("NONEXISTENT")

def test_list_all_indicators():
    # Test listing all available indicators
    indicators = list_indicators()
    assert isinstance(indicators, list)
    assert "sma" in indicators

def test_validate_inputs_valid(sample_data):
    # Test with valid inputs
    validate_inputs(sample_data, ["Open", "High", "Low", "Close", "Volume"])

def test_validate_inputs_invalid(sample_data):
    # Test with missing columns
    with pytest.raises(ValueError, match="Missing required columns: non_existent_column"):
        validate_inputs(sample_data, ["non_existent_column"])

def test_compute_indicator_merges_params(sample_data):
    # Test that default and user-provided params are merged correctly
    result_df, metadata = compute_indicator("SMA", sample_data)
    assert metadata["params"]["timeperiod"] == 30 # Default value

    result_df, metadata = compute_indicator("SMA", sample_data, {"timeperiod": 5})
    assert metadata["params"]["timeperiod"] == 5 # User-provided value