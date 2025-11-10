"""
Test Strategy: Simple SMA Crossover (Streaming Mode Test)
Description: Test sequential data ingestion with streaming mode
Generated: 2025-11-03
Location: codes/ directory
"""

# Add parent directory to path for imports
import sys
from pathlib import Path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import from Backtest package
from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig
from Backtest.canonical_schema import create_signal, OrderSide, OrderAction, OrderType
from Backtest.data_loader import load_market_data
from Backtest.pattern_logger import PatternLogger
from Backtest.signal_logger import SignalLogger
from datetime import datetime
import pandas as pd


class TestSMAStrategy:
    """Test strategy for streaming mode validation"""
    
    def __init__(self, broker: SimBroker, symbol: str = "AAPL", strategy_id: str = "test_sma_001"):
        self.broker = broker
        self.symbol = symbol
        self.strategy_id = strategy_id
        
        # Loggers
        self.pattern_logger = PatternLogger(strategy_id)
        self.signal_logger = SignalLogger(strategy_id)
        
        # State
        self.in_position = False
        self.position_size = 0
        self.entry_price = None
        self.bar_count = 0
        
        print(f"✓ Strategy initialized: {self.__class__.__name__}")
    
    def on_bar(self, timestamp: datetime, data: dict):
        """Process each bar sequentially"""
        self.bar_count += 1
        
        symbol_data = data.get(self.symbol)
        if not symbol_data:
            return
        
        # Extract market data
        market_data = {
            'open': symbol_data.get('open'),
            'high': symbol_data.get('high'),
            'low': symbol_data.get('low'),
            'close': symbol_data.get('close'),
            'volume': symbol_data.get('volume')
        }
        
        # Extract indicators
        sma_fast = symbol_data.get('sma_10')
        sma_slow = symbol_data.get('sma_20')
        
        if sma_fast is None or sma_slow is None:
            return
        
        indicators = {
            'SMA_10': sma_fast,
            'SMA_20': sma_slow
        }
        
        # Check patterns
        self._check_entry_pattern(timestamp, market_data, indicators, sma_fast, sma_slow)
        if self.in_position:
            self._check_exit_pattern(timestamp, market_data, indicators, sma_fast, sma_slow)
    
    def _check_entry_pattern(self, timestamp, market_data, indicators, sma_fast, sma_slow):
        """Check for bullish crossover"""
        pattern_condition = "SMA_10 > SMA_20 (bullish)"
        pattern_found = sma_fast > sma_slow and not self.in_position
        
        self.pattern_logger.log_pattern(
            timestamp=timestamp,
            symbol=self.symbol,
            step_id="entry_check",
            step_title="Bullish SMA Crossover Check",
            pattern_condition=pattern_condition,
            pattern_found=pattern_found,
            market_data=market_data,
            indicator_values=indicators
        )
        
        if pattern_found:
            self._generate_entry_signal(timestamp, market_data, indicators)
    
    def _check_exit_pattern(self, timestamp, market_data, indicators, sma_fast, sma_slow):
        """Check for bearish crossover"""
        pattern_condition = "SMA_10 < SMA_20 (bearish)"
        pattern_found = sma_fast < sma_slow
        
        self.pattern_logger.log_pattern(
            timestamp=timestamp,
            symbol=self.symbol,
            step_id="exit_check",
            step_title="Bearish SMA Crossover Check",
            pattern_condition=pattern_condition,
            pattern_found=pattern_found,
            market_data=market_data,
            indicator_values=indicators
        )
        
        if pattern_found:
            self._generate_exit_signal(timestamp, market_data, indicators)
    
    def _generate_entry_signal(self, timestamp, market_data, indicators):
        """Generate entry signal"""
        size = 10
        price = market_data['close']
        
        self.signal_logger.log_signal(
            timestamp=timestamp,
            symbol=self.symbol,
            side="BUY",
            action="ENTRY",
            order_type="MARKET",
            size=size,
            price=price,
            reason="Bullish SMA crossover",
            market_data=market_data,
            indicator_values=indicators,
            strategy_state={'in_position': self.in_position}
        )
        
        signal = create_signal(
            timestamp=timestamp,
            symbol=self.symbol,
            side=OrderSide.BUY,
            action=OrderAction.ENTRY,
            order_type=OrderType.MARKET,
            size=size,
            strategy_id=self.strategy_id
        )
        self.broker.submit_signal(signal.to_dict())
        
        self.in_position = True
        self.position_size = size
        self.entry_price = price
        
        print(f"  🟢 Entry signal @ ${price:.2f}")
    
    def _generate_exit_signal(self, timestamp, market_data, indicators):
        """Generate exit signal"""
        size = self.position_size
        price = market_data['close']
        
        pnl = (price - self.entry_price) * size if self.entry_price else 0
        
        self.signal_logger.log_signal(
            timestamp=timestamp,
            symbol=self.symbol,
            side="SELL",
            action="EXIT",
            order_type="MARKET",
            size=size,
            price=price,
            reason="Bearish SMA crossover",
            market_data=market_data,
            indicator_values=indicators,
            strategy_state={'entry_price': self.entry_price}
        )
        
        signal = create_signal(
            timestamp=timestamp,
            symbol=self.symbol,
            side=OrderSide.SELL,
            action=OrderAction.EXIT,
            order_type=OrderType.MARKET,
            size=size,
            strategy_id=self.strategy_id
        )
        self.broker.submit_signal(signal.to_dict())
        
        self.in_position = False
        self.position_size = 0
        self.entry_price = None
        
        print(f"  🔴 Exit signal @ ${price:.2f} (P&L: ${pnl:.2f})")
    
    def finalize(self):
        """Close loggers"""
        print(f"\n✓ Processed {self.bar_count} bars total")
        self.pattern_logger.close()
        self.signal_logger.close()


def run_backtest_streaming():
    """Test backtest with STREAMING mode"""
    
    print("=" * 70)
    print("STREAMING MODE TEST")
    print("=" * 70)
    
    # 1. Configure backtest
    config = BacktestConfig(
        start_cash=10000,
        fee_flat=1.0,
        fee_pct=0.002,
        slippage_pct=0.0005
    )
    
    # 2. Initialize broker
    broker = SimBroker(config)
    
    # 3. Initialize strategy
    strategy = TestSMAStrategy(broker, symbol="AAPL", strategy_id="test_sma_streaming")
    
    # 4. Define indicators
    indicators = {
        'SMA': {'timeperiod': 10},
        'SMA': {'timeperiod': 20}
    }
    
    # 5. Load data in STREAMING mode
    print(f"\n🔄 Loading data in STREAMING mode...")
    data_stream = load_market_data(
        ticker=strategy.symbol,
        indicators=indicators,
        period='1mo',
        interval='1d',
        stream=True  # ✅ Enable streaming
    )
    
    print(f"✓ Data stream initialized")
    print(f"✓ Processing bars sequentially...\n")
    
    # 6. Process each bar sequentially
    bar_count = 0
    last_progress = -1
    
    for timestamp, market_data, progress_pct in data_stream:
        bar_count += 1
        
        # Strategy processes this bar
        strategy.on_bar(timestamp, market_data)
        
        # Broker executes any signals
        broker.step_to(timestamp, market_data)
        
        # Show progress every 20%
        current_progress = int(progress_pct // 20) * 20
        if current_progress > last_progress and current_progress > 0:
            print(f"  Progress: {progress_pct:.1f}% ({bar_count} bars)")
            last_progress = current_progress
    
    print(f"\n✓ Completed: Processed {bar_count} bars sequentially")
    
    # 7. Finalize strategy
    strategy.finalize()
    
    # 8. Get metrics
    metrics = broker.compute_metrics()
    
    # 9. Print results
    print("\n" + "=" * 70)
    print("BACKTEST RESULTS (STREAMING MODE)")
    print("=" * 70)
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
    print("=" * 70)
    
    return metrics


def run_backtest_batch():
    """Test backtest with BATCH mode for comparison"""
    
    print("\n\n" + "=" * 70)
    print("BATCH MODE TEST (for comparison)")
    print("=" * 70)
    
    # 1. Configure backtest
    config = BacktestConfig(
        start_cash=10000,
        fee_flat=1.0,
        fee_pct=0.002,
        slippage_pct=0.0005
    )
    
    # 2. Initialize broker
    broker = SimBroker(config)
    
    # 3. Initialize strategy
    strategy = TestSMAStrategy(broker, symbol="AAPL", strategy_id="test_sma_batch")
    
    # 4. Define indicators
    indicators = {
        'SMA': {'timeperiod': 10},
        'SMA': {'timeperiod': 20}
    }
    
    # 5. Load all data at once
    print(f"\n⚡ Loading data in BATCH mode...")
    df, metadata = load_market_data(
        ticker=strategy.symbol,
        indicators=indicators,
        period='1mo',
        interval='1d',
        stream=False  # Batch mode
    )
    
    print(f"✓ Loaded {len(df)} bars")
    print(f"✓ Columns: {list(df.columns)}")
    print(f"✓ Processing bars...\n")
    
    # 6. Process all bars
    for i, (timestamp, row) in enumerate(df.iterrows()):
        market_data = {
            strategy.symbol: {
                'open': row.get('Open', row.get('open')),
                'high': row.get('High', row.get('high')),
                'low': row.get('Low', row.get('low')),
                'close': row.get('Close', row.get('close')),
                'volume': row.get('Volume', row.get('volume')),
                **{col.lower(): row[col] for col in df.columns 
                   if col.lower() not in ['open', 'high', 'low', 'close', 'volume']}
            }
        }
        
        strategy.on_bar(timestamp, market_data)
        broker.step_to(timestamp, market_data)
        
        # Show progress every 20%
        if i % (len(df) // 5 or 1) == 0 and i > 0:
            progress = (i / len(df)) * 100
            print(f"  Progress: {progress:.1f}%")
    
    print(f"\n✓ Completed: Processed {len(df)} bars")
    
    # 7. Finalize strategy
    strategy.finalize()
    
    # 8. Get metrics
    metrics = broker.compute_metrics()
    
    # 9. Print results
    print("\n" + "=" * 70)
    print("BACKTEST RESULTS (BATCH MODE)")
    print("=" * 70)
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
    print("=" * 70)
    
    return metrics


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "SEQUENTIAL DATA INGESTION TEST" + " " * 23 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    # Test streaming mode
    streaming_metrics = run_backtest_streaming()
    
    # Test batch mode for comparison
    batch_metrics = run_backtest_batch()
    
    # Comparison
    print("\n\n" + "=" * 70)
    print("MODE COMPARISON")
    print("=" * 70)
    print(f"{'Metric':<30} {'Streaming':<20} {'Batch':<20}")
    print("-" * 70)
    print(f"{'Total Trades':<30} {streaming_metrics['total_trades']:<20} {batch_metrics['total_trades']:<20}")
    print(f"{'Net Profit':<30} ${streaming_metrics['net_profit']:<19,.2f} ${batch_metrics['net_profit']:<19,.2f}")
    print(f"{'Win Rate':<30} {streaming_metrics['win_rate']*100:<19.1f}% {batch_metrics['win_rate']*100:<19.1f}%")
    print("=" * 70)
    print("\n✅ Both modes should produce identical results!")
    print("✅ Streaming mode prevents look-ahead bias by design")
    print("=" * 70)
