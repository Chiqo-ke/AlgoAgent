"""
Test Diagnostic System - Verify diagnostic logging and analysis works
======================================================================

This script tests the improved code fixing workflow that:
1. Injects diagnostic logging into a bot
2. Runs the instrumented bot
3. Analyzes logs to identify specific issues
4. Generates targeted fix prompts

Usage:
    python test_diagnostic_system.py
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def create_test_bot() -> Path:
    """Create a simple test bot with a known error"""
    test_code = '''
import pandas as pd
import yfinance as yf

def fetch_data(symbol="AAPL", period="1y"):
    """Fetch stock data"""
    data = yf.download(symbol, period=period)
    return data

def calculate_indicators(data):
    """Calculate technical indicators"""
    # This will cause an AttributeError - 'close' should be 'Close'
    data['SMA_20'] = data['close'].rolling(window=20).mean()
    data['SMA_50'] = data['close'].rolling(window=50).mean()
    return data

def generate_signals(data):
    """Generate trading signals"""
    data['signal'] = 0
    data.loc[data['SMA_20'] > data['SMA_50'], 'signal'] = 1
    data.loc[data['SMA_20'] < data['SMA_50'], 'signal'] = -1
    return data

def main():
    print("Starting backtest...")
    
    # Fetch data
    data = fetch_data("AAPL", "6mo")
    print(f"Data fetched: {len(data)} rows")
    
    # Calculate indicators
    data = calculate_indicators(data)
    print("Indicators calculated")
    
    # Generate signals
    data = generate_signals(data)
    print("Signals generated")
    
    # Print results
    print(f"Total signals: {data['signal'].sum()}")
    print("Backtest complete!")

if __name__ == "__main__":
    main()
'''
    
    test_bot_path = Path("AlgoAgent/monolithic_agent/Backtest/test_diagnostic_bot.py")
    test_bot_path.write_text(test_code, encoding='utf-8')
    logger.info(f"Created test bot: {test_bot_path}")
    return test_bot_path


def test_diagnostic_logging():
    """Test diagnostic logging injection"""
    logger.info("\n" + "="*70)
    logger.info("TEST 1: Diagnostic Logging Injection")
    logger.info("="*70)
    
    test_bot = create_test_bot()
    
    try:
        from AlgoAgent.monolithic_agent.Backtest.diagnostic_logger import create_diagnostic_version
        
        success, diagnostic_path, summary = create_diagnostic_version(test_bot)
        
        if success:
            logger.info(f"✓ Diagnostic version created: {diagnostic_path}")
            logger.info(f"  Injection points: {summary.get('total_points', 0)}")
            logger.info(f"  By context: {summary.get('by_context', {})}")
            
            # Read and display a sample of the instrumented code
            diagnostic_file = Path(diagnostic_path)
            instrumented_code = diagnostic_file.read_text(encoding='utf-8')
            logger.info("\nSample of instrumented code (first 30 lines):")
            logger.info("-" * 70)
            for i, line in enumerate(instrumented_code.split('\n')[:30], 1):
                print(f"{i:3}: {line}")
            
            return diagnostic_file
        else:
            logger.error("✗ Failed to create diagnostic version")
            return None
            
    except Exception as e:
        logger.error(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_diagnostic_execution(diagnostic_bot: Path):
    """Test executing bot with diagnostic logging"""
    logger.info("\n" + "="*70)
    logger.info("TEST 2: Diagnostic Execution")
    logger.info("="*70)
    
    try:
        from AlgoAgent.monolithic_agent.Backtest.bot_executor import get_bot_executor
        
        executor = get_bot_executor(timeout_seconds=60)
        result, diagnostic_report = executor.execute_with_diagnostics(
            strategy_file=str(diagnostic_bot.parent / "test_diagnostic_bot.py"),
            cleanup=False  # Keep files for inspection
        )
        
        logger.info(f"\nExecution Result:")
        logger.info(f"  Success: {result.success}")
        logger.info(f"  Duration: {result.duration_seconds:.2f}s")
        if result.error:
            logger.info(f"  Error: {result.error[:200]}")
        
        if diagnostic_report:
            logger.info(f"\nDiagnostic Report:")
            logger.info(f"  Issues found: {len(diagnostic_report.get('issues', []))}")
            logger.info(f"  Execution completed: {diagnostic_report.get('execution_completed')}")
            logger.info(f"  Functions executed: {len(diagnostic_report.get('functions_executed', []))}")
            
            # Show issues
            for i, issue in enumerate(diagnostic_report.get('issues', [])[:5], 1):
                logger.info(f"\n  Issue {i}:")
                logger.info(f"    Type: {issue.get('type')}")
                logger.info(f"    Severity: {issue.get('severity')}")
                logger.info(f"    Description: {issue.get('description')}")
                if issue.get('suggested_fix'):
                    logger.info(f"    Fix: {issue.get('suggested_fix')}")
            
            # Show recommendations
            if diagnostic_report.get('recommendations'):
                logger.info("\n  Recommendations:")
                for rec in diagnostic_report['recommendations']:
                    logger.info(f"    - {rec}")
        else:
            logger.warning("✗ No diagnostic report generated")
        
        return diagnostic_report
        
    except Exception as e:
        logger.error(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_log_analysis():
    """Test log analysis independently"""
    logger.info("\n" + "="*70)
    logger.info("TEST 3: Log Analysis")
    logger.info("="*70)
    
    # Create a sample log content
    sample_log = """
2026-02-01 10:00:00 [INFO] ====================================
2026-02-01 10:00:00 [INFO] DIAGNOSTIC MODE ENABLED
2026-02-01 10:00:00 [INFO] ====================================
2026-02-01 10:00:01 [INFO] [DIAG] Entering function: fetch_data
2026-02-01 10:00:02 [INFO] [DIAG] Calling method: download
2026-02-01 10:00:03 [INFO] [DIAG] Exiting function: fetch_data
2026-02-01 10:00:03 [INFO] [DIAG] Entering function: calculate_indicators
2026-02-01 10:00:04 [ERROR] AttributeError: 'DataFrame' object has no attribute 'close'
2026-02-01 10:00:04 [ERROR] Traceback (most recent call last):
2026-02-01 10:00:04 [ERROR]   File "test_bot.py", line 12, in calculate_indicators
2026-02-01 10:00:04 [ERROR]     data['SMA_20'] = data['close'].rolling(window=20).mean()
"""
    
    try:
        from AlgoAgent.monolithic_agent.Backtest.log_analyzer import LogAnalyzer
        
        analyzer = LogAnalyzer(verbose=True)
        report = analyzer.analyze_log_content(sample_log)
        
        logger.info(f"\nAnalysis Results:")
        logger.info(f"  Success: {report.success}")
        logger.info(f"  Execution completed: {report.execution_completed}")
        logger.info(f"  Issues found: {len(report.issues)}")
        logger.info(f"  Functions executed: {report.functions_executed}")
        
        for i, issue in enumerate(report.issues, 1):
            logger.info(f"\n  Issue {i}:")
            logger.info(f"    Type: {issue.issue_type.value}")
            logger.info(f"    Severity: {issue.severity.value}")
            logger.info(f"    Description: {issue.description}")
            if issue.suggested_fix:
                logger.info(f"    Suggested fix: {issue.suggested_fix}")
        
        if report.recommendations:
            logger.info("\n  Recommendations:")
            for rec in report.recommendations:
                logger.info(f"    - {rec}")
        
        # Test fix prompt generation
        bot_code = "# Sample bot code..."
        fix_prompt = analyzer.generate_fix_prompt(report, bot_code)
        logger.info(f"\n  Generated fix prompt length: {len(fix_prompt)} characters")
        logger.info("\n  Fix prompt sample (first 500 chars):")
        logger.info("-" * 70)
        print(fix_prompt[:500])
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all diagnostic system tests"""
    logger.info("\n" + "="*70)
    logger.info("DIAGNOSTIC SYSTEM TEST SUITE")
    logger.info("="*70)
    
    # Test 1: Diagnostic logging injection
    diagnostic_bot = test_diagnostic_logging()
    
    # Test 2: Log analysis (independent)
    test_log_analysis()
    
    # Test 3: Full diagnostic execution
    if diagnostic_bot:
        test_diagnostic_execution(diagnostic_bot)
    
    logger.info("\n" + "="*70)
    logger.info("ALL TESTS COMPLETE")
    logger.info("="*70)
    
    logger.info("\nNext steps:")
    logger.info("1. Review the diagnostic logs created in AlgoAgent/monolithic_agent/Backtest/")
    logger.info("2. Check that issues were correctly identified")
    logger.info("3. Try the improved fix workflow on a real strategy")


if __name__ == "__main__":
    main()
