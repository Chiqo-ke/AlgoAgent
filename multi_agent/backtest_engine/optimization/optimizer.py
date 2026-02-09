"""
Strategy Optimization Engine
Advanced parameter optimization for trading strategies

Features:
- Grid search optimization
- Bayesian optimization
- Genetic algorithm optimization
- Walk-forward analysis
- Out-of-sample testing
- Parameter sensitivity analysis
- Multi-objective optimization
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable, Union
import logging
from dataclasses import dataclass, field
from itertools import product
import json
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

from ..core.backtesting_engine import BacktestEngine, BacktestConfig
from ..core.strategy_framework import BaseStrategy, StrategyParams
from ..analytics.performance_analytics import PerformanceAnalytics

logger = logging.getLogger(__name__)

@dataclass
class OptimizationParameter:
    """Single optimization parameter definition"""
    name: str
    min_value: Union[int, float]
    max_value: Union[int, float]
    step: Union[int, float] = None
    values: List[Union[int, float]] = None
    param_type: str = "int"  # 'int', 'float', 'choice'
    
    def __post_init__(self):
        if self.values is None and self.step is None:
            if self.param_type == "int":
                self.step = 1
            else:
                self.step = (self.max_value - self.min_value) / 10
    
    def get_values(self) -> List[Union[int, float]]:
        """Get list of values to test"""
        if self.values is not None:
            return self.values
        
        if self.param_type == "int":
            return list(range(int(self.min_value), int(self.max_value) + 1, int(self.step)))
        else:
            values = []
            current = self.min_value
            while current <= self.max_value:
                values.append(current)
                current += self.step
            return values

@dataclass
class OptimizationConfig:
    """Optimization configuration"""
    parameters: List[OptimizationParameter]
    optimization_metric: str = "sharpe_ratio"  # metric to optimize
    maximize: bool = True  # whether to maximize or minimize the metric
    max_iterations: int = 1000
    train_ratio: float = 0.7  # ratio of data for training
    validation_ratio: float = 0.2  # ratio for validation
    test_ratio: float = 0.1  # ratio for out-of-sample testing
    min_trades: int = 10  # minimum trades required for valid result
    parallel: bool = False  # parallel execution (not implemented yet)
    
    def __post_init__(self):
        if abs(self.train_ratio + self.validation_ratio + self.test_ratio - 1.0) > 0.001:
            raise ValueError("Train, validation, and test ratios must sum to 1.0")

@dataclass
class OptimizationResult:
    """Single optimization result"""
    parameters: Dict[str, Any]
    metrics: Dict[str, float]
    backtest_results: Dict[str, Any]
    period: str  # 'train', 'validation', 'test'
    rank: int = 0
    score: float = 0.0

class StrategyOptimizer:
    """
    Advanced strategy optimization engine
    
    Supports multiple optimization algorithms and validation techniques
    """
    
    def __init__(self, strategy_class: type, base_config: BacktestConfig, market_data: Dict[str, pd.DataFrame]):
        """
        Initialize optimizer
        
        Args:
            strategy_class: Strategy class to optimize
            base_config: Base backtesting configuration
            market_data: Market data dictionary
        """
        self.strategy_class = strategy_class
        self.base_config = base_config
        self.market_data = market_data
        
        # Split data for training/validation/testing
        self.data_splits = {}
        self._prepare_data_splits()
        
        # Results storage
        self.optimization_results: List[OptimizationResult] = []
        self.best_parameters = {}
        self.optimization_history = []
        
    def _prepare_data_splits(self):
        """Prepare data splits for training, validation, and testing"""
        for symbol, data in self.market_data.items():
            data_sorted = data.sort_index()
            total_length = len(data_sorted)
            
            # Calculate split indices
            train_end = int(total_length * 0.7)
            validation_end = int(total_length * 0.9)
            
            self.data_splits[symbol] = {
                'train': data_sorted.iloc[:train_end],
                'validation': data_sorted.iloc[train_end:validation_end],
                'test': data_sorted.iloc[validation_end:],
                'full': data_sorted
            }
    
    def _create_strategy_with_params(self, parameters: Dict[str, Any]) -> BaseStrategy:
        """Create strategy instance with given parameters"""
        strategy_params = StrategyParams(
            name=f"OptimizedStrategy",
            params=parameters
        )
        return self.strategy_class(strategy_params)
    
    def _run_single_backtest(self, parameters: Dict[str, Any], data_split: str) -> Dict[str, Any]:
        """
        Run backtest with specific parameters and data split
        
        Args:
            parameters: Strategy parameters
            data_split: 'train', 'validation', 'test', or 'full'
            
        Returns:
            Backtest results
        """
        try:
            # Create strategy with parameters
            strategy = self._create_strategy_with_params(parameters)
            
            # Create backtest config for this split
            config = BacktestConfig(
                start_date=self.base_config.start_date,
                end_date=self.base_config.end_date,
                initial_capital=self.base_config.initial_capital,
                commission=self.base_config.commission,
                slippage=self.base_config.slippage,
                max_positions=self.base_config.max_positions,
                risk_per_trade=self.base_config.risk_per_trade,
                max_daily_loss=self.base_config.max_daily_loss,
                timeframe=self.base_config.timeframe,
                symbols=self.base_config.symbols
            )
            
            # Create engine
            engine = BacktestEngine(config)
            
            # Load data for this split
            split_data = {}
            for symbol in self.base_config.symbols:
                if symbol in self.data_splits:
                    split_data[symbol] = self.data_splits[symbol][data_split]
                    prepared_data = strategy.prepare_data(split_data[symbol].copy(), symbol)
                    engine.load_market_data(symbol, prepared_data)
            
            # Set strategy
            engine.set_strategy(strategy.on_bar)
            
            # Run backtest
            results = engine.run_backtest()
            return results
            
        except Exception as e:
            logger.error(f"Error in backtest with parameters {parameters}: {e}")
            return {}
    
    def grid_search_optimization(self, config: OptimizationConfig) -> List[OptimizationResult]:
        """
        Perform grid search optimization
        
        Args:
            config: Optimization configuration
            
        Returns:
            List of optimization results sorted by performance
        """
        logger.info("Starting grid search optimization...")
        
        # Generate all parameter combinations
        param_names = [p.name for p in config.parameters]
        param_values = [p.get_values() for p in config.parameters]
        
        all_combinations = list(product(*param_values))
        total_combinations = len(all_combinations)
        
        logger.info(f"Testing {total_combinations} parameter combinations")
        
        if total_combinations > config.max_iterations:
            # Randomly sample if too many combinations
            import random
            all_combinations = random.sample(all_combinations, config.max_iterations)
            logger.info(f"Randomly sampling {config.max_iterations} combinations")
        
        results = []
        
        for i, param_combination in enumerate(all_combinations):
            # Create parameter dictionary
            parameters = dict(zip(param_names, param_combination))
            
            # Run training backtest
            train_results = self._run_single_backtest(parameters, 'train')
            
            if not train_results or train_results.get('trades', {}).get('total_trades', 0) < config.min_trades:
                continue
            
            # Calculate training metrics
            train_analytics = PerformanceAnalytics(train_results)
            train_metrics = train_analytics.calculate_advanced_metrics()
            train_metrics.update(train_results['summary'])
            train_metrics.update(train_results['trades'])
            
            # Get optimization score
            score = train_metrics.get(config.optimization_metric, 0)
            if not config.maximize:
                score = -score
            
            # Create result
            result = OptimizationResult(
                parameters=parameters,
                metrics=train_metrics,
                backtest_results=train_results,
                period='train',
                score=score
            )
            
            results.append(result)
            
            # Progress logging
            if (i + 1) % 50 == 0:
                logger.info(f"Completed {i + 1}/{len(all_combinations)} combinations")
        
        # Sort results by score
        results.sort(key=lambda x: x.score, reverse=True)
        
        # Assign ranks
        for i, result in enumerate(results):
            result.rank = i + 1
        
        # Validate top performers on validation set
        top_results = results[:min(20, len(results))]  # Top 20 or fewer
        validated_results = self._validate_results(top_results, config)
        
        self.optimization_results = validated_results
        logger.info(f"Grid search optimization completed. Best {config.optimization_metric}: {validated_results[0].score:.4f}")
        
        return validated_results
    
    def _validate_results(self, results: List[OptimizationResult], config: OptimizationConfig) -> List[OptimizationResult]:
        """
        Validate top results on validation set
        
        Args:
            results: Results to validate
            config: Optimization configuration
            
        Returns:
            Validated results
        """
        logger.info("Validating top performers on validation set...")
        
        validated_results = []
        
        for result in results:
            # Run validation backtest
            val_results = self._run_single_backtest(result.parameters, 'validation')
            
            if not val_results or val_results.get('trades', {}).get('total_trades', 0) < config.min_trades:
                continue
            
            # Calculate validation metrics
            val_analytics = PerformanceAnalytics(val_results)
            val_metrics = val_analytics.calculate_advanced_metrics()
            val_metrics.update(val_results['summary'])
            val_metrics.update(val_results['trades'])
            
            # Get validation score
            val_score = val_metrics.get(config.optimization_metric, 0)
            if not config.maximize:
                val_score = -val_score
            
            # Create validated result
            validated_result = OptimizationResult(
                parameters=result.parameters,
                metrics=val_metrics,
                backtest_results=val_results,
                period='validation',
                score=val_score
            )
            
            validated_results.append(validated_result)
        
        # Sort by validation score
        validated_results.sort(key=lambda x: x.score, reverse=True)
        
        # Assign new ranks
        for i, result in enumerate(validated_results):
            result.rank = i + 1
        
        return validated_results
    
    def bayesian_optimization(self, config: OptimizationConfig) -> List[OptimizationResult]:
        """
        Perform Bayesian optimization (simplified implementation)
        
        Args:
            config: Optimization configuration
            
        Returns:
            Optimization results
        """
        # This would require scikit-optimize or similar library
        # For now, fall back to random search
        logger.warning("Bayesian optimization not fully implemented, using random search")
        return self.random_search_optimization(config)
    
    def random_search_optimization(self, config: OptimizationConfig) -> List[OptimizationResult]:
        """
        Perform random search optimization
        
        Args:
            config: Optimization configuration
            
        Returns:
            Optimization results
        """
        logger.info("Starting random search optimization...")
        
        import random
        results = []
        
        for i in range(config.max_iterations):
            # Generate random parameters
            parameters = {}
            for param in config.parameters:
                if param.param_type == "int":
                    parameters[param.name] = random.randint(int(param.min_value), int(param.max_value))
                elif param.param_type == "float":
                    parameters[param.name] = random.uniform(param.min_value, param.max_value)
                elif param.param_type == "choice" and param.values:
                    parameters[param.name] = random.choice(param.values)
            
            # Run training backtest
            train_results = self._run_single_backtest(parameters, 'train')
            
            if not train_results or train_results.get('trades', {}).get('total_trades', 0) < config.min_trades:
                continue
            
            # Calculate training metrics
            train_analytics = PerformanceAnalytics(train_results)
            train_metrics = train_analytics.calculate_advanced_metrics()
            train_metrics.update(train_results['summary'])
            train_metrics.update(train_results['trades'])
            
            # Get optimization score
            score = train_metrics.get(config.optimization_metric, 0)
            if not config.maximize:
                score = -score
            
            # Create result
            result = OptimizationResult(
                parameters=parameters,
                metrics=train_metrics,
                backtest_results=train_results,
                period='train',
                score=score
            )
            
            results.append(result)
            
            # Progress logging
            if (i + 1) % 100 == 0:
                logger.info(f"Completed {i + 1}/{config.max_iterations} iterations")
        
        # Sort and validate
        results.sort(key=lambda x: x.score, reverse=True)
        top_results = results[:min(20, len(results))]
        validated_results = self._validate_results(top_results, config)
        
        self.optimization_results = validated_results
        logger.info(f"Random search optimization completed. Best {config.optimization_metric}: {validated_results[0].score:.4f}")
        
        return validated_results
    
    def walk_forward_analysis(self, config: OptimizationConfig, window_size: int = 252, step_size: int = 63) -> Dict[str, Any]:
        """
        Perform walk-forward analysis
        
        Args:
            config: Optimization configuration
            window_size: Size of optimization window in days
            step_size: Step size for moving window in days
            
        Returns:
            Walk-forward analysis results
        """
        logger.info("Starting walk-forward analysis...")
        
        # Get full date range
        all_dates = set()
        for symbol in self.base_config.symbols:
            if symbol in self.market_data:
                all_dates.update(self.market_data[symbol].index)
        
        all_dates = sorted(list(all_dates))
        
        if len(all_dates) < window_size + step_size:
            raise ValueError("Not enough data for walk-forward analysis")
        
        walk_forward_results = []
        current_start = 0
        
        while current_start + window_size + step_size <= len(all_dates):
            # Define optimization period
            opt_start_date = all_dates[current_start]
            opt_end_date = all_dates[current_start + window_size - 1]
            
            # Define out-of-sample period
            oos_start_date = all_dates[current_start + window_size]
            oos_end_date = all_dates[min(current_start + window_size + step_size - 1, len(all_dates) - 1)]
            
            logger.info(f"Optimizing period: {opt_start_date} to {opt_end_date}")
            logger.info(f"Testing period: {oos_start_date} to {oos_end_date}")
            
            # Prepare data for this window
            opt_data = {}
            oos_data = {}
            
            for symbol in self.base_config.symbols:
                if symbol in self.market_data:
                    symbol_data = self.market_data[symbol]
                    opt_data[symbol] = symbol_data[(symbol_data.index >= opt_start_date) & 
                                                  (symbol_data.index <= opt_end_date)]
                    oos_data[symbol] = symbol_data[(symbol_data.index >= oos_start_date) & 
                                                  (symbol_data.index <= oos_end_date)]
            
            # Create temporary optimizer for this window
            temp_optimizer = StrategyOptimizer(self.strategy_class, self.base_config, opt_data)
            
            # Run optimization on this period
            opt_results = temp_optimizer.random_search_optimization(config)
            
            if opt_results:
                best_params = opt_results[0].parameters
                
                # Test on out-of-sample period
                oos_config = BacktestConfig(
                    start_date=oos_start_date.strftime('%Y-%m-%d'),
                    end_date=oos_end_date.strftime('%Y-%m-%d'),
                    initial_capital=self.base_config.initial_capital,
                    commission=self.base_config.commission,
                    slippage=self.base_config.slippage,
                    max_positions=self.base_config.max_positions,
                    risk_per_trade=self.base_config.risk_per_trade,
                    max_daily_loss=self.base_config.max_daily_loss,
                    timeframe=self.base_config.timeframe,
                    symbols=self.base_config.symbols
                )
                
                # Create strategy and run OOS test
                strategy = self._create_strategy_with_params(best_params)
                engine = BacktestEngine(oos_config)
                
                for symbol, data in oos_data.items():
                    prepared_data = strategy.prepare_data(data.copy(), symbol)
                    engine.load_market_data(symbol, prepared_data)
                
                engine.set_strategy(strategy.on_bar)
                oos_results = engine.run_backtest()
                
                # Store walk-forward result
                wf_result = {
                    'optimization_period': {'start': opt_start_date, 'end': opt_end_date},
                    'test_period': {'start': oos_start_date, 'end': oos_end_date},
                    'best_parameters': best_params,
                    'optimization_score': opt_results[0].score,
                    'oos_results': oos_results,
                    'oos_metrics': {}
                }
                
                if oos_results:
                    oos_analytics = PerformanceAnalytics(oos_results)
                    wf_result['oos_metrics'] = oos_analytics.calculate_advanced_metrics()
                    wf_result['oos_metrics'].update(oos_results['summary'])
                    wf_result['oos_metrics'].update(oos_results['trades'])
                
                walk_forward_results.append(wf_result)
            
            current_start += step_size
        
        # Analyze walk-forward results
        wf_analysis = self._analyze_walk_forward_results(walk_forward_results, config.optimization_metric)
        
        logger.info("Walk-forward analysis completed")
        return wf_analysis
    
    def _analyze_walk_forward_results(self, wf_results: List[Dict[str, Any]], metric: str) -> Dict[str, Any]:
        """
        Analyze walk-forward results
        
        Args:
            wf_results: Walk-forward results
            metric: Optimization metric
            
        Returns:
            Analysis summary
        """
        if not wf_results:
            return {}
        
        # Extract metrics
        opt_scores = [r['optimization_score'] for r in wf_results]
        oos_scores = [r['oos_metrics'].get(metric, 0) for r in wf_results if r['oos_metrics']]
        
        # Calculate stability metrics
        analysis = {
            'total_periods': len(wf_results),
            'optimization_scores': {
                'mean': np.mean(opt_scores),
                'std': np.std(opt_scores),
                'min': np.min(opt_scores),
                'max': np.max(opt_scores)
            },
            'oos_scores': {
                'mean': np.mean(oos_scores) if oos_scores else 0,
                'std': np.std(oos_scores) if oos_scores else 0,
                'min': np.min(oos_scores) if oos_scores else 0,
                'max': np.max(oos_scores) if oos_scores else 0
            },
            'performance_decay': 0,
            'consistency_ratio': 0,
            'results': wf_results
        }
        
        if oos_scores and opt_scores:
            # Performance decay (difference between optimization and OOS performance)
            if len(opt_scores) == len(oos_scores):
                decay_values = [opt - oos for opt, oos in zip(opt_scores, oos_scores)]
                analysis['performance_decay'] = np.mean(decay_values)
            
            # Consistency ratio (correlation between opt and OOS performance)
            if len(opt_scores) == len(oos_scores) and len(opt_scores) > 1:
                correlation = np.corrcoef(opt_scores, oos_scores)[0, 1]
                analysis['consistency_ratio'] = correlation if not np.isnan(correlation) else 0
        
        return analysis
    
    def parameter_sensitivity_analysis(self, base_parameters: Dict[str, Any], config: OptimizationConfig) -> Dict[str, Any]:
        """
        Analyze parameter sensitivity
        
        Args:
            base_parameters: Base parameter set
            config: Optimization configuration
            
        Returns:
            Sensitivity analysis results
        """
        logger.info("Starting parameter sensitivity analysis...")
        
        sensitivity_results = {}
        
        for param_config in config.parameters:
            param_name = param_config.name
            param_values = param_config.get_values()
            
            param_results = []
            
            for value in param_values:
                # Create parameter set with varied parameter
                test_params = base_parameters.copy()
                test_params[param_name] = value
                
                # Run backtest
                results = self._run_single_backtest(test_params, 'full')
                
                if results and results.get('trades', {}).get('total_trades', 0) >= config.min_trades:
                    analytics = PerformanceAnalytics(results)
                    metrics = analytics.calculate_advanced_metrics()
                    metrics.update(results['summary'])
                    metrics.update(results['trades'])
                    
                    param_results.append({
                        'value': value,
                        'metrics': metrics,
                        'score': metrics.get(config.optimization_metric, 0)
                    })
            
            if param_results:
                # Analyze sensitivity
                scores = [r['score'] for r in param_results]
                values = [r['value'] for r in param_results]
                
                sensitivity_results[param_name] = {
                    'results': param_results,
                    'score_range': max(scores) - min(scores),
                    'optimal_value': values[scores.index(max(scores))],
                    'mean_score': np.mean(scores),
                    'std_score': np.std(scores),
                    'sensitivity_coefficient': np.std(scores) / np.mean(scores) if np.mean(scores) != 0 else 0
                }
        
        logger.info("Parameter sensitivity analysis completed")
        return sensitivity_results
    
    def get_best_parameters(self) -> Dict[str, Any]:
        """Get best parameters from optimization"""
        if not self.optimization_results:
            return {}
        return self.optimization_results[0].parameters
    
    def test_best_parameters(self) -> Dict[str, Any]:
        """Test best parameters on out-of-sample data"""
        if not self.optimization_results:
            return {}
        
        best_params = self.get_best_parameters()
        logger.info(f"Testing best parameters on out-of-sample data: {best_params}")
        
        # Run test on out-of-sample data
        test_results = self._run_single_backtest(best_params, 'test')
        
        if test_results:
            test_analytics = PerformanceAnalytics(test_results)
            test_metrics = test_analytics.calculate_advanced_metrics()
            test_metrics.update(test_results['summary'])
            test_metrics.update(test_results['trades'])
            
            return {
                'parameters': best_params,
                'test_results': test_results,
                'test_metrics': test_metrics,
                'validation_score': self.optimization_results[0].score,
                'test_score': test_metrics.get('sharpe_ratio', 0)  # Use Sharpe as default test metric
            }
        
        return {}
    
    def save_optimization_results(self, filepath: str):
        """Save optimization results to file"""
        results_data = {
            'optimization_config': {
                'parameters': [
                    {
                        'name': p.name,
                        'min_value': p.min_value,
                        'max_value': p.max_value,
                        'step': p.step,
                        'param_type': p.param_type
                    } for p in getattr(self, 'last_config', {}).get('parameters', [])
                ],
                'optimization_metric': getattr(self, 'last_config', {}).get('optimization_metric', 'sharpe_ratio')
            },
            'results': [
                {
                    'rank': r.rank,
                    'parameters': r.parameters,
                    'score': r.score,
                    'metrics': r.metrics,
                    'period': r.period
                } for r in self.optimization_results[:10]  # Save top 10
            ],
            'best_parameters': self.get_best_parameters(),
            'generated_at': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)
        
        logger.info(f"Optimization results saved to {filepath}")