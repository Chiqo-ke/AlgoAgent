"""
Test suite for multi-provider LLM integration.

Tests all providers (OpenCode, GitHub Models, Gemini, OpenAI, Anthropic)
to ensure they work correctly with the enhanced base interface.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm.providers import (
    get_provider_client,
    OpenCodeClient,
    GitHubModelsClient,
    GeminiClient,
    OpenAIClient,
    AnthropicClient,
    ProviderError,
    RateLimitError
)


def get_env_key(provider: str, key_id: str = None) -> str:
    """Get API key from environment variables"""
    if key_id:
        key = os.getenv(f"API_KEY_{key_id}")
        if key:
            return key
    
    # Fallback patterns
    key_patterns = {
        "opencode": ["OPENCODE_API_KEY", "API_KEY_opencode-claude-01"],
        "github-models": ["GITHUB_TOKEN", "API_KEY_github-models-01"],
        "gemini": ["GEMINI_API_KEY", "API_KEY_gemini-flash-01"],
        "openai": ["OPENAI_API_KEY", "API_KEY_openai-gpt4-01"],
        "anthropic": ["ANTHROPIC_API_KEY", "API_KEY_claude-sonnet-01"]
    }
    
    for pattern in key_patterns.get(provider, []):
        key = os.getenv(pattern)
        if key:
            return key
    
    return None


def test_provider(provider_name: str, model: str, key_id: str = None):
    """Test a specific provider"""
    print(f"\n{'='*60}")
    print(f"Testing: {provider_name} ({model})")
    print(f"{'='*60}")
    
    # Get API key
    api_key = get_env_key(provider_name, key_id)
    if not api_key:
        print(f"⏭️  SKIPPED - No API key found")
        print(f"   Set environment variable: API_KEY_{key_id or provider_name}")
        return False
    
    try:
        # Get provider client
        client = get_provider_client(provider_name)
        
        # Test messages
        test_messages = [
            {"role": "user", "content": "Say 'Hello from AI!' and nothing else"}
        ]
        
        # Send request
        print(f"📤 Sending test request...")
        response = client.chat_completion(
            api_key=api_key,
            model=model,
            messages=test_messages,
            max_tokens=50,
            temperature=0.7
        )
        
        # Validate response
        assert 'content' in response, "Missing 'content' in response"
        assert 'tokens' in response, "Missing 'tokens' in response"
        assert 'model' in response, "Missing 'model' in response"
        
        # Print results
        print(f"✅ SUCCESS")
        print(f"📝 Response: {response['content'][:100]}")
        print(f"🤖 Model: {response['model']}")
        print(f"🔢 Tokens: {response['tokens']}")
        
        return True
        
    except RateLimitError as e:
        print(f"⚠️  RATE LIMITED: {str(e)[:100]}")
        if e.retry_after:
            print(f"   Retry after: {e.retry_after} seconds")
        return False
        
    except ProviderError as e:
        print(f"❌ PROVIDER ERROR: {str(e)[:200]}")
        return False
        
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {type(e).__name__}: {str(e)[:200]}")
        import traceback
        traceback.print_exc()
        return False


def test_all_providers():
    """Test all configured providers"""
    print("\n" + "="*60)
    print("  Multi-Provider LLM Integration Test Suite")
    print("="*60)
    
    # Test configurations (provider, model, key_id)
    test_configs = [
        ("opencode", "claude-sonnet-4-20250514", "opencode-claude-01"),
        ("opencode", "gpt-4o", "opencode-gpt4o-01"),
        ("opencode", "gemini-2.0-flash-exp", "opencode-gemini-01"),
        ("github-models", "gpt-4o-mini", "github-models-01"),
        ("gemini", "gemini-2.0-flash-exp", "gemini-flash-01"),
        ("openai", "gpt-4o-mini", "openai-gpt4-01"),
        ("anthropic", "claude-3-5-sonnet-20241022", "claude-sonnet-01")
    ]
    
    results = {}
    for provider, model, key_id in test_configs:
        success = test_provider(provider, model, key_id)
        results[f"{provider}:{model}"] = "✅" if success else "❌"
    
    # Print summary
    print("\n" + "="*60)
    print("  Test Summary")
    print("="*60)
    
    for config, status in results.items():
        print(f"{status} {config}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v == "✅")
    
    print(f"\n📊 Results: {passed}/{total} providers working")
    
    if passed == 0:
        print("\n⚠️  No providers are configured!")
        print("   Set up at least one provider to use the system.")
        print("\n💡 Quick setup:")
        print("   1. Get OpenCode API key: https://opencode.ai")
        print("   2. Set: API_KEY_opencode-claude-01=your_key")
        print("   3. Run: python tests/test_providers.py")


def test_streaming():
    """Test streaming functionality"""
    print("\n" + "="*60)
    print("  Testing Streaming")
    print("="*60)
    
    # Try OpenCode first (most likely to be configured)
    api_key = get_env_key("opencode", "opencode-gpt4o-01")
    
    if not api_key:
        print("⏭️  SKIPPED - No OpenCode API key for streaming test")
        return
    
    try:
        from openai import OpenAI
        
        client = OpenAI(
            api_key=api_key,
            base_url="https://opencode.ai/api/v1"
        )
        
        print("📤 Starting stream...")
        
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Count from 1 to 5"}],
            stream=True,
            max_tokens=100
        )
        
        chunks = []
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                chunks.append(content)
                print(content, end="", flush=True)
        
        print("\n✅ Streaming works!")
        print(f"   Received {len(chunks)} chunks")
        
    except Exception as e:
        print(f"❌ Streaming failed: {e}")


def main():
    """Run all tests"""
    # Load .env if available
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded .env file")
    except ImportError:
        print("⚠️  python-dotenv not installed (optional)")
    
    # Run tests
    test_all_providers()
    test_streaming()
    
    print("\n" + "="*60)
    print("  Testing Complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
