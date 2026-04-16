from django.contrib import admin
from .models import (
    StrategyTemplate, Strategy, StrategyValidation, StrategyPerformance,
    StrategyComment, StrategyTag, StrategyChat, StrategyChatMessage,
    LatestBacktestResult,
)


@admin.register(StrategyTemplate)
class StrategyTemplateAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'category', 'is_system_template', 'is_active', 'created_by', 'created_at']
    list_filter = ['category', 'is_system_template', 'is_active']
    search_fields = ['name', 'description', 'category']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'version', 'status', 'risk_level', 'timeframe', 'created_by', 'created_at']
    list_filter = ['status', 'risk_level', 'timeframe']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'last_validated']


@admin.register(StrategyValidation)
class StrategyValidationAdmin(admin.ModelAdmin):
    list_display = ['id', 'strategy', 'validation_type', 'status', 'score', 'created_at']
    list_filter = ['status', 'validation_type']
    search_fields = ['strategy__name', 'validation_type']
    readonly_fields = ['created_at', 'completed_at']


@admin.register(StrategyPerformance)
class StrategyPerformanceAdmin(admin.ModelAdmin):
    list_display = ['id', 'strategy', 'total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate', 'total_trades', 'created_at']
    list_filter = ['strategy']
    search_fields = ['strategy__name']
    readonly_fields = ['created_at']


@admin.register(StrategyComment)
class StrategyCommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'strategy', 'author', 'rating', 'is_review', 'created_at']
    list_filter = ['is_review', 'rating']
    search_fields = ['strategy__name', 'author__username', 'content']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(StrategyTag)
class StrategyTagAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'color', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']


@admin.register(StrategyChat)
class StrategyChatAdmin(admin.ModelAdmin):
    list_display = ['id', 'session_id', 'user', 'strategy', 'is_active', 'message_count', 'model_name', 'created_at']
    list_filter = ['is_active', 'model_name']
    search_fields = ['session_id', 'user__username', 'title']
    readonly_fields = ['created_at', 'updated_at', 'last_message_at']


@admin.register(StrategyChatMessage)
class StrategyChatMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'role', 'tokens_used', 'created_at']
    list_filter = ['role']
    search_fields = ['session__session_id', 'content']
    readonly_fields = ['created_at']


@admin.register(LatestBacktestResult)
class LatestBacktestResultAdmin(admin.ModelAdmin):
    list_display = ['strategy', 'symbol', 'timeframe', 'total_return_pct', 'win_rate', 'net_profit', 'sharpe_ratio', 'total_trades', 'updated_at']
    list_filter = ['symbol', 'timeframe']
    search_fields = ['strategy__name', 'symbol']
    readonly_fields = ['created_at', 'updated_at']
