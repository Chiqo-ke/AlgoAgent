import sys
sys.path.insert(0, '.')

from Backtest.key_rotation import get_key_manager

# Initialize key manager
km = get_key_manager()
print(f'✅ Key manager initialized')
print(f'   Total keys: {len(km.keys)}')

# Test key selection
key = km.select_key('gemini-2.0-flash', 5000)
if key:
    print(f'   Selected key: {key["key_id"]}')
    print(f'   Model: {key.get("model", "N/A")}')
    print(f'   Has secret: {"secret" in key}')
    print('')
    print('✅ Key rotation infrastructure is working!')
else:
    print('   ❌ No key available')
