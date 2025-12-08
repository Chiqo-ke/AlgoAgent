"""
Bot Performance API Serializers
================================
"""

from rest_framework import serializers
from .bot_performance import BotPerformance, BotTestRun


class BotPerformanceSerializer(serializers.ModelSerializer):
    """Serializer for BotPerformance model"""
    
    strategy_id = serializers.IntegerField(source='strategy.id', read_only=True)
    strategy_name = serializers.CharField(source='strategy.name', read_only=True)
    verification_badge = serializers.SerializerMethodField()
    
    class Meta:
        model = BotPerformance
        fields = [
            'id',
            'strategy_id',
            'strategy_name',
            'verification_status',
            'is_verified',
            'total_trades',
            'entry_trades',
            'exit_trades',
            'win_rate',
            'total_return',
            'sharpe_ratio',
            'max_drawdown',
            'symbol_tested',
            'timeframe_tested',
            'test_period_start',
            'test_period_end',
            'trades_threshold',
            'verification_notes',
            'created_at',
            'updated_at',
            'last_test_at',
            'verified_at',
            'verification_badge'
        ]
        read_only_fields = [
            'id',
            'strategy_id',
            'strategy_name',
            'verification_status',
            'is_verified',
            'created_at',
            'updated_at',
            'verified_at',
            'verification_badge'
        ]
    
    def get_verification_badge(self, obj):
        """Get verification badge information"""
        return obj.get_verification_badge()


class BotTestRunSerializer(serializers.ModelSerializer):
    """Serializer for BotTestRun model"""
    
    strategy_name = serializers.CharField(source='performance.strategy.name', read_only=True)
    backtest_run_id = serializers.CharField(source='backtest_run.run_id', read_only=True)
    
    class Meta:
        model = BotTestRun
        fields = [
            'id',
            'strategy_name',
            'backtest_run_id',
            'passed',
            'trades_made',
            'execution_errors',
            'tested_at'
        ]
        read_only_fields = fields


class BotVerificationRequestSerializer(serializers.Serializer):
    """Serializer for bot verification requests"""
    
    strategy_id = serializers.IntegerField(required=True)
    symbol = serializers.CharField(required=False, default='AAPL')
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    timeframe = serializers.CharField(required=False, default='1d')
    initial_balance = serializers.DecimalField(
        required=False, 
        default=10000, 
        max_digits=20, 
        decimal_places=2
    )
    commission = serializers.DecimalField(
        required=False,
        default=0.002,
        max_digits=10,
        decimal_places=6
    )


class BulkVerificationSerializer(serializers.Serializer):
    """Serializer for bulk bot verification"""
    
    force_retest = serializers.BooleanField(required=False, default=False)
    strategy_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
