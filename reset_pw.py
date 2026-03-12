import signal
signal.signal(signal.SIGINT, signal.SIG_IGN)  # Ignore Ctrl+C / stray interrupts

import os, sys
os.chdir(r'C:\Users\nyaga\Documents\AlgoAgent\monolithic_agent')
sys.path.insert(0, '.')
os.environ['DJANGO_SETTINGS_MODULE'] = 'algoagent_api.settings'
import django
django.setup()
from django.contrib.auth.models import User

NEW_PASSWORD = 'LiveTest@2026'

try:
    u = User.objects.get(username='algotrader')
    print(f'Found user: {u.username} | email: {u.email} | active: {u.is_active}')
except User.DoesNotExist:
    print('ERROR: algotrader not found. All users:')
    for x in User.objects.all():
        print(f'  id={x.id} username={x.username} active={x.is_active}')
    sys.exit(1)

u.set_password(NEW_PASSWORD)
u.save()
print(f'Password reset for algotrader -> {NEW_PASSWORD}')
print(f'Verify: {u.check_password(NEW_PASSWORD)}')
