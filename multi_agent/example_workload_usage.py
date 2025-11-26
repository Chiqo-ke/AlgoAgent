"""
Example: Using Workload-Based Model Selection

This demonstrates how to use the updated LLM Router with:
- Workload-based model selection (light/medium/heavy)
- Safety filter bypass for code generation
- Automatic fallback and retry logic
"""

from llm.router import get_request_router

# Initialize router (uses keys.json configuration)
router = get_request_router()


# Example 1: Light workload - Simple task
print("=" * 60)
print("Example 1: Light Workload (gemini-2.0-flash-exp)")
print("=" * 60)

response = router.send_one_shot(
    prompt="Create a simple TODO list with 3 tasks for building a trading strategy",
    workload="light",  # Uses gemini-2.0-flash-exp (fastest, 15 RPM)
    max_output_tokens=500,
    temperature=0.7
)

if response['success']:
    print("✅ Response received")
    print(f"Model used: {response['model']}")
    print(f"Tokens: {response.get('tokens', {})}")
    print(f"\nContent:\n{response['content'][:200]}...")
else:
    print(f"❌ Error: {response['error']}")


# Example 2: Medium workload - Code generation
print("\n" + "=" * 60)
print("Example 2: Medium Workload (gemini-1.5-pro)")
print("=" * 60)

response = router.send_one_shot(
    prompt="""Generate Python code for a simple moving average crossover strategy.
    Include entry logic, exit logic, and position sizing.""",
    workload="medium",  # Uses gemini-1.5-pro (balanced, 2 RPM)
    max_output_tokens=2000,
    temperature=0.5
)

if response['success']:
    print("✅ Response received")
    print(f"Model used: {response['model']}")
    print(f"Key ID: {response['key_id']}")
    print(f"\nContent preview:\n{response['content'][:300]}...")
else:
    print(f"❌ Error: {response['error']}")


# Example 3: Heavy workload - Complex reasoning
print("\n" + "=" * 60)
print("Example 3: Heavy Workload (gemini-exp-1206)")
print("=" * 60)

response = router.send_one_shot(
    prompt="""Design a comprehensive multi-strategy trading system that includes:
    1. Mean reversion strategy
    2. Trend following strategy
    3. Portfolio risk management
    4. Position correlation analysis
    5. Dynamic capital allocation
    
    Provide detailed architecture and implementation approach.""",
    workload="heavy",  # Uses gemini-exp-1206 (best reasoning, 2 RPM)
    max_output_tokens=4000,
    temperature=0.3
)

if response['success']:
    print("✅ Response received")
    print(f"Model used: {response['model']}")
    print(f"Key ID: {response['key_id']}")
    print(f"\nContent preview:\n{response['content'][:300]}...")
else:
    print(f"❌ Error: {response['error']}")


# Example 4: Conversation with workload
print("\n" + "=" * 60)
print("Example 4: Multi-turn Conversation")
print("=" * 60)

conv_id = "strategy_design_001"

# First message
response = router.send_chat(
    conv_id=conv_id,
    prompt="I want to create a RSI-based mean reversion strategy. What parameters should I consider?",
    workload="medium",
    system_prompt="You are an expert algorithmic trading assistant.",
    max_output_tokens=1000
)

if response['success']:
    print("✅ Turn 1 - Model:", response['model'])
    print(f"Response: {response['content'][:200]}...")
    
    # Follow-up message (uses conversation history)
    response = router.send_chat(
        conv_id=conv_id,
        prompt="How should I handle risk management for this strategy?",
        workload="medium",
        max_output_tokens=1000
    )
    
    if response['success']:
        print("\n✅ Turn 2 - Model:", response['model'])
        print(f"Response: {response['content'][:200]}...")
else:
    print(f"❌ Error: {response['error']}")


# Example 5: Check router health
print("\n" + "=" * 60)
print("Example 5: Router Health Check")
print("=" * 60)

health = router.health_check()
print(f"Healthy: {health['healthy']}")
print(f"Key Manager: {health['key_manager']['active_keys']} active keys")
print(f"Keys in cooldown: {health['key_manager']['keys_in_cooldown']}")
print(f"Conversation Store: {'✅' if health['conversation_store'] else '❌'}")


# Example 6: Automatic fallback
print("\n" + "=" * 60)
print("Example 6: Automatic Fallback")
print("=" * 60)
print("If heavy workload keys are rate-limited, router falls back to medium/light")

response = router.send_one_shot(
    prompt="Quick analysis: What's the main advantage of using EMA over SMA?",
    workload="heavy",  # Requests heavy, but may fallback if rate limited
    max_output_tokens=300
)

if response['success']:
    print(f"✅ Model used: {response['model']}")
    model = response['model']
    if 'flash' in model:
        print("   (Fell back to Flash model)")
    elif '1.5-pro' in model:
        print("   (Fell back to Pro model)")
    else:
        print("   (Used requested heavy model)")
else:
    print(f"❌ Error: {response['error']}")


print("\n" + "=" * 60)
print("WORKLOAD RECOMMENDATIONS")
print("=" * 60)
print("""
Light (gemini-2.0-flash-exp):
  - TODO list generation
  - Simple summaries
  - Template code
  - Chat responses
  - 15 RPM limit

Medium (gemini-1.5-pro):
  - Strategy generation
  - Code review
  - Complex logic
  - Analysis tasks
  - 2 RPM limit

Heavy (gemini-exp-1206):
  - System architecture
  - Advanced reasoning
  - Portfolio optimization
  - Critical decisions
  - 2 RPM limit
  
Note: Safety filters are DISABLED (BLOCK_NONE) for all models
      to ensure code generation isn't blocked.
""")
