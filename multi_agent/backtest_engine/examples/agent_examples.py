"""
Simple Example: How Agents Can Use the Backtesting Engine
Demonstrates the easiest ways for agents to test and optimize strategies
"""

import sys
import os

# Add the backtest_engine to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import the simple API functions
from api import quick_test, optimize_momentum_strategy, bt_api

def example_1_quick_strategy_test():
    """Example 1: Quick strategy test"""
    print("EXAMPLE 1: Quick Strategy Test")
    print("="*50)
    
    # Test momentum strategy on AAPL
    result = quick_test(
        strategy='momentum',
        symbol='AAPL',
        start_date='2023-01-01',
        end_date='2023-12-31'
    )
    
    print(result)
    print("\n")

def example_2_strategy_optimization():
    """Example 2: Strategy optimization"""
    print("EXAMPLE 2: Strategy Optimization")
    print("="*50)
    
    # Optimize momentum strategy parameters
    optimization_result = optimize_momentum_strategy(
        symbol='AAPL',
        start_date='2023-01-01',
        end_date='2023-12-31'
    )
    
    print(f"Best parameters found: {optimization_result['best_parameters']}")
    print(f"Validation Sharpe ratio: {optimization_result['validation_score']:.3f}")
    
    # Test the optimized parameters
    if optimization_result['test_results']:
        test_score = optimization_result['test_results']['test_score']
        print(f"Out-of-sample test score: {test_score:.3f}")
    
    print("\n")

def example_3_custom_strategy():
    """Example 3: Create and test custom strategy"""
    print("EXAMPLE 3: Custom Strategy")
    print("="*50)
    
    # Define a simple mean reversion strategy
    def mean_reversion_entry(data, current_bar):
        """Buy when price is 2 standard deviations below 20-day average"""
        if len(data) < 25:
            return False
        
        sma = data['close'].rolling(20).mean()
        std = data['close'].rolling(20).std()
        
        current_price = data['close'].iloc[-1]
        lower_band = sma.iloc[-1] - (2 * std.iloc[-1])
        
        return current_price < lower_band
    
    def mean_reversion_exit(data, current_bar):
        """Sell when price returns to 20-day average"""
        if len(data) < 25:
            return False
        
        sma = data['close'].rolling(20).mean()
        current_price = data['close'].iloc[-1]
        
        return current_price > sma.iloc[-1]
    
    # Create and test the strategy
    from api import create_and_test_strategy
    
    result = create_and_test_strategy(
        entry_logic=mean_reversion_entry,
        exit_logic=mean_reversion_exit,
        symbol='AAPL',
        name='Mean_Reversion'
    )
    
    print(result)
    print("\n")

def example_4_strategy_comparison():
    """Example 4: Compare multiple strategies"""
    print("EXAMPLE 4: Strategy Comparison")
    print("="*50)
    
    from core.strategy_framework import BaseStrategy, StrategyParams, TechnicalIndicators
    import pandas as pd
    
    # Create a simple bollinger bands strategy
    class BollingerStrategy(BaseStrategy):
        def __init__(self):
            params = StrategyParams(
                name="Bollinger_Bands",
                params={'bb_period': 20, 'bb_std': 2}
            )
            super().__init__(params)
        
        def calculate_indicators(self, data, symbol):
            indicators = {}
            indicators['bb'] = TechnicalIndicators.bollinger_bands(data['close'], 20, 2)
            return indicators
        
        def generate_signal(self, engine, current_data, symbol):
            if symbol not in engine.market_data:
                return {}
            
            historical_data = engine.market_data[symbol].loc[:engine.current_time]
            if len(historical_data) < 25:
                return {}
            
            # Calculate Bollinger Bands
            bb = TechnicalIndicators.bollinger_bands(historical_data['close'], 20, 2)
            current_price = current_data[symbol]['close']
            
            try:
                upper_band = bb['upper'].iloc[-1]
                lower_band = bb['lower'].iloc[-1]
                
                if pd.isna(upper_band) or pd.isna(lower_band):
                    return {}
            except (IndexError, KeyError):
                return {}
            
            # Buy when price touches lower band
            if current_price <= lower_band and symbol not in engine.positions:
                return {
                    'action': 'buy',
                    'stop_loss': current_price * 0.95,
                    'take_profit': current_price * 1.1
                }
            
            # Sell when price touches upper band
            elif current_price >= upper_band and symbol in engine.positions:
                return {'action': 'close'}
            
            return {}
    
    # Compare strategies
    comparison = bt_api.compare_strategies(
        strategies=['momentum', BollingerStrategy()],
        symbols=['AAPL'],
        start_date='2023-01-01',
        end_date='2023-12-31'
    )
    
    print(f"Best strategy: {comparison['best_strategy']}")
    print("\nComparison Results:")
    for result in comparison['comparison_table']:
        strategy = result.get('strategy', 'Unknown')
        total_return = result.get('total_return', 0)
        sharpe_ratio = result.get('sharpe_ratio', 0)
        max_drawdown = result.get('max_drawdown', 0)
        print(f"  {strategy}: Return={total_return:.2f}%, Sharpe={sharpe_ratio:.2f}, MaxDD={max_drawdown:.2f}%")
    
    print("\n")

def example_5_generate_report():
    """Example 5: Generate detailed report"""
    print("EXAMPLE 5: Generate Report")
    print("="*50)
    
    # Run a backtest
    results = bt_api.quick_backtest(
        strategy='momentum',
        symbols=['AAPL'],
        start_date='2023-01-01',
        end_date='2023-12-31'
    )
    
    # Generate detailed report
    report_path = bt_api.generate_report(
        results,
        output_name='example_momentum_report',
        include_plots=True
    )
    
    print(f"Detailed report generated: {report_path}")
    print("The report includes:")
    print("  - Comprehensive performance metrics")
    print("  - Risk analysis")
    print("  - Trade-by-trade breakdown")
    print("  - Visual charts and graphs")
    
    print("\n")

def main():
    """Run all examples"""
    print("🤖 AGENT BACKTESTING EXAMPLES")
    print("="*60)
    print("This demonstrates how agents can easily use the backtesting engine")
    print("="*60)
    print()
    
    try:
        example_1_quick_strategy_test()
        example_2_strategy_optimization()
        example_3_custom_strategy()
        example_4_strategy_comparison()
        example_5_generate_report()
        
        print("✅ ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("\n🎯 KEY TAKEAWAYS FOR AGENTS:")
        print("1. Use quick_test() for fast strategy evaluation")
        print("2. Use optimize_momentum_strategy() for parameter tuning")
        print("3. Create custom strategies with simple entry/exit functions")
        print("4. Compare multiple strategies to find the best")
        print("5. Generate detailed reports for thorough analysis")
        print("\n🚀 The backtesting engine is ready for agent use!")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")
        print("Please check the installation and dependencies")

if __name__ == "__main__":
    main()