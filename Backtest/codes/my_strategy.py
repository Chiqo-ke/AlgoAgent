# MUST NOT EDIT SimBroker
"""
Strategy: AIGeneratedStrategy
Description: Buy when RSI < 30
Generated: 2025-10-17
Location: codes/ directory
"""

# Add parent directory to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sim_broker import SimBroker
from config import BacktestConfig
from canonical_schema import create_signal, OrderSide, OrderAction, OrderType
from data_loader import load_market_data
from datetime import datetime
import pandas as pd


class AIGeneratedStrategy:
    """
    A simple strategy that buys when the RSI is below 30 and sells when RSI is above 70.
    """

    def __init__(self, broker: SimBroker, symbol: str = "AAPL", rsi_period: int = 14):
        """
        Initializes the strategy.

        Args:
            broker: The SimBroker instance for executing trades.
            symbol: The trading symbol. Defaults to "AAPL".
            rsi_period: The time period for calculating RSI. Defaults to 14.
        """
        self.broker = broker
        self.symbol = symbol
        self.rsi_period = rsi_period
        self.position = None  # Track if we have a position
        self.rsi_column = f"RSI_{self.rsi_period}" # Column name for RSI

    def on_bar(self, timestamp: datetime, data: dict):
        """
        Executes the strategy logic for each bar of market data.

        Args:
            timestamp: The timestamp of the current bar.
            data: A dictionary containing market data for the symbol.
        """
        symbol_data = data.get(self.symbol)
        if not symbol_data:
            return  # No data for this symbol, skip

        rsi_value = symbol_data.get(self.rsi_column) # Use correct column name
        if rsi_value is None or pd.isna(rsi_value):
            return  # RSI not available, skip

        snapshot = self.broker.get_account_snapshot()
        has_position = any(p['symbol'] == self.symbol for p in snapshot['positions'])

        if not has_position and rsi_value < 30:
            # Buy when RSI is below 30
            signal = create_signal(
                timestamp=timestamp,
                symbol=self.symbol,
                side=OrderSide.BUY,
                action=OrderAction.ENTRY,
                order_type=OrderType.MARKET,
                size=100
            )
            self.broker.submit_signal(signal.to_dict())
            self.position = "long"

        elif has_position and rsi_value > 70:
            # Sell when RSI is above 70
            signal = create_signal(
                timestamp=timestamp,
                symbol=self.symbol,
                side=OrderSide.SELL,
                action=OrderAction.EXIT,
                order_type=OrderType.MARKET,
                size=100
            )
            self.broker.submit_signal(signal.to_dict())
            self.position = None
        
        elif has_position and self.position == "long" and rsi_value >= 60:
            #Exit once it goes above 60 RSI for profit maximization
            signal = create_signal(
                timestamp=timestamp,
                symbol=self.symbol,
                side=OrderSide.SELL,
                action=OrderAction.EXIT,
                order_type=OrderType.MARKET,
                size=100
            )
            self.broker.submit_signal(signal.to_dict())
            self.position = None


def run_backtest():
    """
    Runs a backtest of the AIGeneratedStrategy.
    """

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
    strategy = AIGeneratedStrategy(broker, symbol="AAPL", rsi_period=14)

    # 4. Load data with RSI indicator
    df, metadata = load_market_data(
        ticker='AAPL',
        indicators={'RSI': {'timeperiod': strategy.rsi_period}},
        period='1mo',
        interval='1d'
    )

    # Column mapping:
    # - RSI with timeperiod=14 -> RSI_14

    # 5. Print loaded columns (CRITICAL - use these exact names!)
    print(f"Loaded {len(df)} bars with columns: {list(df.columns)}")
    # Expected output: ['Open', 'High', 'Low', 'Close', 'Volume', 'RSI_14']
    rsi_column = strategy.rsi_column
    # 6. Run simulation
    for timestamp, row in df.iterrows():
        market_data = {
            'AAPL': {
                'open': row['Open'],
                'high': row['High'],
                'low': row['Low'],
                'close': row['Close'],
                'volume': row['Volume'],
                f"{strategy.rsi_column}": row[f"{strategy.rsi_column}"] #Dynamically pull the RSI based on RSI period
                # Use exact column name!
            }
        }

        strategy.on_bar(timestamp, market_data)
        broker.step_to(timestamp, market_data)

    # 7. Get results
    metrics = broker.compute_metrics()

    # Export results to codes directory
    results_dir = Path(__file__).parent / "results"
    trades_dir = Path(__file__).parent / "trades"
    results_dir.mkdir(exist_ok=True)
    trades_dir.mkdir(exist_ok=True)

    broker.export_trades(str(trades_dir / "trades.csv"))

    with open(results_dir / "metrics.json", 'w') as f:
        import json
        json.dump(metrics, f, indent=2, default=str)
    # 8. Print metrics
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