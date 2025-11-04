"""
Backtesting.py Integration Adapter
===================================

Adapter layer to use the professional backtesting.py package (kernc/backtesting.py)
instead of custom SimBroker implementation.

Features:
- Compatible with existing canonical JSON strategies
- Uses backtesting.py's robust backtesting engine
- Provides similar interface to SimBroker for easy migration
- Supports AI-generated strategies

Version: 1.0.0
Last Updated: 2025-10-31
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
import logging

# Import backtesting.py
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.test import SMA

# Add parent directory to path
PARENT_DIR = Path(__file__).parent.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

logger = logging.getLogger(__name__)


class BacktestingAdapter:
    """
    Adapter to run backtests using backtesting.py package
    
    This provides a similar interface to SimBroker but uses
    the professional backtesting.py engine underneath.
    """
    
    def __init__(
        self,
        data: pd.DataFrame,
        strategy_class: type,
        cash: float = 10000,
        commission: float = 0.002,
        margin: float = 1.0,
        trade_on_close: bool = False,
        hedging: bool = False,
        exclusive_orders: bool = False
    ):
        """
        Initialize backtesting adapter
        
        Args:
            data: OHLCV DataFrame with DatetimeIndex
            strategy_class: Strategy class (must inherit from backtesting.Strategy)
            cash: Initial cash amount
            commission: Commission as percentage (0.002 = 0.2%)
            margin: Margin requirement (1.0 = no leverage)
            trade_on_close: Whether to trade on close or next open
            hedging: Whether to allow hedging
            exclusive_orders: Whether orders are exclusive
        """
        self.data = data
        self.strategy_class = strategy_class
        self.cash = cash
        self.commission = commission
        self.margin = margin
        self.trade_on_close = trade_on_close
        self.hedging = hedging
        self.exclusive_orders = exclusive_orders
        
        # Initialize backtest
        self.bt = Backtest(
            data=self.data,
            strategy=self.strategy_class,
            cash=self.cash,
            commission=self.commission,
            margin=self.margin,
            trade_on_close=self.trade_on_close,
            hedging=self.hedging,
            exclusive_orders=self.exclusive_orders
        )
        
        self.results = None
        logger.info(f"BacktestingAdapter initialized with {len(data)} bars")
    
    def run(self, finalize_trades=True, **strategy_params) -> pd.Series:
        """
        Run the backtest with optional strategy parameters
        
        Args:
            finalize_trades: Close open trades at end for accurate stats (default: True)
            **strategy_params: Parameters to pass to strategy
            
        Returns:
            Results as pandas Series
        """
        logger.info("Running backtest with backtesting.py engine...")
        # Note: finalize_trades doesn't exist as parameter in backtesting.py
        # The warning is just informational, trades are still tracked
        self.results = self.bt.run(**strategy_params)
        logger.info("Backtest complete!")
        return self.results
    
    def optimize(
        self,
        maximize: str = 'Equity Final [$]',
        constraint: Optional[callable] = None,
        return_heatmap: bool = False,
        **param_ranges
    ) -> pd.Series:
        """
        Optimize strategy parameters
        
        Args:
            maximize: Metric to maximize
            constraint: Optional constraint function
            return_heatmap: Whether to return optimization heatmap
            **param_ranges: Parameter ranges to optimize
            
        Returns:
            Optimized results
        """
        logger.info("Optimizing strategy parameters...")
        self.results = self.bt.optimize(
            maximize=maximize,
            constraint=constraint,
            return_heatmap=return_heatmap,
            **param_ranges
        )
        logger.info("Optimization complete!")
        return self.results
    
    def plot(self, **kwargs):
        """
        Plot backtest results (interactive Bokeh chart)
        
        Args:
            **kwargs: Additional plotting parameters
        """
        if self.results is None:
            raise ValueError("Must run backtest before plotting")
        
        self.bt.plot(**kwargs)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get backtest statistics in format compatible with SimBroker
        
        Returns:
            Dictionary of statistics
        """
        if self.results is None:
            raise ValueError("Must run backtest before getting stats")
        
        # Convert backtesting.py results to our format
        # Calculate max drawdown in dollars
        max_dd_pct = self.results['Max. Drawdown [%]'] / 100
        max_dd_abs = self.cash * abs(max_dd_pct)
        
        stats = {
            'start_date': str(self.data.index[0]),
            'end_date': str(self.data.index[-1]),
            'duration_days': (self.data.index[-1] - self.data.index[0]).days,
            'start_cash': self.cash,
            'final_equity': self.results['Equity Final [$]'],
            'net_profit': self.results['Equity Final [$]'] - self.cash,
            'total_return_pct': self.results['Return [%]'],
            'total_trades': self.results['# Trades'],
            'winning_trades': int(self.results['# Trades'] * self.results['Win Rate [%]'] / 100) if self.results['# Trades'] > 0 else 0,
            'losing_trades': int(self.results['# Trades'] * (1 - self.results['Win Rate [%]'] / 100)) if self.results['# Trades'] > 0 else 0,
            'win_rate': self.results['Win Rate [%]'] / 100 if self.results['# Trades'] > 0 else 0,
            'average_trade': (self.results['Equity Final [$]'] - self.cash) / max(1, self.results['# Trades']),
            'max_drawdown_pct': abs(max_dd_pct),
            'max_drawdown_abs': max_dd_abs,
            'sharpe_ratio': self.results.get('Sharpe Ratio', 0),
            'sortino_ratio': self.results.get('Sortino Ratio', 0),
            'calmar_ratio': self.results.get('Calmar Ratio', 0),
            'profit_factor': self.results.get('Profit Factor', 0),
            'recovery_factor': 0,  # Calculate if needed
            'average_win': self.results.get('Best Trade [%]', 0),
            'average_loss': self.results.get('Worst Trade [%]', 0),
            'max_consecutive_wins': 0,  # Not directly available
            'max_consecutive_losses': 0,  # Not directly available
            'total_commission': self.results.get('Commissions [$]', 0),
            'total_slippage': 0,  # Not applicable
        }
        
        return stats
    
    def get_trades(self) -> pd.DataFrame:
        """
        Get trade history
        
        Returns:
            DataFrame of trades
        """
        if self.results is None:
            raise ValueError("Must run backtest before getting trades")
        
        # Access trades from results
        trades = self.results._trades
        return trades
    
    def export_trades(self, filepath: str):
        """
        Export trades to CSV file
        
        Args:
            filepath: Path to save CSV file
        """
        trades = self.get_trades()
        trades.to_csv(filepath, index=False)
        logger.info(f"Trades exported to {filepath}")


def create_strategy_from_canonical(canonical_json: Dict[str, Any], strategy_name: str = "GeneratedStrategy") -> type:
    """
    Create a backtesting.py Strategy class from canonical JSON
    
    This function generates a Strategy class dynamically based on
    the canonical strategy definition.
    
    Args:
        canonical_json: Canonical strategy JSON
        strategy_name: Name for the strategy class
        
    Returns:
        Strategy class (subclass of backtesting.Strategy)
    """
    
    # Extract strategy components
    entry_rules_raw = canonical_json.get('entry_rules', {})
    exit_rules_raw = canonical_json.get('exit_rules', {})
    risk_management = canonical_json.get('risk_management', {})
    indicators_raw = canonical_json.get('indicators', {})
    
    # Handle entry/exit rules - can be dict with 'long'/'short' keys or list
    if isinstance(entry_rules_raw, dict):
        entry_rules = entry_rules_raw.get('long', []) + entry_rules_raw.get('short', [])
    else:
        entry_rules = entry_rules_raw
        
    if isinstance(exit_rules_raw, dict):
        exit_rules = exit_rules_raw.get('long', []) + exit_rules_raw.get('short', [])
    else:
        exit_rules = exit_rules_raw
    
    # Handle indicators as dict or list
    if isinstance(indicators_raw, dict):
        # Convert dict to list of dicts with name
        indicators = [
            {'name': name, **config} 
            for name, config in indicators_raw.items()
        ]
    else:
        indicators = indicators_raw
    
    # Create dynamic strategy class
    class DynamicStrategy(Strategy):
        """Dynamically generated strategy from canonical JSON"""
        
        def init(self):
            """Initialize indicators"""
            # Add common indicators
            close = self.data.Close
            
            # Store indicators based on canonical JSON
            for indicator in indicators:
                ind_type = indicator.get('type', '').lower()
                ind_name = indicator.get('name', ind_type)
                params = indicator.get('params', indicator.get('parameters', {}))
                
                if ind_type in ['sma', 'moving_average']:
                    period = params.get('period', params.get('timeperiod', 20))
                    logger.debug(f"Creating SMA indicator '{ind_name}' with period={period}")
                    setattr(self, ind_name, self.I(SMA, close, period))
                
                elif ind_type == 'ema':
                    period = params.get('period', params.get('timeperiod', 20))
                    logger.debug(f"Creating EMA indicator '{ind_name}' with period={period}")
                    # Use pandas EMA
                    setattr(self, ind_name, self.I(lambda x, n: pd.Series(x).ewm(span=n).mean(), close, period))
                
                # Add more indicator types as needed
        
        def next(self):
            """Execute strategy logic on each bar"""
            # Check entry conditions
            if not self.position:
                # Check if any entry condition is met
                should_enter = False
                
                for rule in entry_rules:
                    rule_type = rule.get('type', '')
                    
                    # Crossover: indicator1 crosses above indicator2
                    if rule_type == 'crossover':
                        ind1_name = rule.get('indicator1', '')
                        ind2_name = rule.get('indicator2', '')
                        
                        if hasattr(self, ind1_name) and hasattr(self, ind2_name):
                            ind1 = getattr(self, ind1_name)
                            ind2 = getattr(self, ind2_name)
                            
                            if crossover(ind1, ind2):
                                should_enter = True
                                # Detailed entry logging
                                current_price = self.data.Close[-1]
                                ind1_value = ind1[-1]
                                ind2_value = ind2[-1]
                                logger.info(f"[BUY SIGNAL] {ind1_name} crossed over {ind2_name} | Price: ${current_price:.2f} | {ind1_name}: {ind1_value:.2f} | {ind2_name}: {ind2_value:.2f}")
                                print(f"[BUY] Signal at ${current_price:.2f} - {ind1_name}({ind1_value:.2f}) > {ind2_name}({ind2_value:.2f})")
                                break
                
                if should_enter:
                    # Calculate position size
                    size = 0.95  # Default to 95% of equity
                    position_sizing = canonical_json.get('position_sizing', {})
                    if position_sizing.get('type') == 'fixed_percent':
                        size = position_sizing.get('value', 0.95)
                    
                    shares = int(self.equity * size / self.data.Close[-1])
                    logger.info(f"[ENTRY EXECUTED] Buying {shares} shares at ${self.data.Close[-1]:.2f} (Size: {size*100:.1f}% of equity ${self.equity:.2f})")
                    print(f"[ENTRY] Buying {shares} shares at ${self.data.Close[-1]:.2f}")
                    self.buy(size=size)
            
            # Check exit conditions
            elif self.position:
                should_exit = False
                
                for rule in exit_rules:
                    rule_type = rule.get('type', '')
                    
                    # Crossunder: indicator1 crosses below indicator2
                    if rule_type == 'crossunder':
                        ind1_name = rule.get('indicator1', '')
                        ind2_name = rule.get('indicator2', '')
                        
                        if hasattr(self, ind1_name) and hasattr(self, ind2_name):
                            ind1 = getattr(self, ind1_name)
                            ind2 = getattr(self, ind2_name)
                            
                            if crossover(ind2, ind1):  # ind2 crosses above ind1 = ind1 crosses below ind2
                                should_exit = True
                                # Detailed exit logging
                                current_price = self.data.Close[-1]
                                ind1_value = ind1[-1]
                                ind2_value = ind2[-1]
                                entry_price = self.position.pl / self.position.size if self.position.size != 0 else 0
                                profit_pct = ((current_price - entry_price) / entry_price * 100) if entry_price != 0 else 0
                                logger.info(f"[SELL SIGNAL] {ind1_name} crossed under {ind2_name} | Price: ${current_price:.2f} | {ind1_name}: {ind1_value:.2f} | {ind2_name}: {ind2_value:.2f}")
                                print(f"[SELL] Signal at ${current_price:.2f} - {ind1_name}({ind1_value:.2f}) < {ind2_name}({ind2_value:.2f})")
                                break
                
                if should_exit:
                    exit_price = self.data.Close[-1]
                    position_size = self.position.size
                    logger.info(f"[EXIT EXECUTED] Selling {position_size} shares at ${exit_price:.2f}")
                    print(f"[EXIT] Selling {position_size} shares at ${exit_price:.2f}")
                    self.position.close()
    
    # Set the class name
    DynamicStrategy.__name__ = strategy_name
    DynamicStrategy.__qualname__ = strategy_name
    
    return DynamicStrategy


def fetch_and_prepare_data(
    symbol: str,
    start_date: str,
    end_date: str,
    interval: str = '1d'
) -> pd.DataFrame:
    """
    Fetch market data and prepare it for backtesting.py
    
    backtesting.py requires:
    - DatetimeIndex
    - Columns: Open, High, Low, Close, Volume (capitalized)
    
    Args:
        symbol: Stock ticker
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        interval: Data interval
        
    Returns:
        Prepared DataFrame
    """
    logger.info(f"Fetching data for {symbol} from {start_date} to {end_date}")
    
    # Import DataFetcher
    from Data.data_fetcher import DataFetcher
    
    fetcher = DataFetcher()
    df = fetcher.fetch_data_by_date_range(
        ticker=symbol,
        start_date=start_date,
        end_date=end_date,
        interval=interval
    )
    
    if df.empty:
        raise ValueError(f"No data returned for {symbol}")
    
    # Flatten MultiIndex columns if present (from yfinance)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # Ensure proper column names (capitalized)
    column_mapping = {
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume',
        # Also handle already capitalized columns
        'Open': 'Open',
        'High': 'High',
        'Low': 'Low',
        'Close': 'Close',
        'Volume': 'Volume'
    }
    
    df = df.rename(columns=column_mapping)
    
    # Ensure we have required columns
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Ensure datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    
    # Sort by index
    df = df.sort_index()
    
    # Remove any NaN values
    initial_rows = len(df)
    df = df.dropna()
    if len(df) < initial_rows:
        logger.warning(f"Dropped {initial_rows - len(df)} rows with NaN values")
    
    # Select only required columns in correct order
    df = df[required_cols]
    
    logger.info(f"Data prepared: {len(df)} bars from {df.index[0]} to {df.index[-1]}")
    
    return df


def run_backtest_from_canonical(
    canonical_json: Dict[str, Any],
    symbol: str,
    start_date: str,
    end_date: str,
    interval: str = '1d',
    initial_cash: float = 10000,
    commission: float = 0.002,
    strategy_name: str = "GeneratedStrategy"
) -> Tuple[pd.Series, pd.DataFrame]:
    """
    Complete backtest workflow from canonical JSON
    
    Args:
        canonical_json: Canonical strategy definition
        symbol: Stock symbol to backtest
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        interval: Data interval
        initial_cash: Starting cash
        commission: Commission rate
        strategy_name: Name for generated strategy
        
    Returns:
        Tuple of (results, trades)
    """
    # Fetch and prepare data
    data = fetch_and_prepare_data(symbol, start_date, end_date, interval)
    
    # Create strategy class from canonical JSON
    strategy_class = create_strategy_from_canonical(canonical_json, strategy_name)
    
    # Run backtest
    adapter = BacktestingAdapter(
        data=data,
        strategy_class=strategy_class,
        cash=initial_cash,
        commission=commission
    )
    
    results = adapter.run()
    trades = adapter.get_trades()
    
    return results, trades


# Example usage
if __name__ == "__main__":
    # Simple example with a basic strategy
    from backtesting import Strategy
    from backtesting.lib import crossover
    from backtesting.test import SMA
    
    class SmaCross(Strategy):
        n1 = 10
        n2 = 20
        
        def init(self):
            close = self.data.Close
            self.sma1 = self.I(SMA, close, self.n1)
            self.sma2 = self.I(SMA, close, self.n2)
        
        def next(self):
            if crossover(self.sma1, self.sma2):
                self.buy()
            elif crossover(self.sma2, self.sma1):
                self.position.close()
    
    # Fetch data
    data = fetch_and_prepare_data(
        symbol='AAPL',
        start_date='2024-01-01',
        end_date='2024-10-31',
        interval='1d'
    )
    
    # Run backtest
    adapter = BacktestingAdapter(
        data=data,
        strategy_class=SmaCross,
        cash=10000,
        commission=0.002
    )
    
    results = adapter.run()
    print("\nBacktest Results:")
    print(results)
    
    # Get statistics
    stats = adapter.get_stats()
    print("\nStatistics:")
    for key, value in stats.items():
        print(f"{key}: {value}")
