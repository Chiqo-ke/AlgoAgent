"""
Strategy API URLs for AlgoAgent
===============================

URL patterns for the strategy API endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from strategies import views_validation

# Create router and register viewsets
router = DefaultRouter()
router.register(r'templates', views.StrategyTemplateViewSet)
router.register(r'strategies', views.StrategyViewSet)
router.register(r'validations', views.StrategyValidationViewSet)
router.register(r'performance', views.StrategyPerformanceViewSet)
router.register(r'comments', views.StrategyCommentViewSet)
router.register(r'tags', views.StrategyTagViewSet)
router.register(r'chat', views.StrategyChatViewSet, basename='chat')
router.register(r'api', views.StrategyAPIViewSet, basename='strategy-api')
router.register(r'bot-performance', views.BotPerformanceViewSet, basename='bot-performance')
router.register(r'backtest-results', views.LatestBacktestResultViewSet, basename='backtest-results')

app_name = 'strategy_api'

urlpatterns = [
    path('', include(router.urls)),
    # Strategy validation endpoints
    path('validate/', views_validation.validate_strategy, name='validate-strategy'),
    path('validate-file/', views_validation.validate_strategy_file, name='validate-strategy-file'),
]