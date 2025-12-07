"""
Bot Executor - Execute and Test Generated Trading Strategies
=============================================================

This module handles:
1. Running newly generated trading bots
2. Capturing execution results and metrics
3. Storing results for future reference and analysis
4. Handling execution errors gracefully
5. Generating performance summaries

Features:
- Automatic bot execution after generation
- Timeout handling for long-running backtests
- Result persistence (JSON, CSV, SQLite)
- Performance metrics calculation
- Error logging and recovery
- Multi-strategy parallel execution (optional)

Last updated: 2025-12-03
Version: 1.0.0
"""

import os
import sys
import json
import time
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import traceback
from dataclasses import dataclass, asdict
import sqlite3

logger = logging.getLogger(__name__)


@dataclass
class BotExecutionResult:
    """Result of executing a bot/strategy"""
    strategy_name: str
    file_path: str
    execution_timestamp: datetime
    success: bool
    duration_seconds: float
    error: Optional[str] = None
    
    # Backtest metrics
    return_pct: Optional[float] = None
    trades: Optional[int] = None
    win_rate: Optional[float] = None
    max_drawdown: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    
    # Execution details
    output_log: Optional[str] = None
    stderr_log: Optional[str] = None
    results_file: Optional[str] = None
    json_results: Optional[Dict[str, Any]] = None
    
    # Metadata
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    test_symbol: str = "AAPL"
    test_period_days: int = 365


class BotExecutor:
    """Execute and test generated trading bots"""
    
    def __init__(
        self,
        results_dir: Optional[str] = None,
        timeout_seconds: int = 300,
        verbose: bool = True
    ):
        """
        Initialize bot executor
        
        Args:
            results_dir: Directory to store execution results (default: codes/results/)
            timeout_seconds: Max time to wait for bot execution (default: 300s)
            verbose: Enable detailed logging (default: True)
        """
        self.results_dir = Path(results_dir or "Backtest/codes/results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        self.timeout_seconds = timeout_seconds
        self.verbose = verbose
        
        # Subdirectories for different result types
        self.logs_dir = self.results_dir / "logs"
        self.metrics_dir = self.results_dir / "metrics"
        self.json_dir = self.results_dir / "json"
        
        for d in [self.logs_dir, self.metrics_dir, self.json_dir]:
            d.mkdir(exist_ok=True)
        
        # Database for results history
        self.db_path = self.results_dir / "execution_history.db"
        self._init_database()
        
        logger.info(
            f"BotExecutor initialized "
            f"(results_dir={self.results_dir}, timeout={timeout_seconds}s)"
        )
    
    def _init_database(self):
        """Initialize SQLite database for results history"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bot_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    execution_timestamp TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    duration_seconds REAL NOT NULL,
                    error TEXT,
                    return_pct REAL,
                    trades INTEGER,
                    win_rate REAL,
                    max_drawdown REAL,
                    sharpe_ratio REAL,
                    test_symbol TEXT,
                    test_period_days INTEGER,
                    results_file TEXT,
                    json_results TEXT
                )
            """)
            
            conn.commit()
            conn.close()
            logger.debug("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
    
    def execute_bot(
        self,
        strategy_file: str,
        strategy_name: str = None,
        description: str = None,
        parameters: Dict[str, Any] = None,
        test_symbol: str = "AAPL",
        test_period_days: int = 365,
        save_results: bool = True
    ) -> BotExecutionResult:
        """
        Execute a generated trading bot/strategy
        
        Args:
            strategy_file: Path to Python strategy file
            strategy_name: Name of strategy (auto-detect if None)
            description: Strategy description (for metadata)
            parameters: Strategy parameters used
            test_symbol: Symbol to test with (default: AAPL)
            test_period_days: Days of historical data (default: 365)
            save_results: Save results to disk (default: True)
        
        Returns:
            BotExecutionResult with execution details and metrics
        """
        start_time = time.time()
        strategy_file = Path(strategy_file)
        
        if not strategy_name:
            strategy_name = strategy_file.stem
        
        logger.info(f"\n{'='*70}")
        logger.info(f"Executing Bot: {strategy_name}")
        logger.info(f"File: {strategy_file}")
        logger.info(f"{'='*70}")
        
        # Store test parameters for CLI argument passing
        self.test_symbol = test_symbol
        # Convert days to period string if parameters not provided
        if parameters and 'test_period' in parameters:
            self.test_period = parameters['test_period']
        else:
            # Map days to period string
            period_map = {30: '1mo', 90: '3mo', 180: '6mo', 365: '1y', 730: '2y', 1825: '5y'}
            self.test_period = period_map.get(test_period_days, f'{test_period_days}d')
        self.test_interval = parameters.get('test_interval', '1d') if parameters else '1d'
        
        result = BotExecutionResult(
            strategy_name=strategy_name,
            file_path=str(strategy_file),
            execution_timestamp=datetime.now(),
            success=False,
            duration_seconds=0,
            description=description,
            parameters=parameters,
            test_symbol=test_symbol,
            test_period_days=test_period_days
        )
        
        try:
            # Verify file exists
            if not strategy_file.exists():
                result.error = f"File not found: {strategy_file}"
                logger.error(result.error)
                return result
            
            # Execute the strategy
            logger.info(f"Starting execution (timeout: {self.timeout_seconds}s)...")
            
            output, stderr = self._run_strategy(strategy_file)
            
            # Parse results from output
            parsed_results = self._parse_execution_output(output, stderr)
            
            # Update result with parsed metrics
            result.success = parsed_results.get('success', False)
            result.return_pct = parsed_results.get('return_pct')
            result.trades = parsed_results.get('trades')
            result.win_rate = parsed_results.get('win_rate')
            result.max_drawdown = parsed_results.get('max_drawdown')
            result.sharpe_ratio = parsed_results.get('sharpe_ratio')
            result.output_log = output
            result.stderr_log = stderr
            result.json_results = parsed_results.get('json_results')
            
            if not result.success:
                result.error = parsed_results.get('error', 'Unknown error during execution')
                logger.warning(f"Execution completed with errors: {result.error}")
            else:
                logger.info(f"[OK] Execution completed successfully")
                logger.info(f"  Return: {result.return_pct:.2f}%" if result.return_pct else "")
                logger.info(f"  Trades: {result.trades}" if result.trades else "")
                logger.info(f"  Win Rate: {result.win_rate:.1%}" if result.win_rate else "")
            
        except subprocess.TimeoutExpired:
            result.error = f"Execution timeout (>{self.timeout_seconds}s)"
            logger.error(result.error)
        except Exception as e:
            result.error = f"Execution failed: {str(e)}"
            logger.error(result.error)
            logger.error(traceback.format_exc())
        finally:
            result.duration_seconds = time.time() - start_time
            
            # Save results
            if save_results:
                self._save_execution_result(result)
            
            logger.info(f"Total execution time: {result.duration_seconds:.2f}s")
            logger.info(f"{'='*70}\n")
        
        return result
    
    def _run_strategy(self, strategy_file: Path) -> Tuple[str, str]:
        """
        Run strategy file and capture output
        
        Args:
            strategy_file: Path to strategy Python file
        
        Returns:
            Tuple of (stdout, stderr)
        """
        try:
            # Find the monolithic_agent root directory (where manage.py exists)
            # This ensures Backtest module can be imported correctly
            current_dir = Path(__file__).resolve().parent
            while current_dir.parent != current_dir:
                if (current_dir / "manage.py").exists():
                    monolithic_root = current_dir
                    break
                current_dir = current_dir.parent
            else:
                # Fallback: use current file's parent's parent (Backtest -> monolithic_agent)
                monolithic_root = Path(__file__).resolve().parent.parent
            
            # Build command with CLI arguments for symbol, period, interval
            cmd = [sys.executable, str(strategy_file)]
            
            # Add test parameters as CLI arguments if provided
            if self.test_symbol and self.test_symbol != "AAPL":
                cmd.extend(['--symbol', self.test_symbol])
            if self.test_period:
                cmd.extend(['--period', self.test_period])
            if self.test_interval:
                cmd.extend(['--interval', self.test_interval])
            
            logger.debug(f"Running: {' '.join(cmd)}")
            logger.debug(f"Working directory: {monolithic_root}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',  # Replace unencodable characters instead of crashing
                cwd=str(monolithic_root)
            )
            
            try:
                stdout, stderr = process.communicate(timeout=self.timeout_seconds)
                return stdout, stderr
            except subprocess.TimeoutExpired:
                process.kill()
                raise
        
        except Exception as e:
            logger.error(f"Failed to run strategy: {e}")
            raise
    
    def _parse_execution_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """
        Parse execution output to extract metrics
        
        Args:
            stdout: Standard output from strategy execution
            stderr: Standard error from strategy execution
        
        Returns:
            Dictionary with parsed metrics
        """
        result = {
            'success': False,
            'error': None,
            'return_pct': None,
            'trades': None,
            'win_rate': None,
            'max_drawdown': None,
            'sharpe_ratio': None,
            'json_results': None
        }
        
        try:
            # Check for errors first
            combined_output = stdout + stderr
            
            # Special handling for encoding errors (charmap_encode)
            if "charmap_encode" in stderr or "UnicodeEncodeError" in stderr:
                result['error'] = stderr if stderr else "Encoding error: Unicode characters in output"
                return result
            
            if "error" in combined_output.lower() or "exception" in combined_output.lower():
                # Try to extract meaningful error message
                lines = combined_output.split('\n')
                for line in lines:
                    if 'error' in line.lower() or 'exception' in line.lower():
                        result['error'] = line.strip()
                        break
                
                if not result['error']:
                    result['error'] = "Execution produced errors (check logs)"
                return result
            
            # Try to parse JSON results if present
            json_match = self._extract_json(stdout)
            if json_match:
                result['json_results'] = json_match
                result['success'] = True
                
                # Extract key metrics from JSON
                if isinstance(json_match, dict):
                    result['return_pct'] = json_match.get('return_pct') or json_match.get('Return [%]')
                    result['trades'] = json_match.get('trades') or json_match.get('# Trades')
                    result['win_rate'] = json_match.get('win_rate') or json_match.get('Win Rate [%]')
                    result['max_drawdown'] = json_match.get('max_drawdown') or json_match.get('Max. Drawdown [%]')
                    result['sharpe_ratio'] = json_match.get('sharpe_ratio') or json_match.get('Sharpe Ratio')
                
                return result
            
            # Parse metrics from text output
            lines = stdout.split('\n')
            
            for line in lines:
                line_lower = line.lower()
                
                if 'return' in line_lower and '%' in line:
                    try:
                        value = float(line.split()[-1].strip('%'))
                        result['return_pct'] = value
                    except (ValueError, IndexError):
                        pass
                
                elif 'trades' in line_lower:
                    try:
                        value = int(line.split()[-1])
                        result['trades'] = value
                    except (ValueError, IndexError):
                        pass
                
                elif 'win rate' in line_lower or 'win_rate' in line_lower:
                    try:
                        value = float(line.split()[-1].strip('%'))
                        result['win_rate'] = value / 100  # Convert to decimal
                    except (ValueError, IndexError):
                        pass
                
                elif 'drawdown' in line_lower:
                    try:
                        value = float(line.split()[-1].strip('%'))
                        result['max_drawdown'] = value
                    except (ValueError, IndexError):
                        pass
                
                elif 'sharpe' in line_lower:
                    try:
                        value = float(line.split()[-1])
                        result['sharpe_ratio'] = value
                    except (ValueError, IndexError):
                        pass
            
            # If we extracted any metrics, consider it successful
            if any([
                result['return_pct'] is not None,
                result['trades'] is not None,
                result['win_rate'] is not None,
                result['max_drawdown'] is not None,
                result['sharpe_ratio'] is not None
            ]):
                result['success'] = True
            else:
                # Check if output looks successful anyway
                if stdout and not stderr:
                    result['success'] = True
                    result['error'] = "Output captured but metrics not parsed"
                else:
                    result['error'] = "No results or metrics found in output"
        
        except Exception as e:
            logger.error(f"Failed to parse execution output: {e}")
            result['error'] = f"Parse error: {str(e)}"
        
        return result
    
    def _extract_json(self, text: str) -> Optional[Dict]:
        """Extract JSON from text output"""
        try:
            # Look for JSON blocks in output
            import re
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(json_pattern, text)
            
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            logger.debug(f"JSON extraction failed: {e}")
        
        return None
    
    def _save_execution_result(self, result: BotExecutionResult):
        """Save execution result to disk and database"""
        try:
            timestamp = result.execution_timestamp.strftime("%Y%m%d_%H%M%S")
            base_name = f"{result.strategy_name}_{timestamp}"
            
            # Save execution log
            if result.output_log:
                log_file = self.logs_dir / f"{base_name}.log"
                log_file.write_text(result.output_log, encoding='utf-8')
                result.results_file = str(log_file)
                logger.debug(f"Saved log to {log_file}")
            
            # Save JSON results
            json_file = self.json_dir / f"{base_name}.json"
            json_data = {
                'strategy_name': result.strategy_name,
                'file_path': result.file_path,
                'execution_timestamp': result.execution_timestamp.isoformat(),
                'success': result.success,
                'duration_seconds': result.duration_seconds,
                'error': result.error,
                'return_pct': result.return_pct,
                'trades': result.trades,
                'win_rate': result.win_rate,
                'max_drawdown': result.max_drawdown,
                'sharpe_ratio': result.sharpe_ratio,
                'test_symbol': result.test_symbol,
                'test_period_days': result.test_period_days,
                'description': result.description,
                'parameters': result.parameters,
                'json_results': result.json_results
            }
            
            json_file.write_text(json.dumps(json_data, indent=2, default=str), encoding='utf-8')
            logger.debug(f"Saved JSON results to {json_file}")
            
            # Save metrics summary
            metrics_file = self.metrics_dir / f"{base_name}.txt"
            metrics_text = self._format_metrics_summary(result)
            metrics_file.write_text(metrics_text, encoding='utf-8')
            logger.debug(f"Saved metrics to {metrics_file}")
            
            # Save to database
            self._save_to_database(result)
            
        except Exception as e:
            logger.error(f"Failed to save execution result: {e}")
    
    def _format_metrics_summary(self, result: BotExecutionResult) -> str:
        """Format metrics as readable text"""
        lines = [
            "=" * 70,
            f"Bot Execution Results - {result.strategy_name}",
            "=" * 70,
            f"",
            f"File: {result.file_path}",
            f"Timestamp: {result.execution_timestamp.isoformat()}",
            f"Duration: {result.duration_seconds:.2f}s",
            f"Status: {'SUCCESS' if result.success else 'FAILED'}",
            f"",
        ]
        
        if result.error:
            lines.append(f"Error: {result.error}")
            lines.append("")
        
        if result.description:
            lines.append(f"Description: {result.description}")
            lines.append("")
        
        lines.extend([
            "METRICS:",
            "-" * 70,
            f"  Return: {result.return_pct:.2f}%" if result.return_pct is not None else "  Return: N/A",
            f"  Trades: {result.trades}" if result.trades is not None else "  Trades: N/A",
            f"  Win Rate: {result.win_rate:.1%}" if result.win_rate is not None else "  Win Rate: N/A",
            f"  Max Drawdown: {result.max_drawdown:.2f}%" if result.max_drawdown is not None else "  Max Drawdown: N/A",
            f"  Sharpe Ratio: {result.sharpe_ratio:.2f}" if result.sharpe_ratio is not None else "  Sharpe Ratio: N/A",
            f"",
            "TEST CONFIGURATION:",
            "-" * 70,
            f"  Symbol: {result.test_symbol}",
            f"  Period: {result.test_period_days} days",
            f"",
        ])
        
        if result.parameters:
            lines.append("PARAMETERS:")
            lines.append("-" * 70)
            for key, value in result.parameters.items():
                lines.append(f"  {key}: {value}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _save_to_database(self, result: BotExecutionResult):
        """Save result to SQLite database"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO bot_executions 
                (strategy_name, file_path, execution_timestamp, success, duration_seconds,
                 error, return_pct, trades, win_rate, max_drawdown, sharpe_ratio,
                 test_symbol, test_period_days, results_file, json_results)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.strategy_name,
                result.file_path,
                result.execution_timestamp.isoformat(),
                result.success,
                result.duration_seconds,
                result.error,
                result.return_pct,
                result.trades,
                result.win_rate,
                result.max_drawdown,
                result.sharpe_ratio,
                result.test_symbol,
                result.test_period_days,
                result.results_file,
                json.dumps(result.json_results) if result.json_results else None
            ))
            
            conn.commit()
            conn.close()
            logger.debug("Result saved to database")
        except Exception as e:
            logger.error(f"Failed to save to database: {e}")
    
    def get_strategy_history(self, strategy_name: str) -> List[BotExecutionResult]:
        """Get execution history for a specific strategy"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM bot_executions
                WHERE strategy_name = ?
                ORDER BY execution_timestamp DESC
            """, (strategy_name,))
            
            rows = cursor.fetchall()
            conn.close()
            
            results = []
            for row in rows:
                result = BotExecutionResult(
                    strategy_name=row['strategy_name'],
                    file_path=row['file_path'],
                    execution_timestamp=datetime.fromisoformat(row['execution_timestamp']),
                    success=bool(row['success']),
                    duration_seconds=row['duration_seconds'],
                    error=row['error'],
                    return_pct=row['return_pct'],
                    trades=row['trades'],
                    win_rate=row['win_rate'],
                    max_drawdown=row['max_drawdown'],
                    sharpe_ratio=row['sharpe_ratio'],
                    test_symbol=row['test_symbol'],
                    test_period_days=row['test_period_days'],
                    results_file=row['results_file']
                )
                results.append(result)
            
            return results
        except Exception as e:
            logger.error(f"Failed to get strategy history: {e}")
            return []
    
    def get_all_executions(self, limit: int = 100) -> List[BotExecutionResult]:
        """Get all execution results"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM bot_executions
                ORDER BY execution_timestamp DESC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            results = []
            for row in rows:
                result = BotExecutionResult(
                    strategy_name=row['strategy_name'],
                    file_path=row['file_path'],
                    execution_timestamp=datetime.fromisoformat(row['execution_timestamp']),
                    success=bool(row['success']),
                    duration_seconds=row['duration_seconds'],
                    error=row['error'],
                    return_pct=row['return_pct'],
                    trades=row['trades'],
                    win_rate=row['win_rate'],
                    max_drawdown=row['max_drawdown'],
                    sharpe_ratio=row['sharpe_ratio'],
                    test_symbol=row['test_symbol'],
                    test_period_days=row['test_period_days'],
                    results_file=row['results_file']
                )
                results.append(result)
            
            return results
        except Exception as e:
            logger.error(f"Failed to get all executions: {e}")
            return []
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary across all executions"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_executions,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                    AVG(return_pct) as avg_return,
                    AVG(trades) as avg_trades,
                    AVG(win_rate) as avg_win_rate,
                    AVG(max_drawdown) as avg_max_drawdown,
                    AVG(sharpe_ratio) as avg_sharpe_ratio,
                    AVG(duration_seconds) as avg_duration
                FROM bot_executions
            """)
            
            row = cursor.fetchone()
            conn.close()
            
            if row and row[0] > 0:  # At least one execution
                return {
                    'total_executions': row[0],
                    'successful': row[1],
                    'success_rate': row[1] / row[0] if row[0] > 0 else 0,
                    'avg_return_pct': row[2],
                    'avg_trades': row[3],
                    'avg_win_rate': row[4],
                    'avg_max_drawdown': row[5],
                    'avg_sharpe_ratio': row[6],
                    'avg_duration_seconds': row[7]
                }
        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
        
        return {}


def get_bot_executor(
    results_dir: Optional[str] = None,
    timeout_seconds: int = 300
) -> BotExecutor:
    """Convenience function to get BotExecutor instance"""
    return BotExecutor(results_dir=results_dir, timeout_seconds=timeout_seconds)


if __name__ == "__main__":
    import argparse
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description='Execute and test trading bots')
    parser.add_argument('bot_file', help='Path to bot/strategy Python file')
    parser.add_argument('-n', '--name', help='Strategy name')
    parser.add_argument('-d', '--description', help='Strategy description')
    parser.add_argument('--symbol', default='AAPL', help='Test symbol (default: AAPL)')
    parser.add_argument('--days', type=int, default=365, help='Test period in days (default: 365)')
    parser.add_argument('--timeout', type=int, default=300, help='Execution timeout in seconds (default: 300)')
    parser.add_argument('--history', action='store_true', help='Show execution history')
    parser.add_argument('--summary', action='store_true', help='Show performance summary')
    
    args = parser.parse_args()
    
    executor = get_bot_executor(timeout_seconds=args.timeout)
    
    if args.summary:
        summary = executor.get_performance_summary()
        print("\n📊 PERFORMANCE SUMMARY")
        print("=" * 70)
        for key, value in summary.items():
            if isinstance(value, float):
                print(f"{key:.<50} {value:>10.2f}")
            else:
                print(f"{key:.<50} {value:>10}")
    
    elif args.history and args.name:
        history = executor.get_strategy_history(args.name)
        print(f"\n📋 EXECUTION HISTORY - {args.name}")
        print("=" * 70)
        for result in history:
            status = "✓" if result.success else "✗"
            print(f"{status} {result.execution_timestamp.isoformat()}")
            print(f"  Return: {result.return_pct:.2f}%" if result.return_pct else "  Return: N/A")
            print(f"  Trades: {result.trades}" if result.trades else "  Trades: N/A")
            print()
    
    else:
        # Execute bot
        result = executor.execute_bot(
            strategy_file=args.bot_file,
            strategy_name=args.name,
            description=args.description,
            test_symbol=args.symbol,
            test_period_days=args.days
        )
        
        print(f"\n{'='*70}")
        print("EXECUTION SUMMARY")
        print(f"{'='*70}")
        print(f"Status: {'SUCCESS ✓' if result.success else 'FAILED ✗'}")
        print(f"Duration: {result.duration_seconds:.2f}s")
        if result.error:
            print(f"Error: {result.error}")
        else:
            if result.return_pct is not None:
                print(f"Return: {result.return_pct:.2f}%")
            if result.trades is not None:
                print(f"Trades: {result.trades}")
            if result.win_rate is not None:
                print(f"Win Rate: {result.win_rate:.1%}")
        print(f"Results saved to: {result.results_file}")
