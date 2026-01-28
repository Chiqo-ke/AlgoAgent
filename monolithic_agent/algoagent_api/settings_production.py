"""
Production settings for AlgoAgent Backend
Inherits from base settings and adds production-specific configuration
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from .settings import *

# Load environment variables from /etc/algoagent/.env (production)
# This takes priority over any .env files in the project directory
env_file = '/etc/algoagent/.env'
if os.path.exists(env_file):
    load_dotenv(env_file, override=True)
    print(f"[Settings] Loaded .env from {env_file}")
else:
    # Fallback: search in project directory (for development/testing)
    env_search_paths = [
        BASE_DIR / '.env',
        BASE_DIR.parent / '.env',
    ]
    for path in env_search_paths:
        if path.exists():
            load_dotenv(path, override=True)
            print(f"[Settings] Loaded .env from {path}")
            break
    else:
        print("[Settings] WARNING: No .env file found!")

# Security Settings
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 'yes')
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

if not SECRET_KEY:
    raise ValueError("DJANGO_SECRET_KEY environment variable is required in production")

# Allowed Hosts - Set from environment variable
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',')
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS if host.strip()]
if not ALLOWED_HOSTS or ALLOWED_HOSTS == ['']:
    raise ValueError("DJANGO_ALLOWED_HOSTS environment variable is required")

# HTTPS/SSL Settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Proxy Settings (nginx reverse proxy)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# Database - PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'algoagent'),
        'USER': os.environ.get('DB_USER', 'algoagent'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,  # Connection pooling
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}

# Redis Configuration for Django Channels
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [os.environ.get('REDIS_URL', 'redis://localhost:6379/0')],
            "capacity": 1500,
            "expiry": 10,
        },
    },
}

# Cache Configuration - Redis
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'algoagent',
        'TIMEOUT': 300,
    }
}

# Static Files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# Media Files
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# CORS Settings - Strict production whitelist
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in CORS_ALLOWED_ORIGINS if origin.strip()]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# WebSocket Origin Validation
ALLOWED_WEBSOCKET_ORIGINS = os.environ.get('ALLOWED_WEBSOCKET_ORIGINS', '').split(',')
ALLOWED_WEBSOCKET_ORIGINS = [origin.strip() for origin in ALLOWED_WEBSOCKET_ORIGINS if origin.strip()]

# CSRF Settings
CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in CSRF_TRUSTED_ORIGINS if origin.strip()]
CSRF_COOKIE_HTTPONLY = False  # Allow JS access for CSRF token
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_AGE = 31449600  # 1 year

# Session Settings
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 1209600  # 2 weeks

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/algoagent/django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/algoagent/django_error.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'error_file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'algoagent_api': {
            'handlers': ['file', 'error_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Email Configuration (Optional - for error reporting)
if os.environ.get('EMAIL_HOST'):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ.get('EMAIL_HOST')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
    EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@algoai.biz')
    SERVER_EMAIL = os.environ.get('SERVER_EMAIL', 'server@algoai.biz')
    
    # Send error emails to admins
    ADMINS = [('Admin', os.environ.get('ADMIN_EMAIL', 'admin@algoai.biz'))]
    MANAGERS = ADMINS

# Google OAuth Settings - From environment
if os.environ.get('GOOGLE_CLIENT_ID'):
    SOCIALACCOUNT_PROVIDERS = {
        'google': {
            'APP': {
                'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
                'secret': os.environ.get('GOOGLE_CLIENT_SECRET'),
                'key': ''
            },
            'SCOPE': [
                'profile',
                'email',
            ],
            'AUTH_PARAMS': {
                'access_type': 'online',
            }
        }
    }

# Performance Optimizations
CONN_MAX_AGE = 600  # Database connection pooling

# File Upload Settings
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB

# Security: Additional Headers
SECURE_REFERRER_POLICY = 'same-origin'

print("✓ Production settings loaded successfully")
print(f"  - Debug: {DEBUG}")
print(f"  - Allowed Hosts: {ALLOWED_HOSTS}")
print(f"  - Database: PostgreSQL ({DATABASES['default']['NAME']})")
print(f"  - Redis: {CACHES['default']['LOCATION']}")
