"""
Execution Simulator
===================

Simulates order execution with realistic fill logic including:
- Market/limit/stop order fills
- Slippage modeling
- Partial fills
- Liquidity constraints
- Latency simulation

Last updated: 2025-10-16
Version: 1.0.0
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import random
import logging
import math

from canonical_schema import (
    Order, Fill, OrderType, OrderStatus, OrderSide,
    generate_id
)
from config import BacktestConfig


logger = logging.getLogger(__name__)


class MarketData:
    """Container for market data at a point in time"""
    
    def __init__(
        self,
        timestamp: datetime,
        symbol: str,
        open: float,
        high: float,
        low: float,
        close: float,
        volume: float = 0.0,
        bid: Optional[float] = None,
        ask: Optional[float] = None
    ):
        self.timestamp = timestamp
        self.symbol = symbol
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.bid = bid if bid is not None else close
        self.ask = ask if ask is not None else close
    
    @property
    def spread(self) -> float:
        """Bid-ask spread"""
        return self.ask - self.bid
    
    @property
    def mid(self) -> float:
        """Mid price"""
        return (self.bid + self.ask) / 2
    
    @property
    def volatility_proxy(self) -> float:
        """Simple intrabar volatility estimate"""
        if self.low >= self.high:
            return 0.0
        return (self.high - self.low) / self.close


class ExecutionSimulator:
    """
    Simulates realistic order execution
    
    Responsibilities:
    - Determine if orders can be filled based on market data
    - Calculate fill prices with slippage
    - Handle partial fills based on liquidity
    - Apply commissions and fees
    - Simulate execution latency
    """
    
    def __init__(self, config: BacktestConfig):
        """
        Initialize execution simulator
        
        Args:
            config: Backtest configuration
        """
        self.config = config
        
        # Set random seed for reproducibility
        if config.random_seed is not None:
            random.seed(config.random_seed)
        
        # Statistics
        self.fills_executed = 0
        self.partial_fills = 0
        self.total_slippage = 0.0
        self.total_commission = 0.0
    
    def process_orders(
        self,
        orders: List[Order],
        market_data: MarketData
    ) -> List[Fill]:
        """
        Process a list of orders against current market data
        
        Args:
            orders: List of active orders to process
            market_data: Current market data
        
        Returns:
            List of fills generated
        """
        fills = []
        
        for order in orders:
            # Skip if order is for different symbol
            if order.symbol != market_data.symbol:
                continue
            
            # Try to fill order
            order_fills = self._try_fill_order(order, market_data)
            fills.extend(order_fills)
        
        return fills
    
    def _try_fill_order(
        self,
        order: Order,
        market_data: MarketData
    ) -> List[Fill]:
        """
        Attempt to fill an order
        
        Args:
            order: Order to fill
            market_data: Current market data
        
        Returns:
            List of fills (0 or more)
        """
        fills = []
        
        # Determine if order can be filled
        can_fill, fill_price = self._check_fill_conditions(order, market_data)
        
        if not can_fill:
            return fills
        
        # Calculate fill size (may be partial)
        fill_size = self._calculate_fill_size(order, market_data)
        
        if fill_size <= 0:
            return fills
        
        # Apply slippage
        slipped_price = self._apply_slippage(
            fill_price,
            order.side,
            market_data
        )
        
        # Calculate commission
        commission = self._calculate_commission(slipped_price, fill_size)
        
        # Create fill
        fill = Fill(
            trade_id=generate_id(),
            order_id=order.order_id,
            signal_id=order.signal_id,
            timestamp=self._apply_latency(market_data.timestamp),
            symbol=order.symbol,
            side=order.side,
            price=slipped_price,
            size=fill_size,
            commission=commission,
            slippage=abs(slipped_price - fill_price),
            note=f"Simulated {order.order_type} fill"
        )
        
        fills.append(fill)
        
        # Update statistics
        self.fills_executed += 1
        if fill_size < order.remaining_size:
            self.partial_fills += 1
        self.total_slippage += fill.slippage * fill_size
        self.total_commission += commission
        
        logger.debug(
            f"Fill: {order.side} {fill_size} {order.symbol} @ {slipped_price:.2f} "
            f"(slippage: {fill.slippage:.4f}, commission: {commission:.2f})"
        )
        
        return fills
    
    def _check_fill_conditions(
        self,
        order: Order,
        market_data: MarketData
    ) -> Tuple[bool, float]:
        """
        Check if order can be filled and determine fill price
        
        Args:
            order: Order to check
            market_data: Current market data
        
        Returns:
            (can_fill: bool, fill_price: float)
        """
        if order.order_type == OrderType.MARKET:
            return self._check_market_order(order, market_data)
        
        elif order.order_type == OrderType.LIMIT:
            return self._check_limit_order(order, market_data)
        
        elif order.order_type == OrderType.STOP:
            return self._check_stop_order(order, market_data)
        
        elif order.order_type == OrderType.STOP_LIMIT:
            return self._check_stop_limit_order(order, market_data)
        
        return False, 0.0
    
    def _check_market_order(
        self,
        order: Order,
        market_data: MarketData
    ) -> Tuple[bool, float]:
        """Check market order fill conditions"""
        # Market orders fill at open of next bar (or current close)
        if self.config.fill_policy == "aggressive":
            # Best case: fill at open
            fill_price = market_data.open
        elif self.config.fill_policy == "conservative":
            # Worst case: fill at close
            fill_price = market_data.close
        else:  # realistic
            # Use bid/ask if available
            if self.config.use_bid_ask:
                fill_price = market_data.ask if order.side == OrderSide.BUY else market_data.bid
            else:
                fill_price = market_data.open
        
        return True, fill_price
    
    def _check_limit_order(
        self,
        order: Order,
        market_data: MarketData
    ) -> Tuple[bool, float]:
        """Check limit order fill conditions"""
        if order.price is None:
            return False, 0.0
        
        limit_price = order.price
        
        # Check if price was touched during the bar
        if order.side == OrderSide.BUY:
            # Buy limit: fill if low <= limit
            if market_data.low <= limit_price:
                # Fill at limit or better
                fill_price = min(limit_price, market_data.open)
                return True, fill_price
        else:  # SELL
            # Sell limit: fill if high >= limit
            if market_data.high >= limit_price:
                # Fill at limit or better
                fill_price = max(limit_price, market_data.open)
                return True, fill_price
        
        return False, 0.0
    
    def _check_stop_order(
        self,
        order: Order,
        market_data: MarketData
    ) -> Tuple[bool, float]:
        """Check stop order fill conditions"""
        if order.stop_price is None:
            return False, 0.0
        
        stop_price = order.stop_price
        
        # Check if stop was triggered
        if order.side == OrderSide.BUY:
            # Buy stop: trigger if high >= stop
            if market_data.high >= stop_price:
                # Becomes market order, fill at open or worse
                fill_price = max(stop_price, market_data.open)
                return True, fill_price
        else:  # SELL
            # Sell stop: trigger if low <= stop
            if market_data.low <= stop_price:
                # Becomes market order, fill at open or worse
                fill_price = min(stop_price, market_data.open)
                return True, fill_price
        
        return False, 0.0
    
    def _check_stop_limit_order(
        self,
        order: Order,
        market_data: MarketData
    ) -> Tuple[bool, float]:
        """Check stop-limit order fill conditions"""
        if order.stop_price is None or order.price is None:
            return False, 0.0
        
        # First check if stop triggered
        stop_triggered = False
        
        if order.side == OrderSide.BUY:
            if market_data.high >= order.stop_price:
                stop_triggered = True
        else:  # SELL
            if market_data.low <= order.stop_price:
                stop_triggered = True
        
        if not stop_triggered:
            return False, 0.0
        
        # If triggered, check limit fill (same as limit order)
        return self._check_limit_order(order, market_data)
    
    def _calculate_fill_size(
        self,
        order: Order,
        market_data: MarketData
    ) -> float:
        """
        Calculate how much of the order can be filled
        
        Args:
            order: Order to fill
            market_data: Current market data
        
        Returns:
            Fill size (may be less than remaining size for partial fills)
        """
        remaining = order.remaining_size
        
        if not self.config.allow_partial_fills:
            return remaining
        
        # Check liquidity constraint
        if self.config.use_volume and market_data.volume > 0:
            max_fillable = market_data.volume * self.config.liquidity_limit_pct
            
            if remaining > max_fillable:
                # Partial fill due to liquidity
                fill_size = max_fillable
                logger.debug(
                    f"Partial fill due to liquidity: {fill_size:.2f} / {remaining:.2f}"
                )
                return max(fill_size, self.config.min_fill_size)
        
        return remaining
    
    def _apply_slippage(
        self,
        price: float,
        side: str,
        market_data: MarketData
    ) -> float:
        """
        Apply slippage to fill price
        
        Args:
            price: Base fill price
            side: Order side (BUY/SELL)
            market_data: Current market data
        
        Returns:
            Slipped price
        """
        if self.config.slippage_model == "fixed":
            slippage = price * self.config.slippage_pct + self.config.slippage_const
        
        elif self.config.slippage_model == "volatility":
            # Slippage proportional to volatility
            volatility = market_data.volatility_proxy
            slippage = price * volatility * self.config.slippage_pct
        
        elif self.config.slippage_model == "spread":
            # Slippage based on bid-ask spread
            slippage = market_data.spread / 2
        
        else:
            slippage = 0.0
        
        # Apply slippage in unfavorable direction
        if side == OrderSide.BUY:
            return price + slippage
        else:
            return price - slippage
    
    def _calculate_commission(self, price: float, size: float) -> float:
        """
        Calculate commission/fees for a fill
        
        Args:
            price: Fill price
            size: Fill size
        
        Returns:
            Commission amount
        """
        notional = price * size
        commission = self.config.fee_flat + (notional * self.config.fee_pct)
        return commission
    
    def _apply_latency(self, timestamp: datetime) -> datetime:
        """
        Apply execution latency
        
        Args:
            timestamp: Original timestamp
        
        Returns:
            Adjusted timestamp
        """
        if self.config.latency_ms > 0:
            return timestamp + timedelta(milliseconds=self.config.latency_ms)
        return timestamp
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get execution simulator statistics"""
        return {
            'fills_executed': self.fills_executed,
            'partial_fills': self.partial_fills,
            'total_slippage': self.total_slippage,
            'total_commission': self.total_commission,
            'avg_slippage_per_fill': (
                self.total_slippage / self.fills_executed
                if self.fills_executed > 0 else 0.0
            ),
            'avg_commission_per_fill': (
                self.total_commission / self.fills_executed
                if self.fills_executed > 0 else 0.0
            )
        }
    
    def reset(self):
        """Reset execution simulator state"""
        self.fills_executed = 0
        self.partial_fills = 0
        self.total_slippage = 0.0
        self.total_commission = 0.0
        
        if self.config.random_seed is not None:
            random.seed(self.config.random_seed)
        
        logger.info("Execution simulator reset")


if __name__ == "__main__":
    # Example usage
    from canonical_schema import OrderSide
    
    logging.basicConfig(level=logging.DEBUG)
    
    config = BacktestConfig(
        slippage_pct=0.001,
        fee_flat=1.0,
        fee_pct=0.001
    )
    
    simulator = ExecutionSimulator(config)
    
    # Create market data
    market_data = MarketData(
        timestamp=datetime.utcnow(),
        symbol="AAPL",
        open=150.0,
        high=151.5,
        low=149.5,
        close=150.5,
        volume=1000000
    )
    
    # Create an order
    order = Order(
        order_id=generate_id(),
        signal_id=generate_id(),
        timestamp=datetime.utcnow(),
        symbol="AAPL",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        size_requested=100
    )
    
    # Process order
    fills = simulator.process_orders([order], market_data)
    
    print(f"Generated {len(fills)} fills")
    for fill in fills:
        print(f"  {fill.side} {fill.size} @ ${fill.price:.2f}")
        print(f"  Commission: ${fill.commission:.2f}")
        print(f"  Slippage: ${fill.slippage:.4f}")
    
    print("\nStatistics:")
    for k, v in simulator.get_statistics().items():
        print(f"  {k}: {v}")
