"""
Strategy: EMA
Description: Simple EMA crossover strategy using backtesting.py
Generated: 2024-11-03
Framework: backtesting.py (kernc)
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import backtesting.py components
from backtesting import Strategy
from backtesting.lib import crossover
from backtesting.test import SMA, GOOG  # Built-in indicators

# Import data fetcher
from Data.data_fetcher import DataFetcher


class EMAStrategy(Strategy):
    """
    EMA crossover strategy.
    
    Parameters:
        fast_period = 12
        slow_period = 26
    """
    
    # Define strategy parameters
    fast_period = 12
    slow_period = 26
    
    def init(self):
        """
        Initialize indicators.
        """
        close = self.data.Close
        
        # Calculate fast EMA
        def EMA(series, period):
            return pd.Series(series).ewm(span=period).mean()
        
        self.ema_fast = self.I(EMA, close, self.fast_period)
        self.ema_slow = self.I(EMA, close, self.slow_period)
    
    def next(self):
        """
        Implement strategy logic.
        """
        # Buy condition: fast EMA crosses above slow EMA
        if crossover(self.ema_fast, self.ema_slow):
            self.buy()
        
        # Sell condition: fast EMA crosses below slow EMA, close position
        elif crossover(self.ema_slow, self.ema_fast):
            self.position.close()


def run_backtest(
    strategy_class,
    symbol: str = "AAPL",
    start_date: str = "2024-01-01",
    end_date: str = "2024-10-31",
    interval: str = "1d",
    cash: float = 10000,
    commission: float = 0.002
):
    """
    Run backtest with the strategy
    
    Args:
        strategy_class: Strategy class to test
        symbol: Stock symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        interval: Data interval
        cash: Initial cash
        commission: Commission rate (0.002 = 0.2%)
    
    Returns:
        Backtest results
    """
    from Backtest.backtesting_adapter import fetch_and_prepare_data, BacktestingAdapter
    
    # Fetch data
    data = fetch_and_prepare_data(symbol, start_date, end_date, interval)
    
    # Run backtest
    adapter = BacktestingAdapter(
        data=data,
        strategy_class=strategy_class,
        cash=cash,
        commission=commission
    )
    
    results = adapter.run()
    
    # Print results
    print("\n" + "=" * 70)
    print(f"BACKTEST RESULTS: {strategy_class.__name__}")
    print("=" * 70)
    print(f"Period: {start_date} to {end_date}")
    print(f"Symbol: {symbol}")
    print()
    print(results)
    print("=" * 70)
    
    # Get detailed stats
    stats = adapter.get_stats()
    print("\nDETAILED STATISTICS:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    return results, adapter


if __name__ == "__main__":
    # Run the backtest
    results, adapter = run_backtest(
        strategy_class=EMAStrategy,
        symbol="AAPL",
        start_date="2024-01-01",
        end_date="2024-10-31",
        cash=10000,
        commission=0.002
    )
    
    # Optionally plot results (opens interactive browser chart)
    # adapter.plot()