# Conversation Memory Integration - Quick Reference

## 🎯 Overview

All AI strategy validation and creation endpoints now support **conversation memory** using LangChain and SQLite storage. This allows the AI to maintain context across multiple interactions.

## 🔑 Key Features

- **Persistent Sessions**: Each conversation has a unique `session_id`
- **Context Awareness**: AI remembers previous discussions in the same session
- **Strategy Linking**: Sessions can be linked to specific strategies
- **Message History**: Full conversation history stored in database
- **Multi-turn Refinement**: Build strategies iteratively with AI assistance

## 📝 New API Fields

All these endpoints now accept optional conversation memory fields:

### 1. Validate Strategy with AI
`POST /api/strategies/api/validate_strategy_with_ai/`

```json
{
  "strategy_text": "Buy when RSI < 30...",
  "input_type": "auto",
  "use_gemini": true,
  "strict_mode": false,
  
  // NEW: Conversation memory fields
  "session_id": "chat_abc123",  // Optional: use existing session
  "use_context": true           // Optional: use conversation history
}
```

**Response includes:**
```json
{
  "status": "success",
  "canonicalized_steps": [...],
  "classification": "...",
  
  // NEW: Session tracking
  "session_id": "chat_abc123",
  "message_count": 5,
  "context_used": true
}
```

### 2. Create Strategy with AI
`POST /api/strategies/api/create_strategy_with_ai/`

```json
{
  "strategy_text": "Buy when RSI < 30...",
  "name": "RSI Strategy",
  "input_type": "auto",
  "use_gemini": true,
  
  // NEW: Conversation memory fields
  "session_id": "chat_abc123",  // Optional: continue existing conversation
  "use_context": true           // Optional: use conversation history
}
```

**Response includes:**
```json
{
  "success": true,
  "strategy": {...},
  "ai_validation": {...},
  
  // NEW: Session tracking
  "session_id": "chat_abc123",
  "message_count": 7
}
```

### 3. Update Strategy with AI
`PUT /api/strategies/api/{strategy_id}/update_strategy_with_ai/`

```json
{
  "strategy_text": "Updated strategy...",
  "update_description": "Added volume filter",
  
  // NEW: Conversation memory fields
  "session_id": "chat_abc123",  // Optional: track updates in conversation
  "use_context": true           // Optional: use conversation history
}
```

## 🔄 Typical Workflow

### Scenario 1: Build a Strategy Iteratively

```bash
# Step 1: Initial validation (creates new session)
POST /api/strategies/api/validate_strategy_with_ai/
{
  "strategy_text": "Buy when RSI drops below 30"
}
# Response: { "session_id": "chat_xyz789", ... }

# Step 2: Chat about the strategy
POST /api/strategies/chat/chat/
{
  "message": "What are the risks with this strategy?",
  "session_id": "chat_xyz789"
}

# Step 3: Refine based on AI feedback (same session)
POST /api/strategies/api/validate_strategy_with_ai/
{
  "strategy_text": "Buy when RSI < 30 AND price above 200 SMA",
  "session_id": "chat_xyz789",
  "use_context": true  // AI remembers previous discussion
}

# Step 4: Create the strategy (same session)
POST /api/strategies/api/create_strategy_with_ai/
{
  "strategy_text": "Buy when RSI < 30 AND price above 200 SMA. Stop loss 2%.",
  "name": "RSI with Trend Filter",
  "session_id": "chat_xyz789",
  "use_context": true
}
# Response: { "strategy": { "id": 5 }, "session_id": "chat_xyz789" }

# Step 5: Later, update the strategy (same session)
PUT /api/strategies/api/5/update_strategy_with_ai/
{
  "strategy_text": "Buy when RSI < 30 AND price above 200 SMA AND volume > avg. Stop loss 2%, TP 6%.",
  "update_description": "Added volume filter and take profit",
  "session_id": "chat_xyz789",
  "use_context": true
}

# Step 6: View conversation history
GET /api/strategies/chat/chat_xyz789/messages/
```

### Scenario 2: Parallel Strategy Development

```bash
# Session 1: Momentum strategy
POST /api/strategies/api/validate_strategy_with_ai/
{
  "strategy_text": "Buy on EMA crossover"
}
# Response: { "session_id": "chat_aaa111" }

# Session 2: Mean reversion strategy
POST /api/strategies/api/validate_strategy_with_ai/
{
  "strategy_text": "Buy at Bollinger Band lower"
}
# Response: { "session_id": "chat_bbb222" }

# Continue session 1
POST /api/strategies/api/validate_strategy_with_ai/
{
  "strategy_text": "Buy on EMA crossover with MACD confirmation",
  "session_id": "chat_aaa111",
  "use_context": true
}

# Continue session 2
POST /api/strategies/api/validate_strategy_with_ai/
{
  "strategy_text": "Buy at Bollinger Band lower with RSI < 35",
  "session_id": "chat_bbb222",
  "use_context": true
}
```

## 📊 Session Management Endpoints

### List All Sessions
```bash
GET /api/strategies/chat/
```

### Get Session Messages
```bash
GET /api/strategies/chat/{session_id}/messages/
```

### Send Chat Message
```bash
POST /api/strategies/chat/chat/
{
  "message": "How can I improve this strategy?",
  "session_id": "chat_abc123",  // Optional
  "use_context": true
}
```

## 💡 Best Practices

1. **Let session_id auto-generate** on first request, then reuse it
2. **Set use_context=true** when building on previous discussions
3. **Use update_description** to document strategy evolution
4. **Link strategies to sessions** for complete development history
5. **Review conversation history** to track decision-making process

## 🔍 Example Test Flow

```python
import requests

BASE_URL = "http://localhost:8000/api/strategies"

# 1. Validate initial idea
response = requests.post(f"{BASE_URL}/api/validate_strategy_with_ai/", json={
    "strategy_text": "Buy when RSI < 30, sell when RSI > 70"
})
session_id = response.json()["session_id"]

# 2. Chat about it
requests.post(f"{BASE_URL}/chat/chat/", json={
    "message": "What timeframe works best for RSI strategies?",
    "session_id": session_id
})

# 3. Refine based on chat
requests.post(f"{BASE_URL}/api/validate_strategy_with_ai/", json={
    "strategy_text": "Buy when RSI < 30 on 1-hour chart. Sell when RSI > 70.",
    "session_id": session_id,
    "use_context": True
})

# 4. Create the strategy
response = requests.post(f"{BASE_URL}/api/create_strategy_with_ai/", json={
    "strategy_text": "Buy when RSI(14) < 30 on 1H chart. Sell when RSI > 70. Stop loss 2%.",
    "name": "RSI Mean Reversion 1H",
    "session_id": session_id,
    "use_context": True
})

strategy_id = response.json()["strategy"]["id"]

# 5. View conversation
messages = requests.get(f"{BASE_URL}/chat/{session_id}/messages/")
print(f"Conversation has {len(messages.json())} messages")
```

## 🎓 Migration Notes

**Old way (no memory):**
```json
POST /api/strategies/api/validate_strategy_with_ai/
{
  "strategy_text": "Buy when RSI < 30"
}
```

**New way (with memory - backward compatible):**
```json
POST /api/strategies/api/validate_strategy_with_ai/
{
  "strategy_text": "Buy when RSI < 30",
  "session_id": "chat_abc123",  // NEW: optional
  "use_context": true           // NEW: optional, defaults to true
}
```

The old way still works! The API is **100% backward compatible**. Session tracking is optional but recommended for multi-turn interactions.

## 📚 Related Documentation

- See `test_conversation_memory.py` for chat-only examples
- See `test_strategy_validation_memory.py` for validation + memory examples
- See `CONVERSATION_MEMORY_SUMMARY.md` for implementation details
