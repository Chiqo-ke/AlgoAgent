"""
Serializers for Live Trading Sessions
"""
from rest_framework import serializers
from .models import LiveTradingSession, BrokerCredential, SessionStatus, ExitMode


# ---------------------------------------------------------------------------
# BrokerCredential serializers
# ---------------------------------------------------------------------------

class BrokerCredentialWriteSerializer(serializers.Serializer):
    """Create / update a saved broker credential."""
    label = serializers.CharField(max_length=100)
    mt5_login = serializers.IntegerField()
    mt5_password = serializers.CharField(write_only=True)
    mt5_server = serializers.CharField(max_length=100)
    mt5_terminal_path = serializers.CharField(max_length=500, required=False, allow_blank=True, default='')
    is_default = serializers.BooleanField(required=False, default=False)


class BrokerCredentialSerializer(serializers.ModelSerializer):
    """Read serializer – never exposes the encrypted password."""
    class Meta:
        model = BrokerCredential
        exclude = ['mt5_password_encrypted']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


# ---------------------------------------------------------------------------
# Session serializers
# ---------------------------------------------------------------------------

class LiveTradingSessionCreateSerializer(serializers.Serializer):
    """
    Accepts the request payload to start a new live session.

    Credentials can be supplied in two ways (mutually exclusive):
      - credential_id: ID of a saved BrokerCredential (preferred)
      - mt5_login + mt5_password + mt5_server: inline credentials
    """
    strategy_id = serializers.IntegerField()
    symbols = serializers.ListField(child=serializers.CharField(), min_length=1)
    timeframe = serializers.CharField(max_length=10)
    dry_run = serializers.BooleanField(default=True)
    risk_pct = serializers.DecimalField(max_digits=5, decimal_places=2, default=2.0)
    exit_mode = serializers.ChoiceField(
        choices=ExitMode.values,
        required=False,
        default=ExitMode.PERCENTAGE,
        help_text='Explicit exit mode: bot, percentage, or fixed_pips.'
    )
    magic_number = serializers.IntegerField(
        required=False,
        allow_null=True,
        default=None,
        help_text='Unique MT5 magic number. Auto-generated if omitted.'
    )
    sl_pips = serializers.FloatField(
        required=False, allow_null=True, default=None,
        help_text='Fixed stop-loss in pips from entry. Overrides the strategy default when the bot has no SL.'
    )
    tp_pips = serializers.FloatField(
        required=False, allow_null=True, default=None,
        help_text='Fixed take-profit in pips from entry. Overrides the strategy default when the bot has no TP.'
    )
    data_bars = serializers.IntegerField(
        required=False, allow_null=True, default=5000, min_value=100, max_value=5000,
        help_text='Historical bars for indicator warm-up (100–5000). Defaults to 5000.'
    )
    max_lots = serializers.FloatField(
        required=False, allow_null=True, default=1.0,
        help_text='Max position size in lots. Caps risk-based sizing. Defaults to 1.0.'
    )
    lot_size = serializers.FloatField(
        required=False, allow_null=True, default=None,
        help_text='Fixed lot size per trade. Overrides risk-based sizing when set.'
    )
    # Option A – reference a saved credential
    credential_id = serializers.IntegerField(required=False, allow_null=True)
    # Option B – inline MT5 credentials
    mt5_login = serializers.IntegerField(required=False, allow_null=True)
    mt5_password = serializers.CharField(write_only=True, required=False, allow_blank=True, default='')
    mt5_server = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')
    mt5_terminal_path = serializers.CharField(max_length=500, required=False, allow_blank=True, default='')

    def validate(self, data):
        # Backward compatibility: infer mode for old clients that do not send exit_mode.
        if 'exit_mode' not in self.initial_data:
            if data.get('sl_pips') is not None or data.get('tp_pips') is not None:
                data['exit_mode'] = ExitMode.FIXED_PIPS
            else:
                data['exit_mode'] = ExitMode.PERCENTAGE

        has_credential_id = bool(data.get('credential_id'))
        has_inline = bool(data.get('mt5_login')) and bool(data.get('mt5_password')) and bool(data.get('mt5_server'))
        if not has_credential_id and not has_inline:
            raise serializers.ValidationError(
                'Provide either "credential_id" (saved broker credential) '
                'or "mt5_login", "mt5_password", and "mt5_server" inline.'
            )

        exit_mode = data.get('exit_mode', ExitMode.PERCENTAGE)
        sl_pips = data.get('sl_pips')
        tp_pips = data.get('tp_pips')

        if exit_mode in (ExitMode.BOT, ExitMode.PERCENTAGE):
            if sl_pips is not None or tp_pips is not None:
                raise serializers.ValidationError(
                    f'"{exit_mode}" mode does not allow session-level sl_pips/tp_pips. '
                    'Use fixed_pips mode to provide SL/TP pips.'
                )

        if exit_mode == ExitMode.FIXED_PIPS:
            if sl_pips is None and tp_pips is None:
                raise serializers.ValidationError(
                    'fixed_pips mode requires at least one of sl_pips or tp_pips.'
                )
            if sl_pips is not None and sl_pips <= 0:
                raise serializers.ValidationError('sl_pips must be greater than 0 when provided.')
            if tp_pips is not None and tp_pips <= 0:
                raise serializers.ValidationError('tp_pips must be greater than 0 when provided.')

        # Magic number: auto-generate or validate uniqueness
        from .models import LiveTradingSession
        magic = data.get('magic_number')
        if not magic:
            data['magic_number'] = LiveTradingSession.generate_unique_magic()
        else:
            if LiveTradingSession.objects.filter(magic_number=magic).exists():
                raise serializers.ValidationError({
                    'magic_number': (
                        f'Magic number {magic} is already in use by another session. '
                        'Omit the field to have one auto-generated, or choose a different value.'
                    )
                })

        return data


class LiveTradingSessionSerializer(serializers.ModelSerializer):
    """Read serializer – never exposes the encrypted password."""
    strategy_name = serializers.CharField(source='strategy.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = LiveTradingSession
        exclude = ['mt5_password_encrypted']
        read_only_fields = [
            'id', 'status', 'pid', 'temp_file_path', 'kill_switch_path',
            'created_by', 'created_at', 'started_at', 'stopped_at', 'error_message'
        ]
