"""
Enhanced Strategy Template with Pattern and Signal Logging
===========================================================

This template demonstrates:
1. Sequential row-by-row data processing
2. Pattern detection logging (True/False for each step)
3. Signal logging for trade simulation
4. Proper integration with SimBroker

Use this as a base template for all generated strategies.

Version: 2.0.0
"""

# Add parent directory to path for imports
import sys
from pathlib import Path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig, get_realistic_config
from Backtest.canonical_schema import create_signal, OrderSide, OrderAction, OrderType
from Backtest.data_loader import load_market_data
from Backtest.pattern_logger import PatternLogger
from Backtest.signal_logger import SignalLogger
from datetime import datetime
import pandas as pd
from typing import Dict, List, Optional
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnhancedStrategyTemplate:
    """
    Enhanced strategy template with pattern and signal logging
    
    Features:
    - Sequential data reading row by row
    - Pattern detection for each step with True/False logging
    - Signal generation with full context logging
    - Indicator value tracking
    """
    
    def __init__(
        self,
        broker: SimBroker,
        symbol: str = "AAPL",
        strategy_id: str = "enhanced_template",
        **params
    ):
        """
        Initialize strategy
        
        Args:
            broker: SimBroker instance
            symbol: Trading symbol
            strategy_id: Unique strategy identifier
            **params: Strategy-specific parameters
        """
        self.broker = broker
        self.symbol = symbol
        self.strategy_id = strategy_id
        self.params = params
        
        # Initialize loggers
        self.pattern_logger = PatternLogger(strategy_id)
        self.signal_logger = SignalLogger(strategy_id)
        
        # Strategy state
        self.position_size = 0
        self.entry_price = None
        self.in_position = False
        
        # Data history for indicator calculation
        self.data_history: List[Dict] = []
        
        logger.info(f"Strategy initialized: {strategy_id}")
        logger.info(f"Parameters: {params}")
    
    def on_bar(self, timestamp: datetime, data: Dict[str, Dict]):
        """
        Process each bar of market data sequentially
        
        This is called for EVERY row of data.
        Pattern detection is logged for each step.
        
        Args:
            timestamp: Current bar timestamp
            data: Market data {symbol: {open, high, low, close, volume, indicators...}}
        """
        symbol_data = data.get(self.symbol)
        if not symbol_data:
            return
        
        # Store in history for later analysis
        row_data = {
            'timestamp': timestamp,
            **symbol_data
        }
        self.data_history.append(row_data)
        
        # Extract market data
        market_data = {
            'open': symbol_data.get('open'),
            'high': symbol_data.get('high'),
            'low': symbol_data.get('low'),
            'close': symbol_data.get('close'),
            'volume': symbol_data.get('volume')
        }
        
        # Extract indicators (these should be pre-calculated in data)
        indicators = self._extract_indicators(symbol_data)
        
        # Process strategy steps sequentially
        self._process_strategy_steps(timestamp, market_data, indicators)
    
    def _extract_indicators(self, symbol_data: Dict) -> Dict[str, float]:
        """
        Extract indicator values from symbol data
        
        Override this in your strategy to extract specific indicators.
        
        Args:
            symbol_data: Raw symbol data including indicators
            
        Returns:
            Dictionary of indicator values
        """
        # Example: Extract EMA indicators
        indicators = {}
        for key, value in symbol_data.items():
            if key.startswith('EMA_') or key.startswith('SMA_') or \
               key.startswith('RSI') or key.startswith('MACD'):
                indicators[key] = value
        return indicators
    
    def _process_strategy_steps(
        self,
        timestamp: datetime,
        market_data: Dict[str, float],
        indicators: Dict[str, float]
    ):
        """
        Process strategy steps with pattern logging
        
        Override this method to implement your strategy logic.
        Each step should log pattern detection results.
        
        Args:
            timestamp: Current timestamp
            market_data: OHLCV data
            indicators: Calculated indicators
        """
        # Example Step 1: Check for entry condition
        self._check_entry_pattern(timestamp, market_data, indicators)
        
        # Example Step 2: Check for exit condition
        if self.in_position:
            self._check_exit_pattern(timestamp, market_data, indicators)
    
    def _check_entry_pattern(
        self,
        timestamp: datetime,
        market_data: Dict[str, float],
        indicators: Dict[str, float]
    ):
        """
        Example: Check entry pattern and log result
        
        Replace this with your actual entry logic.
        """
        step_id = "entry_step"
        step_title = "Check Entry Condition"
        pattern_condition = "Your entry condition here"  # e.g., "EMA_30 > EMA_50"
        
        # Example pattern check (replace with your logic)
        pattern_found = False  # Your condition evaluation
        
        # Log pattern detection (EVERY row is logged)
        self.pattern_logger.log_pattern(
            timestamp=timestamp,
            symbol=self.symbol,
            step_id=step_id,
            step_title=step_title,
            pattern_condition=pattern_condition,
            pattern_found=pattern_found,
            market_data=market_data,
            indicator_values=indicators,
            notes="Entry pattern check"
        )
        
        # If pattern found and not in position, generate signal
        if pattern_found and not self.in_position:
            self._generate_entry_signal(timestamp, market_data, indicators)
    
    def _check_exit_pattern(
        self,
        timestamp: datetime,
        market_data: Dict[str, float],
        indicators: Dict[str, float]
    ):
        """
        Example: Check exit pattern and log result
        
        Replace this with your actual exit logic.
        """
        step_id = "exit_step"
        step_title = "Check Exit Condition"
        pattern_condition = "Your exit condition here"  # e.g., "Stop loss or Take profit"
        
        # Example pattern check (replace with your logic)
        pattern_found = False  # Your condition evaluation
        
        # Log pattern detection (EVERY row is logged)
        self.pattern_logger.log_pattern(
            timestamp=timestamp,
            symbol=self.symbol,
            step_id=step_id,
            step_title=step_title,
            pattern_condition=pattern_condition,
            pattern_found=pattern_found,
            market_data=market_data,
            indicator_values=indicators,
            notes="Exit pattern check"
        )
        
        # If pattern found, generate exit signal
        if pattern_found:
            self._generate_exit_signal(timestamp, market_data, indicators)
    
    def _generate_entry_signal(
        self,
        timestamp: datetime,
        market_data: Dict[str, float],
        indicators: Dict[str, float]
    ):
        """Generate and log entry signal"""
        size = 100  # Your position sizing logic
        price = market_data['close']
        reason = "Entry pattern detected"  # Describe why signal was generated
        
        # Log the signal
        signal_id = self.signal_logger.log_signal(
            timestamp=timestamp,
            symbol=self.symbol,
            side="BUY",
            action="ENTRY",
            order_type="MARKET",
            size=size,
            price=price,
            reason=reason,
            market_data=market_data,
            indicator_values=indicators,
            strategy_state={
                'in_position': self.in_position,
                'position_size': self.position_size
            },
            notes=f"Generated by {self.strategy_id}"
        )
        
        # Submit signal to broker
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
        
        # Update logger with order_id
        if order_id and self.signal_logger.signals:
            self.signal_logger.signals[-1]['order_id'] = order_id
        
        # Update strategy state
        self.in_position = True
        self.position_size = size
        self.entry_price = price
        
        logger.info(f"✓ ENTRY signal: {signal_id}, Order: {order_id}")
    
    def _generate_exit_signal(
        self,
        timestamp: datetime,
        market_data: Dict[str, float],
        indicators: Dict[str, float]
    ):
        """Generate and log exit signal"""
        size = self.position_size
        price = market_data['close']
        reason = "Exit pattern detected"  # Describe why signal was generated
        
        # Log the signal
        signal_id = self.signal_logger.log_signal(
            timestamp=timestamp,
            symbol=self.symbol,
            side="SELL",
            action="EXIT",
            order_type="MARKET",
            size=size,
            price=price,
            reason=reason,
            market_data=market_data,
            indicator_values=indicators,
            strategy_state={
                'in_position': self.in_position,
                'position_size': self.position_size,
                'entry_price': self.entry_price,
                'pnl': (price - self.entry_price) * size if self.entry_price else 0
            },
            notes=f"Generated by {self.strategy_id}"
        )
        
        # Submit signal to broker
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
        
        # Update logger with order_id
        if order_id and self.signal_logger.signals:
            self.signal_logger.signals[-1]['order_id'] = order_id
        
        # Update strategy state
        self.in_position = False
        self.position_size = 0
        self.entry_price = None
        
        logger.info(f"✓ EXIT signal: {signal_id}, Order: {order_id}")
    
    def finalize(self):
        """Close loggers and export summaries"""
        logger.info("Finalizing strategy...")
        
        # Close loggers
        self.pattern_logger.close()
        self.signal_logger.close()
        
        logger.info("Strategy finalized")


def run_backtest():
    """
    Example backtest runner showing sequential data processing
    with pattern and signal logging
    """
    logger.info("=" * 70)
    logger.info("Enhanced Strategy Backtest with Pattern & Signal Logging")
    logger.info("=" * 70)
    
    # 1. Configure broker
    config = get_realistic_config()
    config.start_cash = 100000
    config.save_trades = True
    
    # 2. Initialize broker
    broker = SimBroker(config)
    
    # 3. Initialize strategy
    strategy = EnhancedStrategyTemplate(
        broker=broker,
        symbol="AAPL",
        strategy_id="enhanced_template_001"
    )
    
    # 4. Load market data with indicators
    logger.info("Loading market data...")
    
    # Load data with indicators pre-calculated
    df = load_market_data(
        ticker="AAPL",
        period="6mo",
        interval="1d",
        indicators=[
            {"name": "EMA", "params": {"period": 30}},
            {"name": "EMA", "params": {"period": 50}}
        ]
    )
    
    logger.info(f"Data loaded: {len(df)} bars")
    logger.info(f"Columns: {list(df.columns)}")
    
    # 5. Run simulation - SEQUENTIAL ROW-BY-ROW PROCESSING
    logger.info("Running simulation (row-by-row)...")
    
    for idx, row in df.iterrows():
        timestamp = idx if isinstance(idx, datetime) else pd.to_datetime(idx)
        
        # Prepare market data for this row
        market_data = {
            "AAPL": {
                'open': row.get('Open', row.get('open', 0)),
                'high': row.get('High', row.get('high', 0)),
                'low': row.get('Low', row.get('low', 0)),
                'close': row.get('Close', row.get('close', 0)),
                'volume': row.get('Volume', row.get('volume', 0)),
                # Include all indicator columns
                **{col: row[col] for col in df.columns if col.startswith(('EMA_', 'SMA_', 'RSI', 'MACD'))}
            }
        }
        
        # Strategy analyzes this row and logs patterns
        strategy.on_bar(timestamp, market_data)
        
        # Broker processes any signals and updates state
        broker.step_to(timestamp, market_data)
    
    logger.info("Simulation complete")
    
    # 6. Finalize strategy (close loggers)
    strategy.finalize()
    
    # 7. Get and display results
    metrics = broker.compute_metrics()
    
    # Export trades
    broker.export_trades("results/trades.csv")
    
    # Print summary
    print("\n" + "=" * 70)
    print("BACKTEST RESULTS")
    print("=" * 70)
    print(f"Final Equity: ${metrics['final_equity']:,.2f}")
    print(f"Net Profit: ${metrics['net_profit']:,.2f}")
    print(f"Total Trades: {metrics['total_trades']}")
    print(f"Win Rate: {metrics['win_rate']*100:.1f}%")
    print("=" * 70)
    
    # Get logger summaries
    pattern_summary = strategy.pattern_logger.get_pattern_summary()
    signal_summary = strategy.signal_logger.get_signal_summary()
    
    print("\n" + "=" * 70)
    print("PATTERN DETECTION SUMMARY")
    print("=" * 70)
    print(f"Total Rows Analyzed: {pattern_summary['total_rows']}")
    print(f"Patterns Found: {pattern_summary['patterns_found']}")
    print(f"Detection Rate: {pattern_summary['detection_rate']:.2f}%")
    print(f"Log File: {pattern_summary['log_file']}")
    print("=" * 70)
    
    print("\n" + "=" * 70)
    print("SIGNAL GENERATION SUMMARY")
    print("=" * 70)
    print(f"Total Signals: {signal_summary['total_signals']}")
    print(f"Entry Signals: {signal_summary['entry_signals']}")
    print(f"Exit Signals: {signal_summary['exit_signals']}")
    print(f"CSV File: {signal_summary['csv_file']}")
    print(f"JSON File: {signal_summary['json_file']}")
    print("=" * 70)
    
    return metrics


if __name__ == "__main__":
    try:
        metrics = run_backtest()
    except Exception as e:
        logger.error(f"Backtest failed: {e}", exc_info=True)
        raise
