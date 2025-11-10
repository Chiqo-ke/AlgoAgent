"""
Production Backtest API URLs
=============================

URL configuration for production-hardened backtest endpoints
"""

from django.urls import path
from rest_framework.routers import DefaultRouter
from .production_views import ProductionBacktestViewSet

# Create router for viewset
router = DefaultRouter()
router.register(r'production', ProductionBacktestViewSet, basename='production-backtest')

# URL patterns
urlpatterns = router.urls
