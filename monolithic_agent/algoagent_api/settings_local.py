"""
Local Development Settings for AlgoAgent Backend
=================================================

This file contains settings optimized for local development.
To use these settings, run:
    python manage.py runserver --settings=algoagent_api.settings_local

Or set environment variable:
    $env:DJANGO_SETTINGS_MODULE="algoagent_api.settings_local"
    python manage.py runserver
"""

from .settings import *
import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Allow all local hosts for development
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    'testserver',
    # Add dev tunnel if you use VS Code tunnels
    '*.devtunnels.ms',
]

# Database - Use SQLite for local development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# CORS - Allow all origins for local development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Additional CORS origins for local development
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Disable HTTPS redirects for local development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Use in-memory channel layer for local development (no Redis required)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    },
}

# Cache - Use local memory cache for development (no Redis required)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'algoagent-dev-cache',
    }
}

# Email backend for development - Print emails to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging configuration for development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'debug.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'strategy_api': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'backtest_api': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
import os
logs_dir = BASE_DIR / 'logs'
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Show SQL queries in console (helpful for debugging)
# Uncomment to see all SQL queries
# LOGGING['loggers']['django.db.backends'] = {
#     'handlers': ['console'],
#     'level': 'DEBUG',
# }

# Django Debug Toolbar (optional - uncomment if you want to use it)
# if DEBUG:
#     INSTALLED_APPS += ['debug_toolbar']
#     MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
#     INTERNAL_IPS = ['127.0.0.1', 'localhost']

print("=" * 60)
print("🔧 LOCAL DEVELOPMENT SETTINGS LOADED")
print("=" * 60)
print(f"DEBUG: {DEBUG}")
print(f"DATABASE: SQLite ({DATABASES['default']['NAME']})")
print(f"CORS: Allow all origins")
print(f"CACHE: Local memory")
print(f"CHANNELS: In-memory layer")
print("=" * 60)
