"""
Strategy: Simple RSI Strategy
Description: A basic RSI-based mean reversion strategy
Generated: 2023-10-17
Location: codes/ directory
"""

import sys
from pathlib import Path

# Add parent directory to path (codes -> Backtest -> monolithic_agent)
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Use ONLY these imports (NEVER use 'from sim_broker import'):
from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig
from Backtest.canonical_schema import create_signal, OrderSide, OrderAction, OrderType
from Backtest.data_loader import load_market_data
from Backtest.pattern_logger import PatternLogger
from Backtest.signal_logger import SignalLogger
from datetime import datetime
import pandas as pd


class SimpleRSIStrategy:
    """A simple RSI-based mean reversion strategy"""
    
    def __init__(self, broker: SimBroker, strategy_id: str = "simple_rsi_strategy", rsi_period: int = 14):
        self.broker = broker
        self.strategy_id = strategy_id
        self.rsi_period = rsi_period
        
        # Initialize loggers
        self.pattern_logger = PatternLogger(strategy_id)
        self.signal_logger = SignalLogger(strategy_id)
        
        # Initialize position tracking
        self.in_position = False
        self.position_size = 0
        self.entry_price = None

    def on_bar(self, timestamp: datetime, market_data: dict):
        """
        Process each bar of market data sequentially.
        """
        for symbol, data in market_data.items():
            # Extract market data
            close_price = data.get('close')
            rsi = data.get(f'rsi_{self.rsi_period}')

            if close_price is None or rsi is None:
                print(f"[WARNING] Missing data for {symbol} at {timestamp}")
                continue

            # Check for entry and exit patterns
            if not self.in_position:
                self._check_entry_pattern(timestamp, symbol, close_price, rsi)
            else:
                self._check_exit_pattern(timestamp, symbol, close_price, rsi)

    def _check_entry_pattern(self, timestamp, symbol, close_price, rsi):
        """Check and log entry pattern"""
        pattern_condition = f"RSI({self.rsi_period}) < 30"
        pattern_found = rsi < 30

        # Log pattern check
        self.pattern_logger.log_pattern(
            timestamp=timestamp,
            symbol=symbol,
            step_id="entry_check",
            step_title="Entry Pattern Check",
            pattern_condition=pattern_condition,
            pattern_found=pattern_found,
            market_data={'close': close_price},
            indicator_values={'rsi': rsi}
        )

        if pattern_found:
            self._generate_entry_signal(timestamp, symbol, close_price, rsi)

    def _check_exit_pattern(self, timestamp, symbol, close_price, rsi):
        """Check and log exit pattern"""
        pattern_condition = f"RSI({self.rsi_period}) > 70"
        pattern_found = rsi > 70

        # Log pattern check
        self.pattern_logger.log_pattern(
            timestamp=timestamp,
            symbol=symbol,
            step_id="exit_check",
            step_title="Exit Pattern Check",
            pattern_condition=pattern_condition,
            pattern_found=pattern_found,
            market_data={'close': close_price},
            indicator_values={'rsi': rsi}
        )

        if pattern_found:
            self._generate_exit_signal(timestamp, symbol, close_price, rsi)

    def _generate_entry_signal(self, timestamp, symbol, close_price, rsi):
        """Generate and log entry signal"""
        size = 1  # Fixed position size for simplicity
        stop_loss = close_price - 0.0015  # 15 pips
        take_profit = close_price + 0.0040  # 40 pips

        # Log the signal
        self.signal_logger.log_signal(
            timestamp=timestamp,
            symbol=symbol,
            side="BUY",
            action="ENTRY",
            order_type="MARKET",
            size=size,
            price=close_price,
            reason="RSI below 30 (oversold)",
            market_data={'close': close_price},
            indicator_values={'rsi': rsi},
            strategy_state={'in_position': self.in_position}
        )

        # Submit to broker
        signal = create_signal(
            timestamp=timestamp,
            symbol=symbol,
            side=OrderSide.BUY,
            action=OrderAction.ENTRY,
            order_type=OrderType.MARKET,
            size=size,
            stop_loss=stop_loss,
            take_profit=take_profit,
            strategy_id=self.strategy_id
        )
        self.broker.submit_signal(signal.to_dict())

        # Update position state
        self.in_position = True
        self.position_size = size
        self.entry_price = close_price

    def _generate_exit_signal(self, timestamp, symbol, close_price, rsi):
        """Generate and log exit signal"""
        size = self.position_size

        # Log the signal
        self.signal_logger.log_signal(
            timestamp=timestamp,
            symbol=symbol,
            side="SELL",
            action="EXIT",
            order_type="MARKET",
            size=size,
            price=close_price,
            reason="RSI above 70 (overbought)",
            market_data={'close': close_price},
            indicator_values={'rsi': rsi},
            strategy_state={'entry_price': self.entry_price}
        )

        # Submit to broker
        signal = create_signal(
            timestamp=timestamp,
            symbol=symbol,
            side=OrderSide.SELL,
            action=OrderAction.EXIT,
            order_type=OrderType.MARKET,
            size=size,
            strategy_id=self.strategy_id
        )
        self.broker.submit_signal(signal.to_dict())

        # Update position state
        self.in_position = False
        self.position_size = 0
        self.entry_price = None

    def finalize(self):
        """Close loggers and export summaries"""
        self.pattern_logger.close()
        self.signal_logger.close()


def run_backtest():
    """Runs the backtest for the Simple RSI Strategy in STREAMING mode"""
    
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
    strategy = SimpleRSIStrategy(broker, strategy_id="simple_rsi_strategy")
    print(f"[OK] Strategy initialized: {strategy.__class__.__name__}")
    
    # 4. Define indicators
    indicators = {
        'RSI': {'timeperiod': 14}
    }
    
    # 5. Load data in STREAMING mode
    print(f"[INFO] Loading data in streaming mode...")
    data_stream = load_market_data(
        ticker="*",
        indicators=indicators,
        period='6mo',
        interval='1d',
        stream=True
    )
    
    print(f"[OK] Data stream initialized")
    
    # 6. Process data
    for timestamp, market_data, progress_pct in data_stream:
        strategy.on_bar(timestamp, market_data)
        broker.step_to(timestamp, market_data)
    
    # 7. Finalize strategy
    strategy.finalize()
    
    # 8. Get metrics
    metrics = broker.compute_metrics()
    print(f"[OK] Backtest completed")
    
    # 9. Export trades
    trades_dir = Path(__file__).parent / "trades"
    trades_dir.mkdir(exist_ok=True)
    broker.export_trades(str(trades_dir / "trades.csv"))
    
    # 10. Display results
    print(f"Net Profit: ${metrics['net_profit']:,.2f}")
    print(f"Total Trades: {metrics['total_trades']}")
    print(f"Win Rate: {metrics['win_rate']:.2%}")
    print(f"Max Drawdown: {metrics['max_drawdown_pct']:.2%}")
    
    return metrics


if __name__ == "__main__":
    run_backtest()