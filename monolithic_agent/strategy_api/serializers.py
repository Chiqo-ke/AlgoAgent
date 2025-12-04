"""
Strategy API Serializers for AlgoAgent
======================================

Django REST Framework serializers for the strategy API.
"""

from rest_framework import serializers
from .models import (
    StrategyTemplate, Strategy, StrategyValidation, StrategyPerformance, 
    StrategyComment, StrategyTag, StrategyChat, StrategyChatMessage
)


class StrategyTemplateSerializer(serializers.ModelSerializer):
    """Serializer for StrategyTemplate model"""
    
    class Meta:
        model = StrategyTemplate
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'created_by')


class StrategySerializer(serializers.ModelSerializer):
    """Serializer for Strategy model"""
    template_name = serializers.CharField(source='template.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    # NEW: Add fields for execution results and fix attempts
    execution_result = serializers.JSONField(read_only=True, required=False)
    fix_attempts = serializers.IntegerField(read_only=True, required=False)
    key_rotation_enabled = serializers.BooleanField(read_only=True, required=False, default=False)
    
    class Meta:
        model = Strategy
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'last_validated', 'created_by')


class StrategyValidationSerializer(serializers.ModelSerializer):
    """Serializer for StrategyValidation model"""
    strategy_name = serializers.CharField(source='strategy.name', read_only=True)
    
    class Meta:
        model = StrategyValidation
        fields = '__all__'
        read_only_fields = ('created_at', 'completed_at')


class StrategyPerformanceSerializer(serializers.ModelSerializer):
    """Serializer for StrategyPerformance model"""
    strategy_name = serializers.CharField(source='strategy.name', read_only=True)
    
    class Meta:
        model = StrategyPerformance
        fields = '__all__'
        read_only_fields = ('created_at',)


class StrategyCommentSerializer(serializers.ModelSerializer):
    """Serializer for StrategyComment model"""
    author_username = serializers.CharField(source='author.username', read_only=True)
    strategy_name = serializers.CharField(source='strategy.name', read_only=True)
    
    class Meta:
        model = StrategyComment
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'author')


class StrategyTagSerializer(serializers.ModelSerializer):
    """Serializer for StrategyTag model"""
    
    class Meta:
        model = StrategyTag
        fields = '__all__'
        read_only_fields = ('created_at',)


# Custom serializers for specific API endpoints

class StrategyValidationRequestSerializer(serializers.Serializer):
    """Serializer for strategy validation requests"""
    strategy_id = serializers.IntegerField()
    validation_types = serializers.ListField(
        child=serializers.CharField(max_length=50),
        default=['syntax', 'logic', 'security'],
        help_text="Types of validation to perform"
    )
    config = serializers.JSONField(
        default=dict,
        help_text="Additional validation configuration"
    )


class StrategyExecutionSerializer(serializers.Serializer):
    """Serializer for execution results"""
    success = serializers.BooleanField()
    return_pct = serializers.FloatField(allow_null=True)
    num_trades = serializers.IntegerField(allow_null=True)
    win_rate = serializers.FloatField(allow_null=True)
    sharpe_ratio = serializers.FloatField(allow_null=True)
    max_drawdown = serializers.FloatField(allow_null=True)
    results_file = serializers.CharField(allow_null=True)
    execution_time = serializers.FloatField(allow_null=True)
    error = serializers.CharField(allow_null=True, required=False)


class StrategyFixAttemptSerializer(serializers.Serializer):
    """Serializer for individual fix attempts"""
    attempt = serializers.IntegerField()
    success = serializers.BooleanField()
    error_type = serializers.CharField(allow_null=True)
    error_message = serializers.CharField(allow_null=True)
    severity = serializers.CharField(allow_null=True)
    fix_applied = serializers.BooleanField()


class StrategyGenerateRequestSerializer(serializers.Serializer):
    """Serializer for strategy generation requests"""
    description = serializers.CharField()
    auto_fix = serializers.BooleanField(default=True)
    execute_after_generation = serializers.BooleanField(default=False)
    max_fix_attempts = serializers.IntegerField(default=3, min_value=1, max_value=10)


class StrategyCreateRequestSerializer(serializers.Serializer):
    """Serializer for strategy creation requests"""
    name = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, default='')
    template_id = serializers.IntegerField(required=False)
    strategy_code = serializers.CharField()
    parameters = serializers.JSONField(default=dict)
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        default=list
    )
    timeframe = serializers.CharField(max_length=20, required=False, allow_blank=True, default='')
    risk_level = serializers.CharField(max_length=20, required=False, allow_blank=True, default='')
    expected_return = serializers.DecimalField(max_digits=10, decimal_places=4, required=False, allow_null=True, default=None)
    max_drawdown = serializers.DecimalField(max_digits=10, decimal_places=4, required=False, allow_null=True, default=None)


class StrategyCodeGenerationRequestSerializer(serializers.Serializer):
    """Serializer for strategy code generation requests"""
    strategy_description = serializers.CharField()
    template_id = serializers.IntegerField(required=False)
    parameters = serializers.JSONField(default=dict)
    use_gemini = serializers.BooleanField(default=True)


class StrategySearchSerializer(serializers.Serializer):
    """Serializer for strategy search requests"""
    query = serializers.CharField(required=False, default='')
    category = serializers.CharField(required=False, default='')
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        default=list
    )
    status = serializers.CharField(required=False, default='')
    risk_level = serializers.CharField(required=False, default='')
    timeframe = serializers.CharField(required=False, default='')
    created_by = serializers.CharField(required=False, default='')


class StrategyListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for strategy lists"""
    template_name = serializers.CharField(source='template.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    validation_status = serializers.SerializerMethodField()
    latest_performance = serializers.SerializerMethodField()
    
    class Meta:
        model = Strategy
        fields = [
            'id', 'name', 'description', 'status', 'version', 'tags',
            'timeframe', 'risk_level', 'template_name', 'created_by_username',
            'created_at', 'updated_at', 'validation_status', 'latest_performance'
        ]
    
    def get_validation_status(self, obj):
        """Get latest validation status"""
        latest_validation = obj.validations.first()
        if latest_validation:
            return {
                'status': latest_validation.status,
                'score': latest_validation.score,
                'created_at': latest_validation.created_at
            }
        return None
    
    def get_latest_performance(self, obj):
        """Get latest performance metrics"""
        latest_performance = obj.performance_records.first()
        if latest_performance:
            return {
                'total_return': latest_performance.total_return,
                'sharpe_ratio': latest_performance.sharpe_ratio,
                'max_drawdown': latest_performance.max_drawdown,
                'win_rate': latest_performance.win_rate,
                'created_at': latest_performance.created_at
            }
        return None


class StrategyAIValidationRequestSerializer(serializers.Serializer):
    """Serializer for AI-powered strategy validation requests"""
    strategy_text = serializers.CharField(
        help_text="Raw strategy description in plain text or numbered steps"
    )
    input_type = serializers.ChoiceField(
        choices=['auto', 'numbered', 'freetext', 'url'],
        default='auto',
        help_text="Type of input format"
    )
    use_gemini = serializers.BooleanField(
        default=True,
        help_text="Enable Gemini AI-powered analysis"
    )
    strict_mode = serializers.BooleanField(
        default=False,
        help_text="Enable strict security validation"
    )
    session_id = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional chat session ID for conversation memory"
    )
    use_context = serializers.BooleanField(
        default=True,
        help_text="Use conversation context from session history"
    )


class StrategyAIValidationResponseSerializer(serializers.Serializer):
    """Serializer for AI validation response"""
    status = serializers.CharField()
    canonicalized_steps = serializers.ListField(child=serializers.CharField(), required=False)
    classification = serializers.CharField(required=False)
    classification_detail = serializers.JSONField(required=False)
    recommendations = serializers.CharField(required=False)
    recommendations_list = serializers.ListField(child=serializers.JSONField(), required=False)
    confidence = serializers.CharField(required=False)
    next_actions = serializers.ListField(child=serializers.CharField(), required=False)
    warnings = serializers.ListField(child=serializers.CharField(), required=False)
    canonical_json = serializers.CharField(required=False)
    canonical_json_formatted = serializers.CharField(required=False)
    metadata = serializers.JSONField(required=False)
    provenance = serializers.JSONField(required=False)
    message = serializers.CharField(required=False)
    issues = serializers.ListField(child=serializers.CharField(), required=False)


class StrategyCreateWithAIRequestSerializer(serializers.Serializer):
    """Serializer for creating a strategy with AI validation"""
    strategy_text = serializers.CharField(
        help_text="Raw strategy description - will be validated by AI"
    )
    input_type = serializers.ChoiceField(
        choices=['auto', 'numbered', 'freetext', 'url'],
        default='auto',
        help_text="Type of input format"
    )
    name = serializers.CharField(
        max_length=200,
        required=False,
        help_text="Strategy name (auto-generated if not provided)"
    )
    description = serializers.CharField(
        required=False,
        default='',
        help_text="Additional description"
    )
    template_id = serializers.IntegerField(
        required=False,
        help_text="Optional template to link to"
    )
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        default=list,
        help_text="Tags for categorization"
    )
    use_gemini = serializers.BooleanField(
        default=True,
        help_text="Enable Gemini AI-powered analysis"
    )
    strict_mode = serializers.BooleanField(
        default=False,
        help_text="Enable strict security validation"
    )
    save_to_backtest = serializers.BooleanField(
        default=False,
        help_text="Save canonical JSON to Backtest/codes/"
    )
    session_id = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional chat session ID for conversation memory"
    )
    use_context = serializers.BooleanField(
        default=True,
        help_text="Use conversation context from session history"
    )


# Chat Session Serializers

class StrategyChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for StrategyChatMessage model"""
    
    class Meta:
        model = StrategyChatMessage
        fields = ['id', 'role', 'content', 'tokens_used', 'metadata', 'function_call', 'created_at']
        read_only_fields = ['id', 'created_at']


class StrategyChatSerializer(serializers.ModelSerializer):
    """Serializer for StrategyChat model"""
    messages = StrategyChatMessageSerializer(many=True, read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    strategy_name = serializers.CharField(source='strategy.name', read_only=True)
    
    class Meta:
        model = StrategyChat
        fields = [
            'id', 'session_id', 'user', 'user_username', 'title', 'strategy', 'strategy_name',
            'is_active', 'context_summary', 'message_count', 'model_name', 'temperature',
            'max_tokens', 'created_at', 'updated_at', 'last_message_at', 'messages'
        ]
        read_only_fields = ['id', 'session_id', 'message_count', 'created_at', 'updated_at', 'last_message_at']


class StrategyChatListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing chat sessions (without full message history)"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    strategy_name = serializers.CharField(source='strategy.name', read_only=True)
    
    class Meta:
        model = StrategyChat
        fields = [
            'id', 'session_id', 'user_username', 'title', 'strategy_name',
            'is_active', 'message_count', 'created_at', 'updated_at', 'last_message_at'
        ]
        read_only_fields = ['id', 'session_id', 'message_count', 'created_at', 'updated_at', 'last_message_at']


class ChatMessageRequestSerializer(serializers.Serializer):
    """Serializer for sending a message in a chat session"""
    message = serializers.CharField(help_text="User's message to the AI")
    session_id = serializers.CharField(
        required=False,
        help_text="Existing session ID (if not provided, creates new session)"
    )
    strategy_id = serializers.IntegerField(
        required=False,
        help_text="Link this chat to a specific strategy"
    )
    use_context = serializers.BooleanField(
        default=True,
        help_text="Include conversation history in AI response"
    )


class ChatResponseSerializer(serializers.Serializer):
    """Serializer for AI chat responses"""
    session_id = serializers.CharField(help_text="Chat session ID")
    message = serializers.CharField(help_text="AI's response")
    message_count = serializers.IntegerField(help_text="Total messages in session")
    context_used = serializers.BooleanField(help_text="Whether conversation context was used")
    
