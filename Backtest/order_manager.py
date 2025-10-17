"""
Order Manager
=============

Converts signals to orders, manages order lifecycle, assigns IDs.
Part of the stable SimBroker core.

Last updated: 2025-10-16
Version: 1.0.0
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import defaultdict
import logging

from canonical_schema import (
    Signal, Order, OrderStatus, OrderAction, OrderType,
    generate_id
)
from config import BacktestConfig


logger = logging.getLogger(__name__)


class OrderManager:
    """
    Manages order creation, tracking, and lifecycle.
    
    Responsibilities:
    - Convert signals to orders
    - Assign unique order IDs
    - Track order status
    - Manage order modifications and cancellations
    - Maintain order history
    """
    
    def __init__(self, config: BacktestConfig):
        """
        Initialize order manager
        
        Args:
            config: Backtest configuration
        """
        self.config = config
        
        # Order storage
        self.orders: Dict[str, Order] = {}  # order_id -> Order
        self.active_orders: Dict[str, Order] = {}  # order_id -> Order
        self.completed_orders: Dict[str, Order] = {}  # order_id -> Order
        
        # Indexing
        self.orders_by_symbol: Dict[str, List[str]] = defaultdict(list)
        self.orders_by_signal: Dict[str, str] = {}  # signal_id -> order_id
        
        # Statistics
        self.orders_created = 0
        self.orders_filled = 0
        self.orders_cancelled = 0
        self.orders_rejected = 0
    
    def create_order_from_signal(self, signal: Signal) -> Optional[Order]:
        """
        Convert a signal to an order
        
        Args:
            signal: Signal from strategy
        
        Returns:
            Order object, or None if signal is invalid/rejected
        """
        # Handle different signal actions
        if signal.action == OrderAction.CANCEL:
            return self._handle_cancel_signal(signal)
        
        if signal.action == OrderAction.MODIFY:
            return self._handle_modify_signal(signal)
        
        # Create new order for ENTRY/EXIT
        order = Order(
            order_id=generate_id(),
            signal_id=signal.signal_id,
            timestamp=signal.timestamp,
            symbol=signal.symbol,
            side=signal.side,
            order_type=signal.order_type,
            size_requested=signal.size,
            price=signal.price,
            stop_price=signal.stop_price,
            status=OrderStatus.PENDING,
            meta=signal.meta.copy()
        )
        
        # Validate order
        if not self._validate_order(order):
            order.status = OrderStatus.REJECTED
            self.orders_rejected += 1
            logger.warning(f"Order rejected: {order.order_id}")
            return None
        
        # Store order
        self._store_order(order)
        self.orders_created += 1
        
        logger.info(
            f"Order created: {order.order_id} | "
            f"{order.side} {order.size_requested} {order.symbol} @ "
            f"{order.order_type}"
        )
        
        return order
    
    def _validate_order(self, order: Order) -> bool:
        """
        Validate order before acceptance
        
        Args:
            order: Order to validate
        
        Returns:
            True if valid, False otherwise
        """
        # Check minimum size
        if order.size_requested < self.config.min_lot_size:
            logger.error(
                f"Order size {order.size_requested} below minimum "
                f"{self.config.min_lot_size}"
            )
            return False
        
        # Check max position size if configured
        if self.config.max_position_size:
            if order.size_requested > self.config.max_position_size:
                logger.error(
                    f"Order size {order.size_requested} exceeds maximum "
                    f"{self.config.max_position_size}"
                )
                return False
        
        # Validate price for limit orders
        if order.order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT]:
            if order.price is None or order.price <= 0:
                logger.error(f"Invalid limit price: {order.price}")
                return False
        
        # Validate stop price for stop orders
        if order.order_type in [OrderType.STOP, OrderType.STOP_LIMIT]:
            if order.stop_price is None or order.stop_price <= 0:
                logger.error(f"Invalid stop price: {order.stop_price}")
                return False
        
        return True
    
    def _handle_cancel_signal(self, signal: Signal) -> Optional[Order]:
        """
        Handle order cancellation signal
        
        Args:
            signal: Cancellation signal
        
        Returns:
            Cancelled order, or None if not found/already complete
        """
        # Find order by signal ID
        if signal.signal_id not in self.orders_by_signal:
            logger.warning(
                f"Cannot cancel: no order found for signal {signal.signal_id}"
            )
            return None
        
        order_id = self.orders_by_signal[signal.signal_id]
        order = self.orders.get(order_id)
        
        if not order:
            logger.warning(f"Order {order_id} not found")
            return None
        
        if order.is_complete:
            logger.warning(f"Order {order_id} already complete")
            return None
        
        # Cancel the order
        order.status = OrderStatus.CANCELLED
        order.updated_at = signal.timestamp
        self._move_to_completed(order)
        self.orders_cancelled += 1
        
        logger.info(f"Order cancelled: {order_id}")
        
        return order
    
    def _handle_modify_signal(self, signal: Signal) -> Optional[Order]:
        """
        Handle order modification signal
        
        Args:
            signal: Modification signal
        
        Returns:
            Modified order, or None if not found/cannot modify
        """
        # Find original order
        if signal.signal_id not in self.orders_by_signal:
            logger.warning(
                f"Cannot modify: no order found for signal {signal.signal_id}"
            )
            return None
        
        order_id = self.orders_by_signal[signal.signal_id]
        order = self.orders.get(order_id)
        
        if not order:
            logger.warning(f"Order {order_id} not found")
            return None
        
        if order.is_complete:
            logger.warning(f"Order {order_id} already complete, cannot modify")
            return None
        
        # Update order parameters
        if signal.price is not None:
            order.price = signal.price
        if signal.stop_price is not None:
            order.stop_price = signal.stop_price
        if signal.size > 0:
            # Adjust for already filled size
            order.size_requested = signal.size + order.size_filled
        
        order.updated_at = signal.timestamp
        
        logger.info(f"Order modified: {order_id}")
        
        return order
    
    def _store_order(self, order: Order):
        """Store order in data structures"""
        self.orders[order.order_id] = order
        self.active_orders[order.order_id] = order
        self.orders_by_symbol[order.symbol].append(order.order_id)
        self.orders_by_signal[order.signal_id] = order.order_id
    
    def _move_to_completed(self, order: Order):
        """Move order from active to completed"""
        if order.order_id in self.active_orders:
            del self.active_orders[order.order_id]
        self.completed_orders[order.order_id] = order
    
    def update_order_fill(self, order_id: str, fill_size: float, timestamp: datetime):
        """
        Update order with fill information
        
        Args:
            order_id: Order ID
            fill_size: Size of fill
            timestamp: Fill timestamp
        """
        order = self.orders.get(order_id)
        if not order:
            logger.error(f"Order {order_id} not found for fill update")
            return
        
        order.size_filled += fill_size
        order.updated_at = timestamp
        
        # Update status
        if order.size_filled >= order.size_requested:
            order.status = OrderStatus.FILLED
            self._move_to_completed(order)
            self.orders_filled += 1
            logger.info(f"Order filled: {order_id}")
        elif order.size_filled > 0:
            order.status = OrderStatus.PARTIAL
            logger.info(
                f"Order partially filled: {order_id} "
                f"({order.size_filled}/{order.size_requested})"
            )
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        return self.orders.get(order_id)
    
    def get_active_orders(
        self,
        symbol: Optional[str] = None,
        order_type: Optional[str] = None
    ) -> List[Order]:
        """
        Get active orders with optional filters
        
        Args:
            symbol: Filter by symbol
            order_type: Filter by order type
        
        Returns:
            List of matching active orders
        """
        orders = list(self.active_orders.values())
        
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        
        if order_type:
            orders = [o for o in orders if o.order_type == order_type]
        
        return orders
    
    def get_orders_by_symbol(self, symbol: str) -> List[Order]:
        """Get all orders for a symbol"""
        order_ids = self.orders_by_symbol.get(symbol, [])
        return [self.orders[oid] for oid in order_ids if oid in self.orders]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get order manager statistics"""
        return {
            'total_orders': len(self.orders),
            'active_orders': len(self.active_orders),
            'completed_orders': len(self.completed_orders),
            'orders_created': self.orders_created,
            'orders_filled': self.orders_filled,
            'orders_cancelled': self.orders_cancelled,
            'orders_rejected': self.orders_rejected,
            'symbols_traded': len(self.orders_by_symbol)
        }
    
    def get_all_orders(self) -> List[Order]:
        """Get all orders"""
        return list(self.orders.values())
    
    def reset(self):
        """Reset order manager state"""
        self.orders.clear()
        self.active_orders.clear()
        self.completed_orders.clear()
        self.orders_by_symbol.clear()
        self.orders_by_signal.clear()
        
        self.orders_created = 0
        self.orders_filled = 0
        self.orders_cancelled = 0
        self.orders_rejected = 0
        
        logger.info("Order manager reset")


if __name__ == "__main__":
    # Example usage
    from canonical_schema import create_signal, OrderSide
    
    logging.basicConfig(level=logging.INFO)
    
    config = BacktestConfig()
    manager = OrderManager(config)
    
    # Create a signal
    signal = create_signal(
        timestamp=datetime.utcnow(),
        symbol="AAPL",
        side=OrderSide.BUY,
        action=OrderAction.ENTRY,
        order_type=OrderType.MARKET,
        size=100
    )
    
    # Convert to order
    order = manager.create_order_from_signal(signal)
    
    if order:
        print(f"Order created: {order.order_id}")
        print(f"Active orders: {len(manager.get_active_orders())}")
        
        # Simulate fill
        manager.update_order_fill(order.order_id, 100, datetime.utcnow())
        print(f"Order status: {order.status}")
        print(f"Active orders: {len(manager.get_active_orders())}")
        
        # Stats
        print("\nStatistics:")
        for k, v in manager.get_statistics().items():
            print(f"  {k}: {v}")
