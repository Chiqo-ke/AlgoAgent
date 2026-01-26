"""Check if strategy endpoints are registered"""
import os
import sys
import django

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'algoagent_api.settings')
sys.path.insert(0, os.path.dirname(__file__))

# Setup Django
django.setup()

from rest_framework.routers import DefaultRouter
from strategy_api import views

# Create router and register
router = DefaultRouter()
router.register(r'strategies', views.StrategyViewSet)

print("\n" + "="*70)
print("REGISTERED STRATEGY API ROUTES")
print("="*70)

# Check for our new endpoints
target_endpoints = ['available_indicators', 'execute', 'execution_history', 'fix_errors', 'generate_with_ai']

for url_pattern in router.urls:
    pattern_str = str(url_pattern.pattern)
    name = url_pattern.name
    
    # Check if it's one of our target endpoints
    for endpoint in target_endpoints:
        if endpoint in pattern_str or endpoint in name:
            print(f"\n✅ Found: {endpoint}")
            print(f"   Pattern: {pattern_str}")
            print(f"   Name: {name}")
            break

print("\n" + "="*70)
print("CHECKING VIEWSET METHODS")
print("="*70)

# Check if methods exist in ViewSet
viewset = views.StrategyViewSet()
for method_name in target_endpoints:
    if hasattr(viewset, method_name):
        method = getattr(viewset, method_name)
        print(f"\n✅ Method exists: {method_name}")
        # Check if it's an action
        if hasattr(method, 'mapping'):
            print(f"   Mapped methods: {method.mapping}")
        if hasattr(method, 'detail'):
            print(f"   Detail: {method.detail}")
    else:
        print(f"\n❌ Method missing: {method_name}")

print("\n" + "="*70)
