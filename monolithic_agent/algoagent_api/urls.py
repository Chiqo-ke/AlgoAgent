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
from auth_api.views import frontend_error_log
from algoagent_api.job_views import job_status


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
        },
        'production': {
            'strategies': '/api/production/strategies/',
            'backtests': '/api/production/backtests/',
            'health': {
                'strategies': '/api/production/strategies/health/',
                'backtests': '/api/production/backtests/health/',
            }
        }
    })


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api_root, name='api-root'),
    path('api/auth/', include('auth_api.urls')),
    path('api/data/', include('data_api.urls')),
    path('api/strategies/', include('strategy_api.urls')),
    path('api/backtests/', include('backtest_api.urls')),
    path('api/workflows/', include('workflows_api.urls')),
    # Frontend error logging (called by logger.ts sendErrorToBackend)
    # Both trailing-slash and no-trailing-slash variants are registered because
    # Django's APPEND_SLASH redirect does not follow POST requests, causing a 404
    # when the frontend sends POST /api/logs/frontend-errors (no trailing slash).
    path('api/logs/frontend-errors/', frontend_error_log, name='frontend-error-log'),
    path('api/logs/frontend-errors', frontend_error_log, name='frontend-error-log-noslash'),
    # Production-hardened endpoints with sandbox execution
    path('api/production/', include('algoagent_api.production_api_urls')),
    # Async job status polling (works for any Celery task)
    path('api/jobs/<str:task_id>/', job_status, name='job-status'),
]
