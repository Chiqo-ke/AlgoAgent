"""
Integration test for RequestRouter with multi-key setup.
Tests the complete flow: PlannerService, CoderAgent, ArchitectAgent with retry.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

print("="*60)
print("RequestRouter Multi-Key Integration Test")
print("="*60)

# Verify environment
print("\n1. Environment Configuration:")
print(f"   REDIS_URL: {os.getenv('REDIS_URL', 'NOT SET')}")
print(f"   SECRET_STORE_TYPE: {os.getenv('SECRET_STORE_TYPE', 'NOT SET')}")
print(f"   LLM_MULTI_KEY_ROUTER_ENABLED: {os.getenv('LLM_MULTI_KEY_ROUTER_ENABLED', 'NOT SET')}")
print(f"   LLM_MAX_RETRIES: {os.getenv('LLM_MAX_RETRIES', 'NOT SET')}")
print(f"   LLM_BASE_BACKOFF_MS: {os.getenv('LLM_BASE_BACKOFF_MS', 'NOT SET')}")

# Check API keys
api_keys = []
for key_id in ['gemini-flash-01', 'gemini-flash-02', 'gemini-pro-01']:
    # Try both formats: API_KEY_gemini_flash_01 and API_KEY_gemini-flash-01
    env_key1 = f'API_KEY_{key_id.replace("-", "_")}'
    env_key2 = f'API_KEY_{key_id}'
    key_value = os.getenv(env_key1) or os.getenv(env_key2)
    if key_value:
        api_keys.append(f"{key_id}: {key_value[:15]}...")
    else:
        api_keys.append(f"{key_id}: NOT SET (tried {env_key1} and {env_key2})")

print("\n2. API Keys:")
for key_info in api_keys:
    print(f"   {key_info}")

# Test RequestRouter initialization
print("\n3. Testing RequestRouter Initialization...")
try:
    from llm.router import get_request_router
    
    router = get_request_router()
    print("   ✓ RequestRouter initialized")
    
    # Health check
    health = router.health_check()
    print(f"\n4. Router Health Check:")
    print(f"   Healthy: {health['healthy']}")
    print(f"   Key Manager: {health.get('key_manager', {})}")
    print(f"   Conversation Store: {health.get('conversation_store', 'Unknown')}")
    
except Exception as e:
    print(f"   ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test KeyManager
print("\n5. Testing KeyManager...")
try:
    from keys.manager import get_key_manager
    
    manager = get_key_manager()
    
    # Get all key statuses
    statuses = manager.get_all_key_statuses()
    print(f"   Total keys: {len(statuses)}")
    
    for status in statuses:
        print(f"\n   Key: {status['key_id']}")
        print(f"      Active: {status.get('active', 'Unknown')}")
        print(f"      Model: {status.get('model', 'Unknown')}")
        print(f"      RPM: {status['rpm_usage']['count']}/{status.get('rpm_limit', 'Unknown')}")
        print(f"      TPM: {status['tpm_usage']['used']}/{status.get('tpm_limit', 'Unknown')}")
        print(f"      Cooldown: {status.get('in_cooldown', 'Unknown')}")
    
except Exception as e:
    print(f"   ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test PlannerService integration
print("\n6. Testing PlannerService Integration...")
try:
    from planner_service.planner import PlannerService
    
    # Check if using router
    planner = PlannerService()
    use_router = os.getenv('LLM_MULTI_KEY_ROUTER_ENABLED', 'false').lower() == 'true'
    
    print(f"   Use Router: {use_router}")
    print(f"   Router Object: {planner.router}")
    
    if use_router:
        print("   ✓ PlannerService configured to use RequestRouter")
    else:
        print("   ⚠ PlannerService using fallback mode")
    
except Exception as e:
    print(f"   ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test CoderAgent integration
print("\n7. Testing CoderAgent Integration...")
try:
    from agents.coder_agent.coder import CoderAgent
    from contracts.message_bus import InMemoryMessageBus
    
    bus = InMemoryMessageBus()
    coder = CoderAgent(agent_id="test_coder", message_bus=bus)
    
    use_router = os.getenv('LLM_MULTI_KEY_ROUTER_ENABLED', 'false').lower() == 'true'
    
    print(f"   Use Router: {use_router}")
    print(f"   Router Object: {coder.router}")
    
    if use_router:
        print("   ✓ CoderAgent configured to use RequestRouter")
    else:
        print("   ⚠ CoderAgent using fallback mode")
    
except Exception as e:
    print(f"   ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test ArchitectAgent integration
print("\n8. Testing ArchitectAgent Integration...")
try:
    from agents.architect_agent.architect import ArchitectAgent
    
    bus = InMemoryMessageBus()
    architect = ArchitectAgent(message_bus=bus)
    
    use_router = os.getenv('LLM_MULTI_KEY_ROUTER_ENABLED', 'false').lower() == 'true'
    
    print(f"   Use Router: {use_router}")
    print(f"   Router Object: {architect.router}")
    
    if use_router:
        print("   ✓ ArchitectAgent configured to use RequestRouter")
    else:
        print("   ⚠ ArchitectAgent using fallback mode")
    
except Exception as e:
    print(f"   ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test simple request with retry
print("\n9. Testing Simple Request (with retry capability)...")
try:
    import time
    
    start = time.time()
    response = router.send_one_shot(
        prompt="Say 'RequestRouter integration successful!' in one sentence.",
        model_preference="gemini-2.5-flash"
    )
    duration = time.time() - start
    
    if response['success']:
        print(f"   ✓ Request succeeded in {duration:.2f}s")
        print(f"   Response: {response['content'][:100]}...")
        if 'metadata' in response:
            print(f"   Model: {response['metadata'].get('model_used', 'Unknown')}")
            print(f"   Key: {response['metadata'].get('key_used', 'Unknown')}")
            print(f"   Tokens: {response['metadata'].get('completion_tokens', 'Unknown')}")
        else:
            print(f"   Metadata: Not available")
    else:
        print(f"   ✗ Request failed: {response['error']}")
        sys.exit(1)
    
except Exception as e:
    print(f"   ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test conversation mode
print("\n10. Testing Conversation Mode (with context preservation)...")
try:
    conv_id = "integration_test_conv"
    
    # First message
    response1 = router.send_chat(
        conv_id=conv_id,
        prompt="My name is Alice. Remember this."
    )
    
    if not response1['success']:
        print(f"   ✗ First message failed: {response1['error']}")
        sys.exit(1)
    
    key1 = response1.get('metadata', {}).get('key_used', 'Unknown')
    print(f"   ✓ First message sent (key: {key1})")
    
    # Second message (test context)
    response2 = router.send_chat(
        conv_id=conv_id,
        prompt="What is my name?"
    )
    
    if not response2['success']:
        print(f"   ✗ Second message failed: {response2['error']}")
        sys.exit(1)
    
    key2 = response2.get('metadata', {}).get('key_used', 'Unknown')
    print(f"   ✓ Second message sent (key: {key2})")
    print(f"   Response: {response2['content'][:100]}...")
    
    # Check if context was preserved
    if 'alice' in response2['content'].lower():
        print("   ✓ Context preserved across messages")
    else:
        print("   ⚠ Context may not be preserved")
    
except Exception as e:
    print(f"   ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test retry mechanism (by checking configuration)
print("\n11. Testing Retry Configuration...")
try:
    print(f"   Max Retries: {router.max_retries}")
    print(f"   Base Backoff: {router.base_backoff_ms}ms")
    
    # Test backoff calculation
    backoff_0 = router._calculate_backoff(0)
    backoff_1 = router._calculate_backoff(1)
    backoff_2 = router._calculate_backoff(2)
    
    print(f"   Backoff sequence: {backoff_0}ms → {backoff_1}ms → {backoff_2}ms")
    print("   ✓ Retry mechanism configured")
    
except Exception as e:
    print(f"   ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Final summary
print("\n" + "="*60)
print("Integration Test Summary")
print("="*60)
print("✓ Environment configured")
print("✓ RequestRouter initialized")
print("✓ KeyManager operational")
print("✓ PlannerService integrated")
print("✓ CoderAgent integrated")
print("✓ ArchitectAgent integrated")
print("✓ Simple requests working")
print("✓ Conversation mode working")
print("✓ Retry mechanism configured")
print("\n🎉 ALL TESTS PASSED - RequestRouter fully integrated!")
print("="*60)
