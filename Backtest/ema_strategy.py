# MUST NOT EDIT SimBroker
"""
Strategy: AIGeneratedStrategy
Description: EMA strategy: Buy AAPL when the 50 EMA crosses above the 200 EMA, sell when the 50 EMA crosses below the 200 EMA
Generated: 2025-10-17
"""

from sim_broker import SimBroker
from config import BacktestConfig
from canonical_schema import create_signal, OrderSide, OrderAction, OrderType
from data_loader import load_market_data, get_available_indicators
from datetime import datetime
import pandas as pd


class AIGeneratedStrategy:
    """
    EMA crossover strategy.

    Buys AAPL when the 50 EMA crosses above the 200 EMA,
    sells when the 50 EMA crosses below the 200 EMA.
    """

    def __init__(self, broker: SimBroker):
        """
        Initializes the strategy.

        Args:
            broker: The SimBroker instance.
        """
        self.broker = broker
        self.symbol = "AAPL"
        self.positions = {}  # Track our positions

        # Strategy parameters
        self.ema_short = 50
        self.ema_long = 200
        self.position_size = 100

        self.last_ema_short = None
        self.last_ema_long = None

    def on_bar(self, timestamp: datetime, data: dict):
        """
        Called for each bar of market data.

        Args:
            timestamp: The current bar timestamp.
            data: Market data dictionary {symbol: {open, high, low, close, volume, ema_50, ema_200}}.
        """

        if self.symbol not in data:
            print(f"Symbol {self.symbol} not in data for {timestamp}")
            return

        # Check if EMA values are available
        ema_short_value = data[self.symbol].get(f'ema_{self.ema_short}', None)
        ema_long_value = data[self.symbol].get(f'ema_{self.ema_long}', None)

        if ema_short_value is None or ema_long_value is None:
            # EMA values not available for this bar, skip
            return
        
        # Determine position state
        snapshot = self.broker.get_account_snapshot()
        has_position = any(p['symbol'] == self.symbol for p in snapshot['positions'])

        # Generate signals based on EMA crossover
        if self.last_ema_short is not None and self.last_ema_long is not None:
            # Check for buy signal (50 EMA crosses above 200 EMA)
            if self.last_ema_short <= self.last_ema_long and ema_short_value > ema_long_value and not has_position:
                signal = create_signal(
                    timestamp=timestamp,
                    symbol=self.symbol,
                    side=OrderSide.BUY,
                    action=OrderAction.ENTRY,
                    order_type=OrderType.MARKET,
                    size=self.position_size,
                    strategy_id="AIGeneratedStrategy"
                )
                self.broker.submit_signal(signal.to_dict())

            # Check for sell signal (50 EMA crosses below 200 EMA)
            elif self.last_ema_short >= self.last_ema_long and ema_short_value < ema_long_value and has_position:
                signal = create_signal(
                    timestamp=timestamp,
                    symbol=self.symbol,
                    side=OrderSide.SELL,
                    action=OrderAction.EXIT,
                    order_type=OrderType.MARKET,
                    size=self.position_size,
                    strategy_id="AIGeneratedStrategy"
                )
                self.broker.submit_signal(signal.to_dict())

        # Update EMA values for the next bar
        self.last_ema_short = ema_short_value
        self.last_ema_long = ema_long_value


def run_backtest():
    """
    Main backtest runner for the EMA crossover strategy.
    """

    # 1. Configure the backtest
    config = BacktestConfig(
        start_cash=100000,
        fee_flat=1.0,
        fee_pct=0.001,
        slippage_pct=0.0005
    )

    # 2. Initialize the SimBroker
    broker = SimBroker(config)

    # 3. Initialize the strategy
    strategy = AIGeneratedStrategy(broker)

    # 4. Load market data with required indicators
    from data_loader import load_market_data

    df, metadata = load_market_data(
        ticker=strategy.symbol,
        indicators={
            'EMA': {'timeperiod': strategy.ema_short},
            'EMA': {'timeperiod': strategy.ema_long}
        },
        period='6mo',
        interval='1d'
    )

    # Column mapping:
    # - EMA with timeperiod=50 -> EMA_50
    # - EMA with timeperiod=200 -> EMA_200

    # 5. CRITICAL: Verify actual column names (they include parameters)
    print(f"Loaded {len(df)} bars with columns: {list(df.columns)}")
    # Expected output: ['Open', 'High', 'Low', 'Close', 'Volume', 'EMA_50', 'EMA_200']

    # 6. Run the simulation
    for timestamp, row in df.iterrows():
        market_data = {
            strategy.symbol: {
                'open': row['Open'],
                'high': row['High'],
                'low': row['Low'],
                'close': row['Close'],
                'volume': row['Volume'],
                f'ema_{strategy.ema_short}': row.get(f'EMA_{strategy.ema_short}', None),  # Use exact column name
                f'ema_{strategy.ema_long}': row.get(f'EMA_{strategy.ema_long}', None)   # Use exact column name
            }
        }

        # Strategy analyzes and may emit signals
        strategy.on_bar(timestamp, market_data)

        # Broker processes signals and updates state
        broker.step_to(timestamp, market_data)

    # 7. Get results
    metrics = broker.compute_metrics()
    broker.export_trades("results/trades.csv")

    # 8. Print summary
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


if __name__ == "__main__":
    run_backtest()