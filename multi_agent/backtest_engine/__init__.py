"""
Advanced Backtesting Engine for Algorithmic Trading
Comprehensive backtesting system for strategy development and optimization
"""

from .api import (
    BacktestAPI,
    bt_api,
    quick_test,
    optimize_momentum_strategy,
    create_and_test_strategy,
    compare_momentum_vs_custom
)

from .core.backtesting_engine import BacktestEngine, BacktestConfig, Trade, Position
from .core.strategy_framework import (
    BaseStrategy,
    StrategyParams,
    MomentumStrategy,
    TechnicalIndicators,
    StrategyTester
)

from .analytics.performance_analytics import (
    PerformanceAnalytics,
    ReportGenerator,
    BenchmarkComparison
)

from .optimization.optimizer import (
    StrategyOptimizer,
    OptimizationConfig,
    OptimizationParameter,
    OptimizationResult
)

__version__ = "1.0.0"
__author__ = "AlgoAgent Multi-Agent System"

# Make the API easily accessible
api = bt_api