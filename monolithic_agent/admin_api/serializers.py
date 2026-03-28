from django.contrib.auth.models import User
from rest_framework import serializers

from auth_api.models import UserProfile, ChatSession
from strategy_api.models import Strategy, StrategyChat
from backtest_api.models import BacktestRun, BacktestAlert
from data_api.models import Symbol, DataRequest, DataCache
from trading_sessions_api.models import BrokerCredential, LiveTradingSession


# ── Users ──────────────────────────────────────────────────────────────────────

class AdminUserSerializer(serializers.ModelSerializer):
    groups = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'is_active', 'is_staff', 'date_joined', 'last_login', 'groups', 'profile']

    def get_groups(self, obj):
        return list(obj.groups.values_list('name', flat=True))

    def get_profile(self, obj):
        try:
            p = obj.profile
            return {
                'risk_tolerance': p.default_risk_tolerance,
                'preferred_timeframe': p.default_timeframe,
                'preferred_symbols': p.preferred_symbols,
                'subscription_plan': p.subscription_plan,
                'subscription_updated_at': p.subscription_updated_at,
            }
        except UserProfile.DoesNotExist:
            return None


# ── Live Sessions ──────────────────────────────────────────────────────────────

class AdminLiveSessionSerializer(serializers.ModelSerializer):
    strategy_name = serializers.CharField(source='strategy.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = LiveTradingSession
        # mt5_password_encrypted is intentionally excluded
        fields = [
            'id', 'strategy', 'strategy_name', 'created_by', 'created_by_username',
            'status', 'dry_run', 'symbols', 'timeframe', 'risk_pct',
            'exit_mode', 'mt5_login', 'mt5_server',
            'started_at', 'stopped_at', 'pid', 'created_at',
        ]


# ── Broker Credentials ─────────────────────────────────────────────────────────

class AdminBrokerCredentialSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = BrokerCredential
        # mt5_password_encrypted is intentionally excluded
        fields = ['id', 'user', 'username', 'label', 'mt5_login', 'mt5_server', 'is_default', 'created_at']


# ── Strategies ─────────────────────────────────────────────────────────────────

class AdminStrategySerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    latest_performance = serializers.SerializerMethodField()

    class Meta:
        model = Strategy
        fields = [
            'id', 'name', 'version', 'status', 'risk_level', 'timeframe',
            'created_by', 'created_by_username', 'created_at', 'updated_at',
            'latest_performance',
        ]

    def get_latest_performance(self, obj):
        try:
            lb = obj.latest_backtest
            return {
                'total_return_pct': lb.total_return_pct,
                'win_rate': lb.win_rate,
                'sharpe_ratio': lb.sharpe_ratio,
                'total_trades': lb.total_trades,
            }
        except Exception:
            return None


# ── Backtests ──────────────────────────────────────────────────────────────────

class AdminBacktestRunSerializer(serializers.ModelSerializer):
    strategy_name = serializers.CharField(source='strategy.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = BacktestRun
        fields = [
            'id', 'run_id', 'strategy', 'strategy_name', 'status', 'progress',
            'total_return', 'sharpe_ratio', 'max_drawdown', 'total_trades', 'win_rate',
            'created_by', 'created_by_username', 'created_at', 'started_at', 'completed_at',
            'error_message',
        ]


# ── Market Data ────────────────────────────────────────────────────────────────

class AdminSymbolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Symbol
        fields = ['id', 'symbol', 'name', 'exchange', 'sector', 'is_active', 'created_at']


class AdminDataRequestSerializer(serializers.ModelSerializer):
    symbol_name = serializers.CharField(source='symbol.symbol', read_only=True)
    requested_by_username = serializers.CharField(source='requested_by.username', read_only=True)

    class Meta:
        model = DataRequest
        fields = [
            'id', 'request_id', 'symbol', 'symbol_name', 'period', 'interval',
            'status', 'requested_by', 'requested_by_username', 'created_at', 'completed_at', 'error_message',
        ]


class AdminDataCacheSerializer(serializers.ModelSerializer):
    symbol_name = serializers.CharField(source='symbol.symbol', read_only=True)

    class Meta:
        model = DataCache
        fields = ['id', 'cache_key', 'symbol', 'symbol_name', 'data_type', 'access_count', 'expires_at', 'created_at']


# ── AI Chats ───────────────────────────────────────────────────────────────────

class AdminChatSessionSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = ['id', 'session_id', 'user', 'username', 'title', 'is_active',
                  'message_count', 'created_at', 'updated_at']

    def get_message_count(self, obj):
        return len(obj.messages) if isinstance(obj.messages, list) else 0


class AdminStrategyChatSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    strategy_name = serializers.CharField(source='strategy.name', read_only=True)

    class Meta:
        model = StrategyChat
        fields = ['id', 'session_id', 'user', 'username', 'strategy', 'strategy_name',
                  'is_active', 'message_count', 'model_name', 'created_at', 'updated_at']


# ── Alerts ─────────────────────────────────────────────────────────────────────

class AdminBacktestAlertSerializer(serializers.ModelSerializer):
    run_id = serializers.CharField(source='run.run_id', read_only=True)

    class Meta:
        model = BacktestAlert
        fields = ['id', 'run', 'run_id', 'alert_type', 'title', 'message', 'symbol', 'timestamp', 'created_at']
