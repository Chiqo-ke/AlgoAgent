"""
Authentication API URLs for AlgoAgent
======================================

URL routing for authentication, user profiles, and AI chat.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    UserRegistrationView, UserLoginView, logout_view, current_user_view,
    UserProfileViewSet, AIContextViewSet, ChatSessionViewSet,
    ai_chat_view, health_check
)

# Create router for viewsets
router = DefaultRouter()
router.register(r'profiles', UserProfileViewSet, basename='profile')
router.register(r'ai-contexts', AIContextViewSet, basename='ai-context')
router.register(r'chat-sessions', ChatSessionViewSet, basename='chat-session')

urlpatterns = [
    # Authentication endpoints
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('user/me/', current_user_view, name='current-user'),
    
    # AI Chat endpoint
    path('chat/', ai_chat_view, name='ai-chat'),
    
    # Health check
    path('health/', health_check, name='health'),
    
    # ViewSet routes
    path('', include(router.urls)),
]
