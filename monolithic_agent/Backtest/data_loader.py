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
from typing import Dict, List, Optional, Tuple, Any, Generator
from datetime import datetime
import logging
import sys
import re

# Add parent directory to path for imports
PARENT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PARENT_DIR))

# Initialize logger first
logger = logging.getLogger(__name__)

try:
    from Data.data_fetcher import DataFetcher
    from Data.indicator_calculator import compute_indicator, describe_indicator
    from Data import registry
    DATA_FETCHER_AVAILABLE = True
    INDICATORS_AVAILABLE = True
except ImportError as e:
    DATA_FETCHER_AVAILABLE = False
    INDICATORS_AVAILABLE = False
    logger.warning(f"Data fetcher or indicator calculator not available: {e}")

# Try to import TVscraper as fallback for when yfinance fails
try:
    # Add TVscraper to path if not already installed as package
    # Path: Backtest -> monolithic_agent -> AlgoAgent -> Documents -> TVscraper
    TV_SCRAPER_PATH = Path(__file__).parent.parent.parent.parent / "TVscraper"
    if TV_SCRAPER_PATH.exists() and str(TV_SCRAPER_PATH) not in sys.path:
        sys.path.insert(0, str(TV_SCRAPER_PATH))
        logger.info(f"Added TVscraper to path: {TV_SCRAPER_PATH}")
    
    from tvscraper.mcp_scraper import MCPTradingViewScraper
    TV_SCRAPER_AVAILABLE = True
    logger.info("TVscraper available as data source")
except ImportError as e:
    TV_SCRAPER_AVAILABLE = False
    logger.warning(f"TVscraper not available: {e}")


class DataFormat:
    """Constants for data format"""
    # Required columns from yfinance
    REQUIRED_COLUMNS = ['Open', 'High', 'Low', 'Close', 'Volume']
    
    # Optional columns that may be present
    OPTIONAL_COLUMNS = ['Adj Close']


WAREHOUSE_DIR = PARENT_DIR / "Data" / "data"


def _normalize_interval(interval: str) -> str:
    """Normalize requested interval to warehouse filename suffix format."""
    normalized = str(interval).strip().lower()
    interval_aliases = {
        "60m": "1h",
        "1hr": "1h",
        "1hour": "1h",
        "120m": "2h",
        "2hr": "2h",
        "2hour": "2h",
        "240m": "4h",
        "4hr": "4h",
        "4hour": "4h",
        "1wk": "1w",
    }
    return interval_aliases.get(normalized, normalized)


def _symbol_candidates(symbol: str) -> List[str]:
    """Build case-insensitive symbol candidates, including alias-like variants."""
    raw = str(symbol).strip().upper()
    candidates = {raw}

    if ":" in raw:
        candidates.add(raw.split(":")[-1])

    for sep in ("/", "-", "_", "."):
        if sep in raw:
            candidates.add(raw.replace(sep, ""))

    normalized = set()
    for candidate in candidates:
        cleaned = re.sub(r"[^A-Z0-9]", "", candidate)
        if cleaned:
            normalized.add(cleaned)

    return sorted(normalized)


def _extract_symbol_from_filename(file_path: Path) -> str:
    """Extract symbol segment from `<symbol>_<timeframe>.csv` filename."""
    stem = file_path.stem
    if "_" not in stem:
        return stem
    return stem.rsplit("_", 1)[0]


def _extract_timeframe_from_filename(file_path: Path) -> str:
    """Extract timeframe suffix from `<symbol>_<timeframe>.csv` filename."""
    stem = file_path.stem
    if "_" not in stem:
        return ""
    return stem.rsplit("_", 1)[1].lower()


def _resolve_warehouse_file(ticker: str, interval: str) -> Optional[Path]:
    """Resolve matching warehouse CSV using case-insensitive + alias-style matching."""
    if not WAREHOUSE_DIR.exists():
        logger.error(f"Warehouse directory not found: {WAREHOUSE_DIR}")
        return None

    target_interval = _normalize_interval(interval)
    ticker_candidates = set(_symbol_candidates(ticker))

    for csv_file in sorted(WAREHOUSE_DIR.glob("*.csv")):
        file_interval = _extract_timeframe_from_filename(csv_file)
        if file_interval != target_interval:
            continue

        file_symbol = _extract_symbol_from_filename(csv_file)
        file_symbol_candidates = set(_symbol_candidates(file_symbol))

        if ticker_candidates.intersection(file_symbol_candidates):
            return csv_file

    return None


def _empty_ohlcv_frame() -> pd.DataFrame:
    """Return an empty OHLCV dataframe with expected schema."""
    empty_df = pd.DataFrame(columns=DataFormat.REQUIRED_COLUMNS)
    empty_df.index = pd.DatetimeIndex([], tz="UTC")
    return empty_df


def _normalize_period_slice(df: pd.DataFrame, period: str) -> pd.DataFrame:
    """Filter dataframe by period relative to available warehouse data window."""
    if df.empty:
        return df

    period = str(period).strip().lower()
    if period == "max":
        return df

    duration_map = {
        "1d": pd.Timedelta(days=1),
        "5d": pd.Timedelta(days=5),
        "1wk": pd.Timedelta(days=7),
        "1mo": pd.Timedelta(days=30),
        "3mo": pd.Timedelta(days=90),
        "6mo": pd.Timedelta(days=180),
        "1y": pd.Timedelta(days=365),
        "2y": pd.Timedelta(days=730),
        "5y": pd.Timedelta(days=1825),
        "10y": pd.Timedelta(days=3650),
    }

    duration = duration_map.get(period)
    if duration is None:
        logger.warning(f"Unknown period '{period}', returning full warehouse range")
        return df

    end_ts = df.index.max()
    start_ts = end_ts - duration
    return df[df.index >= start_ts]


def _load_warehouse_csv(
    ticker: str,
    interval: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Tuple[pd.DataFrame, Optional[Path]]:
    """Load and normalize OHLCV data directly from local warehouse CSV."""
    csv_file = _resolve_warehouse_file(ticker, interval)
    if csv_file is None:
        logger.warning(
            f"Warehouse CSV not found for ticker={ticker}, interval={interval}. "
            "Skipping symbol."
        )
        return _empty_ohlcv_frame(), None

    raw_df = pd.read_csv(csv_file)
    if raw_df.empty:
        logger.warning(f"Warehouse CSV is empty: {csv_file.name}")
        return _empty_ohlcv_frame(), csv_file

    rename_map = {
        "datetime": "Datetime",
        "timestamp": "Datetime",
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "volume": "Volume",
    }

    normalized_columns = {col: rename_map.get(str(col).strip().lower(), col) for col in raw_df.columns}
    df = raw_df.rename(columns=normalized_columns)

    if "Datetime" not in df.columns:
        raise ValueError(f"Missing datetime column in warehouse file: {csv_file}")

    missing_cols = [col for col in DataFormat.REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Warehouse file {csv_file.name} missing required columns: {missing_cols}. "
            f"Available: {list(df.columns)}"
        )

    df["Datetime"] = pd.to_datetime(df["Datetime"], utc=True, errors="coerce")
    df = df.dropna(subset=["Datetime"])
    df = df.set_index("Datetime")

    for col in DataFormat.REQUIRED_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=DataFormat.REQUIRED_COLUMNS)
    df = df.sort_index()
    df = df[~df.index.duplicated(keep="last")]
    df = df[DataFormat.REQUIRED_COLUMNS]

    if start_date:
        start_ts = pd.to_datetime(start_date, utc=True, errors="coerce")
        if pd.isna(start_ts):
            raise ValueError(f"Invalid start_date: {start_date}")
        df = df[df.index >= start_ts]

    if end_date:
        end_ts = pd.to_datetime(end_date, utc=True, errors="coerce")
        if pd.isna(end_ts):
            raise ValueError(f"Invalid end_date: {end_date}")
        df = df[df.index <= end_ts]

    return df, csv_file


def fetch_market_data(
    ticker: str,
    period: str = "1mo",
    interval: str = "1d"
) -> pd.DataFrame:
    """
    Fetch market data preferring TVscraper as the primary source.
    Falls back to yfinance only if TVscraper is unavailable or fails.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        period: Time period (e.g., '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'max')
        interval: Data interval (e.g., '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo')
    
    Returns:
        DataFrame with DatetimeIndex and OHLCV columns
    """
    logger.info(f"Loading warehouse data for {ticker}: period={period}, interval={interval}")
    df, csv_file = _load_warehouse_csv(ticker=ticker, interval=interval)
    df = _normalize_period_slice(df, period=period)

    if df.empty:
        logger.warning(
            f"No warehouse rows available for ticker={ticker}, interval={interval}, period={period}. "
            "Symbol skipped."
        )
        return _empty_ohlcv_frame()

    source_name = csv_file.name if csv_file else "unknown"
    logger.info(f"Loaded {len(df)} rows for {ticker} from warehouse file {source_name}")
    return df


def fetch_market_data_with_tvscraper(
    ticker: str,
    period: str = "1mo",
    interval: str = "1d"
) -> pd.DataFrame:
    """
    Fallback: Fetch market data using TVscraper when yfinance fails.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        period: Time period (e.g., '1mo', '3mo', '6mo', '1y')
        interval: Data interval (e.g., '1m', '5m', '1h', '1d')
    
    Returns:
        DataFrame with DatetimeIndex and OHLCV columns
    """
    if not TV_SCRAPER_AVAILABLE:
        raise RuntimeError("TVscraper not available as fallback")
    
    logger.info(f"Using TVscraper for {ticker} (period={period}, interval={interval})")
    
    # Suppress stdout to avoid emoji encoding errors on Windows
    import io
    import contextlib
    
    try:
        # Initialize scraper with stdout suppression
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            scraper = MCPTradingViewScraper()
        
            # Initialize browser (required for TVscraper)
            if not scraper.init_browser():
                raise RuntimeError("Failed to initialize browser for TVscraper")
            
            # Navigate to TradingView
            if not scraper.navigate_to_tradingview():
                raise RuntimeError("Failed to navigate to TradingView")
            
            # Set symbol
            scraper.change_symbol(ticker)
            
            # Map interval to TradingView timeframe format
            timeframe_map = {
                "1m": "1m", "2m": "2m", "3m": "3m", "5m": "5m",
                "15m": "15m", "30m": "30m", "60m": "1h", "90m": "90m",
                "1h": "1h", "1d": "1d", "1w": "1w", "1wk": "1w",
                "1mo": "1M"
            }
            tv_timeframe = timeframe_map.get(interval, interval)
            scraper.change_timeframe(tv_timeframe)
            
            # Calculate approximate bars count based on period
            period_to_bars = {
                "1d": 24, "5d": 120, "1mo": 720, "3mo": 2160,
                "6mo": 4320, "1y": 8760, "2y": 17520, "5y": 43800
            }
            bars_count = period_to_bars.get(period, 720)  # Default to 1 month
            
            # Fetch historical data
            logger.info(f"Fetching {bars_count} bars from TradingView...")
            historical_data = scraper.get_historical_data(bars_count=bars_count)
        
        if not historical_data:
            raise ValueError(f"No data returned from TVscraper for {ticker}")
        
        # Convert TVscraper data format to DataFrame
        data_rows = []
        for bar in historical_data:
            data_rows.append({
                'timestamp': pd.to_datetime(bar['timestamp']),
                'Open': float(bar['open']),
                'High': float(bar['high']),
                'Low': float(bar['low']),
                'Close': float(bar['close']),
                'Volume': float(bar.get('volume', 0))
            })
        
        # Create DataFrame
        df = pd.DataFrame(data_rows)
        df.set_index('timestamp', inplace=True)
        df.index.name = None  # Remove index name to match yfinance format
        
        # Ensure correct data types
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Drop rows with NaN values
        df = df.dropna()
        
        # Sort by datetime
        df = df.sort_index()
        
        logger.info(f"TVscraper fetched {len(df)} rows for {ticker}")
        
        return df
        
    except Exception as e:
        # Remove emoji characters from error message to avoid encoding issues
        error_msg = str(e).encode('ascii', errors='ignore').decode('ascii')
        logger.error(f"TVscraper fetch failed: {error_msg}")
        raise RuntimeError(f"TVscraper fetch failed: {error_msg}") from e


def fetch_market_data_by_date_range(
    ticker: str,
    start_date: str,
    end_date: str,
    interval: str = "1d"
) -> pd.DataFrame:
    """
    Fetch market data using DataFetcher with specific date range.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        interval: Data interval (e.g., '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo')
    
    Returns:
        DataFrame with DatetimeIndex and OHLCV columns
    """
    logger.info(
        f"Loading warehouse data for {ticker}: start_date={start_date}, end_date={end_date}, interval={interval}"
    )
    df, csv_file = _load_warehouse_csv(
        ticker=ticker,
        interval=interval,
        start_date=start_date,
        end_date=end_date,
    )

    if df.empty:
        logger.warning(
            f"No warehouse data for {ticker} between {start_date} and {end_date} "
            f"(interval={interval}). Symbol skipped."
        )
        return _empty_ohlcv_frame()

    source_name = csv_file.name if csv_file else "unknown"
    logger.info(f"Loaded {len(df)} rows for {ticker} from {source_name} for requested date range")
    return df


def validate_indicator_requests(indicators: Dict[str, Optional[Dict[str, Any]]]) -> Tuple[bool, List[str]]:
    """
    Validate indicator requests before processing.
    
    Checks:
    1. Indicator names exist in registry
    2. No duplicate base indicator names (prevents dict key collision)
    3. Parameter values are valid types
    
    Args:
        indicators: Dict mapping indicator name to parameters
    
    Returns:
        Tuple of (is_valid: bool, errors: List[str])
    """
    if not INDICATORS_AVAILABLE:
        return False, ["Indicator calculator not available"]
    
    if not indicators:
        return True, []
    
    errors = []
    available_indicators = registry.list_indicators()
    
    # Check 1: Validate indicator names exist
    for indicator_name in indicators.keys():
        if indicator_name.lower() not in [ind.lower() for ind in available_indicators]:
            errors.append(
                f"Indicator '{indicator_name}' not found in registry. "
                f"Available indicators: {', '.join(available_indicators[:10])}..."
            )
    
    # Check 2: Detect duplicate base names (e.g., multiple 'SMA' requests)
    base_names = [name.split('_')[0].lower() for name in indicators.keys()]
    duplicates = [name for name in set(base_names) if base_names.count(name) > 1]
    if duplicates:
        errors.append(
            f"Duplicate indicator base names detected: {duplicates}. "
            f"Python dicts cannot have duplicate keys. "
            f"Use multi-period format instead: {{'SMA': {{'periods': [20, 50]}}}}"
        )
    
    # Check 3: Validate parameter types
    for indicator_name, params in indicators.items():
        if params is not None and not isinstance(params, dict):
            errors.append(
                f"Parameters for '{indicator_name}' must be a dict or None, got {type(params).__name__}"
            )
    
    is_valid = len(errors) == 0
    return is_valid, errors


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
                   Multi-period format: {'SMA': {'periods': [20, 50]}}
    
    Returns:
        Tuple of (DataFrame with indicators, metadata dict)
    """
    if not INDICATORS_AVAILABLE:
        logger.warning("Indicator calculator not available. Returning original DataFrame.")
        return df.copy(), {'error': 'Indicator calculator not available'}
    
    if not indicators:
        return df.copy(), {}
    
    # Solution 1: Validate indicator requests BEFORE processing
    is_valid, validation_errors = validate_indicator_requests(indicators)
    if not is_valid:
        error_msg = "Indicator validation failed:\n" + "\n".join(f"  - {err}" for err in validation_errors)
        logger.error(error_msg)
        return df.copy(), {'validation_errors': validation_errors}
    
    # Start with copy of original data
    result_df = df.copy()
    metadata = {}
    
    for indicator_name, params in indicators.items():
        try:
            # Use empty dict if params is None
            indicator_params = params if params is not None else {}
            
            # Solution 2: Check if multi-period format is requested
            if 'periods' in indicator_params:
                # Multi-period support: {'SMA': {'periods': [20, 50]}}
                periods = indicator_params['periods']
                if not isinstance(periods, list):
                    periods = [periods]
                
                # Remove 'periods' key and compute for each period
                base_params = {k: v for k, v in indicator_params.items() if k != 'periods'}
                
                for period in periods:
                    period_params = {**base_params, 'timeperiod': period}
                    
                    # Compute indicator for this period
                    indicator_df, indicator_meta = compute_indicator(
                        name=indicator_name,
                        df=df,
                        params=period_params
                    )
                    
                    # Join indicator columns to result
                    result_df = result_df.join(indicator_df, how='left')
                    
                    # Store metadata with period suffix
                    metadata[f"{indicator_name}_{period}"] = indicator_meta
                    
                    logger.info(f"Added indicator: {indicator_name}_{period} with columns {list(indicator_df.columns)}")
            else:
                # Single-period mode (standard)
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


def _stream_data(df: pd.DataFrame, ticker: str) -> Generator[Tuple[datetime, Dict[str, Any], float], None, None]:
    """
    Generator that yields data row-by-row with progress tracking.
    
    This enables sequential processing of market data, simulating real-time
    data feed for more realistic backtesting.
    
    Args:
        df: DataFrame with OHLCV and indicator columns
        ticker: Stock ticker symbol
    
    Yields:
        Tuple of (timestamp, market_data_dict, progress_pct)
        - timestamp: pd.Timestamp of the bar
        - market_data_dict: Dict formatted for strategy consumption
        - progress_pct: Float percentage of completion (0-100)
    
    Example:
        >>> for timestamp, data, progress in _stream_data(df, 'AAPL'):
        ...     print(f"Processing {timestamp} ({progress:.1f}%)")
        ...     strategy.on_bar(timestamp, data)
    """
    total_bars = len(df)
    
    logger.info(f"Streaming {total_bars} bars for {ticker} (sequential mode)")
    
    for i, (timestamp, row) in enumerate(df.iterrows()):
        # Build market data dictionary in format expected by strategies
        market_data = {
            ticker: {
                'open': row.get('Open', row.get('open')),
                'high': row.get('High', row.get('high')),
                'low': row.get('Low', row.get('low')),
                'close': row.get('Close', row.get('close')),
                'volume': row.get('Volume', row.get('volume')),
            }
        }
        
        # Add indicator columns (lowercase keys for consistency)
        for col in df.columns:
            col_lower = col.lower()
            # Skip OHLCV columns (already added)
            if col_lower not in ['open', 'high', 'low', 'close', 'volume']:
                market_data[ticker][col_lower] = row[col]
        
        # Calculate progress percentage
        progress_pct = ((i + 1) / total_bars) * 100
        
        yield timestamp, market_data, progress_pct


def load_market_data(
    ticker: str,
    indicators: Optional[Dict[str, Optional[Dict[str, Any]]]] = None,
    period: str = "1mo",
    interval: str = "1d",
    cache_dir: Optional[Path] = None,
    use_cache: bool = True,
    stream: bool = False
) -> Tuple[pd.DataFrame, Dict[str, Any]] | Generator[Tuple[datetime, Dict[str, Any], float], None, None]:
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
        stream: If True, returns a generator for row-by-row sequential processing (default: False)
    
    Returns:
        If stream=False: Tuple of (DataFrame with OHLCV + indicators, metadata dict)
        If stream=True: Generator yielding (timestamp, market_data_dict, progress_pct)
    
    Example:
        >>> # Batch mode (default)
        >>> df, meta = load_market_data(
        ...     ticker='AAPL',
        ...     indicators={'RSI': {'timeperiod': 14}, 'SMA': {'timeperiod': 20}},
        ...     period='1mo',
        ...     interval='1d'
        ... )
        >>> 
        >>> # Streaming mode (sequential)
        >>> data_stream = load_market_data(
        ...     ticker='AAPL',
        ...     indicators={'RSI': {'timeperiod': 14}},
        ...     period='1mo',
        ...     interval='1d',
        ...     stream=True
        ... )
        >>> for timestamp, market_data, progress_pct in data_stream:
        ...     process_bar(timestamp, market_data)
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
        cache_filename = f"{ticker}_{period}_{interval}_{indicator_str}_warehouse_{timestamp}.parquet"
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
                    # Return generator if streaming mode
                    if stream:
                        return _stream_data(df, ticker)
                    return df, metadata
                except Exception as e:
                    logger.warning(f"Failed to load cache: {e}, fetching fresh data")
    
    # Fetch market data
    logger.info(f"Loading fresh warehouse data for {ticker}")
    df = fetch_market_data(ticker, period, interval)
    
    # Add indicators if requested
    indicator_metadata = {}
    if indicators and not df.empty:
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
        'source': 'warehouse',
        'ticker': ticker,
        'period': period,
        'interval': interval,
        'indicators': indicator_metadata,
        'rows': len(df),
        'columns': list(df.columns),
        'date_range': (
            str(df.index.min()) if not df.empty else None,
            str(df.index.max()) if not df.empty else None,
        ),
        'warehouse_dir': str(WAREHOUSE_DIR),
    }
    
    # Return generator if streaming mode
    if stream:
        return _stream_data(df, ticker)
    
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
        
        print(f"   [OK] Loaded {len(df)} rows")
        print(f"   Columns: {list(df.columns)}")
        print(f"   Date range: {metadata['date_range'][0]} to {metadata['date_range'][1]}")
        print(f"   Source: {metadata['source']}")
        print(f"\n   First 5 rows:")
        print(df.head())
        
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
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
        
        print(f"   [OK] Loaded {len(df)} rows for MSFT")
        print(f"   Columns: {list(df.columns)}")
        print(f"   Date range: {metadata['date_range'][0]} to {metadata['date_range'][1]}")
        
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
