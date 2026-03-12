import os, sys
os.chdir(r'C:\Users\nyaga\Documents\AlgoAgent\monolithic_agent')
sys.path.insert(0, '.')
os.environ['DJANGO_SETTINGS_MODULE'] = 'algoagent_api.settings'
import django
django.setup()

from django.core.management import call_command
call_command('makemigrations', 'trading_sessions_api', '--skip-checks')
