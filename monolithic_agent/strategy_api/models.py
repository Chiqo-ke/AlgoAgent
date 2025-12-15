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


class StrategyChat(models.Model):
    """Model for storing AI chat sessions with conversation history for strategy development"""
    session_id = models.CharField(max_length=100, unique=True, help_text="Unique session identifier")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='strategy_chat_sessions')
    title = models.CharField(max_length=200, blank=True, help_text="Auto-generated or user-set session title")
    
    # Link to strategy if the chat is about a specific strategy
    strategy = models.ForeignKey(
        Strategy, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='strategy_chat_sessions',
        help_text="Associated strategy for this chat session"
    )
    
    # Session metadata
    is_active = models.BooleanField(default=True, help_text="Is this session still active?")
    context_summary = models.TextField(blank=True, help_text="AI-generated summary of the conversation")
    message_count = models.IntegerField(default=0, help_text="Total number of messages in this session")
    
    # Session configuration
    model_name = models.CharField(max_length=50, default='gemini-2.5-flash', help_text="AI model used")
    temperature = models.FloatField(default=0.7, help_text="Temperature setting for AI responses")
    max_tokens = models.IntegerField(default=2048, help_text="Max tokens for AI responses")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp of last message")
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['user', '-updated_at']),
        ]
    
    def __str__(self):
        return f"StrategyChat {self.session_id} - {self.title or 'Untitled'}"


class StrategyChatMessage(models.Model):
    """Model for storing individual messages in strategy chat sessions"""
    MESSAGE_ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]
    
    session = models.ForeignKey(StrategyChat, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=MESSAGE_ROLE_CHOICES, help_text="Message sender role")
    content = models.TextField(help_text="Message content")
    
    # Message metadata
    tokens_used = models.IntegerField(null=True, blank=True, help_text="Number of tokens in this message")
    
    # Additional context stored with message
    metadata = models.JSONField(default=dict, help_text="Additional metadata (strategy references, validation results, etc.)")
    
    # For assistant messages - track the function/action taken
    function_call = models.JSONField(null=True, blank=True, help_text="Function call data if assistant performed an action")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['session', 'created_at']),
        ]
    
    def __str__(self):
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"{self.role}: {preview}"


class LatestBacktestResult(models.Model):
    """
    Model for storing the LATEST backtest result per strategy.
    This replaces the previous result whenever a new backtest is run.
    One-to-one relationship with Strategy.
    """
    strategy = models.OneToOneField(
        Strategy, 
        on_delete=models.CASCADE, 
        related_name='latest_backtest',
        primary_key=True
    )
    
    # Backtest configuration used
    symbol = models.CharField(max_length=20, default='AAPL')
    timeframe = models.CharField(max_length=20, default='1d')
    period = models.CharField(max_length=20, default='1y', help_text="e.g., 1y, 6mo, 3mo")
    initial_balance = models.DecimalField(max_digits=20, decimal_places=2, default=10000)
    commission = models.DecimalField(max_digits=10, decimal_places=6, default=0.001)
    
    # Performance metrics
    total_trades = models.IntegerField(default=0)
    winning_trades = models.IntegerField(default=0)
    losing_trades = models.IntegerField(default=0)
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Win rate percentage")
    
    # Financial results
    net_profit = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_return_pct = models.DecimalField(max_digits=15, decimal_places=6, default=0)
    final_equity = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    max_drawdown = models.DecimalField(max_digits=15, decimal_places=6, default=0)
    sharpe_ratio = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    
    # Trade list (JSON for flexibility)
    trades = models.JSONField(default=list, help_text="List of all trades with entry/exit details")
    
    # Equity curve for charting (JSON)
    equity_curve = models.JSONField(default=list, help_text="Equity over time for chart")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Latest Backtest Result"
        verbose_name_plural = "Latest Backtest Results"
    
    def __str__(self):
        return f"{self.strategy.name} - {self.symbol} ({self.total_trades} trades, {self.win_rate}% WR)"
    
    @classmethod
    def save_result(cls, strategy_id: int, result_data: dict):
        """
        Save or update the latest backtest result for a strategy.
        Replaces any existing result for the same strategy.
        
        Args:
            strategy_id: The ID of the strategy
            result_data: Dictionary containing backtest results
        
        Returns:
            The created/updated LatestBacktestResult instance
        """
        from decimal import Decimal
        
        defaults = {
            'symbol': result_data.get('symbol', 'AAPL'),
            'timeframe': result_data.get('timeframe', '1d'),
            'period': result_data.get('period', '1y'),
            'initial_balance': Decimal(str(result_data.get('initial_balance', 10000))),
            'commission': Decimal(str(result_data.get('commission', 0.001))),
            'total_trades': result_data.get('total_trades', 0),
            'winning_trades': result_data.get('winning_trades', 0),
            'losing_trades': result_data.get('losing_trades', 0),
            'win_rate': Decimal(str(result_data.get('win_rate', 0))),
            'net_profit': Decimal(str(result_data.get('net_profit', 0))),
            'total_return_pct': Decimal(str(result_data.get('total_return_pct', 0))),
            'final_equity': Decimal(str(result_data.get('final_equity', 0))) if result_data.get('final_equity') else None,
            'max_drawdown': Decimal(str(result_data.get('max_drawdown', 0))),
            'sharpe_ratio': Decimal(str(result_data.get('sharpe_ratio', 0))) if result_data.get('sharpe_ratio') else None,
            'trades': result_data.get('trades', []),
            'equity_curve': result_data.get('equity_curve', []),
        }
        
        obj, created = cls.objects.update_or_create(
            strategy_id=strategy_id,
            defaults=defaults
        )
        
        action = "Created" if created else "Updated"
        print(f"💾 {action} LatestBacktestResult for strategy {strategy_id}")
        
        return obj
