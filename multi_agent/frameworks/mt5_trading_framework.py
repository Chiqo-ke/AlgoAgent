"""
MT5 Python Trading Framework
Complete trading system using the official MetaTrader5 Python SDK

Features:
- Real-time market data via MT5 Python SDK
- Order execution and position management
- Technical indicator calculations  
- Risk management and position sizing
- Backtesting with historical data
- Integration with TradingView data
- Dual-mode: Backtest and Live trading

Installation:
pip install MetaTrader5 pandas numpy matplotlib

Requirements:
- MetaTrader 5 terminal installed and running
- Trading account connected (demo recommended for testing)
- Automated trading enabled in MT5
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
from typing import Optional, Dict, List, Tuple, Union
import json

class MT5TradingFramework:
    """
    Complete MT5 trading framework using official Python SDK
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize the MT5 trading framework
        
        Args:
            config: Configuration dictionary with settings
        """
        self.config = config or {}
        
        # Trading configuration
        self.mode = self.config.get('mode', 'live')  # 'live', 'demo', 'backtest'
        self.account = self.config.get('account', {})
        
        # Risk management settings
        self.risk_management = self.config.get('risk_management', {
            'max_risk_per_trade': 0.02,  # 2% per trade
            'max_portfolio_risk': 0.06,  # 6% total portfolio
            'max_daily_loss': 0.05,      # 5% daily loss limit
            'min_stop_loss_distance': 0.005,  # Minimum SL distance
        })
        
        # Connection status
        self.is_connected = False
        self.account_info = {}
        
        # Data storage
        self.positions = {}
        self.orders = {}
        self.price_data = {}
        self.indicators = {}
        self.trade_history = []
        
        # Logging setup
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def connect(self, login: int = None, password: str = None, server: str = None) -> bool:
        """
        Connect to MetaTrader 5
        
        Args:
            login: Account login number
            password: Account password  
            server: Broker server
            
        Returns:
            True if connected successfully, False otherwise
        """
        try:
            # Initialize MT5 connection
            if not mt5.initialize():
                self.logger.error(f"MT5 initialize failed: {mt5.last_error()}")
                return False
            
            # Login if credentials provided
            if login and password and server:
                if not mt5.login(login, password, server):
                    self.logger.error(f"MT5 login failed: {mt5.last_error()}")
                    mt5.shutdown()
                    return False
            
            # Get account information
            self.account_info = mt5.account_info()
            if self.account_info is None:
                self.logger.error(f"Failed to get account info: {mt5.last_error()}")
                mt5.shutdown()
                return False
                
            self.account_info = self.account_info._asdict()
            self.is_connected = True
            
            self.logger.info(f"Connected to MT5 - Account: {self.account_info.get('login')}")
            self.logger.info(f"Balance: {self.account_info.get('balance')}, Equity: {self.account_info.get('equity')}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MetaTrader 5"""
        if self.is_connected:
            mt5.shutdown()
            self.is_connected = False
            self.logger.info("Disconnected from MT5")
    
    # ============ MARKET DATA METHODS ============
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """
        Get symbol information
        
        Args:
            symbol: Symbol name (e.g., 'EURUSD', 'AAPL')
            
        Returns:
            Dictionary with symbol info or None
        """
        try:
            if not self.is_connected:
                self.logger.error("Not connected to MT5")
                return None
                
            info = mt5.symbol_info(symbol)
            if info is None:
                self.logger.error(f"Symbol {symbol} not found")
                return None
                
            return info._asdict()
            
        except Exception as e:
            self.logger.error(f"Error getting symbol info for {symbol}: {e}")
            return None
    
    def get_tick(self, symbol: str) -> Optional[Dict]:
        """
        Get latest tick for symbol
        
        Args:
            symbol: Symbol name
            
        Returns:
            Dictionary with tick data or None
        """
        try:
            if not self.is_connected:
                self.logger.error("Not connected to MT5")
                return None
                
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                self.logger.error(f"No tick data for {symbol}")
                return None
                
            tick_dict = tick._asdict()
            
            # Store in price data cache
            self.price_data[symbol] = {
                'bid': tick_dict['bid'],
                'ask': tick_dict['ask'],
                'last': tick_dict['last'],
                'time': tick_dict['time'],
                'timestamp': time.time()
            }
            
            return tick_dict
            
        except Exception as e:
            self.logger.error(f"Error getting tick for {symbol}: {e}")
            return None
    
    def get_bars(self, symbol: str, timeframe: int, count: int = 1000, 
                 start_time: datetime = None) -> Optional[pd.DataFrame]:
        """
        Get historical bars
        
        Args:
            symbol: Symbol name
            timeframe: MT5 timeframe constant (mt5.TIMEFRAME_M1, etc.)
            count: Number of bars to retrieve
            start_time: Start time for historical data
            
        Returns:
            DataFrame with OHLCV data or None
        """
        try:
            if not self.is_connected:
                self.logger.error("Not connected to MT5")
                return None
                
            if start_time:
                rates = mt5.copy_rates_from(symbol, timeframe, start_time, count)
            else:
                rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
                
            if rates is None:
                self.logger.error(f"No historical data for {symbol}")
                return None
                
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error getting bars for {symbol}: {e}")
            return None
    
    def get_ticks(self, symbol: str, count: int = 1000, 
                  start_time: datetime = None) -> Optional[pd.DataFrame]:
        """
        Get tick data
        
        Args:
            symbol: Symbol name
            count: Number of ticks to retrieve
            start_time: Start time for tick data
            
        Returns:
            DataFrame with tick data or None
        """
        try:
            if not self.is_connected:
                self.logger.error("Not connected to MT5")
                return None
                
            if start_time:
                ticks = mt5.copy_ticks_from(symbol, start_time, count, mt5.COPY_TICKS_ALL)
            else:
                # Get recent ticks
                start_time = datetime.now() - timedelta(hours=1)
                ticks = mt5.copy_ticks_from(symbol, start_time, count, mt5.COPY_TICKS_ALL)
                
            if ticks is None:
                self.logger.error(f"No tick data for {symbol}")
                return None
                
            # Convert to DataFrame
            df = pd.DataFrame(ticks)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error getting ticks for {symbol}: {e}")
            return None
    
    # ============ TECHNICAL INDICATORS ============
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate RSI (Relative Strength Index)
        
        Args:
            prices: Series of price values
            period: RSI period
            
        Returns:
            Series with RSI values
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_sma(self, prices: pd.Series, period: int = 20) -> pd.Series:
        """
        Calculate Simple Moving Average
        
        Args:
            prices: Series of price values
            period: SMA period
            
        Returns:
            Series with SMA values
        """
        return prices.rolling(window=period).mean()
    
    def calculate_ema(self, prices: pd.Series, period: int = 20) -> pd.Series:
        """
        Calculate Exponential Moving Average
        
        Args:
            prices: Series of price values
            period: EMA period
            
        Returns:
            Series with EMA values
        """
        return prices.ewm(span=period, adjust=False).mean()
    
    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, 
                                 std_dev: float = 2) -> Dict[str, pd.Series]:
        """
        Calculate Bollinger Bands
        
        Args:
            prices: Series of price values
            period: Period for calculation
            std_dev: Standard deviation multiplier
            
        Returns:
            Dictionary with upper, middle, and lower bands
        """
        sma = self.calculate_sma(prices, period)
        std = prices.rolling(window=period).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return {
            'upper': upper_band,
            'middle': sma,
            'lower': lower_band
        }
    
    def calculate_macd(self, prices: pd.Series, fast: int = 12, 
                      slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """
        Calculate MACD
        
        Args:
            prices: Series of price values
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line EMA period
            
        Returns:
            Dictionary with MACD line, signal line, and histogram
        """
        ema_fast = self.calculate_ema(prices, fast)
        ema_slow = self.calculate_ema(prices, slow)
        
        macd_line = ema_fast - ema_slow
        signal_line = self.calculate_ema(macd_line, signal)
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def update_indicators(self, symbol: str, timeframe: int = mt5.TIMEFRAME_M1):
        """
        Update all indicators for a symbol
        
        Args:
            symbol: Symbol name
            timeframe: Timeframe for calculation
        """
        try:
            # Get recent data
            bars = self.get_bars(symbol, timeframe, 100)
            if bars is None or len(bars) < 50:
                return
                
            # Calculate indicators
            prices = bars['close']
            
            # RSI
            rsi = self.calculate_rsi(prices, 14)
            self.indicators[f"{symbol}_RSI_14"] = {
                'values': rsi.tolist(),
                'current': rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else None,
                'timestamp': time.time()
            }
            
            # SMA 20
            sma20 = self.calculate_sma(prices, 20)
            self.indicators[f"{symbol}_SMA_20"] = {
                'values': sma20.tolist(),
                'current': sma20.iloc[-1] if not pd.isna(sma20.iloc[-1]) else None,
                'timestamp': time.time()
            }
            
            # EMA 9
            ema9 = self.calculate_ema(prices, 9)
            self.indicators[f"{symbol}_EMA_9"] = {
                'values': ema9.tolist(),
                'current': ema9.iloc[-1] if not pd.isna(ema9.iloc[-1]) else None,
                'timestamp': time.time()
            }
            
            # MACD
            macd = self.calculate_macd(prices)
            self.indicators[f"{symbol}_MACD"] = {
                'macd': macd['macd'].iloc[-1] if not pd.isna(macd['macd'].iloc[-1]) else None,
                'signal': macd['signal'].iloc[-1] if not pd.isna(macd['signal'].iloc[-1]) else None,
                'histogram': macd['histogram'].iloc[-1] if not pd.isna(macd['histogram'].iloc[-1]) else None,
                'timestamp': time.time()
            }
            
            self.logger.info(f"Updated indicators for {symbol}")
            
        except Exception as e:
            self.logger.error(f"Error updating indicators for {symbol}: {e}")
    
    # ============ RISK MANAGEMENT ============
    
    def calculate_position_size(self, symbol: str, entry_price: float, 
                               stop_loss: float, risk_amount: float = None) -> float:
        """
        Calculate position size based on risk management
        
        Args:
            symbol: Symbol name
            entry_price: Entry price
            stop_loss: Stop loss price
            risk_amount: Risk amount in account currency
            
        Returns:
            Position size in lots/shares
        """
        try:
            if risk_amount is None:
                balance = self.account_info.get('balance', 10000)
                risk_amount = balance * self.risk_management['max_risk_per_trade']
            
            # Calculate risk per unit
            risk_per_unit = abs(entry_price - stop_loss)
            
            if risk_per_unit == 0:
                self.logger.warning("Risk per unit is zero - invalid stop loss")
                return 0
            
            # Get symbol info for lot size calculation
            symbol_info = self.get_symbol_info(symbol)
            if symbol_info is None:
                return 0
            
            # Calculate position size
            position_size = risk_amount / risk_per_unit
            
            # Round to appropriate lot size
            min_lot = symbol_info.get('volume_min', 0.01)
            lot_step = symbol_info.get('volume_step', 0.01)
            
            # Round down to nearest step
            position_size = int(position_size / lot_step) * lot_step
            
            # Ensure minimum lot size
            position_size = max(position_size, min_lot)
            
            # Check maximum lot size
            max_lot = symbol_info.get('volume_max', 100.0)
            position_size = min(position_size, max_lot)
            
            return position_size
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 0
    
    def check_risk_limits(self, symbol: str, position_size: float, 
                         entry_price: float, stop_loss: float) -> Dict:
        """
        Check if trade respects risk limits
        
        Args:
            symbol: Symbol name
            position_size: Intended position size
            entry_price: Entry price
            stop_loss: Stop loss price
            
        Returns:
            Dictionary with risk analysis
        """
        try:
            # Calculate trade risk
            risk_per_unit = abs(entry_price - stop_loss)
            trade_risk_amount = risk_per_unit * position_size
            
            balance = self.account_info.get('balance', 10000)
            trade_risk_percent = trade_risk_amount / balance
            
            # Calculate current portfolio risk
            current_risk = self.calculate_current_risk()
            total_risk = current_risk + trade_risk_percent
            
            # Check limits
            risk_check = {
                'within_limits': True,
                'trade_risk_amount': trade_risk_amount,
                'trade_risk_percent': trade_risk_percent,
                'current_portfolio_risk': current_risk,
                'total_portfolio_risk': total_risk,
                'max_trade_risk': self.risk_management['max_risk_per_trade'],
                'max_portfolio_risk': self.risk_management['max_portfolio_risk'],
                'warnings': []
            }
            
            # Check individual trade risk
            if trade_risk_percent > self.risk_management['max_risk_per_trade']:
                risk_check['within_limits'] = False
                risk_check['warnings'].append(f"Trade risk {trade_risk_percent:.2%} exceeds max per trade {self.risk_management['max_risk_per_trade']:.2%}")
            
            # Check total portfolio risk
            if total_risk > self.risk_management['max_portfolio_risk']:
                risk_check['within_limits'] = False
                risk_check['warnings'].append(f"Total risk {total_risk:.2%} exceeds max portfolio {self.risk_management['max_portfolio_risk']:.2%}")
            
            # Check minimum stop loss distance
            stop_distance = abs(entry_price - stop_loss) / entry_price
            if stop_distance < self.risk_management['min_stop_loss_distance']:
                risk_check['warnings'].append(f"Stop loss distance {stop_distance:.3%} very small")
            
            return risk_check
            
        except Exception as e:
            self.logger.error(f"Error checking risk limits: {e}")
            return {'within_limits': False, 'error': str(e)}
    
    def calculate_current_risk(self) -> float:
        """
        Calculate current portfolio risk from open positions
        
        Returns:
            Current risk as percentage of account balance
        """
        try:
            positions = mt5.positions_get()
            if positions is None:
                return 0.0
            
            total_risk = 0.0
            balance = self.account_info.get('balance', 10000)
            
            for position in positions:
                # Calculate potential loss if position hits stop loss
                if position.sl != 0.0:  # Has stop loss
                    current_price = position.price_current
                    stop_loss = position.sl
                    volume = position.volume
                    
                    if position.type == mt5.POSITION_TYPE_BUY:
                        potential_loss = (current_price - stop_loss) * volume
                    else:  # SELL position
                        potential_loss = (stop_loss - current_price) * volume
                    
                    total_risk += max(0, potential_loss) / balance
            
            return total_risk
            
        except Exception as e:
            self.logger.error(f"Error calculating current risk: {e}")
            return 0.0
    
    # ============ TRADING OPERATIONS ============
    
    def send_order(self, symbol: str, order_type: int, volume: float,
                   price: float = None, sl: float = None, tp: float = None,
                   comment: str = "") -> Dict:
        """
        Send trading order
        
        Args:
            symbol: Symbol name
            order_type: Order type (mt5.ORDER_TYPE_BUY, mt5.ORDER_TYPE_SELL, etc.)
            volume: Order volume
            price: Order price (for pending orders)
            sl: Stop loss price
            tp: Take profit price
            comment: Order comment
            
        Returns:
            Dictionary with order result
        """
        try:
            if not self.is_connected:
                return {'success': False, 'error': 'Not connected to MT5'}
            
            # Get current price if not provided
            if price is None:
                tick = self.get_tick(symbol)
                if tick is None:
                    return {'success': False, 'error': 'Could not get current price'}
                    
                if order_type == mt5.ORDER_TYPE_BUY:
                    price = tick['ask']
                else:
                    price = tick['bid']
            
            # Prepare order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "price": price,
                "deviation": 20,  # Max deviation in points
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Add stop loss and take profit if provided
            if sl is not None:
                request["sl"] = sl
            if tp is not None:
                request["tp"] = tp
            
            # Send order
            result = mt5.order_send(request)
            
            if result is None:
                return {'success': False, 'error': f'Order failed: {mt5.last_error()}'}
            
            result_dict = result._asdict()
            
            if result_dict['retcode'] != mt5.TRADE_RETCODE_DONE:
                return {
                    'success': False, 
                    'retcode': result_dict['retcode'],
                    'error': f'Order failed with retcode: {result_dict["retcode"]}'
                }
            
            # Log successful trade
            trade_info = {
                'symbol': symbol,
                'type': 'BUY' if order_type == mt5.ORDER_TYPE_BUY else 'SELL',
                'volume': volume,
                'price': result_dict.get('price', price),
                'sl': sl,
                'tp': tp,
                'timestamp': time.time(),
                'order_id': result_dict.get('order'),
                'deal_id': result_dict.get('deal')
            }
            
            self.trade_history.append(trade_info)
            self.logger.info(f"Order executed: {trade_info}")
            
            return {
                'success': True,
                'result': result_dict,
                'trade_info': trade_info
            }
            
        except Exception as e:
            self.logger.error(f"Error sending order: {e}")
            return {'success': False, 'error': str(e)}
    
    def close_position(self, symbol: str = None, ticket: int = None) -> Dict:
        """
        Close position(s)
        
        Args:
            symbol: Close all positions for this symbol
            ticket: Close specific position by ticket
            
        Returns:
            Dictionary with operation result
        """
        try:
            if not self.is_connected:
                return {'success': False, 'error': 'Not connected to MT5'}
            
            positions = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
            
            if positions is None or len(positions) == 0:
                return {'success': False, 'error': 'No positions to close'}
            
            results = []
            
            for position in positions:
                if ticket and position.ticket != ticket:
                    continue
                
                # Determine close order type
                if position.type == mt5.POSITION_TYPE_BUY:
                    close_type = mt5.ORDER_TYPE_SELL
                else:
                    close_type = mt5.ORDER_TYPE_BUY
                
                # Get current price
                tick = self.get_tick(position.symbol)
                if tick is None:
                    continue
                    
                close_price = tick['bid'] if close_type == mt5.ORDER_TYPE_SELL else tick['ask']
                
                # Prepare close request
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": position.symbol,
                    "volume": position.volume,
                    "type": close_type,
                    "position": position.ticket,
                    "price": close_price,
                    "deviation": 20,
                    "comment": f"Close position {position.ticket}",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
                
                # Send close order
                result = mt5.order_send(request)
                
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    results.append({
                        'success': True,
                        'ticket': position.ticket,
                        'symbol': position.symbol,
                        'volume': position.volume,
                        'close_price': close_price
                    })
                    self.logger.info(f"Position {position.ticket} closed successfully")
                else:
                    results.append({
                        'success': False,
                        'ticket': position.ticket,
                        'error': f'Close failed: {result.retcode if result else mt5.last_error()}'
                    })
            
            return {'success': True, 'results': results}
            
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            return {'success': False, 'error': str(e)}
    
    # ============ STRATEGY METHODS ============
    
    def evaluate_momentum_strategy(self, symbol: str, parameters: Dict = None) -> Dict:
        """
        Evaluate momentum trading strategy
        
        Args:
            symbol: Symbol to analyze
            parameters: Strategy parameters
            
        Returns:
            Dictionary with signal information
        """
        try:
            params = parameters or {}
            
            # Update indicators
            self.update_indicators(symbol)
            
            # Get current price
            tick = self.get_tick(symbol)
            if tick is None:
                return {'action': 'HOLD', 'reason': 'No price data available'}
            
            current_price = tick['ask']
            
            # Get indicators
            rsi_data = self.indicators.get(f"{symbol}_RSI_14")
            sma_data = self.indicators.get(f"{symbol}_SMA_20")
            
            if not rsi_data or not sma_data:
                return {'action': 'HOLD', 'reason': 'Insufficient indicator data'}
            
            rsi = rsi_data['current']
            sma = sma_data['current']
            
            if rsi is None or sma is None:
                return {'action': 'HOLD', 'reason': 'Invalid indicator values'}
            
            # Strategy logic
            signal = {'action': 'HOLD', 'reason': 'No signal', 'confidence': 0.0}
            
            # Buy signal: RSI > 50 and price > SMA20
            if rsi > 50 and rsi < 70 and current_price > sma:
                stop_loss = current_price * 0.98  # 2% stop loss
                take_profit = current_price * 1.04  # 4% take profit
                
                signal = {
                    'action': 'BUY',
                    'entry_price': current_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'confidence': min(0.9, (rsi - 50) / 20 + 0.5),
                    'reason': f'RSI: {rsi:.2f}, Price above SMA20: {sma:.2f}'
                }
            
            # Sell signal: RSI < 50 and price < SMA20  
            elif rsi < 50 and rsi > 30 and current_price < sma:
                stop_loss = current_price * 1.02  # 2% stop loss
                take_profit = current_price * 0.96  # 4% take profit
                
                signal = {
                    'action': 'SELL',
                    'entry_price': current_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'confidence': min(0.9, (50 - rsi) / 20 + 0.5),
                    'reason': f'RSI: {rsi:.2f}, Price below SMA20: {sma:.2f}'
                }
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error evaluating momentum strategy for {symbol}: {e}")
            return {'action': 'HOLD', 'reason': f'Error: {e}'}
    
    def execute_strategy_signal(self, symbol: str, signal: Dict) -> Dict:
        """
        Execute a strategy signal with risk management
        
        Args:
            symbol: Symbol name
            signal: Signal dictionary from strategy evaluation
            
        Returns:
            Dictionary with execution result
        """
        try:
            if signal['action'] == 'HOLD':
                return {'success': False, 'reason': 'No signal to execute'}
            
            # Calculate position size
            position_size = self.calculate_position_size(
                symbol, 
                signal['entry_price'], 
                signal['stop_loss']
            )
            
            if position_size <= 0:
                return {'success': False, 'reason': 'Invalid position size'}
            
            # Check risk limits
            risk_check = self.check_risk_limits(
                symbol, position_size, signal['entry_price'], signal['stop_loss']
            )
            
            if not risk_check['within_limits']:
                return {
                    'success': False, 
                    'reason': 'Risk limits exceeded', 
                    'warnings': risk_check.get('warnings', [])
                }
            
            # Determine order type
            order_type = mt5.ORDER_TYPE_BUY if signal['action'] == 'BUY' else mt5.ORDER_TYPE_SELL
            
            # Execute order
            result = self.send_order(
                symbol=symbol,
                order_type=order_type,
                volume=position_size,
                sl=signal['stop_loss'],
                tp=signal.get('take_profit'),
                comment=f"Strategy signal - {signal['reason']}"
            )
            
            if result['success']:
                self.logger.info(f"Strategy signal executed successfully for {symbol}")
                return {
                    'success': True,
                    'signal': signal,
                    'position_size': position_size,
                    'execution_result': result
                }
            else:
                return {
                    'success': False,
                    'reason': f"Order execution failed: {result.get('error')}"
                }
            
        except Exception as e:
            self.logger.error(f"Error executing strategy signal: {e}")
            return {'success': False, 'reason': f'Error: {e}'}
    
    # ============ UTILITY METHODS ============
    
    def get_account_summary(self) -> Dict:
        """Get account summary information"""
        if not self.is_connected:
            return {}
        
        account_info = mt5.account_info()
        if account_info is None:
            return {}
        
        positions = mt5.positions_get()
        orders = mt5.orders_get()
        
        return {
            'account_info': account_info._asdict(),
            'open_positions': len(positions) if positions else 0,
            'pending_orders': len(orders) if orders else 0,
            'current_risk': self.calculate_current_risk(),
            'connection_status': self.is_connected
        }
    
    def integrate_tradingview_data(self, tradingview_data: Dict):
        """
        Integrate data from TradingView scraper
        
        Args:
            tradingview_data: Data from TradingView scraper
        """
        try:
            if 'indicators' in tradingview_data:
                for indicator, value in tradingview_data['indicators'].items():
                    key = f"TV_{indicator}"
                    self.indicators[key] = {
                        'current': value,
                        'timestamp': time.time(),
                        'source': 'TradingView'
                    }
            
            self.logger.info("Integrated TradingView data successfully")
            
        except Exception as e:
            self.logger.error(f"Error integrating TradingView data: {e}")
    
    def save_state(self, filename: str):
        """Save current framework state"""
        try:
            state = {
                'config': self.config,
                'indicators': self.indicators,
                'trade_history': self.trade_history,
                'timestamp': time.time()
            }
            
            with open(filename, 'w') as f:
                json.dump(state, f, indent=2, default=str)
                
            self.logger.info(f"State saved to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving state: {e}")
    
    def load_state(self, filename: str):
        """Load framework state"""
        try:
            with open(filename, 'r') as f:
                state = json.load(f)
            
            self.indicators.update(state.get('indicators', {}))
            self.trade_history.extend(state.get('trade_history', []))
            
            self.logger.info(f"State loaded from {filename}")
            
        except Exception as e:
            self.logger.error(f"Error loading state: {e}")

# Example usage and testing
if __name__ == "__main__":
    # Initialize framework
    framework = MT5TradingFramework({
        'mode': 'demo',
        'risk_management': {
            'max_risk_per_trade': 0.02,
            'max_portfolio_risk': 0.06,
            'max_daily_loss': 0.05
        }
    })
    
    # Connect to MT5
    if framework.connect():
        print("✅ Connected to MT5")
        
        # Get account summary
        summary = framework.get_account_summary()
        print(f"Account: {summary}")
        
        # Test with EURUSD
        symbol = "EURUSD"
        
        # Update indicators
        framework.update_indicators(symbol)
        
        # Evaluate momentum strategy
        signal = framework.evaluate_momentum_strategy(symbol)
        print(f"Strategy signal: {signal}")
        
        # Execute if valid signal (commented out for safety)
        # if signal['action'] != 'HOLD':
        #     result = framework.execute_strategy_signal(symbol, signal)
        #     print(f"Execution result: {result}")
        
        framework.disconnect()
    else:
        print("❌ Failed to connect to MT5")