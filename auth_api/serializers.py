"""
Authentication API Serializers for AlgoAgent
==============================================

Serializers for user authentication, profiles, and AI chat sessions.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import UserProfile, AIContext, ChatSession, ChatMessage


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model"""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'username', 'email', 'default_risk_tolerance', 'default_timeframe',
            'preferred_symbols', 'trading_goals', 'strategy_preferences',
            'risk_parameters', 'created_at', 'updated_at', 'last_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_active']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label="Confirm Password")
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name']
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
            'email': {'required': True}
        }
    
    def validate(self, attrs):
        """Validate that passwords match"""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        """Create new user with validated data"""
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class AIContextSerializer(serializers.ModelSerializer):
    """Serializer for AIContext model"""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = AIContext
        fields = [
            'id', 'username', 'session_name', 'instructions', 'context_data',
            'is_active', 'created_at', 'updated_at', 'last_used'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_used']


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for ChatMessage model"""
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'metadata', 'tokens_used', 'created_at']
        read_only_fields = ['id', 'created_at']


class ChatSessionSerializer(serializers.ModelSerializer):
    """Serializer for ChatSession model"""
    username = serializers.CharField(source='user.username', read_only=True)
    ai_context_name = serializers.CharField(source='ai_context.session_name', read_only=True, allow_null=True)
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = [
            'id', 'session_id', 'username', 'ai_context', 'ai_context_name',
            'title', 'messages', 'generated_strategies', 'message_count',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'session_id', 'created_at', 'updated_at']
    
    def get_message_count(self, obj):
        """Get count of messages in the session"""
        return len(obj.messages)


class ChatSessionDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for ChatSession with full message history"""
    username = serializers.CharField(source='user.username', read_only=True)
    ai_context_name = serializers.CharField(source='ai_context.session_name', read_only=True, allow_null=True)
    chat_messages = ChatMessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = ChatSession
        fields = [
            'id', 'session_id', 'username', 'ai_context', 'ai_context_name',
            'title', 'messages', 'chat_messages', 'generated_strategies',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'session_id', 'created_at', 'updated_at']


class ChatRequestSerializer(serializers.Serializer):
    """Serializer for chat requests to AI"""
    session_id = serializers.CharField(required=False, allow_null=True, help_text="Existing session ID or null for new session")
    message = serializers.CharField(help_text="User's message to the AI")
    ai_context_id = serializers.IntegerField(required=False, allow_null=True, help_text="AI context to use for this session")
    title = serializers.CharField(required=False, allow_null=True, help_text="Session title (for new sessions)")


class ChatResponseSerializer(serializers.Serializer):
    """Serializer for chat responses from AI"""
    session_id = serializers.CharField()
    title = serializers.CharField()
    user_message = serializers.CharField()
    ai_response = serializers.CharField()
    tokens_used = serializers.IntegerField(required=False)
    generated_strategy_id = serializers.IntegerField(required=False, allow_null=True)
