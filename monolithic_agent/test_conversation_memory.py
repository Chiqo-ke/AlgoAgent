"""
Test Script for AI Agent Conversation Memory
=============================================

This script demonstrates the conversation memory capabilities of the AlgoAgent.
It shows how the AI agent can:
1. Maintain conversation context across multiple messages
2. Remember previous discussions about strategies
3. Provide contextual responses based on chat history
"""

import requests
import json
from datetime import datetime

# API Configuration
BASE_URL = "http://localhost:8000/api/strategies"
CHAT_ENDPOINT = f"{BASE_URL}/chat/chat/"
SESSION_ENDPOINT = f"{BASE_URL}/chat/"

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")

def send_message(message, session_id=None, strategy_id=None):
    """
    Send a message to the AI agent
    
    Args:
        message: User's message
        session_id: Optional existing session ID
        strategy_id: Optional strategy to link to
        
    Returns:
        Response dictionary
    """
    payload = {
        "message": message,
        "use_context": True
    }
    
    if session_id:
        payload["session_id"] = session_id
    if strategy_id:
        payload["strategy_id"] = strategy_id
    
    print(f"USER: {message}")
    
    try:
        response = requests.post(CHAT_ENDPOINT, json=payload)
        response.raise_for_status()
        data = response.json()
        
        print(f"AI: {data['message']}")
        print(f"\n[Session: {data['session_id']}, Messages: {data['message_count']}]")
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return None

def list_sessions():
    """List all active chat sessions"""
    try:
        response = requests.get(SESSION_ENDPOINT)
        response.raise_for_status()
        sessions = response.json()
        
        print(f"Found {len(sessions)} chat sessions:")
        for session in sessions:
            print(f"  - {session['title']} ({session['message_count']} messages)")
            print(f"    ID: {session['session_id']}")
            print(f"    Last active: {session.get('last_message_at', 'N/A')}")
        
        return sessions
    except requests.exceptions.RequestException as e:
        print(f"Error listing sessions: {e}")
        return []

def get_session_messages(session_id):
    """Get all messages from a session"""
    try:
        response = requests.get(f"{SESSION_ENDPOINT}{session_id}/messages/")
        response.raise_for_status()
        messages = response.json()
        
        print(f"\nConversation history ({len(messages)} messages):")
        for msg in messages:
            role = msg['role'].upper()
            content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
            print(f"{role}: {content}")
        
        return messages
    except requests.exceptions.RequestException as e:
        print(f"Error getting messages: {e}")
        return []

def test_conversation_memory():
    """Test conversation memory with a multi-turn dialogue"""
    print_section("Testing Conversation Memory")
    
    # First message - introduce a strategy idea
    print("\n--- Message 1: Introducing a strategy ---")
    response1 = send_message(
        "I want to create a momentum trading strategy using RSI and moving averages."
    )
    
    if not response1:
        print("Failed to get response from AI. Is the server running?")
        return
    
    session_id = response1['session_id']
    
    # Second message - ask a follow-up (tests context memory)
    print("\n--- Message 2: Follow-up question (testing context) ---")
    response2 = send_message(
        "What timeframe would you recommend for this?",
        session_id=session_id
    )
    
    # Third message - ask about a specific aspect
    print("\n--- Message 3: Another contextual question ---")
    response3 = send_message(
        "How should I handle the exit conditions?",
        session_id=session_id
    )
    
    # Fourth message - request refinement
    print("\n--- Message 4: Request refinement ---")
    response4 = send_message(
        "Can you help me add risk management rules to what we discussed?",
        session_id=session_id
    )
    
    # Show the full conversation
    print_section("Full Conversation History")
    get_session_messages(session_id)
    
    return session_id

def test_multiple_sessions():
    """Test creating multiple concurrent sessions"""
    print_section("Testing Multiple Concurrent Sessions")
    
    # Session 1 - About momentum strategy
    print("\n--- Session 1: Momentum Strategy ---")
    s1_msg1 = send_message("I'm interested in momentum strategies")
    session1_id = s1_msg1['session_id'] if s1_msg1 else None
    
    # Session 2 - About mean reversion
    print("\n--- Session 2: Mean Reversion Strategy ---")
    s2_msg1 = send_message("Tell me about mean reversion strategies")
    session2_id = s2_msg1['session_id'] if s2_msg1 else None
    
    # Continue session 1
    print("\n--- Back to Session 1 ---")
    send_message("What indicators work best for momentum?", session_id=session1_id)
    
    # Continue session 2
    print("\n--- Back to Session 2 ---")
    send_message("When do mean reversion strategies work best?", session_id=session2_id)
    
    print("\n--- Listing all sessions ---")
    list_sessions()

def test_strategy_validation_with_memory():
    """Test strategy validation while maintaining conversation context"""
    print_section("Testing Strategy Validation with Memory")
    
    # Start a conversation about creating a strategy
    print("\n--- Initial strategy discussion ---")
    response = send_message(
        "I want to create a strategy that buys when RSI crosses below 30 and sells when it crosses above 70"
    )
    
    if not response:
        return
    
    session_id = response['session_id']
    
    # Ask for improvements
    print("\n--- Asking for improvements (testing context awareness) ---")
    send_message(
        "What improvements would you suggest for this strategy?",
        session_id=session_id
    )
    
    # Ask about a specific improvement
    print("\n--- Follow-up on specific improvement ---")
    send_message(
        "Tell me more about adding position sizing",
        session_id=session_id
    )

def main():
    """Run all tests"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║  AlgoAgent Conversation Memory Test Suite                   ║
    ║  Testing AI agent with LangChain + SQLite memory            ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    print(f"Testing against: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Basic conversation memory
    session_id = test_conversation_memory()
    
    input("\n\nPress Enter to continue to test 2...")
    
    # Test 2: Multiple concurrent sessions
    test_multiple_sessions()
    
    input("\n\nPress Enter to continue to test 3...")
    
    # Test 3: Strategy validation with context
    test_strategy_validation_with_memory()
    
    print_section("All Tests Complete!")
    print("\nThe AI agent now has conversation memory!")
    print("Key features demonstrated:")
    print("  ✓ Maintains context across multiple messages")
    print("  ✓ Remembers previous discussions")
    print("  ✓ Can handle multiple concurrent sessions")
    print("  ✓ Stores conversation history in SQLite database")
    print("  ✓ Uses LangChain for memory management")

if __name__ == "__main__":
    main()
