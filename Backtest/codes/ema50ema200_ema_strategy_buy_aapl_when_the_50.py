"""
Strategy: Ema_50_200EmaStrategy
Description: EMA strategy: Buy AAPL when the 50 EMA crosses above the 200 EMA.
Generated: 2024-10-27
Location: codes/ directory
"""

# Add parent directory to path for imports
import sys
from pathlib import Path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import from Backtest package (NOT as standalone modules)
from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig
from Backtest.canonical_schema import create_signal, OrderSide, OrderAction, OrderType
from Backtest.data_loader import load_market_data
from datetime import datetime
import pandas as pd


class Ema_50_200EmaStrategy:
    """
    EMA strategy: Buy AAPL when the 50 EMA crosses above the 200 EMA.
    """

    def __init__(self, broker: SimBroker, symbol: str = "AAPL"):
        """
        Initializes the strategy with a broker and a symbol.

        Args:
            broker (SimBroker): The broker instance to use for trading.
            symbol (str): The symbol to trade.
        """
        self.broker = broker
        self.symbol = symbol
        self.in_position = False
        self.ema_50 = None
        self.ema_200 = None

    def on_bar(self, timestamp: datetime, data: dict):
        """
        Processes each bar of market data.

        Args:
            timestamp (datetime): The timestamp of the bar.
            data (dict): The market data for the bar.
        """
        symbol_data = data.get(self.symbol)
        if not symbol_data:
            print(f"No data for {self.symbol} at {timestamp}")
            return

        close = symbol_data.get('close')
        ema_50 = symbol_data.get('EMA_50')
        ema_200 = symbol_data.get('EMA_200')

        if ema_50 is None or ema_200 is None:
            # EMA values not available yet, skip
            return

        if not self.in_position and ema_50 > ema_200:
            # 50 EMA crosses above 200 EMA, enter long position
            print(f"{timestamp}: 50 EMA crossed above 200 EMA. Buying {self.symbol}")

            signal = create_signal(
                timestamp=timestamp,
                symbol=self.symbol,
                side=OrderSide.BUY,
                action=OrderAction.ENTRY,
                order_type=OrderType.MARKET,
                size=100  # Example size, adjust as needed
            )
            self.broker.submit_signal(signal.to_dict())
            self.in_position = True

        elif self.in_position and ema_50 < ema_200:
            # 50 EMA crosses below 200 EMA, exit long position
            print(f"{timestamp}: 50 EMA crossed below 200 EMA. Selling {self.symbol}")

            signal = create_signal(
                timestamp=timestamp,
                symbol=self.symbol,
                side=OrderSide.SELL,
                action=OrderAction.EXIT,
                order_type=OrderType.MARKET,
                size=100  # Match the entry size
            )
            self.broker.submit_signal(signal.to_dict())
            self.in_position = False


def run_backtest():
    """Runs the backtest"""

    # 1. Configure backtest
    config = BacktestConfig(
        start_cash=100000,
        fee_flat=1.0,
        fee_pct=0.001,
        slippage_pct=0.0005
    )

    # 2. Initialize broker
    broker = SimBroker(config)

    # 3. Initialize strategy
    strategy = Ema_50_200EmaStrategy(broker)
    print(f"✓ Strategy initialized: {strategy.__class__.__name__}")

    # 4. Load market data with indicators
    indicators = {
        'EMA': {'timeperiod': 50},
        'EMA': {'timeperiod': 200},
    }

    df, metadata = load_market_data(
        ticker=strategy.symbol,
        indicators=indicators,
        period='6mo',
        interval='1d'
    )

    # 5. Verify data
    print(f"✓ Loaded {len(df)} bars")
    print(f"✓ Columns: {list(df.columns)}")

    # 6. Run simulation
    for timestamp, row in df.iterrows():
        market_data = {
            strategy.symbol: {
                'open': row['Open'],
                'high': row['High'],
                'low': row['Low'],
                'close': row['Close'],
                'volume': row['Volume'],
                'EMA_50': row.get('EMA_50', None),
                'EMA_200': row.get('EMA_200', None),
            }
        }

        strategy.on_bar(timestamp, market_data)
        broker.step_to(timestamp, market_data)

    # 7. Get metrics
    metrics = broker.compute_metrics()

    # 8. Export results
    results_dir = Path(__file__).parent / "results"
    trades_dir = Path(__file__).parent / "trades"
    results_dir.mkdir(exist_ok=True)
    trades_dir.mkdir(exist_ok=True)

    broker.export_trades(str(trades_dir / "trades.csv"))

    # 9. Print results
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