"""
Strategy: Algotdrjkhhmjfgxc
Description: Basic trend-following strategy using EMA crossover with RSI filter
Generated: 2025-01-22
Location: codes/ directory
"""

# Add parent directory to path for imports
import sys
from pathlib import Path
# IMPORTANT: Go up 3 levels (codes -> Backtest -> monolithic_agent) to add monolithic_agent to path
# This allows importing Backtest as a package
parent_dir = Path(__file__).parent.parent.parent
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
import os


class AlgotdrjkhhmjfgxcStrategy:
    """
    Trend-following strategy using dual EMA crossover with RSI filter.
    
    Entry Conditions:
    - Fast EMA (12) crosses above Slow EMA (26)
    - RSI is below 70 (not overbought)
    
    Exit Conditions:
    - Fast EMA crosses below Slow EMA
    - OR RSI exceeds 80 (overbought exit)
    """
    
    def __init__(self, broker: SimBroker, symbol: str = "AAPL", strategy_id: str = "algotdrjkhhmjfgxc_001", **params):
        self.broker = broker
        self.symbol = symbol
        self.strategy_id = strategy_id
        
        # Initialize loggers for pattern and signal tracking
        self.pattern_logger = PatternLogger(strategy_id)
        self.signal_logger = SignalLogger(strategy_id)
        
        # Position tracking
        self.in_position = False
        self.position_size = 0
        self.entry_price = None
        
        # Strategy parameters (can be overridden via params)
        self.ema_fast_period = params.get('ema_fast_period', 12)
        self.ema_slow_period = params.get('ema_slow_period', 26)
        self.rsi_period = params.get('rsi_period', 14)
        self.rsi_entry_threshold = params.get('rsi_entry_threshold', 70)
        self.rsi_exit_threshold = params.get('rsi_exit_threshold', 80)
        self.position_pct = params.get('position_pct', 0.95)  # Use 95% of cash
        
        # Tracking for crossover detection
        self.prev_ema_fast = None
        self.prev_ema_slow = None
    
    def on_bar(self, timestamp: datetime, data: dict):
        """
        Process each bar of market data sequentially.
        EVERY row is logged with pattern detection results.
        """
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
        
        # Extract indicators (lowercase keys in streaming mode)
        ema_fast = symbol_data.get(f'ema_{self.ema_fast_period}')
        ema_slow = symbol_data.get(f'ema_{self.ema_slow_period}')
        rsi = symbol_data.get(f'rsi_{self.rsi_period}')
        
        # Build indicator dict for logging
        indicators = {
            f'ema_{self.ema_fast_period}': ema_fast,
            f'ema_{self.ema_slow_period}': ema_slow,
            f'rsi_{self.rsi_period}': rsi
        }
        
        # Check for missing data
        if ema_fast is None or ema_slow is None or rsi is None:
            return
        
        # Check entry pattern (logged for EVERY row)
        if not self.in_position:
            self._check_entry_pattern(timestamp, market_data, indicators, ema_fast, ema_slow, rsi)
        
        # Check exit pattern if in position (logged for EVERY row)
        if self.in_position:
            self._check_exit_pattern(timestamp, market_data, indicators, ema_fast, ema_slow, rsi)
        
        # Update previous values for crossover detection
        self.prev_ema_fast = ema_fast
        self.prev_ema_slow = ema_slow
    
    def _check_entry_pattern(self, timestamp, market_data, indicators, ema_fast, ema_slow, rsi):
        """Check and log entry pattern"""
        # Define entry condition
        pattern_condition = (
            f"EMA({self.ema_fast_period}) > EMA({self.ema_slow_period}) AND "
            f"RSI({self.rsi_period}) < {self.rsi_entry_threshold}"
        )
        
        # Check if crossover occurred (bullish crossover)
        crossover_occurred = False
        if self.prev_ema_fast is not None and self.prev_ema_slow is not None:
            # Bullish crossover: fast was below slow, now above
            crossover_occurred = (self.prev_ema_fast <= self.prev_ema_slow and 
                                ema_fast > ema_slow)
        
        # Pattern found if crossover AND RSI filter
        pattern_found = crossover_occurred and rsi < self.rsi_entry_threshold
        
        # Log pattern check (EVERY row)
        self.pattern_logger.log_pattern(
            timestamp=timestamp,
            symbol=self.symbol,
            step_id="entry_check",
            step_title="Entry Pattern Check",
            pattern_condition=pattern_condition,
            pattern_found=pattern_found,
            market_data=market_data,
            indicator_values=indicators
        )
        
        # Generate signal if pattern found
        if pattern_found:
            self._generate_entry_signal(timestamp, market_data, indicators, ema_fast, ema_slow, rsi)
    
    def _check_exit_pattern(self, timestamp, market_data, indicators, ema_fast, ema_slow, rsi):
        """Check and log exit pattern"""
        # Define exit condition
        pattern_condition = (
            f"EMA({self.ema_fast_period}) < EMA({self.ema_slow_period}) OR "
            f"RSI({self.rsi_period}) > {self.rsi_exit_threshold}"
        )
        
        # Check if bearish crossover occurred
        crossover_occurred = False
        if self.prev_ema_fast is not None and self.prev_ema_slow is not None:
            # Bearish crossover: fast was above slow, now below
            crossover_occurred = (self.prev_ema_fast >= self.prev_ema_slow and 
                                ema_fast < ema_slow)
        
        # Pattern found if crossover OR RSI exceeds threshold
        pattern_found = crossover_occurred or rsi > self.rsi_exit_threshold
        
        # Log pattern check (EVERY row)
        self.pattern_logger.log_pattern(
            timestamp=timestamp,
            symbol=self.symbol,
            step_id="exit_check",
            step_title="Exit Pattern Check",
            pattern_condition=pattern_condition,
            pattern_found=pattern_found,
            market_data=market_data,
            indicator_values=indicators
        )
        
        # Generate signal if pattern found
        if pattern_found:
            reason = "Bearish crossover" if crossover_occurred else f"RSI overbought ({rsi:.2f})"
            self._generate_exit_signal(timestamp, market_data, indicators, reason)
    
    def _generate_entry_signal(self, timestamp, market_data, indicators, ema_fast, ema_slow, rsi):
        """Generate entry trade - CORRECT VERSION"""
        # Position sizing: use get_account_snapshot() for adaptive sizing
        snap = self.broker.get_account_snapshot()
        available_cash = snap['cash']
        current_price = market_data['close']
        size = int(available_cash * self.position_pct / current_price)
        
        if size < 1:
            return  # Insufficient cash
        
        reason = (
            f"Bullish EMA crossover: EMA({self.ema_fast_period})={ema_fast:.2f} > "
            f"EMA({self.ema_slow_period})={ema_slow:.2f}, RSI={rsi:.2f}"
        )
        
        # CRITICAL: Use create_signal() + submit_signal() (REQUIRED)
        signal = create_signal(
            signal_id=f"entry_{timestamp.strftime('%Y%m%d%H%M%S')}",
            timestamp=timestamp,
            symbol=self.symbol,
            side=OrderSide.BUY,
            action=OrderAction.ENTRY,
            order_type=OrderType.MARKET,
            size=size,
            price=current_price,
            reason=reason
        )
        
        order_id = self.broker.submit_signal(signal.to_dict())
        
        if order_id:
            # Log the signal
            self.signal_logger.log_signal(
                timestamp=timestamp,
                symbol=self.symbol,
                side=OrderSide.BUY,
                action=OrderAction.ENTRY,
                order_type=OrderType.MARKET,
                size=size,
                price=current_price,
                reason=reason,
                market_data=market_data,
                indicator_values=indicators
            )
            print(f"[ENTRY] BUY {size} shares of {self.symbol} at ${current_price:.2f}")
            
            # Update state
            self.in_position = True
            self.position_size = size
            self.entry_price = current_price
    
    def _generate_exit_signal(self, timestamp, market_data, indicators, reason):
        """Generate exit trade - CORRECT VERSION"""
        size = self.position_size
        current_price = market_data['close']
        
        # CRITICAL: Use create_signal() + submit_signal() (REQUIRED)
        signal = create_signal(
            signal_id=f"exit_{timestamp.strftime('%Y%m%d%H%M%S')}",
            timestamp=timestamp,
            symbol=self.symbol,
            side=OrderSide.SELL,
            action=OrderAction.EXIT,
            order_type=OrderType.MARKET,
            size=size,
            price=current_price,
            reason=reason
        )
        
        order_id = self.broker.submit_signal(signal.to_dict())
        
        if order_id:
            # Calculate P&L
            pnl = (current_price - self.entry_price) * size if self.entry_price else 0
            pnl_pct = ((current_price / self.entry_price) - 1) * 100 if self.entry_price else 0
            
            # Log the signal
            self.signal_logger.log_signal(
                timestamp=timestamp,
                symbol=self.symbol,
                side=OrderSide.SELL,
                action=OrderAction.EXIT,
                order_type=OrderType.MARKET,
                size=size,
                price=current_price,
                reason=reason,
                market_data=market_data,
                indicator_values=indicators
            )
            print(f"[EXIT] SELL {size} shares of {self.symbol} at ${current_price:.2f} "
                  f"(P&L: ${pnl:.2f}, {pnl_pct:+.2f}%)")
            
            # Update state
            self.in_position = False
            self.position_size = 0
            self.entry_price = None
    
    def finalize(self):
        """Close loggers and export summaries"""
        self.pattern_logger.close()
        self.signal_logger.close()


def run_backtest():
    """Runs the backtest in STREAMING mode with multiple symbols for better pattern detection"""
    
    # Test on multiple symbols to ensure strategy finds trading opportunities
    test_symbols = os.environ.get('BACKTEST_SYMBOLS', 'AAPL,TSLA,MSFT').split(',')
    all_metrics = []
    total_trades = 0
    
    for test_symbol in test_symbols:
        test_symbol = test_symbol.strip()
        print("\n" + "=" * 70)
        print(f"TESTING SYMBOL: {test_symbol}")
        print("=" * 70)
        
        # 1. Configure backtest
        config = BacktestConfig(
            start_cash=100000,
            fee_flat=1.0,
            fee_pct=0.001,
            slippage_pct=0.0005
        )
        
        # 2. Initialize broker for this symbol
        broker = SimBroker(config)
        
        # 3. Initialize strategy with symbol
        strategy = AlgotdrjkhhmjfgxcStrategy(
            broker, 
            symbol=test_symbol, 
            strategy_id=f"algotdrjkhhmjfgxc_{test_symbol}"
        )
        print(f"[OK] Strategy initialized: {strategy.__class__.__name__} for {test_symbol}")
        
        # 4. Define indicators using multi-period format
        indicators = {
            'EMA': {'periods': [12, 26]},  # Creates EMA_12 and EMA_26
            'RSI': {'periods': [14]}       # Creates RSI_14
        }
        
        # 5. Load data in STREAMING mode
        print(f"[LOADING] Loading data in STREAMING mode (sequential)...")
        try:
            data_stream = load_market_data(
                ticker=test_symbol,
                indicators=indicators,
                period='max',   # Use all available warehouse data
                interval='1d',
                stream=True
            )
        except FileNotFoundError:
            print(f"[WARNING] Data file not found for {test_symbol}, skipping...")
            continue
        
        print(f"[OK] Data stream initialized for {test_symbol}")
        print(f"[OK] Processing bars sequentially...")
        
        # 6. Process each bar sequentially
        bar_count = 0
        last_progress = -1
        
        for timestamp, market_data, progress_pct in data_stream:
            bar_count += 1
            
            # Strategy processes this bar
            strategy.on_bar(timestamp, market_data)
            
            # Broker executes any signals
            broker.step_to(timestamp, market_data)
            
            # Show progress every 10%
            current_progress = int(progress_pct / 10) * 10
            if current_progress != last_progress and current_progress > 0:
                print(f"  Progress: {current_progress}% ({bar_count} bars)")
                last_progress = current_progress
        
        print(f"[OK] Processed {bar_count} bars sequentially for {test_symbol}")
        
        # 7. Finalize strategy (close loggers)
        strategy.finalize()
        
        # 8. Get metrics for this symbol
        metrics = broker.compute_metrics()
        metrics['symbol'] = test_symbol
        all_metrics.append(metrics)
        total_trades += metrics.get('total_trades', 0)
        
        # 9. Print symbol results
        print("\n" + "=" * 70)
        print(f"RESULTS FOR {test_symbol}")
        print("=" * 70)
        print(f"Final Equity: ${metrics['final_equity']:,.2f}")
        print(f"Total Trades: {metrics['total_trades']}")
        print(f"Return: {metrics['total_return_pct']:.2f}%")
        if metrics['total_trades'] > 0:
            print(f"Win Rate: {metrics['win_rate'] * 100:.1f}%")
            print(f"Profit Factor: {metrics['profit_factor']:.2f}")
        print("=" * 70)
    
    # 10. Print aggregate results
    print("\n\n" + "=" * 70)
    print("AGGREGATE BACKTEST RESULTS (ALL SYMBOLS)")
    print("=" * 70)
    print(f"Symbols Tested: {', '.join([m['symbol'] for m in all_metrics])}")
    print(f"Total Trades Across All Symbols: {total_trades}")
    
    if total_trades == 0:
        print("\n[WARNING] NO TRADES EXECUTED")
        print("Strategy did not find trading opportunities in any symbol.")
        print("Consider adjusting strategy parameters or testing different symbols.")
    else:
        print("\n[PASS] Strategy generated trades successfully")
    
    for metrics in all_metrics:
        print(f"\n{metrics['symbol']}:")
        print(f"  Net Profit: ${metrics['net_profit']:,.2f} ({metrics['total_return_pct']:.2f}%)")
        print(f"  Trades: {metrics['total_trades']}")
        if metrics['total_trades'] > 0:
            print(f"  Win Rate: {metrics['win_rate'] * 100:.1f}%")
            print(f"  Profit Factor: {metrics['profit_factor']:.2f}")
            print(f"  Max Drawdown: {metrics['max_drawdown_pct'] * 100:.2f}%")
    
    print("=" * 70)
    
    # Return best performing symbol's metrics
    if all_metrics:
        return max(all_metrics, key=lambda x: x.get('total_return_pct', -999))
    return None


if __name__ == "__main__":
    metrics = run_backtest()