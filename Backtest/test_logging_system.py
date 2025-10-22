"""
Test Script - Demonstrates Pattern and Signal Logging
======================================================

This script shows how the new logging system works with
sequential data processing.

Run this from the parent directory:
    python -m Backtest.test_logging_system

Or run from Backtest directory:
    cd Backtest
    python -m test_logging_system
"""

import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Now import with Backtest prefix
from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig, get_realistic_config
from Backtest.canonical_schema import create_signal, OrderSide, OrderAction, OrderType
from Backtest.data_loader import load_market_data
from Backtest.pattern_logger import PatternLogger
from Backtest.signal_logger import SignalLogger
from datetime import datetime
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        
        if ema_30 is None or ema_50 is None:
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
    print("=" * 70)
    
    # 1. Setup
    config = get_realistic_config()
    config.start_cash = 100000
    broker = SimBroker(config)
    
    strategy = SimpleEMAStrategy(broker, symbol="AAPL", strategy_id="test_ema_001")
    print("✓ Strategy initialized with loggers")
    
    # 2. Load data with EMA indicators
    print("\nLoading data with EMA indicators...")
    df = load_market_data(
        ticker="AAPL",
        period="3mo",
        interval="1d",
        indicators=[
            {"name": "EMA", "params": {"period": 30}},
            {"name": "EMA", "params": {"period": 50}}
        ]
    )
    print(f"✓ Loaded {len(df)} bars")
    print(f"✓ Columns: {list(df.columns)}")
    
    # 3. Run simulation - SEQUENTIAL ROW-BY-ROW
    print("\nRunning sequential simulation...")
    print("(Every row will be logged with pattern detection results)")
    
    for idx, row in df.iterrows():
        timestamp = idx if isinstance(idx, datetime) else pd.to_datetime(idx)
        
        market_data = {
            "AAPL": {
                'open': row.get('Open', row.get('open', 0)),
                'high': row.get('High', row.get('high', 0)),
                'low': row.get('Low', row.get('low', 0)),
                'close': row.get('Close', row.get('close', 0)),
                'volume': row.get('Volume', row.get('volume', 0)),
                'EMA_30': row.get('EMA_30'),
                'EMA_50': row.get('EMA_50')
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
