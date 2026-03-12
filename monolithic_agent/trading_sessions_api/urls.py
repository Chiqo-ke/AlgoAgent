from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LiveTradingSessionViewSet, BrokerCredentialViewSet

router = DefaultRouter()
router.register(r'sessions', LiveTradingSessionViewSet, basename='trading-session')
router.register(r'credentials', BrokerCredentialViewSet, basename='broker-credential')

urlpatterns = [
    path('', include(router.urls)),
]
