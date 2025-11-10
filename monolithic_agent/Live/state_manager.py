"""
State Manager - Track positions, orders, and trading state
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from collections import defaultdict
import logging

logger = logging.getLogger('LiveTrader.StateManager')


class StateManager:
    """
    Manages live trading state including positions, daily limits, and synchronization
    """
    
    def __init__(self, config):
        """
        Initialize state manager
        
        Args:
            config: Live trading configuration
        """
        self.config = config
        
        # Position tracking
        self.positions = {}  # symbol -> position dict
        self.position_history = []  # List of all position changes
        
        # Daily limits tracking
        self.daily_trades = defaultdict(int)  # date -> trade count
        self.daily_pnl = defaultdict(float)  # date -> P&L
        
        # Signal tracking
        self.last_signal_time = {}  # symbol -> timestamp
        self.processed_signals = set()  # Set of processed signal IDs
        
        # Trading state
        self.is_trading_enabled = True
        self.kill_switch_active = False
        
        logger.info("StateManager initialized")
    
    def sync_with_mt5(self, mt5_positions: List[Dict[str, Any]]):
        """
        Synchronize internal state with MT5 positions
        
        Args:
            mt5_positions: List of position dicts from MT5
        """
        logger.info(f"Synchronizing state with {len(mt5_positions)} MT5 positions")
        
        # Clear current positions
        self.positions = {}
        
        # Rebuild from MT5
        for pos in mt5_positions:
            symbol = pos['symbol']
            self.positions[symbol] = {
                'ticket': pos['ticket'],
                'symbol': symbol,
                'type': pos['type'],
                'volume': pos['volume'],
                'price_open': pos['price_open'],
                'price_current': pos['price_current'],
                'sl': pos['sl'],
                'tp': pos['tp'],
                'profit': pos['profit'],
                'open_time': pos['time'],
                'magic': pos['magic']
            }
        
        logger.info(f"✓ Synced {len(self.positions)} positions")
    
    def has_position(self, symbol: str) -> bool:
        """Check if we have an open position for symbol"""
        return symbol in self.positions
    
    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get position for symbol"""
        return self.positions.get(symbol)
    
    def update_position(self, symbol: str, position_data: Dict[str, Any]):
        """Update position data"""
        if symbol in self.positions:
            self.positions[symbol].update(position_data)
        else:
            self.positions[symbol] = position_data
        
        # Record in history
        self.position_history.append({
            'timestamp': datetime.now(),
            'action': 'UPDATE',
            'symbol': symbol,
            'data': position_data.copy()
        })
    
    def close_position(self, symbol: str, close_data: Dict[str, Any]):
        """
        Record position closure
        
        Args:
            symbol: Trading symbol
            close_data: Closure details (price, profit, etc.)
        """
        if symbol in self.positions:
            position = self.positions[symbol]
            
            # Record in history
            self.position_history.append({
                'timestamp': datetime.now(),
                'action': 'CLOSE',
                'symbol': symbol,
                'data': {
                    **position,
                    'close_price': close_data.get('price'),
                    'close_profit': close_data.get('profit'),
                    'close_time': datetime.now()
                }
            })
            
            # Update daily stats
            today = date.today()
            self.daily_trades[today] += 1
            self.daily_pnl[today] += close_data.get('profit', 0)
            
            # Remove from active positions
            del self.positions[symbol]
            
            logger.info(f"Position closed: {symbol}, P/L: ${close_data.get('profit', 0):.2f}")
    
    def record_trade(self, symbol: str, profit: float):
        """
        Record a completed trade
        
        Args:
            symbol: Trading symbol
            profit: Trade profit/loss
        """
        today = date.today()
        self.daily_trades[today] += 1
        self.daily_pnl[today] += profit
        
        logger.info(f"Trade recorded: {symbol}, P/L: ${profit:.2f}")
    
    def check_daily_limits(self) -> Dict[str, Any]:
        """
        Check if daily limits are breached
        
        Returns:
            Dict with 'ok' (bool), 'reason' (str), and limit details
        """
        today = date.today()
        trades_today = self.daily_trades[today]
        pnl_today = self.daily_pnl[today]
        
        # Check trade count limit
        if trades_today >= self.config.max_daily_trades:
            return {
                'ok': False,
                'reason': f"Daily trade limit reached ({trades_today}/{self.config.max_daily_trades})",
                'trades': trades_today,
                'pnl': pnl_today
            }
        
        # Check daily loss limit (as percentage of account)
        # Note: This requires account balance to be passed or stored
        # For now, we'll check absolute loss
        max_daily_loss = 1000  # Could be calculated from account balance
        
        if pnl_today < -max_daily_loss:
            return {
                'ok': False,
                'reason': f"Daily loss limit reached (${pnl_today:.2f} < -${max_daily_loss:.2f})",
                'trades': trades_today,
                'pnl': pnl_today
            }
        
        return {
            'ok': True,
            'reason': '',
            'trades': trades_today,
            'pnl': pnl_today
        }
    
    def is_signal_processed(self, signal_id: str) -> bool:
        """Check if signal has been processed"""
        return signal_id in self.processed_signals
    
    def mark_signal_processed(self, signal_id: str):
        """Mark signal as processed"""
        self.processed_signals.add(signal_id)
    
    def update_last_signal_time(self, symbol: str):
        """Update last signal time for symbol"""
        self.last_signal_time[symbol] = datetime.now()
    
    def get_last_signal_time(self, symbol: str) -> Optional[datetime]:
        """Get last signal time for symbol"""
        return self.last_signal_time.get(symbol)
    
    def activate_kill_switch(self, reason: str):
        """
        Activate emergency kill switch
        
        Args:
            reason: Reason for activation
        """
        self.kill_switch_active = True
        self.is_trading_enabled = False
        logger.critical(f"🚨 KILL SWITCH ACTIVATED: {reason}")
    
    def deactivate_kill_switch(self):
        """Deactivate kill switch"""
        self.kill_switch_active = False
        self.is_trading_enabled = True
        logger.warning("Kill switch deactivated")
    
    def disable_trading(self, reason: str):
        """Disable trading"""
        self.is_trading_enabled = False
        logger.warning(f"Trading disabled: {reason}")
    
    def enable_trading(self):
        """Enable trading"""
        if not self.kill_switch_active:
            self.is_trading_enabled = True
            logger.info("Trading enabled")
    
    def can_trade(self) -> tuple[bool, str]:
        """
        Check if trading is allowed
        
        Returns:
            Tuple of (can_trade, reason)
        """
        if self.kill_switch_active:
            return False, "Kill switch is active"
        
        if not self.is_trading_enabled:
            return False, "Trading is disabled"
        
        # Check daily limits
        limit_check = self.check_daily_limits()
        if not limit_check['ok']:
            return False, limit_check['reason']
        
        return True, ""
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get summary of current state"""
        today = date.today()
        
        return {
            'timestamp': datetime.now(),
            'trading_enabled': self.is_trading_enabled,
            'kill_switch_active': self.kill_switch_active,
            'open_positions': len(self.positions),
            'positions': list(self.positions.keys()),
            'daily_trades': self.daily_trades[today],
            'daily_pnl': self.daily_pnl[today],
            'total_signals_processed': len(self.processed_signals)
        }
    
    def reset_daily_stats(self):
        """Reset daily statistics (call at start of new trading day)"""
        today = date.today()
        yesterday_trades = self.daily_trades[today]
        yesterday_pnl = self.daily_pnl[today]
        
        logger.info(f"Daily stats reset. Yesterday: {yesterday_trades} trades, "
                   f"P/L: ${yesterday_pnl:.2f}")
        
        # Keep history but clear old entries (keep last 30 days)
        cutoff_date = date.today()
        for d in list(self.daily_trades.keys()):
            if (cutoff_date - d).days > 30:
                del self.daily_trades[d]
                del self.daily_pnl[d]
