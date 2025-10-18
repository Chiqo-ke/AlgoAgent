"""
MT5 Connector Utility
=====================

Utilities for MetaTrader5 Python integration:
- Data synchronization between Python and MT5
- Symbol information and specifications
- Historical data fetching
- Connection management

References:
- MT5 Python API: https://www.mql5.com/en/docs/python_metatrader5
- copy_rates_range: https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesrange_py
- symbol_info: https://www.mql5.com/en/docs/python_metatrader5/mt5symbolinfo_py

Installation:
    pip install MetaTrader5

Last updated: 2025-10-18
Version: 1.0.0
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
import pandas as pd
import logging
from pathlib import Path

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    logging.warning("MetaTrader5 module not installed. Install with: pip install MetaTrader5")


logger = logging.getLogger(__name__)


class MT5Connector:
    """
    MetaTrader5 Python connector
    
    Provides utilities for:
    - Connecting to MT5 terminal
    - Fetching historical data
    - Getting symbol specifications
    - Validating data consistency with Python backtests
    """
    
    def __init__(
        self,
        terminal_path: Optional[str] = None,
        portable: bool = False,
        timeout: int = 60000
    ):
        """
        Initialize MT5 connector
        
        Args:
            terminal_path: Path to MT5 terminal executable (auto-detect if None)
            portable: Use portable mode
            timeout: Connection timeout in milliseconds
        """
        if not MT5_AVAILABLE:
            raise ImportError(
                "MetaTrader5 module not installed. "
                "Install with: pip install MetaTrader5"
            )
        
        self.terminal_path = terminal_path
        self.portable = portable
        self.timeout = timeout
        self.connected = False
        
        logger.info("MT5Connector initialized")
    
    def connect(self, login: Optional[int] = None, password: Optional[str] = None, 
                server: Optional[str] = None) -> bool:
        """
        Connect to MT5 terminal
        
        Args:
            login: Trading account login (None = use current)
            password: Trading account password
            server: Broker server name
        
        Returns:
            True if connected successfully
        """
        if not MT5_AVAILABLE:
            logger.error("MT5 module not available")
            return False
        
        # Initialize MT5 connection
        if self.terminal_path:
            if not mt5.initialize(
                path=self.terminal_path,
                portable=self.portable,
                timeout=self.timeout
            ):
                error = mt5.last_error()
                logger.error(f"MT5 initialize failed: {error}")
                return False
        else:
            if not mt5.initialize():
                error = mt5.last_error()
                logger.error(f"MT5 initialize failed: {error}")
                return False
        
        # Login if credentials provided
        if login and password and server:
            if not mt5.login(login, password, server):
                error = mt5.last_error()
                logger.error(f"MT5 login failed: {error}")
                mt5.shutdown()
                return False
        
        self.connected = True
        
        # Get terminal info
        terminal_info = mt5.terminal_info()
        if terminal_info:
            logger.info(
                f"Connected to MT5: {terminal_info.company} | "
                f"Build {terminal_info.build} | "
                f"Path: {terminal_info.path}"
            )
        
        # Get version
        version = mt5.version()
        if version:
            logger.info(f"MT5 Version: {version[0]}.{version[1]} (build {version[2]})")
        
        return True
    
    def disconnect(self):
        """Disconnect from MT5 terminal"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            logger.info("Disconnected from MT5")
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get symbol specifications
        
        Args:
            symbol: Symbol name (e.g., "XAUUSD")
        
        Returns:
            Dictionary with symbol info, or None if not found
        """
        if not self.connected:
            logger.error("Not connected to MT5")
            return None
        
        symbol_info = mt5.symbol_info(symbol)
        
        if symbol_info is None:
            logger.error(f"Symbol {symbol} not found")
            return None
        
        return {
            "name": symbol_info.name,
            "description": symbol_info.description,
            "point": symbol_info.point,
            "digits": symbol_info.digits,
            "spread": symbol_info.spread,
            "trade_contract_size": symbol_info.trade_contract_size,
            "volume_min": symbol_info.volume_min,
            "volume_max": symbol_info.volume_max,
            "volume_step": symbol_info.volume_step,
            "currency_base": symbol_info.currency_base,
            "currency_profit": symbol_info.currency_profit,
            "currency_margin": symbol_info.currency_margin,
            "trade_mode": symbol_info.trade_mode,
        }
    
    def get_lot_size(self, symbol: str) -> float:
        """
        Get lot size (contract size) for a symbol
        
        Args:
            symbol: Symbol name
        
        Returns:
            Contract size (shares/oz/units per lot)
        """
        info = self.get_symbol_info(symbol)
        if info:
            return info["trade_contract_size"]
        return 100000.0  # Default for forex
    
    def get_historical_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical OHLCV data from MT5
        
        Args:
            symbol: Symbol name (e.g., "XAUUSD")
            timeframe: Timeframe (M1, M5, M15, M30, H1, H4, D1, W1, MN1)
            start_date: Start date
            end_date: End date
        
        Returns:
            DataFrame with columns: time, open, high, low, close, volume
            or None if fetch failed
        """
        if not self.connected:
            logger.error("Not connected to MT5")
            return None
        
        # Convert timeframe string to MT5 constant
        timeframe_map = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "M30": mt5.TIMEFRAME_M30,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1,
            "W1": mt5.TIMEFRAME_W1,
            "MN1": mt5.TIMEFRAME_MN1,
        }
        
        mt5_timeframe = timeframe_map.get(timeframe)
        if mt5_timeframe is None:
            logger.error(f"Invalid timeframe: {timeframe}")
            return None
        
        # Fetch rates
        rates = mt5.copy_rates_range(symbol, mt5_timeframe, start_date, end_date)
        
        if rates is None or len(rates) == 0:
            error = mt5.last_error()
            logger.error(f"Failed to fetch data: {error}")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(rates)
        
        # Convert time to datetime
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        logger.info(
            f"Fetched {len(df)} bars for {symbol} {timeframe} "
            f"from {start_date} to {end_date}"
        )
        
        return df
    
    def save_historical_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        output_path: Path
    ) -> bool:
        """
        Fetch and save historical data to CSV
        
        Args:
            symbol: Symbol name
            timeframe: Timeframe
            start_date: Start date
            end_date: End date
            output_path: Path to save CSV file
        
        Returns:
            True if successful
        """
        df = self.get_historical_data(symbol, timeframe, start_date, end_date)
        
        if df is None:
            return False
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(df)} bars to {output_path}")
        
        return True
    
    def compare_data_with_python(
        self,
        symbol: str,
        timeframe: str,
        python_data: pd.DataFrame,
        tolerance: float = 0.0001
    ) -> Dict[str, Any]:
        """
        Compare Python data with MT5 data for consistency
        
        Args:
            symbol: Symbol name
            timeframe: Timeframe
            python_data: DataFrame with Python data (must have 'time', 'open', 'high', 'low', 'close')
            tolerance: Price difference tolerance (relative)
        
        Returns:
            Dictionary with comparison results
        """
        if not self.connected:
            logger.error("Not connected to MT5")
            return {"error": "Not connected to MT5"}
        
        # Get date range from Python data
        if 'time' not in python_data.columns and 'timestamp' in python_data.columns:
            python_data = python_data.rename(columns={'timestamp': 'time'})
        
        start_date = pd.to_datetime(python_data['time'].min())
        end_date = pd.to_datetime(python_data['time'].max())
        
        # Fetch MT5 data
        mt5_data = self.get_historical_data(symbol, timeframe, start_date, end_date)
        
        if mt5_data is None:
            return {"error": "Failed to fetch MT5 data"}
        
        # Merge on timestamp
        python_data = python_data.copy()
        python_data['time'] = pd.to_datetime(python_data['time'])
        
        merged = pd.merge(
            python_data[['time', 'open', 'high', 'low', 'close']],
            mt5_data[['time', 'open', 'high', 'low', 'close']],
            on='time',
            how='outer',
            suffixes=('_python', '_mt5')
        )
        
        # Calculate differences
        price_cols = ['open', 'high', 'low', 'close']
        mismatches = 0
        max_diff = 0.0
        
        for col in price_cols:
            python_col = f"{col}_python"
            mt5_col = f"{col}_mt5"
            
            if python_col in merged.columns and mt5_col in merged.columns:
                # Calculate relative difference
                diff = abs(merged[python_col] - merged[mt5_col]) / merged[mt5_col]
                merged[f"{col}_diff"] = diff
                
                # Count mismatches
                mismatches += (diff > tolerance).sum()
                max_diff = max(max_diff, diff.max())
        
        result = {
            "python_bars": len(python_data),
            "mt5_bars": len(mt5_data),
            "matched_bars": len(merged[merged['open_python'].notna() & merged['open_mt5'].notna()]),
            "python_only_bars": len(merged[merged['open_python'].notna() & merged['open_mt5'].isna()]),
            "mt5_only_bars": len(merged[merged['open_python'].isna() & merged['open_mt5'].notna()]),
            "price_mismatches": int(mismatches),
            "max_relative_diff": float(max_diff),
            "tolerance": tolerance,
            "data_consistent": mismatches == 0 and len(python_data) == len(mt5_data)
        }
        
        logger.info(
            f"Data comparison: {result['matched_bars']} matched, "
            f"{result['price_mismatches']} mismatches (tolerance={tolerance})"
        )
        
        return result
    
    def get_mt5_files_path(self) -> Optional[Path]:
        """
        Get the MT5 Files directory path
        
        This is where MQL5 EAs can read/write files.
        
        Returns:
            Path to MT5 Files directory, or None if not connected
        """
        if not self.connected:
            logger.error("Not connected to MT5")
            return None
        
        terminal_info = mt5.terminal_info()
        if terminal_info:
            # MT5 Files directory is at: Terminal_Path/MQL5/Files/
            terminal_path = Path(terminal_info.data_path)
            files_path = terminal_path / "MQL5" / "Files"
            return files_path
        
        return None
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


def get_mt5_timeframe_minutes(timeframe: str) -> int:
    """
    Convert MT5 timeframe string to minutes
    
    Args:
        timeframe: Timeframe string (M1, H1, D1, etc.)
    
    Returns:
        Number of minutes in timeframe
    """
    timeframe_minutes = {
        "M1": 1,
        "M5": 5,
        "M15": 15,
        "M30": 30,
        "H1": 60,
        "H4": 240,
        "D1": 1440,
        "W1": 10080,
        "MN1": 43200,  # Approximate
    }
    return timeframe_minutes.get(timeframe, 60)


def align_timestamp_to_mt5(timestamp: datetime, timeframe: str) -> datetime:
    """
    Align a timestamp to MT5 bar open time
    
    Args:
        timestamp: Input timestamp
        timeframe: MT5 timeframe
    
    Returns:
        Aligned timestamp
    """
    minutes = get_mt5_timeframe_minutes(timeframe)
    
    # Round down to nearest bar open
    total_minutes = timestamp.hour * 60 + timestamp.minute
    aligned_minutes = (total_minutes // minutes) * minutes
    
    aligned = timestamp.replace(
        hour=aligned_minutes // 60,
        minute=aligned_minutes % 60,
        second=0,
        microsecond=0
    )
    
    return aligned
