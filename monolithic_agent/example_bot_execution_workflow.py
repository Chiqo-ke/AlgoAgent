"""
Example: Bot Execution Integration Demo
========================================

This example demonstrates:
1. Generating a strategy with auto-execution
2. Capturing and displaying execution results
3. Retrieving execution history
4. Analyzing performance metrics

Run this to see the complete workflow in action!

Command:
    python example_bot_execution_workflow.py

Expected Output:
    - Strategy generation
    - Bot execution
    - Result capture
    - Metrics display
    - History retrieval
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)8s | %(message)s'
)

logger = logging.getLogger(__name__)


def example_1_generate_and_execute():
    """Example 1: Generate strategy and execute it"""
    logger.info("=" * 80)
    logger.info("EXAMPLE 1: Generate Strategy and Auto-Execute")
    logger.info("=" * 80)
    
    try:
        from Backtest.gemini_strategy_generator import GeminiStrategyGenerator
        from Backtest.bot_executor import BOT_EXECUTOR_AVAILABLE
        
        if not BOT_EXECUTOR_AVAILABLE:
            logger.warning("BotExecutor not available. Skipping execution.")
            return
        
        # Create generator
        logger.info("\n1. Initializing strategy generator...")
        generator = GeminiStrategyGenerator()
        logger.info("   ✓ Generator ready")
        
        # Generate strategy with auto-execution
        logger.info("\n2. Generating strategy with auto-execution...")
        strategy_desc = "Simple moving average crossover strategy with 10-day and 30-day averages"
        
        output_file, execution_result = generator.generate_and_save(
            description=strategy_desc,
            output_path="Backtest/codes/example_ma_strategy.py",
            strategy_name="ExampleMAStrategy",
            execute_after_generation=True,
            test_symbol="AAPL",
            test_period_days=365
        )
        logger.info(f"   ✓ Strategy saved to {output_file}")
        
        # Display results
        if execution_result:
            logger.info("\n3. Execution Results:")
            logger.info(f"   Status: {'SUCCESS ✓' if execution_result.success else 'FAILED ✗'}")
            logger.info(f"   Duration: {execution_result.duration_seconds:.2f}s")
            
            if execution_result.success:
                if execution_result.return_pct is not None:
                    logger.info(f"   Return: {execution_result.return_pct:.2f}%")
                if execution_result.trades is not None:
                    logger.info(f"   Trades: {execution_result.trades}")
                if execution_result.win_rate is not None:
                    logger.info(f"   Win Rate: {execution_result.win_rate:.1%}")
                if execution_result.max_drawdown is not None:
                    logger.info(f"   Max Drawdown: {execution_result.max_drawdown:.2f}%")
                if execution_result.sharpe_ratio is not None:
                    logger.info(f"   Sharpe Ratio: {execution_result.sharpe_ratio:.2f}")
            else:
                logger.warning(f"   Error: {execution_result.error}")
            
            logger.info(f"   Results file: {execution_result.results_file}")
        else:
            logger.warning("   No execution result (BotExecutor unavailable)")
        
        return output_file, execution_result
    
    except ImportError as e:
        logger.error(f"Import error: {e}")
        return None, None
    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)
        return None, None


def example_2_manual_execution():
    """Example 2: Manually execute an existing bot file"""
    logger.info("\n" + "=" * 80)
    logger.info("EXAMPLE 2: Manual Bot Execution")
    logger.info("=" * 80)
    
    try:
        from Backtest.bot_executor import get_bot_executor
        
        # Check if example file exists
        example_file = Path("Backtest/codes/example_strategy.py")
        
        if not example_file.exists():
            logger.warning(f"Example file not found: {example_file}")
            logger.info("Skipping this example...")
            return None
        
        logger.info(f"\n1. Executing bot: {example_file.name}")
        
        executor = get_bot_executor(timeout_seconds=120)
        
        result = executor.execute_bot(
            strategy_file=str(example_file),
            strategy_name="ExampleStrategy",
            description="Example strategy for demonstration",
            test_symbol="AAPL",
            test_period_days=365
        )
        
        logger.info("\n2. Execution Results:")
        logger.info(f"   Status: {'SUCCESS ✓' if result.success else 'FAILED ✗'}")
        logger.info(f"   Duration: {result.duration_seconds:.2f}s")
        
        if result.success:
            if result.return_pct is not None:
                logger.info(f"   Return: {result.return_pct:.2f}%")
            if result.trades is not None:
                logger.info(f"   Trades: {result.trades}")
            if result.win_rate is not None:
                logger.info(f"   Win Rate: {result.win_rate:.1%}")
        else:
            logger.warning(f"   Error: {result.error}")
        
        return result
    
    except ImportError as e:
        logger.error(f"Import error: {e}")
        return None
    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)
        return None


def example_3_execution_history():
    """Example 3: View execution history for a strategy"""
    logger.info("\n" + "=" * 80)
    logger.info("EXAMPLE 3: Execution History")
    logger.info("=" * 80)
    
    try:
        from Backtest.bot_executor import get_bot_executor
        
        executor = get_bot_executor()
        
        logger.info("\n1. Retrieving execution history for 'ExampleMAStrategy'...")
        
        history = executor.get_strategy_history("ExampleMAStrategy")
        
        if not history:
            logger.info("   No execution history found for this strategy yet.")
            logger.info("   Run Example 1 first to generate some history.")
            return
        
        logger.info(f"\n2. Found {len(history)} execution(s):")
        
        for i, run in enumerate(history[:5], 1):  # Show last 5 runs
            logger.info(f"\n   Run {i}: {run.execution_timestamp.isoformat()}")
            logger.info(f"   Status: {'SUCCESS ✓' if run.success else 'FAILED ✗'}")
            logger.info(f"   Duration: {run.duration_seconds:.2f}s")
            
            if run.success:
                if run.return_pct is not None:
                    logger.info(f"   Return: {run.return_pct:.2f}%")
                if run.trades is not None:
                    logger.info(f"   Trades: {run.trades}")
            else:
                if run.error:
                    logger.info(f"   Error: {run.error}")
    
    except ImportError as e:
        logger.error(f"Import error: {e}")
    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)


def example_4_performance_summary():
    """Example 4: Get overall performance statistics"""
    logger.info("\n" + "=" * 80)
    logger.info("EXAMPLE 4: Performance Summary")
    logger.info("=" * 80)
    
    try:
        from Backtest.bot_executor import get_bot_executor
        
        executor = get_bot_executor()
        
        logger.info("\n1. Retrieving performance summary...")
        
        summary = executor.get_performance_summary()
        
        if not summary or summary.get('total_executions', 0) == 0:
            logger.info("   No execution data available yet.")
            logger.info("   Run Example 1 first to generate some data.")
            return
        
        logger.info("\n2. Overall Performance Statistics:")
        logger.info(f"   Total Executions: {summary['total_executions']}")
        logger.info(f"   Successful: {summary['successful']}")
        logger.info(f"   Success Rate: {summary['success_rate']:.1%}")
        
        if summary.get('avg_return_pct') is not None:
            logger.info(f"   Avg Return: {summary['avg_return_pct']:.2f}%")
        if summary.get('avg_trades') is not None:
            logger.info(f"   Avg Trades: {summary['avg_trades']:.1f}")
        if summary.get('avg_win_rate') is not None:
            logger.info(f"   Avg Win Rate: {summary['avg_win_rate']:.1%}")
        if summary.get('avg_max_drawdown') is not None:
            logger.info(f"   Avg Max Drawdown: {summary['avg_max_drawdown']:.2f}%")
        if summary.get('avg_sharpe_ratio') is not None:
            logger.info(f"   Avg Sharpe Ratio: {summary['avg_sharpe_ratio']:.2f}")
        if summary.get('avg_duration_seconds') is not None:
            logger.info(f"   Avg Duration: {summary['avg_duration_seconds']:.2f}s")
    
    except ImportError as e:
        logger.error(f"Import error: {e}")
    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)


def example_5_results_inspection():
    """Example 5: Inspect saved results files"""
    logger.info("\n" + "=" * 80)
    logger.info("EXAMPLE 5: Inspecting Results Files")
    logger.info("=" * 80)
    
    try:
        import json
        
        results_dir = Path("Backtest/codes/results")
        
        if not results_dir.exists():
            logger.info("   Results directory not found.")
            logger.info("   Run Example 1 first to generate results.")
            return
        
        # Check JSON results
        json_dir = results_dir / "json"
        if json_dir.exists():
            json_files = list(json_dir.glob("*.json"))
            
            if json_files:
                logger.info(f"\n1. Found {len(json_files)} JSON result file(s)")
                
                # Show most recent
                latest_json = sorted(json_files)[-1]
                logger.info(f"\n2. Most recent result file: {latest_json.name}")
                
                with open(latest_json, 'r') as f:
                    data = json.load(f)
                
                logger.info(f"   Strategy: {data.get('strategy_name')}")
                logger.info(f"   Status: {'SUCCESS ✓' if data.get('success') else 'FAILED ✗'}")
                logger.info(f"   Timestamp: {data.get('execution_timestamp')}")
                
                if data.get('success'):
                    if data.get('return_pct') is not None:
                        logger.info(f"   Return: {data['return_pct']:.2f}%")
                    if data.get('trades') is not None:
                        logger.info(f"   Trades: {data['trades']}")
                else:
                    logger.info(f"   Error: {data.get('error')}")
        
        # Check log files
        log_dir = results_dir / "logs"
        if log_dir.exists():
            log_files = list(log_dir.glob("*.log"))
            if log_files:
                logger.info(f"\n3. Found {len(log_files)} log file(s)")
                latest_log = sorted(log_files)[-1]
                logger.info(f"   Most recent: {latest_log.name}")
                logger.info(f"   Size: {latest_log.stat().st_size} bytes")
        
        # Check metrics files
        metrics_dir = results_dir / "metrics"
        if metrics_dir.exists():
            metrics_files = list(metrics_dir.glob("*.txt"))
            if metrics_files:
                logger.info(f"\n4. Found {len(metrics_files)} metrics file(s)")
    
    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)


def main():
    """Run all examples"""
    logger.info("\n" + "🤖 BOT EXECUTION INTEGRATION EXAMPLES ".center(80, "="))
    logger.info("")
    
    try:
        # Example 1: Generate and execute (requires API key)
        try:
            output_file, result = example_1_generate_and_execute()
        except Exception as e:
            logger.warning(f"Example 1 skipped: {e}")
        
        # Example 2: Manual execution
        example_2_manual_execution()
        
        # Example 3: View history
        example_3_execution_history()
        
        # Example 4: Performance summary
        example_4_performance_summary()
        
        # Example 5: Inspect results
        example_5_results_inspection()
        
    except KeyboardInterrupt:
        logger.info("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
    
    logger.info("\n" + "=" * 80)
    logger.info("Examples Complete!")
    logger.info("=" * 80)
    logger.info("\nNext Steps:")
    logger.info("1. Check results in: Backtest/codes/results/")
    logger.info("2. Read: BOT_EXECUTION_INTEGRATION_GUIDE.md")
    logger.info("3. Try generating your own strategies with --execute flag")
    logger.info("")


if __name__ == "__main__":
    main()
