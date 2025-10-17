"""
Canonical Schema Definitions for SimBroker
===========================================

This module defines the IMMUTABLE JSON schemas for all data structures
used in the backtesting simulation. These schemas MUST NOT be modified
by AI-generated strategy code.

Last updated: 2025-10-16
Version: 1.0.0
"""

from typing import Any, Dict, List, Optional, Literal
from datetime import datetime
from dataclasses import dataclass, asdict, field
import uuid


# ============================================================================
# ENUMERATIONS (Canonical Values)
# ============================================================================

class OrderSide:
    """Order side constants"""
    BUY = "BUY"
    SELL = "SELL"


class OrderAction:
    """Signal action types"""
    ENTRY = "ENTRY"
    EXIT = "EXIT"
    MODIFY = "MODIFY"
    CANCEL = "CANCEL"


class OrderType:
    """Order type constants"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderStatus:
    """Order lifecycle status"""
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class SizeType:
    """Position sizing method"""
    SHARES = "SHARES"           # Fixed number of shares/contracts
    CONTRACTS = "CONTRACTS"     # Fixed number of contracts
    NOTIONAL = "NOTIONAL"       # Dollar amount
    RISK_PERCENT = "RISK_PERCENT"  # % of equity at risk
    MARGIN_PERCENT = "MARGIN_PERCENT"  # % of available margin
    KELLY = "KELLY"             # Kelly criterion


# ============================================================================
# CANONICAL DATA CLASSES
# ============================================================================

@dataclass
class Signal:
    """
    Canonical Signal Schema (Input from Strategy)
    
    This is the primary interface for strategies to communicate
    trading intentions to the SimBroker.
    """
    signal_id: str
    timestamp: datetime
    symbol: str
    side: str  # OrderSide.BUY or OrderSide.SELL
    action: str  # OrderAction value
    order_type: str  # OrderType value
    size: float
    size_type: str = SizeType.SHARES
    price: Optional[float] = None  # Required for LIMIT/STOP_LIMIT
    stop_price: Optional[float] = None  # For STOP/STOP_LIMIT
    risk_params: Optional[Dict[str, Any]] = None
    strategy_id: str = "default"
    meta: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with ISO timestamps"""
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        return d
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Signal':
        """Create Signal from dictionary"""
        data = data.copy()
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        if 'meta' not in data:
            data['meta'] = {}
        if 'risk_params' not in data:
            data['risk_params'] = None
        return cls(**data)


@dataclass
class Order:
    """
    Canonical Order Schema (Internal Representation)
    
    Represents an order managed by the SimBroker.
    """
    order_id: str
    signal_id: str
    timestamp: datetime
    symbol: str
    side: str
    order_type: str
    size_requested: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    size_filled: float = 0.0
    status: str = OrderStatus.PENDING
    fills: List['Fill'] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    meta: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        d['created_at'] = self.created_at.isoformat()
        d['updated_at'] = self.updated_at.isoformat()
        d['fills'] = [f.to_dict() for f in self.fills]
        return d
    
    @property
    def remaining_size(self) -> float:
        """Calculate unfilled size"""
        return self.size_requested - self.size_filled
    
    @property
    def is_complete(self) -> bool:
        """Check if order is fully filled"""
        return self.status in (OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED)


@dataclass
class Fill:
    """
    Canonical Fill/Trade Record Schema (Output)
    
    Represents an executed fill for part or all of an order.
    """
    trade_id: str
    order_id: str
    signal_id: str
    timestamp: datetime
    symbol: str
    side: str
    price: float
    size: float
    commission: float
    slippage: float
    realized_pnl: float = 0.0
    fee_currency: str = "USD"
    note: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        return d
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Fill':
        """Create Fill from dictionary"""
        data = data.copy()
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        if 'meta' not in data:
            data['meta'] = {}
        return cls(**data)
    
    @property
    def notional(self) -> float:
        """Calculate notional value of the fill"""
        return self.price * self.size
    
    @property
    def total_cost(self) -> float:
        """Calculate total cost including fees"""
        return self.notional + self.commission


@dataclass
class Position:
    """
    Position representation in the account
    """
    symbol: str
    size: float  # Positive for long, negative for short
    avg_price: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    last_price: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @property
    def market_value(self) -> float:
        """Current market value of position"""
        return self.size * self.last_price
    
    @property
    def cost_basis(self) -> float:
        """Total cost basis"""
        return self.size * self.avg_price


@dataclass
class AccountSnapshot:
    """
    Canonical Account Snapshot Schema (Periodic State)
    
    Represents the complete account state at a point in time.
    Used for equity curve construction.
    """
    timestamp: datetime
    cash: float
    equity: float
    positions: List[Position]
    portfolio_value: float = 0.0
    used_margin: float = 0.0
    available_margin: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    meta: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        d = {
            'timestamp': self.timestamp.isoformat(),
            'cash': self.cash,
            'equity': self.equity,
            'portfolio_value': self.portfolio_value,
            'used_margin': self.used_margin,
            'available_margin': self.available_margin,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl,
            'positions': [p.to_dict() for p in self.positions],
            'meta': self.meta
        }
        return d
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AccountSnapshot':
        """Create AccountSnapshot from dictionary"""
        data = data.copy()
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        if 'positions' in data:
            data['positions'] = [Position(**p) if isinstance(p, dict) else p for p in data['positions']]
        if 'meta' not in data:
            data['meta'] = {}
        return cls(**data)


@dataclass
class RiskParams:
    """
    Risk parameters for position sizing
    """
    risk_percent: Optional[float] = None  # % of equity to risk
    stop_loss_price: Optional[float] = None
    stop_loss_distance: Optional[float] = None
    max_position_size: Optional[float] = None
    kelly_fraction: Optional[float] = 0.25  # Kelly multiplier
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


# ============================================================================
# SCHEMA VALIDATION
# ============================================================================

def validate_signal(signal_dict: Dict[str, Any]) -> List[str]:
    """
    Validate a signal dictionary against the canonical schema.
    
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Required fields
    required = ['signal_id', 'timestamp', 'symbol', 'side', 'action', 'order_type', 'size']
    for field in required:
        if field not in signal_dict:
            errors.append(f"Missing required field: {field}")
    
    # Validate enums
    if 'side' in signal_dict and signal_dict['side'] not in [OrderSide.BUY, OrderSide.SELL]:
        errors.append(f"Invalid side: {signal_dict['side']}")
    
    if 'action' in signal_dict and signal_dict['action'] not in [
        OrderAction.ENTRY, OrderAction.EXIT, OrderAction.MODIFY, OrderAction.CANCEL
    ]:
        errors.append(f"Invalid action: {signal_dict['action']}")
    
    if 'order_type' in signal_dict and signal_dict['order_type'] not in [
        OrderType.MARKET, OrderType.LIMIT, OrderType.STOP, OrderType.STOP_LIMIT
    ]:
        errors.append(f"Invalid order_type: {signal_dict['order_type']}")
    
    # Validate price requirements
    if signal_dict.get('order_type') in [OrderType.LIMIT, OrderType.STOP_LIMIT]:
        if 'price' not in signal_dict or signal_dict['price'] is None:
            errors.append(f"Price required for {signal_dict.get('order_type')} orders")
    
    if signal_dict.get('order_type') in [OrderType.STOP, OrderType.STOP_LIMIT]:
        if 'stop_price' not in signal_dict or signal_dict['stop_price'] is None:
            errors.append(f"Stop price required for {signal_dict.get('order_type')} orders")
    
    # Validate size
    if 'size' in signal_dict:
        try:
            size = float(signal_dict['size'])
            if size <= 0:
                errors.append("Size must be positive")
        except (ValueError, TypeError):
            errors.append("Size must be a number")
    
    return errors


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_id() -> str:
    """Generate a unique ID"""
    return str(uuid.uuid4())


def create_signal(
    timestamp: datetime,
    symbol: str,
    side: str,
    action: str,
    order_type: str,
    size: float,
    **kwargs
) -> Signal:
    """
    Helper to create a valid Signal object
    """
    return Signal(
        signal_id=generate_id(),
        timestamp=timestamp,
        symbol=symbol,
        side=side,
        action=action,
        order_type=order_type,
        size=size,
        **kwargs
    )


# ============================================================================
# SCHEMA VERSION INFO
# ============================================================================

SCHEMA_VERSION = "1.0.0"
SCHEMA_DATE = "2025-10-16"

SCHEMA_INFO = {
    "version": SCHEMA_VERSION,
    "date": SCHEMA_DATE,
    "immutable": True,
    "description": "Canonical schemas for SimBroker backtesting engine",
    "entities": {
        "Signal": "Input from strategy to broker",
        "Order": "Internal order representation",
        "Fill": "Executed trade record",
        "Position": "Open position state",
        "AccountSnapshot": "Complete account state at timestamp",
        "RiskParams": "Position sizing parameters"
    }
}


if __name__ == "__main__":
    # Example usage
    signal = create_signal(
        timestamp=datetime.utcnow(),
        symbol="AAPL",
        side=OrderSide.BUY,
        action=OrderAction.ENTRY,
        order_type=OrderType.MARKET,
        size=100,
        strategy_id="example-strategy"
    )
    
    print("Example Signal:")
    print(signal.to_dict())
    
    # Validate
    errors = validate_signal(signal.to_dict())
    print(f"\nValidation: {'PASSED' if not errors else 'FAILED'}")
    if errors:
        for error in errors:
            print(f"  - {error}")
