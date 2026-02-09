import pandas as pd
import numpy as np
from typing import Optional, Tuple, Dict, Any
import logging

class TechnicalIndicators:
    """Technical indicators for the trading strategy"""
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index (RSI)
        
        Args:
            prices: Price series (typically close prices)
            period: RSI calculation period
            
        Returns:
            RSI values as pandas Series
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_sma(prices: pd.Series, period: int = 20) -> pd.Series:
        """
        Calculate Simple Moving Average (SMA)
        
        Args:
            prices: Price series
            period: SMA calculation period
            
        Returns:
            SMA values as pandas Series
        """
        return prices.rolling(window=period).mean()
    
    @staticmethod
    def calculate_ema(prices: pd.Series, period: int = 20) -> pd.Series:
        """
        Calculate Exponential Moving Average (EMA)
        
        Args:
            prices: Price series
            period: EMA calculation period
            
        Returns:
            EMA values as pandas Series
        """
        return prices.ewm(span=period).mean()
    
    @staticmethod
    def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range (ATR)
        
        Args:
            high: High price series
            low: Low price series
            close: Close price series
            period: ATR calculation period
            
        Returns:
            ATR values as pandas Series
        """
        high_low = high - low
        high_close_prev = np.abs(high - close.shift())
        low_close_prev = np.abs(low - close.shift())
        
        true_range = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        return atr
    
    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: float = 2) -> Dict[str, pd.Series]:
        """
        Calculate Bollinger Bands
        
        Args:
            prices: Price series
            period: Moving average period
            std_dev: Standard deviation multiplier
            
        Returns:
            Dictionary with upper, middle, and lower bands
        """
        sma = TechnicalIndicators.calculate_sma(prices, period)
        std = prices.rolling(window=period).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return {
            'upper': upper_band,
            'middle': sma,
            'lower': lower_band
        }

class SignalGenerator:
    """Generate trading signals based on technical indicators"""
    
    def __init__(self, rsi_period: int = 14, sma_period: int = 20, 
                 rsi_long_threshold: int = 50, rsi_short_threshold: int = 50):
        self.rsi_period = rsi_period
        self.sma_period = sma_period
        self.rsi_long_threshold = rsi_long_threshold
        self.rsi_short_threshold = rsi_short_threshold
        self.logger = logging.getLogger(__name__)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on RSI and SMA
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with signals and indicators
        """
        df = data.copy()
        
        # Calculate indicators
        df['rsi'] = TechnicalIndicators.calculate_rsi(df['close'], self.rsi_period)
        df['sma20'] = TechnicalIndicators.calculate_sma(df['close'], self.sma_period)
        df['atr'] = TechnicalIndicators.calculate_atr(df['high'], df['low'], df['close'])
        
        # Initialize signal columns
        df['signal'] = 0  # 1 for long, -1 for short, 0 for no signal
        df['position'] = 0  # Current position
        
        # Generate signals
        for i in range(max(self.rsi_period, self.sma_period), len(df)):
            current_rsi = df['rsi'].iloc[i]
            current_price = df['close'].iloc[i]
            current_sma = df['sma20'].iloc[i]
            
            # Long signal: RSI > 50 and price > SMA20
            if (current_rsi > self.rsi_long_threshold and 
                current_price > current_sma and 
                df['position'].iloc[i-1] != 1):
                df.loc[df.index[i], 'signal'] = 1
                
            # Short signal: RSI < 50 and price < SMA20
            elif (current_rsi < self.rsi_short_threshold and 
                  current_price < current_sma and 
                  df['position'].iloc[i-1] != -1):
                df.loc[df.index[i], 'signal'] = -1
        
        # Calculate positions
        df['position'] = df['signal'].replace(0, method='ffill').fillna(0)
        
        # Add entry and exit signals
        df['entry'] = (df['position'] != df['position'].shift()).astype(int)
        df['exit'] = ((df['position'].shift() != 0) & (df['position'] == 0)).astype(int)
        
        self.logger.info(f"Generated {df['signal'].abs().sum()} signals")
        return df
    
    def get_signal_strength(self, rsi: float, price: float, sma: float) -> float:
        """
        Calculate signal strength (0-1)
        
        Args:
            rsi: Current RSI value
            price: Current price
            sma: Current SMA value
            
        Returns:
            Signal strength between 0 and 1
        """
        if price > sma and rsi > self.rsi_long_threshold:
            # Long signal strength
            rsi_strength = min((rsi - self.rsi_long_threshold) / (100 - self.rsi_long_threshold), 1)
            price_strength = min((price - sma) / sma, 0.1) * 10  # Cap at 10%
            return (rsi_strength + price_strength) / 2
        
        elif price < sma and rsi < self.rsi_short_threshold:
            # Short signal strength
            rsi_strength = min((self.rsi_short_threshold - rsi) / self.rsi_short_threshold, 1)
            price_strength = min((sma - price) / sma, 0.1) * 10  # Cap at 10%
            return (rsi_strength + price_strength) / 2
        
        return 0.0