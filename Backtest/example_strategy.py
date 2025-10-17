# MUST NOT EDIT SimBroker
"""
Example Strategy: Simple Moving Average Crossover
==================================================

Demonstrates proper usage of the SimBroker API.

Strategy Logic:
- Buy when fast MA crosses above slow MA
- Sell when fast MA crosses below slow MA
- Only one position at a time

Author: SimBroker Team
Date: 2025-10-16
"""

from sim_broker import SimBroker
from config import BacktestConfig, get_realistic_config
from canonical_schema import create_signal, OrderSide, OrderAction, OrderType
from datetime import datetime
import pandas as pd
from typing import Dict, List
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleMAStrategy:
    """
    Simple Moving Average Crossover Strategy
    
    Parameters:
    - fast_period: Fast MA period (default: 10)
    - slow_period: Slow MA period (default: 30)
    - size: Position size (default: 100)
    """
    
    def __init__(self, broker: SimBroker, fast_period: int = 10, slow_period: int = 30, size: int = 100):
        """
        Initialize strategy
        
        Args:
            broker: SimBroker instance
            fast_period: Fast MA period
            slow_period: Slow MA period
            size: Position size
        """
        self.broker = broker
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.size = size
        
        # State tracking
        self.price_history: Dict[str, List[float]] = {}
        self.last_signal: Dict[str, str] = {}  # symbol -> "long" or "short" or None
        
        logger.info(
            f"Strategy initialized: MA({fast_period}/{slow_period}), size={size}"
        )
    
    def on_bar(self, timestamp: datetime, data: Dict[str, Dict]):
        """
        Called for each bar of market data
        
        Args:
            timestamp: Current bar timestamp
            data: Market data dict {symbol: {open, high, low, close, volume}}
        """
        for symbol, bars in data.items():
            self._process_symbol(timestamp, symbol, bars)
    
    def _process_symbol(self, timestamp: datetime, symbol: str, bars: Dict):
        """Process a single symbol"""
        # Update price history
        close_price = bars['close']
        
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        
        self.price_history[symbol].append(close_price)
        
        # Need enough data for slow MA
        if len(self.price_history[symbol]) < self.slow_period:
            return
        
        # Calculate MAs
        prices = self.price_history[symbol]
        fast_ma = sum(prices[-self.fast_period:]) / self.fast_period
        slow_ma = sum(prices[-self.slow_period:]) / self.slow_period
        
        # Previous MAs for crossover detection
        if len(prices) < self.slow_period + 1:
            return
        
        prev_fast_ma = sum(prices[-(self.fast_period+1):-1]) / self.fast_period
        prev_slow_ma = sum(prices[-(self.slow_period+1):-1]) / self.slow_period
        
        # Detect crossovers
        bullish_cross = prev_fast_ma <= prev_slow_ma and fast_ma > slow_ma
        bearish_cross = prev_fast_ma >= prev_slow_ma and fast_ma < slow_ma
        
        # Check current position
        snapshot = self.broker.get_account_snapshot()
        position = next(
            (p for p in snapshot['positions'] if p['symbol'] == symbol),
            None
        )
        
        has_long = position is not None and position['size'] > 0
        has_short = position is not None and position['size'] < 0
        
        # Entry/Exit logic
        if bullish_cross and not has_long:
            logger.info(
                f"{timestamp} | {symbol}: Bullish cross detected "
                f"(Fast MA: {fast_ma:.2f}, Slow MA: {slow_ma:.2f})"
            )
            
            # Close short if any
            if has_short:
                self._exit_position(timestamp, symbol, abs(position['size']))
            
            # Enter long
            self._enter_long(timestamp, symbol, self.size)
        
        elif bearish_cross and has_long:
            logger.info(
                f"{timestamp} | {symbol}: Bearish cross detected "
                f"(Fast MA: {fast_ma:.2f}, Slow MA: {slow_ma:.2f})"
            )
            
            # Exit long
            self._exit_position(timestamp, symbol, self.size)
    
    def _enter_long(self, timestamp: datetime, symbol: str, size: int):
        """Enter long position"""
        signal = create_signal(
            timestamp=timestamp,
            symbol=symbol,
            side=OrderSide.BUY,
            action=OrderAction.ENTRY,
            order_type=OrderType.MARKET,
            size=size,
            strategy_id="simple-ma"
        )
        
        order_id = self.broker.submit_signal(signal.to_dict())
        if order_id:
            logger.info(f"{timestamp} | {symbol}: Entered long {size} shares (order: {order_id})")
        else:
            logger.error(f"{timestamp} | {symbol}: Failed to enter long")
    
    def _exit_position(self, timestamp: datetime, symbol: str, size: int):
        """Exit position"""
        signal = create_signal(
            timestamp=timestamp,
            symbol=symbol,
            side=OrderSide.SELL,
            action=OrderAction.EXIT,
            order_type=OrderType.MARKET,
            size=size,
            strategy_id="simple-ma"
        )
        
        order_id = self.broker.submit_signal(signal.to_dict())
        if order_id:
            logger.info(f"{timestamp} | {symbol}: Exited position {size} shares (order: {order_id})")
        else:
            logger.error(f"{timestamp} | {symbol}: Failed to exit position")


def generate_sample_data(symbol: str = "AAPL", days: int = 365) -> pd.DataFrame:
    """
    Generate sample price data for testing
    
    Args:
        symbol: Symbol to generate data for
        days: Number of days
    
    Returns:
        DataFrame with OHLCV data
    """
    import numpy as np
    
    np.random.seed(42)
    
    # Generate random walk
    start_price = 150.0
    prices = [start_price]
    
    for _ in range(days):
        change = np.random.normal(0, 2)
        new_price = max(prices[-1] + change, 50)  # Minimum price 50
        prices.append(new_price)
    
    # Create OHLCV
    data = []
    start_date = datetime(2024, 1, 1)
    
    for i, close in enumerate(prices[1:]):
        date = start_date + pd.Timedelta(days=i)
        
        # Generate OHLC from close
        open_price = prices[i]
        high = max(open_price, close) + abs(np.random.normal(0, 0.5))
        low = min(open_price, close) - abs(np.random.normal(0, 0.5))
        volume = int(np.random.uniform(500000, 2000000))
        
        data.append({
            'timestamp': date,
            'symbol': symbol,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    return pd.DataFrame(data)


def run_backtest():
    """Main backtest runner"""
    
    logger.info("=" * 70)
    logger.info("Starting Simple MA Crossover Backtest")
    logger.info("=" * 70)
    
    # 1. Configure broker
    config = get_realistic_config()  # Realistic fees and slippage
    config.start_cash = 100000
    config.save_trades = True
    
    logger.info(f"Configuration:")
    logger.info(f"  Start Cash: ${config.start_cash:,.2f}")
    logger.info(f"  Fee: ${config.fee_flat} + {config.fee_pct*100:.2f}%")
    logger.info(f"  Slippage: {config.slippage_pct*100:.3f}%")
    
    # 2. Initialize broker
    broker = SimBroker(config)
    logger.info(f"SimBroker initialized (API v{broker.API_VERSION})")
    
    # 3. Initialize strategy
    strategy = SimpleMAStrategy(
        broker=broker,
        fast_period=10,
        slow_period=30,
        size=100
    )
    
    # 4. Load/generate data
    logger.info("Generating sample data...")
    df = generate_sample_data(symbol="AAPL", days=365)
    logger.info(f"Data loaded: {len(df)} bars")
    
    # 5. Run simulation
    logger.info("Running simulation...")
    
    for index, row in df.iterrows():
        timestamp = row['timestamp']
        
        market_data = {
            row['symbol']: {
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row['volume']
            }
        }
        
        # Strategy analyzes and may emit signals
        strategy.on_bar(timestamp, market_data)
        
        # Broker processes signals and updates state
        broker.step_to(timestamp, market_data)
    
    logger.info("Simulation complete")
    
    # 6. Get results
    logger.info("Computing metrics...")
    metrics = broker.compute_metrics()
    
    # 7. Export results
    import os
    os.makedirs("results", exist_ok=True)
    
    broker.export_trades("results/trades.csv")
    logger.info("Exported trades to results/trades.csv")
    
    # Save metrics
    import json
    with open("results/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info("Exported metrics to results/metrics.json")
    
    # 8. Print summary
    print("\n" + "=" * 70)
    print("BACKTEST RESULTS")
    print("=" * 70)
    print(f"Period: {metrics['start_date']} to {metrics['end_date']}")
    print(f"Duration: {metrics['duration_days']} days")
    print()
    print(f"Starting Capital: ${metrics['start_cash']:,.2f}")
    print(f"Final Equity: ${metrics['final_equity']:,.2f}")
    print(f"Net Profit: ${metrics['net_profit']:,.2f} ({metrics['total_return_pct']:.2f}%)")
    print()
    print(f"Total Trades: {metrics['total_trades']}")
    print(f"Winning Trades: {metrics['winning_trades']}")
    print(f"Losing Trades: {metrics['losing_trades']}")
    print(f"Win Rate: {metrics['win_rate']*100:.1f}%")
    print()
    print(f"Profit Factor: {metrics['profit_factor']:.2f}")
    print(f"Average Trade: ${metrics['average_trade']:.2f}")
    print(f"Average Win: ${metrics['average_win']:.2f}")
    print(f"Average Loss: ${metrics['average_loss']:.2f}")
    print()
    print(f"Max Drawdown: ${metrics['max_drawdown_abs']:,.2f} ({metrics['max_drawdown_pct']*100:.2f}%)")
    print(f"Recovery Factor: {metrics['recovery_factor']:.2f}")
    print()
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"Sortino Ratio: {metrics['sortino_ratio']:.2f}")
    print(f"Calmar Ratio: {metrics['calmar_ratio']:.2f}")
    print()
    print(f"Max Consecutive Wins: {metrics['max_consecutive_wins']}")
    print(f"Max Consecutive Losses: {metrics['max_consecutive_losses']}")
    print()
    print(f"Total Commission: ${metrics['total_commission']:,.2f}")
    print(f"Total Slippage: ${metrics['total_slippage']:,.2f}")
    print("=" * 70)
    
    # Get component statistics
    stats = broker.get_statistics()
    print("\nComponent Statistics:")
    print(f"  Orders Created: {stats['orders']['orders_created']}")
    print(f"  Orders Filled: {stats['orders']['orders_filled']}")
    print(f"  Fills Executed: {stats['execution']['fills_executed']}")
    print(f"  Partial Fills: {stats['execution']['partial_fills']}")
    
    return metrics


if __name__ == "__main__":
    try:
        metrics = run_backtest()
    except Exception as e:
        logger.error(f"Backtest failed: {e}", exc_info=True)
        raise
