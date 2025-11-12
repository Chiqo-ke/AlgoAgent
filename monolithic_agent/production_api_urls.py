"""
Production API URL Configuration
================================

New production-hardened endpoints:

Strategy API:
- POST /api/production/strategies/validate-schema/
- POST /api/production/strategies/validate-code/
- POST /api/production/strategies/sandbox-test/
- GET  /api/production/strategies/{id}/lifecycle/
- POST /api/production/strategies/{id}/deploy/
- POST /api/production/strategies/{id}/rollback/
- GET  /api/production/strategies/health/

Backtest API:
- POST /api/production/backtests/validate-config/
- POST /api/production/backtests/run-sandbox/
- GET  /api/production/backtests/{id}/status/
- GET  /api/production/backtests/health/
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from strategy_api.production_views import ProductionStrategyViewSet
from backtest_api.production_views import ProductionBacktestViewSet

# Create routers
router = DefaultRouter()
router.register(r'strategies', ProductionStrategyViewSet, basename='production-strategy')
router.register(r'backtests', ProductionBacktestViewSet, basename='production-backtest')

urlpatterns = [
    path('', include(router.urls)),
]
