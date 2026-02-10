"""
Strategy Testing Framework
Provides standard interface for testing trading strategies with the backtesting engine

Features:
- Base strategy class for consistent interface
- Built-in technical indicators
- Strategy validation and testing
- Performance comparison tools
- Strategy parameter management
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from abc import ABC, abstractmethod
import logging
from dataclasses import dataclass, field

from .backtesting_engine import BacktestEngine, BacktestConfig

logger = logging.getLogger(__name__)

@dataclass
class StrategyParams:
    """Strategy parameters with validation"""
    name: str = "BaseStrategy"
    version: str = "1.0.0"
    description: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get parameter value with default"""
        return self.params.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set parameter value"""
        self.params[key] = value
    
    def validate(self) -> bool:
        """Validate strategy parameters"""
        # Override in specific strategy implementations
        return True

class BaseStrategy(ABC):
    """
    Base class for trading strategies
    
    All strategies should inherit from this class and implement the required methods
    """
    
    def __init__(self, params: StrategyParams):
        """Initialize strategy with parameters"""
        self.params = params
        self.name = params.name
        self.indicators = {}
        self.last_signals = {}
        
        if not params.validate():
            raise ValueError(f"Invalid parameters for strategy {self.name}")
    
    @abstractmethod
    def calculate_indicators(self, data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """
        Calculate technical indicators for the strategy
        
        Args:
            data: Historical price data
            symbol: Trading symbol
            
        Returns:
            Dictionary of indicator values
        """
        pass
    
    @abstractmethod
    def generate_signal(self, engine: BacktestEngine, current_data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """
        Generate trading signal for current market conditions
        
        Args:
            engine: Backtesting engine instance
            current_data: Current market data
            symbol: Trading symbol
            
        Returns:
            Signal dictionary with 'action', 'quantity', 'stop_loss', 'take_profit'
        """
        pass
    
    def prepare_data(self, data: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Prepare market data by adding indicators
        
        Args:
            data: Raw market data
            symbol: Trading symbol
            
        Returns:
            Data with added indicators
        """
        try:
            indicators = self.calculate_indicators(data, symbol)
            
            # Add indicators to dataframe
            for name, values in indicators.items():
                if isinstance(values, (list, np.ndarray, pd.Series)):
                    if len(values) == len(data):
                        data[f"{name}"] = values
                    else:
                        logger.warning(f"Indicator {name} length mismatch for {symbol}")
                
            self.indicators[symbol] = indicators
            return data
            
        except Exception as e:
            logger.error(f"Error preparing data for {symbol}: {e}")
            return data
    
    def on_bar(self, engine: BacktestEngine, current_data: Dict[str, Any]):
        """
        Called on each bar update - main strategy entry point
        
        Args:
            engine: Backtesting engine instance
            current_data: Current market data for all symbols
        """
        try:
            for symbol, bar_data in current_data.items():
                if symbol in engine.config.symbols:
                    signal = self.generate_signal(engine, current_data, symbol)
                    
                    if signal and signal.get('action'):
                        self.execute_signal(engine, symbol, signal)
                        
        except Exception as e:
            logger.error(f"Error in strategy {self.name} on_bar: {e}")
    
    def execute_signal(self, engine: BacktestEngine, symbol: str, signal: Dict[str, Any]):
        """
        Execute trading signal
        
        Args:
            engine: Backtesting engine instance
            symbol: Trading symbol
            signal: Signal dictionary
        """
        action = signal.get('action', '').lower()
        
        if action == 'buy' or action == 'long':
            # Close any short position first
            if symbol in engine.positions and engine.positions[symbol].side == 'short':
                engine.close_position(symbol, "signal_reverse")
            
            # Open long position if not already long
            if symbol not in engine.positions:
                quantity = signal.get('quantity', 0)
                if quantity <= 0:
                    # Calculate position size based on risk
                    current_price = engine.get_current_price(symbol)
                    stop_loss = signal.get('stop_loss', current_price * 0.98)
                    quantity = engine.calculate_position_size(symbol, current_price, stop_loss)
                
                if quantity > 0:
                    engine.open_position(
                        symbol=symbol,
                        side='long',
                        quantity=quantity,
                        stop_loss=signal.get('stop_loss'),
                        take_profit=signal.get('take_profit'),
                        reason=f"{self.name}_long"
                    )
        
        elif action == 'sell' or action == 'short':
            # Close any long position first
            if symbol in engine.positions and engine.positions[symbol].side == 'long':
                engine.close_position(symbol, "signal_reverse")
            
            # Open short position if not already short
            if symbol not in engine.positions:
                quantity = signal.get('quantity', 0)
                if quantity <= 0:
                    # Calculate position size based on risk
                    current_price = engine.get_current_price(symbol)
                    stop_loss = signal.get('stop_loss', current_price * 1.02)
                    quantity = engine.calculate_position_size(symbol, current_price, stop_loss)
                
                if quantity > 0:
                    engine.open_position(
                        symbol=symbol,
                        side='short',
                        quantity=quantity,
                        stop_loss=signal.get('stop_loss'),
                        take_profit=signal.get('take_profit'),
                        reason=f"{self.name}_short"
                    )
        
        elif action == 'close' or action == 'exit':
            # Close existing position
            if symbol in engine.positions:
                engine.close_position(symbol, f"{self.name}_exit")

class TechnicalIndicators:
    """
    Collection of technical indicators for strategy development
    """
    
    @staticmethod
    def sma(prices: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average"""
        return prices.rolling(window=period).mean()
    
    @staticmethod
    def ema(prices: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average"""
        return prices.ewm(span=period).mean()
    
    @staticmethod
    def rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """MACD Indicator"""
        ema_fast = TechnicalIndicators.ema(prices, fast)
        ema_slow = TechnicalIndicators.ema(prices, slow)
        macd_line = ema_fast - ema_slow
        signal_line = TechnicalIndicators.ema(macd_line, signal)
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def bollinger_bands(prices: pd.Series, period: int = 20, std_dev: int = 2) -> Dict[str, pd.Series]:
        """Bollinger Bands"""
        sma = TechnicalIndicators.sma(prices, period)
        std = prices.rolling(window=period).std()
        
        return {
            'upper': sma + (std * std_dev),
            'middle': sma,
            'lower': sma - (std * std_dev)
        }
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Average True Range"""
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()
    
    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
        """Stochastic Oscillator"""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return {
            'k': k_percent,
            'd': d_percent
        }

class MomentumStrategy(BaseStrategy):
    """
    Example momentum strategy implementation
    
    Strategy Logic:
    - Buy when RSI > 50 and price > SMA20
    - Sell when RSI < 50 and price < SMA20
    - Use ATR for stop loss calculation
    """
    
    def __init__(self, params: StrategyParams = None):
        if params is None:
            params = StrategyParams(
                name="MomentumStrategy",
                description="RSI and SMA-based momentum strategy",
                params={
                    'rsi_period': 14,
                    'sma_period': 20,
                    'rsi_long_threshold': 50,
                    'rsi_short_threshold': 50,
                    'atr_period': 14,
                    'atr_multiplier': 2.0,
                    'take_profit_ratio': 2.0
                }
            )
        super().__init__(params)
    
    def calculate_indicators(self, data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """Calculate RSI, SMA, and ATR indicators"""
        indicators = {}
        
        # RSI
        rsi_period = self.params.get('rsi_period', 14)
        indicators['rsi'] = TechnicalIndicators.rsi(data['close'], rsi_period)
        
        # SMA
        sma_period = self.params.get('sma_period', 20)
        indicators['sma'] = TechnicalIndicators.sma(data['close'], sma_period)
        
        # ATR for stop loss
        atr_period = self.params.get('atr_period', 14)
        indicators['atr'] = TechnicalIndicators.atr(data['high'], data['low'], data['close'], atr_period)
        
        return indicators
    
    def generate_signal(self, engine: BacktestEngine, current_data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """Generate momentum-based trading signals"""
        if symbol not in current_data:
            return {}
        
        # Get current values
        current_bar = current_data[symbol]
        current_price = current_bar['close']
        
        # Get historical data to calculate current indicator values
        if symbol not in engine.market_data:
            return {}
        
        # Get data up to current time
        historical_data = engine.market_data[symbol].loc[:engine.current_time]
        if len(historical_data) < max(self.params.get('rsi_period', 14), self.params.get('sma_period', 20)):
            return {}  # Not enough data
        
        # Calculate current indicator values
        indicators = self.calculate_indicators(historical_data, symbol)
        
        # Get latest values
        try:
            current_rsi = indicators['rsi'].iloc[-1]
            current_sma = indicators['sma'].iloc[-1]
            current_atr = indicators['atr'].iloc[-1]
            
            if pd.isna(current_rsi) or pd.isna(current_sma) or pd.isna(current_atr):
                return {}
        
        except (IndexError, KeyError):
            return {}
        
        # Strategy parameters
        rsi_long_threshold = self.params.get('rsi_long_threshold', 50)
        rsi_short_threshold = self.params.get('rsi_short_threshold', 50)
        atr_multiplier = self.params.get('atr_multiplier', 2.0)
        take_profit_ratio = self.params.get('take_profit_ratio', 2.0)
        
        # Generate signals
        signal = {}
        
        # Long signal: RSI > threshold and price > SMA
        if current_rsi > rsi_long_threshold and current_price > current_sma:
            stop_loss = current_price - (current_atr * atr_multiplier)
            take_profit = current_price + (current_atr * atr_multiplier * take_profit_ratio)
            
            signal = {
                'action': 'buy',
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'reason': f'RSI:{current_rsi:.1f}>50, Price:{current_price:.2f}>SMA:{current_sma:.2f}'
            }
        
        # Short signal: RSI < threshold and price < SMA
        elif current_rsi < rsi_short_threshold and current_price < current_sma:
            stop_loss = current_price + (current_atr * atr_multiplier)
            take_profit = current_price - (current_atr * atr_multiplier * take_profit_ratio)
            
            signal = {
                'action': 'sell',
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'reason': f'RSI:{current_rsi:.1f}<50, Price:{current_price:.2f}<SMA:{current_sma:.2f}'
            }
        
        return signal

class StrategyTester:
    """
    Strategy testing and comparison framework
    """
    
    def __init__(self):
        """Initialize strategy tester"""
        self.strategies = {}
        self.test_results = {}
    
    def add_strategy(self, name: str, strategy: BaseStrategy):
        """Add strategy for testing"""
        self.strategies[name] = strategy
        logger.info(f"Added strategy: {name}")
    
    def test_strategy(self, strategy_name: str, config: BacktestConfig, market_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Test a single strategy
        
        Args:
            strategy_name: Name of strategy to test
            config: Backtesting configuration
            market_data: Market data dictionary
            
        Returns:
            Test results
        """
        if strategy_name not in self.strategies:
            raise ValueError(f"Strategy {strategy_name} not found")
        
        strategy = self.strategies[strategy_name]
        logger.info(f"Testing strategy: {strategy_name}")
        
        # Create backtesting engine
        engine = BacktestEngine(config)
        
        # Load market data and prepare with indicators
        for symbol, data in market_data.items():
            prepared_data = strategy.prepare_data(data.copy(), symbol)
            engine.load_market_data(symbol, prepared_data)
        
        # Set strategy function
        engine.set_strategy(strategy.on_bar)
        
        # Run backtest
        results = engine.run_backtest()
        
        # Add strategy info to results
        results['strategy'] = {
            'name': strategy.name,
            'params': strategy.params.params,
            'description': strategy.params.description
        }
        
        # Store results
        self.test_results[strategy_name] = results
        
        logger.info(f"Strategy {strategy_name} test completed")
        return results
    
    def test_all_strategies(self, config: BacktestConfig, market_data: Dict[str, pd.DataFrame]) -> Dict[str, Dict[str, Any]]:
        """
        Test all registered strategies
        
        Args:
            config: Backtesting configuration
            market_data: Market data dictionary
            
        Returns:
            Dictionary of all test results
        """
        results = {}
        
        for strategy_name in self.strategies:
            try:
                results[strategy_name] = self.test_strategy(strategy_name, config, market_data)
            except Exception as e:
                logger.error(f"Error testing strategy {strategy_name}: {e}")
                results[strategy_name] = {'error': str(e)}
        
        return results
    
    def compare_strategies(self, metrics: List[str] = None) -> pd.DataFrame:
        """
        Compare strategy performance
        
        Args:
            metrics: List of metrics to compare
            
        Returns:
            Comparison dataframe
        """
        if metrics is None:
            metrics = ['total_return', 'max_drawdown', 'sharpe_ratio', 'win_rate', 'profit_factor', 'total_trades']
        
        comparison_data = []
        
        for strategy_name, results in self.test_results.items():
            if 'error' in results:
                continue
                
            row = {'strategy': strategy_name}
            
            for metric in metrics:
                if metric in results['summary']:
                    row[metric] = results['summary'][metric]
                elif metric in results['trades']:
                    row[metric] = results['trades'][metric]
                else:
                    row[metric] = None
            
            comparison_data.append(row)
        
        return pd.DataFrame(comparison_data)
    
    def get_best_strategy(self, metric: str = 'sharpe_ratio') -> str:
        """
        Get best performing strategy by metric
        
        Args:
            metric: Metric to use for comparison
            
        Returns:
            Name of best strategy
        """
        comparison = self.compare_strategies([metric])
        if comparison.empty:
            return None
        
        best_idx = comparison[metric].idxmax()
        return comparison.loc[best_idx, 'strategy']