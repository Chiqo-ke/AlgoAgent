import signal
signal.signal(signal.SIGINT, signal.SIG_IGN)
import os, sys
os.chdir(r'C:\Users\nyaga\Documents\AlgoAgent\monolithic_agent')
sys.path.insert(0, '.')
os.environ['DJANGO_SETTINGS_MODULE'] = 'algoagent_api.settings'
import django
django.setup()
import trading_sessions_api.views
print("views.py imported OK")
