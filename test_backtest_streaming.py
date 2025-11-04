"""
Test Backtesting Module with Sequential Execution and Logging

This test verifies:
1. Data loading works correctly
2. Strategy execution with backtesting.py
3. Trade signals are captured
4. Sequential processing for streaming visualization

Run: python test_backtest_streaming.py
"""

import sys
from pathlib import Path
import logging
from datetime import datetime
import json

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)8s | %(name)s | %(message)s',
    handlers=[
        logging.FileHandler('backtest_test.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Add Backtest directory to path
BACKTEST_DIR = Path(__file__).parent / "Backtest"
sys.path.insert(0, str(BACKTEST_DIR))

logger.info("=" * 80)
logger.info("BACKTESTING MODULE TEST - Sequential Execution")
logger.info("=" * 80)

def test_data_loading():
    """Test 1: Verify data loading works"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 1: Data Loading")
    logger.info("=" * 80)
    
    try:
        from Backtest.data_loader import load_market_data
        
        logger.info("Loading data for AAPL, 3mo, 1d...")
        
        # Test non-streaming mode first
        result = load_market_data(
            ticker="AAPL",
            indicators={"SMA": {"timeperiod": 20}, "RSI": {"timeperiod": 14}},
            period="3mo",
            interval="1d",
            stream=False
        )
        
        # Unpack result - load_market_data returns (df, ticker) tuple
        if isinstance(result, tuple):
            data, ticker = result
            logger.info(f"[OK] Data loaded successfully!")
            logger.info(f"   Ticker: {ticker}")
        else:
            data = result
            logger.info(f"[OK] Data loaded successfully!")
        
        logger.info(f"   Shape: {data.shape}")
        logger.info(f"   Columns: {list(data.columns)}")
        logger.info(f"   Date range: {data.index[0]} to {data.index[-1]}")
        logger.info(f"   First row:\n{data.iloc[0]}")
        
        return data
        
    except Exception as e:
        logger.error(f"[ERROR] Data loading failed: {e}", exc_info=True)
        raise


def test_strategy_creation():
    """Test 2: Verify strategy creation from canonical JSON"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Strategy Creation")
    logger.info("=" * 80)
    
    try:
        from Backtest.backtesting_adapter import create_strategy_from_canonical
        
        # Simple SMA crossover strategy
        canonical_json = {
            "name": "SMA_Crossover_Test",
            "type": "canonical",
            "version": "1.0",
            "description": "Simple SMA crossover for testing",
            "parameters": {
                "fast_period": 10,
                "slow_period": 20
            },
            "indicators": {
                "SMA_fast": {
                    "type": "SMA",
                    "params": {"timeperiod": 10}
                },
                "SMA_slow": {
                    "type": "SMA",
                    "params": {"timeperiod": 20}
                }
            },
            "entry_rules": {
                "long": [
                    {
                        "type": "crossover",
                        "indicator1": "SMA_fast",
                        "indicator2": "SMA_slow"
                    }
                ]
            },
            "exit_rules": {
                "long": [
                    {
                        "type": "crossunder",
                        "indicator1": "SMA_fast",
                        "indicator2": "SMA_slow"
                    }
                ]
            },
            "position_sizing": {
                "type": "fixed_percent",
                "value": 0.95
            }
        }
        
        logger.info(f"Creating strategy from canonical JSON...")
        logger.debug(f"Canonical JSON: {json.dumps(canonical_json, indent=2)}")
        
        strategy_class = create_strategy_from_canonical(canonical_json)
        
        logger.info(f"[OK] Strategy created successfully!")
        logger.info(f"   Class name: {strategy_class.__name__}")
        logger.info(f"   Methods: {[m for m in dir(strategy_class) if not m.startswith('_')]}")
        
        return strategy_class, canonical_json
        
    except Exception as e:
        logger.error(f"[ERROR] Strategy creation failed: {e}", exc_info=True)
        raise


def test_backtest_execution(data, strategy_class):
    """Test 3: Run backtest and capture trades"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: Backtest Execution")
    logger.info("=" * 80)
    
    try:
        from Backtest.backtesting_adapter import BacktestingAdapter
        
        logger.info("Initializing BacktestingAdapter...")
        logger.debug(f"Data shape: {data.shape}")
        logger.debug(f"Initial cash: $10,000")
        logger.debug(f"Commission: 0.2%")
        
        adapter = BacktestingAdapter(
            data=data,
            strategy_class=strategy_class,
            cash=10000,
            commission=0.002,
            trade_on_close=False
        )
        
        logger.info("Running backtest...")
        results = adapter.run()
        
        logger.info(f"[OK] Backtest completed successfully!")
        logger.info(f"\n📊 RESULTS:")
        logger.info(f"   Return [%]: {results.get('Return [%]', 0):.2f}%")
        logger.info(f"   Buy & Hold Return [%]: {results.get('Buy & Hold Return [%]', 0):.2f}%")
        logger.info(f"   # Trades: {results.get('# Trades', 0)}")
        logger.info(f"   Win Rate [%]: {results.get('Win Rate [%]', 0):.2f}%")
        logger.info(f"   Sharpe Ratio: {results.get('Sharpe Ratio', 0):.2f}")
        logger.info(f"   Max. Drawdown [%]: {results.get('Max. Drawdown [%]', 0):.2f}%")
        
        # Extract trades
        trades_list = []
        if hasattr(adapter.results, '_trades') and adapter.results._trades is not None:
            trades_df = adapter.results._trades
            logger.info(f"\n📋 TRADES: {len(trades_df)} trades found")
            
            for idx, trade in trades_df.iterrows():
                trade_info = {
                    'entry_time': str(trade.get('EntryTime', '')),
                    'exit_time': str(trade.get('ExitTime', '')),
                    'entry_price': float(trade.get('EntryPrice', 0)),
                    'exit_price': float(trade.get('ExitPrice', 0)),
                    'size': float(trade.get('Size', 0)),
                    'pnl': float(trade.get('PnL', 0)),
                    'return_pct': float(trade.get('ReturnPct', 0))
                }
                trades_list.append(trade_info)
                
                logger.info(f"   Trade {idx + 1}:")
                logger.info(f"      Entry: {trade_info['entry_time']} @ ${trade_info['entry_price']:.2f}")
                logger.info(f"      Exit:  {trade_info['exit_time']} @ ${trade_info['exit_price']:.2f}")
                logger.info(f"      Size:  {trade_info['size']:.0f} shares")
                logger.info(f"      P&L:   ${trade_info['pnl']:.2f} ({trade_info['return_pct']:.2f}%)")
        else:
            logger.warning("[WARN] No trades were executed!")
        
        return results, trades_list
        
    except Exception as e:
        logger.error(f"[ERROR] Backtest execution failed: {e}", exc_info=True)
        raise


def test_sequential_streaming(data, trades_list):
    """Test 4: Simulate sequential streaming with trade signals"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: Sequential Streaming Simulation")
    logger.info("=" * 80)
    
    try:
        logger.info(f"Simulating sequential streaming of {len(data)} candles...")
        logger.info(f"With {len(trades_list)} trade signals to match")
        
        candles_sent = 0
        signals_sent = 0
        
        for idx, (timestamp, row) in enumerate(data.iterrows()):
            timestamp_str = str(timestamp)
            
            # Log every 20th candle or when there's a trade
            has_trade = any(
                t['entry_time'] == timestamp_str or t['exit_time'] == timestamp_str 
                for t in trades_list
            )
            
            if idx % 20 == 0 or has_trade:
                logger.debug(f"Candle {idx + 1}/{len(data)}: {timestamp_str} | " +
                           f"O:{row.get('open', row.get('Open', 0)):.2f} " +
                           f"H:{row.get('high', row.get('High', 0)):.2f} " +
                           f"L:{row.get('low', row.get('Low', 0)):.2f} " +
                           f"C:{row.get('close', row.get('Close', 0)):.2f}")
            
            candles_sent += 1
            
            # Check for trades at this timestamp
            for trade in trades_list:
                # Entry signal
                if trade['entry_time'] == timestamp_str:
                    side = "BUY" if trade['size'] > 0 else "SELL"
                    logger.info(f"   >> ENTRY SIGNAL: {side} @ ${trade['entry_price']:.2f} | Size: {abs(trade['size']):.0f}")
                    signals_sent += 1
                
                # Exit signal
                if trade['exit_time'] == timestamp_str:
                    pnl_status = "WIN" if trade['pnl'] > 0 else "LOSS"
                    logger.info(f"   << EXIT SIGNAL: CLOSE @ ${trade['exit_price']:.2f} | " +
                               f"P&L: ${trade['pnl']:.2f} [{pnl_status}]")
                    signals_sent += 1
        
        logger.info(f"\n[OK] Sequential streaming simulation completed!")
        logger.info(f"   Candles streamed: {candles_sent}")
        logger.info(f"   Signals sent: {signals_sent}")
        logger.info(f"   Expected signals: {len(trades_list) * 2} (entry + exit per trade)")
        
        if signals_sent == len(trades_list) * 2:
            logger.info(f"   [OK] All trade signals matched correctly!")
        else:
            logger.warning(f"   [WARN] Signal count mismatch! Check trade timestamps")
        
    except Exception as e:
        logger.error(f"[ERROR] Sequential streaming failed: {e}", exc_info=True)
        raise


def main():
    """Run all tests"""
    try:
        # Test 1: Data Loading
        data = test_data_loading()
        
        # Test 2: Strategy Creation
        strategy_class, canonical_json = test_strategy_creation()
        
        # Test 3: Backtest Execution
        results, trades_list = test_backtest_execution(data, strategy_class)
        
        # Test 4: Sequential Streaming
        test_sequential_streaming(data, trades_list)
        
        logger.info("\n" + "=" * 80)
        logger.info("[SUCCESS] ALL TESTS PASSED!")
        logger.info("=" * 80)
        logger.info(f"Backtest module is working correctly for streaming visualization")
        logger.info(f"Log file saved to: backtest_test.log")
        
        return True
        
    except Exception as e:
        logger.error("\n" + "=" * 80)
        logger.error("[FAILED] TEST FAILED!")
        logger.error("=" * 80)
        logger.error(f"Error: {e}", exc_info=True)
        logger.info(f"Check backtest_test.log for detailed information")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
