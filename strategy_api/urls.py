"""
Strategy API URLs for AlgoAgent
===============================

URL patterns for the strategy API endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and register viewsets
router = DefaultRouter()
router.register(r'templates', views.StrategyTemplateViewSet)
router.register(r'strategies', views.StrategyViewSet)
router.register(r'validations', views.StrategyValidationViewSet)
router.register(r'performance', views.StrategyPerformanceViewSet)
router.register(r'comments', views.StrategyCommentViewSet)
router.register(r'tags', views.StrategyTagViewSet)
router.register(r'api', views.StrategyAPIViewSet, basename='strategy-api')

app_name = 'strategy_api'

urlpatterns = [
    path('', include(router.urls)),
]