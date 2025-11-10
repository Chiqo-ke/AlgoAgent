"""
Data API Serializers for AlgoAgent
==================================

Django REST Framework serializers for the data API.
"""

from rest_framework import serializers
from .models import Symbol, DataRequest, MarketData, Indicator, IndicatorData, DataCache


class SymbolSerializer(serializers.ModelSerializer):
    """Serializer for Symbol model"""
    
    class Meta:
        model = Symbol
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class DataRequestSerializer(serializers.ModelSerializer):
    """Serializer for DataRequest model"""
    symbol_name = serializers.CharField(source='symbol.symbol', read_only=True)
    
    class Meta:
        model = DataRequest
        fields = '__all__'
        read_only_fields = ('request_id', 'created_at', 'completed_at', 'requested_by')
    
    def create(self, validated_data):
        # Generate unique request ID
        import uuid
        validated_data['request_id'] = f"req_{uuid.uuid4().hex[:8]}"
        return super().create(validated_data)


class MarketDataSerializer(serializers.ModelSerializer):
    """Serializer for MarketData model"""
    symbol_name = serializers.CharField(source='symbol.symbol', read_only=True)
    
    class Meta:
        model = MarketData
        fields = '__all__'
        read_only_fields = ('created_at',)


class IndicatorSerializer(serializers.ModelSerializer):
    """Serializer for Indicator model"""
    
    class Meta:
        model = Indicator
        fields = '__all__'
        read_only_fields = ('created_at',)


class IndicatorDataSerializer(serializers.ModelSerializer):
    """Serializer for IndicatorData model"""
    symbol_name = serializers.CharField(source='symbol.symbol', read_only=True)
    indicator_name = serializers.CharField(source='indicator.name', read_only=True)
    
    class Meta:
        model = IndicatorData
        fields = '__all__'
        read_only_fields = ('created_at',)


class DataCacheSerializer(serializers.ModelSerializer):
    """Serializer for DataCache model"""
    symbol_name = serializers.CharField(source='symbol.symbol', read_only=True)
    
    class Meta:
        model = DataCache
        fields = '__all__'
        read_only_fields = ('created_at', 'accessed_at', 'access_count')


# Custom serializers for specific API endpoints

class DataFetchRequestSerializer(serializers.Serializer):
    """Serializer for data fetch requests"""
    symbol = serializers.CharField(max_length=20)
    period = serializers.ChoiceField(choices=DataRequest.PERIOD_CHOICES, default='1y')
    interval = serializers.ChoiceField(choices=DataRequest.INTERVAL_CHOICES, default='1d')
    indicators = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        default=list,
        help_text="List of indicators to calculate"
    )
    
    def validate_symbol(self, value):
        """Validate symbol format"""
        if not value.isalnum():
            raise serializers.ValidationError("Symbol must be alphanumeric")
        return value.upper()


class IndicatorCalculationRequestSerializer(serializers.Serializer):
    """Serializer for indicator calculation requests"""
    symbol = serializers.CharField(max_length=20)
    indicator = serializers.CharField(max_length=100)
    parameters = serializers.JSONField(default=dict)
    period = serializers.ChoiceField(choices=DataRequest.PERIOD_CHOICES, default='1y')
    interval = serializers.ChoiceField(choices=DataRequest.INTERVAL_CHOICES, default='1d')
    
    def validate_symbol(self, value):
        return value.upper()


class MarketDataBulkSerializer(serializers.Serializer):
    """Serializer for bulk market data operations"""
    symbols = serializers.ListField(
        child=serializers.CharField(max_length=20),
        min_length=1,
        max_length=50
    )
    period = serializers.ChoiceField(choices=DataRequest.PERIOD_CHOICES, default='1y')
    interval = serializers.ChoiceField(choices=DataRequest.INTERVAL_CHOICES, default='1d')
    
    def validate_symbols(self, value):
        """Validate and normalize symbols"""
        return [symbol.upper() for symbol in value if symbol.isalnum()]