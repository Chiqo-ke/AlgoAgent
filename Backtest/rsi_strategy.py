# MUST NOT EDIT SimBroker
"""
Strategy: AIGeneratedStrategy
Description: RSI strategy: Buy AAPL when RSI < 30, sell when RSI > 70
Generated: 2024-01-01
"""

from sim_broker import SimBroker
from config import BacktestConfig
from canonical_schema import create_signal, OrderSide, OrderAction, OrderType
from data_loader import load_market_data
from datetime import datetime
import pandas as pd


class AIGeneratedStrategy:
    """
    RSI strategy: Buy AAPL when RSI < 30, sell when RSI > 70
    """

    def __init__(self, broker: SimBroker):
        """
        Initialize the RSI strategy.

        Args:
            broker: The SimBroker instance for executing trades.
        """
        self.broker = broker
        self.positions = {}  # Track our positions
        self.symbol = "AAPL"

        # Strategy parameters
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.trade_size = 100
        self.strategy_id = "RSI_Strategy"

    def on_bar(self, timestamp: datetime, data: dict):
        """
        Called for each bar of market data.

        Args:
            timestamp: Current bar timestamp
            data: Market data dict {symbol: {open, high, low, close, volume, rsi}}
        """
        # Extract RSI value for the symbol
        rsi_value = data.get(self.symbol, {}).get('rsi')

        # Ensure RSI value is available before proceeding
        if rsi_value is None:
            print(f"RSI value is missing for {self.symbol} at {timestamp}. Skipping.")
            return

        # Check if we have a position
        snapshot = self.broker.get_account_snapshot()
        has_position = any(p['symbol'] == self.symbol for p in snapshot['positions'])

        if not has_position and rsi_value < self.rsi_oversold:
            # Enter a long position if RSI is oversold
            signal = create_signal(
                timestamp=timestamp,
                symbol=self.symbol,
                side=OrderSide.BUY,
                action=OrderAction.ENTRY,
                order_type=OrderType.MARKET,
                size=self.trade_size
            )
            self.broker.submit_signal(signal.to_dict())
            print(f"BUY {self.symbol} at {timestamp}, RSI: {rsi_value}")

        elif has_position and rsi_value > self.rsi_overbought:
            # Exit the long position if RSI is overbought
            # Get the position size from the snapshot
            position = next((p for p in snapshot['positions'] if p['symbol'] == self.symbol), None)
            if position:
                signal = create_signal(
                    timestamp=timestamp,
                    symbol=self.symbol,
                    side=OrderSide.SELL,
                    action=OrderAction.EXIT,
                    order_type=OrderType.MARKET,
                    size=position['size']  # Sell existing position size
                )
                self.broker.submit_signal(signal.to_dict())
                print(f"SELL {self.symbol} at {timestamp}, RSI: {rsi_value}")
            else:
                print(f"No position found for {self.symbol} at {timestamp}.")


def run_backtest():
    """Main backtest runner"""

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

    # 4. Load data with indicators (ALWAYS use data_loader)
    df, metadata = load_market_data(
        ticker='AAPL',
        indicators={
            'RSI': {'timeperiod': 14}
        }
    )

    # Rename RSI_14 to RSI for easier access
    if 'RSI_14' in df.columns:
        df = df.rename(columns={'RSI_14': 'RSI'})

    print(f"Loaded {len(df)} bars with columns: {list(df.columns)}")

    # 5. Run simulation
    for timestamp, row in df.iterrows():
        market_data = {
            'AAPL': {
                'open': row['Open'],
                'high': row['High'],
                'low': row['Low'],
                'close': row['Close'],
                'volume': row['Volume'],
                'rsi': row['RSI']
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
    metrics = run_backtest()