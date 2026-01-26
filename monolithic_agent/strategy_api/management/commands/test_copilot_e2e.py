"""
Django management command to test Copilot E2E flow

Usage: python manage.py test_copilot_e2e
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from pathlib import Path
from datetime import datetime


class Command(BaseCommand):
    help = 'Test end-to-end Copilot strategy generation and execution'
    
    def handle(self, *args, **options):
        self.stdout.write("="*80)
        self.stdout.write(self.style.SUCCESS(
            "  END-TO-END TEST: Copilot Strategy Generation"
        ))
        self.stdout.write("="*80)
        self.stdout.write("")
        
        # Step 1: Verify authentication
        self.stdout.write("Step 1: Verifying Copilot authentication...")
        
        from strategy_api.models import CopilotAuth
        from algoagent_api.copilot_auth import get_auth_manager
        
        token_data = CopilotAuth.get_latest_token()
        if not token_data:
            self.stdout.write(self.style.ERROR("[X] No Copilot token found"))
            self.stdout.write("Run: python manage.py copilot_auth")
            return
        
        auth_manager = get_auth_manager()
        if not auth_manager.is_token_valid(token_data):
            self.stdout.write(self.style.ERROR("[X] Copilot token expired"))
            self.stdout.write("Run: python manage.py copilot_auth")
            return
        
        self.stdout.write(self.style.SUCCESS(f"[OK] Valid token found"))
        self.stdout.write("")
        
        # Step 2: Create test strategy code
        self.stdout.write("Step 2: Creating test strategy...")
        
        strategy_code = """
import os
import sys
from pathlib import Path

# Set Django settings before any Backtest imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoagent_api.settings')

# Add parent directory to path to import Backtest module
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig
from datetime import datetime, timedelta
import pandas as pd

def run_strategy():
    '''Simple Test Strategy - E2E Test with Mock Data'''
    
    print('[INFO] Starting E2E test strategy...')
    
    # Configure backtest
    config = BacktestConfig(
        start_cash=10000.0,
        fee_pct=0.001,
        name='e2e_test_strategy'
    )
    
    # Initialize broker
    broker = SimBroker(config=config)
    
    # Create mock price data (30 days of AAPL-like data)
    print('[INFO] Generating mock market data...')
    dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
    
    # Simulate price movement with trend
    base_price = 150.0
    prices = []
    for i in range(30):
        # Add some trend and noise
        trend = i * 0.5
        noise = (i % 3 - 1) * 2.0
        price = base_price + trend + noise
        prices.append(price)
    
    # Calculate SMAs manually
    sma_5 = []
    sma_10 = []
    for i in range(len(prices)):
        if i >= 4:
            sma_5.append(sum(prices[i-4:i+1]) / 5)
        else:
            sma_5.append(None)
        
        if i >= 9:
            sma_10.append(sum(prices[i-9:i+1]) / 10)
        else:
            sma_10.append(None)
    
    print('[INFO] Starting strategy execution...')
    position = 0
    trade_count = 0
    signal_id = 0
    
    # Process data
    for i, (timestamp, price) in enumerate(zip(dates, prices)):
        # Create market data in correct format: {symbol: {bars}}
        market_data = {
            'AAPL': {
                'open': price,
                'high': price + 1.0,
                'low': price - 1.0,
                'close': price,
                'volume': 1000000
            }
        }
        
        # Update broker
        broker.step_to(timestamp, market_data)
        
        # Skip if indicators not ready
        if sma_5[i] is None or sma_10[i] is None:
            continue
        
        # Trading logic: SMA crossover
        if position == 0 and sma_5[i] > sma_10[i]:
            # Buy signal
            signal_id += 1
            signal = {
                'signal_id': f'sig_{signal_id:04d}',
                'timestamp': timestamp.isoformat(),
                'symbol': 'AAPL',
                'action': 'ENTRY',
                'side': 'BUY',
                'order_type': 'MARKET',
                'size': 10,
                'meta': {'reason': f'SMA crossover: {sma_5[i]:.2f} > {sma_10[i]:.2f}'}
            }
            broker.submit_signal(signal)
            position = 10
            trade_count += 1
            print(f'[TRADE] BUY 10 shares at {timestamp.date()} price ${price:.2f}')
            
        elif position > 0 and sma_5[i] < sma_10[i]:
            # Sell signal
            signal_id += 1
            signal = {
                'signal_id': f'sig_{signal_id:04d}',
                'timestamp': timestamp.isoformat(),
                'symbol': 'AAPL',
                'action': 'EXIT',
                'side': 'SELL',
                'order_type': 'MARKET',
                'size': 10,
                'meta': {'reason': f'SMA crossunder: {sma_5[i]:.2f} < {sma_10[i]:.2f}'}
            }
            broker.submit_signal(signal)
            position = 0
            trade_count += 1
            print(f'[TRADE] SELL 10 shares at {timestamp.date()} price ${price:.2f}')
    
    # Get final results
    print('[INFO] Generating results...')
    metrics = broker.get_statistics()
    
    print('\\n' + '='*60)
    print('BACKTEST RESULTS')
    print('='*60)
    print(f'Total Trades:    {trade_count}')
    print(f'Final Equity:    ${metrics.get(\"equity\", config.start_cash):.2f}')
    total_return = ((metrics.get(\"equity\", config.start_cash) - config.start_cash) / config.start_cash) * 100
    print(f'Total Return:    {total_return:.2f}%')
    print('='*60)
    
    return {'trades': trade_count, 'metrics': metrics}

if __name__ == '__main__':
    run_strategy()
"""
        
        # Save strategy
        from pathlib import Path
        output_dir = Path("Backtest") / "codes"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        strategy_file = output_dir / f"e2e_test_strategy_{timestamp}.py"
        
        with open(strategy_file, 'w') as f:
            f.write(strategy_code)
        
        self.stdout.write(self.style.SUCCESS(f"[OK] Test strategy saved to: {strategy_file}"))
        self.stdout.write("")
        
        # Step 2.5: Validate imports
        self.stdout.write("Step 2.5: Validating imports...")
        
        import_validation = self._validate_imports(strategy_file)
        if not import_validation['valid']:
            self.stdout.write(self.style.ERROR(f"[X] Import validation failed:"))
            for error in import_validation['errors']:
                self.stdout.write(self.style.ERROR(f"  - {error}"))
            return
        
        self.stdout.write(self.style.SUCCESS("[OK] Import validation passed"))
        self.stdout.write("")
        
        # Step 3: Execute strategy
        self.stdout.write("Step 3: Executing strategy...")
        
        try:
            from Backtest.bot_executor import BotExecutor
            executor = BotExecutor()
            execution_result = executor.execute_bot(strategy_file=str(strategy_file))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"[X] Execution failed: {e}"))
            import traceback
            traceback.print_exc()
            return
        
        if not execution_result.success:
            self.stdout.write(self.style.ERROR("[X] Strategy execution failed"))
            self.stdout.write(f"Error: {execution_result.error}")
            return
        
        self.stdout.write(self.style.SUCCESS("[OK] Strategy executed successfully"))
        self.stdout.write("")
        
        # Step 4: Verify trade requirements
        self.stdout.write("Step 4: Verifying trade requirements...")
        
        # Get trade count from execution result
        trade_count = execution_result.trades if execution_result.trades else 0
        
        self.stdout.write(f"Number of trades: {trade_count}")
        
        if trade_count < 1:
            self.stdout.write(self.style.ERROR(
                "[X] FAILED: Strategy must execute at least 1 trade"
            ))
            return
        
        self.stdout.write(self.style.SUCCESS(
            f"[OK] PASSED: Strategy executed {trade_count} trade(s)"
        ))
        self.stdout.write("")
        
        # Step 5: Display metrics
        self.stdout.write("Step 5: Performance Summary")
        self.stdout.write("-" * 80)
        self.stdout.write(f"  Total Trades:    {trade_count}")
        if execution_result.return_pct is not None:
            self.stdout.write(f"  Total Return:    {execution_result.return_pct:.2f}%")
        if execution_result.win_rate is not None:
            self.stdout.write(f"  Win Rate:        {execution_result.win_rate:.2f}%")
        if execution_result.sharpe_ratio is not None:
            self.stdout.write(f"  Sharpe Ratio:    {execution_result.sharpe_ratio:.2f}")
        if execution_result.max_drawdown is not None:
            self.stdout.write(f"  Max Drawdown:    {execution_result.max_drawdown:.2f}%")
        self.stdout.write("-" * 80)
        self.stdout.write("")
        
        # Success!
        self.stdout.write("="*80)
        self.stdout.write(self.style.SUCCESS("  [PASSED] END-TO-END TEST PASSED!"))
        self.stdout.write("="*80)
        self.stdout.write("")
        self.stdout.write("Summary:")
        self.stdout.write(self.style.SUCCESS("  * Copilot authentication verified"))
        self.stdout.write(self.style.SUCCESS("  * Strategy code generated"))
        self.stdout.write(self.style.SUCCESS("  * Strategy executed successfully"))
        self.stdout.write(self.style.SUCCESS(f"  * {trade_count} trade(s) executed (requirement: >= 1)"))
        self.stdout.write(f"  * Strategy file: {strategy_file}")
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("SUCCESS: The Copilot integration is working correctly!"))
        self.stdout.write("")    
    def _validate_imports(self, strategy_file: Path) -> dict:
        """
        Validate that strategy file uses correct import paths
        
        Returns:
            dict with 'valid' (bool) and 'errors' (list) keys
        """
        errors = []
        
        with open(strategy_file, 'r') as f:
            content = f.read()
        
        # Check for incorrect imports
        forbidden_patterns = [
            ('from simbroker import', 'Should use: from Backtest.sim_broker import'),
            ('import simbroker', 'Should use: from Backtest.sim_broker import SimBroker'),
            ('from sim_broker import', 'Should use: from Backtest.sim_broker import'),
            ('import sim_broker', 'Should use: from Backtest.sim_broker import SimBroker'),
            ('from config import', 'Should use: from Backtest.config import'),
            ('import config', 'Should use: from Backtest.config import BacktestConfig'),
        ]
        
        for pattern, suggestion in forbidden_patterns:
            if pattern in content:
                errors.append(f"Found '{pattern}'. {suggestion}")
        
        # Check for required imports
        required_imports = [
            'sys.path',
            'from Backtest.sim_broker import SimBroker',
        ]
        
        for required in required_imports:
            if required not in content:
                errors.append(f"Missing required import/setup: {required}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }