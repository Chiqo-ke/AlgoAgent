"""
Backtest API URLs for AlgoAgent
===============================

URL patterns for the backtest API endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and register viewsets
router = DefaultRouter()
router.register(r'configs', views.BacktestConfigViewSet)
router.register(r'runs', views.BacktestRunViewSet)
router.register(r'results', views.BacktestResultViewSet)
router.register(r'trades', views.TradeViewSet)
router.register(r'alerts', views.BacktestAlertViewSet)
router.register(r'api', views.BacktestAPIViewSet, basename='backtest-api')

app_name = 'backtest_api'

urlpatterns = [
    path('', include(router.urls)),
]