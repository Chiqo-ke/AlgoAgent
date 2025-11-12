"""
Backtest API Serializers for AlgoAgent
======================================

Django REST Framework serializers for the backtest API.
"""

from rest_framework import serializers
from .models import BacktestConfig, BacktestRun, BacktestResult, Trade, BacktestAlert


class BacktestConfigSerializer(serializers.ModelSerializer):
    """Serializer for BacktestConfig model"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = BacktestConfig
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'created_by')


class BacktestRunSerializer(serializers.ModelSerializer):
    """Serializer for BacktestRun model"""
    config_name = serializers.CharField(source='config.name', read_only=True)
    strategy_name = serializers.CharField(source='strategy.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = BacktestRun
        fields = '__all__'
        read_only_fields = ('run_id', 'created_at', 'started_at', 'completed_at', 'created_by')


class BacktestResultSerializer(serializers.ModelSerializer):
    """Serializer for BacktestResult model"""
    run_id = serializers.CharField(source='run.run_id', read_only=True)
    strategy_name = serializers.CharField(source='run.strategy.name', read_only=True)
    
    class Meta:
        model = BacktestResult
        fields = '__all__'
        read_only_fields = ('created_at',)


class TradeSerializer(serializers.ModelSerializer):
    """Serializer for Trade model"""
    run_id = serializers.CharField(source='run.run_id', read_only=True)
    strategy_name = serializers.CharField(source='run.strategy.name', read_only=True)
    
    class Meta:
        model = Trade
        fields = '__all__'
        read_only_fields = ('created_at',)


class BacktestAlertSerializer(serializers.ModelSerializer):
    """Serializer for BacktestAlert model"""
    run_id = serializers.CharField(source='run.run_id', read_only=True)
    
    class Meta:
        model = BacktestAlert
        fields = '__all__'
        read_only_fields = ('created_at',)


# Custom serializers for specific API endpoints

class BacktestRunRequestSerializer(serializers.Serializer):
    """Serializer for backtest run requests"""
    strategy_id = serializers.IntegerField()
    config_id = serializers.IntegerField(required=False)
    symbols = serializers.ListField(
        child=serializers.CharField(max_length=20),
        min_length=1,
        max_length=50
    )
    
    # Optional config overrides
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    initial_capital = serializers.DecimalField(max_digits=20, decimal_places=2, required=False)
    commission = serializers.DecimalField(max_digits=10, decimal_places=6, required=False)
    slippage = serializers.DecimalField(max_digits=10, decimal_places=6, required=False)
    
    def validate_symbols(self, value):
        """Validate and normalize symbols"""
        return [symbol.upper() for symbol in value if symbol.isalnum()]


class BacktestConfigCreateSerializer(serializers.Serializer):
    """Serializer for creating backtest configurations"""
    name = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, default='')
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    initial_capital = serializers.DecimalField(max_digits=20, decimal_places=2)
    commission = serializers.DecimalField(max_digits=10, decimal_places=6, required=False, default=0.001)
    slippage = serializers.DecimalField(max_digits=10, decimal_places=6, required=False, default=0.0005)
    max_position_size = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, default=1.0)
    stop_loss = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    take_profit = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    data_source = serializers.CharField(max_length=50, required=False, default='yfinance')
    timeframe = serializers.CharField(max_length=10, required=False, default='1d')
    benchmark_symbol = serializers.CharField(max_length=20, required=False, default='SPY')
    is_template = serializers.BooleanField(required=False, default=False)
    
    def validate(self, data):
        """Validate date range"""
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError("End date must be after start date")
        return data


class BacktestSearchSerializer(serializers.Serializer):
    """Serializer for backtest search requests"""
    strategy_id = serializers.IntegerField(required=False)
    status = serializers.CharField(required=False)
    start_date_from = serializers.DateField(required=False)
    start_date_to = serializers.DateField(required=False)
    symbols = serializers.ListField(
        child=serializers.CharField(max_length=20),
        required=False,
        default=list
    )
    created_by = serializers.CharField(required=False)


class BacktestRunListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for backtest run lists"""
    config_name = serializers.CharField(source='config.name', read_only=True)
    strategy_name = serializers.CharField(source='strategy.name', read_only=True)
    strategy_version = serializers.CharField(source='strategy.version', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    result_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = BacktestRun
        fields = [
            'id', 'run_id', 'status', 'progress', 'symbols',
            'config_name', 'strategy_name', 'strategy_version',
            'created_by_username', 'created_at', 'started_at', 'completed_at',
            'execution_time', 'total_return', 'sharpe_ratio', 'max_drawdown',
            'total_trades', 'win_rate', 'result_summary'
        ]
    
    def get_result_summary(self, obj):
        """Get summary of backtest results"""
        try:
            result = obj.result
            return {
                'final_value': result.final_portfolio_value,
                'total_return': result.total_return_pct,
                'sharpe_ratio': result.sharpe_ratio,
                'max_drawdown': result.max_drawdown_pct,
                'total_trades': result.total_trades,
                'win_rate': result.win_rate_pct
            }
        except BacktestResult.DoesNotExist:
            return None


class TradeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for trade lists"""
    
    class Meta:
        model = Trade
        fields = [
            'id', 'symbol', 'trade_type', 'status',
            'entry_date', 'entry_price', 'exit_date', 'exit_price',
            'quantity', 'pnl', 'pnl_pct', 'holding_period'
        ]


class BacktestQuickRunSerializer(serializers.Serializer):
    """Serializer for quick backtest runs with minimal configuration"""
    strategy_code = serializers.CharField()
    symbol = serializers.CharField(max_length=20)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    initial_capital = serializers.DecimalField(max_digits=20, decimal_places=2, required=False, default=10000)
    
    def validate_symbol(self, value):
        return value.upper()
    
    def validate(self, data):
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError("End date must be after start date")
        return data