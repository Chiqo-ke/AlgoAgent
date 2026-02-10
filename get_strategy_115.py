import sys
import os

# Set up Django
sys.path.insert(0, 'C:/Users/nyaga/Documents/AlgoAgent/monolithic_agent')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monolithic_agent.settings')

import django
django.setup()

from strategy_api.models import Strategy

# Get strategy 115
try:
    s = Strategy.objects.get(id=115)
    print(f"=== STRATEGY 115: {s.name} ===")
    print(f"Description: {s.description}")
    print(f"Status: {s.status}")
    print(f"Code length: {len(s.code)} chars")
    print(f"\n{'='*80}")
    print("GENERATED CODE:")
    print(f"{'='*80}\n")
    print(s.code)
except Strategy.DoesNotExist:
    print("Strategy 115 not found")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
