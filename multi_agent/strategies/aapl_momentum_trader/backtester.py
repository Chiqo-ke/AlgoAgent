import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns

class Backtester:
    """Backtesting engine for trading strategies"""
    
    def __init__(self, initial_balance: float = 10000, commission: float = 0.0001, 
                 slippage: int = 1):
        self.initial_balance = initial_balance
        self.commission = commission  # Commission as percentage
        self.slippage = slippage  # Slippage in pips
        self.logger = logging.getLogger(__name__)
        
        # Results storage
        self.equity_curve = []
        self.trade_log = []
        self.daily_returns = []
        
    def run_backtest(self, data: pd.DataFrame, signals_df: pd.DataFrame,
                    risk_manager, position_manager) -> Dict:
        """
        Run backtest on historical data
        
        Args:
            data: Historical price data
            signals_df: DataFrame with trading signals
            risk_manager: RiskManager instance
            position_manager: PositionManager instance
            
        Returns:
            Backtest results dictionary
        """
        self.logger.info("Starting backtest...")
        
        balance = self.initial_balance
        equity = balance
        
        # Symbol info for position sizing (simplified for backtesting)
        symbol_info = {
            'point': 0.01,  # For stocks
            'trade_tick_value': 1.0,
            'volume_step': 1,
            'minimum_volume': 1,
            'maximum_volume': 1000
        }
        
        for i, (timestamp, row) in enumerate(signals_df.iterrows()):
            current_price = row['close']
            signal = row['signal']
            rsi = row.get('rsi', 50)
            sma = row.get('sma20', current_price)
            atr = row.get('atr', current_price * 0.02)
            
            # Update existing positions
            current_prices = {'AAPL': current_price}
            position_manager.update_positions(current_prices)
            
            # Check for position exits
            positions_to_close = []
            for pos_id, position in position_manager.get_open_positions().items():
                should_close, reason = risk_manager.should_close_position(
                    position, current_price, timestamp
                )
                
                if should_close:
                    positions_to_close.append((pos_id, reason))
            
            # Close positions
            for pos_id, reason in positions_to_close:
                exit_price = self._apply_slippage(current_price, 'exit')
                closed_position = position_manager.close_position(
                    pos_id, exit_price, timestamp, reason
                )
                
                if closed_position:
                    # Update balance
                    pnl = closed_position['realized_pnl']
                    commission_cost = abs(exit_price * closed_position['volume'] * self.commission)
                    net_pnl = pnl - commission_cost
                    balance += net_pnl
                    
                    # Log trade
                    self.trade_log.append({
                        'timestamp': timestamp,
                        'action': 'close',
                        'symbol': 'AAPL',
                        'direction': closed_position['direction'],
                        'entry_price': closed_position['entry_price'],
                        'exit_price': exit_price,
                        'volume': closed_position['volume'],
                        'pnl': pnl,
                        'commission': commission_cost,
                        'net_pnl': net_pnl,
                        'balance': balance,
                        'reason': reason
                    })
            
            # Check for new signals
            if signal != 0 and position_manager.get_position_count() < risk_manager.max_positions:
                direction = 'long' if signal > 0 else 'short'
                
                # Calculate signal strength
                from indicators import SignalGenerator
                signal_gen = SignalGenerator()
                signal_strength = signal_gen.get_signal_strength(rsi, current_price, sma)
                
                # Validate trade
                spread = 2  # Assume 2 pip spread for backtesting
                is_valid, reason = risk_manager.validate_trade(
                    signal_strength, spread, position_manager.get_position_count()
                )
                
                if is_valid:
                    # Calculate position parameters
                    entry_price = self._apply_slippage(current_price, 'entry', direction)
                    stop_loss = risk_manager.calculate_stop_loss(entry_price, direction, atr)
                    take_profit = risk_manager.calculate_take_profit(entry_price, stop_loss, direction)
                    
                    # Calculate position size
                    volume = risk_manager.calculate_position_size(
                        balance, entry_price, stop_loss, symbol_info
                    )
                    
                    # Open position
                    pos_id = position_manager.open_position(
                        'AAPL', direction, entry_price, volume, 
                        stop_loss, take_profit, timestamp
                    )
                    
                    # Calculate commission
                    commission_cost = entry_price * volume * self.commission
                    balance -= commission_cost
                    
                    # Log trade
                    self.trade_log.append({
                        'timestamp': timestamp,
                        'action': 'open',
                        'symbol': 'AAPL',
                        'direction': direction,
                        'entry_price': entry_price,
                        'volume': volume,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'commission': commission_cost,
                        'balance': balance,
                        'signal_strength': signal_strength
                    })
            
            # Calculate current equity
            unrealized_pnl = sum([pos['unrealized_pnl'] for pos in position_manager.get_open_positions().values()])
            equity = balance + unrealized_pnl
            
            # Store equity curve
            self.equity_curve.append({
                'timestamp': timestamp,
                'balance': balance,
                'equity': equity,
                'unrealized_pnl': unrealized_pnl,
                'open_positions': position_manager.get_position_count()
            })
            
            # Calculate daily returns
            if len(self.equity_curve) > 1:
                prev_equity = self.equity_curve[-2]['equity']
                daily_return = (equity - prev_equity) / prev_equity
                self.daily_returns.append(daily_return)
        
        # Close any remaining positions at the end
        final_timestamp = signals_df.index[-1]
        final_price = signals_df['close'].iloc[-1]
        
        for pos_id in list(position_manager.get_open_positions().keys()):
            exit_price = self._apply_slippage(final_price, 'exit')
            closed_position = position_manager.close_position(
                pos_id, exit_price, final_timestamp, "End of backtest"
            )
            
            if closed_position:
                pnl = closed_position['realized_pnl']
                commission_cost = abs(exit_price * closed_position['volume'] * self.commission)
                net_pnl = pnl - commission_cost
                balance += net_pnl
        
        # Calculate final statistics
        stats = self._calculate_statistics(position_manager)
        
        self.logger.info("Backtest completed")
        return stats
    
    def _apply_slippage(self, price: float, action: str, direction: str = 'long') -> float:
        """Apply slippage to price"""
        slippage_amount = self.slippage * 0.01  # Convert pips to price
        
        if action == 'entry':
            if direction == 'long':
                return price + slippage_amount  # Pay higher for long entry
            else:
                return price - slippage_amount  # Receive less for short entry
        else:  # exit
            if direction == 'long':
                return price - slippage_amount  # Receive less for long exit
            else:
                return price + slippage_amount  # Pay higher for short exit
    
    def _calculate_statistics(self, position_manager) -> Dict:
        """Calculate comprehensive backtest statistics"""
        if not self.equity_curve:
            return {}
        
        equity_df = pd.DataFrame(self.equity_curve)
        equity_df.set_index('timestamp', inplace=True)
        
        # Basic statistics
        final_equity = equity_df['equity'].iloc[-1]
        total_return = (final_equity - self.initial_balance) / self.initial_balance * 100
        
        # Trade statistics
        trade_stats = position_manager.get_statistics()
        
        # Risk metrics
        if len(self.daily_returns) > 0:
            daily_returns = np.array(self.daily_returns)
            sharpe_ratio = np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(252) if np.std(daily_returns) > 0 else 0
            
            # Calculate maximum drawdown
            equity_series = equity_df['equity']
            rolling_max = equity_series.expanding().max()
            drawdown = (equity_series - rolling_max) / rolling_max * 100
            max_drawdown = drawdown.min()
        else:
            sharpe_ratio = 0
            max_drawdown = 0
        
        return {
            'initial_balance': self.initial_balance,
            'final_equity': final_equity,
            'total_return_pct': total_return,
            'total_pnl': final_equity - self.initial_balance,
            'max_drawdown_pct': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'total_trades': trade_stats['total_trades'],
            'winning_trades': trade_stats['winning_trades'],
            'losing_trades': trade_stats['losing_trades'],
            'win_rate_pct': trade_stats['win_rate'],
            'profit_factor': trade_stats['profit_factor'],
            'average_win': trade_stats['average_win'],
            'average_loss': trade_stats['average_loss'],
            'largest_win': trade_stats['largest_win'],
            'largest_loss': trade_stats['largest_loss'],
            'equity_curve': equity_df,
            'trade_log': pd.DataFrame(self.trade_log)
        }
    
    def plot_results(self, results: Dict, save_path: str = None):
        """Plot backtest results"""
        if 'equity_curve' not in results:
            self.logger.warning("No equity curve data to plot")
            return
        
        equity_df = results['equity_curve']
        
        # Create subplots
        fig, axes = plt.subplots(3, 1, figsize=(12, 10))
        
        # Equity curve
        axes[0].plot(equity_df.index, equity_df['equity'], label='Equity', color='blue')
        axes[0].plot(equity_df.index, equity_df['balance'], label='Balance', color='orange')
        axes[0].set_title('Equity Curve')
        axes[0].set_ylabel('USD')
        axes[0].legend()
        axes[0].grid(True)
        
        # Drawdown
        rolling_max = equity_df['equity'].expanding().max()
        drawdown = (equity_df['equity'] - rolling_max) / rolling_max * 100
        axes[1].fill_between(drawdown.index, drawdown, 0, alpha=0.3, color='red')
        axes[1].set_title('Drawdown')
        axes[1].set_ylabel('Percentage (%)')
        axes[1].grid(True)
        
        # Open positions
        axes[2].plot(equity_df.index, equity_df['open_positions'], label='Open Positions', color='green')
        axes[2].set_title('Open Positions')
        axes[2].set_xlabel('Time')
        axes[2].set_ylabel('Number of Positions')
        axes[2].grid(True)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            self.logger.info(f"Results plot saved to {save_path}")
        
        plt.show()
    
    def generate_report(self, results: Dict) -> str:
        """Generate a text report of backtest results"""
        if not results:
            return "No results to report"
        
        report = f"""
AAPL MOMENTUM TRADING STRATEGY - BACKTEST RESULTS
================================================

PERFORMANCE SUMMARY
------------------
Initial Balance:     ${results['initial_balance']:,.2f}
Final Equity:        ${results['final_equity']:,.2f}
Total Return:        {results['total_return_pct']:.2f}%
Total P&L:          ${results['total_pnl']:,.2f}
Max Drawdown:       {results['max_drawdown_pct']:.2f}%
Sharpe Ratio:       {results['sharpe_ratio']:.3f}

TRADE STATISTICS
---------------
Total Trades:       {results['total_trades']}
Winning Trades:     {results['winning_trades']}
Losing Trades:      {results['losing_trades']}
Win Rate:           {results['win_rate_pct']:.1f}%
Profit Factor:      {results['profit_factor']:.2f}

Average Win:        ${results['average_win']:,.2f}
Average Loss:       ${results['average_loss']:,.2f}
Largest Win:        ${results['largest_win']:,.2f}
Largest Loss:       ${results['largest_loss']:,.2f}

RISK METRICS
-----------
Max Drawdown:       {results['max_drawdown_pct']:.2f}%
Sharpe Ratio:       {results['sharpe_ratio']:.3f}
"""
        
        return report