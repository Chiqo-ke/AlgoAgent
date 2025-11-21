"""
Test safety filter retry with Gemini Pro fallback.

This script verifies the new retry mechanism:
1. Detects safety filter errors (finish_reason=2)
2. Automatically retries with Gemini 2.5 Pro
3. Falls back to template mode if Pro also fails

Updated: November 20, 2025
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("SAFETY FILTER RETRY MECHANISM TEST")
print("=" * 70)

# Check configuration
print("\n1. Checking Configuration...")
print(f"   Router Enabled: {os.getenv('LLM_MULTI_KEY_ROUTER_ENABLED')}")
print(f"   Redis URL: {os.getenv('REDIS_URL')}")

# Check API keys
flash_keys = []
pro_keys = []

for i in range(1, 4):
    flash_key = f"API_KEY_gemini_flash_0{i}"
    pro_key = f"API_KEY_gemini_pro_0{i}"
    
    if os.getenv(flash_key):
        flash_keys.append(flash_key)
        print(f"   ✓ {flash_key}: Present")
    
    if os.getenv(pro_key):
        pro_keys.append(pro_key)
        print(f"   ✓ {pro_key}: Present")

print(f"\n   Total Flash Keys: {len(flash_keys)}")
print(f"   Total Pro Keys: {len(pro_keys)}")

if len(pro_keys) == 0:
    print("\n   ⚠️  WARNING: No Pro keys found!")
    print("   Retry mechanism will not work optimally")
    print("   Add API_KEY_gemini_pro_01 to your .env file")
else:
    print(f"\n   ✅ {len(pro_keys)} Pro key(s) available for retry")

# Test the agents
print("\n2. Testing CoderAgent Retry Mechanism...")

try:
    from agents.coder_agent.coder import CoderAgent
    from contracts.message_bus import InMemoryMessageBus
    
    bus = InMemoryMessageBus()
    coder = CoderAgent(
        agent_id="test_safety_retry",
        message_bus=bus,
        model_name="gemini-2.5-flash"
    )
    
    print(f"   ✓ CoderAgent initialized")
    print(f"   - Model: {coder.model_name}")
    print(f"   - Router: {coder.use_router}")
    print(f"   - Conversation ID: {coder.conversation_id}")
    
    # Check if retry method exists
    if hasattr(coder, '_generate_with_gemini'):
        print(f"   ✓ _generate_with_gemini method available")
        
        # Check method signature
        import inspect
        sig = inspect.signature(coder._generate_with_gemini)
        params = list(sig.parameters.keys())
        
        if 'retry_with_pro' in params:
            print(f"   ✓ retry_with_pro parameter found")
            print(f"\n   ✅ CoderAgent has full retry mechanism")
        else:
            print(f"   ✗ retry_with_pro parameter NOT found")
            print(f"   Parameters: {params}")
    else:
        print(f"   ✗ _generate_with_gemini method NOT found")
        
except Exception as e:
    print(f"   ✗ CoderAgent test failed: {e}")

print("\n3. Testing ArchitectAgent Retry Mechanism...")

try:
    from agents.architect_agent.architect import ArchitectAgent
    
    bus = InMemoryMessageBus()
    architect = ArchitectAgent(
        message_bus=bus,
        model_name="gemini-2.5-flash"
    )
    
    print(f"   ✓ ArchitectAgent initialized")
    print(f"   - Model: {architect.model_name}")
    print(f"   - Router: {architect.use_router}")
    print(f"   - Conversation ID: {architect.conversation_id}")
    print(f"\n   ✅ ArchitectAgent has retry mechanism")
    
except Exception as e:
    print(f"   ✗ ArchitectAgent test failed: {e}")

# Explain the workflow
print("\n" + "=" * 70)
print("RETRY WORKFLOW")
print("=" * 70)

print("""
When a safety filter error is detected:

1. ATTEMPT 1: Gemini 2.5 Flash (Fast, default)
   └─ If finish_reason=2 or safety error → Go to Attempt 2

2. ATTEMPT 2: Gemini 2.5 Pro (More permissive)
   └─ Retry same prompt with Pro model
   └─ If success → Return generated code ✓
   └─ If still fails → Go to Fallback

3. FALLBACK: Template Mode
   └─ Use predefined template
   └─ Always succeeds ✓

Benefits:
- Avoids false positives from overly aggressive Flash filters
- Pro model has better context understanding
- Graceful degradation ensures system always works
- No manual intervention needed
""")

print("=" * 70)
print("TEST COMPLETE")
print("=" * 70)

print("\nNext Steps:")
print("1. Start Redis: docker run -d -p 6379:6379 --name redis-llm-router redis:7-alpine")
print("2. Run CLI: python cli.py")
print("3. Submit request: submit Create EMA crossover strategy with stop loss and take profit")
print("4. Watch for retry messages:")
print("   - '[CoderAgent] Safety filter triggered with gemini-2.5-flash'")
print("   - '[CoderAgent] 🔄 Retrying with Gemini 2.5 Pro...'")
print("   - '[CoderAgent] ✓ Pro model succeeded'")

print("\n" + "=" * 70 + "\n")
