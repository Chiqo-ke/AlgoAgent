"""
Test Strategy: Simple Moving Average Crossover
Description: Buy when fast MA crosses above slow MA, sell when fast MA crosses below slow MA
Generated: 2025-10-31
Framework: backtesting.py (kernc)
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Also add grandparent for Data module
grandparent_dir = parent_dir.parent
if str(grandparent_dir) not in sys.path:
    sys.path.insert(0, str(grandparent_dir))

# Import backtesting.py components
from backtesting import Strategy
from backtesting.lib import crossover
from backtesting.test import SMA


class SimpleMACrossover(Strategy):
    """
    Simple Moving Average Crossover Strategy
    
    Parameters:
        fast_period: Period for fast moving average (default: 10)
        slow_period: Period for slow moving average (default: 30)
    """
    
    # Define strategy parameters
    fast_period = 10
    slow_period = 30
    
    def init(self):
        """
        Initialize indicators
        """
        close = self.data.Close
        
        # Create moving averages
        self.ma_fast = self.I(SMA, close, self.fast_period)
        self.ma_slow = self.I(SMA, close, self.slow_period)
    
    def next(self):
        """
        Execute strategy logic for each bar
        """
        # Entry logic - buy when fast MA crosses above slow MA
        if not self.position:
            if crossover(self.ma_fast, self.ma_slow):
                self.buy()
        
        # Exit logic - sell when fast MA crosses below slow MA
        elif self.position:
            if crossover(self.ma_slow, self.ma_fast):
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
    # Import here to ensure path is set
    from Backtest.backtesting_adapter import fetch_and_prepare_data, BacktestingAdapter
    
    # Fetch data
    print(f"\n📊 Fetching data for {symbol}...")
    data = fetch_and_prepare_data(symbol, start_date, end_date, interval)
    print(f"✓ Loaded {len(data)} bars")
    
    # Run backtest
    print(f"\n🚀 Running backtest...")
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
    print("\n📈 DETAILED STATISTICS:")
    print(f"  Start Cash: ${stats['start_cash']:,.2f}")
    print(f"  Final Equity: ${stats['final_equity']:,.2f}")
    print(f"  Net Profit: ${stats['net_profit']:,.2f}")
    print(f"  Total Return: {stats['total_return_pct']:.2f}%")
    print(f"  Total Trades: {stats['total_trades']}")
    print(f"  Win Rate: {stats['win_rate']*100:.1f}%")
    print(f"  Max Drawdown: {stats['max_drawdown_pct']*100:.2f}%")
    print(f"  Sharpe Ratio: {stats['sharpe_ratio']:.2f}")
    
    # Get trades
    trades = adapter.get_trades()
    if len(trades) > 0:
        print(f"\n📋 TRADES ({len(trades)} total):")
        print(trades.head(10))
        
        # Export trades
        trades_file = Path(__file__).parent / "trades" / f"{symbol}_{strategy_class.__name__}_trades.csv"
        trades_file.parent.mkdir(exist_ok=True)
        adapter.export_trades(str(trades_file))
        print(f"\n✓ Trades exported to: {trades_file}")
    
    return results, adapter


if __name__ == "__main__":
    # Run the backtest
    print("=" * 70)
    print("SIMPLE MA CROSSOVER STRATEGY TEST")
    print("=" * 70)
    
    results, adapter = run_backtest(
        strategy_class=SimpleMACrossover,
        symbol="AAPL",
        start_date="2024-01-01",
        end_date="2024-10-31",
        cash=10000,
        commission=0.002
    )
    
    print("\n✅ Backtest complete!")
    print("\nTo view interactive chart, uncomment the following line:")
    print("# adapter.plot()")
