# MUST NOT EDIT SimBroker
"""
Strategy: AIGeneratedStrategy
Description: Simple momentum strategy: buy when price is above 20-day moving average and RSI is above 50, sell when price drops below the moving average
Generated: 2024-02-29
"""

from sim_broker import SimBroker
from config import BacktestConfig
from canonical_schema import create_signal, OrderSide, OrderAction, OrderType
from datetime import datetime
import pandas as pd
import numpy as np


class AIGeneratedStrategy:
    """
    Simple momentum strategy: buy when price is above 20-day moving average and RSI is above 50,
    sell when price drops below the moving average.
    """

    def __init__(self, broker: SimBroker):
        """
        Initialize the strategy.

        Args:
            broker: The SimBroker instance.
        """
        self.broker = broker
        self.positions = {}  # Track our positions {symbol: size}
        self.data = {}  # Store historical data for calculations {symbol: DataFrame}
        self.lookback_period = 20  # Lookback period for moving average calculation
        self.rsi_period = 14  # Period for RSI calculation

    def on_bar(self, timestamp: datetime, data: dict):
        """
        Called for each bar of market data.

        Args:
            timestamp: Current bar timestamp.
            data: Market data dict {symbol: {open, high, low, close, volume}}
        """
        for symbol, bars in data.items():
            self._process_symbol(timestamp, symbol, bars)

    def _process_symbol(self, timestamp: datetime, symbol: str, bars: dict):
        """
        Processes the market data for a single symbol.

        Args:
            timestamp: Current bar timestamp.
            symbol: The symbol being processed.
            bars: Market data for the symbol (open, high, low, close, volume).
        """
        # Update historical data
        if symbol not in self.data:
            self.data[symbol] = pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']).set_index('timestamp')

        new_row = pd.DataFrame([{'timestamp': timestamp, 'open': bars['open'], 'high': bars['high'], 'low': bars['low'], 'close': bars['close'], 'volume': bars['volume']}]).set_index('timestamp')
        self.data[symbol] = pd.concat([self.data[symbol], new_row])

        # Ensure sufficient data for calculations
        if len(self.data[symbol]) < self.lookback_period:
            return

        # Calculate moving average and RSI
        df = self.data[symbol].copy()  # Operate on a copy
        df['SMA'] = df['close'].rolling(window=self.lookback_period).mean()
        df['RSI'] = self._calculate_rsi(df['close'], self.rsi_period)

        # Get the latest values
        current_price = bars['close']
        current_sma = df['SMA'].iloc[-1]
        current_rsi = df['RSI'].iloc[-1]

        # Check if we have a position
        snapshot = self.broker.get_account_snapshot()
        has_position = any(p['symbol'] == symbol for p in snapshot['positions'])
        position_size = next((p['size'] for p in snapshot['positions'] if p['symbol'] == symbol), 0)

        # Generate signals
        if not has_position and current_price > current_sma and current_rsi > 50:
            # Enter a long position
            signal = create_signal(
                timestamp=timestamp,
                symbol=symbol,
                side=OrderSide.BUY,
                action=OrderAction.ENTRY,
                order_type=OrderType.MARKET,
                size=100  # Fixed size for simplicity
            )
            self.broker.submit_signal(signal.to_dict())
            self.positions[symbol] = 100  # Update internal position tracking

        elif has_position and current_price < current_sma:
            # Exit the long position
            signal = create_signal(
                timestamp=timestamp,
                symbol=symbol,
                side=OrderSide.SELL,
                action=OrderAction.EXIT,
                order_type=OrderType.MARKET,
                size=position_size
            )
            self.broker.submit_signal(signal.to_dict())
            self.positions.pop(symbol, None)  # Remove position from tracking

    def _calculate_rsi(self, data: pd.Series, period: int) -> pd.Series:
        """
        Calculates the Relative Strength Index (RSI).

        Args:
            data: The price data series.
            period: The period for RSI calculation.

        Returns:
            The RSI values as a Pandas Series.
        """
        delta = data.diff()
        up, down = delta.copy(), delta.copy()
        up[up < 0] = 0
        down[down > 0] = 0
        roll_up1 = up.rolling(window=period).mean()
        roll_down1 = down.abs().rolling(window=period).mean()
        RS = roll_up1 / roll_down1
        RSI = 100.0 - (100.0 / (1.0 + RS))
        return RSI


def run_backtest():
    """
    Main backtest runner.
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
    except FileNotFoundError:
        print("Error: data.csv not found.  Create a file named 'data.csv' with columns: 'timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume'")
        return None

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
    print(f"Win Rate: {metrics['win_rate'] * 100:.1f}%")
    print(f"Profit Factor: {metrics['profit_factor']:.2f}")
    print()
    print(f"Max Drawdown: {metrics['max_drawdown_pct'] * 100:.2f}%")
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