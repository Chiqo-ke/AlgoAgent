# MUST NOT EDIT SimBroker
"""
Strategy: TestRSIStrategy
Description: Buy when RSI < 30, sell when RSI > 70
Generated: 2024-02-29
"""

from sim_broker import SimBroker
from config import BacktestConfig
from canonical_schema import create_signal, OrderSide, OrderAction, OrderType
from datetime import datetime
import pandas as pd
import numpy as np


class TestRSIStrategy:
    """
    A simple RSI-based trading strategy.  Buys when the RSI falls below a
    threshold and sells when it rises above a threshold.
    """

    def __init__(self, broker: SimBroker, rsi_oversold=30, rsi_overbought=70, size=100):
        """
        Initializes the strategy with a SimBroker instance and RSI thresholds.

        Args:
            broker: The SimBroker instance for order execution and account management.
            rsi_oversold: The RSI level below which to enter a long position.
            rsi_overbought: The RSI level above which to exit a long position.
            size: The quantity of shares to trade per order.
        """
        self.broker = broker
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.size = size
        self.positions = {}  # Track our positions - symbol: quantity

    def on_bar(self, timestamp: datetime, data: dict):
        """
        Analyzes the market data at each bar and generates trading signals.

        Args:
            timestamp: The timestamp of the current bar.
            data: A dictionary containing the market data for all symbols.  Expects
                  a dictionary where keys are symbols and values are dictionaries
                  containing 'open', 'high', 'low', 'close', and 'volume'.
        """

        for symbol, bars in data.items():
            self._process_symbol(timestamp, symbol, bars)

    def _process_symbol(self, timestamp: datetime, symbol: str, bars: dict):
        """
        Processes a single symbol, calculates RSI, and generates signals if necessary.

        Args:
            timestamp: The timestamp of the current bar.
            symbol: The symbol being processed.
            bars: A dictionary containing the 'open', 'high', 'low', 'close', and 'volume'
                  data for the symbol.
        """
        try:
            close_prices = [bars['close']]
            rsi = self._calculate_rsi(close_prices)

            snapshot = self.broker.get_account_snapshot()
            position = next((p for p in snapshot['positions'] if p['symbol'] == symbol), None)
            has_position = position is not None

            if not has_position and rsi < self.rsi_oversold:
                # Enter a long position when RSI is oversold
                signal = create_signal(
                    timestamp=timestamp,
                    symbol=symbol,
                    side=OrderSide.BUY,
                    action=OrderAction.ENTRY,
                    order_type=OrderType.MARKET,
                    size=self.size
                )
                self.broker.submit_signal(signal.to_dict())

            elif has_position and rsi > self.rsi_overbought:
                # Exit the long position when RSI is overbought
                signal = create_signal(
                    timestamp=timestamp,
                    symbol=symbol,
                    side=OrderSide.SELL,
                    action=OrderAction.EXIT,
                    order_type=OrderType.MARKET,
                    size=position['size']  # Sell the existing position
                )
                self.broker.submit_signal(signal.to_dict())
        except Exception as e:
            print(f"Error processing {symbol}: {e}")

    def _calculate_rsi(self, close_prices, period=14):
        """
        Calculates the Relative Strength Index (RSI).  Only works if prices are
        passed in one-at-a-time.

        Args:
            close_prices: A list of closing prices for the asset.
            period: The period for calculating RSI (default is 14).

        Returns:
            The RSI value for the latest closing price.
        """

        if len(close_prices) < 2:
            return 50  # Return neutral RSI if not enough data

        changes = [close_prices[i] - close_prices[i-1] for i in range(1, len(close_prices))]
        gains = [change for change in changes if change > 0]
        losses = [-change for change in changes if change < 0]

        avg_gain = sum(gains) / period if gains else 0
        avg_loss = sum(losses) / period if losses else 0

        if avg_loss == 0:
            return 100 if avg_gain > 0 else 0  # Avoid division by zero
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi


def run_backtest():
    """
    Sets up and executes the backtest using the SimBroker and TestRSIStrategy.
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
    strategy = TestRSIStrategy(broker)

    # 4. Load data
    try:
        data = pd.read_csv("data.csv")
    except FileNotFoundError:
        print("Error: data.csv not found.  Please place it in the same directory.")
        return

    # 5. Run simulation
    for index, row in data.iterrows():
        try:
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
        except Exception as e:
            print(f"Error during backtest on row {index}: {e}")
            return

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
    metrics = run_backtest()