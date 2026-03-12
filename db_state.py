import os, sys
os.chdir(r'C:\Users\nyaga\Documents\AlgoAgent\monolithic_agent')
sys.path.insert(0, '.')
os.environ['DJANGO_SETTINGS_MODULE'] = 'algoagent_api.settings'
import django
django.setup()
from trading_sessions_api.models import LiveTradingSession, BrokerCredential

print("=== BROKER CREDENTIALS ===")
for c in BrokerCredential.objects.all():
    print(f"  id={c.id} user={c.user} label={c.label} server={c.mt5_server} login={c.mt5_login} default={c.is_default}")

print("\n=== LIVE SESSIONS ===")
for s in LiveTradingSession.objects.all():
    print(f"  id={s.id} strategy_id={s.strategy_id} status={s.status} pid={s.pid} dry_run={s.dry_run} error={s.error_message if hasattr(s,'error_message') else 'N/A'}")

print(f"\nTotal sessions: {LiveTradingSession.objects.count()}")
