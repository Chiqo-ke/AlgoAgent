"""
Strategy API Models for AlgoAgent
=================================

Django models for storing trading strategies, validations, and results.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import json


class StrategyTemplate(models.Model):
    """Model for storing strategy templates
    
    Templates serve dual purposes:
    1. Pre-built templates for users to start from
    2. Auto-created templates that track strategy evolution in chat sessions
    """
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField()
    category = models.CharField(max_length=100, help_text="Strategy category (e.g., momentum, mean_reversion)")
    template_code = models.TextField(help_text="Template code with placeholders")
    parameters_schema = models.JSONField(default=dict, help_text="JSON schema for strategy parameters")
    is_active = models.BooleanField(default=True)
    
    # Link to the strategy this template represents (for auto-created templates)
    linked_strategy = models.ForeignKey(
        'Strategy', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='linked_template',
        help_text="Strategy this template is linked to (for chat-based templates)"
    )
    
    # Template type
    is_system_template = models.BooleanField(
        default=False, 
        help_text="True for pre-built templates, False for user/chat-created templates"
    )
    
    # Metadata for tracking latest strategy state
    latest_strategy_code = models.TextField(
        blank=True,
        help_text="Most recent version of the strategy code (auto-updated)"
    )
    latest_parameters = models.JSONField(
        default=dict,
        help_text="Most recent strategy parameters"
    )
    chat_history = models.JSONField(
        default=list,
        help_text="Condensed chat history about this strategy"
    )
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.category})"


class Strategy(models.Model):
    """Model for storing trading strategies"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('validating', 'Validating'),
        ('valid', 'Valid'),
        ('invalid', 'Invalid'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    template = models.ForeignKey(StrategyTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    strategy_code = models.TextField(help_text="Complete strategy code")
    parameters = models.JSONField(default=dict, help_text="Strategy parameters")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    version = models.CharField(max_length=20, default='1.0.0')
    tags = models.JSONField(default=list, help_text="Strategy tags for classification")
    
    # Strategy metadata
    timeframe = models.CharField(max_length=20, blank=True, help_text="Preferred timeframe")
    risk_level = models.CharField(max_length=20, blank=True, help_text="Risk assessment")
    expected_return = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    max_drawdown = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    
    # Ownership and tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_validated = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['name', 'version']
    
    def __str__(self):
        return f"{self.name} v{self.version} ({self.status})"


class StrategyValidation(models.Model):
    """Model for storing strategy validation results"""
    VALIDATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('error', 'Error'),
    ]
    
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name='validations')
    validation_type = models.CharField(max_length=50, help_text="Type of validation (syntax, logic, security, etc.)")
    status = models.CharField(max_length=20, choices=VALIDATION_STATUS_CHOICES, default='pending')
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Validation score 0-100")
    
    # Validation results
    passed_checks = models.JSONField(default=list, help_text="List of passed validation checks")
    failed_checks = models.JSONField(default=list, help_text="List of failed validation checks")
    warnings = models.JSONField(default=list, help_text="List of warnings")
    recommendations = models.JSONField(default=list, help_text="List of recommendations")
    
    # Metadata
    validator_version = models.CharField(max_length=20, blank=True)
    validation_config = models.JSONField(default=dict, help_text="Configuration used for validation")
    execution_time = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, help_text="Validation time in seconds")
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.strategy.name} - {self.validation_type} ({self.status})"


class StrategyPerformance(models.Model):
    """Model for storing strategy performance metrics"""
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name='performance_records')
    backtest_id = models.CharField(max_length=100, blank=True, help_text="Reference to backtest run")
    
    # Performance metrics
    total_return = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    annualized_return = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    volatility = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    sharpe_ratio = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    max_drawdown = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    profit_factor = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    
    # Trading statistics
    total_trades = models.IntegerField(null=True, blank=True)
    winning_trades = models.IntegerField(null=True, blank=True)
    losing_trades = models.IntegerField(null=True, blank=True)
    avg_trade_return = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    
    # Backtest parameters
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    initial_capital = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    final_capital = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.strategy.name} Performance - {self.created_at.date()}"


class StrategyComment(models.Model):
    """Model for strategy comments and reviews"""
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], 
        null=True, blank=True,
        help_text="Rating from 1-5 stars"
    )
    is_review = models.BooleanField(default=False, help_text="Is this a formal review?")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, help_text="Reply to another comment")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment on {self.strategy.name} by {self.author.username}"


class StrategyTag(models.Model):
    """Model for strategy tags/categories"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#000000', help_text="Hex color code for UI")
    strategies = models.ManyToManyField(Strategy, blank=True, related_name='strategy_tags')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
