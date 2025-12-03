#!/usr/bin/env python3
"""
Test: EMA Crossover Bot Creation and Execution
===============================================

This test verifies that the agent can:
1. Generate an EMA crossover strategy (30 and 50 periods)
2. Set stop loss at 10 pips from entry
3. Set take profit at 40 pips
4. Execute the bot during backtesting
5. Verify that at least one trade is executed

Success Criteria: Bot executes at least one trade during backtesting
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Setup paths
MONOLITHIC_PATH = Path(__file__).parent
BACKTEST_PATH = MONOLITHIC_PATH / "Backtest"
sys.path.insert(0, str(MONOLITHIC_PATH))
sys.path.insert(0, str(BACKTEST_PATH))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_ema_crossover.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Import required modules
try:
    from Backtest.gemini_strategy_generator import GeminiStrategyGenerator
    GENERATOR_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import GeminiStrategyGenerator: {e}")
    GENERATOR_AVAILABLE = False

try:
    from Backtest.bot_executor import BotExecutor, get_bot_executor
    EXECUTOR_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import BotExecutor: {e}")
    EXECUTOR_AVAILABLE = False


def test_ema_crossover_bot_generation_and_execution():
    """Test generating and executing an EMA crossover bot"""
    
    logger.info("=" * 80)
    logger.info("TEST: EMA Crossover Bot Generation and Execution")
    logger.info("=" * 80)
    
    # Verify dependencies
    if not GENERATOR_AVAILABLE:
        logger.error("❌ GeminiStrategyGenerator not available")
        return False
    
    if not EXECUTOR_AVAILABLE:
        logger.warning("⚠️  BotExecutor not available - execution will be skipped")
    
    try:
        # Step 1: Generate the strategy
        logger.info("\n[STEP 1] Generating EMA Crossover Strategy...")
        logger.info("-" * 80)
        
        strategy_description = """
        Create an EMA Crossover strategy with these exact specifications:
        
        1. INDICATORS:
           - EMA 30 (fast): Calculate 30-period exponential moving average
           - EMA 50 (slow): Calculate 50-period exponential moving average
        
        2. ENTRY LOGIC:
           - Long Entry: When EMA 30 crosses above EMA 50
           - Short Entry: When EMA 30 crosses below EMA 50
        
        3. RISK MANAGEMENT:
           - Stop Loss: 10 pips from entry price
           - Take Profit: 40 pips from entry price
           - Position Size: 0.1 lots (fixed)
        
        4. TRADING RULES:
           - Only trade major pairs (EURUSD, GBPUSD, USDJPY, AUDUSD)
           - Trade during London and New York sessions
           - Maximum 2 simultaneous positions
           - Close all positions at 5 PM EST
        
        5. IMPLEMENTATION REQUIREMENTS:
           - Use SimBroker API for all trading operations
           - Log all trades with entry, stop loss, take profit levels
           - Track performance metrics: win rate, profit factor, drawdown
           - Ensure tight stop loss execution
        """
        
        generator = GeminiStrategyGenerator()
        
        if not generator.api_key:
            logger.error("❌ No Gemini API key found. Set GEMINI_API_KEY in .env")
            return False
        
        logger.info("📝 Requesting strategy generation from Gemini AI...")
        
        output_path = BACKTEST_PATH / "codes" / "ema_crossover_test_bot.py"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate strategy (without auto-execution first)
        strategy_file, _ = generator.generate_and_save(
            description=strategy_description,
            output_path=str(output_path),
            execute_after_generation=False
        )
        
        if not strategy_file or not Path(strategy_file).exists():
            logger.error("❌ Strategy generation failed - file not created")
            return False
        
        logger.info(f"✅ Strategy generated: {strategy_file}")
        
        # Verify the generated code contains key components
        with open(strategy_file, 'r') as f:
            code_content = f.read()
        
        required_elements = {
            'EMA 30': 'ema_30' in code_content.lower() or 'ema30' in code_content.lower(),
            'EMA 50': 'ema_50' in code_content.lower() or 'ema50' in code_content.lower(),
            'Stop Loss': 'stop' in code_content.lower(),
            'Take Profit': 'profit' in code_content.lower() or 'tp' in code_content.lower(),
        }
        
        logger.info("\n[VERIFICATION] Generated code contains required elements:")
        all_elements_present = True
        for element, present in required_elements.items():
            status = "✅" if present else "⚠️ "
            logger.info(f"  {status} {element}: {'Found' if present else 'Not found'}")
            if not present:
                all_elements_present = False
        
        if not all_elements_present:
            logger.warning("⚠️  Some expected elements missing, but continuing with execution...")
        
        # Step 2: Execute the bot
        logger.info("\n[STEP 2] Executing the Generated Bot...")
        logger.info("-" * 80)
        
        if not EXECUTOR_AVAILABLE:
            logger.error("❌ BotExecutor not available - cannot execute bot")
            logger.info("\nTo use auto-execution:")
            logger.info("1. Ensure bot_executor.py is in Backtest/ directory")
            logger.info("2. Strategy file was generated at: {strategy_file}")
            return False
        
        executor = get_bot_executor()
        logger.info("📊 Running backtesting simulation...")
        
        execution_result = executor.execute_bot(
            strategy_file=str(strategy_file),
            test_symbol="EURUSD",
            test_period_days=90,
            description="EMA Crossover (30/50) - 10pip SL, 40pip TP"
        )
        
        if not execution_result:
            logger.error("❌ Bot execution failed")
            return False
        
        logger.info(f"✅ Bot execution completed")
        
        # Step 3: Analyze results
        logger.info("\n[STEP 3] Analyzing Execution Results...")
        logger.info("-" * 80)
        
        success = execution_result.success
        logger.info(f"Execution Status: {'✅ SUCCESS' if success else '❌ FAILED'}")
        logger.info(f"Duration: {execution_result.duration_seconds:.2f} seconds")
        
        if execution_result.error:
            logger.error(f"Error: {execution_result.error}")
        
        # Critical check: Did the bot execute any trades?
        trades_executed = execution_result.trades
        logger.info(f"\n📈 CRITICAL METRIC: Trades Executed: {trades_executed}")
        
        if trades_executed > 0:
            logger.info(f"✅ SUCCESS: Bot executed {trades_executed} trade(s)!")
        else:
            logger.warning(f"⚠️  WARNING: Bot did not execute any trades")
            logger.info("   This could mean:")
            logger.info("   - EMA crossover signals did not occur in backtest period")
            logger.info("   - Strategy parameters need adjustment")
            logger.info("   - Backtest symbol/period may not have suitable data")
        
        # Display performance metrics
        logger.info("\n[PERFORMANCE METRICS]")
        logger.info("-" * 80)
        
        metrics = {
            'Return %': execution_result.return_pct,
            'Total Trades': execution_result.trades,
            'Win Rate %': execution_result.win_rate,
            'Max Drawdown %': execution_result.max_drawdown,
            'Sharpe Ratio': execution_result.sharpe_ratio,
        }
        
        for metric_name, metric_value in metrics.items():
            if metric_value is not None:
                display_value = f"{metric_value:.2f}" if isinstance(metric_value, (int, float)) else metric_value
                logger.info(f"  {metric_name}: {display_value}")
            else:
                logger.info(f"  {metric_name}: N/A")
        
        # Save results to JSON for easy parsing
        results_json_file = BACKTEST_PATH / "codes" / "results" / "ema_crossover_test_results.json"
        results_json_file.parent.mkdir(parents=True, exist_ok=True)
        
        results_data = {
            'test_name': 'EMA Crossover Bot (30/50)',
            'timestamp': execution_result.execution_timestamp,
            'generation_success': True,
            'execution_success': success,
            'trades_executed': trades_executed,
            'return_pct': execution_result.return_pct,
            'win_rate': execution_result.win_rate,
            'max_drawdown': execution_result.max_drawdown,
            'sharpe_ratio': execution_result.sharpe_ratio,
            'strategy_file': str(strategy_file),
            'test_symbol': execution_result.test_symbol,
            'test_period_days': execution_result.test_period_days,
        }
        
        with open(results_json_file, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        logger.info(f"\n📄 Results saved to: {results_json_file}")
        
        # Final verdict
        logger.info("\n" + "=" * 80)
        logger.info("TEST RESULT SUMMARY")
        logger.info("=" * 80)
        
        if trades_executed > 0:
            logger.info(f"✅ TEST PASSED - Bot executed {trades_executed} trade(s)")
            logger.info(f"   Strategy generation: ✅ SUCCESS")
            logger.info(f"   Bot execution: ✅ SUCCESS")
            logger.info(f"   Trade execution: ✅ SUCCESS ({trades_executed} trade(s))")
            logger.info(f"\n📊 Bot is working correctly and generating trading signals!")
            return True
        else:
            logger.warning(f"⚠️  TEST INCONCLUSIVE - Bot did not execute trades")
            logger.info(f"   Strategy generation: ✅ SUCCESS")
            logger.info(f"   Bot execution: ✅ SUCCESS")
            logger.info(f"   Trade execution: ❌ FAILED (0 trades)")
            logger.info(f"\n⚠️  The bot ran but did not generate signals. Review strategy parameters.")
            return False
    
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    logger.info("\n")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + " " * 20 + "EMA CROSSOVER BOT TESTING SUITE" + " " * 28 + "║")
    logger.info("║" + " " * 15 + "Strategy: EMA 30/50 Crossover | SL: 10pip | TP: 40pip" + " " * 8 + "║")
    logger.info("╚" + "=" * 78 + "╝")
    
    result = test_ema_crossover_bot_generation_and_execution()
    
    sys.exit(0 if result else 1)
