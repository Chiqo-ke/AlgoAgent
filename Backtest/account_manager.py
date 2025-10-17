"""
Account Manager
===============

Tracks positions, cash, P&L, margin, and equity curve.
Part of the stable SimBroker core.

Last updated: 2025-10-16
Version: 1.0.0
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import defaultdict
import logging

from canonical_schema import (
    Fill, Position, AccountSnapshot, OrderSide
)
from config import BacktestConfig


logger = logging.getLogger(__name__)


class AccountManager:
    """
    Manages account state including positions, cash, and equity
    
    Responsibilities:
    - Track cash balance
    - Maintain open positions
    - Calculate realized/unrealized P&L
    - Track margin usage
    - Generate equity curve snapshots
    - Handle position sizing and risk limits
    """
    
    def __init__(self, config: BacktestConfig):
        """
        Initialize account manager
        
        Args:
            config: Backtest configuration
        """
        self.config = config
        
        # Account state
        self.cash = config.start_cash
        self.initial_cash = config.start_cash
        self.positions: Dict[str, Position] = {}  # symbol -> Position
        
        # Equity curve
        self.equity_curve: List[AccountSnapshot] = []
        self.peak_equity = config.start_cash
        
        # P&L tracking
        self.total_realized_pnl = 0.0
        self.total_commission_paid = 0.0
        
        # Price cache for position valuation
        self.last_prices: Dict[str, float] = {}  # symbol -> last price
        
        # Statistics
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
    
    def process_fill(self, fill: Fill):
        """
        Process a fill and update account state
        
        Args:
            fill: Fill to process
        """
        symbol = fill.symbol
        
        # Update last price
        self.last_prices[symbol] = fill.price
        
        # Pay commission
        self.cash -= fill.commission
        self.total_commission_paid += fill.commission
        
        # Update or create position
        if symbol not in self.positions:
            # New position
            self._open_position(fill)
        else:
            # Existing position
            position = self.positions[symbol]
            
            # Check if this is increasing or decreasing position
            if self._is_same_direction(fill.side, position.size):
                self._increase_position(fill)
            else:
                self._decrease_position(fill)
        
        self.total_trades += 1
        
        logger.debug(
            f"Processed fill: {fill.side} {fill.size} {fill.symbol} @ {fill.price:.2f} | "
            f"Cash: ${self.cash:.2f} | Equity: ${self.get_equity():.2f}"
        )
    
    def _open_position(self, fill: Fill):
        """Open a new position"""
        size = fill.size if fill.side == OrderSide.BUY else -fill.size
        
        position = Position(
            symbol=fill.symbol,
            size=size,
            avg_price=fill.price,
            last_price=fill.price,
            unrealized_pnl=0.0,
            realized_pnl=0.0
        )
        
        self.positions[fill.symbol] = position
        
        # Update cash (deduct cost for longs, add proceeds for shorts)
        if fill.side == OrderSide.BUY:
            self.cash -= fill.price * fill.size
        else:
            self.cash += fill.price * fill.size
        
        logger.info(f"Opened position: {size:+.2f} {fill.symbol} @ {fill.price:.2f}")
    
    def _increase_position(self, fill: Fill):
        """Increase existing position in same direction"""
        position = self.positions[fill.symbol]
        
        old_size = abs(position.size)
        add_size = fill.size
        new_size = old_size + add_size
        
        # Update average price (weighted average)
        old_cost = old_size * position.avg_price
        add_cost = add_size * fill.price
        position.avg_price = (old_cost + add_cost) / new_size
        
        # Update size
        if position.size > 0:  # Long
            position.size = new_size
            self.cash -= fill.price * add_size
        else:  # Short
            position.size = -new_size
            self.cash += fill.price * add_size
        
        position.last_price = fill.price
        
        logger.info(
            f"Increased position: {position.size:+.2f} {fill.symbol} "
            f"(avg: {position.avg_price:.2f})"
        )
    
    def _decrease_position(self, fill: Fill):
        """Decrease or close position (opposite direction)"""
        position = self.positions[fill.symbol]
        
        old_size = abs(position.size)
        reduce_size = min(fill.size, old_size)
        
        # Calculate realized P&L
        if position.size > 0:  # Closing long
            realized_pnl = reduce_size * (fill.price - position.avg_price)
            self.cash += fill.price * reduce_size
        else:  # Closing short
            realized_pnl = reduce_size * (position.avg_price - fill.price)
            self.cash -= fill.price * reduce_size
        
        # Update position
        position.realized_pnl += realized_pnl
        self.total_realized_pnl += realized_pnl
        
        # Track win/loss
        if realized_pnl > 0:
            self.winning_trades += 1
        elif realized_pnl < 0:
            self.losing_trades += 1
        
        # Update size
        new_size = old_size - reduce_size
        if new_size > 0:
            position.size = new_size if position.size > 0 else -new_size
            position.last_price = fill.price
            logger.info(
                f"Reduced position: {position.size:+.2f} {fill.symbol} "
                f"(realized P&L: ${realized_pnl:+.2f})"
            )
        else:
            # Position closed
            logger.info(
                f"Closed position: {fill.symbol} "
                f"(realized P&L: ${realized_pnl:+.2f})"
            )
            del self.positions[fill.symbol]
        
        # Handle over-fill (reversal)
        if fill.size > old_size:
            remaining_size = fill.size - old_size
            # Create new position in opposite direction
            reverse_fill = Fill(
                trade_id=fill.trade_id,
                order_id=fill.order_id,
                signal_id=fill.signal_id,
                timestamp=fill.timestamp,
                symbol=fill.symbol,
                side=fill.side,
                price=fill.price,
                size=remaining_size,
                commission=0.0,  # Already paid
                slippage=fill.slippage
            )
            self._open_position(reverse_fill)
    
    def _is_same_direction(self, side: str, position_size: float) -> bool:
        """Check if fill side matches position direction"""
        if side == OrderSide.BUY:
            return position_size >= 0
        else:
            return position_size < 0
    
    def update_prices(self, prices: Dict[str, float]):
        """
        Update last prices for position valuation
        
        Args:
            prices: Dictionary of symbol -> price
        """
        self.last_prices.update(prices)
        
        # Update unrealized P&L for all positions
        for symbol, position in self.positions.items():
            if symbol in prices:
                position.last_price = prices[symbol]
                position.unrealized_pnl = self._calculate_unrealized_pnl(position)
    
    def _calculate_unrealized_pnl(self, position: Position) -> float:
        """Calculate unrealized P&L for a position"""
        if position.size > 0:  # Long
            return position.size * (position.last_price - position.avg_price)
        else:  # Short
            return -position.size * (position.avg_price - position.last_price)
    
    def get_equity(self) -> float:
        """
        Calculate current equity (cash + unrealized P&L)
        
        Returns:
            Total equity
        """
        unrealized_pnl = sum(
            self._calculate_unrealized_pnl(pos)
            for pos in self.positions.values()
        )
        return self.cash + unrealized_pnl
    
    def get_portfolio_value(self) -> float:
        """
        Calculate portfolio value (value of all positions at market price)
        
        Returns:
            Portfolio value
        """
        return sum(
            abs(pos.size) * pos.last_price
            for pos in self.positions.values()
        )
    
    def get_used_margin(self) -> float:
        """
        Calculate used margin
        
        Returns:
            Used margin amount
        """
        if self.config.margin_requirement == 0:
            return 0.0
        
        portfolio_value = self.get_portfolio_value()
        return portfolio_value * self.config.margin_requirement
    
    def get_available_margin(self) -> float:
        """
        Calculate available margin
        
        Returns:
            Available margin amount
        """
        equity = self.get_equity()
        used_margin = self.get_used_margin()
        
        if self.config.leverage > 1:
            max_margin = equity * self.config.leverage
            return max_margin - used_margin
        else:
            return equity - used_margin
    
    def can_open_position(self, symbol: str, size: float, price: float) -> bool:
        """
        Check if account can open a position
        
        Args:
            symbol: Symbol to trade
            size: Position size
            price: Entry price
        
        Returns:
            True if position can be opened
        """
        required_capital = size * price
        
        # Check cash for non-leveraged
        if self.config.leverage == 1.0:
            return self.cash >= required_capital
        
        # Check margin for leveraged
        required_margin = required_capital * self.config.margin_requirement
        available = self.get_available_margin()
        
        return available >= required_margin
    
    def create_snapshot(self, timestamp: datetime) -> AccountSnapshot:
        """
        Create account snapshot for equity curve
        
        Args:
            timestamp: Snapshot timestamp
        
        Returns:
            AccountSnapshot object
        """
        equity = self.get_equity()
        
        # Update peak equity
        if equity > self.peak_equity:
            self.peak_equity = equity
        
        snapshot = AccountSnapshot(
            timestamp=timestamp,
            cash=self.cash,
            equity=equity,
            portfolio_value=self.get_portfolio_value(),
            used_margin=self.get_used_margin(),
            available_margin=self.get_available_margin(),
            unrealized_pnl=sum(
                self._calculate_unrealized_pnl(pos)
                for pos in self.positions.values()
            ),
            realized_pnl=self.total_realized_pnl,
            positions=[
                Position(
                    symbol=pos.symbol,
                    size=pos.size,
                    avg_price=pos.avg_price,
                    unrealized_pnl=self._calculate_unrealized_pnl(pos),
                    realized_pnl=pos.realized_pnl,
                    last_price=pos.last_price
                )
                for pos in self.positions.values()
            ]
        )
        
        self.equity_curve.append(snapshot)
        
        return snapshot
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for symbol"""
        return self.positions.get(symbol)
    
    def get_all_positions(self) -> List[Position]:
        """Get all open positions"""
        return list(self.positions.values())
    
    def get_equity_curve(self) -> List[AccountSnapshot]:
        """Get equity curve snapshots"""
        return self.equity_curve
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get account statistics"""
        equity = self.get_equity()
        total_return = equity - self.initial_cash
        total_return_pct = (total_return / self.initial_cash) * 100
        
        return {
            'initial_cash': self.initial_cash,
            'current_cash': self.cash,
            'equity': equity,
            'portfolio_value': self.get_portfolio_value(),
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'total_realized_pnl': self.total_realized_pnl,
            'total_commission_paid': self.total_commission_paid,
            'open_positions': len(self.positions),
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': (
                (self.winning_trades / self.total_trades * 100)
                if self.total_trades > 0 else 0.0
            ),
            'peak_equity': self.peak_equity,
            'used_margin': self.get_used_margin(),
            'available_margin': self.get_available_margin()
        }
    
    def reset(self):
        """Reset account manager state"""
        self.cash = self.config.start_cash
        self.initial_cash = self.config.start_cash
        self.positions.clear()
        self.equity_curve.clear()
        self.last_prices.clear()
        self.peak_equity = self.config.start_cash
        self.total_realized_pnl = 0.0
        self.total_commission_paid = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        
        logger.info("Account manager reset")


if __name__ == "__main__":
    # Example usage
    from canonical_schema import generate_id
    
    logging.basicConfig(level=logging.INFO)
    
    config = BacktestConfig(start_cash=100000, fee_flat=1.0, fee_pct=0.001)
    manager = AccountManager(config)
    
    # Simulate a trade
    fill1 = Fill(
        trade_id=generate_id(),
        order_id=generate_id(),
        signal_id=generate_id(),
        timestamp=datetime.utcnow(),
        symbol="AAPL",
        side=OrderSide.BUY,
        price=150.0,
        size=100,
        commission=15.0,
        slippage=0.05
    )
    
    manager.process_fill(fill1)
    
    # Update price
    manager.update_prices({"AAPL": 155.0})
    
    # Create snapshot
    snapshot = manager.create_snapshot(datetime.utcnow())
    
    print("Account State:")
    print(f"  Cash: ${manager.cash:.2f}")
    print(f"  Equity: ${manager.get_equity():.2f}")
    print(f"  Open Positions: {len(manager.positions)}")
    
    if "AAPL" in manager.positions:
        pos = manager.positions["AAPL"]
        print(f"\nAAPL Position:")
        print(f"  Size: {pos.size}")
        print(f"  Avg Price: ${pos.avg_price:.2f}")
        print(f"  Last Price: ${pos.last_price:.2f}")
        print(f"  Unrealized P&L: ${pos.unrealized_pnl:.2f}")
    
    print("\nStatistics:")
    for k, v in manager.get_statistics().items():
        if isinstance(v, float):
            print(f"  {k}: {v:.2f}")
        else:
            print(f"  {k}: {v}")
