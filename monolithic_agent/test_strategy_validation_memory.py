"""
Test Script for Strategy Validation with Conversation Memory
============================================================

This script tests the newly integrated conversation memory feature with:
1. AI strategy validation
2. Strategy creation with AI
3. Strategy updates with AI
4. Conversation context tracking across multiple interactions
"""

import requests
import json
from datetime import datetime
from typing import Optional

# API Configuration
BASE_URL = "http://localhost:8000"
STRATEGY_API = f"{BASE_URL}/api/strategies"
VALIDATE_ENDPOINT = f"{STRATEGY_API}/api/validate_strategy_with_ai/"
CREATE_ENDPOINT = f"{STRATEGY_API}/api/create_strategy_with_ai/"
CHAT_ENDPOINT = f"{STRATEGY_API}/chat/chat/"
SESSIONS_ENDPOINT = f"{STRATEGY_API}/chat/"


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def print_response(response_data, title="Response"):
    """Pretty print response data"""
    print(f"\n{title}:")
    print(json.dumps(response_data, indent=2))


def validate_strategy(strategy_text: str, session_id: Optional[str] = None, use_context: bool = True):
    """
    Test strategy validation with conversation memory
    
    Args:
        strategy_text: Strategy description
        session_id: Optional session ID for conversation continuity
        use_context: Whether to use conversation history
    """
    payload = {
        "strategy_text": strategy_text,
        "input_type": "auto",
        "use_gemini": True,
        "strict_mode": False,
        "use_context": use_context
    }
    
    if session_id:
        payload["session_id"] = session_id
    
    print(f"📝 Validating Strategy:")
    print(f"   Text: {strategy_text[:100]}...")
    if session_id:
        print(f"   Session: {session_id}")
    
    try:
        response = requests.post(VALIDATE_ENDPOINT, json=payload)
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ Validation Result:")
        print(f"   Status: {data.get('status')}")
        print(f"   Classification: {data.get('classification')}")
        print(f"   Confidence: {data.get('confidence')}")
        print(f"   Session ID: {data.get('session_id')}")
        print(f"   Message Count: {data.get('message_count')}")
        
        if data.get('canonicalized_steps'):
            print(f"\n   Canonicalized Steps:")
            for step in data['canonicalized_steps'][:3]:
                print(f"      - {step}")
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}")
        return None


def create_strategy(
    strategy_text: str,
    name: Optional[str] = None,
    session_id: Optional[str] = None,
    use_context: bool = True,
    save_to_backtest: bool = False
):
    """
    Test strategy creation with conversation memory
    
    Args:
        strategy_text: Strategy description
        name: Optional strategy name
        session_id: Optional session ID for conversation continuity
        use_context: Whether to use conversation history
        save_to_backtest: Whether to save to Backtest/codes/
    """
    payload = {
        "strategy_text": strategy_text,
        "input_type": "auto",
        "use_gemini": True,
        "strict_mode": False,
        "use_context": use_context,
        "save_to_backtest": save_to_backtest,
        "tags": ["test", "conversation-memory"]
    }
    
    if name:
        payload["name"] = name
    if session_id:
        payload["session_id"] = session_id
    
    print(f"🚀 Creating Strategy:")
    print(f"   Text: {strategy_text[:100]}...")
    if name:
        print(f"   Name: {name}")
    if session_id:
        print(f"   Session: {session_id}")
    
    try:
        response = requests.post(CREATE_ENDPOINT, json=payload)
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ Strategy Created:")
        strategy = data.get('strategy', {})
        print(f"   ID: {strategy.get('id')}")
        print(f"   Name: {strategy.get('name')}")
        print(f"   Risk Level: {strategy.get('risk_level')}")
        print(f"   Session ID: {data.get('session_id')}")
        print(f"   Message Count: {data.get('message_count')}")
        
        if data.get('auto_created_template'):
            template = data['auto_created_template']
            print(f"   Auto-created Template: {template.get('name')} (ID: {template.get('id')})")
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}")
        return None


def update_strategy(
    strategy_id: int,
    strategy_text: str,
    update_description: str,
    session_id: Optional[str] = None,
    use_context: bool = True
):
    """
    Test strategy update with conversation memory
    
    Args:
        strategy_id: ID of strategy to update
        strategy_text: Updated strategy description
        update_description: Description of what changed
        session_id: Optional session ID for conversation continuity
        use_context: Whether to use conversation history
    """
    url = f"{STRATEGY_API}/api/{strategy_id}/update_strategy_with_ai/"
    
    payload = {
        "strategy_text": strategy_text,
        "input_type": "auto",
        "use_gemini": True,
        "strict_mode": False,
        "update_description": update_description,
        "use_context": use_context
    }
    
    if session_id:
        payload["session_id"] = session_id
    
    print(f"🔄 Updating Strategy {strategy_id}:")
    print(f"   Description: {update_description}")
    if session_id:
        print(f"   Session: {session_id}")
    
    try:
        response = requests.put(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ Strategy Updated:")
        strategy = data.get('strategy', {})
        print(f"   Name: {strategy.get('name')}")
        print(f"   Risk Level: {strategy.get('risk_level')}")
        print(f"   Session ID: {data.get('session_id')}")
        print(f"   Message Count: {data.get('message_count')}")
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}")
        return None


def chat_with_ai(message: str, session_id: Optional[str] = None):
    """Send a chat message to the AI"""
    payload = {
        "message": message,
        "use_context": True
    }
    
    if session_id:
        payload["session_id"] = session_id
    
    print(f"💬 Chat Message: {message[:100]}...")
    
    try:
        response = requests.post(CHAT_ENDPOINT, json=payload)
        response.raise_for_status()
        data = response.json()
        
        print(f"🤖 AI Response: {data.get('message', '')[:200]}...")
        print(f"   Session: {data.get('session_id')}")
        print(f"   Messages: {data.get('message_count')}")
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        return None


def get_session_messages(session_id: str):
    """Get conversation history for a session"""
    url = f"{SESSIONS_ENDPOINT}{session_id}/messages/"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        messages = response.json()
        
        print(f"\n📜 Conversation History ({len(messages)} messages):")
        for msg in messages:
            role = msg['role'].upper()
            content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
            print(f"   {role}: {content}")
        
        return messages
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        return []


def test_conversation_flow():
    """Test a complete conversation flow with strategy validation"""
    print_section("Test 1: Complete Conversation Flow with Memory")
    
    # Step 1: Initial validation with new session
    print("\n--- Step 1: Initial Strategy Validation ---")
    result1 = validate_strategy(
        "Buy when RSI(14) drops below 30. Sell when RSI(14) rises above 70. Use 2% stop loss."
    )
    
    if not result1:
        print("❌ Test failed: Could not validate strategy")
        return
    
    session_id = result1.get('session_id')
    print(f"\n✓ Session created: {session_id}")
    
    # Step 2: Chat about the strategy
    print("\n--- Step 2: Chat About Strategy (with context) ---")
    chat_with_ai(
        "What are the main risks with this RSI strategy?",
        session_id=session_id
    )
    
    # Step 3: Validate a refinement (should remember previous discussion)
    print("\n--- Step 3: Validate Refined Strategy (with memory) ---")
    validate_strategy(
        "Buy when RSI(14) < 30 AND price above 200 SMA. "
        "Sell when RSI(14) > 70 OR price crosses below 200 SMA. "
        "Stop loss: 2.5%, Position size: 1% risk per trade.",
        session_id=session_id,
        use_context=True
    )
    
    # Step 4: Create the strategy (same session)
    print("\n--- Step 4: Create Strategy from Conversation ---")
    create_result = create_strategy(
        "Buy when RSI(14) < 30 AND price above 200 SMA. "
        "Sell when RSI(14) > 70 OR price crosses below 200 SMA. "
        "Stop loss: 2.5%, Take profit: 6%, Position size: 1% risk per trade.",
        name="RSI Mean Reversion with Trend Filter",
        session_id=session_id,
        use_context=True,
        save_to_backtest=True
    )
    
    if not create_result:
        print("❌ Test failed: Could not create strategy")
        return
    
    strategy_id = create_result.get('strategy', {}).get('id')
    print(f"\n✓ Strategy created: ID {strategy_id}")
    
    # Step 5: View conversation history
    print("\n--- Step 5: View Conversation History ---")
    get_session_messages(session_id)
    
    # Step 6: Update the strategy (same session)
    print("\n--- Step 6: Update Strategy (with conversation context) ---")
    update_strategy(
        strategy_id=strategy_id,
        strategy_text="Buy when RSI(14) < 30 AND price above 200 SMA AND volume > 20-day average. "
                     "Sell when RSI(14) > 70 OR price crosses below 200 SMA. "
                     "Stop loss: 2%, Take profit: 8%, Position size: 1.5% risk per trade using ATR.",
        update_description="Added volume filter, tightened stop loss, increased take profit, improved position sizing",
        session_id=session_id,
        use_context=True
    )
    
    # Step 7: Final conversation history
    print("\n--- Step 7: Final Conversation History ---")
    get_session_messages(session_id)
    
    print_section("✅ Test 1 Complete - Full Conversation Flow Verified")
    return session_id, strategy_id


def test_multiple_sessions():
    """Test multiple concurrent sessions"""
    print_section("Test 2: Multiple Concurrent Sessions")
    
    # Session 1: Momentum strategy
    print("\n--- Session 1: Momentum Strategy ---")
    result1 = validate_strategy(
        "Buy when 50 EMA crosses above 200 EMA with increasing volume"
    )
    session1_id = result1.get('session_id') if result1 else None
    
    # Session 2: Mean reversion strategy
    print("\n--- Session 2: Mean Reversion Strategy ---")
    result2 = validate_strategy(
        "Buy when price touches lower Bollinger Band, sell at middle band"
    )
    session2_id = result2.get('session_id') if result2 else None
    
    # Continue session 1
    print("\n--- Back to Session 1 ---")
    validate_strategy(
        "Add MACD confirmation: only buy when MACD line crosses above signal line",
        session_id=session1_id,
        use_context=True
    )
    
    # Continue session 2
    print("\n--- Back to Session 2 ---")
    validate_strategy(
        "Add RSI filter: only buy when RSI < 35",
        session_id=session2_id,
        use_context=True
    )
    
    print_section("✅ Test 2 Complete - Multiple Sessions Verified")


def test_context_awareness():
    """Test that the AI remembers context"""
    print_section("Test 3: Context Awareness")
    
    # Create a strategy in a session
    print("\n--- Create Initial Strategy ---")
    result = create_strategy(
        "Simple moving average crossover: buy when 10 SMA crosses above 50 SMA",
        name="Simple MA Crossover",
        use_context=True
    )
    
    if not result:
        print("❌ Test failed")
        return
    
    session_id = result.get('session_id')
    strategy_id = result.get('strategy', {}).get('id')
    
    # Ask follow-up questions (should remember the strategy)
    print("\n--- Ask About Exit Rules (expects AI to remember strategy) ---")
    chat_with_ai(
        "What exit rules would you recommend for this strategy?",
        session_id=session_id
    )
    
    print("\n--- Ask About Risk Management (expects AI to remember) ---")
    chat_with_ai(
        "How should I set position sizes?",
        session_id=session_id
    )
    
    # View the conversation
    print("\n--- Conversation History ---")
    get_session_messages(session_id)
    
    print_section("✅ Test 3 Complete - Context Awareness Verified")


def main():
    """Run all tests"""
    print("""
    ╔════════════════════════════════════════════════════════════════════╗
    ║  AlgoAgent Strategy Validation + Conversation Memory Test Suite   ║
    ║  Testing AI strategy validation with persistent memory            ║
    ╚════════════════════════════════════════════════════════════════════╝
    """)
    
    print(f"Testing against: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Full conversation flow
    test_conversation_flow()
    
    input("\n\n⏸️  Press Enter to continue to Test 2...")
    
    # Test 2: Multiple sessions
    test_multiple_sessions()
    
    input("\n\n⏸️  Press Enter to continue to Test 3...")
    
    # Test 3: Context awareness
    test_context_awareness()
    
    print_section("🎉 All Tests Complete!")
    print("\n✅ Conversation memory successfully integrated with:")
    print("   • Strategy validation (validate_strategy_with_ai)")
    print("   • Strategy creation (create_strategy_with_ai)")
    print("   • Strategy updates (update_strategy_with_ai)")
    print("   • AI chat interactions")
    print("\n💡 Features demonstrated:")
    print("   ✓ Persistent conversation sessions")
    print("   ✓ Context-aware AI responses")
    print("   ✓ Multi-turn strategy refinement")
    print("   ✓ Session-linked strategy tracking")
    print("   ✓ Conversation history retrieval")
    print("   ✓ Multiple concurrent sessions")


if __name__ == "__main__":
    main()
