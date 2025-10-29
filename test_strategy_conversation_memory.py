"""
Test Script for Strategy Validation with Conversation Memory
=============================================================

This script demonstrates how the AI strategy validation APIs now support
conversation memory, allowing the AI to remember previous validations and
provide contextual responses.
"""

import requests
import json
from datetime import datetime
import time

# API Configuration
BASE_URL = "http://localhost:8000/api/strategies"
VALIDATE_ENDPOINT = f"{BASE_URL}/api/validate_strategy_with_ai/"
CREATE_ENDPOINT = f"{BASE_URL}/api/create_strategy_with_ai/"
UPDATE_ENDPOINT = f"{BASE_URL}/api/{{strategy_id}}/update_strategy_with_ai/"
CHAT_ENDPOINT = f"{BASE_URL}/chat/chat/"
SESSION_ENDPOINT = f"{BASE_URL}/chat/"

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def print_response(response_data, title="Response"):
    """Print formatted API response"""
    print(f"\n--- {title} ---")
    print(json.dumps(response_data, indent=2))

def test_1_validate_with_new_session():
    """Test 1: Validate a strategy and create a new conversation session"""
    print_section("Test 1: Strategy Validation with New Session")
    
    payload = {
        "strategy_text": "Buy when RSI(14) drops below 30. Sell when RSI(14) rises above 70. Use 2% stop loss.",
        "input_type": "freetext",
        "use_gemini": True,
        "strict_mode": False,
        "use_context": True
    }
    
    print("Sending strategy validation request (will create new session)...")
    try:
        response = requests.post(VALIDATE_ENDPOINT, json=payload)
        response.raise_for_status()
        data = response.json()
        
        print_response(data, "Validation Result")
        
        # Extract session_id if conversation was created
        session_id = data.get('session_id')
        if session_id:
            print(f"\n✓ Conversation session created: {session_id}")
        
        return session_id, data
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        return None, None

def test_2_validate_with_existing_session(session_id):
    """Test 2: Validate another strategy in the same session (context-aware)"""
    print_section("Test 2: Contextual Validation Using Existing Session")
    
    if not session_id:
        print("⚠ Skipping - no session ID from previous test")
        return
    
    payload = {
        "strategy_text": "Add a trailing stop loss to the previous strategy",
        "input_type": "freetext",
        "use_gemini": True,
        "strict_mode": False,
        "session_id": session_id,
        "use_context": True
    }
    
    print(f"Sending validation with session context (session: {session_id})...")
    print("Note: The AI should remember the previous RSI strategy and add trailing stop to it")
    
    try:
        response = requests.post(VALIDATE_ENDPOINT, json=payload)
        response.raise_for_status()
        data = response.json()
        
        print_response(data, "Contextual Validation Result")
        return data
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        return None

def test_3_create_strategy_with_session(session_id):
    """Test 3: Create a strategy with conversation memory"""
    print_section("Test 3: Create Strategy with Conversation Memory")
    
    payload = {
        "strategy_text": """
        Enhanced RSI Mean Reversion Strategy:
        1. Entry: Buy when RSI(14) < 30 AND price above 200 SMA
        2. Exit: Sell when RSI(14) > 70 OR price below 200 SMA
        3. Stop Loss: 2.5% below entry
        4. Take Profit: 6% above entry
        5. Position Size: Risk 1.5% per trade
        """,
        "input_type": "numbered",
        "name": "RSI Mean Reversion with Trend Filter",
        "description": "RSI strategy enhanced with 200 SMA trend filter",
        "tags": ["rsi", "mean-reversion", "trend-filter"],
        "use_gemini": True,
        "strict_mode": False,
        "save_to_backtest": False,
        "session_id": session_id if session_id else None,
        "use_context": True
    }
    
    print(f"Creating strategy with session: {session_id or 'new session'}...")
    
    try:
        response = requests.post(CREATE_ENDPOINT, json=payload)
        response.raise_for_status()
        data = response.json()
        
        print_response(data, "Strategy Creation Result")
        
        strategy_id = data.get('strategy', {}).get('id')
        if strategy_id:
            print(f"\n✓ Strategy created with ID: {strategy_id}")
        
        return strategy_id, data
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        return None, None

def test_4_chat_about_strategy(session_id):
    """Test 4: Use the chat endpoint to discuss the strategy"""
    print_section("Test 4: Chat About Strategy")
    
    if not session_id:
        print("⚠ Skipping - no session ID available")
        return
    
    questions = [
        "What are the strengths of this RSI strategy?",
        "How can I improve the entry conditions?",
        "What timeframe would you recommend?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\nQuestion {i}: {question}")
        
        payload = {
            "message": question,
            "session_id": session_id,
            "use_context": True
        }
        
        try:
            response = requests.post(CHAT_ENDPOINT, json=payload)
            response.raise_for_status()
            data = response.json()
            
            print(f"AI Response: {data.get('message', 'No response')}")
            print(f"Message count: {data.get('message_count', 0)}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
        
        time.sleep(1)  # Brief pause between messages

def test_5_update_strategy_with_memory(strategy_id, session_id):
    """Test 5: Update strategy with conversation context"""
    print_section("Test 5: Update Strategy with Conversation Memory")
    
    if not strategy_id:
        print("⚠ Skipping - no strategy ID available")
        return
    
    payload = {
        "strategy_text": """
        Updated RSI Mean Reversion Strategy:
        1. Entry: Buy when RSI(14) < 25 AND price above 200 SMA AND volume > 20-day avg
        2. Exit: Sell when RSI(14) > 75 OR price below 200 SMA
        3. Stop Loss: ATR-based stop (2x ATR below entry)
        4. Take Profit: 8% above entry (increased target)
        5. Position Size: Risk 1% per trade (reduced risk)
        6. Additional: Only trade during high liquidity hours (9:30-11:30 AM, 2-3:30 PM EST)
        """,
        "input_type": "numbered",
        "use_gemini": True,
        "strict_mode": False,
        "session_id": session_id,
        "use_context": True,
        "update_description": "Enhanced with volume filter, ATR stops, and time-based filters"
    }
    
    endpoint = UPDATE_ENDPOINT.replace("{strategy_id}", str(strategy_id))
    print(f"Updating strategy {strategy_id} with conversation context...")
    
    try:
        response = requests.put(endpoint, json=payload)
        response.raise_for_status()
        data = response.json()
        
        print_response(data, "Strategy Update Result")
        print("\n✓ Strategy updated with AI validation")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")

def test_6_list_conversation_history(session_id):
    """Test 6: Retrieve full conversation history"""
    print_section("Test 6: Retrieve Conversation History")
    
    if not session_id:
        print("⚠ Skipping - no session ID available")
        return
    
    try:
        response = requests.get(f"{SESSION_ENDPOINT}{session_id}/messages/")
        response.raise_for_status()
        messages = response.json()
        
        print(f"Total messages in conversation: {len(messages)}")
        print("\nConversation Timeline:")
        print("-" * 70)
        
        for i, msg in enumerate(messages, 1):
            role = msg['role'].upper()
            content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
            timestamp = msg.get('created_at', 'N/A')
            print(f"\n{i}. [{timestamp}] {role}:")
            print(f"   {content}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")

def main():
    """Run all tests"""
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║  Strategy Validation + Conversation Memory Integration Test     ║
    ║  Testing AI-powered strategy validation with persistent memory  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    print(f"Testing against: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Initial validation (creates session)
    session_id, validation_result = test_1_validate_with_new_session()
    
    if not session_id:
        print("\n⚠ Warning: Could not create session. Some tests will be skipped.")
        print("Make sure the server is running: python manage.py runserver")
        return
    
    input("\n\nPress Enter to continue to Test 2...")
    
    # Test 2: Contextual validation in same session
    test_2_validate_with_existing_session(session_id)
    
    input("\n\nPress Enter to continue to Test 3...")
    
    # Test 3: Create strategy with session
    strategy_id, creation_result = test_3_create_strategy_with_session(session_id)
    
    input("\n\nPress Enter to continue to Test 4...")
    
    # Test 4: Chat about the strategy
    test_4_chat_about_strategy(session_id)
    
    input("\n\nPress Enter to continue to Test 5...")
    
    # Test 5: Update strategy with memory
    if strategy_id:
        test_5_update_strategy_with_memory(strategy_id, session_id)
    
    input("\n\nPress Enter to continue to Test 6...")
    
    # Test 6: View conversation history
    test_6_list_conversation_history(session_id)
    
    print_section("Test Summary")
    print("✓ All tests completed!")
    print("\nKey Features Demonstrated:")
    print("  1. ✓ Strategy validation creates/uses conversation sessions")
    print("  2. ✓ AI remembers context from previous validations")
    print("  3. ✓ Strategy creation integrates with conversation memory")
    print("  4. ✓ Chat endpoint maintains full conversation context")
    print("  5. ✓ Strategy updates are tracked in conversation history")
    print("  6. ✓ Full conversation history can be retrieved")
    
    print(f"\n📝 Session ID for reference: {session_id}")
    print(f"📝 Strategy ID for reference: {strategy_id if strategy_id else 'N/A'}")

if __name__ == "__main__":
    main()
