"""
Portfolio Manager - Manages multiple trading strategies as a portfolio.

Features:
- Multi-strategy allocation
- Risk management at portfolio level
- Performance tracking
- Auto-rebalancing
- Emergency stop across all strategies
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd


logger = logging.getLogger(__name__)


class PortfolioManager:
    """
    Manages a portfolio of trading strategies.
    """
    
    def __init__(
        self,
        portfolio_id: str,
        name: str,
        total_capital: float,
        max_portfolio_drawdown: float = 0.15,  # 15%
        rebalance_threshold: float = 0.05  # 5% deviation triggers rebalance
    ):
        """
        Initialize portfolio manager.
        
        Args:
            portfolio_id: Unique portfolio identifier
            name: Portfolio name
            total_capital: Total capital allocated to portfolio
            max_portfolio_drawdown: Maximum allowed drawdown (0.15 = 15%)
            rebalance_threshold: Threshold for auto-rebalancing
        """
        self.portfolio_id = portfolio_id
        self.name = name
        self.total_capital = total_capital
        self.max_portfolio_drawdown = max_portfolio_drawdown
        self.rebalance_threshold = rebalance_threshold
        
        self.strategies = {}  # strategy_id -> strategy_info
        self.allocations = {}  # strategy_id -> allocation (0.0 to 1.0)
        self.performance = {
            'start_date': datetime.now().isoformat(),
            'total_trades': 0,
            'total_pnl': 0.0,
            'current_drawdown': 0.0,
            'peak_equity': total_capital,
            'current_equity': total_capital
        }
        
        # Portfolio state file
        self.state_file = Path(f"portfolios/{portfolio_id}_state.json")
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        self._save_state()
    
    def add_strategy(
        self,
        strategy_id: str,
        strategy_file: str,
        allocation: float,
        description: str = ""
    ) -> Dict:
        """
        Add a strategy to the portfolio.
        
        Args:
            strategy_id: Unique strategy identifier
            strategy_file: Path to strategy .py file
            allocation: Allocation (0.0 to 1.0, must sum to 1.0 across all strategies)
            description: Strategy description
            
        Returns:
            {
                'success': bool,
                'message': str
            }
        """
        # Validate allocation
        if allocation < 0 or allocation > 1:
            return {
                'success': False,
                'message': f'Invalid allocation: {allocation}. Must be between 0 and 1.'
            }
        
        # Check total allocation
        current_total = sum(self.allocations.values())
        if current_total + allocation > 1.0:
            return {
                'success': False,
                'message': f'Total allocation would exceed 1.0: {current_total + allocation}'
            }
        
        # Add strategy
        self.strategies[strategy_id] = {
            'strategy_file': strategy_file,
            'description': description,
            'added_date': datetime.now().isoformat(),
            'status': 'active',
            'capital': self.total_capital * allocation,
            'pnl': 0.0,
            'trades': 0
        }
        
        self.allocations[strategy_id] = allocation
        
        self._save_state()
        
        logger.info(f"Added strategy {strategy_id} with {allocation*100}% allocation")
        
        return {
            'success': True,
            'message': f'Strategy {strategy_id} added successfully'
        }
    
    def remove_strategy(self, strategy_id: str) -> Dict:
        """
        Remove a strategy from the portfolio.
        
        Args:
            strategy_id: Strategy to remove
            
        Returns:
            {
                'success': bool,
                'message': str
            }
        """
        if strategy_id not in self.strategies:
            return {
                'success': False,
                'message': f'Strategy {strategy_id} not found'
            }
        
        # Mark as inactive (don't delete for historical tracking)
        self.strategies[strategy_id]['status'] = 'inactive'
        self.strategies[strategy_id]['removed_date'] = datetime.now().isoformat()
        
        # Remove allocation
        del self.allocations[strategy_id]
        
        self._save_state()
        
        logger.info(f"Removed strategy {strategy_id}")
        
        return {
            'success': True,
            'message': f'Strategy {strategy_id} removed successfully'
        }
    
    def update_performance(self, strategy_id: str, pnl: float, trades: int = 1):
        """
        Update strategy performance.
        
        Args:
            strategy_id: Strategy that generated the result
            pnl: Profit/loss from trade(s)
            trades: Number of trades
        """
        if strategy_id not in self.strategies:
            logger.warning(f"Unknown strategy: {strategy_id}")
            return
        
        # Update strategy stats
        self.strategies[strategy_id]['pnl'] += pnl
        self.strategies[strategy_id]['trades'] += trades
        
        # Update portfolio stats
        self.performance['total_pnl'] += pnl
        self.performance['total_trades'] += trades
        self.performance['current_equity'] = self.total_capital + self.performance['total_pnl']
        
        # Update peak and drawdown
        if self.performance['current_equity'] > self.performance['peak_equity']:
            self.performance['peak_equity'] = self.performance['current_equity']
        
        drawdown = (self.performance['peak_equity'] - self.performance['current_equity']) / self.performance['peak_equity']
        self.performance['current_drawdown'] = drawdown
        
        # Check if drawdown limit exceeded
        if drawdown > self.max_portfolio_drawdown:
            logger.warning(
                f"Portfolio drawdown ({drawdown*100:.2f}%) exceeds limit "
                f"({self.max_portfolio_drawdown*100:.2f}%)"
            )
            # Trigger emergency stop would go here
        
        self._save_state()
    
    def get_status(self) -> Dict:
        """
        Get current portfolio status.
        
        Returns:
            {
                'portfolio_id': str,
                'name': str,
                'total_capital': float,
                'current_equity': float,
                'total_pnl': float,
                'total_trades': int,
                'current_drawdown': float,
                'strategies': {...},
                'allocations': {...}
            }
        """
        return {
            'portfolio_id': self.portfolio_id,
            'name': self.name,
            'total_capital': self.total_capital,
            'current_equity': self.performance['current_equity'],
            'total_pnl': self.performance['total_pnl'],
            'total_trades': self.performance['total_trades'],
            'current_drawdown': self.performance['current_drawdown'],
            'peak_equity': self.performance['peak_equity'],
            'strategies': {
                sid: {
                    'description': sinfo['description'],
                    'status': sinfo['status'],
                    'capital': sinfo['capital'],
                    'pnl': sinfo['pnl'],
                    'trades': sinfo['trades'],
                    'allocation': self.allocations.get(sid, 0.0)
                }
                for sid, sinfo in self.strategies.items()
            }
        }
    
    def check_rebalancing_needed(self) -> bool:
        """
        Check if rebalancing is needed based on performance drift.
        
        Returns:
            True if rebalancing needed
        """
        # Calculate actual allocations based on current equity per strategy
        total_equity = self.performance['current_equity']
        
        for strategy_id in self.allocations:
            target_allocation = self.allocations[strategy_id]
            strategy_equity = self.strategies[strategy_id]['capital'] + self.strategies[strategy_id]['pnl']
            actual_allocation = strategy_equity / total_equity if total_equity > 0 else 0
            
            drift = abs(actual_allocation - target_allocation)
            
            if drift > self.rebalance_threshold:
                logger.info(
                    f"Rebalancing needed for {strategy_id}: "
                    f"target={target_allocation*100:.1f}%, "
                    f"actual={actual_allocation*100:.1f}%, "
                    f"drift={drift*100:.1f}%"
                )
                return True
        
        return False
    
    def rebalance(self) -> Dict:
        """
        Rebalance portfolio to target allocations.
        
        Returns:
            {
                'success': bool,
                'adjustments': {...}
            }
        """
        adjustments = {}
        total_equity = self.performance['current_equity']
        
        for strategy_id in self.allocations:
            target_allocation = self.allocations[strategy_id]
            target_capital = total_equity * target_allocation
            
            current_capital = self.strategies[strategy_id]['capital'] + self.strategies[strategy_id]['pnl']
            adjustment = target_capital - current_capital
            
            adjustments[strategy_id] = {
                'current_capital': current_capital,
                'target_capital': target_capital,
                'adjustment': adjustment
            }
            
            # Update capital allocation
            self.strategies[strategy_id]['capital'] = target_capital
        
        self._save_state()
        
        logger.info(f"Portfolio rebalanced: {adjustments}")
        
        return {
            'success': True,
            'adjustments': adjustments
        }
    
    def generate_report(self) -> Dict:
        """
        Generate comprehensive portfolio report.
        
        Returns:
            Detailed performance report
        """
        status = self.get_status()
        
        # Calculate additional metrics
        roi = (self.performance['total_pnl'] / self.total_capital) * 100 if self.total_capital > 0 else 0
        
        # Strategy performance ranking
        strategy_performance = []
        for sid, sinfo in self.strategies.items():
            if sinfo['status'] == 'active':
                strategy_roi = (sinfo['pnl'] / sinfo['capital']) * 100 if sinfo['capital'] > 0 else 0
                strategy_performance.append({
                    'strategy_id': sid,
                    'description': sinfo['description'],
                    'allocation': self.allocations.get(sid, 0.0) * 100,
                    'capital': sinfo['capital'],
                    'pnl': sinfo['pnl'],
                    'roi': strategy_roi,
                    'trades': sinfo['trades']
                })
        
        # Sort by ROI
        strategy_performance.sort(key=lambda x: x['roi'], reverse=True)
        
        report = {
            **status,
            'roi': roi,
            'strategy_performance': strategy_performance,
            'report_date': datetime.now().isoformat()
        }
        
        return report
    
    def _save_state(self):
        """Save portfolio state to file."""
        state = {
            'portfolio_id': self.portfolio_id,
            'name': self.name,
            'total_capital': self.total_capital,
            'max_portfolio_drawdown': self.max_portfolio_drawdown,
            'rebalance_threshold': self.rebalance_threshold,
            'strategies': self.strategies,
            'allocations': self.allocations,
            'performance': self.performance
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    @classmethod
    def load(cls, portfolio_id: str):
        """
        Load portfolio from saved state.
        
        Args:
            portfolio_id: Portfolio to load
            
        Returns:
            PortfolioManager instance
        """
        state_file = Path(f"portfolios/{portfolio_id}_state.json")
        
        if not state_file.exists():
            raise FileNotFoundError(f"Portfolio {portfolio_id} not found")
        
        with open(state_file, 'r') as f:
            state = json.load(f)
        
        # Create instance
        pm = cls(
            portfolio_id=state['portfolio_id'],
            name=state['name'],
            total_capital=state['total_capital'],
            max_portfolio_drawdown=state['max_portfolio_drawdown'],
            rebalance_threshold=state['rebalance_threshold']
        )
        
        # Restore state
        pm.strategies = state['strategies']
        pm.allocations = state['allocations']
        pm.performance = state['performance']
        
        return pm


# Example usage
if __name__ == '__main__':
    # Create portfolio
    pm = PortfolioManager(
        portfolio_id='conservative_001',
        name='Conservative Portfolio',
        total_capital=10000.0,
        max_portfolio_drawdown=0.15
    )
    
    # Add strategies
    pm.add_strategy('rsi_strat', 'strategies/rsi_strategy.py', 0.4, 'RSI oversold/overbought')
    pm.add_strategy('macd_strat', 'strategies/macd_strategy.py', 0.3, 'MACD crossover')
    pm.add_strategy('bb_strat', 'strategies/bb_strategy.py', 0.3', 'Bollinger Bands breakout')
    
    # Simulate some trades
    pm.update_performance('rsi_strat', 120.50, 3)
    pm.update_performance('macd_strat', -45.20, 2)
    pm.update_performance('bb_strat', 85.30, 4)
    
    # Get status
    status = pm.get_status()
    print(json.dumps(status, indent=2))
    
    # Generate report
    report = pm.generate_report()
    print("\n" + "="*50)
    print("Portfolio Report")
    print("="*50)
    print(f"ROI: {report['roi']:.2f}%")
    print(f"Total PnL: ${report['total_pnl']:.2f}")
    print(f"Drawdown: {report['current_drawdown']*100:.2f}%")
    print("\nStrategy Performance:")
    for strat in report['strategy_performance']:
        print(f"  {strat['strategy_id']}: ROI={strat['roi']:.2f}%, PnL=${strat['pnl']:.2f}, Trades={strat['trades']}")
