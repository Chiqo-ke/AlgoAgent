"""
Data Loader - Stable Data Loading Module for SimBroker
========================================================

IMMUTABLE MODULE - DO NOT MODIFY

This module provides stable functions for loading and preparing market data
for backtesting with SimBroker. It handles the standard CSV format from the
Data folder and integrates with the indicator calculator.

Features:
- Load CSV data with standard column format
- Parse both naming formats: TICKER_PERIOD_INTERVAL and batch_TICKER_PERIOD_INTERVAL
- Integrate with indicator calculator for technical indicators
- Cache processed data with indicators
- Validate data integrity

Version: 1.0.0
Last Updated: 2025-10-16
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging
import sys

# Add Data directory to path for indicator calculator
DATA_DIR = Path(__file__).parent.parent / "Data"
sys.path.insert(0, str(DATA_DIR))

try:
    from Data.indicator_calculator import compute_indicator, describe_indicator
    INDICATORS_AVAILABLE = True
except ImportError:
    INDICATORS_AVAILABLE = False
    logging.warning("Indicator calculator not available. Indicators will not be computed.")


logger = logging.getLogger(__name__)


class DataFormat:
    """Constants for data format"""
    # Required columns in CSV
    REQUIRED_COLUMNS = ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']
    
    # Column name mapping (lowercase)
    COLUMN_MAP = {
        'datetime': 'Datetime',
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume',
        'price': 'Close',  # 'Price' maps to 'Close'
    }
    
    # Ticker row index (row 1 in CSV, index 1 after header)
    TICKER_ROW_INDEX = 1


def parse_filename(filename: str) -> Dict[str, str]:
    """
    Parse data filename to extract metadata.
    
    Supports two formats:
    1. TICKER_PERIOD_INTERVAL_YYYYMMDD_HHMMSS.csv
       Example: AAPL_1d_1h_20251013_182543.csv
    
    2. batch_TICKER_PERIOD_INTERVAL_YYYYMMDD_HHMMSS.csv
       Example: batch_AAPL_1mo_1d_20251013_181604.csv
    
    Args:
        filename: Name of the CSV file
    
    Returns:
        Dictionary with keys: ticker, period, interval, date, time, is_batch
    """
    # Remove .csv extension
    name = filename.replace('.csv', '')
    
    # Check if batch format
    is_batch = name.startswith('batch_')
    if is_batch:
        name = name[6:]  # Remove 'batch_' prefix
    
    # Split by underscore
    parts = name.split('_')
    
    if len(parts) < 5:
        raise ValueError(f"Invalid filename format: {filename}")
    
    return {
        'ticker': parts[0],
        'period': parts[1],
        'interval': parts[2],
        'date': parts[3],
        'time': parts[4],
        'is_batch': is_batch,
        'filename': filename
    }


def load_raw_csv(filepath: Path) -> pd.DataFrame:
    """
    Load raw CSV file with standard format.
    
    Expected format:
    - Row 0: Column headers (Price, Close, High, Low, Open, Volume)
    - Row 1: Ticker symbols (Ticker, AAPL, AAPL, AAPL, ...)
    - Row 2: 'Datetime' label and empty cells
    - Row 3+: Actual data
    
    Args:
        filepath: Path to CSV file
    
    Returns:
        DataFrame with DatetimeIndex and OHLCV columns
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Data file not found: {filepath}")
    
    # Read CSV - first column is datetime, skip rows 1 and 2 (ticker and datetime label)
    df = pd.read_csv(filepath, skiprows=[1, 2], index_col=0)
    
    # Rename index to 'Datetime' if needed
    df.index.name = 'Datetime'
    
    # Rename columns to standard names (handle 'Price' -> 'Close')
    column_mapping = {}
    for col in df.columns:
        col_lower = col.lower()
        if col_lower in DataFormat.COLUMN_MAP:
            column_mapping[col] = DataFormat.COLUMN_MAP[col_lower]
    
    df = df.rename(columns=column_mapping)
    
    # Parse datetime index
    df.index = pd.to_datetime(df.index)
    
    # Validate required columns exist (excluding Datetime since it's the index)
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}. Available: {list(df.columns)}")
    
    # Keep only OHLCV columns
    df = df[required_cols]
    
    # Convert to numeric, coerce errors
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Drop rows with NaN values
    df = df.dropna()
    
    # Sort by datetime
    df = df.sort_index()
    
    logger.info(f"Loaded {len(df)} rows from {filepath.name}")
    
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
            # Compute indicator
            indicator_df, indicator_meta = compute_indicator(
                name=indicator_name,
                df=df,
                params=params
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


def find_data_file(
    ticker: str,
    data_dir: Optional[Path] = None,
    period: Optional[str] = None,
    interval: Optional[str] = None,
    is_batch: Optional[bool] = None
) -> Optional[Path]:
    """
    Find data file matching criteria.
    
    Args:
        ticker: Stock ticker (e.g., 'AAPL')
        data_dir: Directory to search (default: Data/data)
        period: Optional period filter (e.g., '1d', '1mo')
        interval: Optional interval filter (e.g., '1h', '1d')
        is_batch: Optional batch format filter
    
    Returns:
        Path to matching file, or None if not found
    """
    if data_dir is None:
        data_dir = Path(__file__).parent.parent / "Data" / "data"
    
    # Get all CSV files
    csv_files = list(data_dir.glob("*.csv"))
    
    # Filter by criteria
    for filepath in csv_files:
        try:
            meta = parse_filename(filepath.name)
            
            # Check ticker (case-insensitive)
            if meta['ticker'].upper() != ticker.upper():
                continue
            
            # Check optional filters
            if period is not None and meta['period'] != period:
                continue
            
            if interval is not None and meta['interval'] != interval:
                continue
            
            if is_batch is not None and meta['is_batch'] != is_batch:
                continue
            
            return filepath
            
        except ValueError:
            continue
    
    return None


def list_available_data(data_dir: Optional[Path] = None) -> List[Dict[str, str]]:
    """
    List all available data files with metadata.
    
    Args:
        data_dir: Directory to search (default: Data/data)
    
    Returns:
        List of metadata dictionaries
    """
    if data_dir is None:
        data_dir = Path(__file__).parent.parent / "Data" / "data"
    
    csv_files = list(data_dir.glob("*.csv"))
    
    results = []
    for filepath in csv_files:
        try:
            meta = parse_filename(filepath.name)
            meta['filepath'] = str(filepath)
            results.append(meta)
        except ValueError as e:
            logger.warning(f"Skipping invalid filename {filepath.name}: {e}")
    
    return results


def load_market_data(
    ticker: str,
    indicators: Optional[Dict[str, Optional[Dict[str, Any]]]] = None,
    data_dir: Optional[Path] = None,
    period: Optional[str] = None,
    interval: Optional[str] = None,
    is_batch: Optional[bool] = None,
    cache_dir: Optional[Path] = None,
    use_cache: bool = True
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Load market data with optional indicators.
    
    This is the main function for loading data in backtests.
    
    Args:
        ticker: Stock ticker symbol
        indicators: Dict of indicators to compute
                   Example: {'RSI': {'timeperiod': 14}, 'SMA': None}
        data_dir: Directory containing CSV files (default: Data/data)
        period: Optional period filter
        interval: Optional interval filter
        is_batch: Optional batch format filter
        cache_dir: Directory to cache processed data (default: Backtest/data)
        use_cache: Whether to use cached data if available
    
    Returns:
        Tuple of (DataFrame with OHLCV + indicators, metadata dict)
    """
    # Set default directories
    if data_dir is None:
        data_dir = Path(__file__).parent.parent / "Data" / "data"
    
    if cache_dir is None:
        cache_dir = Path(__file__).parent / "data"
        cache_dir.mkdir(exist_ok=True)
    
    # Find data file
    filepath = find_data_file(ticker, data_dir, period, interval, is_batch)
    if filepath is None:
        raise FileNotFoundError(
            f"No data file found for ticker={ticker}, period={period}, "
            f"interval={interval}, is_batch={is_batch}"
        )
    
    # Parse filename metadata
    file_meta = parse_filename(filepath.name)
    
    # Generate cache filename if using indicators
    cache_path = None
    if use_cache and indicators:
        # Create cache filename based on ticker, indicators, and parameters
        indicator_str = "_".join(sorted(indicators.keys()))
        cache_filename = f"{ticker}_{indicator_str}_{file_meta['date']}_{file_meta['time']}.parquet"
        cache_path = cache_dir / cache_filename
        
        # Check if cache exists and is newer than source
        if cache_path.exists() and cache_path.stat().st_mtime > filepath.stat().st_mtime:
            logger.info(f"Loading from cache: {cache_path.name}")
            df = pd.read_parquet(cache_path)
            metadata = {
                'source': 'cache',
                'cache_path': str(cache_path),
                'file_meta': file_meta
            }
            return df, metadata
    
    # Load raw data
    logger.info(f"Loading data from: {filepath.name}")
    df = load_raw_csv(filepath)
    
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
        'source': 'csv',
        'filepath': str(filepath),
        'file_meta': file_meta,
        'indicators': indicator_metadata,
        'rows': len(df),
        'columns': list(df.columns),
        'date_range': (str(df.index.min()), str(df.index.max()))
    }
    
    return df, metadata


def get_available_indicators() -> List[str]:
    """
    Get list of available indicators from indicator calculator.
    
    Returns:
        List of indicator names
    """
    if not INDICATORS_AVAILABLE:
        return []
    
    try:
        from Data import registry
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


# Convenience functions for common operations

def load_stock_data(
    ticker: str,
    indicators: Optional[List[str]] = None,
    **kwargs
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Simplified function to load stock data with default indicator parameters.
    
    Args:
        ticker: Stock ticker
        indicators: List of indicator names (uses default parameters)
        **kwargs: Additional arguments passed to load_market_data
    
    Returns:
        Tuple of (DataFrame, metadata)
    """
    indicator_dict = None
    if indicators:
        indicator_dict = {ind: None for ind in indicators}
    
    return load_market_data(ticker, indicators=indicator_dict, **kwargs)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("Data Loader - Example Usage")
    print("=" * 60)
    
    # List available data
    print("\n1. Available data files:")
    available = list_available_data()
    for item in available[:5]:  # Show first 5
        print(f"   {item['ticker']:6s} {item['period']:4s} {item['interval']:3s} "
              f"{'(batch)' if item['is_batch'] else '       '} {item['filename']}")
    print(f"   ... {len(available)} total files")
    
    # List available indicators
    print("\n2. Available indicators:")
    indicators = get_available_indicators()
    print(f"   {len(indicators)} indicators available")
    if indicators:
        print(f"   Examples: {', '.join(indicators[:10])}")
    
    # Load data example
    print("\n3. Loading AAPL data with RSI and SMA indicators...")
    try:
        df, metadata = load_market_data(
            ticker='AAPL',
            indicators={
                'RSI': {'timeperiod': 14},
                'SMA': {'timeperiod': 20}
            }
        )
        
        print(f"   ✅ Loaded {len(df)} rows")
        print(f"   Columns: {list(df.columns)}")
        print(f"   Date range: {metadata['date_range'][0]} to {metadata['date_range'][1]}")
        print(f"\n   First 5 rows:")
        print(df.head())
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
