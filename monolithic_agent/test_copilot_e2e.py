"""
End-to-End Test: Copilot Strategy Generation & Execution

Tests the complete flow:
1. Generate strategy using Copilot
2. Execute the strategy
3. Verify it runs with at least one trade
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoagent.settings')
import django
django.setup()

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

def run_e2e_test():
    """Run complete end-to-end test"""
    
    print("="*80)
    print("  END-TO-END TEST: Copilot Strategy Generation")
    print("="*80)
    print()
    
    # Step 1: Verify authentication
    print("Step 1: Verifying Copilot authentication...")
    from strategy_api.models import CopilotAuth
    from algoagent_api.copilot_auth import get_auth_manager
    
    token_data = CopilotAuth.get_latest_token()
    if not token_data:
        print("❌ No Copilot token found. Run: python manage.py copilot_auth")
        return False
    
    auth_manager = get_auth_manager()
    if not auth_manager.is_token_valid(token_data):
        print("❌ Copilot token expired. Run: python manage.py copilot_auth")
        return False
    
    print(f"✅ Valid token found (expires: {token_data['expires_at']})")
    print()
    
    # Step 2: Import Copilot generator
    print("Step 2: Importing Copilot strategy generator...")
    try:
        from Backtest.copilot_strategy_generator import CopilotStrategyGenerator
        print("✅ CopilotStrategyGenerator imported successfully")
    except Exception as e:
        print(f"❌ Failed to import generator: {e}")
        return False
    print()
    
    # Step 3: Generate strategy
    print("Step 3: Generating trading strategy with Copilot...")
    print("Strategy description: Create a simple moving average crossover strategy")
    print()
    
    try:
        generator = CopilotStrategyGenerator()
        
        strategy_description = """
        Create a simple moving average crossover strategy:
        - Use 20-day and 50-day simple moving averages
        - Buy when 20-day SMA crosses above 50-day SMA
        - Sell when 20-day SMA crosses below 50-day SMA
        - Trade AAPL stock with 1 year of daily data
        - Start with $10,000 initial capital
        - Use 10 shares per trade
        """
        
        print("Calling Copilot API...")
        file_path, execution_result = generator.generate_and_save(
            description=strategy_description,
            execute_after_generation=True
        )
        
        print(f"✅ Strategy generated and saved to: {file_path}")
        print()
        
    except Exception as e:
        print(f"❌ Strategy generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: Verify execution results
    print("Step 4: Verifying strategy execution...")
    
    if execution_result is None:
        print("⚠️  Strategy was not executed automatically")
        print("Executing strategy manually...")
        
        try:
            from Backtest.bot_executor import BotExecutor
            executor = BotExecutor()
            execution_result = executor.execute_bot(strategy_file=file_path)
        except Exception as e:
            print(f"❌ Manual execution failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # Check execution success
    if not execution_result.success:
        print(f"❌ Strategy execution failed")
        print(f"Error: {execution_result.error_message}")
        print()
        print("Generated code:")
        with open(file_path, 'r') as f:
            print(f.read())
        return False
    
    print("✅ Strategy executed successfully")
    print()
    
    # Step 5: Verify trade requirements
    print("Step 5: Verifying trade requirements...")
    
    num_trades = execution_result.num_trades
    print(f"Number of trades: {num_trades}")
    
    if num_trades < 1:
        print("❌ FAILED: Strategy must execute at least 1 trade")
        print()
        print("Execution details:")
        print(f"  Return: {execution_result.return_pct}%")
        print(f"  Sharpe Ratio: {execution_result.sharpe_ratio}")
        print(f"  Max Drawdown: {execution_result.max_drawdown}%")
        return False
    
    print(f"✅ PASSED: Strategy executed {num_trades} trade(s)")
    print()
    
    # Step 6: Display performance metrics
    print("Step 6: Performance metrics...")
    print("-" * 80)
    print(f"  Total Trades:    {execution_result.num_trades}")
    print(f"  Winning Trades:  {execution_result.winning_trades}")
    print(f"  Losing Trades:   {execution_result.losing_trades}")
    print(f"  Win Rate:        {execution_result.win_rate}%")
    print(f"  Total Return:    {execution_result.return_pct}%")
    print(f"  Sharpe Ratio:    {execution_result.sharpe_ratio}")
    print(f"  Max Drawdown:    {execution_result.max_drawdown}%")
    print("-" * 80)
    print()
    
    # Success!
    print("="*80)
    print("  ✅ END-TO-END TEST PASSED!")
    print("="*80)
    print()
    print("Summary:")
    print(f"  ✓ Authentication verified")
    print(f"  ✓ Copilot generator imported")
    print(f"  ✓ Strategy generated via Copilot API")
    print(f"  ✓ Strategy executed successfully")
    print(f"  ✓ At least {num_trades} trade(s) executed")
    print(f"  ✓ Strategy file: {file_path}")
    print()
    
    return True


if __name__ == '__main__':
    success = run_e2e_test()
    sys.exit(0 if success else 1)
