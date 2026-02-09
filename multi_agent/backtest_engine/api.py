"""
Agent-Friendly Backtesting API
Simple, high-level interface for agents to use the backtesting system

Features:
- Simple function-based API
- Automatic data handling
- Built-in strategy examples
- Automatic optimization
- Easy result interpretation
- Report generation
- Integration with MT5 framework
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
import logging
from pathlib import Path
import json

# Import our backtesting components
try:
    from .core.backtesting_engine import BacktestEngine, BacktestConfig
    from .core.strategy_framework import BaseStrategy, StrategyParams, MomentumStrategy, StrategyTester, TechnicalIndicators
    from .analytics.performance_analytics import PerformanceAnalytics, ReportGenerator
    from .optimization.optimizer import StrategyOptimizer, OptimizationConfig, OptimizationParameter
except ImportError:
    # If running as script, use absolute imports
    from core.backtesting_engine import BacktestEngine, BacktestConfig
    from core.strategy_framework import BaseStrategy, StrategyParams, MomentumStrategy, StrategyTester, TechnicalIndicators
    from analytics.performance_analytics import PerformanceAnalytics, ReportGenerator
    from optimization.optimizer import StrategyOptimizer, OptimizationConfig, OptimizationParameter

logger = logging.getLogger(__name__)

class BacktestAPI:
    """
    High-level API for agents to easily use the backtesting system
    """
    
    def __init__(self, data_dir: str = "data", reports_dir: str = "reports"):
        """
        Initialize the backtesting API
        
        Args:
            data_dir: Directory for data storage
            reports_dir: Directory for report storage
        """
        self.data_dir = Path(data_dir)
        self.reports_dir = Path(reports_dir)
        
        # Create directories
        self.data_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        
        # Cache for loaded data
        self.market_data_cache = {}
        
        # Default configuration
        self.default_config = BacktestConfig(
            start_date='2022-01-01',
            end_date='2023-12-31',
            initial_capital=10000.0,
            commission=0.001,
            slippage=0.0001,
            symbols=['AAPL']
        )
        
        logger.info("BacktestAPI initialized")
    
    def load_data_from_mt5(self, symbols: List[str], start_date: str, end_date: str, timeframe: str = "1H") -> Dict[str, pd.DataFrame]:
        """
        Load market data from MT5 (placeholder - would integrate with actual MT5 data)
        
        Args:
            symbols: List of symbols to load
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            timeframe: Timeframe (1H, 1D, etc.)
            
        Returns:
            Dictionary of market data
        """
        logger.info(f"Loading MT5 data for {symbols} from {start_date} to {end_date}")
        
        # For now, generate sample data
        # In production, this would connect to MT5 Python SDK
        market_data = {}
        
        for symbol in symbols:
            # Generate sample OHLCV data
            date_range = pd.date_range(start=start_date, end=end_date, freq='H')
            
            # Simulate price movement
            np.random.seed(hash(symbol) % 2**32)  # Consistent seed per symbol
            returns = np.random.normal(0.0001, 0.02, len(date_range))
            prices = 100 * np.exp(np.cumsum(returns))
            
            # Create OHLCV data
            data = pd.DataFrame({
                'open': prices * (1 + np.random.normal(0, 0.001, len(prices))),
                'high': prices * (1 + abs(np.random.normal(0, 0.002, len(prices)))),
                'low': prices * (1 - abs(np.random.normal(0, 0.002, len(prices)))),
                'close': prices,
                'volume': np.random.randint(1000, 10000, len(prices))
            }, index=date_range)
            
            # Ensure high >= close >= low
            data['high'] = np.maximum(data[['open', 'close']].max(axis=1), data['high'])
            data['low'] = np.minimum(data[['open', 'close']].min(axis=1), data['low'])
            
            market_data[symbol] = data
            logger.info(f"Loaded {len(data)} records for {symbol}")
        
        # Cache the data
        cache_key = f"{'-'.join(symbols)}_{start_date}_{end_date}_{timeframe}"
        self.market_data_cache[cache_key] = market_data
        
        return market_data
    
    def create_simple_strategy(self, 
                             name: str,
                             entry_conditions: Callable[[pd.DataFrame, Dict], bool],
                             exit_conditions: Callable[[pd.DataFrame, Dict], bool],
                             parameters: Dict[str, Any] = None) -> BaseStrategy:
        """
        Create a simple custom strategy
        
        Args:
            name: Strategy name
            entry_conditions: Function that returns True for entry signals
            exit_conditions: Function that returns True for exit signals
            parameters: Strategy parameters
            
        Returns:
            Strategy instance
        """
        class CustomStrategy(BaseStrategy):
            def __init__(self, params):
                super().__init__(params)
                self.entry_func = entry_conditions
                self.exit_func = exit_conditions
            
            def calculate_indicators(self, data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
                # Basic indicators
                indicators = {}
                indicators['sma_20'] = TechnicalIndicators.sma(data['close'], 20)
                indicators['rsi'] = TechnicalIndicators.rsi(data['close'], 14)
                indicators['atr'] = TechnicalIndicators.atr(data['high'], data['low'], data['close'], 14)
                return indicators
            
            def generate_signal(self, engine, current_data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
                if symbol not in engine.market_data:
                    return {}
                
                historical_data = engine.market_data[symbol].loc[:engine.current_time]
                if len(historical_data) < 30:  # Need enough data for indicators
                    return {}
                
                # Check for entry signal
                if symbol not in engine.positions:
                    if self.entry_func(historical_data, current_data.get(symbol, {})):
                        current_price = current_data[symbol]['close']
                        atr = TechnicalIndicators.atr(historical_data['high'], historical_data['low'], historical_data['close'], 14).iloc[-1]
                        
                        return {
                            'action': 'buy',
                            'stop_loss': current_price - (2 * atr),
                            'take_profit': current_price + (3 * atr)
                        }
                
                # Check for exit signal
                elif symbol in engine.positions:
                    if self.exit_func(historical_data, current_data.get(symbol, {})):
                        return {'action': 'close'}
                
                return {}
        
        strategy_params = StrategyParams(
            name=name,
            description=f"Custom strategy: {name}",
            params=parameters or {}
        )
        
        return CustomStrategy(strategy_params)
    
    def quick_backtest(self, 
                      strategy: Union[BaseStrategy, str], 
                      symbols: List[str] = None,
                      start_date: str = '2022-01-01',
                      end_date: str = '2023-12-31',
                      initial_capital: float = 10000.0) -> Dict[str, Any]:
        """
        Run a quick backtest with minimal setup
        
        Args:
            strategy: Strategy instance or 'momentum' for default momentum strategy
            symbols: List of symbols (defaults to ['AAPL'])
            start_date: Start date
            end_date: End date
            initial_capital: Initial capital
            
        Returns:
            Backtest results with key metrics
        """
        # Set defaults
        if symbols is None:
            symbols = ['AAPL']
        
        logger.info(f"Running quick backtest: {symbols}, {start_date} to {end_date}")
        
        # Load market data
        market_data = self.load_data_from_mt5(symbols, start_date, end_date)
        
        # Create strategy if string provided
        if isinstance(strategy, str):
            if strategy.lower() == 'momentum':
                strategy = MomentumStrategy()
            else:
                raise ValueError(f"Unknown strategy: {strategy}")
        
        # Create backtest configuration
        config = BacktestConfig(
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            symbols=symbols
        )
        
        # Create and run backtest
        engine = BacktestEngine(config)
        
        # Load data with strategy indicators
        for symbol, data in market_data.items():
            prepared_data = strategy.prepare_data(data.copy(), symbol)
            engine.load_market_data(symbol, prepared_data)
        
        engine.set_strategy(strategy.on_bar)
        results = engine.run_backtest()
        
        # Generate analytics
        analytics = PerformanceAnalytics(results)
        advanced_metrics = analytics.calculate_advanced_metrics()
        
        # Combine results
        summary = {
            'strategy_name': strategy.name,
            'symbols': symbols,
            'period': f"{start_date} to {end_date}",
            'initial_capital': initial_capital,
            'final_equity': results['summary']['final_equity'],
            'total_return_pct': results['summary']['total_return'],
            'max_drawdown_pct': results['summary']['max_drawdown'],
            'sharpe_ratio': results['summary']['sharpe_ratio'],
            'total_trades': results['trades']['total_trades'],
            'win_rate': results['trades']['win_rate'],
            'profit_factor': results['summary']['profit_factor'],
            'advanced_metrics': advanced_metrics,
            'full_results': results
        }
        
        logger.info(f"Quick backtest completed. Total return: {summary['total_return_pct']:.2f}%")
        return summary
    
    def optimize_strategy(self,
                         strategy_class: type,
                         optimization_params: Dict[str, Dict],
                         symbols: List[str] = None,
                         start_date: str = '2022-01-01',
                         end_date: str = '2023-12-31',
                         optimization_method: str = 'grid_search',
                         max_iterations: int = 500) -> Dict[str, Any]:
        """
        Optimize strategy parameters
        
        Args:
            strategy_class: Strategy class to optimize
            optimization_params: Parameter ranges {'param_name': {'min': 1, 'max': 10, 'step': 1}}
            symbols: List of symbols
            start_date: Start date
            end_date: End date
            optimization_method: 'grid_search', 'random_search', or 'bayesian'
            max_iterations: Maximum iterations
            
        Returns:
            Optimization results
        """
        if symbols is None:
            symbols = ['AAPL']
        
        logger.info(f"Optimizing {strategy_class.__name__} on {symbols}")
        
        # Load market data
        market_data = self.load_data_from_mt5(symbols, start_date, end_date)
        
        # Create optimization configuration
        opt_params = []
        for param_name, param_config in optimization_params.items():
            opt_param = OptimizationParameter(
                name=param_name,
                min_value=param_config['min'],
                max_value=param_config['max'],
                step=param_config.get('step', 1),
                param_type=param_config.get('type', 'int')
            )
            opt_params.append(opt_param)
        
        opt_config = OptimizationConfig(
            parameters=opt_params,
            optimization_metric='sharpe_ratio',
            max_iterations=max_iterations
        )
        
        # Create backtest configuration
        backtest_config = BacktestConfig(
            start_date=start_date,
            end_date=end_date,
            symbols=symbols
        )
        
        # Run optimization
        optimizer = StrategyOptimizer(strategy_class, backtest_config, market_data)
        
        if optimization_method == 'grid_search':
            results = optimizer.grid_search_optimization(opt_config)
        elif optimization_method == 'random_search':
            results = optimizer.random_search_optimization(opt_config)
        elif optimization_method == 'bayesian':
            results = optimizer.bayesian_optimization(opt_config)
        else:
            raise ValueError(f"Unknown optimization method: {optimization_method}")
        
        # Test best parameters
        test_results = optimizer.test_best_parameters()
        
        # Format results for agents
        optimization_summary = {
            'method': optimization_method,
            'symbols': symbols,
            'period': f"{start_date} to {end_date}",
            'total_combinations_tested': len(results),
            'best_parameters': results[0].parameters if results else {},
            'validation_score': results[0].score if results else 0,
            'test_results': test_results,
            'top_10_results': [
                {
                    'rank': r.rank,
                    'parameters': r.parameters,
                    'score': r.score,
                    'total_return': r.metrics.get('total_return', 0),
                    'max_drawdown': r.metrics.get('max_drawdown', 0),
                    'win_rate': r.metrics.get('win_rate', 0)
                } for r in results[:10]
            ],
            'full_results': results
        }
        
        logger.info(f"Optimization completed. Best Sharpe ratio: {optimization_summary['validation_score']:.3f}")
        return optimization_summary
    
    def compare_strategies(self,
                          strategies: List[Union[BaseStrategy, str]],
                          symbols: List[str] = None,
                          start_date: str = '2022-01-01',
                          end_date: str = '2023-12-31') -> Dict[str, Any]:
        """
        Compare multiple strategies
        
        Args:
            strategies: List of strategies to compare
            symbols: List of symbols
            start_date: Start date
            end_date: End date
            
        Returns:
            Comparison results
        """
        if symbols is None:
            symbols = ['AAPL']
        
        logger.info(f"Comparing {len(strategies)} strategies on {symbols}")
        
        # Load market data once
        market_data = self.load_data_from_mt5(symbols, start_date, end_date)
        
        # Create configuration
        config = BacktestConfig(
            start_date=start_date,
            end_date=end_date,
            symbols=symbols
        )
        
        # Create strategy tester
        tester = StrategyTester()
        
        # Add strategies
        for i, strategy in enumerate(strategies):
            if isinstance(strategy, str):
                if strategy.lower() == 'momentum':
                    strategy_instance = MomentumStrategy()
                else:
                    continue
            else:
                strategy_instance = strategy
            
            strategy_name = f"{strategy_instance.name}_{i}"
            tester.add_strategy(strategy_name, strategy_instance)
        
        # Run tests
        all_results = tester.test_all_strategies(config, market_data)
        
        # Generate comparison
        comparison_df = tester.compare_strategies()
        best_strategy = tester.get_best_strategy()
        
        comparison_summary = {
            'symbols': symbols,
            'period': f"{start_date} to {end_date}",
            'strategies_tested': len(all_results),
            'best_strategy': best_strategy,
            'comparison_table': comparison_df.to_dict('records') if not comparison_df.empty else [],
            'detailed_results': all_results
        }
        
        logger.info(f"Strategy comparison completed. Best strategy: {best_strategy}")
        return comparison_summary
    
    def generate_report(self, 
                       backtest_results: Dict[str, Any], 
                       output_name: str = None,
                       include_plots: bool = True) -> str:
        """
        Generate comprehensive HTML report
        
        Args:
            backtest_results: Results from quick_backtest or full backtest
            output_name: Output file name (without extension)
            include_plots: Whether to include plots
            
        Returns:
            Path to generated report
        """
        if output_name is None:
            output_name = f"backtest_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Extract full results if this is from quick_backtest
        if 'full_results' in backtest_results:
            full_results = backtest_results['full_results']
        else:
            full_results = backtest_results
        
        # Create analytics
        analytics = PerformanceAnalytics(full_results)
        report_generator = ReportGenerator(analytics)
        
        # Generate HTML report
        html_path = self.reports_dir / f"{output_name}.html"
        report_path = report_generator.generate_html_report(str(html_path), include_plots)
        
        # Save plots if requested
        if include_plots:
            plots_dir = self.reports_dir / f"{output_name}_plots"
            report_generator.save_plots(str(plots_dir))
        
        logger.info(f"Report generated: {report_path}")
        return report_path
    
    def agent_friendly_summary(self, backtest_results: Dict[str, Any]) -> str:
        """
        Generate agent-friendly text summary of results
        
        Args:
            backtest_results: Backtest results
            
        Returns:
            Text summary suitable for agent interpretation
        """
        if 'full_results' in backtest_results:
            # This is from quick_backtest
            summary = f"""
BACKTESTING RESULTS SUMMARY

Strategy: {backtest_results['strategy_name']}
Symbols: {', '.join(backtest_results['symbols'])}
Period: {backtest_results['period']}

PERFORMANCE METRICS:
- Initial Capital: ${backtest_results['initial_capital']:,.2f}
- Final Equity: ${backtest_results['final_equity']:,.2f}
- Total Return: {backtest_results['total_return_pct']:.2f}%
- Maximum Drawdown: {backtest_results['max_drawdown_pct']:.2f}%
- Sharpe Ratio: {backtest_results['sharpe_ratio']:.3f}

TRADING STATISTICS:
- Total Trades: {backtest_results['total_trades']}
- Win Rate: {backtest_results['win_rate']:.1f}%
- Profit Factor: {backtest_results['profit_factor']:.2f}

INTERPRETATION:
"""
            # Add interpretation
            if backtest_results['total_return_pct'] > 10:
                summary += "✅ STRONG PERFORMANCE: Strategy generated good returns\n"
            elif backtest_results['total_return_pct'] > 0:
                summary += "⚠️ MODERATE PERFORMANCE: Strategy was profitable but modest returns\n"
            else:
                summary += "❌ POOR PERFORMANCE: Strategy lost money\n"
            
            if backtest_results['sharpe_ratio'] > 1.0:
                summary += "✅ GOOD RISK-ADJUSTED RETURNS: High Sharpe ratio\n"
            elif backtest_results['sharpe_ratio'] > 0.5:
                summary += "⚠️ MODERATE RISK-ADJUSTED RETURNS: Decent Sharpe ratio\n"
            else:
                summary += "❌ POOR RISK-ADJUSTED RETURNS: Low Sharpe ratio\n"
            
            if backtest_results['max_drawdown_pct'] < 10:
                summary += "✅ LOW RISK: Small maximum drawdown\n"
            elif backtest_results['max_drawdown_pct'] < 20:
                summary += "⚠️ MODERATE RISK: Moderate maximum drawdown\n"
            else:
                summary += "❌ HIGH RISK: Large maximum drawdown\n"
            
            if backtest_results['win_rate'] > 60:
                summary += "✅ HIGH WIN RATE: Strategy wins majority of trades\n"
            elif backtest_results['win_rate'] > 40:
                summary += "⚠️ MODERATE WIN RATE: Balanced win/loss ratio\n"
            else:
                summary += "❌ LOW WIN RATE: Strategy loses more often than it wins\n"
            
            # Recommendations
            summary += "\nRECOMMENDations:\n"
            if (backtest_results['total_return_pct'] > 10 and 
                backtest_results['sharpe_ratio'] > 1.0 and 
                backtest_results['max_drawdown_pct'] < 15):
                summary += "🎯 READY FOR LIVE TRADING: Strategy shows strong performance metrics\n"
            elif backtest_results['total_return_pct'] > 0:
                summary += "🔧 NEEDS OPTIMIZATION: Strategy is profitable but could be improved\n"
                summary += "   - Consider optimizing parameters\n"
                summary += "   - Review risk management settings\n"
                summary += "   - Test on different time periods\n"
            else:
                summary += "🚫 NOT READY: Strategy needs significant improvement\n"
                summary += "   - Revise strategy logic\n"
                summary += "   - Improve entry/exit conditions\n"
                summary += "   - Consider different approach\n"
        
        else:
            # This is raw backtest results
            summary = f"Total Return: {backtest_results['summary']['total_return']:.2f}%"
        
        return summary

# Global API instance for easy access
bt_api = BacktestAPI()

# Convenience functions for agents
def quick_test(strategy='momentum', symbol='AAPL', start_date='2022-01-01', end_date='2023-12-31') -> str:
    """
    Quick and easy strategy test for agents
    
    Args:
        strategy: Strategy to test ('momentum' or strategy instance)
        symbol: Symbol to test
        start_date: Start date
        end_date: End date
        
    Returns:
        Agent-friendly summary
    """
    results = bt_api.quick_backtest(
        strategy=strategy,
        symbols=[symbol],
        start_date=start_date,
        end_date=end_date
    )
    return bt_api.agent_friendly_summary(results)

def optimize_momentum_strategy(symbol='AAPL', start_date='2022-01-01', end_date='2023-12-31') -> Dict[str, Any]:
    """
    Optimize momentum strategy parameters
    
    Args:
        symbol: Symbol to optimize on
        start_date: Start date
        end_date: End date
        
    Returns:
        Optimization results
    """
    optimization_params = {
        'rsi_period': {'min': 10, 'max': 20, 'step': 2},
        'sma_period': {'min': 15, 'max': 30, 'step': 5},
        'atr_multiplier': {'min': 1.5, 'max': 3.0, 'step': 0.5, 'type': 'float'}
    }
    
    return bt_api.optimize_strategy(
        strategy_class=MomentumStrategy,
        optimization_params=optimization_params,
        symbols=[symbol],
        start_date=start_date,
        end_date=end_date,
        optimization_method='random_search',
        max_iterations=100
    )

def create_and_test_strategy(entry_logic, exit_logic, symbol='AAPL', name='CustomStrategy') -> str:
    """
    Create and test a custom strategy
    
    Args:
        entry_logic: Function for entry conditions
        exit_logic: Function for exit conditions
        symbol: Symbol to test
        name: Strategy name
        
    Returns:
        Agent-friendly summary
    """
    strategy = bt_api.create_simple_strategy(
        name=name,
        entry_conditions=entry_logic,
        exit_conditions=exit_logic
    )
    
    results = bt_api.quick_backtest(
        strategy=strategy,
        symbols=[symbol]
    )
    
    return bt_api.agent_friendly_summary(results)

def compare_momentum_vs_custom(custom_strategy, symbol='AAPL') -> Dict[str, Any]:
    """
    Compare momentum strategy vs custom strategy
    
    Args:
        custom_strategy: Custom strategy instance
        symbol: Symbol to test
        
    Returns:
        Comparison results
    """
    return bt_api.compare_strategies(
        strategies=['momentum', custom_strategy],
        symbols=[symbol]
    )