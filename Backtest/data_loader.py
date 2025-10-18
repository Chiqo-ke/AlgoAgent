"""
Data Loader - Dynamic Data Loading Module for SimBroker
========================================================

This module provides dynamic functions for loading and preparing market data
for backtesting with SimBroker. It fetches data in real-time using the 
DataFetcher and computes indicators dynamically using the indicator calculator.

Features:
- Fetch live market data using yfinance
- Dynamic indicator calculation with parameter support
- Cache processed data with indicators
- Validate data integrity
- Support for multiple timeframes and periods

Version: 2.0.0
Last Updated: 2025-10-17
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging
import sys

# Add parent directory to path for imports
PARENT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PARENT_DIR))

try:
    from Data.data_fetcher import DataFetcher
    from Data.indicator_calculator import compute_indicator, describe_indicator
    from Data import registry
    DATA_FETCHER_AVAILABLE = True
    INDICATORS_AVAILABLE = True
except ImportError as e:
    DATA_FETCHER_AVAILABLE = False
    INDICATORS_AVAILABLE = False
    logging.warning(f"Data fetcher or indicator calculator not available: {e}")


logger = logging.getLogger(__name__)


class DataFormat:
    """Constants for data format"""
    # Required columns from yfinance
    REQUIRED_COLUMNS = ['Open', 'High', 'Low', 'Close', 'Volume']
    
    # Optional columns that may be present
    OPTIONAL_COLUMNS = ['Adj Close']


def fetch_market_data(
    ticker: str,
    period: str = "1mo",
    interval: str = "1d"
) -> pd.DataFrame:
    """
    Fetch market data using DataFetcher (yfinance).
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        period: Time period (e.g., '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'max')
        interval: Data interval (e.g., '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo')
    
    Returns:
        DataFrame with DatetimeIndex and OHLCV columns
    """
    if not DATA_FETCHER_AVAILABLE:
        raise RuntimeError("DataFetcher not available. Cannot fetch market data.")
    
    logger.info(f"Fetching {ticker} data: period={period}, interval={interval}")
    
    fetcher = DataFetcher()
    df = fetcher.fetch_historical_data(ticker, period=period, interval=interval)
    
    if df.empty:
        raise ValueError(f"No data returned for {ticker} with period={period}, interval={interval}")
    
    # Ensure datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    
    # Validate required columns
    missing = [col for col in DataFormat.REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}. Available: {list(df.columns)}")
    
    # Keep only OHLCV columns (drop Adj Close if present)
    df = df[DataFormat.REQUIRED_COLUMNS]
    
    # Convert to numeric, coerce errors
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Drop rows with NaN values
    df = df.dropna()
    
    # Sort by datetime
    df = df.sort_index()
    
    logger.info(f"Fetched {len(df)} rows for {ticker}")
    
    return df


def add_indicators(
    df: pd.DataFrame,
    indicators: Dict[str, Optional[Dict[str, Any]]]
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Add technical indicators to dataframe using indicator calculator.
    
    Args:
        df: DataFrame with OHLCV columns
        indicators: Dict mapping indicator name to parameters
                   Example: {'RSI': {'timeperiod': 14}, 'SMA': {'timeperiod': 20}}
                   Use None for default parameters: {'RSI': None}
    
    Returns:
        Tuple of (DataFrame with indicators, metadata dict)
    """
    if not INDICATORS_AVAILABLE:
        logger.warning("Indicator calculator not available. Returning original DataFrame.")
        return df.copy(), {'error': 'Indicator calculator not available'}
    
    if not indicators:
        return df.copy(), {}
    
    # Start with copy of original data
    result_df = df.copy()
    metadata = {}
    
    for indicator_name, params in indicators.items():
        try:
            # Use empty dict if params is None
            indicator_params = params if params is not None else {}
            
            # Compute indicator
            indicator_df, indicator_meta = compute_indicator(
                name=indicator_name,
                df=df,
                params=indicator_params
            )
            
            # Join indicator columns to result
            result_df = result_df.join(indicator_df, how='left')
            
            # Store metadata
            metadata[indicator_name] = indicator_meta
            
            logger.info(f"Added indicator: {indicator_name} with columns {list(indicator_df.columns)}")
            
        except Exception as e:
            logger.error(f"Failed to compute indicator {indicator_name}: {e}")
            metadata[indicator_name] = {'error': str(e)}
    
    return result_df, metadata


def get_available_indicators() -> List[str]:
    """
    Get list of available indicators from indicator calculator.
    
    Returns:
        List of indicator names
    """
    if not INDICATORS_AVAILABLE:
        return []
    
    try:
        return registry.list_indicators()
    except Exception as e:
        logger.error(f"Failed to list indicators: {e}")
        return []


def describe_indicator_params(indicator_name: str) -> Dict[str, Any]:
    """
    Get parameter information for an indicator.
    
    Args:
        indicator_name: Name of the indicator
    
    Returns:
        Dictionary with indicator metadata
    """
    if not INDICATORS_AVAILABLE:
        return {'error': 'Indicator calculator not available'}
    
    try:
        return describe_indicator(indicator_name)
    except Exception as e:
        return {'error': str(e)}


def load_market_data(
    ticker: str,
    indicators: Optional[Dict[str, Optional[Dict[str, Any]]]] = None,
    period: str = "1mo",
    interval: str = "1d",
    cache_dir: Optional[Path] = None,
    use_cache: bool = True
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Load market data dynamically with optional indicators.
    
    This is the main function for loading data in backtests. It fetches data
    in real-time using yfinance and computes indicators dynamically.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        indicators: Dict of indicators to compute
                   Example: {'RSI': {'timeperiod': 14}, 'SMA': {'timeperiod': 20}}
                   Use None for default parameters: {'RSI': None, 'MACD': None}
        period: Time period (default: '1mo')
                Valid: '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'max'
        interval: Data interval (default: '1d')
                 Valid: '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo'
        cache_dir: Directory to cache processed data (default: Backtest/data)
        use_cache: Whether to use cached data if available
    
    Returns:
        Tuple of (DataFrame with OHLCV + indicators, metadata dict)
    
    Example:
        >>> df, meta = load_market_data(
        ...     ticker='AAPL',
        ...     indicators={'RSI': {'timeperiod': 14}, 'SMA': {'timeperiod': 20}},
        ...     period='1mo',
        ...     interval='1d'
        ... )
    """
    # Set default cache directory
    if cache_dir is None:
        cache_dir = Path(__file__).parent / "data"
        cache_dir.mkdir(exist_ok=True)
    
    # Generate cache filename if using indicators
    cache_path = None
    if use_cache and indicators:
        # Create cache filename based on ticker, indicators, period, and interval
        indicator_str = "_".join(sorted(indicators.keys()))
        timestamp = datetime.now().strftime("%Y%m%d")
        cache_filename = f"{ticker}_{period}_{interval}_{indicator_str}_{timestamp}.parquet"
        cache_path = cache_dir / cache_filename
        
        # Check if cache exists and is recent (less than 1 day old)
        if cache_path.exists():
            cache_age_hours = (datetime.now().timestamp() - cache_path.stat().st_mtime) / 3600
            if cache_age_hours < 24:  # Cache valid for 24 hours
                logger.info(f"Loading from cache: {cache_path.name}")
                try:
                    df = pd.read_parquet(cache_path)
                    metadata = {
                        'source': 'cache',
                        'cache_path': str(cache_path),
                        'cache_age_hours': round(cache_age_hours, 2),
                        'ticker': ticker,
                        'period': period,
                        'interval': interval
                    }
                    return df, metadata
                except Exception as e:
                    logger.warning(f"Failed to load cache: {e}, fetching fresh data")
    
    # Fetch market data
    logger.info(f"Fetching fresh data for {ticker}")
    df = fetch_market_data(ticker, period, interval)
    
    # Add indicators if requested
    indicator_metadata = {}
    if indicators:
        df, indicator_metadata = add_indicators(df, indicators)
    
    # Save to cache
    if cache_path and indicators:
        try:
            df.to_parquet(cache_path)
            logger.info(f"Cached data to: {cache_path.name}")
        except Exception as e:
            logger.warning(f"Failed to cache data: {e}")
    
    # Build metadata
    metadata = {
        'source': 'yfinance',
        'ticker': ticker,
        'period': period,
        'interval': interval,
        'indicators': indicator_metadata,
        'rows': len(df),
        'columns': list(df.columns),
        'date_range': (str(df.index.min()), str(df.index.max()))
    }
    
    return df, metadata


# Convenience functions for common operations

def load_stock_data(
    ticker: str,
    indicators: Optional[List[str]] = None,
    period: str = "1mo",
    interval: str = "1d",
    **kwargs
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Simplified function to load stock data with default indicator parameters.
    
    Args:
        ticker: Stock ticker (e.g., 'AAPL', 'GOOGL', 'MSFT')
        indicators: List of indicator names (uses default parameters)
                   Example: ['RSI', 'SMA', 'MACD']
        period: Time period (default: '1mo')
        interval: Data interval (default: '1d')
        **kwargs: Additional arguments passed to load_market_data
    
    Returns:
        Tuple of (DataFrame, metadata)
    
    Example:
        >>> df, meta = load_stock_data('AAPL', indicators=['RSI', 'SMA'], period='3mo')
    """
    indicator_dict = None
    if indicators:
        # Use None for each indicator to get default parameters
        indicator_dict = {ind: None for ind in indicators}
    
    return load_market_data(ticker, indicators=indicator_dict, period=period, interval=interval, **kwargs)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("Data Loader - Example Usage (Dynamic Mode)")
    print("=" * 60)
    
    # List available indicators
    print("\n1. Available indicators:")
    indicators = get_available_indicators()
    print(f"   {len(indicators)} indicators available")
    if indicators:
        print(f"   Examples: {', '.join(indicators[:10])}")
    
    # Load data example with dynamic fetching
    print("\n2. Loading AAPL data with RSI and SMA indicators...")
    print("   (Fetching live data from yfinance)")
    try:
        df, metadata = load_market_data(
            ticker='AAPL',
            indicators={
                'RSI': {'timeperiod': 14},
                'SMA': {'timeperiod': 20}
            },
            period='1mo',
            interval='1d'
        )
        
        print(f"   ✅ Loaded {len(df)} rows")
        print(f"   Columns: {list(df.columns)}")
        print(f"   Date range: {metadata['date_range'][0]} to {metadata['date_range'][1]}")
        print(f"   Source: {metadata['source']}")
        print(f"\n   First 5 rows:")
        print(df.head())
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Example with simplified function
    print("\n3. Using simplified load_stock_data function...")
    try:
        df, metadata = load_stock_data(
            ticker='MSFT',
            indicators=['RSI', 'MACD'],
            period='5d',
            interval='1h'
        )
        
        print(f"   ✅ Loaded {len(df)} rows for MSFT")
        print(f"   Columns: {list(df.columns)}")
        print(f"   Date range: {metadata['date_range'][0]} to {metadata['date_range'][1]}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
