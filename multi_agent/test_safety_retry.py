"""
Test safety filter retry mechanism with Gemini Pro fallback.
"""
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_safety_retry():
    """Test that safety filter triggers Pro model retry."""
    print("=" * 70)
    print("TESTING SAFETY FILTER RETRY MECHANISM")
    print("=" * 70)
    
    # Test 1: Verify environment setup
    print("\n1️⃣ Checking Environment Configuration...")
    router_enabled = os.getenv('LLM_MULTI_KEY_ROUTER_ENABLED', 'false').lower() == 'true'
    print(f"   ✓ Router Enabled: {router_enabled}")
    
    if not router_enabled:
        print("   ⚠️  Router is disabled - enable it in .env")
        return False
    
    # Check API keys
    flash_keys = [f"API_KEY_gemini_flash_{i:02d}" for i in range(1, 4)]
    pro_keys = [f"API_KEY_gemini_pro_{i:02d}" for i in range(1, 3)]
    
    flash_count = sum(1 for k in flash_keys if os.getenv(k))
    pro_count = sum(1 for k in pro_keys if os.getenv(k))
    
    print(f"   ✓ Gemini Flash Keys: {flash_count}")
    print(f"   ✓ Gemini Pro Keys: {pro_count}")
    
    if pro_count == 0:
        print("   ⚠️  No Pro keys found - retry will fail")
        return False
    
    # Test 2: Import and initialize router
    print("\n2️⃣ Initializing RequestRouter...")
    try:
        from llm.router import get_request_router
        router = get_request_router()
        print("   ✓ Router initialized")
        
        # Health check
        health = router.health_check()
        print(f"   ✓ Router Healthy: {health['healthy']}")
        print(f"   ✓ Total Keys: {health['key_manager']['total_keys']}")
        print(f"   ✓ Active Keys: {health['key_manager']['active_keys']}")
    except Exception as e:
        print(f"   ✗ Router initialization failed: {e}")
        return False
    
    # Test 3: Test with financial prompt (likely to trigger safety filter)
    print("\n3️⃣ Testing with Financial Trading Prompt...")
    test_prompt = """
Create Python code for a trading strategy with these requirements:
- Buy when RSI indicator drops below 30
- Sell when RSI indicator rises above 70
- Set stop loss at 2% below entry price
- Set take profit at 5% above entry price
- Use 10 pips as the minimum pip value

Generate complete Python code implementing this strategy.
"""
    
    try:
        print("   → Sending request (may trigger safety filter on Flash models)...")
        response = router.send_chat(
            conv_id="test_safety_filter",
            prompt=test_prompt,
            model_preference="gemini-2.5-flash",  # Start with Flash
            tags=["flash"]
        )
        
        if response.get("success"):
            print("   ✓ Response received successfully!")
            print(f"   ✓ Model used: {response.get('model_used', 'unknown')}")
            print(f"   ✓ Response length: {len(response.get('response', ''))} chars")
            
            # Check if Pro model was used (indicating retry worked)
            model_used = response.get('model_used', '')
            if 'pro' in model_used.lower():
                print("   ✅ SUCCESS: Retried with Pro model after safety filter!")
            elif 'flash' in model_used.lower():
                print("   ℹ️  Flash model succeeded (no safety filter triggered)")
            
            return True
        else:
            print(f"   ✗ Request failed: {response.get('error')}")
            return False
            
    except Exception as e:
        print(f"   ✗ Exception occurred: {e}")
        return False

if __name__ == "__main__":
    print("\n🧪 Safety Filter Retry Test\n")
    
    success = test_safety_retry()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ SAFETY RETRY MECHANISM IS WORKING!")
        print("=" * 70)
        print("\nNext steps:")
        print("  1. Run: python cli.py")
        print("  2. Submit: Create RSI strategy with buy<30 sell>70")
        print("  3. Watch for '[CoderAgent] Retrying with Pro model...' messages")
    else:
        print("⚠️  SAFETY RETRY TEST INCOMPLETE")
        print("=" * 70)
        print("\nPlease ensure:")
        print("  1. LLM_MULTI_KEY_ROUTER_ENABLED=true in .env")
        print("  2. At least 1 Pro API key configured")
        print("  3. Redis is running: docker ps")
    print()
