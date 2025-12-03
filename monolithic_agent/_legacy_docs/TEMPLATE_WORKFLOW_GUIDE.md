# Template Workflow Guide

## Overview

The AlgoAgent strategy system now supports a dual-purpose template mechanism that enables:

1. **Pre-built Templates**: System templates for quick-start strategy development
2. **Auto-Generated Templates**: Dynamic templates that track strategy evolution through AI chat sessions

## How It Works

### For Users Starting Strategy Development

When a user creates their first strategy without specifying a `template_id`, the system automatically:

1. Creates a new strategy
2. Generates a linked `StrategyTemplate` to track the strategy's evolution
3. Links the template back to the strategy for bidirectional reference
4. Returns both the strategy and template information

**Example Request:**
```json
POST {{strategyApiBase}}/api/create_strategy/
{
    "name": "My Momentum Strategy",
    "description": "A custom momentum-based trading strategy",
    "strategy_code": "def initialize(context):\n    context.asset = 'AAPL'\n...",
    "parameters": {
        "asset": "AAPL",
        "lookback": 20
    },
    "tags": ["momentum", "custom"],
    "timeframe": "1d",
    "risk_level": "medium"
}
```

**Response:**
```json
{
    "id": 1,
    "name": "My Momentum Strategy",
    "template": 1,
    "auto_created_template": {
        "id": 1,
        "name": "Template: My Momentum Strategy",
        "message": "Template automatically created for tracking strategy evolution"
    },
    ...
}
```

### For AI Agents

The AI agent can now:

#### 1. Get Full Context
Retrieve complete context including chat history and latest strategy state:

```json
GET {{strategyApiBase}}/templates/1/get_context/
```

**Response includes:**
- Complete template information
- Chat history
- Linked strategy details
- Context summary statistics

#### 2. Update Template with Strategy Changes
After each significant chat interaction where the strategy is modified:

```json
POST {{strategyApiBase}}/templates/1/sync_from_strategy/
{
    "strategy_code": "# Updated code...",
    "parameters": {
        "asset": "AAPL",
        "lookback": 30
    },
    "chat_message": "Modified lookback period from 20 to 30 based on user request",
    "description": "Enhanced momentum strategy with longer lookback"
}
```

This ensures:
- Template stays synchronized with strategy evolution
- Chat history is preserved
- AI can access full context in future conversations

## Database Schema

### StrategyTemplate Model

```python
class StrategyTemplate(models.Model):
    # Basic template info
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField()
    category = models.CharField(max_length=100)
    template_code = models.TextField()
    parameters_schema = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    
    # Link to strategy (for auto-created templates)
    linked_strategy = models.ForeignKey('Strategy', ...)
    
    # Template type
    is_system_template = models.BooleanField(default=False)
    
    # Tracking latest state
    latest_strategy_code = models.TextField(blank=True)
    latest_parameters = models.JSONField(default=dict)
    chat_history = models.JSONField(default=list)
    
    # Metadata
    created_by = models.ForeignKey(User, ...)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### ChatSession Model

```python
class ChatSession(models.Model):
    user = models.ForeignKey(User, ...)
    ai_context = models.ForeignKey(AIContext, ...)
    
    # Link to strategy template
    strategy_template_id = models.IntegerField(null=True, blank=True)
    
    # Session info
    session_id = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=200)
    messages = models.JSONField(default=list)
    generated_strategies = models.JSONField(default=list)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

## API Endpoints

### Create Strategy (Auto Template)
**Endpoint:** `POST /api/strategies/api/create_strategy/`

**When to use:** First message in a chat session, or when starting fresh strategy development

**Behavior:**
- If `template_id` is provided → Uses that template
- If `template_id` is NOT provided → Auto-creates a new template
- Returns strategy + template information

### Sync Template from Strategy
**Endpoint:** `POST /api/strategies/templates/{id}/sync_from_strategy/`

**When to use:** After AI agent makes changes to the strategy

**Payload:**
```json
{
    "strategy_code": "string",          // Required: Updated code
    "parameters": {},                    // Required: Updated parameters
    "chat_message": "string",           // Required: Summary of changes
    "description": "string",            // Optional: Updated description
    "force_update": false               // Optional: Override system template protection
}
```

**Features:**
- Updates `latest_strategy_code` and `template_code`
- Merges parameters into `parameters_schema`
- Appends chat message to `chat_history` (keeps last 50)
- Prevents updating system templates unless `force_update=true`

### Get Template Context
**Endpoint:** `GET /api/strategies/templates/{id}/get_context/`

**When to use:** When AI agent needs full context about a strategy

**Returns:**
- Full template data
- Linked strategy information
- Chat history
- Context summary statistics

## Workflow Examples

### Example 1: User Starts New Strategy

1. **User sends first message to AI:**
   "Create a momentum strategy for AAPL"

2. **AI creates strategy (no template_id):**
   ```json
   POST /api/create_strategy/
   {
       "name": "AAPL Momentum Strategy",
       "strategy_code": "...",
       "parameters": {"asset": "AAPL"}
   }
   ```

3. **System auto-creates template:**
   - Template ID: 1
   - Linked to Strategy ID: 1
   - Returns template info in response

4. **AI stores template_id in ChatSession:**
   ```python
   chat_session.strategy_template_id = 1
   ```

### Example 2: User Modifies Strategy in Chat

1. **User:** "Change the lookback period to 30"

2. **AI modifies strategy and updates template:**
   ```json
   POST /templates/1/sync_from_strategy/
   {
       "strategy_code": "# Updated code with lookback=30...",
       "parameters": {"asset": "AAPL", "lookback": 30},
       "chat_message": "Changed lookback period from 20 to 30"
   }
   ```

3. **System updates template:**
   - Updates `latest_strategy_code`
   - Updates `latest_parameters`
   - Adds chat message to history

### Example 3: User Returns to Previous Chat

1. **User opens previous chat session**

2. **AI retrieves context:**
   ```json
   GET /templates/1/get_context/
   ```

3. **AI receives:**
   - Current strategy state
   - Full chat history
   - All parameters and code
   - Can continue conversation with full context

## Benefits

### For Users
- ✅ **No setup required** - Template auto-created on first message
- ✅ **Edit strategies easily** - Template tracks all changes
- ✅ **Chat history preserved** - Context maintained across sessions
- ✅ **Multiple strategies** - Each gets its own template

### For AI Agents
- ✅ **Full context access** - See entire strategy evolution
- ✅ **Bidirectional sync** - Keep template and strategy aligned
- ✅ **Chat history** - Understand previous decisions
- ✅ **Easy updates** - Simple sync endpoint

### For System
- ✅ **Version tracking** - Every change documented
- ✅ **Reusability** - Successful strategies become templates
- ✅ **User engagement** - Track strategy development journey
- ✅ **Data-driven insights** - Understand user preferences

## Migration Notes

### Existing Code
The changes are backward compatible:
- Old strategies without templates continue to work
- `template_id` remains optional in create requests
- Existing templates are unaffected

### Database Migration Required
Run migrations to add new fields:
```bash
python manage.py makemigrations
python manage.py migrate
```

New fields added:
- `StrategyTemplate.linked_strategy`
- `StrategyTemplate.is_system_template`
- `StrategyTemplate.latest_strategy_code`
- `StrategyTemplate.latest_parameters`
- `StrategyTemplate.chat_history`
- `ChatSession.strategy_template_id`

## Best Practices

### For AI Implementation

1. **Always create template on first message**
   - Don't provide `template_id` in initial create_strategy call
   - Store returned template ID in ChatSession

2. **Sync after significant changes**
   - User requests modifications
   - Strategy code is updated
   - Parameters are changed
   - Don't sync on every message, only when code/params change

3. **Retrieve context when resuming**
   - Use `get_context` when chat session reopens
   - Load chat history for continuity
   - Reference previous decisions

4. **Include meaningful chat messages**
   - Summarize what changed and why
   - Help future AI understand user intent
   - Keep messages concise but informative

### For System Templates

1. **Mark as system templates**
   - Set `is_system_template=True` for pre-built templates
   - Prevents accidental overwrites
   - Requires `force_update=true` to modify

2. **Use clear categories**
   - momentum, mean-reversion, arbitrage, etc.
   - Helps users discover relevant templates
   - Enables better filtering

## Testing

See Postman collection for examples:
- `Create Strategy (Simple - Auto Template)` - Auto-template creation
- `Sync Template from Strategy (AI Agent)` - Update workflow
- `Get Template Context (AI Agent)` - Context retrieval

## Troubleshooting

### Template not auto-created
- Check if `skip_template_creation: true` in request
- Verify user permissions
- Check server logs for errors

### Sync fails
- Ensure template ID is correct
- Check if template is system template (needs `force_update`)
- Verify JSON payload format

### Chat history too large
- System keeps only last 50 entries
- Older entries automatically removed
- Consider summarizing long conversations

## Support

For issues or questions:
- Check API errors in response
- Review server logs
- Verify database migrations ran successfully
- Test with Postman collection examples
