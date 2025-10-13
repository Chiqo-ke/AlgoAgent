import pandas as pd
import numpy as np
import pytest
from Data.indicator_calculator import compute_indicator
from Data.registry import list_indicators
from Data.talib_adapters import HAS_TALIB

# Fixture for a static, simple dataset
@pytest.fixture
def static_data():
    data = {
        'Open':  [10, 11, 14, 13, 12, 15, 17, 16, 14, 13],
        'High':  [11, 12, 15, 14, 13, 16, 18, 17, 15, 14],
        'Low':   [9,  10, 13, 12, 11, 14, 16, 15, 13, 12],
        'Close': [10, 12, 15, 14, 13, 16, 18, 17, 15, 14],
        'Volume':[100, 110, 120, 130, 140, 150, 160, 170, 180, 190]
    }
    df = pd.DataFrame(data)
    df.index = pd.to_datetime(pd.date_range(start='2023-01-01', periods=10, freq='D'))
    # Ensure column names are capitalized like in data_fetcher
    df.columns = [col.capitalize() for col in df.columns]
    return df

# Test for SMA output correctness
def test_sma_output(static_data):
    indicator_name = "SMA"
    params = {"timeperiod": 3}
    
    # Expected values for SMA with timeperiod=3 on the 'Close' series [10, 12, 15, 14, 13, 16, 18, 17, 15, 14]
    expected_values = [np.nan, np.nan, 12.33333, 13.66667, 14.0, 14.33333, 15.66667, 17.0, 16.66667, 15.33333]
    
    # Check if the indicator is registered before running the test
    assert indicator_name.lower() in list_indicators(), f"{indicator_name} is not registered."

    # Compute the indicator
    result_df, metadata = compute_indicator(indicator_name, static_data, params)
    
    # The output column name might vary, so we get it from the metadata
    output_column = metadata['outputs'][0]
    
    assert output_column in result_df.columns, f"Output column {output_column} not in result DataFrame."
    
    # Compare the computed values with the expected values
    np.testing.assert_allclose(result_df[output_column].values, expected_values, rtol=1e-5)

# Test for EMA output correctness
def test_ema_output(static_data):
    indicator_name = "EMA"
    params = {"timeperiod": 3}

    assert indicator_name.lower() in list_indicators(), f"{indicator_name} is not registered."

    result_df, metadata = compute_indicator(indicator_name, static_data, params)
    output_column = metadata['outputs'][0]

    assert output_column in result_df.columns
    
    # Conditionally select the baseline for comparison
    if HAS_TALIB:
        import talib
        expected_series = talib.EMA(static_data['Close'], timeperiod=params["timeperiod"])
    else:
        import ta
        expected_series = ta.trend.ema_indicator(static_data['Close'], window=params["timeperiod"])

    # Align series and compare non-NaN values
    comparison_df = pd.DataFrame({
        'actual': result_df[output_column],
        'expected': expected_series
    }).dropna()

    np.testing.assert_allclose(comparison_df['actual'], comparison_df['expected'], rtol=1e-5)

# Test for RSI output correctness
def test_rsi_output(static_data):
    indicator_name = "RSI"
    params = {"timeperiod": 4} # Using a period of 4 for this test

    assert indicator_name.lower() in list_indicators(), f"{indicator_name} is not registered."

    result_df, metadata = compute_indicator(indicator_name, static_data, params)
    output_column = metadata['outputs'][0]

    assert output_column in result_df.columns

    # Conditionally select the baseline for comparison
    if HAS_TALIB:
        import talib
        expected_series = talib.RSI(static_data['Close'], timeperiod=params["timeperiod"])
    else:
        import ta
        expected_series = ta.momentum.rsi(static_data['Close'], window=params["timeperiod"])

    # Align series and compare non-NaN values to handle different NaN padding
    comparison_df = pd.DataFrame({
        'actual': result_df[output_column],
        'expected': expected_series
    }).dropna()

    np.testing.assert_allclose(comparison_df['actual'], comparison_df['expected'], rtol=1e-5)