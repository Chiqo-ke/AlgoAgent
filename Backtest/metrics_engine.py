"""
Metrics Engine
==============

Computes standard performance metrics with canonical formulas.
These formulas are IMMUTABLE and must not be modified by generated strategies.

Last updated: 2025-10-16
Version: 1.0.0
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import math
import logging

from canonical_schema import Fill, AccountSnapshot, OrderSide
from config import BacktestConfig


logger = logging.getLogger(__name__)


class MetricsEngine:
    """
    Computes performance metrics from trade and equity data
    
    All metric formulas are canonical and MUST NOT be changed.
    Strategies may add new metrics but cannot modify existing ones.
    """
    
    # Canonical formula version
    VERSION = "1.0.0"
    
    def __init__(self, config: BacktestConfig):
        """
        Initialize metrics engine
        
        Args:
            config: Backtest configuration
        """
        self.config = config
    
    def compute_all_metrics(
        self,
        fills: List[Fill],
        equity_curve: List[AccountSnapshot],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Compute all performance metrics
        
        Args:
            fills: List of all fills
            equity_curve: List of equity snapshots
            start_date: Backtest start date
            end_date: Backtest end date
        
        Returns:
            Dictionary of all metrics
        """
        if not equity_curve or len(equity_curve) == 0:
            return self._get_empty_metrics(start_date, end_date)
        
        # Separate winning and losing trades
        winning_fills, losing_fills = self._separate_trades(fills)
        
        # Calculate basic metrics
        metrics = {
            # Metadata
            'version': self.VERSION,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'duration_days': (end_date - start_date).days,
            
            # Account metrics
            'start_cash': equity_curve[0].cash if equity_curve else self.config.start_cash,
            'final_equity': equity_curve[-1].equity if equity_curve else 0.0,
            'peak_equity': max(s.equity for s in equity_curve) if equity_curve else 0.0,
            
            # P&L metrics
            'net_profit': self._calculate_net_profit(equity_curve),
            'gross_profit': self._calculate_gross_profit(winning_fills),
            'gross_loss': self._calculate_gross_loss(losing_fills),
            
            # Trade metrics
            'total_trades': len(fills),
            'winning_trades': len(winning_fills),
            'losing_trades': len(losing_fills),
            'win_rate': self._calculate_win_rate(winning_fills, fills),
            
            # Profit metrics
            'profit_factor': self._calculate_profit_factor(winning_fills, losing_fills),
            'average_trade': self._calculate_average_trade(fills),
            'average_win': self._calculate_average_win(winning_fills),
            'average_loss': self._calculate_average_loss(losing_fills),
            'expectancy': self._calculate_expectancy(winning_fills, losing_fills, fills),
            
            # Risk metrics
            'max_drawdown_abs': self._calculate_max_drawdown_abs(equity_curve),
            'max_drawdown_pct': self._calculate_max_drawdown_pct(equity_curve),
            'recovery_factor': self._calculate_recovery_factor(equity_curve),
            
            # Return metrics
            'total_return_pct': self._calculate_total_return_pct(equity_curve),
            'cagr': self._calculate_cagr(equity_curve, start_date, end_date),
            
            # Risk-adjusted returns
            'sharpe_ratio': self._calculate_sharpe_ratio(equity_curve),
            'sortino_ratio': self._calculate_sortino_ratio(equity_curve),
            'calmar_ratio': self._calculate_calmar_ratio(equity_curve, start_date, end_date),
            
            # Streak metrics
            'max_consecutive_wins': self._calculate_max_consecutive_wins(fills),
            'max_consecutive_losses': self._calculate_max_consecutive_losses(fills),
            
            # Additional metrics
            'largest_win': self._calculate_largest_win(winning_fills),
            'largest_loss': self._calculate_largest_loss(losing_fills),
            'total_commission': sum(f.commission for f in fills),
            'total_slippage': sum(f.slippage * f.size for f in fills),
        }
        
        return metrics
    
    def _get_empty_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Return empty metrics when no trades executed"""
        return {
            'version': self.VERSION,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'duration_days': (end_date - start_date).days,
            'start_cash': self.config.start_cash,
            'final_equity': self.config.start_cash,
            'peak_equity': self.config.start_cash,
            'net_profit': 0.0,
            'gross_profit': 0.0,
            'gross_loss': 0.0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'average_trade': 0.0,
            'average_win': 0.0,
            'average_loss': 0.0,
            'expectancy': 0.0,
            'max_drawdown_abs': 0.0,
            'max_drawdown_pct': 0.0,
            'recovery_factor': 0.0,
            'total_return_pct': 0.0,
            'cagr': 0.0,
            'sharpe_ratio': 0.0,
            'sortino_ratio': 0.0,
            'calmar_ratio': 0.0,
            'max_consecutive_wins': 0,
            'max_consecutive_losses': 0,
            'largest_win': 0.0,
            'largest_loss': 0.0,
            'total_commission': 0.0,
            'total_slippage': 0.0,
        }
    
    def _separate_trades(self, fills: List[Fill]) -> tuple:
        """Separate fills into winning and losing trades"""
        winning = [f for f in fills if f.realized_pnl > 0]
        losing = [f for f in fills if f.realized_pnl < 0]
        return winning, losing
    
    # =============================================================================
    # CANONICAL METRIC FORMULAS (DO NOT MODIFY)
    # =============================================================================
    
    def _calculate_net_profit(self, equity_curve: List[AccountSnapshot]) -> float:
        """Net profit = final_equity - starting_equity"""
        if not equity_curve or len(equity_curve) == 0:
            return 0.0
        return equity_curve[-1].equity - equity_curve[0].equity
    
    def _calculate_gross_profit(self, winning_fills: List[Fill]) -> float:
        """Gross profit = sum of winning trades P&L"""
        return sum(f.realized_pnl for f in winning_fills)
    
    def _calculate_gross_loss(self, losing_fills: List[Fill]) -> float:
        """Gross loss = abs(sum of losing trades P&L)"""
        return abs(sum(f.realized_pnl for f in losing_fills))
    
    def _calculate_win_rate(self, winning_fills: List[Fill], all_fills: List[Fill]) -> float:
        """Win rate = #winning_trades / #total_closed_trades"""
        if len(all_fills) == 0:
            return 0.0
        return len(winning_fills) / len(all_fills)
    
    def _calculate_profit_factor(
        self,
        winning_fills: List[Fill],
        losing_fills: List[Fill]
    ) -> float:
        """Profit factor = gross_profit / gross_loss"""
        gross_profit = self._calculate_gross_profit(winning_fills)
        gross_loss = self._calculate_gross_loss(losing_fills)
        
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0
        
        return gross_profit / gross_loss
    
    def _calculate_average_trade(self, fills: List[Fill]) -> float:
        """Average trade = net_profit / number_of_trades"""
        if len(fills) == 0:
            return 0.0
        total_pnl = sum(f.realized_pnl for f in fills)
        return total_pnl / len(fills)
    
    def _calculate_average_win(self, winning_fills: List[Fill]) -> float:
        """Average win = sum(winning_pnl) / #wins"""
        if len(winning_fills) == 0:
            return 0.0
        return sum(f.realized_pnl for f in winning_fills) / len(winning_fills)
    
    def _calculate_average_loss(self, losing_fills: List[Fill]) -> float:
        """Average loss = sum(losing_pnl) / #losses"""
        if len(losing_fills) == 0:
            return 0.0
        return sum(f.realized_pnl for f in losing_fills) / len(losing_fills)
    
    def _calculate_expectancy(
        self,
        winning_fills: List[Fill],
        losing_fills: List[Fill],
        all_fills: List[Fill]
    ) -> float:
        """Expectancy = avg_win * win_rate - avg_loss * loss_rate"""
        if len(all_fills) == 0:
            return 0.0
        
        win_rate = len(winning_fills) / len(all_fills)
        loss_rate = len(losing_fills) / len(all_fills)
        
        avg_win = self._calculate_average_win(winning_fills)
        avg_loss = abs(self._calculate_average_loss(losing_fills))
        
        return avg_win * win_rate - avg_loss * loss_rate
    
    def _calculate_max_drawdown_abs(self, equity_curve: List[AccountSnapshot]) -> float:
        """Maximum drawdown (absolute) = max peak-to-trough drop"""
        if not equity_curve or len(equity_curve) < 2:
            return 0.0
        
        peak = equity_curve[0].equity
        max_dd = 0.0
        
        for snapshot in equity_curve:
            equity = snapshot.equity
            if equity > peak:
                peak = equity
            
            drawdown = peak - equity
            if drawdown > max_dd:
                max_dd = drawdown
        
        return max_dd
    
    def _calculate_max_drawdown_pct(self, equity_curve: List[AccountSnapshot]) -> float:
        """Max drawdown % = max_drawdown / peak_equity"""
        if not equity_curve or len(equity_curve) < 2:
            return 0.0
        
        peak = equity_curve[0].equity
        max_dd_pct = 0.0
        
        for snapshot in equity_curve:
            equity = snapshot.equity
            if equity > peak:
                peak = equity
            
            if peak > 0:
                dd_pct = (peak - equity) / peak
                if dd_pct > max_dd_pct:
                    max_dd_pct = dd_pct
        
        return max_dd_pct
    
    def _calculate_recovery_factor(self, equity_curve: List[AccountSnapshot]) -> float:
        """Recovery factor = net_profit / max_drawdown"""
        if not equity_curve:
            return 0.0
        
        net_profit = self._calculate_net_profit(equity_curve)
        max_dd = self._calculate_max_drawdown_abs(equity_curve)
        
        if max_dd == 0:
            return float('inf') if net_profit > 0 else 0.0
        
        return net_profit / max_dd
    
    def _calculate_total_return_pct(self, equity_curve: List[AccountSnapshot]) -> float:
        """Total return % = (final_equity - start_equity) / start_equity * 100"""
        if not equity_curve or len(equity_curve) == 0:
            return 0.0
        
        start_equity = equity_curve[0].equity
        final_equity = equity_curve[-1].equity
        
        if start_equity == 0:
            return 0.0
        
        return ((final_equity - start_equity) / start_equity) * 100
    
    def _calculate_cagr(
        self,
        equity_curve: List[AccountSnapshot],
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """CAGR = (final_equity / start_equity) ^ (1 / years) - 1"""
        if not equity_curve or len(equity_curve) < 2:
            return 0.0
        
        start_equity = equity_curve[0].equity
        final_equity = equity_curve[-1].equity
        
        if start_equity <= 0:
            return 0.0
        
        years = (end_date - start_date).days / 365.25
        if years <= 0:
            return 0.0
        
        try:
            cagr = (final_equity / start_equity) ** (1 / years) - 1
            return cagr * 100  # As percentage
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def _calculate_sharpe_ratio(self, equity_curve: List[AccountSnapshot]) -> float:
        """
        Sharpe ratio (annualized) = (mean(daily_returns) / std(daily_returns)) * sqrt(252)
        Risk-free rate defaults to 0
        """
        if not equity_curve or len(equity_curve) < 2:
            return 0.0
        
        # Calculate returns
        returns = []
        for i in range(1, len(equity_curve)):
            prev_equity = equity_curve[i-1].equity
            curr_equity = equity_curve[i].equity
            
            if prev_equity > 0:
                ret = (curr_equity - prev_equity) / prev_equity
                returns.append(ret)
        
        if len(returns) < 2:
            return 0.0
        
        # Calculate mean and std
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std_return = math.sqrt(variance)
        
        if std_return == 0:
            return 0.0
        
        # Annualize (assuming daily data)
        sharpe = (mean_return / std_return) * math.sqrt(252)
        
        return sharpe
    
    def _calculate_sortino_ratio(self, equity_curve: List[AccountSnapshot]) -> float:
        """Sortino ratio = mean(daily_returns) / std(downside_returns) * sqrt(252)"""
        if not equity_curve or len(equity_curve) < 2:
            return 0.0
        
        # Calculate returns
        returns = []
        downside_returns = []
        
        for i in range(1, len(equity_curve)):
            prev_equity = equity_curve[i-1].equity
            curr_equity = equity_curve[i].equity
            
            if prev_equity > 0:
                ret = (curr_equity - prev_equity) / prev_equity
                returns.append(ret)
                
                if ret < 0:
                    downside_returns.append(ret)
        
        if len(returns) < 2 or len(downside_returns) == 0:
            return 0.0
        
        # Calculate mean and downside std
        mean_return = sum(returns) / len(returns)
        downside_variance = sum(r ** 2 for r in downside_returns) / len(downside_returns)
        downside_std = math.sqrt(downside_variance)
        
        if downside_std == 0:
            return 0.0
        
        # Annualize
        sortino = (mean_return / downside_std) * math.sqrt(252)
        
        return sortino
    
    def _calculate_calmar_ratio(
        self,
        equity_curve: List[AccountSnapshot],
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """Calmar ratio = CAGR / max_drawdown"""
        if not equity_curve or len(equity_curve) < 2:
            return 0.0
        
        cagr = self._calculate_cagr(equity_curve, start_date, end_date)
        max_dd_pct = self._calculate_max_drawdown_pct(equity_curve)
        
        if max_dd_pct == 0:
            return float('inf') if cagr > 0 else 0.0
        
        # Convert to same units (both as percentage)
        return cagr / (max_dd_pct * 100)
    
    def _calculate_max_consecutive_wins(self, fills: List[Fill]) -> int:
        """Count longest streak of winning trades"""
        if not fills:
            return 0
        
        max_streak = 0
        current_streak = 0
        
        for fill in fills:
            if fill.realized_pnl > 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        return max_streak
    
    def _calculate_max_consecutive_losses(self, fills: List[Fill]) -> int:
        """Count longest streak of losing trades"""
        if not fills:
            return 0
        
        max_streak = 0
        current_streak = 0
        
        for fill in fills:
            if fill.realized_pnl < 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        return max_streak
    
    def _calculate_largest_win(self, winning_fills: List[Fill]) -> float:
        """Largest single winning trade"""
        if not winning_fills:
            return 0.0
        return max(f.realized_pnl for f in winning_fills)
    
    def _calculate_largest_loss(self, losing_fills: List[Fill]) -> float:
        """Largest single losing trade (absolute value)"""
        if not losing_fills:
            return 0.0
        return abs(min(f.realized_pnl for f in losing_fills))


if __name__ == "__main__":
    # Example usage
    import random
    from canonical_schema import generate_id
    
    logging.basicConfig(level=logging.INFO)
    
    config = BacktestConfig()
    engine = MetricsEngine(config)
    
    # Generate sample data
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 12, 31)
    
    # Create sample fills
    fills = []
    for i in range(50):
        pnl = random.gauss(100, 500)  # Random P&L
        fill = Fill(
            trade_id=generate_id(),
            order_id=generate_id(),
            signal_id=generate_id(),
            timestamp=start_date + timedelta(days=i*7),
            symbol="AAPL",
            side=OrderSide.BUY if random.random() > 0.5 else OrderSide.SELL,
            price=150.0,
            size=100,
            commission=10.0,
            slippage=0.05,
            realized_pnl=pnl
        )
        fills.append(fill)
    
    # Create sample equity curve
    equity_curve = []
    equity = 100000
    for i in range(365):
        equity += random.gauss(50, 200)
        snapshot = AccountSnapshot(
            timestamp=start_date + timedelta(days=i),
            cash=equity * 0.5,
            equity=equity,
            positions=[]
        )
        equity_curve.append(snapshot)
    
    # Compute metrics
    metrics = engine.compute_all_metrics(fills, equity_curve, start_date, end_date)
    
    print("Sample Metrics:")
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
