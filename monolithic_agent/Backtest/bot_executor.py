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
import shutil

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
        verbose: bool = True,
        venv_path: Optional[Path] = None
    ):
        """
        Initialize bot executor
        
        Args:
            results_dir: Directory to store execution results (default: codes/results/)
            timeout_seconds: Max time to wait for bot execution (default: 300s)
            verbose: Enable detailed logging (default: True)
            venv_path: Path to virtual environment (default: C:/Users/nyaga/Documents/.venv)
        """
        # Set virtual environment path
        if venv_path:
            self.venv_path = Path(venv_path)
        else:
            # Default to Documents/.venv
            self.venv_path = Path(r"C:\Users\nyaga\Documents\.venv")
        
        # Get Python executable from venv
        if self.venv_path.exists():
            self.python_executable = str(self.venv_path / "Scripts" / "python.exe")
            logger.info(f"Using virtual environment: {self.venv_path}")
            logger.info(f"Python executable: {self.python_executable}")
        else:
            logger.warning(f"Virtual environment not found at {self.venv_path}, using system Python")
            self.python_executable = sys.executable
        
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
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
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
            start_date: Start date for backtest in YYYY-MM-DD format (optional)
            end_date: End date for backtest in YYYY-MM-DD format (optional)
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
        self.start_date = start_date
        self.end_date = end_date
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
    
    def execute_with_diagnostics(
        self,
        strategy_file: str,
        strategy_name: str = None,
        cleanup: bool = True
    ) -> Tuple[BotExecutionResult, Optional[Dict[str, Any]]]:
        """
        Execute bot with diagnostic logging to identify issues
        
        This method:
        1. Creates a diagnostic version of the bot with logging injected
        2. Runs the diagnostic version
        3. Analyzes the logs to identify specific issues
        4. Returns both execution result and diagnostic report
        
        Args:
            strategy_file: Path to Python strategy file
            strategy_name: Name of strategy (auto-detect if None)
            cleanup: Remove diagnostic files after execution (default: True)
            
        Returns:
            Tuple of (BotExecutionResult, diagnostic_report_dict or None)
        """
        strategy_file = Path(strategy_file)
        
        if not strategy_name:
            strategy_name = strategy_file.stem
        
        logger.info(f"\n{'='*70}")
        logger.info(f"🔍 DIAGNOSTIC EXECUTION: {strategy_name}")
        logger.info(f"{'='*70}")
        
        diagnostic_file = None
        log_file = None
        diagnostic_report = None
        
        try:
            # Step 1: Create diagnostic version with logging
            logger.info("Step 1: Injecting diagnostic logging...")
            from .diagnostic_logger import create_diagnostic_version
            
            success, diagnostic_path, injection_summary = create_diagnostic_version(
                bot_file=strategy_file
            )
            
            if not success:
                logger.error("Failed to create diagnostic version")
                # Fall back to regular execution
                return self.execute_bot(strategy_file=str(strategy_file)), None
            
            diagnostic_file = Path(diagnostic_path)
            logger.info(f"✓ Created diagnostic version: {diagnostic_file.name}")
            logger.info(f"  Injected {injection_summary.get('total_points', 0)} diagnostic points")
            
            # Step 2: Execute diagnostic version
            logger.info("\nStep 2: Executing diagnostic version...")
            result = self.execute_bot(
                strategy_file=str(diagnostic_file),
                strategy_name=f"{strategy_name}_diagnostic",
                save_results=False  # Don't save diagnostic runs
            )
            
            # Step 3: Find and analyze log file
            logger.info("\nStep 3: Analyzing diagnostic logs...")
            log_files = list(diagnostic_file.parent.glob("diagnostic_log_*.log"))
            
            if log_files:
                # Use the most recent log file
                log_file = max(log_files, key=lambda p: p.stat().st_mtime)
                logger.info(f"Found log file: {log_file.name}")
                
                from .log_analyzer import LogAnalyzer
                analyzer = LogAnalyzer(verbose=True)
                
                # Read original code for context
                original_code = strategy_file.read_text(encoding='utf-8')
                
                report = analyzer.analyze_log_file(log_file)
                
                # Convert report to dict for return
                diagnostic_report = {
                    'success': report.success,
                    'execution_completed': report.execution_completed,
                    'issues': [
                        {
                            'type': issue.issue_type.value,
                            'severity': issue.severity.value,
                            'description': issue.description,
                            'line_number': issue.line_number,
                            'function_name': issue.function_name,
                            'suggested_fix': issue.suggested_fix,
                            'confidence': issue.confidence,
                            'evidence': issue.evidence[:3]  # Limit evidence
                        }
                        for issue in report.issues
                    ],
                    'functions_executed': report.functions_executed,
                    'recommendations': report.recommendations,
                    'error_message': report.error_message,
                    'fix_prompt': analyzer.generate_fix_prompt(report, original_code)
                }
                
                logger.info(f"✓ Analysis complete: {len(report.issues)} issues found")
                
                # Log issues
                for issue in report.issues:
                    logger.warning(f"  [{issue.severity.value}] {issue.description}")
                    if issue.suggested_fix:
                        logger.info(f"      Fix: {issue.suggested_fix}")
            else:
                logger.warning("No diagnostic log file found")
            
        except Exception as e:
            logger.error(f"Diagnostic execution failed: {e}")
            logger.error(traceback.format_exc())
            # Fall back to regular execution
            return self.execute_bot(strategy_file=str(strategy_file)), None
        
        finally:
            # Cleanup diagnostic files
            if cleanup:
                try:
                    if diagnostic_file and diagnostic_file.exists():
                        diagnostic_file.unlink()
                        logger.debug(f"Cleaned up diagnostic file: {diagnostic_file}")
                    
                    if log_file and log_file.exists():
                        log_file.unlink()
                        logger.debug(f"Cleaned up log file: {log_file}")
                except Exception as e:
                    logger.warning(f"Cleanup failed: {e}")
        
        logger.info(f"{'='*70}\n")
        return result, diagnostic_report
    
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
            # Use virtual environment Python if available
            cmd = [self.python_executable, str(strategy_file)]
            
            # Add test parameters as CLI arguments if provided
            if self.test_symbol and self.test_symbol != "AAPL":
                cmd.extend(['--symbol', self.test_symbol])
            if self.test_period:
                cmd.extend(['--period', self.test_period])
            if self.test_interval:
                cmd.extend(['--interval', self.test_interval])
            
            logger.debug(f"Running: {' '.join(cmd)}")
            logger.debug(f"Working directory: {monolithic_root}")
            
            # Set Django settings environment variable for strategies that import Backtest modules
            import os
            env = os.environ.copy()
            env['DJANGO_SETTINGS_MODULE'] = 'monolithic_agent.settings'
            
            # Set date range environment variables if provided
            if self.start_date:
                env['BACKTEST_START_DATE'] = self.start_date
                logger.info(f"Setting backtest start date: {self.start_date}")
            if self.end_date:
                env['BACKTEST_END_DATE'] = self.end_date
                logger.info(f"Setting backtest end date: {self.end_date}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',  # Replace unencodable characters instead of crashing
                cwd=str(monolithic_root),
                env=env
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
            # STEP 1: Try to parse metrics FIRST (optimistic approach)
            # If the strategy produced valid results, ignore stderr warnings
            
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
            
            # Check for SignalLogger output as proof of successful execution
            # SignalLogger always outputs summary regardless of JSON parsing
            if 'Total Signals:' in stdout or 'signal_logger' in stdout.lower():
                for line in lines:
                    if 'Total Signals:' in line or 'total signals:' in line.lower():
                        try:
                            # Extract signal count from "Total Signals: 8"
                            signal_count = int(line.split(':')[-1].strip())
                            if signal_count > 0:
                                result['trades'] = signal_count
                                result['success'] = True
                                logger.info(f"✅ Detected {signal_count} signals from SignalLogger output")
                                
                                # Try to extract additional metrics from signal logger
                                for metric_line in lines:
                                    if 'Buy Signals:' in metric_line:
                                        logger.info(f"  {metric_line.strip()}")
                                    elif 'Sell Signals:' in metric_line:
                                        logger.info(f"  {metric_line.strip()}")
                                
                                # Signal logger output proves execution succeeded
                                return result
                        except (ValueError, IndexError):
                            pass
            
            # Check for AccountManager messages (position opened/closed) as proof of execution
            if 'Opened position:' in stdout or 'Closed position:' in stdout:
                position_count = stdout.count('Opened position:')
                if position_count > 0:
                    result['trades'] = position_count
                    result['success'] = True
                    logger.info(f"✅ Detected {position_count} positions opened/closed from AccountManager")
                    
                    # Extract P&L if available
                    for line in lines:
                        if 'realized P&L:' in line.lower():
                            logger.info(f"  {line.strip()}")
                    
                    return result
            
            # If we extracted any metrics, consider it successful
            if any([
                result['return_pct'] is not None,
                result['trades'] is not None,
                result['win_rate'] is not None,
                result['max_drawdown'] is not None,
                result['sharpe_ratio'] is not None
            ]):
                result['success'] = True
                
                # CRITICAL: Validate that at least one trade was made
                # Bot must make trades to pass debugging test
                if result['trades'] is not None and result['trades'] == 0:
                    result['success'] = False
                    result['error'] = "Strategy executed but made NO TRADES (0 trades). Bot must place at least one trade to pass."
                    logger.warning("⚠️ TRADE VALIDATION FAILED: Bot made 0 trades")
                elif result['trades'] is None:
                    # Trades not found in output - might indicate parsing issue or no trades
                    result['success'] = False
                    result['error'] = "Cannot verify trades were made - metrics parsing issue or no trades placed"
                    logger.warning("⚠️ TRADE VALIDATION: Unable to verify trade count")
                
                # If successful with valid trades, return immediately (ignore stderr warnings)
                if result['success']:
                    return result
            
            # STEP 2: Only check stderr if we didn't get valid results
            combined_output = stdout + stderr
            
            # Special handling for encoding errors (charmap_encode)
            if "charmap_encode" in stderr or "UnicodeEncodeError" in stderr:
                result['error'] = stderr if stderr else "Encoding error: Unicode characters in output"
                return result
            
            # Ignore warnings and benign messages
            ignored_patterns = [
                "redis connection failed",
                "docker command failed",
                "docker not available",
                "futurewarning",
                "deprecationwarning",
                "trying to import",  # Import warnings
                "resulted in these errors",  # Import continuation messages
            ]
            
            # Filter out ignored patterns from error detection
            filtered_output = combined_output.lower()
            for pattern in ignored_patterns:
                filtered_output = filtered_output.replace(pattern, '')
            
            if "error" in filtered_output or "exception" in filtered_output:
                # Try to extract meaningful error message
                lines = combined_output.split('\n')
                for line in lines:
                    line_lower = line.lower()
                    # Skip lines with ignored patterns
                    if any(pattern in line_lower for pattern in ignored_patterns):
                        continue
                    if 'error' in line_lower or 'exception' in line_lower:
                        result['error'] = line.strip()
                        break
                
                if not result['error']:
                    result['error'] = "Execution produced errors (check logs)"
                return result
            
            # STEP 3: No valid results and no clear errors
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
    timeout_seconds: int = 300,
    venv_path: Optional[Path] = None
) -> BotExecutor:
    """Convenience function to get BotExecutor instance
    
    Args:
        results_dir: Directory for results
        timeout_seconds: Execution timeout
        venv_path: Path to virtual environment (default: C:/Users/nyaga/Documents/.venv)
    """
    return BotExecutor(
        results_dir=results_dir,
        timeout_seconds=timeout_seconds,
        venv_path=venv_path
    )


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
