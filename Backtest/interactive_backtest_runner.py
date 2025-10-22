"""
Interactive Backtest Runner
===========================

This module provides an interactive command-line interface for running backtests
with user-specified parameters including symbol selection and date range.

Features:
- Interactive symbol selection
- Custom date range input (From: {date}, To: {date})
- Data fetching from Data module using fetch_data_by_date_range
- Automatic indicator loading
- Full backtest execution with results

Version: 1.0.0
Last Updated: 2025-10-22
"""

import pandas as pd
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import logging

# Add parent directory to path for imports
PARENT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PARENT_DIR))

from Data.data_fetcher import DataFetcher
from Backtest.config import get_realistic_config, BacktestConfig
from Backtest.sim_broker import SimBroker

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_date(date_string: str) -> Tuple[bool, Optional[datetime]]:
    """
    Validate date string format.
    
    Args:
        date_string: Date in YYYY-MM-DD format
        
    Returns:
        Tuple of (is_valid, datetime_object or None)
    """
    try:
        date_obj = datetime.strptime(date_string, "%Y-%m-%d")
        return True, date_obj
    except ValueError:
        return False, None


def get_user_symbol() -> str:
    """
    Prompt user to enter stock symbol.
    
    Returns:
        Stock symbol in uppercase
    """
    print("\n" + "=" * 70)
    print("STOCK SYMBOL SELECTION")
    print("=" * 70)
    
    while True:
        symbol = input("\nEnter stock symbol (e.g., AAPL, MSFT, GOOGL): ").strip().upper()
        
        if not symbol:
            print("❌ Symbol cannot be empty. Please try again.")
            continue
            
        if not symbol.replace("^", "").replace(".", "").isalnum():
            print("❌ Invalid symbol format. Please use alphanumeric characters only.")
            continue
            
        print(f"✓ Selected symbol: {symbol}")
        return symbol


def get_user_date_range() -> Tuple[str, str]:
    """
    Prompt user to enter backtest date range.
    
    Returns:
        Tuple of (start_date, end_date) in YYYY-MM-DD format
    """
    print("\n" + "=" * 70)
    print("DATE RANGE SELECTION")
    print("=" * 70)
    print("Please enter dates in YYYY-MM-DD format (e.g., 2024-01-01)")
    
    # Get start date
    while True:
        start_input = input("\nFrom (start date): ").strip()
        
        if not start_input:
            print("❌ Start date cannot be empty.")
            continue
            
        is_valid, start_date = validate_date(start_input)
        if not is_valid:
            print("❌ Invalid date format. Please use YYYY-MM-DD (e.g., 2024-01-01)")
            continue
            
        if start_date > datetime.now():
            print("❌ Start date cannot be in the future.")
            continue
            
        print(f"✓ Start date: {start_input}")
        break
    
    # Get end date
    while True:
        end_input = input("To (end date): ").strip()
        
        if not end_input:
            print("❌ End date cannot be empty.")
            continue
            
        is_valid, end_date = validate_date(end_input)
        if not is_valid:
            print("❌ Invalid date format. Please use YYYY-MM-DD (e.g., 2025-01-01)")
            continue
            
        if end_date > datetime.now():
            print("❌ End date cannot be in the future.")
            continue
            
        if end_date <= start_date:
            print(f"❌ End date must be after start date ({start_input}).")
            continue
            
        print(f"✓ End date: {end_input}")
        break
    
    # Calculate duration
    duration = (end_date - start_date).days
    print(f"\n📅 Backtest period: {duration} days ({start_input} to {end_input})")
    
    return start_input, end_input


def get_user_interval() -> str:
    """
    Prompt user to select data interval.
    
    Returns:
        Interval string (e.g., '1d', '1h', '30m')
    """
    print("\n" + "=" * 70)
    print("DATA INTERVAL SELECTION")
    print("=" * 70)
    print("Available intervals:")
    print("  1. 1d  - Daily")
    print("  2. 1h  - Hourly")
    print("  3. 30m - 30 minutes")
    print("  4. 15m - 15 minutes")
    print("  5. 5m  - 5 minutes")
    
    intervals = {
        '1': '1d',
        '2': '1h',
        '3': '30m',
        '4': '15m',
        '5': '5m'
    }
    
    while True:
        choice = input("\nSelect interval (1-5) or enter custom (e.g., 2m, 1wk): ").strip()
        
        if choice in intervals:
            interval = intervals[choice]
            print(f"✓ Selected interval: {interval}")
            return interval
        elif choice and any(choice.endswith(suffix) for suffix in ['m', 'h', 'd', 'wk', 'mo']):
            print(f"✓ Custom interval: {choice}")
            return choice
        else:
            print("❌ Invalid selection. Please choose 1-5 or enter a valid interval.")


def fetch_data_for_backtest(
    symbol: str,
    start_date: str,
    end_date: str,
    interval: str = '1d'
) -> pd.DataFrame:
    """
    Fetch market data using DataFetcher with date range.
    
    Args:
        symbol: Stock ticker symbol
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        interval: Data interval (default: '1d')
        
    Returns:
        DataFrame with OHLCV data
    """
    print("\n" + "=" * 70)
    print("FETCHING MARKET DATA")
    print("=" * 70)
    print(f"Symbol: {symbol}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Interval: {interval}")
    print("\nFetching data from Yahoo Finance...")
    
    fetcher = DataFetcher()
    df = fetcher.fetch_data_by_date_range(
        ticker=symbol,
        start_date=start_date,
        end_date=end_date,
        interval=interval
    )
    
    if df.empty:
        raise ValueError(f"No data returned for {symbol} in the specified date range")
    
    # Flatten MultiIndex columns if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # Ensure datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    
    # Sort by datetime
    df = df.sort_index()
    
    # Convert to numeric
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Drop rows with NaN values
    initial_rows = len(df)
    df = df.dropna()
    dropped_rows = initial_rows - len(df)
    
    print(f"✓ Data fetched successfully!")
    print(f"  Total bars: {len(df)}")
    if dropped_rows > 0:
        print(f"  Dropped {dropped_rows} rows with missing data")
    print(f"  Date range: {df.index[0]} to {df.index[-1]}")
    print(f"  Columns: {list(df.columns)}")
    
    return df


def get_backtest_config() -> BacktestConfig:
    """
    Get backtest configuration from user or use defaults.
    
    Returns:
        BacktestConfig object
    """
    print("\n" + "=" * 70)
    print("BACKTEST CONFIGURATION")
    print("=" * 70)
    
    # Ask if user wants to customize config
    customize = input("\nUse default configuration? (Y/n): ").strip().lower()
    
    if customize == 'n' or customize == 'no':
        # Get custom parameters
        config = get_realistic_config()
        
        try:
            cash_input = input(f"\nStarting cash (default ${config.start_cash:,.0f}): ").strip()
            if cash_input:
                config.start_cash = float(cash_input)
            
            print("\nFee structure:")
            fee_pct_input = input(f"  Fee percentage (default {config.fee_pct*100:.3f}%): ").strip()
            if fee_pct_input:
                config.fee_pct = float(fee_pct_input) / 100
                
            fee_flat_input = input(f"  Flat fee per order (default ${config.fee_flat}): ").strip()
            if fee_flat_input:
                config.fee_flat = float(fee_flat_input)
            
            slippage_input = input(f"\nSlippage percentage (default {config.slippage_pct*100:.4f}%): ").strip()
            if slippage_input:
                config.slippage_pct = float(slippage_input) / 100
                
        except ValueError as e:
            print(f"⚠️  Invalid input: {e}. Using defaults.")
    else:
        config = get_realistic_config()
    
    # Display configuration
    print("\n✓ Configuration set:")
    print(f"  Starting Cash: ${config.start_cash:,.2f}")
    print(f"  Fee: ${config.fee_flat} + {config.fee_pct*100:.3f}%")
    print(f"  Slippage: {config.slippage_pct*100:.4f}%")
    
    return config


def convert_to_broker_format(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Convert DataFrame to SimBroker expected format.
    
    Args:
        df: DataFrame with OHLCV data
        symbol: Stock symbol
        
    Returns:
        DataFrame in broker format with required columns
    """
    # Create a copy to avoid modifying original
    broker_df = pd.DataFrame()
    broker_df['timestamp'] = df.index
    broker_df['symbol'] = symbol
    broker_df['open'] = df['Open'].values
    broker_df['high'] = df['High'].values
    broker_df['low'] = df['Low'].values
    broker_df['close'] = df['Close'].values
    broker_df['volume'] = df['Volume'].values
    
    return broker_df


def run_backtest_simulation(
    broker: SimBroker,
    df: pd.DataFrame,
    symbol: str,
    strategy_class,
    strategy_params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Run the backtest simulation.
    
    Args:
        broker: SimBroker instance
        df: Market data DataFrame
        symbol: Stock symbol
        strategy_class: Strategy class to instantiate
        strategy_params: Parameters for strategy initialization
        
    Returns:
        Dictionary of metrics
    """
    print("\n" + "=" * 70)
    print("RUNNING BACKTEST SIMULATION")
    print("=" * 70)
    
    # Initialize strategy
    strategy = strategy_class(broker=broker, **strategy_params)
    print(f"✓ Strategy initialized: {strategy_class.__name__}")
    
    # Convert data to broker format
    broker_df = convert_to_broker_format(df, symbol)
    
    # Run simulation
    print(f"\nSimulating {len(broker_df)} bars...")
    progress_interval = max(1, len(broker_df) // 20)  # Update every 5%
    
    for idx, row in broker_df.iterrows():
        timestamp = row['timestamp']
        
        market_data = {
            row['symbol']: {
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row['volume']
            }
        }
        
        # Strategy analyzes and may emit signals
        strategy.on_bar(timestamp, market_data)
        
        # Broker processes signals and updates state
        broker.step_to(timestamp, market_data)
        
        # Progress update
        if idx % progress_interval == 0:
            progress = (idx / len(broker_df)) * 100
            print(f"  Progress: {progress:.0f}%", end='\r')
    
    print("  Progress: 100% ✓")
    print("\n✓ Simulation complete!")
    
    # Compute metrics
    print("\nComputing performance metrics...")
    metrics = broker.compute_metrics()
    
    return metrics


def display_results(metrics: Dict[str, Any], broker: SimBroker):
    """
    Display backtest results in a formatted manner.
    
    Args:
        metrics: Dictionary of computed metrics
        broker: SimBroker instance for additional stats
    """
    print("\n" + "=" * 70)
    print("BACKTEST RESULTS")
    print("=" * 70)
    print(f"Period: {metrics['start_date']} to {metrics['end_date']}")
    print(f"Duration: {metrics['duration_days']} days")
    print()
    print(f"Starting Capital: ${metrics['start_cash']:,.2f}")
    print(f"Final Equity: ${metrics['final_equity']:,.2f}")
    print(f"Net Profit: ${metrics['net_profit']:,.2f} ({metrics['total_return_pct']:.2f}%)")
    print()
    print(f"Total Trades: {metrics['total_trades']}")
    print(f"Winning Trades: {metrics['winning_trades']}")
    print(f"Losing Trades: {metrics['losing_trades']}")
    print(f"Win Rate: {metrics['win_rate']*100:.1f}%")
    print()
    print(f"Profit Factor: {metrics['profit_factor']:.2f}")
    print(f"Average Trade: ${metrics['average_trade']:.2f}")
    print(f"Average Win: ${metrics['average_win']:.2f}")
    print(f"Average Loss: ${metrics['average_loss']:.2f}")
    print()
    print(f"Max Drawdown: ${metrics['max_drawdown_abs']:,.2f} ({metrics['max_drawdown_pct']*100:.2f}%)")
    print(f"Recovery Factor: {metrics['recovery_factor']:.2f}")
    print()
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"Sortino Ratio: {metrics['sortino_ratio']:.2f}")
    print(f"Calmar Ratio: {metrics['calmar_ratio']:.2f}")
    print()
    print(f"Max Consecutive Wins: {metrics['max_consecutive_wins']}")
    print(f"Max Consecutive Losses: {metrics['max_consecutive_losses']}")
    print()
    print(f"Total Commission: ${metrics['total_commission']:,.2f}")
    print(f"Total Slippage: ${metrics['total_slippage']:,.2f}")
    print("=" * 70)
    
    # Component statistics
    stats = broker.get_statistics()
    print("\nComponent Statistics:")
    print(f"  Orders Created: {stats['orders']['orders_created']}")
    print(f"  Orders Filled: {stats['orders']['orders_filled']}")
    print(f"  Fills Executed: {stats['execution']['fills_executed']}")
    print(f"  Partial Fills: {stats['execution']['partial_fills']}")


def save_results(broker: SimBroker, metrics: Dict[str, Any], symbol: str):
    """
    Save backtest results to files.
    
    Args:
        broker: SimBroker instance
        metrics: Metrics dictionary
        symbol: Stock symbol
    """
    print("\n" + "=" * 70)
    print("SAVING RESULTS")
    print("=" * 70)
    
    import os
    import json
    
    # Create results directory
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    
    # Generate timestamp for unique filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save trades
    trades_file = results_dir / f"{symbol}_trades_{timestamp}.csv"
    broker.export_trades(str(trades_file))
    print(f"✓ Trades saved to: {trades_file}")
    
    # Save metrics
    metrics_file = results_dir / f"{symbol}_metrics_{timestamp}.json"
    with open(metrics_file, "w") as f:
        json.dump(metrics, f, indent=2, default=str)
    print(f"✓ Metrics saved to: {metrics_file}")
    
    print("\n✓ All results saved successfully!")


def main():
    """
    Main entry point for interactive backtest runner.
    """
    print("\n" + "=" * 70)
    print("INTERACTIVE BACKTEST RUNNER")
    print("=" * 70)
    print("Welcome! This tool will guide you through setting up and running")
    print("a backtest with your custom parameters.")
    
    try:
        # Step 1: Get symbol
        symbol = get_user_symbol()
        
        # Step 2: Get date range
        start_date, end_date = get_user_date_range()
        
        # Step 3: Get interval
        interval = get_user_interval()
        
        # Step 4: Fetch data
        df = fetch_data_for_backtest(symbol, start_date, end_date, interval)
        
        # Step 5: Get configuration
        config = get_backtest_config()
        
        # Step 6: Initialize broker
        print("\n" + "=" * 70)
        print("INITIALIZING BROKER")
        print("=" * 70)
        broker = SimBroker(config)
        print(f"✓ SimBroker initialized (API v{broker.API_VERSION})")
        
        # Step 7: Import and setup strategy
        # For now, using a simple example strategy
        # Users can modify this to use their own strategies
        print("\n⚠️  Note: Using example Simple MA Crossover strategy")
        print("   Modify this script to use your custom strategy")
        
        from Backtest.example_strategy import SimpleMAStrategy
        
        strategy_params = {
            'fast_period': 10,
            'slow_period': 30,
            'size': 100
        }
        
        # Ask if user wants to customize strategy parameters
        customize_strategy = input("\nCustomize strategy parameters? (y/N): ").strip().lower()
        if customize_strategy == 'y' or customize_strategy == 'yes':
            try:
                fast = input(f"Fast MA period (default {strategy_params['fast_period']}): ").strip()
                if fast:
                    strategy_params['fast_period'] = int(fast)
                    
                slow = input(f"Slow MA period (default {strategy_params['slow_period']}): ").strip()
                if slow:
                    strategy_params['slow_period'] = int(slow)
                    
                size = input(f"Position size (default {strategy_params['size']}): ").strip()
                if size:
                    strategy_params['size'] = int(size)
            except ValueError as e:
                print(f"⚠️  Invalid input: {e}. Using defaults.")
        
        print(f"\n✓ Strategy parameters:")
        print(f"  Fast MA: {strategy_params['fast_period']}")
        print(f"  Slow MA: {strategy_params['slow_period']}")
        print(f"  Position Size: {strategy_params['size']}")
        
        # Step 8: Run backtest
        metrics = run_backtest_simulation(
            broker=broker,
            df=df,
            symbol=symbol,
            strategy_class=SimpleMAStrategy,
            strategy_params=strategy_params
        )
        
        # Step 9: Display results
        display_results(metrics, broker)
        
        # Step 10: Save results
        save_option = input("\nSave results to files? (Y/n): ").strip().lower()
        if save_option != 'n' and save_option != 'no':
            save_results(broker, metrics, symbol)
        
        print("\n" + "=" * 70)
        print("BACKTEST COMPLETE")
        print("=" * 70)
        print("Thank you for using the Interactive Backtest Runner!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Backtest cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Backtest failed: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
