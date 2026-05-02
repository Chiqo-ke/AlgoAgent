from django.contrib import admin
from .models import Symbol, DataRequest, MarketData, Indicator, IndicatorData, DataCache


@admin.register(Symbol)
class SymbolAdmin(admin.ModelAdmin):
    list_display = ['id', 'symbol', 'name', 'exchange', 'sector', 'is_active', 'created_at']
    list_filter = ['is_active', 'exchange', 'sector']
    search_fields = ['symbol', 'name', 'exchange']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(DataRequest)
class DataRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'request_id', 'symbol', 'period', 'interval', 'status', 'requested_by', 'created_at']
    list_filter = ['status', 'period', 'interval']
    search_fields = ['request_id', 'symbol__symbol', 'requested_by__username']
    readonly_fields = ['created_at', 'completed_at']


@admin.register(MarketData)
class MarketDataAdmin(admin.ModelAdmin):
    list_display = ['id', 'symbol', 'timestamp', 'open_price', 'high_price', 'low_price', 'close_price', 'volume', 'interval']
    list_filter = ['interval', 'symbol']
    search_fields = ['symbol__symbol']
    readonly_fields = ['created_at']


@admin.register(Indicator)
class IndicatorAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'display_name', 'category', 'is_active', 'created_at']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'display_name', 'description']
    readonly_fields = ['created_at']


@admin.register(IndicatorData)
class IndicatorDataAdmin(admin.ModelAdmin):
    list_display = ['id', 'symbol', 'indicator', 'timestamp', 'interval', 'created_at']
    list_filter = ['interval', 'indicator']
    search_fields = ['symbol__symbol', 'indicator__name']
    readonly_fields = ['created_at']


@admin.register(DataCache)
class DataCacheAdmin(admin.ModelAdmin):
    list_display = ['id', 'cache_key', 'symbol', 'data_type', 'access_count', 'expires_at', 'created_at']
    list_filter = ['data_type']
    search_fields = ['cache_key', 'symbol__symbol']
    readonly_fields = ['created_at', 'accessed_at']
