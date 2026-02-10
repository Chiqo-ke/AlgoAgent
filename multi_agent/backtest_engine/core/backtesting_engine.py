"""
Advanced Backtesting Engine
Comprehensive backtesting system for algorithmic trading strategies

Features:
- Strategy-agnostic testing framework
- Real market data simulation
- Comprehensive performance analytics
- Risk management validation
- Parameter optimization
- Agent-friendly API
- Detailed reporting system
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Trade:
    """Individual trade record"""
    entry_time: datetime
    exit_time: Optional[datetime] = None
    symbol: str = ""
    side: str = ""  # 'long' or 'short'
    entry_price: float = 0.0
    exit_price: float = 0.0
    quantity: float = 0.0
    commission: float = 0.0
    slippage: float = 0.0
    pnl: float = 0.0
    pnl_pct: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reason: str = ""  # exit reason
    strategy_params: Dict = None
    
    def __post_init__(self):
        if self.strategy_params is None:
            self.strategy_params = {}

@dataclass
class Position:
    """Current position state"""
    symbol: str
    side: str
    quantity: float
    entry_price: float
    entry_time: datetime
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    def update_current_price(self, price: float):
        """Update current price and unrealized PnL"""
        self.current_price = price
        if self.side == 'long':
            self.unrealized_pnl = (price - self.entry_price) * self.quantity
        else:
            self.unrealized_pnl = (self.entry_price - price) * self.quantity

@dataclass
class BacktestConfig:
    """Backtesting configuration"""
    start_date: str
    end_date: str
    initial_capital: float = 10000.0
    commission: float = 0.001  # 0.1%
    slippage: float = 0.0001   # 0.01%
    max_positions: int = 5
    risk_per_trade: float = 0.02  # 2%
    max_daily_loss: float = 0.05  # 5%
    timeframe: str = "1H"
    symbols: List[str] = None
    
    def __post_init__(self):
        if self.symbols is None:
            self.symbols = ["AAPL"]

class BacktestEngine:
    """
    Advanced backtesting engine for trading strategies
    
    Features:
    - Event-driven simulation
    - Real market data
    - Position management
    - Risk management
    - Performance analytics
    """
    
    def __init__(self, config: BacktestConfig):
        """Initialize the backtesting engine"""
        self.config = config
        self.current_time = None
        self.current_data = {}
        
        # Portfolio state
        self.cash = config.initial_capital
        self.initial_capital = config.initial_capital
        self.positions: Dict[str, Position] = {}
        self.closed_trades: List[Trade] = []
        self.open_trades: Dict[str, Trade] = {}
        
        # Performance tracking
        self.equity_curve = []
        self.daily_returns = []
        self.drawdown_curve = []
        self.max_equity = config.initial_capital
        
        # Risk management
        self.daily_pnl = 0.0
        self.last_trade_date = None
        
        # Strategy function
        self.strategy_func = None
        
        # Data storage
        self.market_data = {}
        
    def load_market_data(self, symbol: str, data: pd.DataFrame):
        """
        Load market data for backtesting
        
        Args:
            symbol: Trading symbol
            data: DataFrame with OHLCV data
        """
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in data.columns for col in required_columns):
            raise ValueError(f"Data must contain columns: {required_columns}")
        
        # Ensure datetime index
        if not isinstance(data.index, pd.DatetimeIndex):
            if 'timestamp' in data.columns:
                data.index = pd.to_datetime(data['timestamp'])
            else:
                raise ValueError("Data must have datetime index or 'timestamp' column")
        
        # Filter by date range
        start_date = pd.to_datetime(self.config.start_date)
        end_date = pd.to_datetime(self.config.end_date)
        data = data[(data.index >= start_date) & (data.index <= end_date)]
        
        self.market_data[symbol] = data
        logger.info(f"Loaded {len(data)} records for {symbol}")
        
    def set_strategy(self, strategy_func: Callable):
        """
        Set the strategy function to test
        
        Args:
            strategy_func: Function that takes (engine, current_data) and returns signals
        """
        self.strategy_func = strategy_func
        
    def get_current_price(self, symbol: str) -> float:
        """Get current price for symbol"""
        if symbol in self.current_data:
            return self.current_data[symbol]['close']
        return 0.0
    
    def get_portfolio_value(self) -> float:
        """Calculate total portfolio value"""
        total_value = self.cash
        
        for symbol, position in self.positions.items():
            current_price = self.get_current_price(symbol)
            position.update_current_price(current_price)
            total_value += position.unrealized_pnl + (position.quantity * position.entry_price)
            
        return total_value
    
    def calculate_position_size(self, symbol: str, entry_price: float, stop_loss: float) -> float:
        """
        Calculate position size based on risk management
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            stop_loss: Stop loss price
            
        Returns:
            Position size in shares/units
        """
        if stop_loss == 0 or entry_price == stop_loss:
            return 0.0
        
        portfolio_value = self.get_portfolio_value()
        risk_amount = portfolio_value * self.config.risk_per_trade
        
        price_risk = abs(entry_price - stop_loss)
        position_size = risk_amount / price_risk
        
        # Ensure we have enough cash
        required_cash = position_size * entry_price * (1 + self.config.commission)
        if required_cash > self.cash:
            position_size = self.cash / (entry_price * (1 + self.config.commission))
        
        return max(0.0, position_size)
    
    def open_position(self, symbol: str, side: str, quantity: float, 
                     stop_loss: Optional[float] = None, 
                     take_profit: Optional[float] = None,
                     reason: str = "strategy_signal") -> bool:
        """
        Open a new position
        
        Args:
            symbol: Trading symbol
            side: 'long' or 'short'
            quantity: Position size
            stop_loss: Stop loss price
            take_profit: Take profit price
            reason: Entry reason
            
        Returns:
            True if position opened successfully
        """
        if symbol in self.positions:
            logger.warning(f"Position already exists for {symbol}")
            return False
        
        if len(self.positions) >= self.config.max_positions:
            logger.warning(f"Maximum positions ({self.config.max_positions}) reached")
            return False
        
        current_price = self.get_current_price(symbol)
        if current_price == 0:
            logger.error(f"No price data available for {symbol}")
            return False
        
        # Apply slippage
        if side == 'long':
            entry_price = current_price * (1 + self.config.slippage)
        else:
            entry_price = current_price * (1 - self.config.slippage)
        
        # Calculate costs
        commission_cost = quantity * entry_price * self.config.commission
        total_cost = quantity * entry_price + commission_cost
        
        # Check if we have enough cash
        if total_cost > self.cash:
            logger.warning(f"Insufficient cash for {symbol} position. Required: {total_cost:.2f}, Available: {self.cash:.2f}")
            return False
        
        # Create position
        position = Position(
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=entry_price,
            entry_time=self.current_time,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        # Create trade record
        trade = Trade(
            entry_time=self.current_time,
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            quantity=quantity,
            commission=commission_cost,
            slippage=entry_price - current_price,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        # Update portfolio
        self.positions[symbol] = position
        self.open_trades[symbol] = trade
        self.cash -= total_cost
        
        logger.info(f"Opened {side} position: {symbol} @ {entry_price:.4f}, Size: {quantity:.2f}")
        return True
    
    def close_position(self, symbol: str, reason: str = "strategy_exit") -> bool:
        """
        Close an existing position
        
        Args:
            symbol: Trading symbol
            reason: Exit reason
            
        Returns:
            True if position closed successfully
        """
        if symbol not in self.positions:
            logger.warning(f"No position to close for {symbol}")
            return False
        
        position = self.positions[symbol]
        trade = self.open_trades[symbol]
        
        current_price = self.get_current_price(symbol)
        
        # Apply slippage
        if position.side == 'long':
            exit_price = current_price * (1 - self.config.slippage)
        else:
            exit_price = current_price * (1 + self.config.slippage)
        
        # Calculate PnL
        if position.side == 'long':
            gross_pnl = (exit_price - position.entry_price) * position.quantity
        else:
            gross_pnl = (position.entry_price - exit_price) * position.quantity
        
        # Calculate costs
        commission_cost = position.quantity * exit_price * self.config.commission
        net_pnl = gross_pnl - commission_cost - trade.commission
        
        # Update cash
        proceeds = position.quantity * exit_price - commission_cost
        self.cash += proceeds
        
        # Complete trade record
        trade.exit_time = self.current_time
        trade.exit_price = exit_price
        trade.pnl = net_pnl
        trade.pnl_pct = net_pnl / (position.entry_price * position.quantity) * 100
        trade.reason = reason
        trade.commission += commission_cost
        trade.slippage += abs(exit_price - current_price)
        
        # Move to closed trades
        self.closed_trades.append(trade)
        
        # Remove from open positions
        del self.positions[symbol]
        del self.open_trades[symbol]
        
        # Update daily PnL
        self.daily_pnl += net_pnl
        
        logger.info(f"Closed {position.side} position: {symbol} @ {exit_price:.4f}, PnL: {net_pnl:.2f}")
        return True
    
    def check_stop_loss_take_profit(self):
        """Check and execute stop loss and take profit orders"""
        positions_to_close = []
        
        for symbol, position in self.positions.items():
            current_price = self.get_current_price(symbol)
            
            # Check stop loss
            if position.stop_loss:
                if position.side == 'long' and current_price <= position.stop_loss:
                    positions_to_close.append((symbol, "stop_loss"))
                elif position.side == 'short' and current_price >= position.stop_loss:
                    positions_to_close.append((symbol, "stop_loss"))
            
            # Check take profit
            if position.take_profit:
                if position.side == 'long' and current_price >= position.take_profit:
                    positions_to_close.append((symbol, "take_profit"))
                elif position.side == 'short' and current_price <= position.take_profit:
                    positions_to_close.append((symbol, "take_profit"))
        
        # Close positions
        for symbol, reason in positions_to_close:
            self.close_position(symbol, reason)
    
    def check_risk_limits(self) -> bool:
        """
        Check if risk limits are breached
        
        Returns:
            True if trading should continue, False if limits breached
        """
        # Check daily loss limit
        if self.last_trade_date != self.current_time.date():
            self.daily_pnl = 0.0
            self.last_trade_date = self.current_time.date()
        
        portfolio_value = self.get_portfolio_value()
        daily_loss_limit = self.initial_capital * self.config.max_daily_loss
        
        if self.daily_pnl < -daily_loss_limit:
            logger.warning(f"Daily loss limit breached: {self.daily_pnl:.2f}")
            # Close all positions
            for symbol in list(self.positions.keys()):
                self.close_position(symbol, "risk_limit")
            return False
        
        return True
    
    def update_equity_curve(self):
        """Update equity curve and drawdown calculation"""
        portfolio_value = self.get_portfolio_value()
        
        self.equity_curve.append({
            'timestamp': self.current_time,
            'equity': portfolio_value,
            'cash': self.cash,
            'positions_value': portfolio_value - self.cash
        })
        
        # Update max equity and drawdown
        if portfolio_value > self.max_equity:
            self.max_equity = portfolio_value
        
        drawdown = (self.max_equity - portfolio_value) / self.max_equity * 100
        self.drawdown_curve.append({
            'timestamp': self.current_time,
            'drawdown': drawdown
        })
        
        # Calculate daily return
        if len(self.equity_curve) > 1:
            prev_equity = self.equity_curve[-2]['equity']
            daily_return = (portfolio_value - prev_equity) / prev_equity * 100
            self.daily_returns.append({
                'timestamp': self.current_time,
                'return': daily_return
            })
    
    def run_backtest(self) -> Dict[str, Any]:
        """
        Run the backtesting simulation
        
        Returns:
            Backtesting results dictionary
        """
        if not self.strategy_func:
            raise ValueError("No strategy function set")
        
        if not self.market_data:
            raise ValueError("No market data loaded")
        
        logger.info("Starting backtesting simulation...")
        logger.info(f"Period: {self.config.start_date} to {self.config.end_date}")
        logger.info(f"Initial capital: ${self.config.initial_capital:,.2f}")
        
        # Get all timestamps across all symbols
        all_timestamps = set()
        for symbol, data in self.market_data.items():
            all_timestamps.update(data.index)
        
        # Sort timestamps
        timestamps = sorted(all_timestamps)
        
        # Run simulation
        for i, timestamp in enumerate(timestamps):
            self.current_time = timestamp
            
            # Update current data for all symbols
            self.current_data = {}
            for symbol, data in self.market_data.items():
                if timestamp in data.index:
                    self.current_data[symbol] = data.loc[timestamp].to_dict()
            
            # Skip if no data available
            if not self.current_data:
                continue
            
            # Update position prices and check risk management
            self.check_stop_loss_take_profit()
            
            # Check risk limits
            if not self.check_risk_limits():
                logger.warning("Risk limits breached, stopping backtest")
                break
            
            # Run strategy
            try:
                self.strategy_func(self, self.current_data)
            except Exception as e:
                logger.error(f"Strategy error at {timestamp}: {e}")
                continue
            
            # Update performance tracking
            self.update_equity_curve()
            
            # Progress logging
            if i % 1000 == 0:
                portfolio_value = self.get_portfolio_value()
                logger.info(f"Progress: {i}/{len(timestamps)}, Portfolio: ${portfolio_value:,.2f}")
        
        # Close all remaining positions
        for symbol in list(self.positions.keys()):
            self.close_position(symbol, "backtest_end")
        
        logger.info("Backtesting simulation completed")
        
        # Return results
        return self.get_results()
    
    def get_results(self) -> Dict[str, Any]:
        """
        Get comprehensive backtesting results
        
        Returns:
            Dictionary containing all results and metrics
        """
        final_equity = self.get_portfolio_value()
        total_return = (final_equity - self.initial_capital) / self.initial_capital * 100
        
        # Trade statistics
        winning_trades = [t for t in self.closed_trades if t.pnl > 0]
        losing_trades = [t for t in self.closed_trades if t.pnl < 0]
        
        win_rate = len(winning_trades) / len(self.closed_trades) * 100 if self.closed_trades else 0
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        
        profit_factor = abs(sum(t.pnl for t in winning_trades) / sum(t.pnl for t in losing_trades)) if losing_trades else float('inf')
        
        # Calculate Sharpe ratio (simplified)
        if self.daily_returns:
            returns_series = [r['return'] for r in self.daily_returns]
            sharpe_ratio = np.mean(returns_series) / np.std(returns_series) * np.sqrt(252) if np.std(returns_series) > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Maximum drawdown
        max_drawdown = max([d['drawdown'] for d in self.drawdown_curve]) if self.drawdown_curve else 0
        
        results = {
            'summary': {
                'start_date': self.config.start_date,
                'end_date': self.config.end_date,
                'initial_capital': self.initial_capital,
                'final_equity': final_equity,
                'total_return': total_return,
                'total_return_pct': total_return,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'profit_factor': profit_factor
            },
            'trades': {
                'total_trades': len(self.closed_trades),
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': win_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'largest_win': max([t.pnl for t in self.closed_trades]) if self.closed_trades else 0,
                'largest_loss': min([t.pnl for t in self.closed_trades]) if self.closed_trades else 0
            },
            'equity_curve': self.equity_curve,
            'drawdown_curve': self.drawdown_curve,
            'daily_returns': self.daily_returns,
            'closed_trades': [asdict(trade) for trade in self.closed_trades],
            'config': asdict(self.config)
        }
        
        return results

    def save_results(self, results: Dict[str, Any], filepath: str):
        """Save results to file"""
        # Convert datetime objects to strings for JSON serialization
        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=serialize_datetime)
        
        logger.info(f"Results saved to {filepath}")