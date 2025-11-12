"""
Production API URLs
===================

URL configuration for production-hardened endpoints
"""

from django.urls import path
from rest_framework.routers import DefaultRouter
from .production_views import ProductionStrategyViewSet

# Create router for viewset
router = DefaultRouter()
router.register(r'production', ProductionStrategyViewSet, basename='production-strategy')

# URL patterns
urlpatterns = router.urls

# Additional patterns can be added here if needed
