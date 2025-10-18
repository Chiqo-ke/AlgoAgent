"""
MT5 Integration Example
=======================

End-to-end example demonstrating:
1. Running Python backtest with signal export
2. Preparing signals for MT5
3. Validating against MT5 execution
4. Reconciling results

Last updated: 2025-10-18
Version: 1.0.0
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import logging
import pandas as pd

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig
from Backtest.data_loader import DataLoader
from Backtest.canonical_schema import create_signal, OrderSide, OrderAction, OrderType
from Backtest.mt5_connector import MT5Connector, align_timestamp_to_mt5
from Backtest.mt5_reconciliation import MT5Reconciliation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleXAUUSDStrategy:
    """
    Simple XAUUSD strategy for demonstration
    
    Strategy: Moving Average Crossover
    - Buy when fast MA crosses above slow MA
    - Sell when fast MA crosses below slow MA
    """
    
    def __init__(self, broker: SimBroker, fast_period: int = 10, slow_period: int = 30):
        self.broker = broker
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.price_history = []
    
    def on_bar(self, timestamp: datetime, data: dict):
        """Process each bar"""
        bars = data.get('XAUUSD', {})
        if not bars:
            return
        
        close = bars['close']
        self.price_history.append(close)
        
        # Need enough data
        if len(self.price_history) < self.slow_period + 1:
            return
        
        # Calculate MAs
        prices = self.price_history
        fast_ma = sum(prices[-self.fast_period:]) / self.fast_period
        slow_ma = sum(prices[-self.slow_period:]) / self.slow_period
        
        prev_fast = sum(prices[-(self.fast_period+1):-1]) / self.fast_period
        prev_slow = sum(prices[-(self.slow_period+1):-1]) / self.slow_period
        
        # Detect crossover
        bullish_cross = prev_fast <= prev_slow and fast_ma > slow_ma
        bearish_cross = prev_fast >= prev_slow and fast_ma < slow_ma
        
        # Get position
        snapshot = self.broker.get_account_snapshot()
        has_position = len(snapshot['positions']) > 0
        
        # Trading logic
        if bullish_cross and not has_position:
            # Enter long
            signal = create_signal(
                timestamp=timestamp,
                symbol="XAUUSD",
                side=OrderSide.BUY,
                action=OrderAction.ENTRY,
                order_type=OrderType.MARKET,
                size=100  # 100 oz = 1 lot
            )
            
            # Add stop loss and take profit to metadata
            signal.meta['stop_loss'] = close - 10.0  # $10 below entry
            signal.meta['take_profit'] = close + 20.0  # $20 above entry
            
            self.broker.submit_signal(signal.to_dict())
            logger.info(f"{timestamp}: BUY signal at {close}")
        
        elif bearish_cross and has_position:
            # Exit long
            signal = create_signal(
                timestamp=timestamp,
                symbol="XAUUSD",
                side=OrderSide.SELL,
                action=OrderAction.EXIT,
                order_type=OrderType.MARKET,
                size=100
            )
            self.broker.submit_signal(signal.to_dict())
            logger.info(f"{timestamp}: EXIT signal at {close}")


def run_python_backtest_with_mt5_export():
    """
    Step 1: Run Python backtest and export signals for MT5
    """
    logger.info("=" * 70)
    logger.info("STEP 1: Running Python Backtest with MT5 Signal Export")
    logger.info("=" * 70)
    
    # Configure backtest
    config = BacktestConfig(
        start_cash=10000,
        fee_flat=0.0,
        fee_pct=0.001,
        slippage_pct=0.0005
    )
    
    # Initialize broker with MT5 export enabled
    broker = SimBroker(
        config=config,
        enable_mt5_export=True,
        mt5_symbol="XAUUSD",
        mt5_timeframe="H1"
    )
    
    # Load sample data (you should replace this with actual XAUUSD data)
    # For demonstration, we'll create synthetic data
    logger.info("Loading XAUUSD data...")
    
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 31)
    
    # Generate synthetic XAUUSD data (replace with actual data loading)
    dates = pd.date_range(start_date, end_date, freq='1H')
    base_price = 2000.0
    
    data = []
    for i, date in enumerate(dates):
        # Simple random walk
        change = (i % 10 - 5) * 0.5
        close = base_price + change
        data.append({
            'timestamp': date,
            'open': close - 0.5,
            'high': close + 1.0,
            'low': close - 1.0,
            'close': close,
            'volume': 1000
        })
    
    df = pd.DataFrame(data)
    logger.info(f"Loaded {len(df)} bars from {start_date} to {end_date}")
    
    # Initialize strategy
    strategy = SimpleXAUUSDStrategy(broker)
    
    # Run backtest
    logger.info("Running backtest...")
    for idx, row in df.iterrows():
        timestamp = row['timestamp']
        market_data = {
            'XAUUSD': {
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row['volume']
            }
        }
        
        # Step broker forward
        broker.step_to(timestamp, market_data)
        
        # Process strategy
        strategy.on_bar(timestamp, market_data)
    
    # Get results
    metrics = broker.compute_metrics()
    logger.info("\nPython Backtest Results:")
    logger.info(f"  Total Trades: {metrics.get('total_trades', 0)}")
    logger.info(f"  Win Rate: {metrics.get('win_rate', 0):.2%}")
    logger.info(f"  Total P&L: ${metrics.get('total_pnl', 0):,.2f}")
    logger.info(f"  Max Drawdown: {metrics.get('max_drawdown', 0):.2%}")
    
    # Export trades
    trades_path = Path("Backtest/results/trades.csv")
    broker.export_trades(str(trades_path))
    logger.info(f"\nTrades exported to: {trades_path}")
    
    # Export signals for MT5
    signal_files = broker.export_mt5_signals(format="both")
    if signal_files:
        logger.info(f"\nMT5 Signals exported:")
        logger.info(f"  CSV: {signal_files.get('csv')}")
        logger.info(f"  JSON: {signal_files.get('json')}")
        
        # Get export summary
        summary = broker.get_mt5_export_summary()
        if summary:
            logger.info(f"\nSignal Export Summary:")
            logger.info(f"  Total Signals: {summary['total_signals']}")
            logger.info(f"  Signal Types: {summary['signal_types']}")
            logger.info(f"  Lot Conversion: {summary['shares_per_lot']} oz/lot")
    
    return broker, signal_files, metrics


def validate_mt5_data_sync():
    """
    Step 2: Validate that Python and MT5 have same historical data
    """
    logger.info("\n" + "=" * 70)
    logger.info("STEP 2: Validating Data Synchronization with MT5")
    logger.info("=" * 70)
    
    try:
        connector = MT5Connector()
        
        if not connector.connect():
            logger.warning("Could not connect to MT5 - skipping data validation")
            logger.info("Make sure MT5 terminal is running and logged in")
            return False
        
        # Get symbol info
        symbol_info = connector.get_symbol_info("XAUUSD")
        if symbol_info:
            logger.info(f"\nXAUUSD Symbol Info:")
            logger.info(f"  Description: {symbol_info['description']}")
            logger.info(f"  Contract Size: {symbol_info['trade_contract_size']} oz/lot")
            logger.info(f"  Min Lot: {symbol_info['volume_min']}")
            logger.info(f"  Spread: {symbol_info['spread']} points")
        
        # Get sample data
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 7)
        
        mt5_data = connector.get_historical_data("XAUUSD", "H1", start_date, end_date)
        if mt5_data is not None:
            logger.info(f"\nMT5 Historical Data:")
            logger.info(f"  Bars: {len(mt5_data)}")
            logger.info(f"  Date Range: {mt5_data['time'].min()} to {mt5_data['time'].max()}")
            logger.info(f"  Price Range: ${mt5_data['close'].min():.2f} - ${mt5_data['close'].max():.2f}")
        
        # Get MT5 Files directory
        files_path = connector.get_mt5_files_path()
        if files_path:
            logger.info(f"\nMT5 Files Directory: {files_path}")
            logger.info("Copy your signal CSV file to this directory for the EA to read")
        
        connector.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"MT5 validation failed: {e}")
        return False


def prepare_mt5_instructions(signal_files: dict):
    """
    Step 3: Provide instructions for MT5 setup
    """
    logger.info("\n" + "=" * 70)
    logger.info("STEP 3: MT5 Setup Instructions")
    logger.info("=" * 70)
    
    if not signal_files:
        logger.error("No signal files available")
        return
    
    csv_file = signal_files.get('csv')
    
    logger.info("""
MT5 Strategy Tester Setup:
--------------------------

1. COPY SIGNAL FILE:
   - Copy the signal CSV file to MT5's Files directory
   - Path: C:\\Users\\[YourUser]\\AppData\\Roaming\\MetaQuotes\\Terminal\\[TerminalID]\\MQL5\\Files\\
   - File: {}

2. COPY EXPERT ADVISOR:
   - Copy 'PythonSignalExecutor.mq5' to MT5's Experts directory
   - Path: C:\\Users\\[YourUser]\\AppData\\Roaming\\MetaQuotes\\Terminal\\[TerminalID]\\MQL5\\Experts\\
   - Or use MetaEditor to open and compile the EA

3. CONFIGURE STRATEGY TESTER:
   - Open Strategy Tester (Ctrl+R)
   - Expert Advisor: PythonSignalExecutor
   - Symbol: XAUUSD
   - Period: H1 (1 Hour)
   - Date Range: Match your Python backtest dates
   - Model: "Every tick based on real ticks" (most accurate)
   - Optimization: OFF
   
4. SET EA PARAMETERS:
   - SignalFile: {} (just the filename)
   - RiskPercent: 0 (use signal lot sizes)
   - Slippage: 10 points
   - MagicNumber: 20241018

5. RUN BACKTEST:
   - Click "Start" button
   - Monitor "Journal" tab for EA logs
   - Check for signal reading confirmations

6. EXPORT RESULTS:
   - After completion, right-click report → "Save as Report"
   - Save to: Backtest/mt5_results/
   - Compare with Python results

""".format(csv_file.name if csv_file else "signal_file.csv", 
           csv_file.name if csv_file else "signal_file.csv"))


def run_reconciliation():
    """
    Step 4: Reconcile Python and MT5 results (after MT5 backtest)
    """
    logger.info("\n" + "=" * 70)
    logger.info("STEP 4: Reconciliation (Run after MT5 backtest completes)")
    logger.info("=" * 70)
    
    logger.info("""
After running the MT5 backtest:

1. COLLECT MT5 METRICS:
   - Total trades
   - Win rate
   - Total P&L
   - Max drawdown
   - Sharpe ratio

2. RUN RECONCILIATION:
   ```python
   from Backtest.mt5_reconciliation import quick_reconcile
   
   quick_reconcile(
       signals_path=Path("Backtest/mt5_signals/signals.csv"),
       python_trades_path=Path("Backtest/results/trades.csv"),
       mt5_symbol="XAUUSD",
       mt5_start_date=datetime(2024, 1, 1),
       mt5_end_date=datetime(2024, 1, 31),
       python_metrics={...},  # From Python backtest
       mt5_metrics={...},     # From MT5 report
       output_dir=Path("Backtest/mt5_results/")
   )
   ```

3. REVIEW DISCREPANCIES:
   - Check reconciliation_report.json
   - Investigate unmatched signals
   - Compare execution prices
   - Analyze metric differences

4. EXPECTED DIFFERENCES:
   - Slippage (MT5 more realistic)
   - Spread costs
   - Order rejections (margin constraints)
   - Minor timing differences

5. UNEXPECTED DIFFERENCES (Investigate):
   - Large execution rate difference
   - Wrong trade directions
   - Significant P&L variance
   - Missing trades
""")


def main():
    """Run complete MT5 integration example"""
    logger.info("╔" + "═" * 68 + "╗")
    logger.info("║" + " " * 15 + "MT5 INTEGRATION EXAMPLE" + " " * 30 + "║")
    logger.info("║" + " " * 10 + "Python Signal Generation → MT5 Execution" + " " * 18 + "║")
    logger.info("╚" + "═" * 68 + "╝")
    
    try:
        # Step 1: Run Python backtest with export
        broker, signal_files, metrics = run_python_backtest_with_mt5_export()
        
        # Step 2: Validate MT5 connection and data
        validate_mt5_data_sync()
        
        # Step 3: Provide MT5 setup instructions
        prepare_mt5_instructions(signal_files)
        
        # Step 4: Reconciliation instructions
        run_reconciliation()
        
        logger.info("\n" + "=" * 70)
        logger.info("MT5 Integration Example Complete!")
        logger.info("=" * 70)
        logger.info("\nNext Steps:")
        logger.info("1. Copy signal file to MT5 Files directory")
        logger.info("2. Run MT5 Strategy Tester with PythonSignalExecutor EA")
        logger.info("3. Compare results and reconcile any discrepancies")
        logger.info("\nFor detailed documentation, see: Backtest/MT5_INTEGRATION_GUIDE.md")
        
    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
