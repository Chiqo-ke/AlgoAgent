"""
Bot Verification Service
========================

Automated service to test bot scripts and update verification status.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction

logger = logging.getLogger(__name__)

# Add Backtest to path
BACKTEST_DIR = Path(__file__).parent.parent / "Backtest"
sys.path.insert(0, str(BACKTEST_DIR))


class BotVerificationService:
    """Service to test and verify bot trading capabilities"""
    
    def __init__(self):
        self.default_test_config = {
            'symbol': 'AAPL',
            'start_date': (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d'),
            'end_date': datetime.now().strftime('%Y-%m-%d'),
            'timeframe': '1d',
            'initial_balance': 10000,
            'commission': 0.002
        }
    
    def test_bot_script(self, bot_script_path: str, test_config: dict = None):
        """
        Test a bot script by running a backtest
        
        Args:
            bot_script_path: Path to bot .py file
            test_config: Optional test configuration
        
        Returns:
            dict with test results
        """
        config = test_config or self.default_test_config
        
        try:
            # Import backtesting adapter
            from Backtest.backtesting_adapter import run_backtest_from_canonical
            
            # Read bot file
            bot_file = Path(bot_script_path)
            if not bot_file.exists():
                return {
                    'success': False,
                    'error': f'Bot file not found: {bot_script_path}'
                }
            
            # Check if there's a corresponding JSON file
            json_file = bot_file.with_suffix('.json')
            if not json_file.exists():
                return {
                    'success': False,
                    'error': f'Canonical JSON not found: {json_file}'
                }
            
            # Load canonical JSON
            import json
            with open(json_file, 'r') as f:
                canonical_json = json.load(f)
            
            logger.info(f"Testing bot: {bot_file.name}")
            
            # Run backtest
            results, trades = run_backtest_from_canonical(
                canonical_json=canonical_json,
                symbol=config['symbol'],
                start_date=config['start_date'],
                end_date=config['end_date'],
                interval=config['timeframe'],
                initial_cash=config['initial_balance'],
                commission=config['commission'],
                strategy_name=canonical_json.get('strategy_name', bot_file.stem)
            )
            
            # Count trades
            total_trades = int(results.get('# Trades', 0))
            
            return {
                'success': True,
                'total_trades': total_trades,
                'trades': trades,
                'results': results,
                'passed': total_trades > 0,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Error testing bot {bot_script_path}: {e}")
            return {
                'success': False,
                'total_trades': 0,
                'error': str(e),
                'passed': False
            }
    
    def verify_strategy(self, strategy_id: int, test_config: dict = None):
        """
        Test and verify a strategy bot
        
        Args:
            strategy_id: Strategy database ID
            test_config: Optional test configuration
        
        Returns:
            BotPerformance instance
        """
        from strategy_api.models import Strategy
        from strategy_api.bot_performance import BotPerformance, BotTestRun
        from backtest_api.models import BacktestRun, BacktestConfig
        from decimal import Decimal
        
        try:
            strategy = Strategy.objects.get(id=strategy_id)
        except Strategy.DoesNotExist:
            logger.error(f"Strategy {strategy_id} not found")
            return None
        
        # Get or create performance tracker
        performance, created = BotPerformance.objects.get_or_create(
            strategy=strategy,
            defaults={
                'verification_status': 'testing'
            }
        )
        
        # Find bot script in codes directory
        codes_dir = BACKTEST_DIR / 'codes'
        bot_file = None
        
        # First, check if strategy has file_path specified
        if hasattr(strategy, 'file_path') and strategy.file_path:
            bot_file_path = BACKTEST_DIR.parent / strategy.file_path
            if bot_file_path.exists():
                bot_file = bot_file_path
                logger.info(f"Found bot file from strategy.file_path: {bot_file}")
        
        # If not found, try to find by strategy name
        if not bot_file:
            bot_files = list(codes_dir.glob(f'{strategy.name.lower().replace(" ", "")[:20]}*.py'))
            if bot_files:
                bot_file = bot_files[0]
        
        # Try by strategy ID or algo prefix
        if not bot_file:
            bot_files = list(codes_dir.glob(f'algo*{strategy.id}*.py'))
            if bot_files:
                bot_file = bot_files[0]
        
        # Try extracting bot name from strategy name or tags
        if not bot_file:
            # Look for algo numbers in strategy name
            import re
            match = re.search(r'(algo\d+)', strategy.name.lower())
            if match:
                bot_name = match.group(1)
                bot_files = list(codes_dir.glob(f'{bot_name}*.py'))
                if bot_files:
                    bot_file = bot_files[0]
        
        if not bot_file:
            logger.warning(f"No bot script found for strategy: {strategy.name}")
            performance.verification_status = 'failed'
            performance.verification_notes = "No bot script file found in codes directory"
            performance.save()
            return performance
        
        logger.info(f"Testing bot script: {bot_file}")
        
        # Run test
        test_result = self.test_bot_script(str(bot_file), test_config)
        
        if not test_result['success']:
            performance.verification_status = 'failed'
            performance.verification_notes = f"Test failed: {test_result.get('error', 'Unknown error')}"
            performance.save()
            return performance
        
        # Create BacktestRun record
        config_data = test_config or self.default_test_config
        
        with transaction.atomic():
            # Create or get config
            config, _ = BacktestConfig.objects.get_or_create(
                name=f"Bot verification test - {strategy.name}",
                defaults={
                    'description': 'Automated bot verification test',
                    'start_date': config_data['start_date'],
                    'end_date': config_data['end_date'],
                    'initial_capital': Decimal(str(config_data['initial_balance'])),
                    'commission': Decimal(str(config_data['commission'])),
                    'timeframe': config_data['timeframe']
                }
            )
            
            # Create backtest run
            backtest_run = BacktestRun.objects.create(
                run_id=f"verify_{strategy.id}_{int(timezone.now().timestamp())}",
                config=config,
                strategy=strategy,
                symbols=[config_data['symbol']],
                status='completed',
                total_trades=test_result['total_trades'],
                total_return=Decimal(str(test_result['results'].get('Return [%]', 0))),
                win_rate=Decimal(str(test_result['results'].get('Win Rate [%]', 0))),
                sharpe_ratio=Decimal(str(test_result['results'].get('Sharpe Ratio', 0))),
                max_drawdown=Decimal(str(test_result['results'].get('Max. Drawdown [%]', 0))),
                completed_at=timezone.now()
            )
            
            # Update performance from backtest
            performance.update_from_backtest(backtest_run)
            
            # Create test run record
            BotTestRun.objects.create(
                performance=performance,
                backtest_run=backtest_run,
                passed=test_result['passed'],
                trades_made=test_result['total_trades']
            )
        
        logger.info(
            f"Verification complete for {strategy.name}: "
            f"{performance.verification_status} - {performance.total_trades} trades"
        )
        
        return performance
    
    def verify_all_bots(self, force_retest=False):
        """
        Test all strategy bots in the system
        
        Args:
            force_retest: If True, retest even verified bots
        
        Returns:
            dict with verification summary
        """
        from strategy_api.models import Strategy
        from strategy_api.bot_performance import BotPerformance
        
        # Get all strategies
        strategies = Strategy.objects.filter(status='active')
        
        results = {
            'total': strategies.count(),
            'verified': 0,
            'failed': 0,
            'testing': 0,
            'errors': []
        }
        
        for strategy in strategies:
            # Skip if already verified and not forcing retest
            if not force_retest:
                existing = BotPerformance.objects.filter(
                    strategy=strategy,
                    is_verified=True
                ).exists()
                if existing:
                    results['verified'] += 1
                    continue
            
            try:
                performance = self.verify_strategy(strategy.id)
                
                if performance:
                    if performance.is_verified:
                        results['verified'] += 1
                    elif performance.verification_status == 'failed':
                        results['failed'] += 1
                    else:
                        results['testing'] += 1
                else:
                    results['errors'].append(f"Strategy {strategy.id}: No performance result")
                    
            except Exception as e:
                logger.error(f"Error verifying strategy {strategy.id}: {e}")
                results['errors'].append(f"Strategy {strategy.id}: {str(e)}")
        
        return results
    
    def get_verified_bots(self):
        """Get list of all verified bots"""
        from strategy_api.bot_performance import BotPerformance
        
        return BotPerformance.objects.filter(
            is_verified=True
        ).select_related('strategy').order_by('-total_return')
