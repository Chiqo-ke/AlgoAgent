"""
BaseAdapter - Protocol interface for all broker adapters.

This is the contract that all adapters (SimBroker, Live MT5, etc.) must implement.
Strategy code must ONLY use this interface - never import SimBroker or broker APIs directly.

This ensures strategies work for both backtesting and live trading by swapping adapters.
"""

from typing import Dict, List, Protocol, Optional
import pandas as pd


class BaseAdapter(Protocol):
    """
    Universal broker adapter interface.
    
    All broker implementations (SimBroker, MT5, IBKR, etc.) must implement this.
    Strategy code uses only this interface - no direct broker imports.
    """
    
    def place_order(self, order_request: Dict) -> Dict:
        """
        Place a new order.
        
        Args:
            order_request: MT5-like order dict with:
                - action: 'BUY' or 'SELL'
                - symbol: str
                - volume: float (lots)
                - type: 'MARKET' or 'LIMIT'
                - price: float (for limit orders)
                - sl: float (optional stop loss)
                - tp: float (optional take profit)
                - comment: str (optional)
                
        Returns:
            Response dict with:
                - success: bool
                - order_id: str (if success)
                - position_id: str (if filled immediately)
                - fill_price: float (if filled)
                - error: str (if failed)
        """
        ...
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel a pending order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if cancelled successfully
        """
        ...
    
    def close_position(self, pos_id: str, price: float = None) -> Dict:
        """
        Close an open position.
        
        Args:
            pos_id: Position ID to close
            price: Optional price (for limit close); None = market close
            
        Returns:
            Response dict with:
                - success: bool
                - close_price: float
                - pnl: float
                - error: str (if failed)
        """
        ...
    
    def step_bar(self, bar: pd.Series) -> List[Dict]:
        """
        Process one bar of data (backtest only).
        
        Updates internal state, checks SL/TP hits, executes pending orders.
        
        Args:
            bar: OHLCV bar as pandas Series with:
                - Open, High, Low, Close: float
                - Volume: int
                - Index: timestamp
                
        Returns:
            List of events that occurred during this bar:
                - {'event': 'position_opened', 'position_id': str, 'price': float, ...}
                - {'event': 'position_closed', 'position_id': str, 'pnl': float, 'reason': str, ...}
                - {'event': 'order_filled', 'order_id': str, ...}
                - {'event': 'sl_hit', 'position_id': str, ...}
                - {'event': 'tp_hit', 'position_id': str, ...}
        """
        ...
    
    def get_positions(self) -> List[Dict]:
        """
        Get all open positions.
        
        Returns:
            List of position dicts with:
                - position_id: str
                - symbol: str
                - action: 'BUY' or 'SELL'
                - volume: float
                - entry_price: float
                - current_price: float
                - pnl: float
                - sl: float (optional)
                - tp: float (optional)
                - open_time: timestamp
        """
        ...
    
    def get_account(self) -> Dict:
        """
        Get account state.
        
        Returns:
            Account dict with:
                - balance: float
                - equity: float
                - margin: float
                - free_margin: float
                - margin_level: float (percent)
        """
        ...
    
    def generate_report(self) -> Dict:
        """
        Generate performance report.
        
        Returns:
            Report dict with:
                - total_trades: int
                - winning_trades: int
                - losing_trades: int
                - total_pnl: float
                - win_rate: float
                - profit_factor: float
                - max_drawdown: float
                - sharpe_ratio: float
                - equity_curve: List[Dict] (timestamp, equity)
                - trades: List[Dict] (all trade records)
        """
        ...
    
    def save_report(self, out_dir: str) -> Dict[str, str]:
        """
        Save report artifacts to directory.
        
        Args:
            out_dir: Directory path to save artifacts
            
        Returns:
            Dict of saved file paths:
                - trades: 'path/to/trades.csv'
                - equity_curve: 'path/to/equity_curve.csv'
                - summary: 'path/to/summary.json'
        """
        ...


# Type alias for convenience
Adapter = BaseAdapter
