"""
Data API URLs for AlgoAgent
===========================

URL patterns for the data API endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and register viewsets
router = DefaultRouter()
router.register(r'symbols', views.SymbolViewSet)
router.register(r'data-requests', views.DataRequestViewSet)
router.register(r'market-data', views.MarketDataViewSet)
router.register(r'indicators', views.IndicatorViewSet)
router.register(r'indicator-data', views.IndicatorDataViewSet)
router.register(r'api', views.DataAPIViewSet, basename='data-api')

app_name = 'data_api'

urlpatterns = [
    path('', include(router.urls)),
]