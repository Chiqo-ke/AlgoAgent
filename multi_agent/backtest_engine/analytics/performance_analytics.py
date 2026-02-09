"""
Performance Analytics and Reporting
Advanced analytics and reporting tools for backtesting results

Features:
- Comprehensive performance metrics
- Risk analysis and attribution
- Visual reporting and charts
- Benchmark comparison
- Trade analysis and insights
- Portfolio performance analytics
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
import logging
from pathlib import Path
import seaborn as sns

logger = logging.getLogger(__name__)

class PerformanceAnalytics:
    """
    Comprehensive performance analytics for backtesting results
    """
    
    def __init__(self, results: Dict[str, Any]):
        """
        Initialize with backtesting results
        
        Args:
            results: Results dictionary from backtesting engine
        """
        self.results = results
        self.summary = results.get('summary', {})
        self.trades = results.get('trades', {})
        self.equity_curve = pd.DataFrame(results.get('equity_curve', []))
        self.drawdown_curve = pd.DataFrame(results.get('drawdown_curve', []))
        self.daily_returns = pd.DataFrame(results.get('daily_returns', []))
        self.closed_trades = pd.DataFrame(results.get('closed_trades', []))
        
        # Convert timestamp columns to datetime
        for df, col in [(self.equity_curve, 'timestamp'), 
                       (self.drawdown_curve, 'timestamp'), 
                       (self.daily_returns, 'timestamp')]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
                df.set_index(col, inplace=True)
        
        # Convert trade timestamps
        if not self.closed_trades.empty:
            for col in ['entry_time', 'exit_time']:
                if col in self.closed_trades.columns:
                    self.closed_trades[col] = pd.to_datetime(self.closed_trades[col])
    
    def calculate_advanced_metrics(self) -> Dict[str, Any]:
        """
        Calculate advanced performance metrics
        
        Returns:
            Dictionary of advanced metrics
        """
        metrics = {}
        
        if self.daily_returns.empty or self.equity_curve.empty:
            return metrics
        
        returns = self.daily_returns['return'] / 100  # Convert to decimal
        equity = self.equity_curve['equity']
        
        try:
            # Return metrics
            metrics['annualized_return'] = returns.mean() * 252 * 100
            metrics['volatility'] = returns.std() * np.sqrt(252) * 100
            metrics['sharpe_ratio'] = metrics['annualized_return'] / metrics['volatility'] if metrics['volatility'] > 0 else 0
            
            # Sortino ratio (using downside deviation)
            downside_returns = returns[returns < 0]
            downside_deviation = downside_returns.std() * np.sqrt(252) * 100
            metrics['sortino_ratio'] = metrics['annualized_return'] / downside_deviation if downside_deviation > 0 else 0
            
            # Calmar ratio
            max_dd = self.summary.get('max_drawdown', 0)
            metrics['calmar_ratio'] = metrics['annualized_return'] / max_dd if max_dd > 0 else 0
            
            # Value at Risk (VaR) - 5% and 1%
            metrics['var_5'] = np.percentile(returns, 5) * 100
            metrics['var_1'] = np.percentile(returns, 1) * 100
            
            # Maximum consecutive wins/losses
            if not self.closed_trades.empty:
                trades_pnl = self.closed_trades['pnl']
                wins = (trades_pnl > 0).astype(int)
                losses = (trades_pnl < 0).astype(int)
                
                # Calculate consecutive sequences
                metrics['max_consecutive_wins'] = self._max_consecutive(wins)
                metrics['max_consecutive_losses'] = self._max_consecutive(losses)
                
                # Trade duration analysis
                if 'entry_time' in self.closed_trades.columns and 'exit_time' in self.closed_trades.columns:
                    duration = (self.closed_trades['exit_time'] - self.closed_trades['entry_time']).dt.days
                    metrics['avg_trade_duration'] = duration.mean()
                    metrics['max_trade_duration'] = duration.max()
                    metrics['min_trade_duration'] = duration.min()
                
                # Win/Loss analysis
                winning_trades = self.closed_trades[self.closed_trades['pnl'] > 0]['pnl']
                losing_trades = self.closed_trades[self.closed_trades['pnl'] < 0]['pnl']
                
                if len(winning_trades) > 0 and len(losing_trades) > 0:
                    metrics['avg_win'] = winning_trades.mean()
                    metrics['avg_loss'] = abs(losing_trades.mean())
                    metrics['win_loss_ratio'] = metrics['avg_win'] / metrics['avg_loss']
                    metrics['expectancy'] = (self.trades.get('win_rate', 0) / 100 * metrics['avg_win']) - ((100 - self.trades.get('win_rate', 0)) / 100 * metrics['avg_loss'])
            
            # Recovery factor
            total_pnl = self.summary.get('final_equity', 0) - self.summary.get('initial_capital', 0)
            metrics['recovery_factor'] = total_pnl / max_dd if max_dd > 0 else 0
            
            # Pain index (average drawdown)
            if not self.drawdown_curve.empty:
                metrics['pain_index'] = self.drawdown_curve['drawdown'].mean()
            
            # Ulcer index
            if not self.drawdown_curve.empty:
                metrics['ulcer_index'] = np.sqrt(np.mean(self.drawdown_curve['drawdown'] ** 2))
            
        except Exception as e:
            logger.error(f"Error calculating advanced metrics: {e}")
        
        return metrics
    
    def _max_consecutive(self, series: pd.Series) -> int:
        """Calculate maximum consecutive 1s in a binary series"""
        max_count = 0
        current_count = 0
        
        for value in series:
            if value == 1:
                current_count += 1
                max_count = max(max_count, current_count)
            else:
                current_count = 0
        
        return max_count
    
    def analyze_trades(self) -> Dict[str, Any]:
        """
        Detailed trade analysis
        
        Returns:
            Trade analysis results
        """
        if self.closed_trades.empty:
            return {}
        
        analysis = {}
        
        try:
            # Basic trade statistics
            pnl = self.closed_trades['pnl']
            analysis['total_trades'] = len(pnl)
            analysis['winning_trades'] = len(pnl[pnl > 0])
            analysis['losing_trades'] = len(pnl[pnl < 0])
            analysis['breakeven_trades'] = len(pnl[pnl == 0])
            
            # PnL statistics
            analysis['gross_profit'] = pnl[pnl > 0].sum()
            analysis['gross_loss'] = abs(pnl[pnl < 0].sum())
            analysis['net_profit'] = pnl.sum()
            
            # Trade distribution
            analysis['largest_win'] = pnl.max()
            analysis['largest_loss'] = pnl.min()
            analysis['average_trade'] = pnl.mean()
            analysis['median_trade'] = pnl.median()
            analysis['trade_std'] = pnl.std()
            
            # Side analysis (long vs short)
            long_trades = self.closed_trades[self.closed_trades['side'] == 'long']
            short_trades = self.closed_trades[self.closed_trades['side'] == 'short']
            
            if not long_trades.empty:
                analysis['long_trades_count'] = len(long_trades)
                analysis['long_trades_pnl'] = long_trades['pnl'].sum()
                analysis['long_win_rate'] = len(long_trades[long_trades['pnl'] > 0]) / len(long_trades) * 100
                analysis['long_avg_trade'] = long_trades['pnl'].mean()
            
            if not short_trades.empty:
                analysis['short_trades_count'] = len(short_trades)
                analysis['short_trades_pnl'] = short_trades['pnl'].sum()
                analysis['short_win_rate'] = len(short_trades[short_trades['pnl'] > 0]) / len(short_trades) * 100
                analysis['short_avg_trade'] = short_trades['pnl'].mean()
            
            # Exit reason analysis
            if 'reason' in self.closed_trades.columns:
                exit_reasons = self.closed_trades['reason'].value_counts()
                analysis['exit_reasons'] = exit_reasons.to_dict()
            
            # Monthly performance
            if 'exit_time' in self.closed_trades.columns:
                monthly_pnl = self.closed_trades.groupby(self.closed_trades['exit_time'].dt.to_period('M'))['pnl'].sum()
                analysis['monthly_performance'] = monthly_pnl.to_dict()
                analysis['positive_months'] = len(monthly_pnl[monthly_pnl > 0])
                analysis['negative_months'] = len(monthly_pnl[monthly_pnl < 0])
                analysis['best_month'] = monthly_pnl.max()
                analysis['worst_month'] = monthly_pnl.min()
        
        except Exception as e:
            logger.error(f"Error in trade analysis: {e}")
        
        return analysis
    
    def calculate_risk_metrics(self) -> Dict[str, Any]:
        """
        Calculate comprehensive risk metrics
        
        Returns:
            Risk metrics dictionary
        """
        risk_metrics = {}
        
        try:
            if not self.daily_returns.empty:
                returns = self.daily_returns['return'] / 100
                
                # Downside risk metrics
                downside_returns = returns[returns < 0]
                risk_metrics['downside_frequency'] = len(downside_returns) / len(returns) * 100
                risk_metrics['average_downside_return'] = downside_returns.mean() * 100 if len(downside_returns) > 0 else 0
                risk_metrics['worst_day'] = returns.min() * 100
                risk_metrics['best_day'] = returns.max() * 100
                
                # Rolling metrics
                rolling_returns = returns.rolling(window=30)  # 30-day rolling
                risk_metrics['worst_30d_return'] = rolling_returns.sum().min() * 100
                risk_metrics['best_30d_return'] = rolling_returns.sum().max() * 100
                
            # Drawdown analysis
            if not self.drawdown_curve.empty:
                drawdowns = self.drawdown_curve['drawdown']
                risk_metrics['max_drawdown'] = drawdowns.max()
                risk_metrics['average_drawdown'] = drawdowns.mean()
                risk_metrics['drawdown_frequency'] = len(drawdowns[drawdowns > 0]) / len(drawdowns) * 100
                
                # Drawdown duration analysis
                in_drawdown = drawdowns > 0
                drawdown_periods = []
                current_period = 0
                
                for is_dd in in_drawdown:
                    if is_dd:
                        current_period += 1
                    else:
                        if current_period > 0:
                            drawdown_periods.append(current_period)
                            current_period = 0
                
                if current_period > 0:
                    drawdown_periods.append(current_period)
                
                if drawdown_periods:
                    risk_metrics['max_drawdown_duration'] = max(drawdown_periods)
                    risk_metrics['avg_drawdown_duration'] = np.mean(drawdown_periods)
            
            # Position size risk
            if not self.closed_trades.empty:
                trade_sizes = abs(self.closed_trades['pnl'])
                risk_metrics['largest_loss_pct'] = abs(self.closed_trades['pnl'].min()) / self.summary.get('initial_capital', 1) * 100
                risk_metrics['average_trade_risk'] = trade_sizes.mean() / self.summary.get('initial_capital', 1) * 100
                
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
        
        return risk_metrics
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive performance report
        
        Returns:
            Complete performance report
        """
        report = {
            'basic_metrics': self.summary.copy(),
            'trade_metrics': self.trades.copy(),
            'advanced_metrics': self.calculate_advanced_metrics(),
            'trade_analysis': self.analyze_trades(),
            'risk_metrics': self.calculate_risk_metrics(),
            'generated_at': datetime.now().isoformat()
        }
        
        return report

class ReportGenerator:
    """
    Generate visual and text reports from backtesting results
    """
    
    def __init__(self, analytics: PerformanceAnalytics):
        """
        Initialize with performance analytics
        
        Args:
            analytics: PerformanceAnalytics instance
        """
        self.analytics = analytics
        plt.style.use('seaborn-v0_8' if 'seaborn-v0_8' in plt.style.available else 'default')
    
    def create_equity_curve_plot(self, figsize: Tuple[int, int] = (12, 6)) -> plt.Figure:
        """
        Create equity curve plot
        
        Args:
            figsize: Figure size
            
        Returns:
            Matplotlib figure
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, height_ratios=[3, 1])
        
        if not self.analytics.equity_curve.empty:
            # Equity curve
            equity_data = self.analytics.equity_curve.copy()
            ax1.plot(equity_data.index, equity_data['equity'], label='Portfolio Value', linewidth=2, color='blue')
            ax1.axhline(y=self.analytics.summary.get('initial_capital', 10000), 
                       color='red', linestyle='--', alpha=0.7, label='Initial Capital')
            
            ax1.set_title('Portfolio Equity Curve')
            ax1.set_ylabel('Portfolio Value ($)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Format x-axis
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            
            # Drawdown
            if not self.analytics.drawdown_curve.empty:
                drawdown_data = self.analytics.drawdown_curve.copy()
                ax2.fill_between(drawdown_data.index, 0, -drawdown_data['drawdown'], 
                               alpha=0.3, color='red', label='Drawdown')
                ax2.set_ylabel('Drawdown (%)')
                ax2.set_xlabel('Date')
                ax2.grid(True, alpha=0.3)
                ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
                ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        
        plt.tight_layout()
        return fig
    
    def create_returns_distribution_plot(self, figsize: Tuple[int, int] = (10, 6)) -> plt.Figure:
        """
        Create returns distribution plot
        
        Args:
            figsize: Figure size
            
        Returns:
            Matplotlib figure
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
        
        if not self.analytics.daily_returns.empty:
            returns = self.analytics.daily_returns['return']
            
            # Histogram
            ax1.hist(returns, bins=50, alpha=0.7, color='blue', edgecolor='black')
            ax1.axvline(returns.mean(), color='red', linestyle='--', label=f'Mean: {returns.mean():.2f}%')
            ax1.set_title('Daily Returns Distribution')
            ax1.set_xlabel('Daily Return (%)')
            ax1.set_ylabel('Frequency')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Q-Q plot
            from scipy import stats
            stats.probplot(returns, dist="norm", plot=ax2)
            ax2.set_title('Q-Q Plot (Normal Distribution)')
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def create_trade_analysis_plot(self, figsize: Tuple[int, int] = (12, 8)) -> plt.Figure:
        """
        Create trade analysis visualization
        
        Args:
            figsize: Figure size
            
        Returns:
            Matplotlib figure
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=figsize)
        
        if not self.analytics.closed_trades.empty:
            trades = self.analytics.closed_trades.copy()
            
            # PnL by trade number
            ax1.bar(range(len(trades)), trades['pnl'], color=['green' if x > 0 else 'red' for x in trades['pnl']])
            ax1.set_title('PnL by Trade Number')
            ax1.set_xlabel('Trade Number')
            ax1.set_ylabel('PnL ($)')
            ax1.grid(True, alpha=0.3)
            
            # Cumulative PnL
            cumulative_pnl = trades['pnl'].cumsum()
            ax2.plot(range(len(cumulative_pnl)), cumulative_pnl, linewidth=2, color='blue')
            ax2.set_title('Cumulative PnL')
            ax2.set_xlabel('Trade Number')
            ax2.set_ylabel('Cumulative PnL ($)')
            ax2.grid(True, alpha=0.3)
            
            # PnL distribution
            ax3.hist(trades['pnl'], bins=30, alpha=0.7, color='purple', edgecolor='black')
            ax3.axvline(0, color='red', linestyle='--', label='Breakeven')
            ax3.set_title('Trade PnL Distribution')
            ax3.set_xlabel('PnL ($)')
            ax3.set_ylabel('Frequency')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            
            # Win/Loss by side
            if 'side' in trades.columns:
                side_analysis = trades.groupby(['side', trades['pnl'] > 0])['pnl'].count().unstack(fill_value=0)
                side_analysis.plot(kind='bar', ax=ax4, color=['red', 'green'])
                ax4.set_title('Win/Loss by Trade Side')
                ax4.set_xlabel('Trade Side')
                ax4.set_ylabel('Number of Trades')
                ax4.legend(['Losses', 'Wins'])
                ax4.grid(True, alpha=0.3)
                plt.setp(ax4.xaxis.get_majorticklabels(), rotation=0)
        
        plt.tight_layout()
        return fig
    
    def create_monthly_performance_heatmap(self, figsize: Tuple[int, int] = (12, 6)) -> plt.Figure:
        """
        Create monthly performance heatmap
        
        Args:
            figsize: Figure size
            
        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        if not self.analytics.closed_trades.empty and 'exit_time' in self.analytics.closed_trades.columns:
            trades = self.analytics.closed_trades.copy()
            
            # Group by year-month
            trades['year'] = trades['exit_time'].dt.year
            trades['month'] = trades['exit_time'].dt.month
            monthly_pnl = trades.groupby(['year', 'month'])['pnl'].sum().reset_index()
            
            # Create pivot table for heatmap
            pivot_table = monthly_pnl.pivot(index='year', columns='month', values='pnl')
            
            # Create heatmap
            sns.heatmap(pivot_table, annot=True, fmt='.0f', cmap='RdYlGn', center=0,
                       cbar_kws={'label': 'PnL ($)'}, ax=ax)
            
            ax.set_title('Monthly Performance Heatmap')
            ax.set_xlabel('Month')
            ax.set_ylabel('Year')
            
            # Set month labels
            month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            ax.set_xticklabels(month_labels[:len(pivot_table.columns)])
        
        plt.tight_layout()
        return fig
    
    def generate_html_report(self, output_path: str, include_plots: bool = True) -> str:
        """
        Generate comprehensive HTML report
        
        Args:
            output_path: Path to save HTML report
            include_plots: Whether to include plots in report
            
        Returns:
            Path to generated HTML file
        """
        # Generate performance report
        report = self.analytics.generate_performance_report()
        
        # HTML template
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Backtesting Performance Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ text-align: center; color: #333; }}
                .section {{ margin: 20px 0; }}
                .metrics-table {{ border-collapse: collapse; width: 100%; }}
                .metrics-table th, .metrics-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                .metrics-table th {{ background-color: #f2f2f2; }}
                .positive {{ color: green; }}
                .negative {{ color: red; }}
                .plot {{ text-align: center; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Backtesting Performance Report</h1>
                <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="section">
                <h2>Executive Summary</h2>
                <table class="metrics-table">
                    <tr><th>Metric</th><th>Value</th></tr>
                    <tr><td>Initial Capital</td><td>${report['basic_metrics'].get('initial_capital', 0):,.2f}</td></tr>
                    <tr><td>Final Equity</td><td>${report['basic_metrics'].get('final_equity', 0):,.2f}</td></tr>
                    <tr><td>Total Return</td><td class="{'positive' if report['basic_metrics'].get('total_return', 0) > 0 else 'negative'}">{report['basic_metrics'].get('total_return', 0):.2f}%</td></tr>
                    <tr><td>Max Drawdown</td><td class="negative">{report['basic_metrics'].get('max_drawdown', 0):.2f}%</td></tr>
                    <tr><td>Sharpe Ratio</td><td>{report['basic_metrics'].get('sharpe_ratio', 0):.2f}</td></tr>
                    <tr><td>Total Trades</td><td>{report['trade_metrics'].get('total_trades', 0)}</td></tr>
                    <tr><td>Win Rate</td><td>{report['trade_metrics'].get('win_rate', 0):.1f}%</td></tr>
                    <tr><td>Profit Factor</td><td>{report['basic_metrics'].get('profit_factor', 0):.2f}</td></tr>
                </table>
            </div>
            
            <div class="section">
                <h2>Advanced Performance Metrics</h2>
                <table class="metrics-table">
                    <tr><th>Metric</th><th>Value</th></tr>
        """
        
        for metric, value in report['advanced_metrics'].items():
            if isinstance(value, (int, float)):
                html_content += f"<tr><td>{metric.replace('_', ' ').title()}</td><td>{value:.2f}</td></tr>\n"
        
        html_content += """
                </table>
            </div>
            
            <div class="section">
                <h2>Risk Metrics</h2>
                <table class="metrics-table">
                    <tr><th>Metric</th><th>Value</th></tr>
        """
        
        for metric, value in report['risk_metrics'].items():
            if isinstance(value, (int, float)):
                html_content += f"<tr><td>{metric.replace('_', ' ').title()}</td><td>{value:.2f}</td></tr>\n"
        
        html_content += """
                </table>
            </div>
            
            <div class="section">
                <h2>Trade Analysis</h2>
                <table class="metrics-table">
                    <tr><th>Metric</th><th>Value</th></tr>
        """
        
        for metric, value in report['trade_analysis'].items():
            if isinstance(value, (int, float)) and not metric.endswith('_performance'):
                if 'pnl' in metric or 'profit' in metric or 'loss' in metric:
                    html_content += f"<tr><td>{metric.replace('_', ' ').title()}</td><td>${value:.2f}</td></tr>\n"
                else:
                    html_content += f"<tr><td>{metric.replace('_', ' ').title()}</td><td>{value:.2f}</td></tr>\n"
        
        html_content += """
                </table>
            </div>
        </body>
        </html>
        """
        
        # Save HTML file
        output_file = Path(output_path)
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        logger.info(f"HTML report generated: {output_file}")
        return str(output_file)
    
    def save_plots(self, output_dir: str):
        """
        Save all plots to directory
        
        Args:
            output_dir: Directory to save plots
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Generate and save plots
        try:
            fig1 = self.create_equity_curve_plot()
            fig1.savefig(output_path / 'equity_curve.png', dpi=300, bbox_inches='tight')
            plt.close(fig1)
            
            fig2 = self.create_returns_distribution_plot()
            fig2.savefig(output_path / 'returns_distribution.png', dpi=300, bbox_inches='tight')
            plt.close(fig2)
            
            fig3 = self.create_trade_analysis_plot()
            fig3.savefig(output_path / 'trade_analysis.png', dpi=300, bbox_inches='tight')
            plt.close(fig3)
            
            fig4 = self.create_monthly_performance_heatmap()
            fig4.savefig(output_path / 'monthly_performance.png', dpi=300, bbox_inches='tight')
            plt.close(fig4)
            
            logger.info(f"Plots saved to {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving plots: {e}")

class BenchmarkComparison:
    """
    Compare strategy performance against benchmarks
    """
    
    def __init__(self, strategy_results: Dict[str, Any]):
        """
        Initialize with strategy results
        
        Args:
            strategy_results: Strategy backtesting results
        """
        self.strategy_results = strategy_results
        self.benchmark_data = {}
    
    def add_benchmark(self, name: str, benchmark_data: pd.DataFrame):
        """
        Add benchmark data for comparison
        
        Args:
            name: Benchmark name (e.g., 'SPY', 'Buy_and_Hold')
            benchmark_data: Benchmark price data
        """
        self.benchmark_data[name] = benchmark_data
        logger.info(f"Added benchmark: {name}")
    
    def calculate_benchmark_returns(self, name: str, start_date: str, end_date: str) -> Dict[str, float]:
        """
        Calculate benchmark returns for comparison period
        
        Args:
            name: Benchmark name
            start_date: Start date
            end_date: End date
            
        Returns:
            Benchmark performance metrics
        """
        if name not in self.benchmark_data:
            return {}
        
        data = self.benchmark_data[name]
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        
        # Filter data by date range
        period_data = data[(data.index >= start_date) & (data.index <= end_date)]
        
        if len(period_data) < 2:
            return {}
        
        start_price = period_data.iloc[0]['close']
        end_price = period_data.iloc[-1]['close']
        total_return = (end_price - start_price) / start_price * 100
        
        # Calculate daily returns
        daily_returns = period_data['close'].pct_change().dropna() * 100
        
        metrics = {
            'total_return': total_return,
            'annualized_return': daily_returns.mean() * 252,
            'volatility': daily_returns.std() * np.sqrt(252),
            'sharpe_ratio': (daily_returns.mean() * 252) / (daily_returns.std() * np.sqrt(252)) if daily_returns.std() > 0 else 0,
            'max_drawdown': self._calculate_max_drawdown(period_data['close'])
        }
        
        return metrics
    
    def _calculate_max_drawdown(self, prices: pd.Series) -> float:
        """Calculate maximum drawdown from price series"""
        peak = prices.expanding().max()
        drawdown = (prices - peak) / peak * 100
        return abs(drawdown.min())
    
    def generate_comparison_report(self) -> Dict[str, Any]:
        """
        Generate comparison report between strategy and benchmarks
        
        Returns:
            Comparison report
        """
        comparison = {
            'strategy': self.strategy_results['summary'],
            'benchmarks': {},
            'comparison_metrics': {}
        }
        
        start_date = self.strategy_results['config']['start_date']
        end_date = self.strategy_results['config']['end_date']
        
        # Calculate benchmark metrics
        for name in self.benchmark_data:
            comparison['benchmarks'][name] = self.calculate_benchmark_returns(name, start_date, end_date)
        
        # Calculate relative performance
        strategy_return = self.strategy_results['summary'].get('total_return', 0)
        strategy_sharpe = self.strategy_results['summary'].get('sharpe_ratio', 0)
        strategy_max_dd = self.strategy_results['summary'].get('max_drawdown', 0)
        
        for name, benchmark_metrics in comparison['benchmarks'].items():
            comparison['comparison_metrics'][name] = {
                'excess_return': strategy_return - benchmark_metrics.get('total_return', 0),
                'sharpe_difference': strategy_sharpe - benchmark_metrics.get('sharpe_ratio', 0),
                'drawdown_difference': strategy_max_dd - benchmark_metrics.get('max_drawdown', 0)
            }
        
        return comparison