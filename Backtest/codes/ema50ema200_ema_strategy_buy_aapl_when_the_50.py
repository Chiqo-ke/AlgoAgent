# MUST NOT EDIT SimBroker
"""
Strategy: Ema_50/ema_200EmaStrategy:
Description: Buy AAPL when the 50 EMA crosses above the 200 EMA.
Stop-loss and take-profit are optional.
Generated: 2025-10-17
Location: codes/ directory
"""

# Add parent directory to path for imports
import sys
from pathlib import Path

parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from sim_broker import SimBroker
from config import BacktestConfig
from canonical_schema import create_signal, OrderSide, OrderAction, OrderType
from data_loader import load_market_data
from datetime import datetime
import pandas as pd


class Ema_50_200EmaStrategy:  # Fixed class name
    """
    A simple EMA crossover strategy.  Buys when the 50 EMA crosses above the 200 EMA.
    """

    def __init__(self, broker: SimBroker, symbol: str = "AAPL", ema_short: int = 50, ema_long: int = 200,
                 stop_loss_pct: float = 0.0, take_profit_pct: float = 0.0):
        """
        Initializes the EMA crossover strategy.

        Args:
            broker: The SimBroker instance.
            symbol: The ticker symbol to trade.
            ema_short: The period for the short EMA.
            ema_long: The period for the long EMA.
            stop_loss_pct: Optional stop loss percentage (0.0 to disable).
            take_profit_pct: Optional take profit percentage (0.0 to disable).
        """
        self.broker = broker
        self.symbol = symbol
        self.ema_short = ema_short
        self.ema_long = ema_long
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.position_size = 100  # fixed size

        self.in_position = False  # Track if we are currently in a position

    def on_bar(self, timestamp: datetime, data: dict):
        """
        Called for each bar of market data.  Checks for EMA crossovers and triggers trades.

        Args:
            timestamp: The current bar's timestamp.
            data: A dictionary containing the market data for all symbols.
        """
        # Get market data for the strategy's symbol
        symbol_data = data.get(self.symbol)

        if not symbol_data:
            print(f"No data for {self.symbol} at {timestamp}")
            return

        # Get the EMAs from the market data.  Note the exact column names MUST match.
        ema_short_value = symbol_data.get(f'ema_{self.ema_short}', None)
        ema_long_value = symbol_data.get(f'ema_{self.ema_long}', None)

        if ema_short_value is None or ema_long_value is None:
            print(f"Missing EMA values for {self.symbol} at {timestamp}")
            return

        # Check if the EMAs have crossed
        if ema_short_value > ema_long_value and not self.in_position:
            # Generate a buy signal
            signal = create_signal(
                timestamp=timestamp,
                symbol=self.symbol,
                side=OrderSide.BUY,
                action=OrderAction.ENTRY,
                order_type=OrderType.MARKET,
                size=self.position_size
            )
            self.broker.submit_signal(signal.to_dict())
            self.in_position = True
            print(f"BUY {self.symbol} at {timestamp}")  # Log the trade

        elif ema_short_value < ema_long_value and self.in_position:
            # Generate a sell signal
            signal = create_signal(
                timestamp=timestamp,
                symbol=self.symbol,
                side=OrderSide.SELL,
                action=OrderAction.EXIT,
                order_type=OrderType.MARKET,
                size=self.position_size
            )
            self.broker.submit_signal(signal.to_dict())
            self.in_position = False
            print(f"SELL {self.symbol} at {timestamp}")  # Log the trade

        # (Simplified) Stop-loss/take-profit management. Not a full implementation
        if self.in_position:
            # Simplified logic: Just close position after some time if take_profit is set
            if self.take_profit_pct > 0.0:
                # Get the entry price (very simplified)
                positions = self.broker.get_account_snapshot()['positions']
                if positions:  # if positions exist
                    entry_price = positions[0]['avg_price'] # get the first position
                    current_price = symbol_data.get('close')
                    if current_price > entry_price * (1 + self.take_profit_pct):
                        # close position
                        signal = create_signal(
                            timestamp=timestamp,
                            symbol=self.symbol,
                            side=OrderSide.SELL,
                            action=OrderAction.EXIT,
                            order_type=OrderType.MARKET,
                            size=self.position_size
                        )
                        self.broker.submit_signal(signal.to_dict())
                        self.in_position = False
                        print(f"SELL (Take Profit) {self.symbol} at {timestamp}")  # Log the trade



def run_backtest():
    """
    Runs a backtest of the EMA crossover strategy.
    """

    # 1. Configure the backtest
    config = BacktestConfig(
        start_cash=100000,
        fee_flat=1.0,
        fee_pct=0.001,
        slippage_pct=0.0005
    )

    # 2. Initialize the broker
    broker = SimBroker(config)

    # 3. Initialize the strategy
    strategy = Ema_50_200EmaStrategy(broker, stop_loss_pct=0.0, take_profit_pct=0.05)  # use the new class name
    print(f"✓ Strategy initialized: {strategy.__class__.__name__}")

    # 4. Load the market data with EMA indicators
    indicators = {
        'EMA': {'timeperiod': strategy.ema_short},
        'EMA': {'timeperiod': strategy.ema_long},  # Add EMA_200
    }

    df, metadata = load_market_data(
        ticker=strategy.symbol,
        indicators=indicators,
        period='6mo',
        interval='1d'
    )

    # Column mapping:
    # - EMA with timeperiod=50 --> EMA_50
    # - EMA with timeperiod=200 --> EMA_200

    # 5. Verify columns (MANDATORY)
    print(f"✓ Loaded {len(df)} bars")
    print(f"✓ Columns: {list(df.columns)}")  # Show all columns

    # Ensure needed columns are present. The strategy logic will gracefully handle if EMAs are missing, but this is
    # good for debugging.  Example output:
    # ✓ Loaded 126 bars
    # ✓ Columns: ['Open', 'High', 'Low', 'Close', 'Volume', 'EMA_50', 'EMA_200']

    # 6. Run the simulation
    for timestamp, row in df.iterrows():
        # Create the market data dictionary
        market_data = {
            strategy.symbol: {
                'open': row['Open'],
                'high': row['High'],
                'low': row['Low'],
                'close': row['Close'],
                'volume': row['Volume'],
                f'ema_{strategy.ema_short}': row.get(f'EMA_{strategy.ema_short}', None),  # EMA_50
                f'ema_{strategy.ema_long}': row.get(f'EMA_{strategy.ema_long}', None),  # EMA_200
            }
        }

        # Pass the market data to the strategy
        strategy.on_bar(timestamp, market_data)

        # Step the broker
        broker.step_to(timestamp, market_data)

    # 7. Get the results
    metrics = broker.compute_metrics()

    # 8. Export the results to the codes directory
    results_dir = Path(__file__).parent / "results"
    trades_dir = Path(__file__).parent / "trades"
    results_dir.mkdir(exist_ok=True)
    trades_dir.mkdir(exist_ok=True)

    broker.export_trades(str(trades_dir / "trades.csv"))

    # 9. Print the results
    print("=" * 50)
    print("BACKTEST RESULTS")
    print("=" * 50)
    print(f"Period: {metrics['start_date']} to {metrics['end_date']}")
    print(f"Duration: {metrics['duration_days']} days")
    print()
    print(f"Starting Capital: ${metrics['start_cash']:,.2f}")
    print(f"Final Equity: ${metrics['final_equity']:,.2f}")
    print(f"Net Profit: ${metrics['net_profit']:,.2f} ({metrics['total_return_pct']:.2f}%)")
    print()
    print(f"Total Trades: {metrics['total_trades']}")
    print(f"Win Rate: {metrics['win_rate'] * 100:.1f}%")
    print(f"Profit Factor: {metrics['profit_factor']:.2f}")
    print()
    print(f"Max Drawdown: {metrics['max_drawdown_pct'] * 100:.2f}%")
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"Sortino Ratio: {metrics['sortino_ratio']:.2f}")
    print("=" * 50)

    return metrics


if __name__ == "__main__":
    metrics = run_backtest()