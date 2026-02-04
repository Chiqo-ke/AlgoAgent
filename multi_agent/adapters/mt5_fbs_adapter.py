"""
MT5 FBS Adapter - MetaTrader 5 adapter for FBS broker.

Implements BaseAdapter for live trading on FBS demo and live accounts.

SAFETY FEATURES:
- Demo account mode by default
- Position size limits
- Maximum daily loss limits
- Emergency stop functionality
- Manual approval required for live trading
"""

from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime
import logging
import time

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    print("Warning: MetaTrader5 not installed. Install with: pip install MetaTrader5")


logger = logging.getLogger(__name__)


class MT5FBSAdapter:
    """
    MetaTrader 5 adapter for FBS broker.
    
    Implements BaseAdapter interface for live/demo trading.
    """
    
    def __init__(
        self,
        account: int,
        password: str,
        server: str = "FBS-Demo",  # FBS-Demo or FBS-Real
        mode: str = "demo",  # "demo" or "live"
        max_position_size: float = 0.1,  # Max lot size
        max_daily_loss: float = 100.0,  # Max daily loss in account currency
        approval_token: Optional[str] = None
    ):
        """
        Initialize MT5 FBS adapter.
        
        Args:
            account: MT5 account number
            password: MT5 account password
            server: MT5 server name
            mode: Trading mode ("demo" or "live")
            max_position_size: Maximum position size (lots)
            max_daily_loss: Maximum daily loss limit
            approval_token: Required for live trading
            
        Raises:
            RuntimeError: If MT5 not available or connection fails
            ValueError: If live mode without approval token
        """
        if not MT5_AVAILABLE:
            raise RuntimeError(
                "MetaTrader5 not installed. "
                "Install with: pip install MetaTrader5"
            )
        
        if mode == "live" and not approval_token:
            raise ValueError(
                "Live trading requires approval_token. "
                "Set mode='demo' for testing or provide approval token."
            )
        
        self.account = account
        self.password = password
        self.server = server
        self.mode = mode
        self.max_position_size = max_position_size
        self.max_daily_loss = max_daily_loss
        self.approval_token = approval_token
        
        # Initialize connection
        self.connected = False
        self.daily_pnl = 0.0
        self.start_balance = 0.0
        self.positions = {}
        
        self._connect()
    
    def _connect(self):
        """Establish connection to MT5."""
        if not mt5.initialize():
            error = mt5.last_error()
            raise RuntimeError(f"MT5 initialize failed: {error}")
        
        # Login
        authorized = mt5.login(
            login=self.account,
            password=self.password,
            server=self.server
        )
        
        if not authorized:
            mt5.shutdown()
            error = mt5.last_error()
            raise RuntimeError(f"MT5 login failed: {error}")
        
        self.connected = True
        
        # Get initial account info
        account_info = mt5.account_info()
        if account_info:
            self.start_balance = account_info.balance
        
        logger.info(
            f"MT5 connected: {self.server}, "
            f"Account: {self.account}, "
            f"Mode: {self.mode}, "
            f"Balance: {self.start_balance}"
        )
    
    def place_order(self, order_request: Dict) -> Dict:
        """
        Place order on MT5.
        
        Args:
            order_request: {
                'action': 'BUY' | 'SELL',
                'symbol': str,
                'volume': float (lots),
                'type': 'MARKET' | 'LIMIT',
                'price': float (optional, for limit orders),
                'sl': float (optional, stop loss),
                'tp': float (optional, take profit),
                'comment': str (optional)
            }
        
        Returns:
            {
                'success': bool,
                'order_id': int,
                'position_id': int,
                'fill_price': float,
                'error': str (if failed)
            }
        """
        if not self.connected:
            return {'success': False, 'error': 'Not connected to MT5'}
        
        # Safety check: position size
        volume = order_request.get('volume', 0.01)
        if volume > self.max_position_size:
            return {
                'success': False,
                'error': f'Position size {volume} exceeds limit {self.max_position_size}'
            }
        
        # Safety check: daily loss
        if self.daily_pnl < -self.max_daily_loss:
            return {
                'success': False,
                'error': f'Daily loss limit reached: {self.daily_pnl}'
            }
        
        # Parse order request
        action = order_request['action']
        symbol = order_request['symbol']
        order_type = order_request.get('type', 'MARKET')
        price = order_request.get('price')
        sl = order_request.get('sl', 0.0)
        tp = order_request.get('tp', 0.0)
        comment = order_request.get('comment', 'AlgoAgent')
        
        # Determine order type
        if order_type == 'MARKET':
            if action == 'BUY':
                mt5_order_type = mt5.ORDER_TYPE_BUY
            else:
                mt5_order_type = mt5.ORDER_TYPE_SELL
        elif order_type == 'LIMIT':
            if action == 'BUY':
                mt5_order_type = mt5.ORDER_TYPE_BUY_LIMIT
            else:
                mt5_order_type = mt5.ORDER_TYPE_SELL_LIMIT
        else:
            return {'success': False, 'error': f'Unknown order type: {order_type}'}
        
        # Get current price if not provided
        if price is None:
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return {'success': False, 'error': f'Failed to get price for {symbol}'}
            price = tick.ask if action == 'BUY' else tick.bid
        
        # Prepare request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": mt5_order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 10,
            "magic": 234000,  # Magic number for AlgoAgent
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Send order
        result = mt5.order_send(request)
        
        if result is None:
            error = mt5.last_error()
            return {'success': False, 'error': f'Order send failed: {error}'}
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return {
                'success': False,
                'error': f'Order failed: {result.retcode} - {result.comment}'
            }
        
        return {
            'success': True,
            'order_id': result.order,
            'position_id': result.order,  # MT5 uses order ID as position ID
            'fill_price': result.price,
            'volume': result.volume
        }
    
    def close_position(self, pos_id: str, price: float = None) -> Dict:
        """
        Close position on MT5.
        
        Args:
            pos_id: Position ID to close
            price: Closing price (optional, uses market price if not provided)
            
        Returns:
            {
                'success': bool,
                'closed_price': float,
                'pnl': float,
                'error': str (if failed)
            }
        """
        if not self.connected:
            return {'success': False, 'error': 'Not connected to MT5'}
        
        # Get position info
        positions = mt5.positions_get(ticket=int(pos_id))
        
        if not positions:
            return {'success': False, 'error': f'Position {pos_id} not found'}
        
        position = positions[0]
        symbol = position.symbol
        volume = position.volume
        
        # Determine close direction (opposite of position)
        if position.type == mt5.ORDER_TYPE_BUY:
            close_type = mt5.ORDER_TYPE_SELL
        else:
            close_type = mt5.ORDER_TYPE_BUY
        
        # Get current price if not provided
        if price is None:
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return {'success': False, 'error': f'Failed to get price for {symbol}'}
            price = tick.bid if position.type == mt5.ORDER_TYPE_BUY else tick.ask
        
        # Prepare close request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": close_type,
            "position": int(pos_id),
            "price": price,
            "deviation": 10,
            "magic": 234000,
            "comment": "AlgoAgent close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Send close order
        result = mt5.order_send(request)
        
        if result is None:
            error = mt5.last_error()
            return {'success': False, 'error': f'Close failed: {error}'}
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return {
                'success': False,
                'error': f'Close failed: {result.retcode} - {result.comment}'
            }
        
        # Calculate PnL
        pnl = position.profit
        
        # Update daily PnL
        self.daily_pnl += pnl
        
        return {
            'success': True,
            'closed_price': result.price,
            'pnl': pnl,
            'daily_pnl': self.daily_pnl
        }
    
    def get_positions(self) -> List[Dict]:
        """
        Get all open positions.
        
        Returns:
            List of position dicts
        """
        if not self.connected:
            return []
        
        positions = mt5.positions_get()
        
        if positions is None:
            return []
        
        result = []
        for pos in positions:
            result.append({
                'position_id': pos.ticket,
                'symbol': pos.symbol,
                'type': 'BUY' if pos.type == mt5.ORDER_TYPE_BUY else 'SELL',
                'volume': pos.volume,
                'open_price': pos.price_open,
                'current_price': pos.price_current,
                'sl': pos.sl,
                'tp': pos.tp,
                'profit': pos.profit,
                'comment': pos.comment,
                'time': datetime.fromtimestamp(pos.time)
            })
        
        return result
    
    def get_account(self) -> Dict:
        """
        Get account information.
        
        Returns:
            {
                'balance': float,
                'equity': float,
                'margin': float,
                'free_margin': float,
                'margin_level': float,
                'profit': float
            }
        """
        if not self.connected:
            return {
                'balance': 0.0,
                'equity': 0.0,
                'error': 'Not connected'
            }
        
        account_info = mt5.account_info()
        
        if account_info is None:
            return {'balance': 0.0, 'equity': 0.0, 'error': 'Failed to get account info'}
        
        return {
            'balance': account_info.balance,
            'equity': account_info.equity,
            'margin': account_info.margin,
            'free_margin': account_info.margin_free,
            'margin_level': account_info.margin_level,
            'profit': account_info.profit,
            'currency': account_info.currency,
            'leverage': account_info.leverage,
            'server': account_info.server
        }
    
    def emergency_stop(self) -> Dict:
        """
        Emergency stop - close all positions immediately.
        
        Returns:
            {
                'success': bool,
                'closed_positions': int,
                'errors': List[str]
            }
        """
        logger.warning("EMERGENCY STOP TRIGGERED")
        
        positions = self.get_positions()
        closed = 0
        errors = []
        
        for pos in positions:
            result = self.close_position(str(pos['position_id']))
            if result['success']:
                closed += 1
            else:
                errors.append(f"Failed to close {pos['position_id']}: {result.get('error')}")
        
        return {
            'success': len(errors) == 0,
            'closed_positions': closed,
            'errors': errors
        }
    
    def disconnect(self):
        """Disconnect from MT5."""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            logger.info("MT5 disconnected")
    
    def __del__(self):
        """Cleanup on deletion."""
        self.disconnect()


# Example usage
if __name__ == '__main__':
    # Demo account example
    print("MT5 FBS Adapter - Demo Account Test")
    print("=" * 50)
    
    # Replace with your demo account credentials
    adapter = MT5FBSAdapter(
        account=12345678,  # Your demo account number
        password="your_password",
        server="FBS-Demo",
        mode="demo",
        max_position_size=0.1,
        max_daily_loss=100.0
    )
    
    # Get account info
    account = adapter.get_account()
    print(f"\nAccount Info:")
    print(f"  Balance: {account['balance']}")
    print(f"  Equity: {account['equity']}")
    print(f"  Server: {account['server']}")
    
    # Get positions
    positions = adapter.get_positions()
    print(f"\nOpen Positions: {len(positions)}")
    
    adapter.disconnect()
