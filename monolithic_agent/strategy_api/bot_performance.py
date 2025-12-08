"""
Bot Performance Tracking System
================================

Tracks bot trading performance and automatically flags verified bots.
"""

from django.db import models
from django.utils import timezone
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class BotPerformance(models.Model):
    """Track performance history for strategy bots"""
    
    VERIFICATION_STATUS = [
        ('unverified', 'Unverified'),
        ('testing', 'Under Testing'),
        ('verified', 'Verified - Makes Trades'),
        ('failed', 'Failed - No Trades'),
    ]
    
    strategy = models.ForeignKey(
        'strategy_api.Strategy',
        on_delete=models.CASCADE,
        related_name='performance_history'
    )
    
    # Verification status
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS,
        default='unverified'
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="True if bot successfully makes trades"
    )
    
    # Trading performance
    total_trades = models.IntegerField(default=0)
    entry_trades = models.IntegerField(default=0)
    exit_trades = models.IntegerField(default=0)
    win_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Win rate percentage"
    )
    total_return = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Total return percentage"
    )
    sharpe_ratio = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True
    )
    max_drawdown = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        null=True,
        blank=True
    )
    
    # Test run details
    symbol_tested = models.CharField(max_length=20, blank=True)
    timeframe_tested = models.CharField(max_length=10, blank=True)
    test_period_start = models.DateField(null=True, blank=True)
    test_period_end = models.DateField(null=True, blank=True)
    
    # Verification criteria
    trades_threshold = models.IntegerField(
        default=2,
        help_text="Minimum trades required for verification"
    )
    verification_notes = models.TextField(
        blank=True,
        help_text="Automated verification notes"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_test_at = models.DateTimeField(default=timezone.now)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Bot Performance'
        verbose_name_plural = 'Bot Performances'
    
    def __str__(self):
        status = "✅" if self.is_verified else "⏳"
        return f"{status} {self.strategy.name} - {self.total_trades} trades"
    
    def update_from_backtest(self, backtest_run):
        """
        Update performance metrics from a BacktestRun instance
        
        Args:
            backtest_run: BacktestRun model instance
        """
        self.total_trades = backtest_run.total_trades or 0
        self.win_rate = backtest_run.win_rate
        self.total_return = backtest_run.total_return
        self.sharpe_ratio = backtest_run.sharpe_ratio
        self.max_drawdown = backtest_run.max_drawdown
        self.last_test_at = timezone.now()
        
        # Update symbol and timeframe from run
        if backtest_run.symbols:
            self.symbol_tested = backtest_run.symbols[0] if isinstance(backtest_run.symbols, list) else backtest_run.symbols
        if backtest_run.config:
            self.timeframe_tested = backtest_run.config.timeframe
            self.test_period_start = backtest_run.config.start_date
            self.test_period_end = backtest_run.config.end_date
        
        # Check verification criteria
        self.check_verification()
        self.save()
    
    def check_verification(self):
        """
        Check if bot meets verification criteria and update status
        """
        old_status = self.is_verified
        
        # Verification criteria: must have at least minimum trades
        if self.total_trades >= self.trades_threshold:
            self.is_verified = True
            self.verification_status = 'verified'
            
            if not self.verified_at:
                self.verified_at = timezone.now()
            
            self.verification_notes = (
                f"✅ Bot verified with {self.total_trades} trades "
                f"(threshold: {self.trades_threshold}). "
            )
            
            if self.total_return:
                self.verification_notes += f"Return: {self.total_return:.2f}%. "
            if self.win_rate:
                self.verification_notes += f"Win rate: {self.win_rate:.2f}%."
            
            # Log verification event
            if not old_status:
                logger.info(
                    f"✅ Bot VERIFIED: {self.strategy.name} - "
                    f"{self.total_trades} trades, "
                    f"Return: {self.total_return}%, "
                    f"Win Rate: {self.win_rate}%"
                )
        else:
            self.is_verified = False
            
            if self.total_trades == 0:
                self.verification_status = 'failed'
                self.verification_notes = (
                    f"❌ Bot made 0 trades (threshold: {self.trades_threshold}). "
                    "Strategy may have logic errors or conditions never met."
                )
            else:
                self.verification_status = 'testing'
                self.verification_notes = (
                    f"⏳ Bot made {self.total_trades} trades "
                    f"(threshold: {self.trades_threshold}). "
                    "Needs more trades for verification."
                )
    
    def get_verification_badge(self):
        """Return badge information for frontend"""
        if self.is_verified:
            return {
                'status': 'verified',
                'label': 'Verified Bot',
                'icon': '✅',
                'color': 'green',
                'description': f'{self.total_trades} trades made'
            }
        elif self.verification_status == 'failed':
            return {
                'status': 'failed',
                'label': 'No Trades',
                'icon': '❌',
                'color': 'red',
                'description': 'Bot made 0 trades'
            }
        elif self.verification_status == 'testing':
            return {
                'status': 'testing',
                'label': 'Testing',
                'icon': '⏳',
                'color': 'yellow',
                'description': f'{self.total_trades}/{self.trades_threshold} trades'
            }
        else:
            return {
                'status': 'unverified',
                'label': 'Not Tested',
                'icon': '❓',
                'color': 'gray',
                'description': 'No test data'
            }


class BotTestRun(models.Model):
    """Track individual test runs for bots"""
    
    performance = models.ForeignKey(
        BotPerformance,
        on_delete=models.CASCADE,
        related_name='test_runs'
    )
    backtest_run = models.OneToOneField(
        'backtest_api.BacktestRun',
        on_delete=models.CASCADE,
        related_name='bot_test'
    )
    
    # Test outcome
    passed = models.BooleanField(default=False)
    trades_made = models.IntegerField(default=0)
    execution_errors = models.TextField(blank=True)
    
    # Timestamps
    tested_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-tested_at']
    
    def __str__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"{status} - {self.performance.strategy.name} ({self.trades_made} trades)"
