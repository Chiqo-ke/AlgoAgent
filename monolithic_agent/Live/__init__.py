"""
AlgoAgent Live Trading Module

Production-ready live trading system that reuses Backtesting strategies
and executes trades via MetaTrader5.

Components:
- config: Configuration management and MT5 constants
- backtesting_bridge: Bridge to Backtesting module APIs
- mt5_connector: MetaTrader5 connection management
- mt5_bridge_connector: HTTP bridge connector for Linux/Wine deployments
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

# MT5-dependent components require MetaTrader5 to be installed and the module
# to be imported from within the Live/ working directory (they use bare
# `from config import ...` instead of relative imports).  Wrap them so that
# importing Live.live_data_fetcher (which has no MT5 dependency) still works.
try:
    from .config import LiveConfig, setup_logging, MT5Constants
    from .mt5_connector import MT5Connector
    from .mt5_bridge_connector import MT5BridgeConnector
    from .order_executor import OrderExecutor
    from .state_manager import StateManager
    from .audit_logger import AuditLogger
    from .backtesting_bridge import BacktestingBridge
    from .alerts import AlertSystem
    from .dashboard import Dashboard
    from .live_trader import LiveTrader

    def get_mt5_connector(config: LiveConfig):  # type: ignore[misc]
        """
        Factory — returns the right connector based on config.mt5_use_bridge.

        On Linux/Wine (this VPS):   MT5_USE_BRIDGE=true  → MT5BridgeConnector
        On Windows (dev machine):   MT5_USE_BRIDGE=false → MT5Connector  (original)
        """
        if config.mt5_use_bridge:
            return MT5BridgeConnector(config, bridge_url=config.mt5_bridge_url)
        return MT5Connector(config)

except (ImportError, ModuleNotFoundError):
    pass  # MT5 components unavailable; live_data_fetcher still importable.


__all__ = [
    'LiveConfig',
    'setup_logging',
    'MT5Constants',
    'MT5Connector',
    'MT5BridgeConnector',
    'get_mt5_connector',
    'OrderExecutor',
    'StateManager',
    'AuditLogger',
    'BacktestingBridge',
    'AlertSystem',
    'Dashboard',
    'LiveTrader'
]
