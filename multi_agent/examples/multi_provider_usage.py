"""
Example usage of enhanced multi-provider LLM system.

Demonstrates how to use OpenCode and other providers in your agents.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm.request_router import RequestRouter
from llm.providers import get_provider_client


def example_basic_usage():
    """Basic usage with RequestRouter (recommended)"""
    print("\n" + "="*60)
    print("  Example 1: Basic Usage with RequestRouter")
    print("="*60)
    
    router = RequestRouter()
    
    # Simple one-shot request
    # RequestRouter automatically handles:
    # - Key rotation
    # - Rate limiting
    # - Failover between providers
    # - Redis-based tracking
    
    response = router.send_one_shot(
        prompt="Explain what is a trading algorithm in one sentence",
        model_preference="claude-sonnet-4-20250514",  # Prefer Claude Sonnet 4
        temperature=0.7,
        max_tokens=100
    )
    
    print(f"\n📝 Response: {response['content']}")
    print(f"🤖 Model Used: {response.get('model', 'unknown')}")
    print(f"🔢 Tokens: {response.get('tokens', {})}")


def example_with_messages():
    """Usage with conversation history"""
    print("\n" + "="*60)
    print("  Example 2: Multi-Turn Conversation")
    print("="*60)
    
    router = RequestRouter()
    
    messages = [
        {"role": "system", "content": "You are a Python expert helping with code."},
        {"role": "user", "content": "How do I read a CSV file in Python?"},
        {"role": "assistant", "content": "You can use pandas: `df = pd.read_csv('file.csv')`"},
        {"role": "user", "content": "How do I filter rows where column 'price' > 100?"}
    ]
    
    # Router preserves conversation context
    response = router.send_one_shot(
        messages=messages,
        model_preference="gpt-4o",  # Can mix models in conversation
        temperature=0.7
    )
    
    print(f"\n📝 Response: {response['content'][:200]}...")


def example_multi_provider_fallback():
    """Demonstrates automatic failover between providers"""
    print("\n" + "="*60)
    print("  Example 3: Multi-Provider Fallback")
    print("="*60)
    
    router = RequestRouter()
    
    # Configure multiple providers in keys.json with different priorities
    # Router will try them in order:
    # 1. opencode-claude-01 (priority 1)
    # 2. opencode-gpt4o-01 (priority 2)
    # 3. github-models-01 (priority 4)
    
    response = router.send_one_shot(
        prompt="Generate a Python function to calculate factorial",
        model_preference="claude-sonnet-4-20250514",
        temperature=0.7,
        max_tokens=500
    )
    
    print(f"\n📝 Generated Code:\n{response['content']}")
    print(f"\n✅ Used provider: {response.get('model', 'unknown')}")


def example_direct_provider_usage():
    """Direct provider client usage (advanced)"""
    print("\n" + "="*60)
    print("  Example 4: Direct Provider Client")
    print("="*60)
    
    # Get OpenCode client directly
    client = get_provider_client("opencode")
    
    # Get API key from environment
    api_key = os.getenv("API_KEY_opencode-claude-01")
    
    if not api_key:
        print("⏭️  SKIPPED - No OpenCode API key configured")
        return
    
    # Use client directly (bypasses RequestRouter)
    response = client.chat_completion(
        api_key=api_key,
        model="claude-sonnet-4-20250514",
        messages=[
            {"role": "user", "content": "What is 15 * 24?"}
        ],
        max_tokens=50,
        temperature=0.3
    )
    
    print(f"\n📝 Response: {response['content']}")
    print(f"🔢 Tokens used: {response['tokens']}")


def example_workload_routing():
    """Route requests based on workload complexity"""
    print("\n" + "="*60)
    print("  Example 5: Workload-Based Routing")
    print("="*60)
    
    router = RequestRouter()
    
    # Light workload - use fast model
    simple_task = router.send_one_shot(
        prompt="Say hello",
        model_preference="gemini-2.0-flash-exp",  # Fast, efficient
        temperature=0.7
    )
    print(f"\n💨 Light task (Gemini Flash): {simple_task['content']}")
    
    # Heavy workload - use powerful model
    complex_task = router.send_one_shot(
        prompt="Design a microservices architecture for a trading platform",
        model_preference="claude-sonnet-4-20250514",  # Best for complex reasoning
        temperature=0.7,
        max_tokens=1000
    )
    print(f"\n🧠 Heavy task (Claude Sonnet 4): {complex_task['content'][:150]}...")


def example_agent_integration():
    """How to use in agent classes"""
    print("\n" + "="*60)
    print("  Example 6: Agent Integration Pattern")
    print("="*60)
    
    class CoderAgent:
        """Example agent that generates code"""
        
        def __init__(self):
            self.router = RequestRouter()
            self.conversation_history = []
        
        def generate_code(self, task: str) -> dict:
            """Generate code for a task"""
            # Build messages
            messages = [
                {"role": "system", "content": "You are an expert Python developer. Generate clean, well-documented code."}
            ]
            messages.extend(self.conversation_history)
            messages.append({"role": "user", "content": f"Task: {task}"})
            
            # Use Claude Sonnet 4 for code generation (best quality)
            response = self.router.send_one_shot(
                messages=messages,
                model_preference="claude-sonnet-4-20250514",
                temperature=0.7,
                max_tokens=2000
            )
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": task})
            self.conversation_history.append({"role": "assistant", "content": response['content']})
            
            return {
                "code": response['content'],
                "model": response.get('model'),
                "tokens": response.get('tokens', {})
            }
    
    # Use the agent
    agent = CoderAgent()
    result = agent.generate_code("Create a function to validate email addresses")
    
    print(f"\n📝 Generated Code:\n{result['code'][:200]}...")
    print(f"\n✅ Model: {result['model']}")
    print(f"🔢 Tokens: {result['tokens']}")


def example_cost_tracking():
    """Track costs across providers"""
    print("\n" + "="*60)
    print("  Example 7: Cost Tracking")
    print("="*60)
    
    # Approximate pricing (per 1K tokens)
    PRICING = {
        "claude-sonnet-4-20250514": {"input": 0.003, "output": 0.015},
        "gpt-4o": {"input": 0.0025, "output": 0.01},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gemini-2.0-flash-exp": {"input": 0.0, "output": 0.0},  # Free tier
    }
    
    def calculate_cost(model: str, tokens: dict) -> float:
        """Calculate estimated cost"""
        if model not in PRICING:
            return 0.0
        
        pricing = PRICING[model]
        cost = (
            tokens.get('input', 0) / 1000 * pricing['input'] +
            tokens.get('output', 0) / 1000 * pricing['output']
        )
        return cost
    
    router = RequestRouter()
    
    # Make request
    response = router.send_one_shot(
        prompt="Explain REST API in 2 sentences",
        model_preference="claude-sonnet-4-20250514",
        temperature=0.7
    )
    
    # Calculate cost
    model = response.get('model', '')
    tokens = response.get('tokens', {})
    cost = calculate_cost(model, tokens)
    
    print(f"\n📝 Response: {response['content']}")
    print(f"\n💰 Cost Breakdown:")
    print(f"   Model: {model}")
    print(f"   Input tokens: {tokens.get('input', 0)}")
    print(f"   Output tokens: {tokens.get('output', 0)}")
    print(f"   Estimated cost: ${cost:.6f}")


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("  Enhanced Multi-Provider LLM Usage Examples")
    print("="*60)
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded .env file\n")
    except ImportError:
        print("⚠️  python-dotenv not installed (pip install python-dotenv)\n")
    
    try:
        # Run examples
        example_basic_usage()
        example_with_messages()
        example_multi_provider_fallback()
        example_direct_provider_usage()
        example_workload_routing()
        example_agent_integration()
        example_cost_tracking()
        
        print("\n" + "="*60)
        print("  All Examples Complete!")
        print("="*60)
        print("\n💡 Next Steps:")
        print("   1. Set up OpenCode: See OPENCODE_SETUP.md")
        print("   2. Configure keys.json with your preferences")
        print("   3. Run: python tests/test_providers.py")
        print("   4. Use in your agents!")
        print()
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
