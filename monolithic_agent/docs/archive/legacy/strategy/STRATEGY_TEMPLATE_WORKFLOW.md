# Strategy Template Auto-Creation & Sync Workflow

## Overview

The AlgoAgent Strategy API now supports an intelligent template system that automatically tracks strategy evolution during AI-powered chat sessions. This feature allows:

1. **Users** to start creating strategies without needing to select a template
2. **AI Agents** to maintain context and chat history for each strategy
3. **Automatic synchronization** of template data with strategy changes

---

## How It Works

### 1. Creating a Strategy (User Perspective)

When a user creates a strategy using the `/api/create_strategy/` endpoint:

**Option A: Without Template (Auto-Creation)**
```json
POST {{strategyApiBase}}/api/create_strategy/
{
    "name": "My Momentum Strategy",
    "description": "A custom momentum trading strategy",
    "strategy_code": "def initialize(context):\n    pass",
    "parameters": {
        "asset": "AAPL",
        "lookback": 20
    },
    "tags": ["momentum", "custom"],
    "timeframe": "1d",
    "risk_level": "medium"
}
```

**What Happens:**
- ✅ Strategy is created with ID (e.g., `1`)
- ✅ A `StrategyTemplate` is **automatically created** with:
  - Unique name: `"Template: My Momentum Strategy"`
  - Link back to the strategy (`linked_strategy_id = 1`)
  - Initial code and parameters stored
  - Empty chat history
  - `is_system_template = False`
- ✅ Response includes template info:
```json
{
    "id": 1,
    "name": "My Momentum Strategy",
    "template": 5,  // Auto-created template ID
    "auto_created_template": {
        "id": 5,
        "name": "Template: My Momentum Strategy",
        "message": "Template automatically created for tracking strategy evolution"
    }
}
```

**Option B: With Existing Template**
```json
POST {{strategyApiBase}}/api/create_strategy/
{
    "template_id": 2,  // Use existing template
    "name": "RSI Strategy from Template",
    "strategy_code": "...",
    ...
}
```

---

### 2. AI Agent Workflow

The AI agent (e.g., Gemini) can now interact with strategies through an iterative development process:

#### Step 1: User Starts Conversation
```
User: "Create a momentum trading strategy for AAPL"
```

#### Step 2: Agent Creates Initial Strategy
```http
POST /api/strategies/api/create_strategy/
{
    "name": "AAPL Momentum Strategy",
    "description": "Initial momentum strategy based on user request",
    "strategy_code": "# Initial code...",
    ...
}
```

**Response includes auto-created template ID: `5`**

#### Step 3: User Requests Changes
```
User: "Add RSI confirmation to the entry logic"
```

#### Step 4: Agent Syncs Template with Changes
```http
POST /api/strategies/templates/5/sync_from_strategy/
{
    "strategy_code": "# Updated code with RSI...",
    "parameters": {
        "asset": "AAPL",
        "lookback": 20,
        "rsi_period": 14,
        "rsi_threshold": 30
    },
    "chat_message": "Added RSI confirmation: Buy signals now require RSI < 30",
    "description": "AAPL Momentum Strategy with RSI confirmation"
}
```

**What This Does:**
- Updates `template.latest_strategy_code`
- Updates `template.template_code`
- Merges new parameters into `parameters_schema`
- Appends chat message to `chat_history` with timestamp
- Keeps last 50 chat messages to prevent unbounded growth

#### Step 5: Agent Retrieves Context (for next message)
```http
GET /api/strategies/templates/5/get_context/
```

**Response:**
```json
{
    "id": 5,
    "name": "Template: AAPL Momentum Strategy",
    "latest_strategy_code": "# Updated code with RSI...",
    "latest_parameters": {...},
    "chat_history": [
        {
            "timestamp": "2025-10-28T10:30:00Z",
            "message": "Added RSI confirmation: Buy signals now require RSI < 30",
            "user": "algotrader"
        }
    ],
    "linked_strategy": {
        "id": 1,
        "name": "AAPL Momentum Strategy",
        "status": "draft",
        "version": "1.0.0",
        ...
    },
    "context_summary": {
        "chat_messages_count": 1,
        "last_update": "2025-10-28T10:30:00Z",
        "is_active": true,
        "template_type": "user-generated"
    }
}
```

---

## API Endpoints

### Create Strategy (Auto-Template)
```
POST /api/strategies/api/create_strategy/
```

**Parameters:**
- `template_id` (optional): Use existing template, or omit for auto-creation
- `skip_template_creation` (optional): Set to `true` to disable auto-creation
- Standard strategy fields: `name`, `description`, `strategy_code`, `parameters`, etc.

**Response:** Standard strategy object + `auto_created_template` info

---

### Sync Template from Strategy Updates
```
POST /api/strategies/templates/{id}/sync_from_strategy/
```

**Purpose:** AI agent updates template with latest strategy changes

**Parameters:**
```json
{
    "strategy_code": "string (optional)",
    "parameters": "object (optional)",
    "chat_message": "string (optional) - summary of changes",
    "description": "string (optional)",
    "force_update": "boolean (optional) - allow updating system templates"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Template synchronized successfully",
    "template": {...}
}
```

**Protection:** System templates (`is_system_template=true`) cannot be updated unless `force_update=true`

---

### Get Template Context
```
GET /api/strategies/templates/{id}/get_context/
```

**Purpose:** Retrieve full context for AI agent decision-making

**Response:** Template with chat history, linked strategy info, and summary statistics

---

## Database Schema Changes

### StrategyTemplate Model (Enhanced)

```python
class StrategyTemplate(models.Model):
    # Original fields
    name = CharField(max_length=200, unique=True)
    description = TextField()
    category = CharField(max_length=100)
    template_code = TextField()
    parameters_schema = JSONField(default=dict)
    is_active = BooleanField(default=True)
    
    # NEW: Link to strategy
    linked_strategy = ForeignKey(
        'Strategy', 
        null=True, 
        blank=True,
        related_name='linked_template'
    )
    
    # NEW: Template type
    is_system_template = BooleanField(default=False)
    
    # NEW: Latest state tracking
    latest_strategy_code = TextField(blank=True)
    latest_parameters = JSONField(default=dict)
    chat_history = JSONField(default=list)  # Last 50 messages
    
    created_by = ForeignKey(User, null=True, blank=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

### ChatSession Model (Enhanced)

```python
class ChatSession(models.Model):
    user = ForeignKey(User, on_delete=CASCADE)
    ai_context = ForeignKey(AIContext, null=True, blank=True)
    
    session_id = CharField(max_length=100, unique=True)
    title = CharField(max_length=200)
    
    # NEW: Link to strategy template
    strategy_template_id = IntegerField(null=True, blank=True)
    
    messages = JSONField(default=list)
    generated_strategies = JSONField(default=list)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

---

## Use Cases

### Use Case 1: First-Time User Creating Strategy
```
1. User sends first message: "Create a simple moving average strategy"
2. AI creates strategy WITHOUT template_id
3. System auto-creates template
4. AI can now track conversation history in template.chat_history
5. Future modifications update the template automatically
```

### Use Case 2: Editing an Existing Strategy
```
1. User: "Modify my AAPL strategy to use 50-day MA instead of 20-day"
2. AI retrieves template context (GET /templates/{id}/get_context/)
3. AI sees chat_history showing previous 20-day MA decision
4. AI updates strategy code
5. AI syncs template (POST /templates/{id}/sync_from_strategy/)
6. Template now has full history of changes
```

### Use Case 3: User Edits Strategy via UI
```
1. User manually edits strategy code in web UI
2. Frontend can call /templates/{id}/sync_from_strategy/
3. Template stays in sync with UI changes
4. AI agent can see user's manual modifications in next chat
```

---

## Migration Instructions

To apply these database changes:

```bash
cd AlgoAgent
python manage.py makemigrations strategy_api auth_api
python manage.py migrate
```

This will create migrations for:
- New fields in `StrategyTemplate`
- New field in `ChatSession`

---

## Benefits

✅ **No Template Selection Required**: Users can start immediately  
✅ **Full Chat History**: AI remembers entire conversation  
✅ **Automatic Sync**: No manual template management needed  
✅ **User Editable**: Users can edit strategies via UI, syncs to template  
✅ **Context Preservation**: AI always has full context for better decisions  
✅ **Backward Compatible**: Existing templates still work  

---

## Example Postman Flow

1. **Create Strategy (Auto-Template)**
   - Request: `Create Strategy (Simple - Auto Template)`
   - Note the `auto_created_template.id` in response

2. **Sync Template After Changes**
   - Request: `Sync Template from Strategy (AI Agent)`
   - Use template ID from step 1

3. **Get Full Context**
   - Request: `Get Template Context (AI Agent)`
   - See chat history and linked strategy info

---

## Notes for AI Agents

1. **Always check for template_id in strategy response** after creation
2. **Use sync_from_strategy after each significant change** to maintain history
3. **Use get_context before generating responses** to understand full context
4. **Include meaningful chat_message** when syncing (helps users understand changes)
5. **Check chat_history** to avoid repeating previous suggestions

---

## Security Considerations

- System templates (`is_system_template=true`) protected from accidental updates
- User authentication required for syncing (if enabled)
- Chat history limited to 50 messages to prevent DoS
- Template names must be unique

---

## Future Enhancements

- [ ] Add template versioning
- [ ] Add template branching (create variant from existing)
- [ ] Add template comparison tools
- [ ] Add chat message search/filtering
- [ ] Add automatic summary generation from chat history
