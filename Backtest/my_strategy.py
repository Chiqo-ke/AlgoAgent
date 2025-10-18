# MUST NOT EDIT SimBroker
"""
Strategy: AIGeneratedStrategy
Description: Buy when RSI < 30, sell when RSI > 70
Generated: 2024-01-01
"""

from sim_broker import SimBroker
from config import BacktestConfig
from canonical_schema import create_signal, OrderSide, OrderAction, OrderType
from datetime import datetime
import pandas as pd
import talib


class AIGeneratedStrategy:
    """
    A simple RSI-based trading strategy.

    The strategy buys when the RSI falls below 30 and sells when it rises above 70.
    """

    def __init__(self, broker: SimBroker):
        """
        Initializes the strategy with the broker instance.

        Args:
            broker: The SimBroker instance to use for trading.
        """
        self.broker = broker
        self.positions = {}  # Track our positions (symbol: size)
        self.rsi_period = 14  # RSI calculation period

    def on_bar(self, timestamp: datetime, data: dict):
        """
        Called for each bar of market data.

        Args:
            timestamp: The timestamp of the current bar.
            data: A dictionary containing market data for each symbol.
                 Example: {"AAPL": {"open": 150.0, "high": 151.0, "low": 149.0, "close": 150.5, "volume": 1000000}}
        """
        for symbol, bars in data.items():
            self._process_symbol(timestamp, symbol, bars)

    def _process_symbol(self, timestamp: datetime, symbol: str, bars: dict):
        """
        Processes the market data for a specific symbol.

        Args:
            timestamp: The timestamp of the current bar.
            symbol: The symbol of the asset.
            bars: A dictionary containing the open, high, low, close, and volume for the asset.
        """
        close_prices = [bars['close']] # Use only the current close price
        if len(close_prices) < self.rsi_period:
          return # Not enough data to calculate RSI

        rsi = talib.RSI(pd.Series(close_prices), timeperiod=self.rsi_period)[-1]

        snapshot = self.broker.get_account_snapshot()
        has_position = any(p['symbol'] == symbol for p in snapshot['positions'])

        if not has_position and rsi < 30:
            # Oversold: Buy signal
            signal = create_signal(
                timestamp=timestamp,
                symbol=symbol,
                side=OrderSide.BUY,
                action=OrderAction.ENTRY,
                order_type=OrderType.MARKET,
                size=100  # Fixed size for simplicity
            )
            self.broker.submit_signal(signal.to_dict())

        elif has_position and rsi > 70:
            # Overbought: Sell signal
            for position in snapshot['positions']:
                if position['symbol'] == symbol:
                    size = position['size']
                    signal = create_signal(
                        timestamp=timestamp,
                        symbol=symbol,
                        side=OrderSide.SELL,
                        action=OrderAction.EXIT,
                        order_type=OrderType.MARKET,
                        size=size
                    )
                    self.broker.submit_signal(signal.to_dict())
                    break  # Exit only the relevant position


def run_backtest():
    """
    Runs the backtest simulation.
    """

    # 1. Configure
    config = BacktestConfig(
        start_cash=100000,
        fee_flat=1.0,
        fee_pct=0.001,
        slippage_pct=0.0005
    )

    # 2. Initialize broker
    broker = SimBroker(config)

    # 3. Initialize strategy
    strategy = AIGeneratedStrategy(broker)

    # 4. Load data
    try:
        data = pd.read_csv("data.csv")
        # Expected columns: timestamp, symbol, open, high, low, close, volume
    except FileNotFoundError:
        print("Error: data.csv not found.  Please ensure it exists.")
        return

    # 5. Run simulation
    for index, row in data.iterrows():
        timestamp = pd.to_datetime(row['timestamp'])

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

    # 6. Get results
    metrics = broker.compute_metrics()
    broker.export_trades("results/trades.csv")

    # 7. Print summary
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
    print(f"Win Rate: {metrics['win_rate']*100:.1f}%")
    print(f"Profit Factor: {metrics['profit_factor']:.2f}")
    print()
    print(f"Max Drawdown: {metrics['max_drawdown_pct']*100:.2f}%")
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"Sortino Ratio: {metrics['sortino_ratio']:.2f}")
    print("=" * 50)

    return metrics

def test_strategy():
    """Minimal test to verify API usage"""
    config = BacktestConfig(start_cash=10000)
    broker = SimBroker(config)

    # Test signal submission
    signal = create_signal(
        timestamp=datetime(2025, 1, 1),
        symbol="TEST",
        side=OrderSide.BUY,
        action=OrderAction.ENTRY,
        order_type=OrderType.MARKET,
        size=10
    )

    order_id = broker.submit_signal(signal.to_dict())
    assert order_id != "", "Signal should be accepted"

    # Test step
    market_data = {"TEST": {"open": 100, "high": 101, "low": 99, "close": 100, "volume": 1000}}
    broker.step_to(datetime(2025, 1, 1), market_data)

    # Test snapshot
    snapshot = broker.get_account_snapshot()
    assert 'equity' in snapshot
    assert 'cash' in snapshot

    # Test metrics
    metrics = broker.compute_metrics()
    assert 'total_trades' in metrics

    print("✓ All tests passed")


if __name__ == "__main__":
    test_strategy()
    run_backtest()