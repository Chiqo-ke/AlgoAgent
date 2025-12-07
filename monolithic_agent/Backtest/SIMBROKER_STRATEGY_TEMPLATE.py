"""
SimBroker Strategy Template with Dynamic Data Loading
======================================================

This template demonstrates how to create a trading strategy using:
1. SimBroker for signal simulation (NOT backtesting.py)
2. DataLoader for dynamic data fetching
3. User-configurable symbol, period, and timeframe

Version: 2.0.0
Last Updated: 2025-12-04
"""

# Add parent directory to path for imports
import sys
from pathlib import Path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig
from Backtest.canonical_schema import create_signal, OrderSide, OrderAction, OrderType
from Backtest.data_loader import fetch_market_data, add_indicators
from datetime import datetime
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExampleEMACrossStrategy:
    """
    Example EMA Crossover Strategy using SimBroker
    
    Features:
    - Uses SimBroker for signal simulation
    - Loads data dynamically using DataLoader
    - User can specify any symbol, period, timeframe
    """
    
    def __init__(self, broker: SimBroker, symbol: str = "AAPL", **params):
        """
        Initialize strategy
        
        Args:
            broker: SimBroker instance
            symbol: Trading symbol
            **params: Additional strategy parameters
        """
        self.broker = broker
        self.symbol = symbol
        self.params = params
        
        # Strategy state
        self.position_size = 0
        self.in_position = False
        self.signal_count = 0
        
        # EMA parameters
        self.ema_fast = params.get('ema_fast', 12)
        self.ema_slow = params.get('ema_slow', 26)
        
        logger.info(f"Strategy initialized: {symbol}")
        logger.info(f"EMA Fast: {self.ema_fast}, EMA Slow: {self.ema_slow}")
    
    def on_bar(self, timestamp: datetime, data: dict):
        """
        Process each bar of market data
        
        Args:
            timestamp: Current bar timestamp
            data: Market data dictionary with structure:
                  {symbol: {'open': float, 'high': float, 'low': float, 
                           'close': float, 'volume': float, 
                           'EMA_12': float, 'EMA_26': float, ...}}
        """
        # Get data for this symbol
        symbol_data = data.get(self.symbol)
        if not symbol_data:
            return
        
        # Extract price and indicators
        close = symbol_data.get('close')
        ema_fast = symbol_data.get(f'EMA_{self.ema_fast}')
        ema_slow = symbol_data.get(f'EMA_{self.ema_slow}')
        
        # Check if indicators are available
        if ema_fast is None or ema_slow is None:
            return
        
        # Entry logic: EMA fast crosses above EMA slow
        if not self.in_position and ema_fast > ema_slow:
            signal = create_signal(
                signal_id=f"entry_{self.signal_count}",
                timestamp=timestamp,
                symbol=self.symbol,
                side=OrderSide.BUY,
                action=OrderAction.ENTRY,
                order_type=OrderType.MARKET,
                size=100,  # 100 shares
                price=close,
                reason=f"EMA cross: {ema_fast:.2f} > {ema_slow:.2f}"
            )
            
            order_id = self.broker.submit_signal(signal.to_dict())
            if order_id:
                self.in_position = True
                self.position_size = 100
                self.signal_count += 1
                logger.info(f"ENTRY: {timestamp.date()} @ {close:.2f}")
        
        # Exit logic: EMA fast crosses below EMA slow
        elif self.in_position and ema_fast < ema_slow:
            signal = create_signal(
                signal_id=f"exit_{self.signal_count}",
                timestamp=timestamp,
                symbol=self.symbol,
                side=OrderSide.SELL,
                action=OrderAction.EXIT,
                order_type=OrderType.MARKET,
                size=self.position_size,
                price=close,
                reason=f"EMA cross: {ema_fast:.2f} < {ema_slow:.2f}"
            )
            
            order_id = self.broker.submit_signal(signal.to_dict())
            if order_id:
                self.in_position = False
                self.position_size = 0
                self.signal_count += 1
                logger.info(f"EXIT: {timestamp.date()} @ {close:.2f}")


def run_backtest(
    symbol: str = "AAPL",
    period: str = "1y", 
    interval: str = "1d",
    cash: float = 10000,
    commission: float = 0.002,
    ema_fast: int = 12,
    ema_slow: int = 26
):
    """
    Run backtest with dynamic data loading
    
    Args:
        symbol: Trading symbol (e.g., 'AAPL', 'MSFT', 'EURUSD')
        period: Data period - Options:
                '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'max'
        interval: Data interval - Options:
                  '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo'
        cash: Initial cash
        commission: Commission rate (0.002 = 0.2%)
        ema_fast: Fast EMA period
        ema_slow: Slow EMA period
    
    Returns:
        Dictionary with backtest metrics
    """
    logger.info("="*70)
    logger.info(f"STARTING BACKTEST: {symbol}")
    logger.info(f"Period: {period}, Interval: {interval}")
    logger.info(f"Initial Cash: ${cash:,.2f}, Commission: {commission*100}%")
    logger.info("="*70)
    
    # 1. Fetch market data using DataLoader
    logger.info(f"\n[1/6] Fetching market data for {symbol}...")
    df = fetch_market_data(symbol, period=period, interval=interval)
    logger.info(f"Loaded {len(df)} bars from {df.index[0].date()} to {df.index[-1].date()}")
    
    # 2. Add required indicators
    logger.info(f"\n[2/6] Computing technical indicators...")
    indicators_config = {
        f'EMA_{ema_fast}': {'name': 'EMA', 'timeperiod': ema_fast},
        f'EMA_{ema_slow}': {'name': 'EMA', 'timeperiod': ema_slow}
    }
    
    # Compute each indicator separately
    result_df = df.copy()
    metadata = {}
    
    for indicator_key, indicator_params in indicators_config.items():
        indicator_name = indicator_params.pop('name')
        ind_df, ind_meta = add_indicators(df, {indicator_name: indicator_params})
        # Join to result
        for col in ind_df.columns:
            if col not in result_df.columns:
                result_df[col] = ind_df[col]
        metadata[indicator_key] = ind_meta
    
    df_with_indicators = result_df
    logger.info(f"Added indicators: {[k for k in indicators_config.keys()]}")
    
    # 3. Setup SimBroker
    logger.info(f"\n[3/6] Initializing SimBroker...")
    config = BacktestConfig(
        initial_capital=cash,
        commission_rate=commission
    )
    broker = SimBroker(config)
    
    # 4. Initialize strategy
    logger.info(f"\n[4/6] Initializing strategy...")
    strategy = ExampleEMACrossStrategy(
        broker, 
        symbol=symbol,
        ema_fast=ema_fast,
        ema_slow=ema_slow
    )
    
    # 5. Run simulation row by row
    logger.info(f"\n[5/6] Running simulation...")
    for timestamp, row in df_with_indicators.iterrows():
        # Step broker to current timestamp
        broker.step_to(timestamp)
        
        # Prepare data dictionary
        data = {
            symbol: {
                'open': row['Open'],
                'high': row['High'],
                'low': row['Low'],
                'close': row['Close'],
                'volume': row['Volume'],
                # Add all indicator columns dynamically
                **{k: row[k] for k in row.index if k not in ['Open', 'High', 'Low', 'Close', 'Volume']}
            }
        }
        
        # Call strategy logic
        strategy.on_bar(timestamp, data)
    
    # 6. Get results
    logger.info(f"\n[6/6] Computing metrics...")
    metrics = broker.compute_metrics()
    
    # 7. Print results
    print("\n" + "="*70)
    print(f"BACKTEST RESULTS: {symbol} ({period}, {interval})")
    print("="*70)
    
    if metrics:
        for key, value in metrics.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
    else:
        print("  No trades executed")
    
    print("="*70)
    
    return metrics


if __name__ == "__main__":
    """
    USER CONFIGURATION
    ==================
    
    Change these parameters to test different configurations:
    
    SYMBOL: Any valid ticker
    - Stocks: 'AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN'
    - Forex: 'EURUSD=X', 'GBPUSD=X', 'USDJPY=X'
    - Crypto: 'BTC-USD', 'ETH-USD'
    
    PERIOD: How much historical data to fetch
    - '1d'   : 1 day
    - '5d'   : 5 days
    - '1mo'  : 1 month
    - '3mo'  : 3 months
    - '6mo'  : 6 months
    - '1y'   : 1 year (default)
    - '2y'   : 2 years
    - '5y'   : 5 years
    - 'max'  : Maximum available
    
    INTERVAL: Data granularity
    - '1m'   : 1 minute bars (only for recent data)
    - '5m'   : 5 minute bars
    - '15m'  : 15 minute bars
    - '1h'   : 1 hour bars
    - '1d'   : 1 day bars (default)
    - '1wk'  : 1 week bars
    """
    
    # Example 1: Default - AAPL with 1 year of daily data
    results = run_backtest(
        symbol="AAPL",
        period="1y",
        interval="1d",
        cash=10000,
        commission=0.002,
        ema_fast=12,
        ema_slow=26
    )
    
    # Example 2: Test with different symbol and timeframe
    # Uncomment to try:
    # results = run_backtest(
    #     symbol="MSFT",
    #     period="6mo",
    #     interval="1h",
    #     cash=20000,
    #     commission=0.001
    # )
    
    # Example 3: Test with crypto
    # Uncomment to try:
    # results = run_backtest(
    #     symbol="BTC-USD",
    #     period="3mo",
    #     interval="1d",
    #     cash=10000,
    #     commission=0.001
    # )
