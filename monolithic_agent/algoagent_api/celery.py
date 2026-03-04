import os
from celery import Celery

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoagent_api.settings')

app = Celery('algoagent_api')

# Read all Celery config from Django settings (keys prefixed with CELERY_)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in every app listed in INSTALLED_APPS
app.autodiscover_tasks()
