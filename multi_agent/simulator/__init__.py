"""
SimBroker - Portable, Testable Trading Simulator
Provides MT5-compatible order execution simulation for backtesting strategies.
"""

from .simbroker import (
    SimBroker,
    SimConfig,
    Order,
    Fill,
    Position,
    EquityPoint,
    AccountSnapshot,
    OrderResponse,
    CloseResult,
    Event,
    OrderSide,
    OrderStatus,
    CloseReason,
    EventType,
)

__all__ = [
    'SimBroker',
    'SimConfig',
    'Order',
    'Fill',
    'Position',
    'EquityPoint',
    'AccountSnapshot',
    'OrderResponse',
    'CloseResult',
    'Event',
    'OrderSide',
    'OrderStatus',
    'CloseReason',
    'EventType',
]

__version__ = '1.0.0'
