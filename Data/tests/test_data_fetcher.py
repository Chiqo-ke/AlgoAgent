import pytest
import pandas as pd
from datetime import datetime
from Data.data_fetcher import DataFetcher

@pytest.fixture
def mock_yfinance(mocker):
    """Fixture to mock yfinance.download"""
    return mocker.patch('yfinance.download')

@pytest.fixture
def fetcher():
    """Fixture to provide a DataFetcher instance"""
    return DataFetcher()

@pytest.fixture
def sample_dataframe():
    """Fixture to provide a sample yfinance-like DataFrame"""
    data = {
        'Open': [100, 102, 101],
        'High': [103, 104, 102],
        'Low': [99, 101, 100],
        'Close': [102, 103, 101],
        'Volume': [1000, 1100, 1200]
    }
    df = pd.DataFrame(data, index=pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03']))
    return df

# Tests for fetch_historical_data
def test_fetch_historical_data_success(fetcher, mock_yfinance, sample_dataframe):
    mock_yfinance.return_value = sample_dataframe
    
    df = fetcher.fetch_historical_data("AAPL", period="1y", interval="1d")

    mock_yfinance.assert_called_once_with("AAPL", period="1y", interval="1d")
    pd.testing.assert_frame_equal(df, sample_dataframe)
    assert isinstance(df.index, pd.DatetimeIndex)
    assert all(col in df.columns for col in ['Open', 'High', 'Low', 'Close', 'Volume'])

def test_fetch_historical_data_empty(fetcher, mock_yfinance):
    mock_yfinance.return_value = pd.DataFrame()
    
    df = fetcher.fetch_historical_data("EMPTY", period="1y", interval="1d")

    mock_yfinance.assert_called_once_with("EMPTY", period="1y", interval="1d")
    assert df.empty

def test_fetch_historical_data_error(fetcher, mock_yfinance):
    mock_yfinance.side_effect = Exception("Test Error")
    
    df = fetcher.fetch_historical_data("ERROR", period="1y", interval="1d")

    mock_yfinance.assert_called_once_with("ERROR", period="1y", interval="1d")
    assert df.empty

# Tests for fetch_data_by_date_range
def test_fetch_data_by_date_range_success(fetcher, mock_yfinance, sample_dataframe):
    mock_yfinance.return_value = sample_dataframe
    start_date = "2023-01-01"
    end_date = "2023-01-03"

    df = fetcher.fetch_data_by_date_range("GOOG", start_date=start_date, end_date=end_date, interval="1d")

    mock_yfinance.assert_called_once_with("GOOG", start=start_date, end=end_date, interval="1d")
    pd.testing.assert_frame_equal(df, sample_dataframe)
    assert isinstance(df.index, pd.DatetimeIndex)
    assert all(col in df.columns for col in ['Open', 'High', 'Low', 'Close', 'Volume'])

def test_fetch_data_by_date_range_empty(fetcher, mock_yfinance):
    mock_yfinance.return_value = pd.DataFrame()
    start_date = "2023-01-01"
    end_date = "2023-01-03"

    df = fetcher.fetch_data_by_date_range("EMPTY", start_date=start_date, end_date=end_date)

    mock_yfinance.assert_called_once_with("EMPTY", start=start_date, end=end_date, interval="1d")
    assert df.empty

def test_fetch_data_by_date_range_error(fetcher, mock_yfinance):
    mock_yfinance.side_effect = Exception("Test Error")
    start_date = "2023-01-01"
    end_date = "2023-01-03"

    df = fetcher.fetch_data_by_date_range("ERROR", start_date=start_date, end_date=end_date)

    mock_yfinance.assert_called_once_with("ERROR", start=start_date, end=end_date, interval="1d")
    assert df.empty
