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
from backtesting.test import SMA  # Built-in indicators


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
        
        # Calculate EMAs using pandas ewm - returns numpy array
        def EMA(values, n):
            """Calculate EMA and return as numpy array"""
            return pd.Series(values).ewm(span=n, adjust=False).mean().values
        
        # Use self.I to make indicators plottable
        self.ema_fast = self.I(EMA, close, self.fast_period)
        self.ema_slow = self.I(EMA, close, self.slow_period)
        
        print(f"[INIT] Strategy initialized with fast={self.fast_period}, slow={self.slow_period}")
    
    def next(self):
        """
        Implement strategy logic.
        """
        # Skip if we don't have valid indicator values
        if np.isnan(self.ema_fast[-1]) or np.isnan(self.ema_slow[-1]):
            return
        
        # Buy condition: fast EMA crosses above slow EMA
        if crossover(self.ema_fast, self.ema_slow):
            if not self.position:
                print(f"[BUY SIGNAL] Bar {len(self.data)} | Price: ${self.data.Close[-1]:.2f} | "
                      f"EMA_fast: {self.ema_fast[-1]:.2f} | EMA_slow: {self.ema_slow[-1]:.2f}")
                self.buy()
                print(f"[ENTRY] Bought at ${self.data.Close[-1]:.2f}")
        
        # Sell condition: fast EMA crosses below slow EMA
        elif crossover(self.ema_slow, self.ema_fast):
            if self.position:
                print(f"[SELL SIGNAL] Bar {len(self.data)} | Price: ${self.data.Close[-1]:.2f} | "
                      f"EMA_fast: {self.ema_fast[-1]:.2f} | EMA_slow: {self.ema_slow[-1]:.2f}")
                self.position.close()
                print(f"[EXIT] Sold at ${self.data.Close[-1]:.2f}")


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
    # Import from parent directory (already in sys.path)
    from backtesting_adapter import fetch_and_prepare_data, BacktestingAdapter
    
    print(f"[DATA] Fetching {symbol} data from {start_date} to {end_date}...")
    
    # Fetch data
    data = fetch_and_prepare_data(symbol, start_date, end_date, interval)
    
    print(f"[DATA] Loaded {len(data)} bars")
    print(f"[DATA] Columns: {list(data.columns)}")
    print(f"[DATA] Date range: {data.index[0]} to {data.index[-1]}")
    
    # Run backtest
    print(f"\n[BACKTEST] Running backtest...")
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
    print(f"Bars: {len(data)}")
    print()
    print(results)
    print("=" * 70)
    
    return results, adapter


if __name__ == "__main__":
    # Activate venv first
    print("Testing EMA Strategy with detailed logging...")
    print("=" * 70)
    
    # Run the backtest
    results, adapter = run_backtest(
        strategy_class=EMAStrategy,
        symbol="AAPL",
        start_date="2024-01-01",
        end_date="2024-10-31",
        cash=10000,
        commission=0.002
    )
    
    print("\n[TEST] Test completed!")
    
    # Optionally plot results (opens interactive browser chart)
    # adapter.plot()
    
    # Optionally plot results (opens interactive browser chart)
    # adapter.plot()