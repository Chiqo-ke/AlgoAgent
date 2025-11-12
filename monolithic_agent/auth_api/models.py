"""
Authentication API Models for AlgoAgent
========================================

Models for user profiles, AI context, and chat sessions.
"""

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """Extended user profile with trading preferences and AI context"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # User preferences
    default_risk_tolerance = models.CharField(
        max_length=20, 
        choices=[
            ('conservative', 'Conservative'),
            ('moderate', 'Moderate'),
            ('aggressive', 'Aggressive'),
        ],
        default='moderate'
    )
    default_timeframe = models.CharField(max_length=20, default='1d', help_text="Preferred trading timeframe")
    preferred_symbols = models.JSONField(default=list, help_text="List of preferred trading symbols")
    
    # AI Context - User's strategic preferences
    trading_goals = models.TextField(blank=True, help_text="User's trading goals and objectives")
    strategy_preferences = models.TextField(blank=True, help_text="Preferred strategy types and approaches")
    risk_parameters = models.JSONField(default=dict, help_text="Custom risk parameters")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_active = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Profile: {self.user.username}"


class AIContext(models.Model):
    """Store user instructions and context for AI interactions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_contexts')
    
    # Context information
    session_name = models.CharField(max_length=200, help_text="Name for this context session")
    instructions = models.TextField(help_text="User instructions for the AI agent")
    context_data = models.JSONField(default=dict, help_text="Additional structured context data")
    
    # Session metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-last_used']
        verbose_name_plural = "AI Contexts"
    
    def __str__(self):
        return f"{self.user.username} - {self.session_name}"


class ChatSession(models.Model):
    """Store AI chat sessions for strategy development"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    ai_context = models.ForeignKey(AIContext, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Session info
    session_id = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=200, default="New Strategy Session")
    
    # Link to strategy template (for strategy development sessions)
    # Note: This creates a circular import, so we use string reference
    strategy_template_id = models.IntegerField(
        null=True, 
        blank=True,
        help_text="ID of the StrategyTemplate this session is developing"
    )
    
    # Conversation history
    messages = models.JSONField(default=list, help_text="Chat message history")
    
    # Generated artifacts
    generated_strategies = models.JSONField(default=list, help_text="List of strategy IDs generated in this session")
    
    # Session state
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"


class ChatMessage(models.Model):
    """Individual chat messages in a session"""
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'AI Assistant'),
        ('system', 'System'),
    ]
    
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='chat_messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    
    # Message metadata
    metadata = models.JSONField(default=dict, help_text="Additional message metadata")
    tokens_used = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


# Signal to automatically create UserProfile when a User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile automatically when a new User is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the UserProfile when the User is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
