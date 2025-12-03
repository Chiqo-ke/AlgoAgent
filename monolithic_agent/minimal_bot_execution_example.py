#!/usr/bin/env python
"""
Minimal Example: Bot Generation + Execution + Results
======================================================

This is the simplest way to use the new bot execution system.

The workflow:
1. Generate a bot with a natural language description
2. Automatically execute it after generation
3. See results immediately
4. Results stored for future reference

Usage:
    python minimal_bot_execution_example.py

Expected Output:
    - Bot generation progress
    - Bot execution progress
    - Performance metrics
    - Results file path
"""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Run minimal example"""
    
    # Title
    print("\n" + "="*70)
    print("BOT GENERATION + EXECUTION WORKFLOW".center(70))
    print("="*70)
    
    try:
        # Step 1: Import required modules
        print("\n[1/4] Importing modules...")
        try:
            from Backtest.gemini_strategy_generator import GeminiStrategyGenerator
            from Backtest.bot_executor import BOT_EXECUTOR_AVAILABLE
            print("      ✓ Imports successful")
        except ImportError as e:
            print(f"      ✗ Import failed: {e}")
            print("\n      Fix: pip install google-generativeai python-dotenv")
            return False
        
        # Step 2: Verify API key
        print("\n[2/4] Checking API configuration...")
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key or api_key.startswith('AIza'):  # Placeholder check
            print("      ⚠️  No valid API key found")
            print("      Note: Generation will fail, but execution framework is ready")
        else:
            print("      ✓ API key configured")
        
        # Step 3: Generate and execute bot
        print("\n[3/4] Generating strategy with auto-execution...")
        print("      Creating generator...")
        
        generator = GeminiStrategyGenerator()
        
        # Define strategy
        strategy_description = "Simple RSI oscillator strategy: buy when RSI drops below 30, sell when it rises above 70"
        
        print(f"      Generating: {strategy_description[:60]}...")
        
        # Generate with auto-execution
        output_file, execution_result = generator.generate_and_save(
            description=strategy_description,
            output_path="Backtest/codes/minimal_example_bot.py",
            strategy_name="MinimalExampleBot",
            execute_after_generation=BOT_EXECUTOR_AVAILABLE,  # Auto-execute if available
            test_symbol="AAPL",
            test_period_days=365
        )
        
        print(f"      ✓ Strategy generated: {output_file.name}")
        
        # Step 4: Display results
        print("\n[4/4] Results")
        print("-" * 70)
        
        print(f"\nGenerated File:")
        print(f"  Location: {output_file}")
        print(f"  Size: {output_file.stat().st_size:,} bytes")
        
        if execution_result:
            print(f"\nExecution Results:")
            print(f"  Status: {'SUCCESS ✓' if execution_result.success else 'FAILED ✗'}")
            print(f"  Duration: {execution_result.duration_seconds:.2f} seconds")
            
            if execution_result.success:
                # Display available metrics
                metrics = []
                if execution_result.return_pct is not None:
                    metrics.append(f"Return: {execution_result.return_pct:.2f}%")
                if execution_result.trades is not None:
                    metrics.append(f"Trades: {execution_result.trades}")
                if execution_result.win_rate is not None:
                    metrics.append(f"Win Rate: {execution_result.win_rate:.1%}")
                if execution_result.max_drawdown is not None:
                    metrics.append(f"Max Drawdown: {execution_result.max_drawdown:.2f}%")
                if execution_result.sharpe_ratio is not None:
                    metrics.append(f"Sharpe: {execution_result.sharpe_ratio:.2f}")
                
                if metrics:
                    print("\n  Metrics:")
                    for metric in metrics:
                        print(f"    • {metric}")
                else:
                    print("\n  ℹ️  No metrics parsed from output")
                    print("     (Check logs for details)")
            else:
                print(f"\n  Error: {execution_result.error}")
            
            if execution_result.results_file:
                print(f"\n  Results File: {execution_result.results_file}")
                print(f"  Results Dir: Backtest/codes/results/")
        else:
            print("\nExecution Results:")
            print("  Status: SKIPPED (BotExecutor not available)")
            print("  Note: You can execute the bot manually later:")
            print(f"    python {output_file}")
        
        # Summary
        print("\n" + "="*70)
        print("WORKFLOW COMPLETE ✓".center(70))
        print("="*70)
        
        print("\nNext Steps:")
        print("1. Review results in: Backtest/codes/results/")
        print("2. Query execution history:")
        print("   from Backtest.bot_executor import get_bot_executor")
        print("   executor = get_bot_executor()")
        print("   history = executor.get_strategy_history('MinimalExampleBot')")
        print("\n3. Generate more bots and watch their performance!")
        
        return True
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
