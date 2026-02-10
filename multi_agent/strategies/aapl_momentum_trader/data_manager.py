import pandas as pd
import numpy as np
from typing import Optional, Union
import logging
from abc import ABC, abstractmethod

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    print("MetaTrader5 not available. Install with: pip install MetaTrader5")

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("yfinance not available. Install with: pip install yfinance")

class DataProvider(ABC):
    """Abstract base class for data providers"""
    
    @abstractmethod
    def get_historical_data(self, symbol: str, timeframe: str, 
                          start_date: str, end_date: str) -> pd.DataFrame:
        pass
    
    @abstractmethod
    def get_live_data(self, symbol: str, timeframe: str, bars: int) -> pd.DataFrame:
        pass

class MT5DataProvider(DataProvider):
    """MetaTrader 5 data provider"""
    
    def __init__(self, server: str, login: int, password: str):
        self.server = server
        self.login = login
        self.password = password
        self.connected = False
        self.logger = logging.getLogger(__name__)
        
        if not MT5_AVAILABLE:
            raise ImportError("MetaTrader5 module not available")
    
    def connect(self) -> bool:
        """Connect to MT5 terminal"""
        if not mt5.initialize():
            self.logger.error(f"MT5 initialization failed: {mt5.last_error()}")
            return False
        
        if not mt5.login(self.login, password=self.password, server=self.server):
            self.logger.error(f"MT5 login failed: {mt5.last_error()}")
            mt5.shutdown()
            return False
        
        self.connected = True
        self.logger.info(f"Connected to MT5: {mt5.account_info()}")
        return True
    
    def disconnect(self):
        """Disconnect from MT5"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            self.logger.info("Disconnected from MT5")
    
    def _get_mt5_timeframe(self, timeframe: str) -> int:
        """Convert string timeframe to MT5 timeframe constant"""
        timeframe_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1,
            'W1': mt5.TIMEFRAME_W1,
            'MN1': mt5.TIMEFRAME_MN1
        }
        return timeframe_map.get(timeframe.upper(), mt5.TIMEFRAME_H1)
    
    def get_historical_data(self, symbol: str, timeframe: str, 
                          start_date: str, end_date: str) -> pd.DataFrame:
        """Get historical data from MT5"""
        if not self.connected:
            if not self.connect():
                raise ConnectionError("Failed to connect to MT5")
        
        mt5_timeframe = self._get_mt5_timeframe(timeframe)
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        
        rates = mt5.copy_rates_range(symbol, mt5_timeframe, start_date, end_date)
        
        if rates is None or len(rates) == 0:
            self.logger.error(f"No data received for {symbol}")
            return pd.DataFrame()
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        df.rename(columns={
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'tick_volume': 'volume'
        }, inplace=True)
        
        self.logger.info(f"Retrieved {len(df)} bars for {symbol}")
        return df
    
    def get_live_data(self, symbol: str, timeframe: str, bars: int = 100) -> pd.DataFrame:
        """Get live data from MT5"""
        if not self.connected:
            if not self.connect():
                raise ConnectionError("Failed to connect to MT5")
        
        mt5_timeframe = self._get_mt5_timeframe(timeframe)
        rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, bars)
        
        if rates is None or len(rates) == 0:
            self.logger.error(f"No live data received for {symbol}")
            return pd.DataFrame()
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        df.rename(columns={
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'tick_volume': 'volume'
        }, inplace=True)
        
        return df
    
    def get_symbol_info(self, symbol: str) -> dict:
        """Get symbol information"""
        if not self.connected:
            if not self.connect():
                raise ConnectionError("Failed to connect to MT5")
        
        info = mt5.symbol_info(symbol)
        if info is None:
            return {}
        
        return {
            'symbol': info.name,
            'point': info.point,
            'digits': info.digits,
            'spread': info.spread,
            'trade_tick_value': info.trade_tick_value,
            'trade_tick_size': info.trade_tick_size,
            'minimum_volume': info.volume_min,
            'maximum_volume': info.volume_max,
            'volume_step': info.volume_step
        }

class YFinanceDataProvider(DataProvider):
    """Yahoo Finance data provider for backtesting"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        if not YFINANCE_AVAILABLE:
            raise ImportError("yfinance module not available")
    
    def _convert_timeframe(self, timeframe: str) -> str:
        """Convert timeframe to yfinance format"""
        timeframe_map = {
            'M1': '1m',
            'M5': '5m',
            'M15': '15m',
            'M30': '30m',
            'H1': '1h',
            'H4': '4h',
            'D1': '1d',
            'W1': '1wk',
            'MN1': '1mo'
        }
        return timeframe_map.get(timeframe.upper(), '1h')
    
    def get_historical_data(self, symbol: str, timeframe: str, 
                          start_date: str, end_date: str) -> pd.DataFrame:
        """Get historical data from Yahoo Finance"""
        try:
            yf_timeframe = self._convert_timeframe(timeframe)
            ticker = yf.Ticker(symbol)
            
            df = ticker.history(
                start=start_date,
                end=end_date,
                interval=yf_timeframe,
                auto_adjust=True,
                prepost=False
            )
            
            if df.empty:
                self.logger.error(f"No data received for {symbol}")
                return pd.DataFrame()
            
            # Standardize column names
            df.columns = [col.lower() for col in df.columns]
            df = df[['open', 'high', 'low', 'close', 'volume']]
            
            self.logger.info(f"Retrieved {len(df)} bars for {symbol} from Yahoo Finance")
            return df
            
        except Exception as e:
            self.logger.error(f"Error fetching data from Yahoo Finance: {e}")
            return pd.DataFrame()
    
    def get_live_data(self, symbol: str, timeframe: str, bars: int = 100) -> pd.DataFrame:
        """Get recent data from Yahoo Finance (simulates live data)"""
        try:
            yf_timeframe = self._convert_timeframe(timeframe)
            ticker = yf.Ticker(symbol)
            
            # Get last 30 days of data
            df = ticker.history(
                period="30d",
                interval=yf_timeframe,
                auto_adjust=True,
                prepost=False
            )
            
            if df.empty:
                self.logger.error(f"No live data received for {symbol}")
                return pd.DataFrame()
            
            # Return last 'bars' number of bars
            df = df.tail(bars)
            df.columns = [col.lower() for col in df.columns]
            df = df[['open', 'high', 'low', 'close', 'volume']]
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error fetching live data from Yahoo Finance: {e}")
            return pd.DataFrame()

class DataManager:
    """Unified data manager for different data sources"""
    
    def __init__(self, provider_type: str = "yfinance", **provider_config):
        self.provider_type = provider_type
        self.provider = None
        self.logger = logging.getLogger(__name__)
        
        if provider_type.lower() == "mt5":
            self.provider = MT5DataProvider(**provider_config)
        elif provider_type.lower() == "yfinance":
            self.provider = YFinanceDataProvider()
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")
    
    def get_data(self, symbol: str, timeframe: str, start_date: str, 
                 end_date: str = None, live: bool = False, bars: int = 100) -> pd.DataFrame:
        """
        Get market data
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe (M1, M5, M15, M30, H1, H4, D1, W1, MN1)
            start_date: Start date for historical data
            end_date: End date for historical data (None for live data)
            live: Whether to get live data
            bars: Number of bars for live data
            
        Returns:
            DataFrame with OHLCV data
        """
        if live or end_date is None:
            return self.provider.get_live_data(symbol, timeframe, bars)
        else:
            return self.provider.get_historical_data(symbol, timeframe, start_date, end_date)
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """Validate data quality"""
        if data.empty:
            self.logger.warning("Data is empty")
            return False
        
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in data.columns for col in required_columns):
            self.logger.warning(f"Missing required columns. Required: {required_columns}")
            return False
        
        # Check for missing values
        if data[required_columns].isnull().sum().sum() > 0:
            self.logger.warning("Data contains missing values")
            return False
        
        # Check for invalid prices
        if (data['high'] < data['low']).any():
            self.logger.warning("Data contains invalid high/low prices")
            return False
        
        if ((data['close'] > data['high']) | (data['close'] < data['low'])).any():
            self.logger.warning("Data contains invalid close prices")
            return False
        
        if ((data['open'] > data['high']) | (data['open'] < data['low'])).any():
            self.logger.warning("Data contains invalid open prices")
            return False
        
        return True
    
    def cleanup_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean and prepare data"""
        df = data.copy()
        
        # Remove duplicates
        df = df[~df.index.duplicated(keep='first')]
        
        # Sort by time
        df = df.sort_index()
        
        # Forward fill missing values (conservative approach)
        df = df.fillna(method='ffill')
        
        # Remove any remaining NaN rows
        df = df.dropna()
        
        return df