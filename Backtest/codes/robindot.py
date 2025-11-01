"""
Strategy: robin.dot
Description: This is a template strategy to demonstrate backtesting.py integration with SimBroker.  It does nothing.
Generated: 2024-11-02
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
from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig
from Backtest.canonical_schema import create_signal, OrderSide, OrderAction, OrderType


class robin_dot(Strategy):
    """
    Template strategy to demonstrate backtesting.py integration with SimBroker.

    Parameters (can be optimized):
        n1 = 10  # Example: Fast MA period
        n2 = 20  # Example: Slow MA period
    """

    # Define strategy parameters as class attributes
    # These can be optimized using bt.optimize()
    n1 = 10  # Example: Fast MA period
    n2 = 20  # Example: Slow MA period

    def init(self):
        """
        Initialize indicators and preprocessed data.
        This runs once at the start of backtest.
        Use self.I() to wrap indicators for proper integration.
        """
        close = self.data.Close

        # Example: Create moving averages
        self.sma1 = self.I(SMA, close, self.n1)
        self.sma2 = self.I(SMA, close, self.n2)

        # You can create custom indicators using lambda
        # self.custom_ind = self.I(lambda x: your_function(x), close)

    def next(self):
        """
        Execute strategy logic for each bar.
        This is called for each row of data sequentially.
        """
        # Entry logic
        if not self.position:
            if crossover(self.sma1, self.sma2):
                self.buy()  # Enter long position

        # Exit logic
        elif self.position:
            if crossover(self.sma2, self.sma1):
                self.position.close()  # Close position


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
        strategy_class=robin_dot,
        symbol="AAPL",
        start_date="2024-01-01",
        end_date="2024-10-31",
        cash=10000,
        commission=0.002
    )

    # Optionally plot results (opens interactive browser chart)
    # adapter.plot()