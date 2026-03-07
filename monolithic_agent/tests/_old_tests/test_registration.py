#!/usr/bin/env python3
"""Quick test to verify indicator registration"""

import sys
import os

# Add Data directory to path
data_dir = os.path.join(os.path.dirname(__file__), 'Data')
sys.path.insert(0, data_dir)

# Now import and test
import registry

print("="*60)
print(" INDICATOR REGISTRATION TEST")
print("="*60)

registered = registry.list_indicators()

if registered:
    print(f"\n✅ SUCCESS: {len(registered)} indicators registered!")
    print(f"\nRegistered indicators:")
    for ind in sorted(registered):
        entry = registry.get_entry(ind)
        if entry:
            print(f"  - {ind.upper():<12} | inputs: {', '.join(entry['inputs']):<20} | outputs: {len(entry['outputs'])} | source: {entry['source_hint']}")
else:
    print("\n❌ FAILED: No indicators registered!")
    print("Check the docstrings in talib_adapters.py and ta_fallback_adapters.py")

print("\n" + "="*60)
