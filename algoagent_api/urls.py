"""
URL configuration for algoagent_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.utils import timezone


def api_root(request):
    """API root endpoint with navigation links"""
    return JsonResponse({
        'message': 'AlgoAgent API',
        'version': '1.0.0',
        'timestamp': timezone.now(),
        'endpoints': {
            'auth': '/api/auth/',
            'data': '/api/data/',
            'strategies': '/api/strategies/',
            'backtests': '/api/backtests/',
            'admin': '/admin/',
            'api_browser': '/api/data/',  # For browsable API
        },
        'authentication': {
            'register': '/api/auth/register/',
            'login': '/api/auth/login/',
            'token_refresh': '/api/auth/token/refresh/',
            'logout': '/api/auth/logout/',
            'current_user': '/api/auth/user/me/',
        },
        'ai_chat': {
            'chat': '/api/auth/chat/',
            'sessions': '/api/auth/chat-sessions/',
            'contexts': '/api/auth/ai-contexts/',
        },
        'health_checks': {
            'auth_api': '/api/auth/health/',
            'data_api': '/api/data/api/health/',
            'strategy_api': '/api/strategies/api/health/',
            'backtest_api': '/api/backtests/api/health/',
        }
    })


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api_root, name='api-root'),
    path('api/auth/', include('auth_api.urls')),
    path('api/data/', include('data_api.urls')),
    path('api/strategies/', include('strategy_api.urls')),
    path('api/backtests/', include('backtest_api.urls')),
]
