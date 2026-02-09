#!/usr/bin/env python3
"""
AAPL Momentum Strategy - Example Usage
This script demonstrates how to use the AAPL momentum trading strategy
"""

import sys
import os

# Add the strategy modules to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import AAPLMomentumStrategy
from config import *

def run_quick_backtest():
    """Run a quick backtest example"""
    print("=" * 60)
    print("AAPL MOMENTUM STRATEGY - QUICK BACKTEST EXAMPLE")
    print("=" * 60)
    
    # Initialize strategy in backtest mode
    strategy = AAPLMomentumStrategy(mode='backtest')
    
    print("Running backtest...")
    try:
        # Run backtest
        results = strategy.run_backtest()
        
        # Print key results
        print("\nKEY RESULTS:")
        print(f"Total Return: {results.get('total_return_pct', 0):.2f}%")
        print(f"Win Rate: {results.get('win_rate_pct', 0):.1f}%")
        print(f"Total Trades: {results.get('total_trades', 0)}")
        print(f"Profit Factor: {results.get('profit_factor', 0):.2f}")
        print(f"Max Drawdown: {results.get('max_drawdown_pct', 0):.2f}%")
        print(f"Sharpe Ratio: {results.get('sharpe_ratio', 0):.3f}")
        
        return results
        
    except Exception as e:
        print(f"Backtest failed: {e}")
        return None

def setup_demo_trading():
    """Setup demo trading example"""
    print("\n" + "=" * 60)
    print("DEMO TRADING SETUP EXAMPLE")
    print("=" * 60)
    
    print("To run demo trading:")
    print("1. Install MetaTrader 5 terminal")
    print("2. Open a demo account with your broker")
    print("3. Update config.py with your account details:")
    print("   - MT5_CONFIG['server'] = 'YourBroker-Demo'")
    print("   - MT5_CONFIG['login'] = YOUR_ACCOUNT_NUMBER")
    print("   - MT5_CONFIG['password'] = 'YOUR_PASSWORD'")
    print("4. Run: python main.py --mode demo")
    
    print("\nIMPORTANT: Always test with demo account before live trading!")

def show_configuration_options():
    """Show configuration options"""
    print("\n" + "=" * 60)
    print("CONFIGURATION OPTIONS")
    print("=" * 60)
    
    print("Strategy Parameters:")
    print(f"  Symbol: {STRATEGY_CONFIG['symbol']}")
    print(f"  Timeframe: {STRATEGY_CONFIG['timeframe']}")
    print(f"  RSI Period: {STRATEGY_CONFIG['rsi_period']}")
    print(f"  SMA Period: {STRATEGY_CONFIG['sma_period']}")
    print(f"  RSI Long Threshold: {STRATEGY_CONFIG['rsi_long_threshold']}")
    print(f"  RSI Short Threshold: {STRATEGY_CONFIG['rsi_short_threshold']}")
    
    print("\nRisk Management:")
    print(f"  Risk per Trade: {RISK_CONFIG['risk_per_trade']*100:.1f}%")
    print(f"  Max Positions: {RISK_CONFIG['max_positions']}")
    print(f"  Stop Loss: {RISK_CONFIG['stop_loss_pips']} pips")
    print(f"  Take Profit Ratio: {RISK_CONFIG['take_profit_ratio']}:1")
    print(f"  Max Spread: {RISK_CONFIG['max_spread']} pips")
    
    print("\nBacktest Settings:")
    print(f"  Start Date: {BACKTEST_CONFIG['start_date']}")
    print(f"  End Date: {BACKTEST_CONFIG['end_date']}")
    print(f"  Initial Balance: ${BACKTEST_CONFIG['initial_balance']:,}")
    print(f"  Commission: {BACKTEST_CONFIG['commission']*100:.3f}%")

def main():
    """Main example function"""
    print("AAPL Momentum Trading Strategy - Example Usage")
    
    # Show configuration
    show_configuration_options()
    
    # Run backtest example
    results = run_quick_backtest()
    
    # Show demo setup
    setup_demo_trading()
    
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("1. Review and adjust configuration in config.py")
    print("2. Run full backtests with different parameters")
    print("3. Test on demo account before live trading")
    print("4. Monitor performance and adjust strategy as needed")
    
    print("\nFiles generated:")
    print("- aapl_momentum.log (trading log)")
    print("- backtest_results.png (performance chart)")

if __name__ == "__main__":
    main()