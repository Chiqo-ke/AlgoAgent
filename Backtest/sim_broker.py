"""
SimBroker - Simulation Broker/Execution Engine
===============================================

The stable, immutable core of the backtesting system.
This API MUST NOT be modified by AI-generated strategy code.

Last updated: 2025-10-16
Version: 1.0.0

IMPORTANT: # MUST NOT EDIT SimBroker
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from pathlib import Path

from .canonical_schema import (
    Signal, Order, Fill, AccountSnapshot,
    OrderStatus
)
from .config import BacktestConfig
from .order_manager import OrderManager
from .execution_simulator import ExecutionSimulator, MarketData
from .account_manager import AccountManager
from .metrics_engine import MetricsEngine
from .validators import Validators


logger = logging.getLogger(__name__)


class SimBroker:
    """
    Stable Simulation Broker API
    
    This is the IMMUTABLE interface for backtesting.
    AI-generated strategies must use ONLY these public methods.
    
    Stable API Methods (DO NOT CHANGE):
    - submit_signal(signal: dict) -> str
    - get_order(order_id: str) -> dict
    - cancel_order(order_id: str) -> bool
    - step_to(timestamp: datetime) -> None
    - get_account_snapshot() -> dict
    - get_equity_curve() -> List[dict]
    - export_trades(path: str) -> None
    - compute_metrics() -> dict
    """
    
    # API Version - increment only for breaking changes
    API_VERSION = "1.0.0"
    
    def __init__(self, config: Optional[BacktestConfig] = None):
        """
        Initialize SimBroker
        
        Args:
            config: Backtest configuration (uses defaults if None)
        """
        self.config = config or BacktestConfig()
        
        # Core components
        self.order_manager = OrderManager(self.config)
        self.execution_simulator = ExecutionSimulator(self.config)
        self.account_manager = AccountManager(self.config)
        self.metrics_engine = MetricsEngine(self.config)
        self.validators = Validators(self.config)
        
        # State
        self.current_time: Optional[datetime] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.is_running = False
        self.is_stopped = False
        
        # Storage
        self.all_fills: List[Fill] = []
        self.market_data_cache: Dict[str, MarketData] = {}
        
        # Validate configuration
        config_warnings = self.validators.validate_backtest_config()
        for warning in config_warnings:
            logger.warning(f"[{warning.severity}] {warning.message}")
        
        logger.info(f"SimBroker initialized (API v{self.API_VERSION})")
    
    # =========================================================================
    # STABLE PUBLIC API (DO NOT MODIFY)
    # =========================================================================
    
    def submit_signal(self, signal: dict) -> str:
        """
        Submit a trading signal (STABLE API)
        
        This is the primary interface for strategies to communicate
        with the broker.
        
        Args:
            signal: Signal dictionary matching canonical schema
        
        Returns:
            order_id if order created, empty string if rejected
        
        Example:
            >>> signal = {
            ...     "signal_id": "abc-123",
            ...     "timestamp": datetime.now(),
            ...     "symbol": "AAPL",
            ...     "side": "BUY",
            ...     "action": "ENTRY",
            ...     "order_type": "MARKET",
            ...     "size": 100
            ... }
            >>> order_id = broker.submit_signal(signal)
        """
        if self.is_stopped:
            logger.warning("Broker stopped - signal rejected")
            return ""
        
        # Convert dict to Signal object
        try:
            signal_obj = Signal.from_dict(signal)
        except Exception as e:
            logger.error(f"Invalid signal format: {e}")
            return ""
        
        # Validate signal
        errors = self.validators.validate_signal(signal_obj)
        if errors:
            logger.error(f"Signal validation failed: {errors}")
            return ""
        
        # Create order
        order = self.order_manager.create_order_from_signal(signal_obj)
        
        if order is None:
            return ""
        
        return order.order_id
    
    def get_order(self, order_id: str) -> dict:
        """
        Get order details (STABLE API)
        
        Args:
            order_id: Order ID
        
        Returns:
            Order dictionary, or empty dict if not found
        """
        order = self.order_manager.get_order(order_id)
        if order:
            return order.to_dict()
        return {}
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order (STABLE API)
        
        Args:
            order_id: Order ID to cancel
        
        Returns:
            True if cancelled, False if not found or cannot cancel
        """
        order = self.order_manager.get_order(order_id)
        if not order:
            return False
        
        if order.is_complete:
            logger.warning(f"Order {order_id} already complete")
            return False
        
        order.status = OrderStatus.CANCELLED
        order.updated_at = self.current_time or datetime.utcnow()
        
        logger.info(f"Order cancelled: {order_id}")
        return True
    
    def step_to(self, timestamp: datetime, market_data: Optional[Dict[str, Any]] = None):
        """
        Advance simulation to timestamp and process fills (STABLE API)
        
        This method:
        1. Updates current time
        2. Processes active orders against market data
        3. Updates account state
        4. Records equity snapshot
        
        Args:
            timestamp: Timestamp to advance to
            market_data: Optional dict with market data
                        {symbol: {open, high, low, close, volume}}
        """
        if self.is_stopped:
            return
        
        if not self.is_running:
            self.start_time = timestamp
            self.is_running = True
        
        self.current_time = timestamp
        self.end_time = timestamp
        
        # Update market data cache
        if market_data:
            self._update_market_data(market_data, timestamp)
        
        # Process orders
        self._process_active_orders()
        
        # Update account prices
        self._update_account_prices()
        
        # Create snapshot
        snapshot = self.account_manager.create_snapshot(timestamp)
        
        # Check drawdown stop
        if self.validators.check_drawdown_stop(
            snapshot.equity,
            self.account_manager.peak_equity
        ):
            self.is_stopped = True
            logger.error("Backtest stopped due to max drawdown")
        
        # Log progress
        if self.config.log_every_n_bars > 0:
            snapshot_count = len(self.account_manager.equity_curve)
            if snapshot_count % self.config.log_every_n_bars == 0:
                logger.info(
                    f"Progress: {snapshot_count} bars | "
                    f"Equity: ${snapshot.equity:,.2f} | "
                    f"Trades: {self.account_manager.total_trades}"
                )
    
    def get_account_snapshot(self) -> dict:
        """
        Get current account state (STABLE API)
        
        Returns:
            AccountSnapshot dictionary
        """
        snapshot = self.account_manager.create_snapshot(
            self.current_time or datetime.utcnow()
        )
        return snapshot.to_dict()
    
    def get_equity_curve(self) -> List[dict]:
        """
        Get equity curve snapshots (STABLE API)
        
        Returns:
            List of AccountSnapshot dictionaries
        """
        return [s.to_dict() for s in self.account_manager.get_equity_curve()]
    
    def export_trades(self, path: str):
        """
        Export trades to CSV (STABLE API)
        
        Args:
            path: File path for export
        """
        import csv
        
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', newline='') as f:
            if not self.all_fills:
                f.write("No trades executed\n")
                return
            
            fieldnames = [
                'trade_id', 'order_id', 'signal_id', 'timestamp',
                'symbol', 'side', 'price', 'size', 'commission',
                'slippage', 'realized_pnl', 'note'
            ]
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for fill in self.all_fills:
                row = fill.to_dict()
                # Keep only relevant fields
                row = {k: row[k] for k in fieldnames if k in row}
                writer.writerow(row)
        
        logger.info(f"Exported {len(self.all_fills)} trades to {path}")
    
    def compute_metrics(self) -> dict:
        """
        Compute performance metrics (STABLE API)
        
        Returns:
            Dictionary of all metrics
        """
        if not self.start_time or not self.end_time:
            logger.warning("No time range - returning empty metrics")
            return self.metrics_engine._get_empty_metrics(
                datetime.utcnow(),
                datetime.utcnow()
            )
        
        metrics = self.metrics_engine.compute_all_metrics(
            self.all_fills,
            self.account_manager.get_equity_curve(),
            self.start_time,
            self.end_time
        )
        
        return metrics
    
    # =========================================================================
    # INTERNAL METHODS (Not part of stable API)
    # =========================================================================
    
    def _update_market_data(self, data: Dict[str, Any], timestamp: datetime):
        """Update market data cache"""
        for symbol, bars in data.items():
            market_data = MarketData(
                timestamp=timestamp,
                symbol=symbol,
                open=bars.get('open', bars.get('close', 0)),
                high=bars.get('high', bars.get('close', 0)),
                low=bars.get('low', bars.get('close', 0)),
                close=bars.get('close', 0),
                volume=bars.get('volume', 0),
                bid=bars.get('bid'),
                ask=bars.get('ask')
            )
            self.market_data_cache[symbol] = market_data
    
    def _process_active_orders(self):
        """Process all active orders"""
        active_orders = self.order_manager.get_active_orders()
        
        for order in active_orders:
            # Get market data for symbol
            market_data = self.market_data_cache.get(order.symbol)
            if not market_data:
                continue
            
            # Try to fill order
            fills = self.execution_simulator.process_orders([order], market_data)
            
            # Process fills
            for fill in fills:
                self._process_fill(fill, order)
    
    def _process_fill(self, fill: Fill, order: Order):
        """Process a fill"""
        # Store fill
        self.all_fills.append(fill)
        
        # Update order
        self.order_manager.update_order_fill(
            order.order_id,
            fill.size,
            fill.timestamp
        )
        
        # Update account
        self.account_manager.process_fill(fill)
    
    def _update_account_prices(self):
        """Update account with latest prices"""
        prices = {
            symbol: data.close
            for symbol, data in self.market_data_cache.items()
        }
        self.account_manager.update_prices(prices)
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics
        
        Returns:
            Dictionary of statistics from all components
        """
        return {
            'broker': {
                'api_version': self.API_VERSION,
                'is_running': self.is_running,
                'is_stopped': self.is_stopped,
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'end_time': self.end_time.isoformat() if self.end_time else None,
            },
            'orders': self.order_manager.get_statistics(),
            'execution': self.execution_simulator.get_statistics(),
            'account': self.account_manager.get_statistics(),
        }
    
    def reset(self):
        """Reset broker state (for multiple backtests)"""
        self.order_manager.reset()
        self.execution_simulator.reset()
        self.account_manager.reset()
        self.validators.clear_warnings()
        
        self.current_time = None
        self.start_time = None
        self.end_time = None
        self.is_running = False
        self.is_stopped = False
        
        self.all_fills.clear()
        self.market_data_cache.clear()
        
        logger.info("SimBroker reset")


# Export stable API version
__version__ = SimBroker.API_VERSION


if __name__ == "__main__":
    # Example usage
    from canonical_schema import create_signal, OrderSide, OrderAction, OrderType
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize broker
    config = BacktestConfig(
        start_cash=100000,
        fee_flat=1.0,
        fee_pct=0.001,
        slippage_pct=0.0005
    )
    
    broker = SimBroker(config)
    
    print(f"SimBroker API Version: {broker.API_VERSION}\n")
    
    # Submit a signal
    signal = create_signal(
        timestamp=datetime(2025, 1, 1, 9, 30),
        symbol="AAPL",
        side=OrderSide.BUY,
        action=OrderAction.ENTRY,
        order_type=OrderType.MARKET,
        size=100
    )
    
    order_id = broker.submit_signal(signal.to_dict())
    print(f"Order submitted: {order_id}\n")
    
    # Simulate market data and step
    market_data = {
        "AAPL": {
            "open": 150.0,
            "high": 151.0,
            "low": 149.5,
            "close": 150.5,
            "volume": 1000000
        }
    }
    
    broker.step_to(datetime(2025, 1, 1, 9, 31), market_data)
    
    # Get account snapshot
    snapshot = broker.get_account_snapshot()
    print("Account Snapshot:")
    print(f"  Cash: ${snapshot['cash']:.2f}")
    print(f"  Equity: ${snapshot['equity']:.2f}")
    print(f"  Positions: {len(snapshot['positions'])}\n")
    
    # Get statistics
    stats = broker.get_statistics()
    print("Statistics:")
    print(f"  Orders created: {stats['orders']['orders_created']}")
    print(f"  Fills executed: {stats['execution']['fills_executed']}")
    print(f"  Total trades: {stats['account']['total_trades']}\n")
    
    # Compute metrics
    metrics = broker.compute_metrics()
    print("Metrics:")
    print(f"  Net profit: ${metrics['net_profit']:.2f}")
    print(f"  Total trades: {metrics['total_trades']}")
