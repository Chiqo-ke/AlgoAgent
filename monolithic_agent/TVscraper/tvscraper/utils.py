"""
Utility functions for TradingView scraper
"""

import re
from typing import Optional, List, Dict
from datetime import datetime


def parse_price(price_str: str) -> Optional[float]:
    """
    Parse a price string to float.
    
    Args:
        price_str: Price string (e.g., "1.18133", "1,234.56")
        
    Returns:
        Float value or None if parsing fails
    """
    if not price_str:
        return None
    
    try:
        # Remove commas and convert to float
        clean_str = price_str.replace(",", "")
        return float(clean_str)
    except (ValueError, AttributeError):
        return None


def parse_change(change_str: str) -> Optional[Dict[str, float]]:
    """
    Parse a change string to extract absolute and percentage changes.
    
    Args:
        change_str: Change string (e.g., "−0.00076 (−0.06%)")
        
    Returns:
        Dict with 'absolute' and 'percent' keys or None
    """
    if not change_str:
        return None
    
    try:
        # Pattern: number (number%)
        pattern = r'([+−-]?\d+\.?\d*)\s*\(([+−-]?\d+\.?\d*)%\)'
        match = re.search(pattern, change_str)
        
        if match:
            absolute = float(match.group(1).replace("−", "-"))
            percent = float(match.group(2).replace("−", "-"))
            return {"absolute": absolute, "percent": percent}
        
        return None
    except (ValueError, AttributeError):
        return None


def format_timeframe(tf_str: str) -> str:
    """
    Normalize timeframe strings.
    
    Args:
        tf_str: Timeframe string in various formats
        
    Returns:
        Normalized timeframe string
    """
    normalize_map = {
        "1min": "1m",
        "3min": "3m",
        "5min": "5m",
        "15min": "15m",
        "30min": "30m",
        "1hour": "1h",
        "4hour": "4h",
        "1day": "1D",
        "1week": "1W",
        "1month": "1M"
    }
    
    return normalize_map.get(tf_str.lower(), tf_str)


def validate_symbol(symbol: str) -> bool:
    """
    Validate a trading symbol format.
    
    Args:
        symbol: Symbol string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not symbol:
        return False
    
    # Basic validation: alphanumeric and some special chars
    pattern = r'^[A-Z0-9/:.-]{1,20}$'
    return bool(re.match(pattern, symbol.upper()))


def extract_ohlc_from_text(text: str) -> Optional[Dict]:
    """
    Extract OHLC values from text content.
    
    Args:
        text: Text containing OHLC data
        
    Returns:
        Dict with O, H, L, C values or None
    """
    try:
        ohlc_pattern = r'O\s*([\d,.]+)\s*H\s*([\d,.]+)\s*L\s*([\d,.]+)\s*C\s*([\d,.]+)'
        match = re.search(ohlc_pattern, text)
        
        if match:
            return {
                "open": parse_price(match.group(1)),
                "high": parse_price(match.group(2)),
                "low": parse_price(match.group(3)),
                "close": parse_price(match.group(4))
            }
        
        return None
    except Exception:
        return None


def timestamp_to_iso(timestamp: int) -> str:
    """
    Convert Unix timestamp to ISO format string.
    
    Args:
        timestamp: Unix timestamp in seconds or milliseconds
        
    Returns:
        ISO format datetime string
    """
    # Handle both seconds and milliseconds
    if timestamp > 10**10:
        timestamp = timestamp / 1000
    
    return datetime.fromtimestamp(timestamp).isoformat()


def create_session_id() -> str:
    """
    Create a unique session ID for tracking scraping sessions.
    
    Returns:
        Session ID string
    """
    return f"tv_session_{int(datetime.now().timestamp())}"


def rate_limit_delay(calls_per_minute: int = 30) -> float:
    """
    Calculate delay between requests to respect rate limits.
    
    Args:
        calls_per_minute: Maximum calls allowed per minute
        
    Returns:
        Delay in seconds
    """
    return 60.0 / calls_per_minute


def clean_indicator_value(value_str: str) -> Optional[float]:
    """
    Clean and parse indicator value strings.
    
    Args:
        value_str: Raw indicator value string
        
    Returns:
        Parsed float value or None
    """
    if not value_str:
        return None
    
    try:
        # Remove units, commas, and extra whitespace
        clean = re.sub(r'[^\d.+-]', '', value_str)
        return float(clean) if clean else None
    except (ValueError, AttributeError):
        return None


def ensure_directory_exists(filepath: str) -> str:
    """
    Ensure the directory for a file path exists.
    
    Args:
        filepath: Path to file
        
    Returns:
        Absolute filepath
    """
    import os
    from pathlib import Path
    
    path = Path(filepath).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


def get_default_export_path(symbol: str, format: str = 'json') -> str:
    """
    Generate default export path for market data.
    
    Args:
        symbol: Trading symbol
        format: File format (json, csv, xlsx)
        
    Returns:
        Default filepath
    """
    import os
    from datetime import datetime
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"tv_{symbol}_{timestamp}.{format}"
    
    # Default to exports folder in current directory
    export_dir = os.path.join(os.getcwd(), 'exports')
    os.makedirs(export_dir, exist_ok=True)
    
    return os.path.join(export_dir, filename)
