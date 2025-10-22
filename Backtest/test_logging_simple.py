"""
Simple Test - Pattern and Signal Logging (No External Dependencies)
====================================================================

This test uses synthetic data to demonstrate the logging system
without requiring yfinance or other external dependencies.
"""

import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig, get_realistic_config
from Backtest.canonical_schema import create_signal, OrderSide, OrderAction, OrderType
from Backtest.pattern_logger import PatternLogger
from Backtest.signal_logger import SignalLogger
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_test_data(days=60):
    """Generate synthetic OHLCV data with EMA indicators"""
    np.random.seed(42)
    
    # Generate dates
    start_date = datetime(2025, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(days)]
    
    # Generate random walk price data
    close_prices = []
    price = 150.0
    for _ in range(days):
        change = np.random.randn() * 2  # Random walk
        price = max(100, price + change)  # Keep above 100
        close_prices.append(price)
    
    # Create OHLCV
    data = []
    for i, (date, close) in enumerate(zip(dates, close_prices)):
        open_price = close + np.random.randn() * 0.5
        high = max(open_price, close) + abs(np.random.randn()) * 0.5
        low = min(open_price, close) - abs(np.random.randn()) * 0.5
        volume = int(1000000 + np.random.randn() * 100000)
        
        data.append({
            'timestamp': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    
    # Calculate EMA indicators
    df['EMA_30'] = df['close'].ewm(span=30, adjust=False).mean()
    df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
    
    return df


class SimpleEMAStrategy:
    """Simple EMA crossover with logging"""
    
    def __init__(self, broker, symbol="AAPL", strategy_id="ema_test"):
        self.broker = broker
        self.symbol = symbol
        self.strategy_id = strategy_id
        
        # Initialize loggers
        self.pattern_logger = PatternLogger(strategy_id)
        self.signal_logger = SignalLogger(strategy_id)
        
        # Strategy state
        self.in_position = False
        self.position_size = 0
        self.entry_price = None
    
    def on_bar(self, timestamp, data):
        """Process each bar with pattern logging"""
        symbol_data = data.get(self.symbol)
        if not symbol_data:
            return
        
        # Extract data
        market_data = {
            'open': symbol_data.get('open'),
            'high': symbol_data.get('high'),
            'low': symbol_data.get('low'),
            'close': symbol_data.get('close'),
            'volume': symbol_data.get('volume')
        }
        
        # Get EMA values
        ema_30 = symbol_data.get('EMA_30')
        ema_50 = symbol_data.get('EMA_50')
        
        if ema_30 is None or ema_50 is None or pd.isna(ema_30) or pd.isna(ema_50):
            return
        
        indicators = {'EMA_30': ema_30, 'EMA_50': ema_50}
        
        # Check entry pattern (LOGGED FOR EVERY ROW)
        entry_condition = "EMA_30 > EMA_50"
        entry_pattern_found = ema_30 > ema_50 and not self.in_position
        
        self.pattern_logger.log_pattern(
            timestamp=timestamp,
            symbol=self.symbol,
            step_id="s1_entry",
            step_title="EMA Crossover Entry",
            pattern_condition=entry_condition,
            pattern_found=entry_pattern_found,
            market_data=market_data,
            indicator_values=indicators,
            notes=f"EMA_30={ema_30:.2f}, EMA_50={ema_50:.2f}"
        )
        
        # Generate entry signal if pattern found
        if entry_pattern_found:
            size = 100
            price = market_data['close']
            
            # Log the signal
            self.signal_logger.log_signal(
                timestamp=timestamp,
                symbol=self.symbol,
                side="BUY",
                action="ENTRY",
                order_type="MARKET",
                size=size,
                price=price,
                reason="EMA_30 crossed above EMA_50",
                market_data=market_data,
                indicator_values=indicators,
                strategy_state={'in_position': False}
            )
            
            # Submit to broker
            signal = create_signal(
                timestamp=timestamp,
                symbol=self.symbol,
                side=OrderSide.BUY,
                action=OrderAction.ENTRY,
                order_type=OrderType.MARKET,
                size=size,
                strategy_id=self.strategy_id
            )
            order_id = self.broker.submit_signal(signal.to_dict())
            
            self.in_position = True
            self.position_size = size
            self.entry_price = price
            
            logger.info(f"✓ ENTRY signal at {timestamp}, price={price:.2f}")
        
        # Check exit pattern (LOGGED FOR EVERY ROW WHERE IN POSITION)
        if self.in_position:
            exit_condition = "EMA_30 < EMA_50"
            exit_pattern_found = ema_30 < ema_50
            
            self.pattern_logger.log_pattern(
                timestamp=timestamp,
                symbol=self.symbol,
                step_id="s2_exit",
                step_title="EMA Crossover Exit",
                pattern_condition=exit_condition,
                pattern_found=exit_pattern_found,
                market_data=market_data,
                indicator_values=indicators,
                notes=f"EMA_30={ema_30:.2f}, EMA_50={ema_50:.2f}"
            )
            
            # Generate exit signal if pattern found
            if exit_pattern_found:
                size = self.position_size
                price = market_data['close']
                
                # Log the signal
                self.signal_logger.log_signal(
                    timestamp=timestamp,
                    symbol=self.symbol,
                    side="SELL",
                    action="EXIT",
                    order_type="MARKET",
                    size=size,
                    price=price,
                    reason="EMA_30 crossed below EMA_50",
                    market_data=market_data,
                    indicator_values=indicators,
                    strategy_state={
                        'entry_price': self.entry_price,
                        'pnl': (price - self.entry_price) * size
                    }
                )
                
                # Submit to broker
                signal = create_signal(
                    timestamp=timestamp,
                    symbol=self.symbol,
                    side=OrderSide.SELL,
                    action=OrderAction.EXIT,
                    order_type=OrderType.MARKET,
                    size=size,
                    strategy_id=self.strategy_id
                )
                order_id = self.broker.submit_signal(signal.to_dict())
                
                self.in_position = False
                self.position_size = 0
                self.entry_price = None
                
                logger.info(f"✓ EXIT signal at {timestamp}, price={price:.2f}")
    
    def finalize(self):
        """Close loggers"""
        self.pattern_logger.close()
        self.signal_logger.close()


def test_logging_system():
    """Test the pattern and signal logging system"""
    
    print("=" * 70)
    print("Testing Pattern and Signal Logging System")
    print("(Using Synthetic Data)")
    print("=" * 70)
    
    # 1. Setup
    config = get_realistic_config()
    config.start_cash = 100000
    broker = SimBroker(config)
    
    strategy = SimpleEMAStrategy(broker, symbol="AAPL", strategy_id="test_ema_001")
    print("✓ Strategy initialized with loggers")
    
    # 2. Generate synthetic data
    print("\nGenerating synthetic data with EMA indicators...")
    df = generate_test_data(days=60)
    print(f"✓ Generated {len(df)} bars")
    print(f"✓ Columns: {list(df.columns)}")
    
    # 3. Run simulation - SEQUENTIAL ROW-BY-ROW
    print("\nRunning sequential simulation...")
    print("(Every row will be logged with pattern detection results)")
    
    for timestamp, row in df.iterrows():
        market_data = {
            "AAPL": {
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row['volume'],
                'EMA_30': row['EMA_30'],
                'EMA_50': row['EMA_50']
            }
        }
        
        strategy.on_bar(timestamp, market_data)
        broker.step_to(timestamp, market_data)
    
    print("✓ Simulation complete")
    
    # 4. Finalize
    strategy.finalize()
    
    # 5. Results
    metrics = broker.compute_metrics()
    
    print("\n" + "=" * 70)
    print("BACKTEST RESULTS")
    print("=" * 70)
    print(f"Final Equity: ${metrics['final_equity']:,.2f}")
    print(f"Net Profit: ${metrics['net_profit']:,.2f}")
    print(f"Total Trades: {metrics['total_trades']}")
    print(f"Win Rate: {metrics['win_rate']*100:.1f}%")
    
    # 6. Logger summaries
    pattern_summary = strategy.pattern_logger.get_pattern_summary()
    signal_summary = strategy.signal_logger.get_signal_summary()
    
    print("\n" + "=" * 70)
    print("PATTERN DETECTION SUMMARY")
    print("=" * 70)
    print(f"Total Rows Analyzed: {pattern_summary['total_rows']}")
    print(f"Patterns Found: {pattern_summary['patterns_found']}")
    print(f"Detection Rate: {pattern_summary['detection_rate']:.2f}%")
    print(f"\n📁 Pattern Log: {pattern_summary['log_file']}")
    
    print("\n" + "=" * 70)
    print("SIGNAL GENERATION SUMMARY")
    print("=" * 70)
    print(f"Total Signals: {signal_summary['total_signals']}")
    print(f"Entry Signals: {signal_summary['entry_signals']}")
    print(f"Exit Signals: {signal_summary['exit_signals']}")
    print(f"\n📁 Signal CSV: {signal_summary['csv_file']}")
    print(f"📁 Signal JSON: {signal_summary['json_file']}")
    
    print("\n" + "=" * 70)
    print("✓ Test completed successfully!")
    print("=" * 70)
    print("\nCheck the 'signals' folder for detailed logs:")
    print("  - Pattern logs show True/False for each row")
    print("  - Signal logs contain all trading signals for simulation")
    print("=" * 70)


if __name__ == "__main__":
    try:
        test_logging_system()
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        raise
