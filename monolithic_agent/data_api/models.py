"""
Data API Models for AlgoAgent
============================

Django models for storing market data, indicators, and data requests.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import json


class Symbol(models.Model):
    """Model for storing tradeable symbols"""
    symbol = models.CharField(max_length=20, unique=True, help_text="Trading symbol (e.g., AAPL, MSFT)")
    name = models.CharField(max_length=255, help_text="Full company/asset name")
    exchange = models.CharField(max_length=50, blank=True, help_text="Exchange where symbol is traded")
    sector = models.CharField(max_length=100, blank=True, help_text="Business sector")
    industry = models.CharField(max_length=100, blank=True, help_text="Industry classification")
    is_active = models.BooleanField(default=True, help_text="Whether symbol is actively tracked")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['symbol']

    def __str__(self):
        return f"{self.symbol} - {self.name}"


class DataRequest(models.Model):
    """Model for tracking data fetch requests"""
    PERIOD_CHOICES = [
        ('1d', '1 Day'),
        ('5d', '5 Days'),
        ('1mo', '1 Month'),
        ('3mo', '3 Months'),
        ('6mo', '6 Months'),
        ('1y', '1 Year'),
        ('2y', '2 Years'),
        ('5y', '5 Years'),
        ('10y', '10 Years'),
        ('ytd', 'Year to Date'),
        ('max', 'Maximum Available'),
    ]
    
    INTERVAL_CHOICES = [
        ('1m', '1 Minute'),
        ('2m', '2 Minutes'),
        ('5m', '5 Minutes'),
        ('15m', '15 Minutes'),
        ('30m', '30 Minutes'),
        ('60m', '1 Hour'),
        ('90m', '90 Minutes'),
        ('1h', '1 Hour'),
        ('1d', '1 Day'),
        ('5d', '5 Days'),
        ('1wk', '1 Week'),
        ('1mo', '1 Month'),
        ('3mo', '3 Months'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    request_id = models.CharField(max_length=50, unique=True)
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE)
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, default='1y')
    interval = models.CharField(max_length=10, choices=INTERVAL_CHOICES, default='1d')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.request_id} - {self.symbol.symbol} ({self.status})"


class MarketData(models.Model):
    """Model for storing market data points"""
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    open_price = models.DecimalField(max_digits=20, decimal_places=6)
    high_price = models.DecimalField(max_digits=20, decimal_places=6)
    low_price = models.DecimalField(max_digits=20, decimal_places=6)
    close_price = models.DecimalField(max_digits=20, decimal_places=6)
    volume = models.BigIntegerField()
    adj_close = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    interval = models.CharField(max_length=10, default='1d')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['symbol', 'timestamp', 'interval']
        ordering = ['symbol', 'timestamp']
    
    def __str__(self):
        return f"{self.symbol.symbol} - {self.timestamp} ({self.interval})"


class Indicator(models.Model):
    """Model for storing indicator definitions"""
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, help_text="e.g., trend, momentum, volatility, volume")
    parameters = models.JSONField(default=dict, help_text="Default parameters for the indicator")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.display_name} ({self.name})"


class IndicatorData(models.Model):
    """Model for storing calculated indicator values"""
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE)
    indicator = models.ForeignKey(Indicator, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    value = models.JSONField(help_text="Indicator value(s) - can be single value or multiple values")
    parameters = models.JSONField(help_text="Parameters used for this calculation")
    interval = models.CharField(max_length=10, default='1d')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['symbol', 'indicator', 'timestamp', 'interval']
        ordering = ['symbol', 'indicator', 'timestamp']
    
    def __str__(self):
        return f"{self.symbol.symbol} - {self.indicator.name} - {self.timestamp}"


class DataCache(models.Model):
    """Model for caching processed data and indicators"""
    cache_key = models.CharField(max_length=255, unique=True)
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE)
    data_type = models.CharField(max_length=50, help_text="Type of cached data (market_data, indicators, etc.)")
    parameters = models.JSONField(default=dict, help_text="Parameters used to generate this cache")
    data = models.JSONField(help_text="Cached data")
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    accessed_at = models.DateTimeField(auto_now=True)
    access_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Cache: {self.cache_key}"
