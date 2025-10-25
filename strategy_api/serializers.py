"""
Strategy API Serializers for AlgoAgent
======================================

Django REST Framework serializers for the strategy API.
"""

from rest_framework import serializers
from .models import StrategyTemplate, Strategy, StrategyValidation, StrategyPerformance, StrategyComment, StrategyTag


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
    timeframe = serializers.CharField(max_length=20, required=False, default='')
    risk_level = serializers.CharField(max_length=20, required=False, default='')


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