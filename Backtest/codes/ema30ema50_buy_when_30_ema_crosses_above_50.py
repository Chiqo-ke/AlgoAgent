"""
Strategy: Ema_30/ema_50BuyWhen
Description: EMA_30/EMA_50 Buy when 30 EMA crosses above 50 EMA.
Buy when 30 EMA crosses above 50 EMA, set stop loss 5 pips below entry price and take profit 15 pips above entry price.
Generated: 2024-01-01
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


class Ema_30Ema_50BuyWhen:
    """
    Strategy: EMA_30/EMA_50 Buy when 30 EMA crosses above 50 EMA.
    Buy when 30 EMA crosses above 50 EMA, set stop loss 5 pips below entry price and take profit 15 pips above entry price.
    """

    def __init__(self, broker: SimBroker, symbol: str = "AAPL", **params):
        """
        Initializes the strategy.

        Args:
            broker (SimBroker): The broker instance.
            symbol (str, optional): The symbol to trade. Defaults to "AAPL".
            **params: Additional parameters.
        """
        self.broker = broker
        self.symbol = symbol
        self.in_position = False
        self.ema_short_period = params.get("ema_short_period", 30)  # Default short EMA period
        self.ema_long_period = params.get("ema_long_period", 50)  # Default long EMA period
        self.stop_loss_pips = params.get("stop_loss_pips", 0.05) # Stop loss in percentage
        self.take_profit_pips = params.get("take_profit_pips", 0.15) # Take profit in percentage
        self.entry_price = None

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

        ema_short = symbol_data.get(f'EMA_{self.ema_short_period}', None)
        ema_long = symbol_data.get(f'EMA_{self.ema_long_period}', None)
        close_price = symbol_data.get('close', None)

        if ema_short is None or ema_long is None or close_price is None:
            print(f"Missing EMA or close price for {self.symbol} at {timestamp}")
            return

        if not self.in_position and ema_short > ema_long:
            # Generate buy signal
            signal = create_signal(
                timestamp=timestamp,
                symbol=self.symbol,
                side=OrderSide.BUY,
                action=OrderAction.ENTRY,
                order_type=OrderType.MARKET,
                size=100  # Fixed size for this example
            )
            self.broker.submit_signal(signal.to_dict())
            self.in_position = True
            self.entry_price = close_price
            print(f"✓ BUY signal at {timestamp}, price: {close_price}")

        elif self.in_position:
            # Check for stop loss or take profit
            if self.entry_price:
                stop_loss_price = self.entry_price * (1 - self.stop_loss_pips)
                take_profit_price = self.entry_price * (1 + self.take_profit_pips)

                if close_price <= stop_loss_price or close_price >= take_profit_price:
                    # Generate sell signal
                    signal = create_signal(
                        timestamp=timestamp,
                        symbol=self.symbol,
                        side=OrderSide.SELL,
                        action=OrderAction.EXIT,
                        order_type=OrderType.MARKET,
                        size=100  # Fixed size for this example
                    )
                    self.broker.submit_signal(signal.to_dict())
                    self.in_position = False
                    print(f"✓ SELL signal at {timestamp}, price: {close_price}, SL: {close_price <= stop_loss_price}, TP: {close_price >= take_profit_price}")
            else:
                print("Entry price not set")


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
    strategy = Ema_30Ema_50BuyWhen(broker)
    print(f"✓ Strategy initialized: {strategy.__class__.__name__}")

    # 4. Load market data with indicators
    indicators = {
        'EMA': {'timeperiod': strategy.ema_short_period},
        'EMA': {'timeperiod': strategy.ema_long_period}
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
                f'EMA_{strategy.ema_short_period}': row.get(f'EMA_{strategy.ema_short_period}', None),
                f'EMA_{strategy.ema_long_period}': row.get(f'EMA_{strategy.ema_long_period}', None),
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