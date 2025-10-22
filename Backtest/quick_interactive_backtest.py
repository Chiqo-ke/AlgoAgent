"""
Quick Interactive Backtest
==========================

Simplified interactive backtest runner with minimal user input.
Perfect for quick backtests with default settings.

Usage:
    python quick_interactive_backtest.py

Version: 1.0.0
"""

import sys
from pathlib import Path

# Add parent directory to path
PARENT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PARENT_DIR))

from Backtest.interactive_backtest_runner import (
    get_user_symbol,
    get_user_date_range,
    fetch_data_for_backtest,
    get_realistic_config,
    run_backtest_simulation,
    display_results,
    save_results
)
from Backtest.sim_broker import SimBroker
from Backtest.example_strategy import SimpleMAStrategy


def main():
    """Quick backtest with minimal configuration."""
    print("\n" + "=" * 70)
    print("QUICK INTERACTIVE BACKTEST")
    print("=" * 70)
    print("Streamlined backtest setup with default configurations\n")
    
    try:
        # Get basic inputs
        symbol = get_user_symbol()
        start_date, end_date = get_user_date_range()
        
        # Use daily interval by default
        interval = '1d'
        print(f"\n✓ Using interval: {interval} (daily)")
        
        # Fetch data
        df = fetch_data_for_backtest(symbol, start_date, end_date, interval)
        
        # Use default config
        config = get_realistic_config()
        config.start_cash = 100000
        print("\n✓ Using default configuration:")
        print(f"  Starting Cash: ${config.start_cash:,.2f}")
        print(f"  Fee: ${config.fee_flat} + {config.fee_pct*100:.3f}%")
        
        # Initialize broker
        broker = SimBroker(config)
        print(f"\n✓ SimBroker initialized")
        
        # Use default strategy
        strategy_params = {
            'fast_period': 10,
            'slow_period': 30,
            'size': 100
        }
        print(f"\n✓ Using Simple MA Crossover Strategy")
        print(f"  Fast MA: {strategy_params['fast_period']}")
        print(f"  Slow MA: {strategy_params['slow_period']}")
        
        # Run backtest
        metrics = run_backtest_simulation(
            broker=broker,
            df=df,
            symbol=symbol,
            strategy_class=SimpleMAStrategy,
            strategy_params=strategy_params
        )
        
        # Display results
        display_results(metrics, broker)
        
        # Auto-save results
        save_results(broker, metrics, symbol)
        
        print("\n✓ Quick backtest complete!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Backtest cancelled.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
