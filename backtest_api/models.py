"""
Backtest API Models for AlgoAgent
=================================

Django models for storing backtest configurations, runs, and results.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import json


class BacktestConfig(models.Model):
    """Model for storing backtest configurations"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Backtest parameters
    start_date = models.DateField()
    end_date = models.DateField()
    initial_capital = models.DecimalField(
        max_digits=20, 
        decimal_places=2, 
        default=Decimal('10000.00'),
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Trading parameters
    commission = models.DecimalField(
        max_digits=10, 
        decimal_places=6, 
        default=Decimal('0.001'),
        help_text="Commission rate (e.g., 0.001 = 0.1%)"
    )
    slippage = models.DecimalField(
        max_digits=10, 
        decimal_places=6, 
        default=Decimal('0.0005'),
        help_text="Slippage rate"
    )
    
    # Risk management
    max_position_size = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('1.00'),
        help_text="Maximum position size as fraction of capital"
    )
    stop_loss = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Stop loss percentage"
    )
    take_profit = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Take profit percentage"
    )
    
    # Data configuration
    data_source = models.CharField(max_length=50, default='yfinance')
    timeframe = models.CharField(max_length=10, default='1d')
    benchmark_symbol = models.CharField(max_length=20, default='SPY', help_text="Benchmark for comparison")
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_template = models.BooleanField(default=False, help_text="Is this a template configuration?")
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.start_date} to {self.end_date})"


class BacktestRun(models.Model):
    """Model for storing backtest execution runs"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('queued', 'Queued'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    run_id = models.CharField(max_length=100, unique=True)
    config = models.ForeignKey(BacktestConfig, on_delete=models.CASCADE, related_name='runs')
    strategy = models.ForeignKey('strategy_api.Strategy', on_delete=models.CASCADE, related_name='backtest_runs')
    symbols = models.JSONField(help_text="List of symbols to backtest")
    
    # Execution status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Completion percentage"
    )
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    execution_time = models.DecimalField(
        max_digits=10, 
        decimal_places=3, 
        null=True, 
        blank=True,
        help_text="Execution time in seconds"
    )
    
    # Results summary
    total_return = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    annualized_return = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    max_drawdown = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    sharpe_ratio = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    total_trades = models.IntegerField(null=True, blank=True)
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Error handling
    error_message = models.TextField(blank=True)
    error_traceback = models.TextField(blank=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.run_id} - {self.strategy.name} ({self.status})"


class BacktestResult(models.Model):
    """Model for storing detailed backtest results"""
    run = models.OneToOneField(BacktestRun, on_delete=models.CASCADE, related_name='result')
    
    # Portfolio metrics
    final_portfolio_value = models.DecimalField(max_digits=20, decimal_places=2)
    total_return_pct = models.DecimalField(max_digits=15, decimal_places=6)
    annualized_return_pct = models.DecimalField(max_digits=15, decimal_places=6)
    volatility = models.DecimalField(max_digits=15, decimal_places=6)
    sharpe_ratio = models.DecimalField(max_digits=15, decimal_places=6)
    sortino_ratio = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    calmar_ratio = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    
    # Drawdown metrics
    max_drawdown_pct = models.DecimalField(max_digits=15, decimal_places=6)
    max_drawdown_duration = models.IntegerField(help_text="Max drawdown duration in days")
    current_drawdown_pct = models.DecimalField(max_digits=15, decimal_places=6)
    
    # Trading metrics
    total_trades = models.IntegerField()
    winning_trades = models.IntegerField()
    losing_trades = models.IntegerField()
    win_rate_pct = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Trade statistics
    avg_trade_return_pct = models.DecimalField(max_digits=15, decimal_places=6)
    avg_winning_trade_pct = models.DecimalField(max_digits=15, decimal_places=6)
    avg_losing_trade_pct = models.DecimalField(max_digits=15, decimal_places=6)
    largest_winning_trade_pct = models.DecimalField(max_digits=15, decimal_places=6)
    largest_losing_trade_pct = models.DecimalField(max_digits=15, decimal_places=6)
    
    # Additional metrics
    profit_factor = models.DecimalField(max_digits=15, decimal_places=6)
    recovery_factor = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    payoff_ratio = models.DecimalField(max_digits=15, decimal_places=6)
    
    # Benchmark comparison
    benchmark_return_pct = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    alpha = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    beta = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    
    # Time series data (stored as JSON for flexibility)
    portfolio_values = models.JSONField(help_text="Time series of portfolio values")
    returns = models.JSONField(help_text="Time series of returns")
    drawdowns = models.JSONField(help_text="Time series of drawdowns")
    positions = models.JSONField(help_text="Position sizes over time")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Results for {self.run.run_id}"


class Trade(models.Model):
    """Model for storing individual trades"""
    TRADE_TYPE_CHOICES = [
        ('long', 'Long'),
        ('short', 'Short'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ]
    
    run = models.ForeignKey(BacktestRun, on_delete=models.CASCADE, related_name='trades')
    symbol = models.CharField(max_length=20)
    trade_type = models.CharField(max_length=10, choices=TRADE_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    # Entry details
    entry_date = models.DateTimeField()
    entry_price = models.DecimalField(max_digits=20, decimal_places=6)
    quantity = models.DecimalField(max_digits=20, decimal_places=6)
    entry_value = models.DecimalField(max_digits=20, decimal_places=2)
    entry_commission = models.DecimalField(max_digits=20, decimal_places=6, default=0)
    
    # Exit details
    exit_date = models.DateTimeField(null=True, blank=True)
    exit_price = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    exit_value = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    exit_commission = models.DecimalField(max_digits=20, decimal_places=6, default=0)
    
    # Performance
    pnl = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    pnl_pct = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    holding_period = models.IntegerField(null=True, blank=True, help_text="Holding period in days")
    
    # Trade metadata
    signal_name = models.CharField(max_length=100, blank=True, help_text="Signal that triggered the trade")
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-entry_date']
    
    def __str__(self):
        return f"{self.trade_type.upper()} {self.symbol} - {self.entry_date.date()} ({self.status})"


class BacktestAlert(models.Model):
    """Model for storing backtest alerts and notifications"""
    ALERT_TYPE_CHOICES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('success', 'Success'),
    ]
    
    run = models.ForeignKey(BacktestRun, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    timestamp = models.DateTimeField()
    
    # Additional context
    symbol = models.CharField(max_length=20, blank=True)
    trade_id = models.CharField(max_length=100, blank=True)
    context_data = models.JSONField(default=dict, help_text="Additional context information")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.alert_type.upper()}: {self.title}"
