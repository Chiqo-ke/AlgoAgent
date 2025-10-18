# MUST NOT EDIT SimBroker
"""
Strategy: AIGeneratedStrategy
Description: Simple test strategy: Buy AAPL when price crosses above 50 SMA
Generated: 2025-10-17
Location: codes/ directory
"""

# Add parent directory to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Now we can import from parent Backtest directory
from sim_broker import SimBroker
from config import BacktestConfig
from canonical_schema import create_signal, OrderSide, OrderAction, OrderType
from data_loader import load_market_data
from datetime import datetime
import pandas as pd


class AIGeneratedStrategy:
    """
    A simple trading strategy that buys AAPL when the price crosses above its 50-day SMA.
    """

    def __init__(self, broker: SimBroker, symbol: str = "AAPL", sma_period: int = 50):
        """
        Initializes the strategy with a SimBroker instance.

        Args:
            broker: The SimBroker instance to use for trading.
            symbol: The symbol to trade (default: "AAPL").
            sma_period: The period for the Simple Moving Average (default: 50).
        """
        self.broker = broker
        self.symbol = symbol
        self.sma_period = sma_period
        self.position = False  # Track if we have a position
        self.last_price = None

    def on_bar(self, timestamp: datetime, data: dict):
        """
        Called for each bar of market data. Executes the strategy logic.

        Args:
            timestamp: The timestamp of the current bar.
            data: A dictionary containing market data for the symbol.
        """
        # Ensure data is available for the specified symbol
        if self.symbol not in data:
            print(f"Warning: No data for {self.symbol} at {timestamp}")
            return

        # Get current price
        current_price = data[self.symbol]['close']
        self.last_price = current_price
        sma_column_name = f"SMA_{self.sma_period}" # construct column name based on sma_period
        
        # Check if SMA is available
        if sma_column_name not in data[self.symbol]:
          print(f"SMA_{self.sma_period} not available in market data.")
          return

        # Get SMA value
        sma = data[self.symbol][sma_column_name]

        # Check if SMA value is None or NaN before proceeding
        if sma is None or pd.isna(sma):
          print(f"SMA is None or NaN at {timestamp}. Skipping bar.")
          return

        # Strategy logic: Buy if price crosses above SMA
        if current_price > sma and not self.position:
            signal = create_signal(
                timestamp=timestamp,
                symbol=self.symbol,
                side=OrderSide.BUY,
                action=OrderAction.ENTRY,
                order_type=OrderType.MARKET,
                size=100  # Fixed size for simplicity
            )
            order_id = self.broker.submit_signal(signal.to_dict())
            print(f"Buy signal emitted at {timestamp}, order id: {order_id}")
            self.position = True

        # Strategy logic: Sell if price crosses below SMA
        elif current_price < sma and self.position:
            signal = create_signal(
                timestamp=timestamp,
                symbol=self.symbol,
                side=OrderSide.SELL,
                action=OrderAction.EXIT,
                order_type=OrderType.MARKET,
                size=100  # Fixed size for simplicity
            )
            order_id = self.broker.submit_signal(signal.to_dict())
            print(f"Sell signal emitted at {timestamp}, order id: {order_id}")
            self.position = False


def run_backtest():
    """
    Runs the backtest for the AIGeneratedStrategy.
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

    # 4. Load market data with indicators (SMA_50)
    try:
        df, metadata = load_market_data(
            ticker="AAPL",
            indicators={"SMA": {"timeperiod": 50}},
            period="3mo",
            interval="1d"
        )

        # Column mapping:
        # - Close -> Close
        # - SMA with timeperiod=50 -> SMA_50
        print(f"Loaded columns: {list(df.columns)}")

    except Exception as e:
        print(f"Error loading market data: {e}")
        return

    # 5. Run the simulation
    try:
        for timestamp, row in df.iterrows():
            # Create market data dictionary in the required format
            market_data = {
                "AAPL": {
                    "open": row["Open"],
                    "high": row["High"],
                    "low": row["Low"],
                    "close": row["Close"],
                    "volume": row["Volume"],
                    "SMA_50": row["SMA_50"] if "SMA_50" in row else None, #SMA must be passed if loaded
                    # Add any additional market data you need here, e.g., SMA, RSI, etc.
                }
            }

            strategy.on_bar(timestamp, market_data) # Pass data to strategy.on_bar to evaluate conditions
            broker.step_to(timestamp, market_data) # Move simulation forward to next timestamp to process orders

    except Exception as e:
        print(f"Error during simulation: {e}")
        return

    # 6. Get the results
    metrics = broker.compute_metrics()

    # Export results to codes directory
    results_dir = Path(__file__).parent / "results"
    trades_dir = Path(__file__).parent / "trades"
    results_dir.mkdir(exist_ok=True)
    trades_dir.mkdir(exist_ok=True)

    broker.export_trades(str(trades_dir / "trades.csv"))
    # Optionally export metrics
    with open(results_dir / "metrics.json", 'w') as f:
        import json
        json.dump(metrics, f, indent=2, default=str)


    # 7. Print the results
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


if __name__ == "__main__":
    metrics = run_backtest()