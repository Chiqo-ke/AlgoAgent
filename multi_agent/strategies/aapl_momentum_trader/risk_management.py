import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

class RiskManager:
    """Risk management for trading positions"""
    
    def __init__(self, risk_per_trade: float = 0.02, max_positions: int = 1, 
                 stop_loss_pips: int = 100, take_profit_ratio: float = 2.0,
                 max_spread: int = 5):
        self.risk_per_trade = risk_per_trade
        self.max_positions = max_positions
        self.stop_loss_pips = stop_loss_pips
        self.take_profit_ratio = take_profit_ratio
        self.max_spread = max_spread
        self.logger = logging.getLogger(__name__)
    
    def calculate_position_size(self, account_balance: float, entry_price: float, 
                              stop_loss_price: float, symbol_info: dict) -> float:
        """
        Calculate position size based on risk percentage
        
        Args:
            account_balance: Current account balance
            entry_price: Entry price for the trade
            stop_loss_price: Stop loss price
            symbol_info: Symbol information (point, tick_value, etc.)
            
        Returns:
            Position size in lots
        """
        risk_amount = account_balance * self.risk_per_trade
        price_diff = abs(entry_price - stop_loss_price)
        
        # Get symbol point and tick value
        point = symbol_info.get('point', 0.0001)
        tick_value = symbol_info.get('trade_tick_value', 1.0)
        volume_step = symbol_info.get('volume_step', 0.01)
        min_volume = symbol_info.get('minimum_volume', 0.01)
        max_volume = symbol_info.get('maximum_volume', 100.0)
        
        # Calculate position size
        pips_at_risk = price_diff / point
        value_per_pip = tick_value
        
        if pips_at_risk > 0 and value_per_pip > 0:
            position_size = risk_amount / (pips_at_risk * value_per_pip)
            
            # Round to volume step
            position_size = round(position_size / volume_step) * volume_step
            
            # Apply limits
            position_size = max(min_volume, min(position_size, max_volume))
            
            self.logger.info(f"Calculated position size: {position_size} lots "
                           f"(Risk: ${risk_amount:.2f}, Pips at risk: {pips_at_risk:.1f})")
            
            return position_size
        
        self.logger.warning("Invalid parameters for position size calculation")
        return min_volume
    
    def calculate_stop_loss(self, entry_price: float, direction: str, 
                          atr: float = None, use_atr: bool = True) -> float:
        """
        Calculate stop loss price
        
        Args:
            entry_price: Entry price
            direction: 'long' or 'short'
            atr: Average True Range value
            use_atr: Whether to use ATR for dynamic stop loss
            
        Returns:
            Stop loss price
        """
        if use_atr and atr is not None and atr > 0:
            # Dynamic stop loss based on ATR
            stop_distance = atr * 1.5  # 1.5x ATR
        else:
            # Fixed stop loss in pips
            point = 0.0001 if 'JPY' not in str(entry_price) else 0.01
            stop_distance = self.stop_loss_pips * point
        
        if direction.lower() == 'long':
            stop_loss = entry_price - stop_distance
        else:  # short
            stop_loss = entry_price + stop_distance
        
        self.logger.info(f"Stop loss calculated: {stop_loss:.5f} "
                        f"(Distance: {stop_distance:.5f})")
        
        return stop_loss
    
    def calculate_take_profit(self, entry_price: float, stop_loss_price: float, 
                            direction: str) -> float:
        """
        Calculate take profit price based on risk-reward ratio
        
        Args:
            entry_price: Entry price
            stop_loss_price: Stop loss price
            direction: 'long' or 'short'
            
        Returns:
            Take profit price
        """
        risk_distance = abs(entry_price - stop_loss_price)
        profit_distance = risk_distance * self.take_profit_ratio
        
        if direction.lower() == 'long':
            take_profit = entry_price + profit_distance
        else:  # short
            take_profit = entry_price - profit_distance
        
        self.logger.info(f"Take profit calculated: {take_profit:.5f} "
                        f"(R:R = 1:{self.take_profit_ratio})")
        
        return take_profit
    
    def validate_trade(self, signal_strength: float, spread: float, 
                      current_positions: int) -> Tuple[bool, str]:
        """
        Validate if trade should be executed
        
        Args:
            signal_strength: Strength of the signal (0-1)
            spread: Current spread in pips
            current_positions: Number of current open positions
            
        Returns:
            Tuple of (is_valid, reason)
        """
        # Check maximum positions
        if current_positions >= self.max_positions:
            return False, f"Maximum positions reached ({self.max_positions})"
        
        # Check spread
        if spread > self.max_spread:
            return False, f"Spread too high: {spread} > {self.max_spread} pips"
        
        # Check signal strength (minimum 0.3 for execution)
        if signal_strength < 0.3:
            return False, f"Signal strength too low: {signal_strength:.2f}"
        
        return True, "Trade validated"
    
    def should_close_position(self, position: dict, current_price: float, 
                            current_time: datetime) -> Tuple[bool, str]:
        """
        Determine if position should be closed
        
        Args:
            position: Position information
            current_price: Current market price
            current_time: Current time
            
        Returns:
            Tuple of (should_close, reason)
        """
        entry_price = position.get('entry_price', 0)
        stop_loss = position.get('stop_loss', 0)
        take_profit = position.get('take_profit', 0)
        direction = position.get('direction', 'long')
        entry_time = position.get('entry_time')
        
        # Check stop loss
        if direction.lower() == 'long':
            if current_price <= stop_loss:
                return True, "Stop loss hit"
            if take_profit > 0 and current_price >= take_profit:
                return True, "Take profit hit"
        else:  # short
            if current_price >= stop_loss:
                return True, "Stop loss hit"
            if take_profit > 0 and current_price <= take_profit:
                return True, "Take profit hit"
        
        # Check time-based exit (optional)
        if entry_time:
            time_diff = current_time - entry_time
            if time_diff.total_seconds() > 86400:  # 24 hours
                return True, "Time-based exit (24h)"
        
        return False, ""

class PositionManager:
    """Manage trading positions"""
    
    def __init__(self):
        self.positions: Dict[str, dict] = {}
        self.trade_history: List[dict] = []
        self.logger = logging.getLogger(__name__)
    
    def open_position(self, symbol: str, direction: str, entry_price: float,
                     volume: float, stop_loss: float, take_profit: float,
                     timestamp: datetime) -> str:
        """
        Open a new position
        
        Args:
            symbol: Trading symbol
            direction: 'long' or 'short'
            entry_price: Entry price
            volume: Position size
            stop_loss: Stop loss price
            take_profit: Take profit price
            timestamp: Entry timestamp
            
        Returns:
            Position ID
        """
        position_id = f"{symbol}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        position = {
            'id': position_id,
            'symbol': symbol,
            'direction': direction,
            'entry_price': entry_price,
            'volume': volume,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'entry_time': timestamp,
            'status': 'open',
            'unrealized_pnl': 0.0
        }
        
        self.positions[position_id] = position
        
        self.logger.info(f"Opened {direction} position: {position_id} "
                        f"@ {entry_price:.5f}, SL: {stop_loss:.5f}, "
                        f"TP: {take_profit:.5f}")
        
        return position_id
    
    def close_position(self, position_id: str, exit_price: float, 
                      timestamp: datetime, reason: str = "") -> dict:
        """
        Close an existing position
        
        Args:
            position_id: Position ID
            exit_price: Exit price
            timestamp: Exit timestamp
            reason: Reason for closing
            
        Returns:
            Closed position information
        """
        if position_id not in self.positions:
            self.logger.error(f"Position {position_id} not found")
            return {}
        
        position = self.positions[position_id].copy()
        position['exit_price'] = exit_price
        position['exit_time'] = timestamp
        position['status'] = 'closed'
        position['close_reason'] = reason
        
        # Calculate P&L
        pnl = self._calculate_pnl(position, exit_price)
        position['realized_pnl'] = pnl
        
        # Add to trade history
        self.trade_history.append(position)
        
        # Remove from active positions
        del self.positions[position_id]
        
        self.logger.info(f"Closed position: {position_id} @ {exit_price:.5f}, "
                        f"P&L: {pnl:.2f}, Reason: {reason}")
        
        return position
    
    def update_positions(self, current_prices: dict) -> None:
        """Update unrealized P&L for open positions"""
        for position_id, position in self.positions.items():
            symbol = position['symbol']
            if symbol in current_prices:
                current_price = current_prices[symbol]
                pnl = self._calculate_pnl(position, current_price)
                position['unrealized_pnl'] = pnl
    
    def _calculate_pnl(self, position: dict, current_price: float) -> float:
        """Calculate profit/loss for a position"""
        entry_price = position['entry_price']
        volume = position['volume']
        direction = position['direction']
        
        if direction.lower() == 'long':
            pnl = (current_price - entry_price) * volume * 100000  # Assuming forex lot size
        else:  # short
            pnl = (entry_price - current_price) * volume * 100000
        
        return pnl
    
    def get_open_positions(self) -> Dict[str, dict]:
        """Get all open positions"""
        return self.positions.copy()
    
    def get_position_count(self) -> int:
        """Get number of open positions"""
        return len(self.positions)
    
    def get_trade_history(self) -> List[dict]:
        """Get trade history"""
        return self.trade_history.copy()
    
    def get_statistics(self) -> dict:
        """Calculate trading statistics"""
        if not self.trade_history:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'average_win': 0.0,
                'average_loss': 0.0,
                'profit_factor': 0.0,
                'largest_win': 0.0,
                'largest_loss': 0.0
            }
        
        closed_trades = [t for t in self.trade_history if t.get('realized_pnl') is not None]
        
        if not closed_trades:
            return {'total_trades': len(self.trade_history)}
        
        pnls = [trade['realized_pnl'] for trade in closed_trades]
        winning_trades = [pnl for pnl in pnls if pnl > 0]
        losing_trades = [pnl for pnl in pnls if pnl < 0]
        
        total_pnl = sum(pnls)
        total_wins = sum(winning_trades) if winning_trades else 0
        total_losses = abs(sum(losing_trades)) if losing_trades else 0
        
        return {
            'total_trades': len(closed_trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / len(closed_trades) * 100 if closed_trades else 0,
            'total_pnl': total_pnl,
            'average_win': np.mean(winning_trades) if winning_trades else 0,
            'average_loss': np.mean(losing_trades) if losing_trades else 0,
            'profit_factor': total_wins / total_losses if total_losses > 0 else 0,
            'largest_win': max(pnls) if pnls else 0,
            'largest_loss': min(pnls) if pnls else 0
        }