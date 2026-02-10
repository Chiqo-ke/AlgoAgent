"""
Multi-Factor Volume-Price Divergence Strategy
An innovative trading strategy that combines:
1. Volume-Price Divergence Analysis
2. Dynamic Support/Resistance Levels
3. Momentum Confirmation with RSI
4. Market Regime Detection
5. Adaptive Stop-Loss and Take-Profit

Strategy Logic:
- Identifies divergences between price and volume trends
- Uses dynamic support/resistance levels for entry timing
- Confirms signals with momentum indicators
- Adapts position sizing based on market volatility
- Implements trailing stops for profit maximization
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

# Import framework components
from core.strategy_framework import BaseStrategy, StrategyParams
try:
    from core.strategy_framework import TechnicalIndicators
except ImportError:
    # If TechnicalIndicators is not available, we'll create basic implementations
    class TechnicalIndicators:
        @staticmethod
        def sma(series, period):
            return series.rolling(window=period).mean()
        
        @staticmethod
        def rsi(series, period):
            delta = series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))
        
        @staticmethod
        def atr(high, low, close, period):
            hl = high - low
            hc = abs(high - close.shift())
            lc = abs(low - close.shift())
            tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
            return tr.rolling(period).mean()

logger = logging.getLogger(__name__)

class VolumePrice_Divergence_Strategy(BaseStrategy):
    """
    Multi-Factor Volume-Price Divergence Strategy
    
    This innovative strategy looks for:
    1. Volume-Price divergences (bullish/bearish)
    2. Dynamic support/resistance breaks
    3. Momentum confirmation with RSI
    4. Adaptive risk management
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        """Initialize strategy with custom parameters"""
        default_params = {
            'volume_ma_period': 20,          # Volume moving average period
            'price_ma_period': 20,           # Price moving average period
            'rsi_period': 14,                # RSI period
            'rsi_oversold': 30,              # RSI oversold threshold
            'rsi_overbought': 70,            # RSI overbought threshold
            'atr_period': 14,                # ATR period for volatility
            'atr_stop_multiplier': 2.0,      # Stop loss ATR multiplier
            'atr_target_multiplier': 3.0,    # Take profit ATR multiplier
            'min_volume_ratio': 1.2,         # Minimum volume ratio for signal
            'lookback_period': 5,            # Lookback for divergence detection
            'support_resistance_period': 50, # Period for S/R calculation
            'min_bars_for_signal': 50        # Minimum bars needed
        }
        
        if params:
            default_params.update(params)
        
        strategy_params = StrategyParams(
            name="VolumePrice_Divergence",
            version="1.0.0",
            description="Multi-factor strategy using volume-price divergence with dynamic S/R",
            params=default_params
        )
        
        super().__init__(strategy_params)
        logger.info(f"Initialized {self.name} strategy with parameters: {self.params.params}")
    
    def calculate_indicators(self, data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """Calculate all technical indicators needed for the strategy"""
        indicators = {}
        
        try:
            # Basic indicators
            indicators['sma'] = TechnicalIndicators.sma(data['close'], self.params.get('price_ma_period'))
            indicators['rsi'] = TechnicalIndicators.rsi(data['close'], self.params.get('rsi_period'))
            indicators['atr'] = TechnicalIndicators.atr(data['high'], data['low'], data['close'], 
                                                       self.params.get('atr_period'))
            
            # Volume indicators
            indicators['volume_sma'] = TechnicalIndicators.sma(data['volume'], 
                                                              self.params.get('volume_ma_period'))
            
            # Volume-Price Trend (VPT)
            indicators['vpt'] = self.calculate_vpt(data)
            
            # Dynamic Support/Resistance
            indicators['support_resistance'] = self.calculate_dynamic_support_resistance(data)
            
            # Price momentum
            indicators['price_momentum'] = self.calculate_price_momentum(data)
            
            # Volume momentum  
            indicators['volume_momentum'] = self.calculate_volume_momentum(data)
            
            # Market regime (trending vs ranging)
            indicators['market_regime'] = self.detect_market_regime(data)
            
        except Exception as e:
            logger.error(f"Error calculating indicators for {symbol}: {e}")
            indicators = {}
        
        return indicators
    
    def calculate_vpt(self, data: pd.DataFrame) -> pd.Series:
        """Calculate Volume Price Trend indicator"""
        try:
            price_change = data['close'].pct_change()
            vpt = (data['volume'] * price_change).cumsum()
            return vpt
        except:
            return pd.Series(index=data.index)
    
    def calculate_dynamic_support_resistance(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calculate dynamic support and resistance levels"""
        try:
            period = self.params.get('support_resistance_period')
            
            # Rolling highs and lows
            resistance = data['high'].rolling(window=period).max()
            support = data['low'].rolling(window=period).min()
            
            # Add some buffer for better signals
            price_range = resistance - support
            resistance_buffer = resistance + (price_range * 0.02)  # 2% buffer
            support_buffer = support - (price_range * 0.02)
            
            return {
                'resistance': resistance_buffer,
                'support': support_buffer,
                'mid_line': (resistance_buffer + support_buffer) / 2
            }
        except:
            return {'resistance': pd.Series(index=data.index), 
                   'support': pd.Series(index=data.index),
                   'mid_line': pd.Series(index=data.index)}
    
    def calculate_price_momentum(self, data: pd.DataFrame) -> pd.Series:
        """Calculate price momentum over lookback period"""
        try:
            lookback = self.params.get('lookback_period')
            return data['close'].pct_change(periods=lookback) * 100
        except:
            return pd.Series(index=data.index)
    
    def calculate_volume_momentum(self, data: pd.DataFrame) -> pd.Series:
        """Calculate volume momentum over lookback period"""
        try:
            lookback = self.params.get('lookback_period')
            volume_sma = TechnicalIndicators.sma(data['volume'], self.params.get('volume_ma_period'))
            return (data['volume'] / volume_sma - 1) * 100  # Volume vs average
        except:
            return pd.Series(index=data.index)
    
    def detect_market_regime(self, data: pd.DataFrame) -> pd.Series:
        """Detect if market is trending or ranging"""
        try:
            # Use ADX-like calculation
            period = 20
            high_low = data['high'] - data['low']
            high_close_prev = abs(data['high'] - data['close'].shift(1))
            low_close_prev = abs(data['low'] - data['close'].shift(1))
            
            true_range = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
            atr = true_range.rolling(period).mean()
            
            # Simple trend strength indicator
            price_range = data['high'].rolling(period).max() - data['low'].rolling(period).min()
            trend_strength = atr / price_range * 100
            
            return trend_strength  # Higher values = more trending
        except:
            return pd.Series(index=data.index)
    
    def detect_divergence(self, historical_data: pd.DataFrame, current_idx: int) -> Dict[str, bool]:
        """Detect volume-price divergences"""
        divergences = {'bullish': False, 'bearish': False}
        
        try:
            if len(historical_data) < self.params.get('min_bars_for_signal'):
                return divergences
            
            lookback = self.params.get('lookback_period')
            if current_idx < lookback:
                return divergences
            
            # Get recent data
            recent_data = historical_data.iloc[current_idx-lookback:current_idx+1]
            
            if len(recent_data) < lookback:
                return divergences
            
            # Price trend (last vs first in period)
            price_trend = recent_data['close'].iloc[-1] - recent_data['close'].iloc[0]
            
            # Volume trend (recent average vs older average)
            mid_point = len(recent_data) // 2
            recent_volume_avg = recent_data['volume'].iloc[mid_point:].mean()
            older_volume_avg = recent_data['volume'].iloc[:mid_point].mean()
            volume_trend = recent_volume_avg - older_volume_avg
            
            # VPT trend
            vpt_trend = recent_data['vpt'].iloc[-1] - recent_data['vpt'].iloc[0] if 'vpt' in recent_data.columns else 0
            
            # Bullish divergence: Price down, but volume/VPT up
            if price_trend < 0 and (volume_trend > 0 or vpt_trend > 0):
                divergences['bullish'] = True
            
            # Bearish divergence: Price up, but volume/VPT down  
            elif price_trend > 0 and (volume_trend < 0 or vpt_trend < 0):
                divergences['bearish'] = True
            
        except Exception as e:
            logger.error(f"Error detecting divergence: {e}")
        
        return divergences
    
    def generate_signal(self, engine, current_data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """Generate trading signals based on multi-factor analysis"""
        if symbol not in engine.market_data or symbol not in current_data:
            return {}
        
        try:
            # Get historical data up to current time
            historical_data = engine.market_data[symbol].loc[:engine.current_time].copy()
            
            if len(historical_data) < self.params.get('min_bars_for_signal'):
                return {}
            
            # Calculate indicators for the historical data
            indicators = self.calculate_indicators(historical_data, symbol)
            
            # Add indicators to historical data for easier access
            for key, value in indicators.items():
                if isinstance(value, pd.Series):
                    historical_data[key] = value
                elif isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        historical_data[f"{key}_{sub_key}"] = sub_value
            
            current_bar = current_data[symbol]
            current_price = current_bar['close']
            current_volume = current_bar['volume']
            current_idx = len(historical_data) - 1
            
            # Get current indicator values
            try:
                current_rsi = historical_data['rsi'].iloc[-1] if not pd.isna(historical_data['rsi'].iloc[-1]) else 50
                current_atr = historical_data['atr'].iloc[-1] if not pd.isna(historical_data['atr'].iloc[-1]) else current_price * 0.02
                current_support = historical_data['support_resistance_support'].iloc[-1] if 'support_resistance_support' in historical_data.columns else current_price * 0.95
                current_resistance = historical_data['support_resistance_resistance'].iloc[-1] if 'support_resistance_resistance' in historical_data.columns else current_price * 1.05
                volume_ratio = current_volume / historical_data['volume_sma'].iloc[-1] if not pd.isna(historical_data['volume_sma'].iloc[-1]) else 1.0
            except (IndexError, KeyError):
                return {}
            
            # Detect divergences
            divergences = self.detect_divergence(historical_data, current_idx)
            
            # Market regime
            try:
                trend_strength = historical_data['market_regime'].iloc[-1] if not pd.isna(historical_data['market_regime'].iloc[-1]) else 50
            except:
                trend_strength = 50
            
            # Entry conditions
            min_volume_ratio = self.params.get('min_volume_ratio')
            
            # LONG SIGNAL
            if symbol not in engine.positions:
                # Bullish conditions
                bullish_divergence = divergences['bullish']
                oversold_rsi = current_rsi < self.params.get('rsi_oversold')
                price_near_support = current_price <= current_support * 1.02  # Within 2% of support
                volume_confirmation = volume_ratio >= min_volume_ratio
                trending_market = trend_strength > 30  # Somewhat trending market
                
                if bullish_divergence and oversold_rsi and price_near_support and volume_confirmation:
                    stop_loss = current_price - (current_atr * self.params.get('atr_stop_multiplier'))
                    take_profit = current_price + (current_atr * self.params.get('atr_target_multiplier'))
                    
                    return {
                        'action': 'buy',
                        'stop_loss': max(stop_loss, current_support * 0.98),  # Don't set stop too far below support
                        'take_profit': min(take_profit, current_resistance * 0.98),  # Target below resistance
                        'confidence': min(100, 50 + (volume_ratio * 10) + (40 - current_rsi)),  # Higher volume and more oversold = higher confidence
                        'reason': f"Bullish divergence + oversold RSI({current_rsi:.1f}) + support({current_support:.2f}) + volume({volume_ratio:.2f}x)"
                    }
            
            # EXIT CONDITIONS (if we have a position)
            else:
                position = engine.positions[symbol]
                entry_price = position.entry_price
                current_pnl_pct = ((current_price - entry_price) / entry_price) * 100
                
                # Bearish conditions for exit
                bearish_divergence = divergences['bearish']
                overbought_rsi = current_rsi > self.params.get('rsi_overbought')
                price_near_resistance = current_price >= current_resistance * 0.98
                
                # Exit on bearish signals or profit target
                if bearish_divergence or (overbought_rsi and price_near_resistance) or current_pnl_pct > 15:
                    return {
                        'action': 'close',
                        'reason': f"Exit: bearish_div={bearish_divergence}, overbought_rsi={overbought_rsi}({current_rsi:.1f}), resistance={price_near_resistance}, pnl={current_pnl_pct:.1f}%"
                    }
                
                # Trailing stop (move stop loss up if in profit)
                elif current_pnl_pct > 5:
                    new_stop = current_price - (current_atr * 1.5)  # Tighter trailing stop
                    if new_stop > position.stop_loss:
                        return {
                            'action': 'modify_stop',
                            'new_stop_loss': new_stop,
                            'reason': f"Trailing stop: profit={current_pnl_pct:.1f}%"
                        }
        
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}")
        
        return {}
    
    def prepare_data(self, data: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Prepare data with all indicators"""
        try:
            # Add all indicators to the data
            indicators = self.calculate_indicators(data, symbol)
            
            for key, value in indicators.items():
                if isinstance(value, pd.Series):
                    data[key] = value
                elif isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        data[f"{key}_{sub_key}"] = sub_value
            
            logger.info(f"Data prepared for {symbol} with {len(data)} rows")
            return data
            
        except Exception as e:
            logger.error(f"Error preparing data for {symbol}: {e}")
            return data


def create_volume_price_divergence_strategy(params: Dict[str, Any] = None) -> VolumePrice_Divergence_Strategy:
    """
    Factory function to create VolumePrice_Divergence_Strategy
    
    Args:
        params: Optional parameters to override defaults
        
    Returns:
        Configured strategy instance
    """
    return VolumePrice_Divergence_Strategy(params)


# Example usage and parameter sets for optimization
OPTIMIZATION_PARAMETERS = {
    'volume_ma_period': {'min': 10, 'max': 30, 'step': 5},
    'rsi_period': {'min': 10, 'max': 20, 'step': 2}, 
    'rsi_oversold': {'min': 25, 'max': 35, 'step': 5},
    'rsi_overbought': {'min': 65, 'max': 75, 'step': 5},
    'atr_stop_multiplier': {'min': 1.5, 'max': 3.0, 'step': 0.5, 'type': 'float'},
    'atr_target_multiplier': {'min': 2.0, 'max': 4.0, 'step': 0.5, 'type': 'float'},
    'min_volume_ratio': {'min': 1.0, 'max': 2.0, 'step': 0.2, 'type': 'float'},
    'lookback_period': {'min': 3, 'max': 8, 'step': 1}
}

# Conservative parameters for low-risk trading
CONSERVATIVE_PARAMS = {
    'atr_stop_multiplier': 1.5,
    'atr_target_multiplier': 2.0,
    'min_volume_ratio': 1.5,
    'rsi_oversold': 25,
    'rsi_overbought': 75
}

# Aggressive parameters for higher returns (higher risk)
AGGRESSIVE_PARAMS = {
    'atr_stop_multiplier': 2.5,
    'atr_target_multiplier': 4.0,
    'min_volume_ratio': 1.0,
    'rsi_oversold': 35,
    'rsi_overbought': 65
}

if __name__ == "__main__":
    # Test strategy creation
    print("Creating VolumePrice_Divergence_Strategy...")
    strategy = create_volume_price_divergence_strategy()
    print(f"Strategy created: {strategy.name}")
    print(f"Parameters: {strategy.params.params}")