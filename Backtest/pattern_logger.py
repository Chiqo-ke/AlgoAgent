"""
Pattern Logger - Logs pattern detection results for debugging
==============================================================

Logs every row of data with pattern analysis results (True/False)
to help debug strategy step execution.

Features:
- Sequential row-by-row logging
- Pattern detection results with True/False
- Timestamps and data values
- Easy CSV export for analysis
- Per-strategy log files

Version: 1.0.0
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
import csv

logger = logging.getLogger(__name__)


class PatternLogger:
    """
    Logs pattern detection results for each data row during backtesting
    """
    
    def __init__(self, strategy_id: str, signals_dir: Optional[Path] = None):
        """
        Initialize Pattern Logger
        
        Args:
            strategy_id: Unique strategy identifier
            signals_dir: Directory to save pattern logs (default: ./signals)
        """
        self.strategy_id = strategy_id
        self.signals_dir = signals_dir or Path(__file__).parent / "signals"
        self.signals_dir.mkdir(exist_ok=True)
        
        # Create pattern log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.pattern_log_file = self.signals_dir / f"{strategy_id}_patterns_{timestamp}.csv"
        
        # Pattern log buffer
        self.pattern_logs: List[Dict[str, Any]] = []
        
        # Initialize CSV with headers
        self._init_pattern_log()
        
        logger.info(f"PatternLogger initialized: {self.pattern_log_file}")
    
    def _init_pattern_log(self):
        """Initialize pattern log CSV file with headers"""
        headers = [
            'timestamp',
            'symbol',
            'step_id',
            'step_title',
            'pattern_condition',
            'pattern_found',  # True/False
            'close',
            'open',
            'high',
            'low',
            'volume',
            'indicator_values',
            'notes'
        ]
        
        with open(self.pattern_log_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
    
    def log_pattern(
        self,
        timestamp: datetime,
        symbol: str,
        step_id: str,
        step_title: str,
        pattern_condition: str,
        pattern_found: bool,
        market_data: Dict[str, Any],
        indicator_values: Optional[Dict[str, float]] = None,
        notes: str = ""
    ):
        """
        Log a pattern detection result
        
        Args:
            timestamp: Current bar timestamp
            symbol: Trading symbol
            step_id: Strategy step identifier
            step_title: Human-readable step description
            pattern_condition: The condition being checked (e.g., "EMA_30 > EMA_50")
            pattern_found: Whether pattern was found (True/False)
            market_data: OHLCV data for current bar
            indicator_values: Dictionary of indicator values
            notes: Additional notes
        """
        log_entry = {
            'timestamp': timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            'symbol': symbol,
            'step_id': step_id,
            'step_title': step_title,
            'pattern_condition': pattern_condition,
            'pattern_found': pattern_found,
            'close': market_data.get('close', 0),
            'open': market_data.get('open', 0),
            'high': market_data.get('high', 0),
            'low': market_data.get('low', 0),
            'volume': market_data.get('volume', 0),
            'indicator_values': str(indicator_values or {}),
            'notes': notes
        }
        
        # Append to buffer
        self.pattern_logs.append(log_entry)
        
        # Write to file immediately (for real-time debugging)
        with open(self.pattern_log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=log_entry.keys())
            writer.writerow(log_entry)
    
    def get_pattern_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics of pattern detection
        
        Returns:
            Dictionary with pattern statistics
        """
        if not self.pattern_logs:
            return {
                'total_rows': 0,
                'patterns_found': 0,
                'patterns_not_found': 0,
                'detection_rate': 0.0,
                'log_file': str(self.pattern_log_file) if self.pattern_log_file else 'N/A'
            }
        
        total = len(self.pattern_logs)
        found = sum(1 for log in self.pattern_logs if log['pattern_found'])
        not_found = total - found
        
        return {
            'total_rows': total,
            'patterns_found': found,
            'patterns_not_found': not_found,
            'detection_rate': (found / total * 100) if total > 0 else 0.0,
            'log_file': str(self.pattern_log_file)
        }
    
    def export_to_dataframe(self) -> pd.DataFrame:
        """Export pattern logs to DataFrame for analysis"""
        return pd.DataFrame(self.pattern_logs)
    
    def close(self):
        """Close the logger and print summary"""
        summary = self.get_pattern_summary()
        logger.info(f"Pattern Detection Summary:")
        logger.info(f"  Total Rows Analyzed: {summary['total_rows']}")
        logger.info(f"  Patterns Found: {summary['patterns_found']}")
        logger.info(f"  Patterns Not Found: {summary['patterns_not_found']}")
        logger.info(f"  Detection Rate: {summary['detection_rate']:.2f}%")
        logger.info(f"  Log saved to: {summary['log_file']}")
