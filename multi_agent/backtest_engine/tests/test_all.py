"""
Comprehensive Test Suite for the Backtesting Engine
Tests all components of the backtesting system
"""

import sys
import os
sys.path.append('..')

import pandas as pd
import numpy as np
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_quick_backtest():
    """Test the quick backtest functionality"""
    logger.info("Testing quick backtest...")
    
    try:
        from ..api import quick_test
        
        # Test momentum strategy
        result = quick_test(
            strategy='momentum',
            symbol='AAPL',
            start_date='2023-01-01',
            end_date='2023-06-30'
        )
        
        print("✅ Quick Backtest Result:")
        print(result)
        print("\n" + "="*60 + "\n")
        
        return True
    except Exception as e:
        logger.error(f"Quick backtest test failed: {e}")
        return False

def test_strategy_optimization():
    """Test strategy optimization"""
    logger.info("Testing strategy optimization...")
    
    try:
        from ..api import optimize_momentum_strategy
        
        # Test optimization with small parameter space
        result = optimize_momentum_strategy(
            symbol='AAPL',
            start_date='2023-01-01',
            end_date='2023-03-31'
        )
        
        print("✅ Strategy Optimization Result:")
        print(f"Method: {result['method']}")
        print(f"Best parameters: {result['best_parameters']}")
        print(f"Validation score: {result['validation_score']:.3f}")
        print(f"Total combinations tested: {result['total_combinations_tested']}")
        print("\n" + "="*60 + "\n")
        
        return True
    except Exception as e:
        logger.error(f"Strategy optimization test failed: {e}")
        return False

def test_custom_strategy():
    """Test custom strategy creation"""
    logger.info("Testing custom strategy creation...")
    
    try:
        from ..api import create_and_test_strategy
        
        # Define simple moving average crossover strategy
        def ma_crossover_entry(data, current_bar):
            """Entry when fast MA crosses above slow MA"""
            if len(data) < 50:
                return False
            
            fast_ma = data['close'].rolling(10).mean()
            slow_ma = data['close'].rolling(20).mean()
            
            # Check for crossover
            if (fast_ma.iloc[-1] > slow_ma.iloc[-1] and 
                fast_ma.iloc[-2] <= slow_ma.iloc[-2]):
                return True
            return False
        
        def ma_crossover_exit(data, current_bar):
            """Exit when fast MA crosses below slow MA"""
            if len(data) < 50:
                return False
            
            fast_ma = data['close'].rolling(10).mean()
            slow_ma = data['close'].rolling(20).mean()
            
            # Check for crossover
            if (fast_ma.iloc[-1] < slow_ma.iloc[-1] and 
                fast_ma.iloc[-2] >= slow_ma.iloc[-2]):
                return True
            return False
        
        result = create_and_test_strategy(
            entry_logic=ma_crossover_entry,
            exit_logic=ma_crossover_exit,
            symbol='AAPL',
            name='MA_Crossover'
        )
        
        print("✅ Custom Strategy (MA Crossover) Result:")
        print(result)
        print("\n" + "="*60 + "\n")
        
        return True
    except Exception as e:
        logger.error(f"Custom strategy test failed: {e}")
        return False

def test_strategy_comparison():
    """Test strategy comparison"""
    logger.info("Testing strategy comparison...")
    
    try:
        from ..api import bt_api, MomentumStrategy, create_and_test_strategy
        from ..core.strategy_framework import BaseStrategy, StrategyParams, TechnicalIndicators
        
        # Create a simple RSI strategy
        class RSIStrategy(BaseStrategy):
            def __init__(self, params=None):
                if params is None:
                    params = StrategyParams(
                        name="RSI_Strategy",
                        params={'rsi_period': 14, 'rsi_oversold': 30, 'rsi_overbought': 70}
                    )
                super().__init__(params)
            
            def calculate_indicators(self, data, symbol):
                indicators = {}
                indicators['rsi'] = TechnicalIndicators.rsi(data['close'], self.params.get('rsi_period', 14))
                return indicators
            
            def generate_signal(self, engine, current_data, symbol):
                if symbol not in engine.market_data:
                    return {}
                
                historical_data = engine.market_data[symbol].loc[:engine.current_time]
                if len(historical_data) < 20:
                    return {}
                
                # Calculate RSI
                rsi = TechnicalIndicators.rsi(historical_data['close'], 14)
                current_rsi = rsi.iloc[-1]
                
                if pd.isna(current_rsi):
                    return {}
                
                current_price = current_data[symbol]['close']
                
                # RSI oversold - buy signal
                if current_rsi < 30 and symbol not in engine.positions:
                    return {
                        'action': 'buy',
                        'stop_loss': current_price * 0.95,
                        'take_profit': current_price * 1.1
                    }
                
                # RSI overbought - sell signal
                elif current_rsi > 70 and symbol in engine.positions:
                    return {'action': 'close'}
                
                return {}
        
        # Compare momentum vs RSI strategy
        comparison = bt_api.compare_strategies(
            strategies=['momentum', RSIStrategy()],
            symbols=['AAPL'],
            start_date='2023-01-01',
            end_date='2023-06-30'
        )
        
        print("✅ Strategy Comparison Result:")
        print(f"Strategies tested: {comparison['strategies_tested']}")
        print(f"Best strategy: {comparison['best_strategy']}")
        print("Comparison table:")
        for row in comparison['comparison_table']:
            print(f"  {row}")
        print("\n" + "="*60 + "\n")
        
        return True
    except Exception as e:
        logger.error(f"Strategy comparison test failed: {e}")
        return False

def test_full_backtest_api():
    """Test the full BacktestAPI functionality"""
    logger.info("Testing full BacktestAPI...")
    
    try:
        from ..api import BacktestAPI
        
        # Create API instance
        api = BacktestAPI()
        
        # Test data loading
        market_data = api.load_data_from_mt5(
            symbols=['AAPL', 'MSFT'],
            start_date='2023-01-01',
            end_date='2023-03-31'
        )
        
        print(f"✅ Loaded data for {len(market_data)} symbols")
        for symbol, data in market_data.items():
            print(f"  {symbol}: {len(data)} records")
        
        # Test momentum strategy
        momentum_results = api.quick_backtest(
            strategy='momentum',
            symbols=['AAPL'],
            start_date='2023-01-01',
            end_date='2023-03-31'
        )
        
        print(f"✅ Momentum strategy return: {momentum_results['total_return_pct']:.2f}%")
        
        # Generate report
        report_path = api.generate_report(momentum_results, "test_momentum_report", include_plots=False)
        print(f"✅ Report generated: {report_path}")
        
        print("\n" + "="*60 + "\n")
        return True
        
    except Exception as e:
        logger.error(f"Full BacktestAPI test failed: {e}")
        return False

def test_performance_analytics():
    """Test performance analytics functionality"""
    logger.info("Testing performance analytics...")
    
    try:
        from ..api import bt_api
        from ..analytics.performance_analytics import PerformanceAnalytics
        
        # Run a backtest first
        results = bt_api.quick_backtest(
            strategy='momentum',
            symbols=['AAPL'],
            start_date='2023-01-01',
            end_date='2023-06-30'
        )
        
        # Create analytics
        analytics = PerformanceAnalytics(results['full_results'])
        
        # Test advanced metrics
        advanced_metrics = analytics.calculate_advanced_metrics()
        print("✅ Advanced Metrics:")
        for metric, value in advanced_metrics.items():
            if isinstance(value, (int, float)):
                print(f"  {metric}: {value:.3f}")
        
        # Test trade analysis
        trade_analysis = analytics.analyze_trades()
        print("\n✅ Trade Analysis:")
        print(f"  Total trades: {trade_analysis.get('total_trades', 0)}")
        print(f"  Gross profit: ${trade_analysis.get('gross_profit', 0):.2f}")
        print(f"  Gross loss: ${trade_analysis.get('gross_loss', 0):.2f}")
        
        # Test risk metrics
        risk_metrics = analytics.calculate_risk_metrics()
        print("\n✅ Risk Metrics:")
        for metric, value in risk_metrics.items():
            if isinstance(value, (int, float)):
                print(f"  {metric}: {value:.3f}")
        
        print("\n" + "="*60 + "\n")
        return True
        
    except Exception as e:
        logger.error(f"Performance analytics test failed: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("🚀 Starting Backtesting Engine Test Suite")
    print("="*60)
    
    tests = [
        ("Quick Backtest", test_quick_backtest),
        ("Custom Strategy", test_custom_strategy),
        ("Strategy Comparison", test_strategy_comparison),
        ("Full BacktestAPI", test_full_backtest_api),
        ("Performance Analytics", test_performance_analytics),
        ("Strategy Optimization", test_strategy_optimization),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print("🏁 TEST SUITE COMPLETE")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Backtesting engine is ready for use.")
        return True
    else:
        print(f"\n⚠️ {failed} tests failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)