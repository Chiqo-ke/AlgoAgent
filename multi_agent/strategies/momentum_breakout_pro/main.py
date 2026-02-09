import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta
from .config import STRATEGY_CONFIG, SYMBOL_CONFIGS, RISK_CONFIG
from .indicators import BreakoutSignalGenerator
from .risk_management import AdvancedRiskManager, PositionManager

class MomentumBreakoutStrategy:
    """
    Main strategy class for Momentum Breakout Pro
    
    This class orchestrates the entire trading strategy including:
    - Multi-timeframe signal generation
    - Risk management
    - Position management
    - Trade execution logic
    """
    
    def __init__(self, symbol: str, mt5_interface=None):
        """
        Initialize the Momentum Breakout Pro strategy
        
        Args:
            symbol: Trading symbol (EURUSD, AAPL, MSFT)
            mt5_interface: MT5 interface for live trading (optional)
        """
        self.symbol = symbol
        self.mt5_interface = mt5_interface
        
        # Configuration
        self.config = STRATEGY_CONFIG.copy()
        self.symbol_config = SYMBOL_CONFIGS.get(symbol, {})
        self.risk_config = RISK_CONFIG.copy()
        
        # Strategy components
        self.signal_generator = BreakoutSignalGenerator(self.config, self.symbol_config)
        self.risk_manager = AdvancedRiskManager(self.risk_config, SYMBOL_CONFIGS)
        self.position_manager = PositionManager(self.risk_config)
        
        # State tracking
        self.account_balance = 100000  # Default balance, should be updated from MT5
        self.current_drawdown = 0.0
        self.daily_pnl = 0.0
        self.last_signal_time = None
        
        # Data storage
        self.data_4h = pd.DataFrame()
        self.data_1h = pd.DataFrame()  
        self.data_15m = pd.DataFrame()
        
        # Performance tracking
        self.performance_metrics = {}
        self.trade_log = []
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initialized Momentum Breakout Pro strategy for {symbol}")
    
    def update_market_data(self, data_4h: pd.DataFrame, data_1h: pd.DataFrame, 
                          data_15m: pd.DataFrame) -> None:
        """
        Update market data for all timeframes
        
        Args:
            data_4h: 4-hour OHLCV data
            data_1h: 1-hour OHLCV data
            data_15m: 15-minute OHLCV data
        """
        self.data_4h = data_4h.copy()
        self.data_1h = data_1h.copy()
        self.data_15m = data_15m.copy()
        
        # Update position tracking with latest prices
        if not self.data_15m.empty:
            current_price = self.data_15m['close'].iloc[-1]
            self._update_open_positions(current_price)
    
    def analyze_market(self) -> Dict[str, Any]:
        """
        Perform comprehensive market analysis
        
        Returns:
            Dictionary with market analysis results
        """
        analysis = {
            'timestamp': datetime.now(),
            'symbol': self.symbol,
            'current_price': 0,
            'signal': None,
            'market_condition': 'unknown',
            'volatility_regime': 'unknown',
            'trend_direction': 'unknown',
            'trade_recommendation': 'HOLD',
            'risk_assessment': {}
        }
        
        try:
            if self.data_15m.empty or self.data_4h.empty:
                analysis['error'] = 'Insufficient data for analysis'
                return analysis
            
            current_price = self.data_15m['close'].iloc[-1]
            analysis['current_price'] = current_price
            
            # Generate trading signal
            signal_data = self.signal_generator.generate_signals(
                self.data_4h, self.data_1h, self.data_15m
            )
            
            analysis['signal'] = signal_data
            
            # Assess market conditions
            market_conditions = self._assess_market_conditions()
            analysis.update(market_conditions)
            
            # Risk assessment
            current_positions = self.position_manager.get_position_statistics()['current_positions']
            
            if signal_data['signal'] != 0:
                risk_valid, risk_reasons = self.risk_manager.validate_trade_risk(
                    self.symbol, signal_data['signal_strength'], current_positions,
                    self.account_balance, self.current_drawdown
                )
                
                analysis['risk_assessment'] = {
                    'valid': risk_valid,
                    'reasons': risk_reasons
                }
                
                if risk_valid and signal_data['signal'] != 0:
                    if signal_data['signal'] == 1:
                        analysis['trade_recommendation'] = 'BUY'
                    else:
                        analysis['trade_recommendation'] = 'SELL'
                else:
                    analysis['trade_recommendation'] = 'HOLD'
            
        except Exception as e:
            self.logger.error(f"Error in market analysis: {e}")
            analysis['error'] = str(e)
        
        return analysis
    
    def execute_trade(self, signal_data: Dict[str, Any]) -> Optional[str]:
        """
        Execute a trade based on signal data
        
        Args:
            signal_data: Signal information from market analysis
            
        Returns:
            Position ID if trade executed, None otherwise
        """
        if signal_data['signal'] == 0:
            return None
        
        try:
            current_price = signal_data['entry_price']
            direction = 'long' if signal_data['signal'] == 1 else 'short'
            
            # Calculate ATR for stop loss
            from .indicators import BreakoutIndicators
            atr = BreakoutIndicators.calculate_atr(
                self.data_15m['high'], self.data_15m['low'], self.data_15m['close']
            ).iloc[-1]
            
            # Calculate stop loss
            stop_loss = self.risk_manager.calculate_stop_loss(
                self.symbol, current_price, direction, atr, self.data_15m
            )
            
            # Calculate take profit levels
            tp_levels = self.risk_manager.calculate_take_profit_levels(
                current_price, stop_loss, direction
            )
            
            # Calculate position size
            position_size = self.risk_manager.calculate_position_size(
                self.symbol, self.account_balance, current_price, stop_loss
            )
            
            if position_size <= 0:
                self.logger.warning("Position size calculation returned 0 or negative")
                return None
            
            # Execute trade through MT5 (if available)
            if self.mt5_interface:
                order_result = self._execute_mt5_trade(
                    direction, current_price, position_size, stop_loss, tp_levels
                )
                if not order_result['success']:
                    self.logger.error(f"MT5 order failed: {order_result['error']}")
                    return None
            
            # Record position in position manager
            position_id = self.position_manager.open_position(
                symbol=self.symbol,
                direction=direction,
                entry_price=current_price,
                position_size=position_size,
                stop_loss=stop_loss,
                take_profit_levels=tp_levels,
                signal_data=signal_data,
                timestamp=datetime.now()
            )
            
            # Log trade
            trade_log_entry = {
                'timestamp': datetime.now(),
                'position_id': position_id,
                'symbol': self.symbol,
                'direction': direction,
                'entry_price': current_price,
                'position_size': position_size,
                'stop_loss': stop_loss,
                'take_profit_levels': tp_levels,
                'signal_strength': signal_data['signal_strength'],
                'confidence': signal_data['confidence'],
                'action': 'ENTRY'
            }
            
            self.trade_log.append(trade_log_entry)
            self.last_signal_time = datetime.now()
            
            self.logger.info(f"Trade executed: {position_id} - {direction} {self.symbol} "
                           f"@ {current_price:.5f}, Size: {position_size}")
            
            return position_id
            
        except Exception as e:
            self.logger.error(f"Error executing trade: {e}")
            return None
    
    def manage_positions(self) -> List[Dict[str, Any]]:
        """
        Manage existing positions (exits, trailing stops, etc.)
        
        Returns:
            List of position management actions taken
        """
        actions = []
        
        if self.data_15m.empty:
            return actions
        
        current_price = self.data_15m['close'].iloc[-1]
        current_time = datetime.now()
        
        # Calculate current ATR for trailing stops
        from .indicators import BreakoutIndicators
        current_atr = BreakoutIndicators.calculate_atr(
            self.data_15m['high'], self.data_15m['low'], self.data_15m['close']
        ).iloc[-1]
        
        # Check each open position
        positions_to_close = []
        
        for position_id, position in self.position_manager.positions.items():
            try:
                # Update MFE/MAE tracking
                self.position_manager.update_mfe_mae(position_id, current_price)
                
                # Check if position should be closed
                should_close, reason, exit_type = self.risk_manager.should_close_position(
                    position, current_price, current_atr, current_time
                )
                
                if should_close:
                    positions_to_close.append((position_id, reason, exit_type))
                    continue
                
                # Update trailing stops for profitable positions
                entry_price = position['entry_price']
                direction = position['direction']
                
                # Check if position is profitable enough for trailing stop
                if direction.lower() == 'long':
                    profit_ratio = (current_price - entry_price) / abs(entry_price - position['stop_loss'])
                else:
                    profit_ratio = (entry_price - current_price) / abs(entry_price - position['stop_loss'])
                
                if profit_ratio >= 1.0:  # 1:1 risk-reward achieved
                    new_trailing_stop = self.risk_manager.calculate_trailing_stop(
                        self.symbol, entry_price, current_price, direction, 
                        current_atr, position.get('trailing_stop')
                    )
                    
                    if new_trailing_stop != position.get('trailing_stop'):
                        self.position_manager.update_trailing_stop(position_id, new_trailing_stop)
                        actions.append({
                            'action': 'TRAILING_STOP_UPDATE',
                            'position_id': position_id,
                            'new_stop': new_trailing_stop,
                            'timestamp': current_time
                        })
                
            except Exception as e:
                self.logger.error(f"Error managing position {position_id}: {e}")
        
        # Close positions that need to be closed
        for position_id, reason, exit_type in positions_to_close:
            try:
                position = self.position_manager.positions[position_id]
                
                # Determine close size based on exit type
                if exit_type in ['TAKE_PROFIT_1']:
                    # Close 50% at first TP
                    close_size = position['original_size'] * self.risk_config['tp1_position_percent']
                elif exit_type in ['TAKE_PROFIT_2']:
                    # Close 30% at second TP  
                    close_size = position['original_size'] * self.risk_config['tp2_position_percent']
                else:
                    # Close entire position
                    close_size = position['current_size']
                
                # Execute close through MT5 if available
                if self.mt5_interface:
                    close_result = self._close_mt5_position(position_id, close_size, current_price)
                    if not close_result['success']:
                        self.logger.error(f"MT5 close failed: {close_result['error']}")
                        continue
                
                # Record the close
                partial_close = self.position_manager.close_partial_position(
                    position_id, close_size, current_price, current_time, reason
                )
                
                actions.append({
                    'action': 'POSITION_CLOSE',
                    'position_id': position_id,
                    'close_type': exit_type,
                    'close_size': close_size,
                    'exit_price': current_price,
                    'pnl': partial_close.get('pnl', 0),
                    'reason': reason,
                    'timestamp': current_time
                })
                
                # Log the exit
                trade_log_entry = {
                    'timestamp': current_time,
                    'position_id': position_id,
                    'symbol': self.symbol,
                    'action': 'EXIT',
                    'exit_type': exit_type,
                    'exit_price': current_price,
                    'close_size': close_size,
                    'pnl': partial_close.get('pnl', 0),
                    'reason': reason
                }
                
                self.trade_log.append(trade_log_entry)
                
            except Exception as e:
                self.logger.error(f"Error closing position {position_id}: {e}")
        
        return actions
    
    def get_strategy_status(self) -> Dict[str, Any]:
        """
        Get comprehensive strategy status and performance
        
        Returns:
            Dictionary with strategy status information
        """
        position_stats = self.position_manager.get_position_statistics()
        
        status = {
            'timestamp': datetime.now(),
            'symbol': self.symbol,
            'strategy_name': 'Momentum Breakout Pro',
            'account_balance': self.account_balance,
            'current_drawdown': self.current_drawdown,
            'daily_pnl': self.daily_pnl,
            'open_positions': len(self.position_manager.positions),
            'position_statistics': position_stats,
            'last_signal_time': self.last_signal_time,
            'total_trades': len(self.trade_log),
            'data_status': {
                '15m_bars': len(self.data_15m),
                '1h_bars': len(self.data_1h),
                '4h_bars': len(self.data_4h),
                'last_update': self.data_15m.index[-1] if not self.data_15m.empty else None
            }
        }
        
        # Add current market price if available
        if not self.data_15m.empty:
            status['current_price'] = self.data_15m['close'].iloc[-1]
        
        return status
    
    def _assess_market_conditions(self) -> Dict[str, str]:
        """Assess current market conditions"""
        
        conditions = {
            'market_condition': 'unknown',
            'volatility_regime': 'unknown', 
            'trend_direction': 'unknown'
        }
        
        try:
            if len(self.data_15m) < 50:
                return conditions
            
            # Calculate indicators for market assessment
            from .indicators import BreakoutIndicators
            
            # Volatility assessment using ATR
            atr = BreakoutIndicators.calculate_atr(
                self.data_15m['high'], self.data_15m['low'], self.data_15m['close']
            )
            
            current_atr = atr.iloc[-1]
            avg_atr = atr.tail(20).mean()
            
            if current_atr > avg_atr * 1.3:
                conditions['volatility_regime'] = 'high'
            elif current_atr < avg_atr * 0.7:
                conditions['volatility_regime'] = 'low'
            else:
                conditions['volatility_regime'] = 'normal'
            
            # Trend assessment using EMAs
            ema_20 = BreakoutIndicators.calculate_ema(self.data_15m['close'], 20)
            ema_50 = BreakoutIndicators.calculate_ema(self.data_15m['close'], 50)
            
            current_price = self.data_15m['close'].iloc[-1]
            current_ema_20 = ema_20.iloc[-1]
            current_ema_50 = ema_50.iloc[-1]
            
            if current_price > current_ema_20 > current_ema_50:
                conditions['trend_direction'] = 'bullish'
            elif current_price < current_ema_20 < current_ema_50:
                conditions['trend_direction'] = 'bearish'
            else:
                conditions['trend_direction'] = 'sideways'
            
            # Overall market condition
            if conditions['volatility_regime'] == 'low' and conditions['trend_direction'] == 'sideways':
                conditions['market_condition'] = 'consolidating'
            elif conditions['volatility_regime'] == 'high' and conditions['trend_direction'] in ['bullish', 'bearish']:
                conditions['market_condition'] = 'trending'
            else:
                conditions['market_condition'] = 'transitional'
                
        except Exception as e:
            self.logger.error(f"Error assessing market conditions: {e}")
        
        return conditions
    
    def _update_open_positions(self, current_price: float) -> None:
        """Update unrealized P&L for open positions"""
        try:
            current_prices = {self.symbol: current_price}
            self.position_manager.update_positions(current_prices)
            
            # Update daily P&L and drawdown
            self._update_account_metrics()
            
        except Exception as e:
            self.logger.error(f"Error updating positions: {e}")
    
    def _update_account_metrics(self) -> None:
        """Update account-level metrics"""
        try:
            position_stats = self.position_manager.get_position_statistics()
            
            # Update daily P&L (simplified - should track from start of day)
            self.daily_pnl = position_stats.get('total_pnl', 0)
            
            # Update drawdown (simplified calculation)
            if position_stats.get('total_pnl', 0) < 0:
                self.current_drawdown = abs(position_stats['total_pnl']) / self.account_balance
            else:
                self.current_drawdown = 0
                
        except Exception as e:
            self.logger.error(f"Error updating account metrics: {e}")
    
    def _execute_mt5_trade(self, direction: str, price: float, size: float, 
                          stop_loss: float, take_profit_levels: Dict[str, float]) -> Dict[str, Any]:
        """Execute trade through MT5 interface (placeholder)"""
        
        # This would integrate with actual MT5 interface
        # For now, return success for backtesting
        return {
            'success': True,
            'order_id': f"MT5_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'executed_price': price,
            'executed_size': size
        }
    
    def _close_mt5_position(self, position_id: str, size: float, price: float) -> Dict[str, Any]:
        """Close position through MT5 interface (placeholder)"""
        
        # This would integrate with actual MT5 interface
        return {
            'success': True,
            'close_price': price,
            'closed_size': size
        }