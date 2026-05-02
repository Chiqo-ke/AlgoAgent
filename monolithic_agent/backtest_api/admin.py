from django.contrib import admin
from .models import BacktestConfig, BacktestRun, BacktestResult, Trade, BacktestAlert


@admin.register(BacktestConfig)
class BacktestConfigAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'start_date', 'end_date', 'initial_capital', 'data_source', 'timeframe', 'is_template', 'created_by', 'created_at']
    list_filter = ['is_template', 'data_source', 'timeframe']
    search_fields = ['name', 'description', 'created_by__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(BacktestRun)
class BacktestRunAdmin(admin.ModelAdmin):
    list_display = ['id', 'run_id', 'strategy', 'status', 'progress', 'total_return', 'sharpe_ratio', 'total_trades', 'created_by', 'created_at']
    list_filter = ['status']
    search_fields = ['run_id', 'strategy__name', 'created_by__username']
    readonly_fields = ['created_at', 'started_at', 'completed_at']


@admin.register(BacktestResult)
class BacktestResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'run', 'final_portfolio_value', 'total_return_pct', 'sharpe_ratio', 'max_drawdown_pct', 'total_trades', 'win_rate_pct', 'created_at']
    search_fields = ['run__run_id']
    readonly_fields = ['created_at']


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ['id', 'run', 'symbol', 'trade_type', 'status', 'entry_date', 'exit_date', 'pnl', 'pnl_pct']
    list_filter = ['trade_type', 'status', 'symbol']
    search_fields = ['symbol', 'run__run_id', 'signal_name']
    readonly_fields = ['created_at']


@admin.register(BacktestAlert)
class BacktestAlertAdmin(admin.ModelAdmin):
    list_display = ['id', 'run', 'alert_type', 'title', 'symbol', 'timestamp']
    list_filter = ['alert_type']
    search_fields = ['title', 'message', 'symbol', 'run__run_id']
    readonly_fields = ['created_at']
