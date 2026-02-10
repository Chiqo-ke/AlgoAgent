import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
from .indicators import BreakoutIndicators

class AdvancedRiskManager:
    """Advanced risk management for Momentum Breakout Pro strategy"""
    
    def __init__(self, risk_config: dict, symbol_configs: dict):
        self.risk_config = risk_config
        self.symbol_configs = symbol_configs
        self.logger = logging.getLogger(__name__)
    
    def calculate_position_size(self, symbol: str, account_balance: float, 
                              entry_price: float, stop_loss_price: float) -> float:
        """
        Calculate optimal position size based on risk percentage and volatility
        
        Args:
            symbol: Trading symbol
            account_balance: Current account balance
            entry_price: Planned entry price
            stop_loss_price: Stop loss price
            
        Returns:
            Position size in units (lots for forex, shares for stocks)
        """
        risk_amount = account_balance * self.risk_config['risk_per_trade']
        price_diff = abs(entry_price - stop_loss_price)
        
        symbol_config = self.symbol_configs.get(symbol, {})
        point_value = symbol_config.get('point_value', 0.0001)
        
        if price_diff <= 0:
            self.logger.warning(f"Invalid price difference for {symbol}: {price_diff}")
            return 0
        
        try:
            if symbol == 'EURUSD':
                # Forex position sizing
                # Risk per pip = Risk amount / (Stop loss in pips)
                stop_loss_pips = price_diff / point_value
                risk_per_pip = risk_amount / stop_loss_pips
                
                # Standard lot size is 100,000 units, mini lot is 10,000
                # For EURUSD, 1 pip on 1 standard lot = $10
                pip_value_per_lot = 10  # For EURUSD
                position_size = risk_per_pip / pip_value_per_lot
                
                # Round to mini lots (0.01)
                position_size = round(position_size, 2)
                position_size = max(0.01, min(position_size, 100))  # Min 0.01, Max 100 lots
                
            else:
                # Stock position sizing  
                # Number of shares = Risk amount / Price difference per share
                position_size = risk_amount / price_diff
                
                # Round to whole shares
                position_size = int(position_size)
                position_size = max(1, min(position_size, 10000))  # Min 1 share, Max 10,000 shares
            
            self.logger.info(f"Position size for {symbol}: {position_size} "
                           f"(Risk: ${risk_amount:.2f}, Price diff: {price_diff:.5f})")
            
            return position_size
            
        except Exception as e:
            self.logger.error(f"Error calculating position size for {symbol}: {e}")
            return 0
    
    def calculate_stop_loss(self, symbol: str, entry_price: float, direction: str, 
                          atr_value: float, data: pd.DataFrame) -> float:
        """
        Calculate dynamic stop loss using ATR and minimum/maximum constraints
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            direction: 'long' or 'short'
            atr_value: Current ATR value
            data: Recent price data for validation
            
        Returns:
            Stop loss price
        """
        symbol_config = self.symbol_configs.get(symbol, {})
        
        # Base stop loss using ATR
        atr_stop_distance = atr_value * self.risk_config['stop_loss_atr_multiplier']
        
        # Apply minimum and maximum constraints
        if symbol == 'EURUSD':
            min_stop_distance = entry_price * self.risk_config['min_stop_loss_percent']
        else:
            min_stop_distance = entry_price * self.risk_config['min_stop_loss_percent_stocks']
        
        max_stop_distance = entry_price * self.risk_config['max_stop_loss_percent']
        
        # Use the larger of ATR-based or minimum stop
        stop_distance = max(atr_stop_distance, min_stop_distance)
        stop_distance = min(stop_distance, max_stop_distance)
        
        if direction.lower() == 'long':
            stop_loss = entry_price - stop_distance
        else:  # short
            stop_loss = entry_price + stop_distance
        
        # Validate stop loss doesn't conflict with recent price action
        stop_loss = self._validate_stop_loss(symbol, stop_loss, direction, data)
        
        self.logger.info(f"Stop loss for {symbol} {direction}: {stop_loss:.5f} "
                        f"(Distance: {stop_distance:.5f}, ATR: {atr_value:.5f})")
        
        return stop_loss
    
    def calculate_take_profit_levels(self, entry_price: float, stop_loss_price: float, 
                                   direction: str) -> Dict[str, float]:
        """
        Calculate multiple take profit levels
        
        Args:
            entry_price: Entry price
            stop_loss_price: Stop loss price
            direction: 'long' or 'short'
            
        Returns:
            Dictionary with take profit levels
        """
        risk_distance = abs(entry_price - stop_loss_price)
        
        tp_levels = {}
        
        if direction.lower() == 'long':
            tp_levels['tp1'] = entry_price + (risk_distance * self.risk_config['tp1_ratio'])
            tp_levels['tp2'] = entry_price + (risk_distance * self.risk_config['tp2_ratio'])
        else:  # short
            tp_levels['tp1'] = entry_price - (risk_distance * self.risk_config['tp1_ratio'])
            tp_levels['tp2'] = entry_price - (risk_distance * self.risk_config['tp2_ratio'])
        
        self.logger.info(f"Take profit levels: TP1={tp_levels['tp1']:.5f}, TP2={tp_levels['tp2']:.5f}")
        
        return tp_levels
    
    def calculate_trailing_stop(self, symbol: str, entry_price: float, current_price: float,
                              direction: str, atr_value: float, current_trailing_stop: float = None) -> float:
        """
        Calculate trailing stop loss
        
        Args:
            symbol: Trading symbol
            entry_price: Original entry price
            current_price: Current market price
            direction: 'long' or 'short'
            atr_value: Current ATR value
            current_trailing_stop: Current trailing stop level
            
        Returns:
            New trailing stop price
        """
        trailing_distance = atr_value * self.risk_config['tp3_trailing_atr']
        
        if direction.lower() == 'long':
            # Only move trailing stop up
            new_trailing_stop = current_price - trailing_distance
            if current_trailing_stop is None:
                return new_trailing_stop
            else:
                return max(new_trailing_stop, current_trailing_stop)
        else:  # short
            # Only move trailing stop down
            new_trailing_stop = current_price + trailing_distance
            if current_trailing_stop is None:
                return new_trailing_stop
            else:
                return min(new_trailing_stop, current_trailing_stop)
    
    def validate_trade_risk(self, symbol: str, signal_strength: float, current_positions: int,
                           account_balance: float, current_drawdown: float) -> Tuple[bool, List[str]]:
        """
        Comprehensive trade validation including portfolio risk
        
        Args:
            symbol: Trading symbol
            signal_strength: Signal strength (0-1)
            current_positions: Current number of positions
            account_balance: Current account balance
            current_drawdown: Current portfolio drawdown
            
        Returns:
            Tuple of (is_valid, list_of_reasons)
        """
        validation_reasons = []
        is_valid = True
        
        # Check maximum positions
        if current_positions >= self.risk_config['max_positions']:
            is_valid = False
            validation_reasons.append(f"Maximum positions reached: {current_positions}/{self.risk_config['max_positions']}")
        
        # Check symbol-specific position limit
        symbol_positions = self._count_symbol_positions(symbol, current_positions)
        if symbol_positions >= self.risk_config['max_symbol_positions']:
            is_valid = False
            validation_reasons.append(f"Maximum {symbol} positions reached: {symbol_positions}")
        
        # Check drawdown limits
        if current_drawdown >= self.risk_config['max_drawdown_percent']:
            is_valid = False
            validation_reasons.append(f"Maximum drawdown exceeded: {current_drawdown:.2%}")
        
        # Check signal strength threshold
        min_signal_strength = 0.4  # Minimum 40% signal strength
        if signal_strength < min_signal_strength:
            is_valid = False
            validation_reasons.append(f"Signal strength too low: {signal_strength:.2f} < {min_signal_strength}")
        
        # Check account balance
        min_balance = 1000  # Minimum $1000 account balance
        if account_balance < min_balance:
            is_valid = False
            validation_reasons.append(f"Account balance too low: ${account_balance:.2f}")
        
        # Check trading session (symbol-specific)
        if not self._is_trading_session_valid(symbol):
            is_valid = False
            validation_reasons.append(f"Outside trading session for {symbol}")
        
        if is_valid:
            validation_reasons.append("All risk criteria passed")
            
        return is_valid, validation_reasons
    
    def should_close_position(self, position: dict, current_price: float, current_atr: float,
                            current_time: datetime) -> Tuple[bool, str, str]:
        """
        Determine if position should be closed with reason and exit type
        
        Args:
            position: Position dictionary with entry details
            current_price: Current market price
            current_atr: Current ATR value
            current_time: Current timestamp
            
        Returns:
            Tuple of (should_close, reason, exit_type)
        """
        entry_price = position.get('entry_price', 0)
        stop_loss = position.get('stop_loss', 0)
        take_profit_levels = position.get('take_profit_levels', {})
        direction = position.get('direction', 'long')
        entry_time = position.get('entry_time')
        trailing_stop = position.get('trailing_stop')
        symbol = position.get('symbol', '')
        
        # Check stop loss
        if direction.lower() == 'long':
            if stop_loss > 0 and current_price <= stop_loss:
                return True, f"Stop loss hit at {stop_loss:.5f}", "STOP_LOSS"
            if trailing_stop and current_price <= trailing_stop:
                return True, f"Trailing stop hit at {trailing_stop:.5f}", "TRAILING_STOP"
        else:  # short
            if stop_loss > 0 and current_price >= stop_loss:
                return True, f"Stop loss hit at {stop_loss:.5f}", "STOP_LOSS"
            if trailing_stop and current_price >= trailing_stop:
                return True, f"Trailing stop hit at {trailing_stop:.5f}", "TRAILING_STOP"
        
        # Check take profit levels
        if 'tp1' in take_profit_levels:
            tp1 = take_profit_levels['tp1']
            if direction.lower() == 'long':
                if current_price >= tp1:
                    return True, f"Take profit 1 hit at {tp1:.5f}", "TAKE_PROFIT_1"
            else:
                if current_price <= tp1:
                    return True, f"Take profit 1 hit at {tp1:.5f}", "TAKE_PROFIT_1"
        
        if 'tp2' in take_profit_levels:
            tp2 = take_profit_levels['tp2']
            if direction.lower() == 'long':
                if current_price >= tp2:
                    return True, f"Take profit 2 hit at {tp2:.5f}", "TAKE_PROFIT_2"
            else:
                if current_price <= tp2:
                    return True, f"Take profit 2 hit at {tp2:.5f}", "TAKE_PROFIT_2"
        
        # Check maximum hold time
        if entry_time and self.risk_config['max_hold_hours'] > 0:
            time_diff = current_time - entry_time
            if time_diff.total_seconds() > self.risk_config['max_hold_hours'] * 3600:
                return True, f"Maximum hold time exceeded ({self.risk_config['max_hold_hours']}h)", "TIME_EXIT"
        
        # Check Friday close rule
        if self.risk_config['friday_close_enabled']:
            if current_time.weekday() == 4:  # Friday
                if symbol == 'EURUSD':
                    # Close forex positions before 21:00 UTC Friday
                    if current_time.hour >= 21:
                        return True, "Friday close rule", "FRIDAY_CLOSE"
                else:
                    # Close stock positions before market close Friday
                    if current_time.hour >= 20:  # 4 PM EST = 20 UTC
                        return True, "Friday close rule", "FRIDAY_CLOSE"
        
        return False, "", ""
    
    def _validate_stop_loss(self, symbol: str, stop_loss: float, direction: str, 
                          data: pd.DataFrame) -> float:
        """Validate and adjust stop loss based on recent price action"""
        
        if len(data) < 5:
            return stop_loss
        
        recent_data = data.tail(20)  # Last 20 periods
        
        if direction.lower() == 'long':
            # For long positions, ensure stop is below recent significant lows
            recent_low = recent_data['low'].min()
            if stop_loss >= recent_low:
                # Adjust stop to be slightly below recent low
                buffer = recent_low * 0.001  # 0.1% buffer
                adjusted_stop = recent_low - buffer
                self.logger.info(f"Adjusted long stop loss from {stop_loss:.5f} to {adjusted_stop:.5f}")
                return adjusted_stop
        else:
            # For short positions, ensure stop is above recent significant highs
            recent_high = recent_data['high'].max()
            if stop_loss <= recent_high:
                # Adjust stop to be slightly above recent high
                buffer = recent_high * 0.001  # 0.1% buffer
                adjusted_stop = recent_high + buffer
                self.logger.info(f"Adjusted short stop loss from {stop_loss:.5f} to {adjusted_stop:.5f}")
                return adjusted_stop
        
        return stop_loss
    
    def _count_symbol_positions(self, symbol: str, current_positions: int) -> int:
        """Count positions for specific symbol (placeholder)"""
        # This would integrate with actual position tracking system
        return 0  # Simplified for now
    
    def _is_trading_session_valid(self, symbol: str) -> bool:
        """Check if current time is within valid trading session"""
        current_time = datetime.utcnow()
        current_hour = current_time.hour + (current_time.minute / 60)
        
        symbol_config = self.symbol_configs.get(symbol, {})
        
        if symbol == 'EURUSD':
            # Forex trading - check for optimal session times
            trading_hours = symbol_config.get('trading_hours', {'start': 12, 'end': 16})
            return trading_hours['start'] <= current_hour <= trading_hours['end']
        else:
            # Stock trading - check for market hours
            trading_hours = symbol_config.get('trading_hours', {'start': 14.5, 'end': 20.5})
            
            # Avoid first 30 minutes if configured
            if current_hour < trading_hours['start'] + 0.5:  # 30 minutes
                return False
                
            return trading_hours['start'] <= current_hour <= trading_hours['end']

class PositionManager:
    """Enhanced position management with partial closes and scaling"""
    
    def __init__(self, risk_config: dict):
        self.risk_config = risk_config
        self.positions: Dict[str, dict] = {}
        self.trade_history: List[dict] = []
        self.logger = logging.getLogger(__name__)
    
    def open_position(self, symbol: str, direction: str, entry_price: float,
                     position_size: float, stop_loss: float, take_profit_levels: Dict[str, float],
                     signal_data: dict, timestamp: datetime) -> str:
        """
        Open a new position with advanced tracking
        
        Args:
            symbol: Trading symbol
            direction: 'long' or 'short'
            entry_price: Entry price
            position_size: Full position size
            stop_loss: Stop loss price
            take_profit_levels: Dictionary of take profit levels
            signal_data: Original signal information
            timestamp: Entry timestamp
            
        Returns:
            Position ID
        """
        position_id = f"{symbol}_{direction}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        position = {
            'id': position_id,
            'symbol': symbol,
            'direction': direction,
            'entry_price': entry_price,
            'original_size': position_size,
            'current_size': position_size,
            'stop_loss': stop_loss,
            'take_profit_levels': take_profit_levels,
            'trailing_stop': None,
            'entry_time': timestamp,
            'status': 'open',
            'unrealized_pnl': 0.0,
            'realized_pnl': 0.0,
            'partial_closes': [],
            'signal_data': signal_data,
            'max_favorable_excursion': 0.0,
            'max_adverse_excursion': 0.0,
        }
        
        self.positions[position_id] = position
        
        self.logger.info(f"Opened {direction} position: {position_id} "
                        f"@ {entry_price:.5f}, Size: {position_size}, "
                        f"SL: {stop_loss:.5f}, TPs: {take_profit_levels}")
        
        return position_id
    
    def close_partial_position(self, position_id: str, close_size: float, exit_price: float,
                             timestamp: datetime, reason: str = "") -> dict:
        """
        Close part of a position
        
        Args:
            position_id: Position ID
            close_size: Size to close
            exit_price: Exit price
            timestamp: Exit timestamp
            reason: Reason for closing
            
        Returns:
            Partial close information
        """
        if position_id not in self.positions:
            self.logger.error(f"Position {position_id} not found")
            return {}
        
        position = self.positions[position_id]
        
        if close_size > position['current_size']:
            close_size = position['current_size']
        
        # Calculate P&L for this partial close
        partial_pnl = self._calculate_pnl_for_size(position, exit_price, close_size)
        
        # Record partial close
        partial_close = {
            'size': close_size,
            'exit_price': exit_price,
            'exit_time': timestamp,
            'pnl': partial_pnl,
            'reason': reason
        }
        
        position['partial_closes'].append(partial_close)
        position['current_size'] -= close_size
        position['realized_pnl'] += partial_pnl
        
        self.logger.info(f"Partial close: {position_id}, Size: {close_size}, "
                        f"Price: {exit_price:.5f}, P&L: {partial_pnl:.2f}, Reason: {reason}")
        
        # If position is fully closed, move to history
        if position['current_size'] <= 0:
            position['status'] = 'closed'
            position['exit_time'] = timestamp
            self.trade_history.append(position.copy())
            del self.positions[position_id]
        
        return partial_close
    
    def update_trailing_stop(self, position_id: str, new_trailing_stop: float) -> bool:
        """Update trailing stop for a position"""
        if position_id in self.positions:
            old_stop = self.positions[position_id].get('trailing_stop')
            self.positions[position_id]['trailing_stop'] = new_trailing_stop
            
            self.logger.info(f"Updated trailing stop for {position_id}: "
                           f"{old_stop} -> {new_trailing_stop:.5f}")
            return True
        return False
    
    def update_mfe_mae(self, position_id: str, current_price: float) -> None:
        """Update Maximum Favorable/Adverse Excursion"""
        if position_id not in self.positions:
            return
        
        position = self.positions[position_id]
        entry_price = position['entry_price']
        direction = position['direction']
        
        if direction.lower() == 'long':
            # For long positions
            favorable_move = max(0, current_price - entry_price)
            adverse_move = max(0, entry_price - current_price)
        else:
            # For short positions  
            favorable_move = max(0, entry_price - current_price)
            adverse_move = max(0, current_price - entry_price)
        
        position['max_favorable_excursion'] = max(
            position['max_favorable_excursion'], favorable_move
        )
        position['max_adverse_excursion'] = max(
            position['max_adverse_excursion'], adverse_move
        )
    
    def get_position_statistics(self) -> Dict[str, Any]:
        """Get comprehensive position statistics"""
        total_trades = len(self.trade_history)
        
        if total_trades == 0:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0,
                'total_pnl': 0,
                'avg_mfe': 0,
                'avg_mae': 0
            }
        
        pnls = [trade['realized_pnl'] for trade in self.trade_history if 'realized_pnl' in trade]
        winning_trades = [pnl for pnl in pnls if pnl > 0]
        losing_trades = [pnl for pnl in pnls if pnl < 0]
        
        mfe_values = [trade.get('max_favorable_excursion', 0) for trade in self.trade_history]
        mae_values = [trade.get('max_adverse_excursion', 0) for trade in self.trade_history]
        
        total_wins = sum(winning_trades) if winning_trades else 0
        total_losses = abs(sum(losing_trades)) if losing_trades else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / total_trades * 100 if total_trades > 0 else 0,
            'avg_win': np.mean(winning_trades) if winning_trades else 0,
            'avg_loss': np.mean(losing_trades) if losing_trades else 0,
            'profit_factor': total_wins / total_losses if total_losses > 0 else float('inf') if total_wins > 0 else 0,
            'total_pnl': sum(pnls),
            'avg_mfe': np.mean(mfe_values) if mfe_values else 0,
            'avg_mae': np.mean(mae_values) if mae_values else 0,
            'largest_win': max(pnls) if pnls else 0,
            'largest_loss': min(pnls) if pnls else 0,
            'current_positions': len(self.positions)
        }
    
    def _calculate_pnl_for_size(self, position: dict, current_price: float, size: float) -> float:
        """Calculate P&L for a specific position size"""
        entry_price = position['entry_price']
        direction = position['direction']
        symbol = position['symbol']
        
        if direction.lower() == 'long':
            price_diff = current_price - entry_price
        else:  # short
            price_diff = entry_price - current_price
        
        if symbol == 'EURUSD':
            # Forex P&L calculation (assuming EURUSD)
            pnl = price_diff * size * 100000  # Standard lot size
        else:
            # Stock P&L calculation
            pnl = price_diff * size
        
        return pnl