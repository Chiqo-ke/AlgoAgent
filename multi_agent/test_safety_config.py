"""
Quick test for safety filter retry mechanism.
Tests only the key configuration without heavy imports.
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("SAFETY FILTER RETRY - CONFIGURATION CHECK")
print("=" * 70)

# Check router configuration
router_enabled = os.getenv('LLM_MULTI_KEY_ROUTER_ENABLED', 'false').lower() == 'true'
redis_url = os.getenv('REDIS_URL', 'not set')

print(f"\n✓ Router Enabled: {router_enabled}")
print(f"✓ Redis URL: {redis_url}")

# Check Flash keys
print("\nFlash Keys (gemini-2.5-flash):")
flash_keys = []
for i in range(1, 4):
    key_name = f"API_KEY_gemini_flash_0{i}"
    if os.getenv(key_name):
        flash_keys.append(key_name)
        masked = os.getenv(key_name)[:8] + "..." + os.getenv(key_name)[-4:]
        print(f"  ✓ {key_name}: {masked}")

# Check Pro keys
print("\nPro Keys (gemini-2.5-pro):")
pro_keys = []
for i in range(1, 4):
    key_name = f"API_KEY_gemini_pro_0{i}"
    if os.getenv(key_name):
        pro_keys.append(key_name)
        masked = os.getenv(key_name)[:8] + "..." + os.getenv(key_name)[-4:]
        print(f"  ✓ {key_name}: {masked}")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

print(f"\nTotal Flash Keys: {len(flash_keys)}")
print(f"Total Pro Keys: {len(pro_keys)}")

if len(pro_keys) >= 1:
    print(f"\n✅ RETRY MECHANISM READY")
    print(f"   - {len(flash_keys)} Flash keys for initial attempts")
    print(f"   - {len(pro_keys)} Pro key(s) for safety filter retry")
else:
    print(f"\n⚠️  NO PRO KEYS CONFIGURED")
    print(f"   Retry will not work optimally")

# Explain the flow
print("\n" + "=" * 70)
print("HOW IT WORKS")
print("=" * 70)

print("""
When you submit a strategy request with financial terms:

1. PlannerService generates TodoList
   └─ Uses gemini-flash-01 (fast)

2. CoderAgent generates code
   └─ Attempt 1: gemini-flash-01
   └─ If safety filter (finish_reason=2):
      └─ Attempt 2: gemini-pro-01 ← NEW!
      └─ If still fails: Template mode

3. ArchitectAgent designs contract
   └─ Attempt 1: gemini-flash-01
   └─ If safety filter (finish_reason=2):
      └─ Attempt 2: gemini-pro-01 ← NEW!
      └─ If still fails: Error

Benefits:
• Pro model has less aggressive safety filters
• Better understanding of technical/financial context
• Automatic - no manual intervention
• Always has fallback (template mode)
""")

print("=" * 70)
print("NEXT STEPS")
print("=" * 70)

print("""
1. Ensure Redis is running:
   docker ps | findstr redis

2. If not running:
   docker start redis-llm-router
   OR
   docker run -d -p 6379:6379 --name redis-llm-router redis:7-alpine

3. Test with CLI:
   python cli.py

4. Submit a "risky" request:
   >>> submit Buy when 20 EMA crosses above 40 EMA. Set stop loss 10 pips below entry and take profit 40 pips above entry.

5. Watch for retry messages:
   [CoderAgent] Safety filter triggered with gemini-2.5-flash
   [CoderAgent] 🔄 Retrying with Gemini 2.5 Pro...
   [CoderAgent] ✓ Pro model succeeded

6. If Pro succeeds, you'll see:
   ✓ Code generated in XX.XXs
   ✓ Strategy file created

7. If Pro also fails:
   [CoderAgent] ⚠️  Falling back to template mode...
   ✓ Strategy file created (from template)
""")

print("=" * 70 + "\n")
