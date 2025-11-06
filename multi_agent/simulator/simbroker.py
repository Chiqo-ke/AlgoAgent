"""
SimBroker - Deterministic Trading Simulator for Backtesting
============================================================

A portable, testable MT5-compatible order execution simulator.
Provides deterministic backtesting with configurable slippage,
commission, and intrabar SL/TP resolution.

Architecture:
    Strategy -> Order Request (MT5 format) -> SimBroker
             -> Order Engine -> Risk & Accounting -> Events/Logs

Deterministic Intrabar Resolution:
    Long positions:  Open -> High -> Low -> Close sequence
    Short positions: Open -> Low -> High -> Close sequence
    
    This ensures reproducible SL/TP resolution within OHLC bars.
"""

import uuid
import math
import random
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
import pandas as pd
import json
from pathlib import Path


# ============================================================================
# ENUMERATIONS
# ============================================================================

class OrderSide(str, Enum):
    """Order side enumeration"""
    BUY = 'buy'
    SELL = 'sell'


class OrderStatus(str, Enum):
    """Order status enumeration"""
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    FILLED = 'filled'
    CANCELLED = 'cancelled'
    REJECTED = 'rejected'


class CloseReason(str, Enum):
    """Position close reason enumeration"""
    TP = 'tp'           # Take profit hit
    SL = 'sl'           # Stop loss hit
    MANUAL = 'manual'   # Manual close by strategy
    TIMEOUT = 'timeout' # Time-based exit
    MARGIN = 'margin'   # Margin call


class EventType(str, Enum):
    """Broker event types"""
    ORDER_ACCEPTED = 'order_accepted'
    ORDER_REJECTED = 'order_rejected'
    ORDER_FILLED = 'order_filled'
    ORDER_CANCELLED = 'order_cancelled'
    POSITION_OPENED = 'position_opened'
    POSITION_CLOSED = 'position_closed'
    POSITION_MODIFIED = 'position_modified'
    MARGIN_CALL = 'margin_call'


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class SimConfig:
    """
    Simulation configuration parameters.
    
    Attributes:
        starting_balance: Initial account balance
        leverage: Trading leverage (e.g., 100 = 100:1)
        lot_size: Units per lot (100,000 for forex standard lot)
        point: Minimum price movement (0.0001 for 4-digit pairs)
        slippage: Slippage model config {'type': 'fixed', 'value': 2}
        commission: Commission model config {'type': 'per_lot', 'value': 1.5}
        margin_call_level: Margin level (%) triggering margin call
        stop_out_level: Margin level (%) forcing position closure
        allow_hedging: Allow opposing positions on same symbol
        rng_seed: Random seed for deterministic slippage
        debug: Enable debug logging
    """
    starting_balance: float = 10000.0
    leverage: float = 100.0
    lot_size: float = 100000.0
    point: float = 0.0001
    slippage: Dict[str, Any] = field(default_factory=lambda: {"type": "fixed", "value": 2})
    commission: Dict[str, Any] = field(default_factory=lambda: {"type": "per_lot", "value": 1.5})
    margin_call_level: float = 50.0  # %
    stop_out_level: float = 20.0     # %
    allow_hedging: bool = False
    rng_seed: int = 12345
    debug: bool = False
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        if self.starting_balance <= 0:
            errors.append("starting_balance must be positive")
        if self.leverage <= 0:
            errors.append("leverage must be positive")
        if self.lot_size <= 0:
            errors.append("lot_size must be positive")
        if self.point <= 0:
            errors.append("point must be positive")
        if self.margin_call_level >= 100 or self.margin_call_level <= 0:
            errors.append("margin_call_level must be between 0 and 100")
        if self.stop_out_level >= self.margin_call_level:
            errors.append("stop_out_level must be less than margin_call_level")
        return errors


@dataclass
class Order:
    """
    Internal order representation.
    
    Maps MT5-like order requests to internal model.
    """
    order_id: str
    symbol: str
    side: OrderSide
    volume: float  # lots
    requested_price: Optional[float] = None
    sl: Optional[float] = None
    tp: Optional[float] = None
    deviation: float = 10.0
    magic: int = 0
    comment: str = ""
    type_time: str = "ORDER_TIME_GTC"
    type_filling: str = "ORDER_FILLING_RETURN"
    status: OrderStatus = OrderStatus.PENDING
    created_at: pd.Timestamp = field(default_factory=lambda: pd.Timestamp.utcnow())
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        d = asdict(self)
        d['side'] = self.side.value
        d['status'] = self.status.value
        d['created_at'] = str(self.created_at)
        return d


@dataclass
class Fill:
    """
    Trade/fill record representing a filled order and its lifecycle.
    """
    trade_id: str
    order_id: str
    symbol: str
    side: OrderSide
    entry_price: float
    volume: float  # lots
    sl: Optional[float] = None
    tp: Optional[float] = None
    open_time: pd.Timestamp = field(default_factory=lambda: pd.Timestamp.utcnow())
    close_time: Optional[pd.Timestamp] = None
    close_price: Optional[float] = None
    profit: Optional[float] = None
    commission_entry: float = 0.0
    commission_exit: float = 0.0
    slippage_entry: float = 0.0
    slippage_exit: float = 0.0
    reason_close: Optional[CloseReason] = None
    magic: int = 0
    comment: str = ""
    
    @property
    def total_commission(self) -> float:
        """Total commission (entry + exit)"""
        return self.commission_entry + self.commission_exit
    
    @property
    def net_profit(self) -> Optional[float]:
        """Net profit after commissions"""
        if self.profit is None:
            return None
        return self.profit - self.total_commission
    
    @property
    def is_open(self) -> bool:
        """Check if position is still open"""
        return self.close_time is None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        d = asdict(self)
        d['side'] = self.side.value
        d['reason_close'] = self.reason_close.value if self.reason_close else None
        d['open_time'] = str(self.open_time)
        d['close_time'] = str(self.close_time) if self.close_time else None
        d['total_commission'] = self.total_commission
        d['net_profit'] = self.net_profit
        return d


@dataclass
class Position:
    """
    Active position (alias for open Fill for API clarity)
    """
    fill: Fill
    
    @property
    def position_id(self) -> str:
        return self.fill.trade_id
    
    def floating_pnl(self, current_price: float, lot_size: float) -> float:
        """Calculate floating P&L at current price"""
        price_diff = current_price - self.fill.entry_price
        if self.fill.side == OrderSide.SELL:
            price_diff = -price_diff
        return price_diff * self.fill.volume * lot_size
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return self.fill.to_dict()


@dataclass
class EquityPoint:
    """
    Point-in-time account snapshot for equity curve.
    """
    time: pd.Timestamp
    balance: float
    equity: float
    floating_pnl: float
    used_margin: float
    free_margin: float
    margin_level: float  # equity / used_margin * 100
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        d = asdict(self)
        d['time'] = str(self.time)
        return d


@dataclass
class AccountSnapshot:
    """
    Current account state.
    """
    balance: float
    equity: float
    floating_pnl: float
    used_margin: float
    free_margin: float
    margin_level: float
    total_positions: int
    total_orders: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class OrderResponse:
    """
    Response from place_order operation.
    """
    order_id: Optional[str]
    status: OrderStatus
    message: str = ""
    
    @property
    def success(self) -> bool:
        return self.status in (OrderStatus.ACCEPTED, OrderStatus.FILLED)
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['status'] = self.status.value
        d['success'] = self.success
        return d


@dataclass
class CloseResult:
    """
    Result from close_position operation.
    """
    success: bool
    position_id: str
    close_price: Optional[float] = None
    profit: Optional[float] = None
    message: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Event:
    """
    Broker event (fills, closures, etc.)
    """
    event_type: EventType
    timestamp: pd.Timestamp
    data: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            'event_type': self.event_type.value,
            'timestamp': str(self.timestamp),
            'data': self.data
        }


# ============================================================================
# SIMBROKER CLASS
# ============================================================================

class SimBroker:
    """
    Portable, deterministic trading simulator.
    
    Simulates order execution, position management, and P&L tracking
    for backtesting trading strategies with MT5-compatible interface.
    
    Usage:
        >>> config = SimConfig(starting_balance=10000, leverage=100)
        >>> broker = SimBroker(config)
        >>> response = broker.place_order({
        ...     'action': 'TRADE_ACTION_DEAL',
        ...     'symbol': 'EURUSD',
        ...     'volume': 0.1,
        ...     'type': 'ORDER_TYPE_BUY',
        ...     'sl': 1.0950,
        ...     'tp': 1.1050
        ... })
        >>> events = broker.step_bar(bar_data)
    """
    
    def __init__(self, config: SimConfig):
        """
        Initialize SimBroker with configuration.
        
        Args:
            config: SimConfig instance with simulation parameters
        
        Raises:
            ValueError: If configuration is invalid
        """
        errors = config.validate()
        if errors:
            raise ValueError(f"Invalid configuration: {', '.join(errors)}")
        
        self.cfg = config
        self.rng = random.Random(config.rng_seed)
        self._event_log: List[Event] = []
        self._intrabar_log: List[Dict] = []  # Debug log for intrabar events
        self.reset()
    
    def reset(self) -> None:
        """
        Reset broker state to initial conditions.
        
        Clears all orders, positions, trades, and resets balance.
        Useful for running multiple test scenarios.
        """
        self.orders: Dict[str, Order] = {}
        self.positions: Dict[str, Position] = {}
        self.trades: List[Fill] = []
        self.balance = self.cfg.starting_balance
        self.equity_curve: List[EquityPoint] = []
        self._event_log.clear()
        self._intrabar_log.clear()
        self._current_bar_time: Optional[pd.Timestamp] = None
        
        if self.cfg.debug:
            print(f"[SimBroker] Reset - Balance: {self.balance}")
    
    # ========================================================================
    # PUBLIC API - ORDER MANAGEMENT
    # ========================================================================
    
    def place_order(self, order_request: Dict) -> OrderResponse:
        """
        Place a new order (MT5-compatible request format).
        
        Args:
            order_request: Dictionary with keys:
                - action: 'TRADE_ACTION_DEAL' (market order)
                - symbol: Trading symbol
                - volume: Position size in lots
                - type: 'ORDER_TYPE_BUY' or 'ORDER_TYPE_SELL'
                - price: Optional limit price (None for market)
                - sl: Stop loss price (optional)
                - tp: Take profit price (optional)
                - deviation: Max slippage points (optional)
                - magic: Magic number for strategy identification
                - comment: Order comment
        
        Returns:
            OrderResponse with order_id and status
        
        Example:
            >>> response = broker.place_order({
            ...     'action': 'TRADE_ACTION_DEAL',
            ...     'symbol': 'AAPL',
            ...     'volume': 0.1,
            ...     'type': 'ORDER_TYPE_BUY',
            ...     'sl': 149.23,
            ...     'tp': 151.23
            ... })
        """
        try:
            # Validate required fields
            required = ['symbol', 'volume', 'type']
            missing = [f for f in required if f not in order_request]
            if missing:
                return OrderResponse(
                    order_id=None,
                    status=OrderStatus.REJECTED,
                    message=f"Missing required fields: {missing}"
                )
            
            # Parse order type to side
            order_type = order_request.get('type', '').upper()
            if 'BUY' in order_type:
                side = OrderSide.BUY
            elif 'SELL' in order_type:
                side = OrderSide.SELL
            else:
                return OrderResponse(
                    order_id=None,
                    status=OrderStatus.REJECTED,
                    message=f"Invalid order type: {order_type}"
                )
            
            # Validate volume
            volume = float(order_request['volume'])
            if volume <= 0:
                return OrderResponse(
                    order_id=None,
                    status=OrderStatus.REJECTED,
                    message=f"Invalid volume: {volume}"
                )
            
            # Check margin requirements
            price_estimate = order_request.get('price', 0) or 100.0  # Default estimate
            required_margin = self._calculate_required_margin(volume, price_estimate)
            account = self.get_account()
            
            if required_margin > account.free_margin:
                return OrderResponse(
                    order_id=None,
                    status=OrderStatus.REJECTED,
                    message=f"Insufficient margin: need {required_margin:.2f}, have {account.free_margin:.2f}"
                )
            
            # Create order
            order_id = str(uuid.uuid4())
            order = Order(
                order_id=order_id,
                symbol=order_request['symbol'],
                side=side,
                volume=volume,
                requested_price=order_request.get('price'),
                sl=order_request.get('sl'),
                tp=order_request.get('tp'),
                deviation=order_request.get('deviation', 10.0),
                magic=order_request.get('magic', 0),
                comment=order_request.get('comment', ''),
                type_time=order_request.get('type_time', 'ORDER_TIME_GTC'),
                type_filling=order_request.get('type_filling', 'ORDER_FILLING_RETURN'),
                status=OrderStatus.ACCEPTED
            )
            
            self.orders[order_id] = order
            
            # Log event
            self._log_event(EventType.ORDER_ACCEPTED, {
                'order_id': order_id,
                'symbol': order.symbol,
                'side': order.side.value,
                'volume': order.volume
            })
            
            if self.cfg.debug:
                print(f"[SimBroker] Order accepted: {order_id} {order.side.value} {order.volume} {order.symbol}")
            
            return OrderResponse(
                order_id=order_id,
                status=OrderStatus.ACCEPTED,
                message="Order accepted"
            )
        
        except Exception as e:
            return OrderResponse(
                order_id=None,
                status=OrderStatus.REJECTED,
                message=f"Error placing order: {str(e)}"
            )
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel a pending order.
        
        Args:
            order_id: Order ID to cancel
        
        Returns:
            True if cancelled, False if not found or already filled
        """
        if order_id not in self.orders:
            if self.cfg.debug:
                print(f"[SimBroker] Cancel failed: Order {order_id} not found")
            return False
        
        order = self.orders[order_id]
        if order.status not in [OrderStatus.PENDING, OrderStatus.ACCEPTED]:
            if self.cfg.debug:
                print(f"[SimBroker] Cancel failed: Order {order_id} status is {order.status}")
            return False
        
        order.status = OrderStatus.CANCELLED
        del self.orders[order_id]
        
        self._log_event(EventType.ORDER_CANCELLED, {'order_id': order_id})
        
        if self.cfg.debug:
            print(f"[SimBroker] Order cancelled: {order_id}")
        
        return True
    
    def close_position(self, position_id: str, price: Optional[float] = None) -> CloseResult:
        """
        Manually close an open position.
        
        Args:
            position_id: Position ID (trade_id) to close
            price: Close price (None = use current bar close)
        
        Returns:
            CloseResult with success status and P&L
        """
        if position_id not in self.positions:
            return CloseResult(
                success=False,
                position_id=position_id,
                message="Position not found"
            )
        
        position = self.positions[position_id]
        
        # Use provided price or require it
        if price is None:
            return CloseResult(
                success=False,
                position_id=position_id,
                message="Close price required for manual close"
            )
        
        # Apply exit slippage and commission
        exit_slip = self._compute_exit_slippage(position.fill, price)
        final_price = price + exit_slip
        exit_commission = self._compute_commission(position.fill.volume, final_price)
        
        # Calculate profit
        profit = self._compute_profit(position.fill, final_price)
        
        # Update fill record
        position.fill.close_time = self._current_bar_time or pd.Timestamp.utcnow()
        position.fill.close_price = final_price
        position.fill.slippage_exit = exit_slip
        position.fill.commission_exit = exit_commission
        position.fill.profit = profit
        position.fill.reason_close = CloseReason.MANUAL
        
        # Update balance
        self.balance += profit - exit_commission
        
        # Remove from positions
        del self.positions[position_id]
        
        # Log event
        self._log_event(EventType.POSITION_CLOSED, {
            'position_id': position_id,
            'reason': CloseReason.MANUAL.value,
            'profit': profit,
            'net_profit': profit - exit_commission
        })
        
        if self.cfg.debug:
            print(f"[SimBroker] Position closed manually: {position_id} P&L: {profit:.2f}")
        
        return CloseResult(
            success=True,
            position_id=position_id,
            close_price=final_price,
            profit=profit - exit_commission,
            message="Position closed"
        )
    
    # ========================================================================
    # PUBLIC API - SIMULATION STEPPING
    # ========================================================================
    
    def step_bar(self, bar: pd.Series) -> List[Event]:
        """
        Process one OHLCV bar and execute order/position logic.
        
        Deterministic execution sequence:
        1. Fill pending orders at bar Open (+ slippage)
        2. Check SL/TP for all open positions using intrabar logic
        3. Update equity curve
        
        Args:
            bar: pandas Series with keys:
                - Date or index: bar timestamp
                - Open: opening price
                - High: high price
                - Low: low price
                - Close: closing price
                - Volume: volume (optional)
        
        Returns:
            List of Event objects (fills, closures, margin calls)
        
        Example:
            >>> bar = pd.Series({
            ...     'Date': pd.Timestamp('2024-01-01'),
            ...     'Open': 150.0,
            ...     'High': 151.5,
            ...     'Low': 149.5,
            ...     'Close': 151.0
            ... })
            >>> events = broker.step_bar(bar)
        """
        events = []
        
        # Extract bar data
        bar_time = bar.get('Date', bar.name) if 'Date' in bar else bar.name
        if not isinstance(bar_time, pd.Timestamp):
            bar_time = pd.Timestamp(bar_time)
        
        self._current_bar_time = bar_time
        
        open_price = float(bar['Open'])
        high_price = float(bar['High'])
        low_price = float(bar['Low'])
        close_price = float(bar['Close'])
        
        if self.cfg.debug:
            print(f"\n[SimBroker] === Bar {bar_time} O:{open_price} H:{high_price} L:{low_price} C:{close_price} ===")
        
        # Step 1: Fill pending orders at Open
        events.extend(self._fill_pending_orders(bar_time, open_price))
        
        # Step 2: Check SL/TP for open positions (intrabar logic)
        events.extend(self._check_position_exits(bar_time, open_price, high_price, low_price, close_price))
        
        # Step 3: Check margin level and handle margin calls
        events.extend(self._check_margin_level(close_price))
        
        # Step 4: Record equity curve point
        self._record_equity_point(bar_time, close_price)
        
        return events
    
    def step_tick(self, tick: Dict) -> List[Event]:
        """
        Process one tick (for tick-mode simulation - future enhancement).
        
        Args:
            tick: Dictionary with keys:
                - timestamp: tick time
                - price: tick price
                - volume: tick volume
        
        Returns:
            List of Event objects
        
        Note:
            Currently not fully implemented. Bar-mode is recommended.
        """
        # TODO: Implement tick-by-tick simulation
        # For now, raise NotImplementedError
        raise NotImplementedError("Tick-mode simulation not yet implemented. Use step_bar() for bar-mode.")
    
    # ========================================================================
    # PUBLIC API - QUERY METHODS
    # ========================================================================
    
    def get_positions(self) -> List[Position]:
        """
        Get all open positions.
        
        Returns:
            List of Position objects
        """
        return list(self.positions.values())
    
    def get_account(self) -> AccountSnapshot:
        """
        Get current account state.
        
        Returns:
            AccountSnapshot with balance, equity, margin info
        """
        # Calculate floating P&L (need current prices - use last close or 0)
        # Note: In real usage, caller should track current prices
        floating_pnl = 0.0
        # We don't have current price here, so floating_pnl = 0 (will be updated in step_bar)
        
        used_margin = sum(
            self._calculate_required_margin(pos.fill.volume, pos.fill.entry_price)
            for pos in self.positions.values()
        )
        
        equity = self.balance + floating_pnl
        free_margin = equity - used_margin
        margin_level = (equity / used_margin * 100.0) if used_margin > 0 else float('inf')
        
        return AccountSnapshot(
            balance=self.balance,
            equity=equity,
            floating_pnl=floating_pnl,
            used_margin=used_margin,
            free_margin=free_margin,
            margin_level=margin_level,
            total_positions=len(self.positions),
            total_orders=len(self.orders)
        )
    
    def get_trades(self) -> List[Fill]:
        """
        Get all trade records (both open and closed).
        
        Returns:
            List of Fill objects
        """
        return self.trades.copy()
    
    def get_closed_trades(self) -> List[Fill]:
        """
        Get only closed trade records.
        
        Returns:
            List of closed Fill objects
        """
        return [t for t in self.trades if not t.is_open]
    
    def get_events(self) -> List[Event]:
        """
        Get event log.
        
        Returns:
            List of Event objects
        """
        return self._event_log.copy()
    
    # ========================================================================
    # PUBLIC API - REPORTING
    # ========================================================================
    
    def generate_report(self) -> Dict:
        """
        Generate comprehensive backtest report with metrics.
        
        Returns:
            Dictionary containing:
                - summary metrics (total_trades, win_rate, net_pnl, etc.)
                - trades: list of trade dicts
                - equity_curve: list of equity points
                - config: simulation config used
        
        Example:
            >>> report = broker.generate_report()
            >>> print(f"Win rate: {report['metrics']['win_rate']:.1%}")
        """
        closed_trades = self.get_closed_trades()
        
        # Calculate metrics
        total_trades = len(closed_trades)
        
        if total_trades == 0:
            metrics = {
                'total_trades': 0,
                'win_rate': 0.0,
                'avg_profit': 0.0,
                'avg_loss': 0.0,
                'expectancy': 0.0,
                'total_net_pnl': 0.0,
                'total_gross_pnl': 0.0,
                'total_commissions': 0.0,
                'return_pct': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0
            }
        else:
            winning_trades = [t for t in closed_trades if (t.net_profit or 0) > 0]
            losing_trades = [t for t in closed_trades if (t.net_profit or 0) <= 0]
            
            win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
            
            avg_profit = sum(t.net_profit for t in winning_trades) / len(winning_trades) if winning_trades else 0
            avg_loss = sum(t.net_profit for t in losing_trades) / len(losing_trades) if losing_trades else 0
            
            expectancy = (win_rate * avg_profit) + ((1 - win_rate) * avg_loss)
            
            total_gross_pnl = sum(t.profit for t in closed_trades if t.profit is not None)
            total_commissions = sum(t.total_commission for t in closed_trades)
            total_net_pnl = sum(t.net_profit for t in closed_trades if t.net_profit is not None)
            
            return_pct = (total_net_pnl / self.cfg.starting_balance) * 100
            
            # Calculate max drawdown from equity curve
            max_dd = self._calculate_max_drawdown()
            
            # Calculate Sharpe ratio (simplified - assumes daily returns)
            sharpe = self._calculate_sharpe_ratio()
            
            metrics = {
                'total_trades': total_trades,
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': win_rate,
                'avg_profit': avg_profit,
                'avg_loss': avg_loss,
                'expectancy': expectancy,
                'total_gross_pnl': total_gross_pnl,
                'total_commissions': total_commissions,
                'total_net_pnl': total_net_pnl,
                'return_pct': return_pct,
                'max_drawdown': max_dd,
                'max_drawdown_pct': (max_dd / self.cfg.starting_balance) * 100,
                'sharpe_ratio': sharpe,
                'profit_factor': abs(avg_profit / avg_loss) if avg_loss != 0 else float('inf')
            }
        
        return {
            'metrics': metrics,
            'trades': [t.to_dict() for t in closed_trades],
            'equity_curve': [ep.to_dict() for ep in self.equity_curve],
            'config': asdict(self.cfg),
            'summary': {
                'starting_balance': self.cfg.starting_balance,
                'ending_balance': self.balance,
                'total_return': self.balance - self.cfg.starting_balance,
                'return_pct': ((self.balance - self.cfg.starting_balance) / self.cfg.starting_balance) * 100
            }
        }
    
    def save_report(self, output_dir: Path) -> Dict[str, Path]:
        """
        Save report artifacts to files.
        
        Args:
            output_dir: Directory to save files
        
        Returns:
            Dictionary mapping artifact names to file paths
        
        Example:
            >>> paths = broker.save_report(Path('artifacts/'))
            >>> print(f"Trades saved to {paths['trades']}")
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        report = self.generate_report()
        
        # Save trades.csv
        trades_df = pd.DataFrame(report['trades'])
        trades_path = output_dir / 'trades.csv'
        trades_df.to_csv(trades_path, index=False)
        
        # Save equity_curve.csv
        equity_df = pd.DataFrame(report['equity_curve'])
        equity_path = output_dir / 'equity_curve.csv'
        equity_df.to_csv(equity_path, index=False)
        
        # Save test_report.json
        report_path = output_dir / 'test_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        if self.cfg.debug:
            print(f"[SimBroker] Report saved to {output_dir}")
        
        return {
            'trades': trades_path,
            'equity_curve': equity_path,
            'report': report_path
        }
    
    # ========================================================================
    # INTERNAL METHODS - ORDER FILLING
    # ========================================================================
    
    def _fill_pending_orders(self, timestamp: pd.Timestamp, fill_price: float) -> List[Event]:
        """Fill all pending orders at specified price (bar Open)"""
        events = []
        
        orders_to_fill = list(self.orders.values())
        
        for order in orders_to_fill:
            # Apply entry slippage
            entry_slip = self._compute_entry_slippage(order, fill_price)
            actual_fill_price = fill_price + entry_slip
            
            # Calculate entry commission
            entry_commission = self._compute_commission(order.volume, actual_fill_price)
            
            # Create fill/trade record
            trade_id = str(uuid.uuid4())
            fill = Fill(
                trade_id=trade_id,
                order_id=order.order_id,
                symbol=order.symbol,
                side=order.side,
                entry_price=actual_fill_price,
                volume=order.volume,
                sl=order.sl,
                tp=order.tp,
                open_time=timestamp,
                commission_entry=entry_commission,
                slippage_entry=entry_slip,
                magic=order.magic,
                comment=order.comment
            )
            
            # Store as position and in trades list
            self.positions[trade_id] = Position(fill=fill)
            self.trades.append(fill)
            
            # Update order status and remove from pending
            order.status = OrderStatus.FILLED
            del self.orders[order.order_id]
            
            # Log events
            events.append(self._log_event(EventType.ORDER_FILLED, {
                'order_id': order.order_id,
                'trade_id': trade_id,
                'fill_price': actual_fill_price,
                'slippage': entry_slip
            }))
            
            events.append(self._log_event(EventType.POSITION_OPENED, {
                'position_id': trade_id,
                'symbol': fill.symbol,
                'side': fill.side.value,
                'volume': fill.volume,
                'entry_price': actual_fill_price
            }))
            
            if self.cfg.debug:
                print(f"[SimBroker] Order filled: {order.order_id} -> Position {trade_id} @ {actual_fill_price:.4f}")
        
        return events
    
    # ========================================================================
    # INTERNAL METHODS - POSITION MANAGEMENT
    # ========================================================================
    
    def _check_position_exits(
        self,
        timestamp: pd.Timestamp,
        open_: float,
        high: float,
        low: float,
        close: float
    ) -> List[Event]:
        """
        Check SL/TP hits for all positions using deterministic intrabar logic.
        
        Intrabar sequence:
            Long:  Open -> High -> Low -> Close
            Short: Open -> Low -> High -> Close
        
        This ensures deterministic SL/TP resolution within OHLC bars.
        """
        events = []
        
        positions_to_check = list(self.positions.items())
        
        for position_id, position in positions_to_check:
            fill = position.fill
            
            # Determine intrabar price sequence based on side
            if fill.side == OrderSide.BUY:
                # Long: Open -> High -> Low -> Close
                price_sequence = [
                    ('open', open_),
                    ('high', high),
                    ('low', low),
                    ('close', close)
                ]
            else:  # SELL
                # Short: Open -> Low -> High -> Close
                price_sequence = [
                    ('open', open_),
                    ('low', low),
                    ('high', high),
                    ('close', close)
                ]
            
            # Check each price point in sequence for SL/TP hits
            exit_reason = None
            exit_price = None
            exit_point = None
            
            for point_name, price in price_sequence:
                if exit_reason:
                    break  # Already exited
                
                # Check TP
                if fill.tp is not None:
                    if fill.side == OrderSide.BUY and price >= fill.tp:
                        exit_reason = CloseReason.TP
                        exit_price = fill.tp
                        exit_point = point_name
                        break
                    elif fill.side == OrderSide.SELL and price <= fill.tp:
                        exit_reason = CloseReason.TP
                        exit_price = fill.tp
                        exit_point = point_name
                        break
                
                # Check SL
                if fill.sl is not None:
                    if fill.side == OrderSide.BUY and price <= fill.sl:
                        exit_reason = CloseReason.SL
                        exit_price = fill.sl
                        exit_point = point_name
                        break
                    elif fill.side == OrderSide.SELL and price >= fill.sl:
                        exit_reason = CloseReason.SL
                        exit_price = fill.sl
                        exit_point = point_name
                        break
            
            # If exit triggered, close position
            if exit_reason and exit_price:
                # Apply exit slippage
                exit_slip = self._compute_exit_slippage(fill, exit_price)
                final_exit_price = exit_price + exit_slip
                
                # Calculate exit commission
                exit_commission = self._compute_commission(fill.volume, final_exit_price)
                
                # Calculate profit
                profit = self._compute_profit(fill, final_exit_price)
                
                # Update fill record
                fill.close_time = timestamp
                fill.close_price = final_exit_price
                fill.slippage_exit = exit_slip
                fill.commission_exit = exit_commission
                fill.profit = profit
                fill.reason_close = exit_reason
                
                # Update balance
                net_profit = profit - exit_commission
                self.balance += net_profit
                
                # Remove from positions
                del self.positions[position_id]
                
                # Log intrabar event for debugging
                if self.cfg.debug:
                    self._intrabar_log.append({
                        'timestamp': timestamp,
                        'position_id': position_id,
                        'side': fill.side.value,
                        'exit_point': exit_point,
                        'exit_reason': exit_reason.value,
                        'exit_price': final_exit_price,
                        'profit': net_profit,
                        'bar_ohlc': f"O:{open_} H:{high} L:{low} C:{close}"
                    })
                    print(f"[SimBroker] Position closed: {position_id} {exit_reason.value} @ {exit_point} {final_exit_price:.4f} P&L: {net_profit:.2f}")
                
                # Log event
                events.append(self._log_event(EventType.POSITION_CLOSED, {
                    'position_id': position_id,
                    'reason': exit_reason.value,
                    'exit_price': final_exit_price,
                    'profit': profit,
                    'net_profit': net_profit,
                    'exit_point': exit_point
                }))
        
        return events
    
    def _check_margin_level(self, current_price: float) -> List[Event]:
        """Check margin level and handle margin calls/stop-outs"""
        events = []
        
        if not self.positions:
            return events
        
        # Calculate floating P&L and margin level
        floating_pnl = sum(
            pos.floating_pnl(current_price, self.cfg.lot_size)
            for pos in self.positions.values()
        )
        
        used_margin = sum(
            self._calculate_required_margin(pos.fill.volume, pos.fill.entry_price)
            for pos in self.positions.values()
        )
        
        equity = self.balance + floating_pnl
        margin_level = (equity / used_margin * 100.0) if used_margin > 0 else float('inf')
        
        # Check stop-out level (force close positions)
        if margin_level <= self.cfg.stop_out_level:
            if self.cfg.debug:
                print(f"[SimBroker] STOP OUT! Margin level: {margin_level:.2f}%")
            
            # Close all positions at current price
            for position_id in list(self.positions.keys()):
                result = self.close_position(position_id, current_price)
                if result.success:
                    events.append(self._log_event(EventType.POSITION_CLOSED, {
                        'position_id': position_id,
                        'reason': 'stop_out',
                        'margin_level': margin_level
                    }))
        
        # Check margin call level (warning)
        elif margin_level <= self.cfg.margin_call_level:
            if self.cfg.debug:
                print(f"[SimBroker] MARGIN CALL! Margin level: {margin_level:.2f}%")
            
            events.append(self._log_event(EventType.MARGIN_CALL, {
                'margin_level': margin_level,
                'equity': equity,
                'used_margin': used_margin
            }))
        
        return events
    
    # ========================================================================
    # INTERNAL METHODS - CALCULATIONS
    # ========================================================================
    
    def _compute_entry_slippage(self, order: Order, market_price: float) -> float:
        """
        Calculate entry slippage based on configured model.
        
        Returns slippage amount to add to market_price.
        Positive = worse fill for trader.
        """
        slip_cfg = self.cfg.slippage
        slip_type = slip_cfg.get('type', 'fixed')
        
        # Direction: positive slippage means worse fill
        side_multiplier = 1 if order.side == OrderSide.BUY else -1
        
        if slip_type == 'fixed':
            points = slip_cfg.get('value', 0)
            return side_multiplier * points * self.cfg.point
        
        elif slip_type == 'random':
            max_points = slip_cfg.get('value', 0)
            points = self.rng.uniform(0, max_points)  # Always positive (adverse)
            return side_multiplier * points * self.cfg.point
        
        elif slip_type == 'percent':
            pct = slip_cfg.get('value', 0) / 100.0
            return side_multiplier * market_price * pct
        
        else:
            return 0.0
    
    def _compute_exit_slippage(self, fill: Fill, market_price: float) -> float:
        """Calculate exit slippage (inverse of entry side)"""
        slip_cfg = self.cfg.slippage
        slip_type = slip_cfg.get('type', 'fixed')
        
        # Exit slippage goes opposite direction (closing reverses side)
        side_multiplier = -1 if fill.side == OrderSide.BUY else 1
        
        if slip_type == 'fixed':
            points = slip_cfg.get('value', 0)
            return side_multiplier * points * self.cfg.point
        
        elif slip_type == 'random':
            max_points = slip_cfg.get('value', 0)
            points = self.rng.uniform(0, max_points)
            return side_multiplier * points * self.cfg.point
        
        elif slip_type == 'percent':
            pct = slip_cfg.get('value', 0) / 100.0
            return side_multiplier * market_price * pct
        
        else:
            return 0.0
    
    def _compute_commission(self, volume: float, price: float) -> float:
        """Calculate commission based on configured model"""
        comm_cfg = self.cfg.commission
        comm_type = comm_cfg.get('type', 'per_lot')
        
        if comm_type == 'per_lot':
            rate = comm_cfg.get('value', 0)
            return volume * rate
        
        elif comm_type == 'percent':
            pct = comm_cfg.get('value', 0) / 100.0
            notional = volume * self.cfg.lot_size * price
            return notional * pct
        
        elif comm_type == 'flat':
            return comm_cfg.get('value', 0)
        
        else:
            return 0.0
    
    def _compute_profit(self, fill: Fill, close_price: float) -> float:
        """Calculate gross profit (before commissions)"""
        price_diff = close_price - fill.entry_price
        
        if fill.side == OrderSide.SELL:
            price_diff = -price_diff
        
        return price_diff * fill.volume * self.cfg.lot_size
    
    def _calculate_required_margin(self, volume: float, price: float) -> float:
        """Calculate required margin for position"""
        notional = volume * self.cfg.lot_size * price
        return notional / self.cfg.leverage
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown from equity curve"""
        if not self.equity_curve:
            return 0.0
        
        equity_values = [ep.equity for ep in self.equity_curve]
        peak = equity_values[0]
        max_dd = 0.0
        
        for equity in equity_values:
            if equity > peak:
                peak = equity
            dd = peak - equity
            if dd > max_dd:
                max_dd = dd
        
        return max_dd
    
    def _calculate_sharpe_ratio(self) -> float:
        """Calculate Sharpe ratio from equity curve (simplified)"""
        if len(self.equity_curve) < 2:
            return 0.0
        
        # Calculate period returns
        returns = []
        for i in range(1, len(self.equity_curve)):
            prev_eq = self.equity_curve[i-1].equity
            curr_eq = self.equity_curve[i].equity
            ret = (curr_eq - prev_eq) / prev_eq if prev_eq > 0 else 0
            returns.append(ret)
        
        if not returns:
            return 0.0
        
        # Sharpe = mean(returns) / std(returns)
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std_return = math.sqrt(variance)
        
        if std_return == 0:
            return 0.0
        
        # Annualize assuming daily data (252 trading days)
        sharpe = (mean_return / std_return) * math.sqrt(252)
        return sharpe
    
    # ========================================================================
    # INTERNAL METHODS - UTILITIES
    # ========================================================================
    
    def _record_equity_point(self, timestamp: pd.Timestamp, current_price: float) -> None:
        """Record equity curve point"""
        floating_pnl = sum(
            pos.floating_pnl(current_price, self.cfg.lot_size)
            for pos in self.positions.values()
        )
        
        used_margin = sum(
            self._calculate_required_margin(pos.fill.volume, pos.fill.entry_price)
            for pos in self.positions.values()
        )
        
        equity = self.balance + floating_pnl
        free_margin = equity - used_margin
        margin_level = (equity / used_margin * 100.0) if used_margin > 0 else float('inf')
        
        point = EquityPoint(
            time=timestamp,
            balance=self.balance,
            equity=equity,
            floating_pnl=floating_pnl,
            used_margin=used_margin,
            free_margin=free_margin,
            margin_level=margin_level
        )
        
        self.equity_curve.append(point)
    
    def _log_event(self, event_type: EventType, data: Dict) -> Event:
        """Log broker event"""
        event = Event(
            event_type=event_type,
            timestamp=self._current_bar_time or pd.Timestamp.utcnow(),
            data=data
        )
        self._event_log.append(event)
        return event
    
    def get_intrabar_log(self) -> List[Dict]:
        """Get intrabar debug log (for testing/debugging)"""
        return self._intrabar_log.copy()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def load_config_from_yaml(config_path: Path) -> SimConfig:
    """
    Load SimConfig from YAML file.
    
    Args:
        config_path: Path to config YAML file
    
    Returns:
        SimConfig instance
    """
    import yaml
    
    with open(config_path) as f:
        cfg_dict = yaml.safe_load(f)
    
    return SimConfig(**cfg_dict)


def create_default_config(preset: str = 'default') -> SimConfig:
    """
    Create SimConfig with preset values.
    
    Args:
        preset: Preset name ('default', 'conservative', 'aggressive')
    
    Returns:
        SimConfig instance
    """
    presets = {
        'default': SimConfig(),
        'conservative': SimConfig(
            slippage={'type': 'fixed', 'value': 5},
            commission={'type': 'per_lot', 'value': 3.0}
        ),
        'aggressive': SimConfig(
            slippage={'type': 'fixed', 'value': 1},
            commission={'type': 'per_lot', 'value': 0.5}
        ),
        'zero_cost': SimConfig(
            slippage={'type': 'fixed', 'value': 0},
            commission={'type': 'per_lot', 'value': 0}
        )
    }
    
    return presets.get(preset, presets['default'])
