from django.urls import path
from .views import (
    AdminStatsView,
    AdminUserListView,
    AdminUserDetailView,
    AdminSubscriptionListView,
    AdminSubscriptionUpdateView,
    AdminLiveSessionListView,
    AdminStrategyListView,
    AdminBacktestListView,
    AdminMarketDataView,
    AdminChatListView,
    AdminBrokerCredentialListView,
    AdminAlertListView,
)

urlpatterns = [
    path('stats/', AdminStatsView.as_view(), name='admin-stats'),
    path('users/', AdminUserListView.as_view(), name='admin-users'),
    path('users/<int:user_id>/', AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('subscriptions/', AdminSubscriptionListView.as_view(), name='admin-subscriptions'),
    path('subscriptions/<int:user_id>/', AdminSubscriptionUpdateView.as_view(), name='admin-subscription-update'),
    path('live-sessions/', AdminLiveSessionListView.as_view(), name='admin-live-sessions'),
    path('strategies/', AdminStrategyListView.as_view(), name='admin-strategies'),
    path('backtests/', AdminBacktestListView.as_view(), name='admin-backtests'),
    path('market-data/', AdminMarketDataView.as_view(), name='admin-market-data'),
    path('chats/', AdminChatListView.as_view(), name='admin-chats'),
    path('broker-credentials/', AdminBrokerCredentialListView.as_view(), name='admin-broker-credentials'),
    path('alerts/', AdminAlertListView.as_view(), name='admin-alerts'),
]
