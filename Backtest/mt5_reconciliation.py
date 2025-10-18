"""
MT5 Reconciliation Tools
========================

Tools for comparing Python backtest results with MT5 execution results.
Validates signal execution and identifies discrepancies.

Last updated: 2025-10-18
Version: 1.0.0
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
import pandas as pd
import json
import logging

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False


logger = logging.getLogger(__name__)


class MT5Reconciliation:
    """
    Compare Python backtest results with MT5 execution
    
    Analyzes:
    - Signal execution rate
    - Price differences
    - Trade-by-trade comparison
    - Performance metrics comparison
    """
    
    def __init__(self):
        """Initialize reconciliation tool"""
        self.python_trades: Optional[pd.DataFrame] = None
        self.mt5_trades: Optional[pd.DataFrame] = None
        self.python_signals: Optional[pd.DataFrame] = None
        self.comparison_results: Dict[str, Any] = {}
    
    def load_python_trades(self, trades_path: Path) -> bool:
        """
        Load Python backtest trade results
        
        Args:
            trades_path: Path to Python trades CSV
        
        Returns:
            True if loaded successfully
        """
        try:
            self.python_trades = pd.read_csv(trades_path)
            self.python_trades['timestamp'] = pd.to_datetime(self.python_trades['timestamp'])
            logger.info(f"Loaded {len(self.python_trades)} Python trades from {trades_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load Python trades: {e}")
            return False
    
    def load_python_signals(self, signals_path: Path) -> bool:
        """
        Load exported Python signals
        
        Args:
            signals_path: Path to signal CSV/JSON file
        
        Returns:
            True if loaded successfully
        """
        try:
            if signals_path.suffix == '.csv':
                self.python_signals = pd.read_csv(signals_path)
            elif signals_path.suffix == '.json':
                with open(signals_path, 'r') as f:
                    data = json.load(f)
                    self.python_signals = pd.DataFrame(data['signals'])
            
            self.python_signals['timestamp'] = pd.to_datetime(self.python_signals['timestamp'])
            logger.info(f"Loaded {len(self.python_signals)} Python signals from {signals_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load Python signals: {e}")
            return False
    
    def load_mt5_history(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        magic_number: Optional[int] = None
    ) -> bool:
        """
        Load MT5 trade history
        
        Args:
            symbol: Symbol name
            start_date: Start date
            end_date: End date
            magic_number: Filter by magic number (optional)
        
        Returns:
            True if loaded successfully
        """
        if not MT5_AVAILABLE:
            logger.error("MetaTrader5 module not available")
            return False
        
        try:
            # Initialize MT5 if not already connected
            if not mt5.initialize():
                logger.error("Failed to initialize MT5")
                return False
            
            # Get deals
            deals = mt5.history_deals_get(start_date, end_date)
            
            if deals is None or len(deals) == 0:
                logger.warning("No MT5 deals found in specified period")
                return False
            
            # Convert to DataFrame
            df = pd.DataFrame(list(deals), columns=deals[0]._asdict().keys())
            
            # Filter by symbol
            df = df[df['symbol'] == symbol]
            
            # Filter by magic number if specified
            if magic_number is not None:
                df = df[df['magic'] == magic_number]
            
            # Convert time
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            self.mt5_trades = df
            logger.info(f"Loaded {len(self.mt5_trades)} MT5 deals")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load MT5 history: {e}")
            return False
        finally:
            mt5.shutdown()
    
    def load_mt5_report(self, report_path: Path) -> bool:
        """
        Load MT5 backtest report (HTML or statement file)
        
        This is an alternative to loading directly from MT5 terminal.
        
        Args:
            report_path: Path to MT5 report file
        
        Returns:
            True if loaded successfully
        """
        # TODO: Parse MT5 HTML report
        # This would require HTML parsing to extract trade data
        logger.warning("MT5 report parsing not yet implemented")
        return False
    
    def compare_signals_to_trades(self) -> Dict[str, Any]:
        """
        Compare exported signals with actual MT5 execution
        
        Returns:
            Dictionary with comparison results
        """
        if self.python_signals is None:
            logger.error("Python signals not loaded")
            return {"error": "Python signals not loaded"}
        
        if self.mt5_trades is None:
            logger.error("MT5 trades not loaded")
            return {"error": "MT5 trades not loaded"}
        
        # Filter for entry signals only
        entry_signals = self.python_signals[
            self.python_signals['signal'].isin(['BUY', 'SELL'])
        ].copy()
        
        # Match signals with MT5 trades
        matched = 0
        unmatched_signals = []
        price_diffs = []
        
        for idx, signal in entry_signals.iterrows():
            signal_time = signal['timestamp']
            signal_type = signal['signal']
            
            # Find corresponding MT5 trade (within time tolerance)
            time_tolerance = pd.Timedelta(minutes=5)
            mt5_trades_nearby = self.mt5_trades[
                (self.mt5_trades['time'] >= signal_time - time_tolerance) &
                (self.mt5_trades['time'] <= signal_time + time_tolerance) &
                (self.mt5_trades['entry'] == 1)  # Entry deals only
            ]
            
            if len(mt5_trades_nearby) > 0:
                matched += 1
                # Compare prices if available
                # Note: MT5 deal price vs Python expected price
                mt5_price = mt5_trades_nearby.iloc[0]['price']
                # Python price would need to be in signals or trades
            else:
                unmatched_signals.append({
                    'timestamp': signal_time,
                    'signal': signal_type,
                    'signal_id': signal.get('signal_id', 'N/A')
                })
        
        execution_rate = (matched / len(entry_signals)) * 100 if len(entry_signals) > 0 else 0
        
        result = {
            "total_signals": len(entry_signals),
            "matched_trades": matched,
            "unmatched_signals": len(unmatched_signals),
            "execution_rate": execution_rate,
            "unmatched_details": unmatched_signals[:10]  # First 10 for review
        }
        
        logger.info(f"Signal execution rate: {execution_rate:.1f}% ({matched}/{len(entry_signals)})")
        
        self.comparison_results['signal_execution'] = result
        return result
    
    def compare_metrics(
        self,
        python_metrics: Dict[str, float],
        mt5_metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Compare performance metrics between Python and MT5
        
        Args:
            python_metrics: Python backtest metrics
            mt5_metrics: MT5 backtest metrics
        
        Returns:
            Dictionary with metric comparisons
        """
        comparison = {}
        
        # Common metrics to compare
        metric_keys = [
            'total_trades',
            'total_pnl',
            'win_rate',
            'max_drawdown',
            'sharpe_ratio',
            'profit_factor'
        ]
        
        for key in metric_keys:
            py_value = python_metrics.get(key, 0)
            mt5_value = mt5_metrics.get(key, 0)
            
            if py_value != 0:
                diff_pct = ((mt5_value - py_value) / py_value) * 100
            else:
                diff_pct = 0
            
            comparison[key] = {
                'python': py_value,
                'mt5': mt5_value,
                'difference': mt5_value - py_value,
                'difference_pct': diff_pct
            }
        
        self.comparison_results['metrics'] = comparison
        
        logger.info("Metric comparison complete")
        for key, values in comparison.items():
            logger.info(f"  {key}: Python={values['python']:.2f}, MT5={values['mt5']:.2f}, Diff={values['difference_pct']:.1f}%")
        
        return comparison
    
    def generate_report(self, output_path: Path) -> bool:
        """
        Generate comprehensive reconciliation report
        
        Args:
            output_path: Path to save report (JSON format)
        
        Returns:
            True if report generated successfully
        """
        if not self.comparison_results:
            logger.error("No comparison results available")
            return False
        
        try:
            report = {
                "timestamp": datetime.now().isoformat(),
                "python_data": {
                    "trades": len(self.python_trades) if self.python_trades is not None else 0,
                    "signals": len(self.python_signals) if self.python_signals is not None else 0
                },
                "mt5_data": {
                    "trades": len(self.mt5_trades) if self.mt5_trades is not None else 0
                },
                "comparison": self.comparison_results
            }
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Reconciliation report saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return False
    
    def get_discrepancies(self, threshold_pct: float = 5.0) -> List[Dict[str, Any]]:
        """
        Get list of significant discrepancies
        
        Args:
            threshold_pct: Percentage threshold for significance
        
        Returns:
            List of discrepancy details
        """
        discrepancies = []
        
        if 'metrics' in self.comparison_results:
            for key, values in self.comparison_results['metrics'].items():
                if abs(values['difference_pct']) > threshold_pct:
                    discrepancies.append({
                        'metric': key,
                        'python_value': values['python'],
                        'mt5_value': values['mt5'],
                        'difference_pct': values['difference_pct']
                    })
        
        return discrepancies


def quick_reconcile(
    signals_path: Path,
    python_trades_path: Path,
    mt5_symbol: str,
    mt5_start_date: datetime,
    mt5_end_date: datetime,
    python_metrics: Dict[str, float],
    mt5_metrics: Dict[str, float],
    output_dir: Path
) -> bool:
    """
    Quick reconciliation workflow
    
    Args:
        signals_path: Path to exported signals
        python_trades_path: Path to Python trades
        mt5_symbol: MT5 symbol
        mt5_start_date: MT5 backtest start date
        mt5_end_date: MT5 backtest end date
        python_metrics: Python backtest metrics
        mt5_metrics: MT5 backtest metrics
        output_dir: Directory for output reports
    
    Returns:
        True if reconciliation completed successfully
    """
    reconciler = MT5Reconciliation()
    
    # Load data
    if not reconciler.load_python_signals(signals_path):
        return False
    
    if not reconciler.load_python_trades(python_trades_path):
        return False
    
    if not reconciler.load_mt5_history(mt5_symbol, mt5_start_date, mt5_end_date):
        logger.warning("Could not load MT5 history - skipping signal execution comparison")
    
    # Compare
    reconciler.compare_signals_to_trades()
    reconciler.compare_metrics(python_metrics, mt5_metrics)
    
    # Generate report
    report_path = output_dir / "reconciliation_report.json"
    reconciler.generate_report(report_path)
    
    # Check for major discrepancies
    discrepancies = reconciler.get_discrepancies(threshold_pct=10.0)
    if discrepancies:
        logger.warning(f"Found {len(discrepancies)} significant discrepancies:")
        for disc in discrepancies:
            logger.warning(f"  {disc['metric']}: {disc['difference_pct']:.1f}% difference")
    else:
        logger.info("No significant discrepancies found")
    
    return True
