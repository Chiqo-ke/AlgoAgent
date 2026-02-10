"""
Multi-Provider Integration Test Suite

Tests the enhanced multi-provider system with:
- OpenCode (Claude Sonnet 4, GPT-4o, Gemini)
- GitHub Models
- Direct provider access (Gemini, Anthropic, OpenAI)

Usage:
    python test_multi_provider.py
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

import logging
from llm.providers import get_provider_client, _PROVIDERS
from llm.base_provider import LLMResponse, ProviderError, RateLimitError, AuthenticationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_env():
    """Load environment variables from .env file"""
    env_path = Path(__file__).parent / '.env'
    if not env_path.exists():
        logger.warning(f".env file not found at {env_path}")
        return
    
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()


def get_api_key(key_id: str) -> str:
    """Get API key from environment"""
    # Try multiple formats
    formats = [
        f"API_KEY_{key_id}",
        f"API_KEY_{key_id.replace('-', '_')}",
        key_id.upper()
    ]
    
    for fmt in formats:
        key = os.getenv(fmt)
        if key and not key.startswith('YOUR'):
            return key
    
    return None


def test_provider(provider_name: str, model: str, key_id: str):
    """
    Test a specific provider with a simple request.
    
    Args:
        provider_name: Provider name (e.g., 'opencode', 'github-models')
        model: Model name (e.g., 'claude-sonnet-4-20250514')
        key_id: Key identifier from keys.json
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing: {provider_name} - {model}")
    logger.info(f"Key ID: {key_id}")
    logger.info(f"{'='*60}")
    
    # Get API key
    api_key = get_api_key(key_id)
    if not api_key:
        logger.warning(f"❌ Skipping: No API key found for {key_id}")
        logger.info(f"   Expected env var: API_KEY_{key_id}")
        return None
    
    # Mask key for display
    masked_key = f"{api_key[:10]}...{api_key[-4:]}" if len(api_key) > 14 else "***"
    logger.info(f"🔑 API Key: {masked_key}")
    
    try:
        # Get provider client
        client = get_provider_client(provider_name)
        
        # Test messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello from {provider_name}!' and nothing else."}
        ]
        
        # Make request
        logger.info("📤 Sending request...")
        response = client.chat_completion(
            api_key=api_key,
            model=model,
            messages=messages,
            max_tokens=50,
            temperature=0.7
        )
        
        # Display response
        logger.info(f"✅ SUCCESS!")
        logger.info(f"📝 Response: {response['content']}")
        logger.info(f"🎯 Model: {response['model']}")
        logger.info(f"📊 Tokens: {response['tokens']}")
        logger.info(f"🏁 Finish Reason: {response['finish_reason']}")
        
        return response
        
    except AuthenticationError as e:
        logger.error(f"❌ Authentication failed: {e}")
        logger.info("   Check if your API key is correct and has proper permissions")
        return None
        
    except RateLimitError as e:
        logger.error(f"❌ Rate limit exceeded: {e}")
        if hasattr(e, 'retry_after'):
            logger.info(f"   Retry after: {e.retry_after} seconds")
        return None
        
    except ProviderError as e:
        logger.error(f"❌ Provider error: {e}")
        return None
        
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_opencode():
    """Test OpenCode provider with multiple models"""
    logger.info("\n" + "="*60)
    logger.info("TESTING OPENCODE (Unified Multi-Provider)")
    logger.info("="*60)
    
    tests = [
        ("opencode", "claude-sonnet-4-20250514", "opencode-claude-01"),
        ("opencode", "gpt-4o-mini", "opencode-gpt4o-01"),
        ("opencode", "gemini-2.0-flash-exp", "opencode-gemini-01"),
    ]
    
    results = []
    for provider, model, key_id in tests:
        result = test_provider(provider, model, key_id)
        results.append((provider, model, result is not None))
    
    return results


def test_github_models():
    """Test GitHub Models provider"""
    logger.info("\n" + "="*60)
    logger.info("TESTING GITHUB MODELS (Free Tier)")
    logger.info("="*60)
    
    result = test_provider(
        "github-models",
        "gpt-4o-mini",
        "github-models-01"
    )
    
    return [("github-models", "gpt-4o-mini", result is not None)]


def print_summary(all_results):
    """Print test summary"""
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    
    total = len(all_results)
    passed = sum(1 for _, _, success in all_results if success)
    failed = total - passed
    
    for provider, model, success in all_results:
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} | {provider:20} | {model}")
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Total: {total} | Passed: {passed} | Failed: {failed}")
    logger.info(f"Success Rate: {(passed/total*100):.1f}%")
    logger.info(f"{'='*60}\n")


def main():
    """Run all tests"""
    logger.info("\n" + "="*80)
    logger.info(" "*20 + "MULTI-PROVIDER INTEGRATION TEST")
    logger.info("="*80)
    logger.info("\nThis will test your multi-provider LLM setup with:")
    logger.info("  • OpenCode (Claude Sonnet 4, GPT-4o, Gemini)")
    logger.info("  • GitHub Models (Free Tier)")
    logger.info("\nMake sure you have:")
    logger.info("  1. API keys configured in .env")
    logger.info("  2. keys.json with provider configurations")
    logger.info("  3. Redis running (docker run -d -p 6379:6379 redis)")
    logger.info("\n" + "="*80 + "\n")
    
    # Load environment
    logger.info("Loading environment variables...")
    load_env()
    
    # Show available providers
    logger.info("\n📚 Registered Providers:")
    for name in _PROVIDERS.keys():
        logger.info(f"  • {name}")
    
    # Run tests
    all_results = []
    
    # Test OpenCode
    opencode_results = test_opencode()
    all_results.extend(opencode_results)
    
    # Test GitHub Models
    github_results = test_github_models()
    all_results.extend(github_results)
    
    # Print summary
    print_summary(all_results)
    
    # Return exit code
    passed = sum(1 for _, _, success in all_results if success)
    return 0 if passed > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
