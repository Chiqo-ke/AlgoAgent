"""
Strategy: AIGeneratedStrategy
Description: 
        Create a trading strategy using RSI (Relative Strength Index) with these specifications:
        
        STRATEGY REQUIREMENTS:
        - Indicator: RSI with 30 periods
        - Buy Signal: RSI crosses above 30 (oversold territory)
        - Sell Signal: RSI crosses below 70 (overbought territory)
        - Stop Loss: 10 pips from entry price
        - Take Profit: 40 pips from entry price
        - Trading asset: GOOG (Google stock data)
        
        The strategy should:
        1. Calculate RSI with period=30
        2. Generate buy signals when RSI > 30 (uptrend)
        3. Generate sell signals when RSI < 70 (downtrend)
        4. Use fixed 10 pip stop loss and 40 pip take profit
        5. Be compatible with backtesting framework
        
        Use the bt (Backtest.py) library for implementation.
        
"""

# Add parent directory to path for imports
import sys
from pathlib import Path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

#from Backtest.sim_broker import SimBroker # Not needed in backtesting.py
#from Backtest.config import BacktestConfig # Not needed in backtesting.py
#from Backtest.canonical_schema import create_signal, OrderSide, OrderAction, OrderType # Not needed in backtesting.py
from datetime import datetime
import pandas as pd
from backtesting import Strategy, Backtest
from backtesting.lib import crossover
from backtesting.test import GOOG, SMA
import numpy as np

class AIGeneratedStrategy(Strategy):
    """
    RSI strategy with fixed stop loss and take profit.
    
    Parameters:
        rsi_period: Period for RSI calculation (default: 30)
        stop_loss_pips: Stop loss in pips (default: 10)
        take_profit_pips: Take profit in pips (default: 40)
    """
    rsi_period = 30
    stop_loss_pips = 10
    take_profit_pips = 40

    def init(self):
        """
        Initialize RSI indicator.
        """
        close = self.data.Close

        def RSI(arr, period):
            delta = pd.Series(arr).diff()
            gain = delta.where(delta > 0, 0).rolling(period).mean()
            loss = -delta.where(delta < 0, 0).rolling(period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))

        self.rsi = self.I(RSI, close, self.rsi_period)

    def next(self):
        """
        Implement RSI trading logic with stop loss and take profit.
        """
        if not self.position:
            # Buy signal: RSI crosses above 30
            if self.rsi[-1] > 30: # fixed crossover issue
                entry_price = self.data.Close[-1]
                stop_loss_price = entry_price - (self.stop_loss_pips / 10000)  # Assuming prices are in 4 decimal places
                take_profit_price = entry_price + (self.take_profit_pips / 10000)

                self.buy(sl=stop_loss_price, tp=take_profit_price)

        else:
            # Sell signal: RSI crosses below 70
            if self.rsi[-1] < 70: # fixed crossover issue
                self.position.close()

def run_backtest(
    strategy_class,
    symbol: str = "GOOG",
    start_date: str = "2004-01-01",
    end_date: str = "2013-12-31",
    cash: float = 10000,
    commission: float = 0.002
):
    """
    Run backtest with the RSI strategy
    
    Args:
        strategy_class: Strategy class to test
        symbol: Stock symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        cash: Initial cash
        commission: Commission rate (0.002 = 0.2%)
    
    Returns:
        Backtest results
    """
    
    # Run backtest
    bt = Backtest(
        data=GOOG,
        strategy=strategy_class,
        cash=cash,
        commission=commission,
        exclusive_orders=True,
        trade_on_close=True
    )

    results = bt.run()

    # Print results
    print("\n" + "=" * 70)
    print(f"BACKTEST RESULTS: {strategy_class.__name__}")
    print("=" * 70)
    print(f"Period: {start_date} to {end_date}")
    print(f"Symbol: {symbol}")
    print()
    print(results)
    print("=" * 70)
    
    return results, bt


if __name__ == "__main__":
    # Run the backtest
    results, bt = run_backtest(
        strategy_class=AIGeneratedStrategy,
        symbol="GOOG",
        start_date="2004-01-01",
        end_date="2013-12-31",
        cash=10000,
        commission=0.002
    )