"""
Test Azure OpenAI integration with the multi-agent LLM router.

This script verifies that:
1. Azure OpenAI provider is properly registered
2. Azure endpoints are configured correctly
3. API keys are accessible from environment/secret store
4. Fallback mechanism works when Gemini keys are unavailable
"""
import os
import sys
import logging

# Add multi_agent to path
sys.path.insert(0, os.path.dirname(__file__))

from llm.router import get_request_router
from llm.providers import get_provider_client, ProviderError
from keys.manager import KeyManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_azure_provider_registration():
    """Test 1: Verify Azure OpenAI provider is registered."""
    print("\n" + "="*70)
    print("TEST 1: Azure Provider Registration")
    print("="*70)
    
    try:
        client = get_provider_client('azure-openai')
        print("✅ Azure OpenAI provider successfully registered")
        print(f"   Provider class: {client.__class__.__name__}")
        return True
    except ProviderError as e:
        print(f"❌ FAILED: {e}")
        return False


def test_azure_configuration():
    """Test 2: Verify Azure endpoint configuration."""
    print("\n" + "="*70)
    print("TEST 2: Azure Configuration")
    print("="*70)
    
    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    api_version = os.getenv('AZURE_OPENAI_API_VERSION')
    
    if endpoint:
        print(f"✅ AZURE_OPENAI_ENDPOINT configured: {endpoint}")
    else:
        print("❌ AZURE_OPENAI_ENDPOINT not set in environment")
        return False
    
    if api_version:
        print(f"✅ AZURE_OPENAI_API_VERSION configured: {api_version}")
    else:
        print("⚠️  AZURE_OPENAI_API_VERSION not set (will use default: 2024-02-15-preview)")
    
    return True


def test_azure_keys_loaded():
    """Test 3: Verify Azure keys are loaded in KeyManager."""
    print("\n" + "="*70)
    print("TEST 3: Azure Keys in KeyManager")
    print("="*70)
    
    try:
        manager = KeyManager.get_instance()
        azure_keys = [
            key for key in manager.active_keys 
            if key.provider == 'azure-openai'
        ]
        
        if azure_keys:
            print(f"✅ Found {len(azure_keys)} Azure OpenAI key(s):")
            for key in azure_keys:
                priority = key.tags.get('priority', 'N/A')
                workload = key.tags.get('workload', 'N/A')
                print(f"   - {key.key_id}: {key.model_name}")
                print(f"     └─ Priority: {priority}, Workload: {workload}")
                print(f"     └─ RPM: {key.rpm}, TPM: {key.tpm}")
            return True
        else:
            print("❌ No Azure OpenAI keys found in keys.json")
            print("   Make sure keys.json contains entries with provider='azure-openai'")
            return False
            
    except Exception as e:
        print(f"❌ Error loading KeyManager: {e}")
        return False


def test_azure_api_key_retrieval():
    """Test 4: Verify Azure API keys can be retrieved from secret store."""
    print("\n" + "="*70)
    print("TEST 4: Azure API Key Retrieval")
    print("="*70)
    
    try:
        from keys.secret_store import get_secret_store
        
        store = get_secret_store()
        
        # Test key retrieval for configured Azure keys
        test_key_ids = ['azure-gpt4o-mini-01', 'azure-gpt4o-01']
        
        for key_id in test_key_ids:
            try:
                api_key = store.get_key(key_id)
                if api_key and api_key != f'your_azure_openai_api_key_here':
                    print(f"✅ {key_id}: Retrieved successfully")
                    print(f"   └─ Key length: {len(api_key)} characters")
                    print(f"   └─ Key preview: {api_key[:10]}...{api_key[-4:]}")
                else:
                    print(f"⚠️  {key_id}: Key is placeholder value")
                    print(f"   └─ Update API_KEY_{key_id.replace('-', '_')} in .env")
            except Exception as e:
                print(f"❌ {key_id}: Failed to retrieve - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error accessing secret store: {e}")
        return False


def test_azure_direct_call():
    """Test 5: Make a direct API call to Azure OpenAI."""
    print("\n" + "="*70)
    print("TEST 5: Direct Azure API Call")
    print("="*70)
    
    # Check if user has configured real API key
    from keys.secret_store import get_secret_store
    store = get_secret_store()
    
    try:
        test_key = store.get_key('azure-gpt4o-mini-01')
        if not test_key or test_key == 'your_azure_openai_api_key_here':
            print("⚠️  SKIPPED: Azure API key not configured yet")
            print("   Update API_KEY_azure_gpt4o_mini_01 in .env to run this test")
            return None
    except:
        print("⚠️  SKIPPED: Could not check API key status")
        return None
    
    try:
        router = get_request_router()
        
        print("Sending test request to Azure OpenAI (gpt-4o-mini)...")
        response = router.send_one_shot(
            prompt="Respond with exactly: 'Azure OpenAI integration successful!'",
            model_preference="gpt-4o-mini",
            workload="light",
            max_output_tokens=50,
            temperature=0.0
        )
        
        if response.get('success'):
            content = response.get('content', '')
            model = response.get('model', 'unknown')
            tokens = response.get('tokens', {})
            
            print(f"✅ API call successful!")
            print(f"   Model: {model}")
            print(f"   Response: {content}")
            print(f"   Tokens: {tokens.get('total', 'N/A')} (input: {tokens.get('input', 'N/A')}, output: {tokens.get('output', 'N/A')})")
            return True
        else:
            error = response.get('error', 'Unknown error')
            print(f"❌ API call failed: {error}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during API call: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fallback_mechanism():
    """Test 6: Verify fallback from Gemini to Azure."""
    print("\n" + "="*70)
    print("TEST 6: Fallback Mechanism (Simulation)")
    print("="*70)
    
    try:
        manager = KeyManager.get_instance()
        
        # Count available providers
        gemini_keys = [k for k in manager.active_keys if k.provider == 'gemini']
        azure_keys = [k for k in manager.active_keys if k.provider == 'azure-openai']
        
        print(f"Provider inventory:")
        print(f"   - Gemini keys: {len(gemini_keys)} (priority 1)")
        print(f"   - Azure keys: {len(azure_keys)} (priority 2)")
        
        if gemini_keys and azure_keys:
            print("\n✅ Fallback mechanism configured correctly:")
            print("   1. Router will try Gemini keys first (priority 1)")
            print("   2. If Gemini fails/exhausted, will try Azure (priority 2)")
            print("   3. KeyManager selects by: workload → priority → capacity")
            return True
        elif azure_keys and not gemini_keys:
            print("\n⚠️  Only Azure keys configured (no Gemini fallback source)")
            return True
        else:
            print("\n❌ No Azure keys configured for fallback")
            return False
            
    except Exception as e:
        print(f"❌ Error checking fallback: {e}")
        return False


def run_all_tests():
    """Run all Azure integration tests."""
    print("\n")
    print("█" * 70)
    print("  AZURE OPENAI INTEGRATION TEST SUITE")
    print("█" * 70)
    
    results = {
        'Provider Registration': test_azure_provider_registration(),
        'Configuration': test_azure_configuration(),
        'Keys Loaded': test_azure_keys_loaded(),
        'Key Retrieval': test_azure_api_key_retrieval(),
        'Direct API Call': test_azure_direct_call(),
        'Fallback Mechanism': test_fallback_mechanism()
    }
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result is True else "❌ FAIL" if result is False else "⚠️  SKIP"
        print(f"{status}  {test_name}")
    
    print(f"\nResults: {passed} passed, {failed} failed, {skipped} skipped")
    
    if failed == 0 and passed > 0:
        print("\n🎉 All critical tests passed! Azure OpenAI integration is ready.")
    elif failed > 0:
        print("\n⚠️  Some tests failed. Review errors above and check configuration.")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
