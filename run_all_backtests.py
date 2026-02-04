"""
Master script to run all 10 trading strategies and generate summary report
"""

import sys
import importlib.util
from pathlib import Path

# Strategy files
strategies = [
    '01_rsi_momentum.py',
    '02_macd_crossover.py',
    '03_bollinger_bands.py',
    '04_ma_crossover.py',
    '05_stochastic.py',
    '06_atr_volatility.py',
    '07_support_resistance.py',
    '08_price_action.py',
    '09_vwap.py',
    '10_ichimoku.py'
]

def run_strategy(filepath):
    """Dynamically import and run a strategy"""
    spec = importlib.util.spec_from_file_location("strategy", filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.run_backtest()

def main():
    strategies_dir = Path(r'C:\Users\nyaga\Documents\AlgoAgent\strategies')
    results = []
    
    print("="*80)
    print("RUNNING ALL 10 TRADING STRATEGY BACKTESTS")
    print("="*80)
    print()
    
    for strategy_file in strategies:
        filepath = strategies_dir / strategy_file
        print(f"\n{'#'*80}")
        print(f"Running: {strategy_file}")
        print(f"{'#'*80}")
        
        try:
            result = run_strategy(filepath)
            if result:
                results.append(result)
        except Exception as e:
            print(f"ERROR running {strategy_file}: {e}")
            results.append({
                'Strategy': strategy_file.replace('.py', '').replace('_', ' ').title(),
                'Total Trades': 'ERROR',
                'Win Rate': 'ERROR',
                'ROI': 'ERROR',
                'Max Drawdown': 'ERROR',
                'Sharpe Ratio': 'ERROR'
            })
    
    # Generate summary report
    print("\n" + "="*80)
    print("GENERATING SUMMARY REPORT")
    print("="*80)
    
    summary_path = strategies_dir.parent / 'BACKTEST_SUMMARY.md'
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("# Trading Strategy Backtesting Summary\n\n")
        f.write("**Date Range:** February 3, 2025 to February 3, 2026 (1 year)\n")
        f.write("**Starting Capital:** $10,000\n")
        f.write("**Symbol:** EURUSD=X (or available forex pair)\n")
        f.write("**Timeframe:** 1H candles (or daily if hourly unavailable)\n\n")
        f.write("---\n\n")
        f.write("## Performance Summary\n\n")
        f.write("| # | Strategy | Total Trades | Win Rate | ROI | Max Drawdown | Sharpe Ratio |\n")
        f.write("|---|----------|--------------|----------|-----|--------------|-------------|\n")
        
        for i, result in enumerate(results, 1):
            f.write(f"| {i} | {result['Strategy']} | {result['Total Trades']} | "
                   f"{result['Win Rate']} | {result['ROI']} | {result['Max Drawdown']} | "
                   f"{result['Sharpe Ratio']} |\n")
        
        f.write("\n---\n\n")
        f.write("## Strategy Descriptions\n\n")
        
        descriptions = [
            ("RSI Momentum", "Buys when RSI < 30 (oversold), sells when RSI > 70 (overbought)"),
            ("MACD Crossover", "Trades on MACD line crossing signal line"),
            ("Bollinger Bands Breakout", "Enters on breakout above upper band, exits below lower band"),
            ("MA Crossover (EMA 9/21)", "Golden/death cross strategy with 9 and 21-period EMAs"),
            ("Stochastic Oscillator", "Trades %K and %D crossovers in oversold/overbought zones"),
            ("ATR Volatility Breakout", "Enters on volatility-adjusted price breakouts"),
            ("Support/Resistance", "Identifies key levels and trades bounces"),
            ("Price Action (Candlestick)", "Detects engulfing patterns, hammers, shooting stars"),
            ("VWAP", "Trades price crosses above/below volume-weighted average price"),
            ("Ichimoku Cloud", "Uses Tenkan/Kijun crosses with cloud position confirmation")
        ]
        
        for i, (name, desc) in enumerate(descriptions, 1):
            f.write(f"### {i}. {name}\n")
            f.write(f"{desc}\n\n")
        
        f.write("---\n\n")
        f.write("## Key Metrics Explained\n\n")
        f.write("- **Total Trades:** Number of completed buy/sell cycles\n")
        f.write("- **Win Rate:** Percentage of profitable trades\n")
        f.write("- **ROI:** Return on Investment (% gain/loss from starting capital)\n")
        f.write("- **Max Drawdown:** Largest peak-to-trough decline in equity\n")
        f.write("- **Sharpe Ratio:** Risk-adjusted return (higher is better)\n\n")
        
        f.write("---\n\n")
        f.write("## Implementation Notes\n\n")
        f.write("[✓] Each strategy is **standalone and executable**\n\n")
        f.write("[✓] Single source of truth - same logic for **backtesting AND live trading**\n\n")
        f.write("[✓] Real market data fetched via **yfinance**\n\n")
        f.write("[✓] Each file contains:\n")
        f.write("- Strategy class with `__init__`, `on_bar()`, `should_enter()`, `should_exit()`\n")
        f.write("- `run_backtest()` function with performance metrics\n")
        f.write("- Data fetching and complete backtest execution\n\n")
        
        f.write("---\n\n")
        f.write("*Generated on: February 3, 2026*\n")
    
    print(f"\n[OK] Summary report saved to: {summary_path}")
    print("\nAll backtests complete!")

if __name__ == '__main__':
    main()
