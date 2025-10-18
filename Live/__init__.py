"""
AlgoAgent Live Trading Module

Production-ready live trading system that reuses Backtesting strategies
and executes trades via MetaTrader5.

Components:
- config: Configuration management and MT5 constants
- backtesting_bridge: Bridge to Backtesting module APIs
- mt5_connector: MetaTrader5 connection management
- order_executor: Order execution with retries and idempotency
- state_manager: Position and state tracking
- audit_logger: Persistent audit trail in SQLite
- alerts: Notification system (Telegram, webhook)
- dashboard: Web monitoring interface
- live_trader: Main orchestrator and trading loop

Quick Start:
    >>> from config import LiveConfig
    >>> from live_trader import LiveTrader
    >>> 
    >>> config = LiveConfig()
    >>> trader = LiveTrader(config, strategy_path='../Backtest/codes/my_strategy.py')
    >>> trader.start()

For detailed documentation, see README.md
"""

__version__ = '1.0.0'
__author__ = 'AlgoAgent'

from .config import LiveConfig, setup_logging, MT5Constants
from .mt5_connector import MT5Connector
from .order_executor import OrderExecutor
from .state_manager import StateManager
from .audit_logger import AuditLogger
from .backtesting_bridge import BacktestingBridge
from .alerts import AlertSystem
from .dashboard import Dashboard
from .live_trader import LiveTrader

__all__ = [
    'LiveConfig',
    'setup_logging',
    'MT5Constants',
    'MT5Connector',
    'OrderExecutor',
    'StateManager',
    'AuditLogger',
    'BacktestingBridge',
    'AlertSystem',
    'Dashboard',
    'LiveTrader'
]
