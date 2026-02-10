import pandas as pd
import numpy as np
from typing import Optional, Tuple, Dict, Any, List
import logging
from datetime import datetime, timedelta

class BreakoutIndicators:
    """Advanced technical indicators for the Momentum Breakout Pro strategy"""
    
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
        return prices.ewm(span=period, adjust=False).mean()
    
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
        atr = true_range.ewm(span=period, adjust=False).mean()
        return atr
    
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
        gain = (delta.where(delta > 0, 0)).ewm(span=period, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(span=period, adjust=False).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
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
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return {
            'upper': upper_band,
            'middle': sma,
            'lower': lower_band,
            'width': (upper_band - lower_band) / sma,  # Bollinger Band Width
            'percent_b': (prices - lower_band) / (upper_band - lower_band)  # %B
        }
    
    @staticmethod
    def calculate_volume_indicators(volume: pd.Series, period_long: int = 20, period_short: int = 5) -> Dict[str, pd.Series]:
        """
        Calculate volume-based indicators
        
        Args:
            volume: Volume series
            period_long: Long-term average period
            period_short: Short-term average period
            
        Returns:
            Dictionary with volume indicators
        """
        volume_sma_long = volume.rolling(window=period_long).mean()
        volume_sma_short = volume.rolling(window=period_short).mean()
        
        return {
            'sma_long': volume_sma_long,
            'sma_short': volume_sma_short,
            'ratio_to_avg': volume / volume_sma_long,
            'surge_ratio': volume / volume_sma_short,
        }
    
    @staticmethod
    def calculate_breakout_levels(high: pd.Series, low: pd.Series, period: int = 20) -> Dict[str, pd.Series]:
        """
        Calculate breakout levels (highest high and lowest low)
        
        Args:
            high: High price series
            low: Low price series
            period: Lookback period
            
        Returns:
            Dictionary with breakout levels
        """
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()
        
        return {
            'resistance': highest_high,
            'support': lowest_low,
            'range': highest_high - lowest_low
        }

class BreakoutPatternDetector:
    """Pattern detection for breakout signals"""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def detect_trend_bias(self, data_4h: pd.DataFrame) -> int:
        """
        Determine trend bias from 4H timeframe
        
        Args:
            data_4h: 4H OHLCV data
            
        Returns:
            1 for bullish, -1 for bearish, 0 for neutral
        """
        if len(data_4h) < self.config['ema_trend_period']:
            return 0
        
        ema_50 = BreakoutIndicators.calculate_ema(data_4h['close'], self.config['ema_trend_period'])
        current_price = data_4h['close'].iloc[-1]
        current_ema = ema_50.iloc[-1]
        
        if current_price > current_ema:
            return 1  # Bullish bias
        elif current_price < current_ema:
            return -1  # Bearish bias
        else:
            return 0  # Neutral
    
    def detect_breakout_pattern(self, data_15m: pd.DataFrame, direction: int) -> Dict[str, Any]:
        """
        Detect breakout pattern on 15M timeframe
        
        Args:
            data_15m: 15M OHLCV data
            direction: 1 for long, -1 for short
            
        Returns:
            Dictionary with pattern detection results
        """
        if len(data_15m) < self.config['breakout_period'] + 1:
            return {'valid': False, 'reason': 'Insufficient data'}
        
        # Calculate breakout levels
        breakout_levels = BreakoutIndicators.calculate_breakout_levels(
            data_15m['high'], data_15m['low'], self.config['breakout_period']
        )
        
        current_candle = data_15m.iloc[-1]
        previous_resistance = breakout_levels['resistance'].iloc[-2]
        previous_support = breakout_levels['support'].iloc[-2]
        
        pattern_result = {
            'valid': False,
            'breakout_level': 0,
            'candle_quality': 0,
            'gap_size': 0,
            'reason': ''
        }
        
        if direction == 1:  # Long breakout
            if current_candle['close'] > previous_resistance:
                # Check candle quality (close in top 75% of range)
                candle_range = current_candle['high'] - current_candle['low']
                close_position = (current_candle['close'] - current_candle['low']) / candle_range if candle_range > 0 else 0
                
                # Check gap size
                gap_size = breakout_levels['range'].iloc[-2]
                atr_current = BreakoutIndicators.calculate_atr(
                    data_15m['high'], data_15m['low'], data_15m['close']
                ).iloc[-1]
                
                pattern_result.update({
                    'breakout_level': previous_resistance,
                    'candle_quality': close_position,
                    'gap_size': gap_size / atr_current if atr_current > 0 else 0
                })
                
                # Validate pattern
                if (close_position >= self.config['candle_close_threshold'] and 
                    gap_size >= atr_current * self.config['min_gap_atr_multiplier']):
                    pattern_result['valid'] = True
                    pattern_result['reason'] = 'Valid long breakout pattern'
                else:
                    pattern_result['reason'] = f'Pattern quality insufficient: close_pos={close_position:.2f}, gap_ratio={gap_size/atr_current:.2f}'
        
        elif direction == -1:  # Short breakout
            if current_candle['close'] < previous_support:
                # Check candle quality (close in bottom 75% of range)
                candle_range = current_candle['high'] - current_candle['low']
                close_position = (current_candle['high'] - current_candle['close']) / candle_range if candle_range > 0 else 0
                
                # Check gap size
                gap_size = breakout_levels['range'].iloc[-2]
                atr_current = BreakoutIndicators.calculate_atr(
                    data_15m['high'], data_15m['low'], data_15m['close']
                ).iloc[-1]
                
                pattern_result.update({
                    'breakout_level': previous_support,
                    'candle_quality': close_position,
                    'gap_size': gap_size / atr_current if atr_current > 0 else 0
                })
                
                # Validate pattern
                if (close_position >= self.config['candle_close_threshold'] and 
                    gap_size >= atr_current * self.config['min_gap_atr_multiplier']):
                    pattern_result['valid'] = True
                    pattern_result['reason'] = 'Valid short breakout pattern'
                else:
                    pattern_result['reason'] = f'Pattern quality insufficient: close_pos={close_position:.2f}, gap_ratio={gap_size/atr_current:.2f}'
        
        return pattern_result
    
    def validate_volume_surge(self, data_15m: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate volume surge for breakout confirmation
        
        Args:
            data_15m: 15M OHLCV data with volume
            
        Returns:
            Dictionary with volume validation results
        """
        if len(data_15m) < max(self.config['volume_sma_period'], self.config['volume_short_period']):
            return {'valid': False, 'reason': 'Insufficient volume data'}
        
        volume_indicators = BreakoutIndicators.calculate_volume_indicators(
            data_15m['volume'], self.config['volume_sma_period'], self.config['volume_short_period']
        )
        
        current_volume = data_15m['volume'].iloc[-1]
        surge_ratio = volume_indicators['surge_ratio'].iloc[-1]
        avg_ratio = volume_indicators['ratio_to_avg'].iloc[-1]
        
        volume_result = {
            'valid': False,
            'current_volume': current_volume,
            'surge_ratio': surge_ratio,
            'avg_ratio': avg_ratio,
            'reason': ''
        }
        
        # Check volume criteria
        if (surge_ratio >= self.config['volume_surge_multiplier'] and 
            avg_ratio >= self.config['volume_confirmation_multiplier']):
            volume_result['valid'] = True
            volume_result['reason'] = 'Volume surge confirmed'
        else:
            volume_result['reason'] = f'Volume insufficient: surge={surge_ratio:.2f}, avg={avg_ratio:.2f}'
        
        return volume_result
    
    def validate_volatility_expansion(self, data_15m: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate volatility expansion criteria
        
        Args:
            data_15m: 15M OHLCV data
            
        Returns:
            Dictionary with volatility validation results
        """
        if len(data_15m) < 50:  # Need enough data for percentile calculation
            return {'valid': False, 'reason': 'Insufficient data for volatility analysis'}
        
        # Calculate ATR and Bollinger Bands
        atr = BreakoutIndicators.calculate_atr(
            data_15m['high'], data_15m['low'], data_15m['close'], self.config['atr_period']
        )
        
        bb = BreakoutIndicators.calculate_bollinger_bands(
            data_15m['close'], self.config['bb_period'], self.config['bb_std_dev']
        )
        
        # Check ATR expansion
        atr_expanding = True
        for i in range(1, self.config['atr_expansion_periods'] + 1):
            if len(atr) < i + 1 or atr.iloc[-i] <= atr.iloc[-i-1]:
                atr_expanding = False
                break
        
        # Check Bollinger Band compression
        bb_width_percentile = bb['width'].rolling(window=50).rank(pct=True).iloc[-1] * 100
        bb_compressed = bb_width_percentile <= self.config['bb_compression_percentile']
        
        volatility_result = {
            'valid': atr_expanding and bb_compressed,
            'atr_expanding': atr_expanding,
            'bb_compressed': bb_compressed,
            'bb_percentile': bb_width_percentile,
            'reason': ''
        }
        
        if volatility_result['valid']:
            volatility_result['reason'] = 'Volatility expansion confirmed'
        else:
            volatility_result['reason'] = f'Volatility criteria failed: ATR_exp={atr_expanding}, BB_comp={bb_compressed}'
        
        return volatility_result

class BreakoutSignalGenerator:
    """Generate trading signals for the Momentum Breakout Pro strategy"""
    
    def __init__(self, config: dict, symbol_config: dict):
        self.config = config
        self.symbol_config = symbol_config
        self.pattern_detector = BreakoutPatternDetector(config)
        self.logger = logging.getLogger(__name__)
    
    def generate_signals(self, data_4h: pd.DataFrame, data_1h: pd.DataFrame, 
                        data_15m: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate trading signals using multi-timeframe analysis
        
        Args:
            data_4h: 4H OHLCV data for trend bias
            data_1h: 1H OHLCV data for confirmation  
            data_15m: 15M OHLCV data for entry signals
            
        Returns:
            Dictionary with signal information
        """
        signal_result = {
            'signal': 0,  # 1 for long, -1 for short, 0 for no signal
            'signal_strength': 0,
            'entry_price': 0,
            'confidence': 0,
            'reasons': [],
            'invalidation_reasons': []
        }
        
        try:
            # Step 1: Determine trend bias from 4H
            trend_bias = self.pattern_detector.detect_trend_bias(data_4h)
            if trend_bias == 0:
                signal_result['invalidation_reasons'].append('No clear trend bias on 4H')
                return signal_result
            
            # Step 2: Check for breakout patterns on 15M
            long_pattern = self.pattern_detector.detect_breakout_pattern(data_15m, 1)
            short_pattern = self.pattern_detector.detect_breakout_pattern(data_15m, -1)
            
            # Determine signal direction
            potential_signal = 0
            pattern_result = None
            
            if trend_bias == 1 and long_pattern['valid']:
                potential_signal = 1
                pattern_result = long_pattern
                signal_result['entry_price'] = data_15m['close'].iloc[-1]
            elif trend_bias == -1 and short_pattern['valid']:
                potential_signal = -1
                pattern_result = short_pattern  
                signal_result['entry_price'] = data_15m['close'].iloc[-1]
            
            if potential_signal == 0:
                if trend_bias == 1 and not long_pattern['valid']:
                    signal_result['invalidation_reasons'].append(f"Long pattern invalid: {long_pattern['reason']}")
                elif trend_bias == -1 and not short_pattern['valid']:
                    signal_result['invalidation_reasons'].append(f"Short pattern invalid: {short_pattern['reason']}")
                return signal_result
            
            # Step 3: Volume confirmation
            volume_validation = self.pattern_detector.validate_volume_surge(data_15m)
            if not volume_validation['valid']:
                signal_result['invalidation_reasons'].append(volume_validation['reason'])
                return signal_result
            
            # Step 4: Volatility expansion
            volatility_validation = self.pattern_detector.validate_volatility_expansion(data_15m)
            if not volatility_validation['valid']:
                signal_result['invalidation_reasons'].append(volatility_validation['reason'])
                return signal_result
            
            # Step 5: Technical confluence checks
            technical_validation = self._validate_technical_confluence(data_15m, potential_signal)
            if not technical_validation['valid']:
                signal_result['invalidation_reasons'].extend(technical_validation['reasons'])
                return signal_result
            
            # Step 6: Calculate signal strength and confidence
            signal_strength = self._calculate_signal_strength(
                pattern_result, volume_validation, volatility_validation, technical_validation
            )
            
            # All criteria passed - generate signal
            signal_result.update({
                'signal': potential_signal,
                'signal_strength': signal_strength,
                'confidence': min(signal_strength * 100, 95),  # Cap at 95%
                'reasons': [
                    f'Trend bias: {"Bullish" if trend_bias == 1 else "Bearish"}',
                    f'Pattern: {pattern_result["reason"]}',
                    f'Volume: {volume_validation["reason"]}',
                    f'Volatility: {volatility_validation["reason"]}',
                    f'Technical: {technical_validation["summary"]}'
                ],
                'pattern_details': pattern_result,
                'volume_details': volume_validation,
                'volatility_details': volatility_validation,
                'technical_details': technical_validation
            })
            
            self.logger.info(f"Signal generated: {potential_signal} with strength {signal_strength:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error generating signals: {e}")
            signal_result['invalidation_reasons'].append(f'Technical error: {str(e)}')
        
        return signal_result
    
    def _validate_technical_confluence(self, data_15m: pd.DataFrame, direction: int) -> Dict[str, Any]:
        """Validate technical confluence for signal confirmation"""
        
        validation_result = {
            'valid': True,
            'reasons': [],
            'rsi_valid': False,
            'proximity_valid': False,
            'level_clear': False,
            'summary': ''
        }
        
        try:
            # Calculate RSI
            rsi = BreakoutIndicators.calculate_rsi(data_15m['close'], self.config['rsi_period'])
            current_rsi = rsi.iloc[-1]
            
            # Check RSI criteria
            if direction == 1:  # Long
                rsi_valid = (self.config['rsi_long_min'] <= current_rsi <= self.config['rsi_long_max'])
                if not rsi_valid:
                    validation_result['reasons'].append(f'RSI invalid for long: {current_rsi:.1f}')
            else:  # Short
                rsi_valid = (self.config['rsi_short_min'] <= current_rsi <= self.config['rsi_short_max'])
                if not rsi_valid:
                    validation_result['reasons'].append(f'RSI invalid for short: {current_rsi:.1f}')
            
            validation_result['rsi_valid'] = rsi_valid
            
            # Check proximity to breakout level
            breakout_levels = BreakoutIndicators.calculate_breakout_levels(
                data_15m['high'], data_15m['low'], self.config['breakout_period']
            )
            
            current_price = data_15m['close'].iloc[-1]
            
            if direction == 1:
                breakout_level = breakout_levels['resistance'].iloc[-2]
                proximity = abs(current_price - breakout_level) / breakout_level
                proximity_valid = proximity <= self.config['breakout_proximity']
                if not proximity_valid:
                    validation_result['reasons'].append(f'Too far from resistance: {proximity:.3f}')
            else:
                breakout_level = breakout_levels['support'].iloc[-2]  
                proximity = abs(current_price - breakout_level) / breakout_level
                proximity_valid = proximity <= self.config['breakout_proximity']
                if not proximity_valid:
                    validation_result['reasons'].append(f'Too far from support: {proximity:.3f}')
            
            validation_result['proximity_valid'] = proximity_valid
            
            # Check for clear path (no immediate resistance/support)
            level_clear = True  # Simplified for now - could add S/R level detection
            validation_result['level_clear'] = level_clear
            
            # Overall validation
            validation_result['valid'] = rsi_valid and proximity_valid and level_clear
            
            if validation_result['valid']:
                validation_result['summary'] = f'Technical confluence confirmed (RSI: {current_rsi:.1f})'
            else:
                validation_result['summary'] = 'Technical confluence failed'
                
        except Exception as e:
            validation_result['valid'] = False
            validation_result['reasons'].append(f'Technical validation error: {str(e)}')
            validation_result['summary'] = 'Technical validation error'
        
        return validation_result
    
    def _calculate_signal_strength(self, pattern_result: Dict, volume_result: Dict, 
                                 volatility_result: Dict, technical_result: Dict) -> float:
        """Calculate signal strength (0-1) based on various factors"""
        
        strength_components = []
        
        # Pattern strength (0-0.3)
        if pattern_result:
            pattern_strength = min(pattern_result.get('candle_quality', 0) * 0.3, 0.3)
            strength_components.append(pattern_strength)
        
        # Volume strength (0-0.25)  
        if volume_result:
            volume_surge = min(volume_result.get('surge_ratio', 0) / 3.0, 1.0)  # Normalize to 1.0
            volume_strength = volume_surge * 0.25
            strength_components.append(volume_strength)
        
        # Volatility strength (0-0.2)
        if volatility_result:
            volatility_strength = 0.2 if volatility_result.get('atr_expanding', False) else 0.1
            strength_components.append(volatility_strength)
        
        # Technical strength (0-0.25)
        if technical_result:
            technical_strength = 0.25 if technical_result.get('valid', False) else 0.1
            strength_components.append(technical_strength)
        
        total_strength = sum(strength_components)
        return min(total_strength, 1.0)  # Cap at 1.0