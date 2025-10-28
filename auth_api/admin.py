"""
Authentication API Admin for AlgoAgent
=======================================

Django admin configuration for auth models.
"""

from django.contrib import admin
from .models import UserProfile, AIContext, ChatSession, ChatMessage


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for UserProfile"""
    list_display = ['user', 'default_risk_tolerance', 'default_timeframe', 'created_at', 'last_active']
    list_filter = ['default_risk_tolerance', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'last_active']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Preferences', {
            'fields': ('default_risk_tolerance', 'default_timeframe', 'preferred_symbols')
        }),
        ('AI Context', {
            'fields': ('trading_goals', 'strategy_preferences', 'risk_parameters')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'last_active'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AIContext)
class AIContextAdmin(admin.ModelAdmin):
    """Admin interface for AIContext"""
    list_display = ['user', 'session_name', 'is_active', 'created_at', 'last_used']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username', 'session_name', 'instructions']
    readonly_fields = ['created_at', 'updated_at', 'last_used']
    
    fieldsets = (
        ('Session Info', {
            'fields': ('user', 'session_name', 'is_active')
        }),
        ('Context', {
            'fields': ('instructions', 'context_data')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'last_used'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    """Admin interface for ChatSession"""
    list_display = ['user', 'title', 'session_id', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username', 'title', 'session_id']
    readonly_fields = ['session_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Session Info', {
            'fields': ('user', 'session_id', 'title', 'ai_context', 'is_active')
        }),
        ('Conversation', {
            'fields': ('messages',)
        }),
        ('Artifacts', {
            'fields': ('generated_strategies',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    """Admin interface for ChatMessage"""
    list_display = ['session', 'role', 'content_preview', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['session__title', 'content']
    readonly_fields = ['created_at']
    
    def content_preview(self, obj):
        """Show preview of message content"""
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content Preview'
    
    fieldsets = (
        ('Message Info', {
            'fields': ('session', 'role', 'content')
        }),
        ('Metadata', {
            'fields': ('metadata', 'tokens_used', 'created_at')
        }),
    )
