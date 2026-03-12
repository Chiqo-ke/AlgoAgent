import os, sys
os.chdir(r'C:\Users\nyaga\Documents\AlgoAgent\monolithic_agent')
sys.path.insert(0, '.')
os.environ['DJANGO_SETTINGS_MODULE'] = 'algoagent_api.settings'
import django
django.setup()

from django.contrib.auth.models import User
from strategy_api.models import Strategy

print("=== USERS ===")
for u in User.objects.all():
    print(f"  id={u.id}  username={u.username}  is_superuser={u.is_superuser}")

print("\n=== STRATEGIES ===")
for s in Strategy.objects.all():
    has_code = bool(s.strategy_code and s.strategy_code.strip())
    print(f"  id={s.id}  name={s.name}  owner={s.created_by.username}  has_code={has_code}")

print(f"\nTotal strategies: {Strategy.objects.count()}")
