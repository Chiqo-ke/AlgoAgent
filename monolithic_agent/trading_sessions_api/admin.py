from django.contrib import admin
from .models import LiveTradingSession, BrokerCredential


@admin.register(BrokerCredential)
class BrokerCredentialAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'label', 'mt5_server', 'mt5_login', 'is_default', 'created_at']
    list_filter = ['is_default', 'mt5_server']
    exclude = ['mt5_password_encrypted']  # Never expose encrypted password in admin


@admin.register(LiveTradingSession)
class LiveTradingSessionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'strategy', 'created_by', 'status', 'dry_run',
        'symbols', 'timeframe', 'started_at', 'stopped_at'
    ]
    list_filter = ['status', 'dry_run', 'timeframe']
    readonly_fields = ['pid', 'temp_file_path', 'kill_switch_path', 'started_at', 'stopped_at']
    exclude = ['mt5_password_encrypted']  # Never expose encrypted password in admin
