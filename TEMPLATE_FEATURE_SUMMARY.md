# Template Workflow Feature - Implementation Summary

## Purpose

The `template_id` in the `{{strategyApiBase}}/api/create_strategy/` endpoint serves dual purposes:

### 1. **Optional Pre-built Templates**
Users can specify a `template_id` to start from a pre-built strategy template (e.g., Momentum, Mean Reversion, etc.)

### 2. **Auto-Generated Strategy Tracking** (NEW)
When `template_id` is NOT provided, the system now automatically creates a template to track the strategy's evolution through AI chat sessions.

## What Was Implemented

### ✅ Database Changes

**StrategyTemplate Model** (`strategy_api/models.py`)
- Added `linked_strategy` - Links template to the strategy it represents
- Added `is_system_template` - Distinguishes pre-built vs user-generated templates
- Added `latest_strategy_code` - Tracks most recent strategy code
- Added `latest_parameters` - Tracks most recent parameters
- Added `chat_history` - Stores conversation history (last 50 messages)

**ChatSession Model** (`auth_api/models.py`)
- Added `strategy_template_id` - Links chat session to strategy template for context continuity

### ✅ API Endpoints

**Enhanced: Create Strategy** (`POST /api/create_strategy/`)
- Now auto-creates a `StrategyTemplate` if `template_id` not provided
- Links template ↔ strategy bidirectionally
- Returns template info in response

**New: Sync Template** (`POST /templates/{id}/sync_from_strategy/`)
- AI agent updates template with latest strategy changes
- Accepts: `strategy_code`, `parameters`, `chat_message`, `description`
- Protects system templates (requires `force_update=true`)
- Maintains chat history (last 50 entries)

**New: Get Context** (`GET /templates/{id}/get_context/`)
- AI agent retrieves full template context
- Returns: template data, linked strategy, chat history, statistics
- Enables AI to resume conversations with full context

### ✅ Documentation

**Created Files:**
1. `TEMPLATE_WORKFLOW_GUIDE.md` - Comprehensive usage guide
2. `TEMPLATE_MIGRATION_STEPS.md` - Migration instructions

**Updated Files:**
1. `Strategy_API_Collection.json` - Added new endpoint examples

## User Workflow

### Scenario: User Starts Creating a Strategy

**Step 1: First Message**
```
User: "Create a momentum strategy for AAPL"
```

**Step 2: AI Creates Strategy (No template_id)**
```json
POST /api/create_strategy/
{
    "name": "AAPL Momentum Strategy",
    "strategy_code": "def initialize(context):...",
    "parameters": {"asset": "AAPL"}
}
```

**Step 3: System Auto-Creates Template**
- Template ID: 1 (auto-generated)
- Linked to Strategy ID: 1
- Response includes `auto_created_template` info

**Step 4: AI Stores Template Reference**
```python
chat_session.strategy_template_id = 1
```

### Scenario: User Modifies Strategy

**Step 1: User Request**
```
User: "Change lookback period to 30"
```

**Step 2: AI Updates Template**
```json
POST /templates/1/sync_from_strategy/
{
    "strategy_code": "# Updated code...",
    "parameters": {"lookback": 30},
    "chat_message": "Changed lookback from 20 to 30"
}
```

**Step 3: Template Synchronized**
- Latest code updated
- Parameters merged
- Chat history appended

### Scenario: User Returns to Chat

**Step 1: AI Retrieves Context**
```json
GET /templates/1/get_context/
```

**Step 2: AI Receives Full Context**
- Current strategy state
- Complete chat history
- All parameters and code
- Can continue with full context awareness

## Benefits

### For Users
✅ No manual template setup required  
✅ Strategy evolution automatically tracked  
✅ Chat history preserved across sessions  
✅ Easy to edit and iterate on strategies  

### For AI Agents
✅ Full context access for better responses  
✅ Simple sync mechanism after updates  
✅ Chat history for understanding user intent  
✅ Can resume conversations seamlessly  

### For System
✅ Version tracking of all changes  
✅ Successful strategies become reusable templates  
✅ User engagement tracking  
✅ Data-driven insights on strategy development  

## Migration Required

**Before using these features:**

```powershell
cd c:\Users\nyaga\Documents\AlgoAgent
python manage.py makemigrations strategy_api
python manage.py makemigrations auth_api
python manage.py migrate
```

This adds the new fields to the database.

## Backward Compatibility

✅ All existing code continues to work  
✅ Old strategies unaffected  
✅ `template_id` remains optional  
✅ No breaking changes  

## Testing

Use the updated Postman collection:
1. `Create Strategy (Simple - Auto Template)` - Test auto-creation
2. `Sync Template from Strategy (AI Agent)` - Test sync workflow
3. `Get Template Context (AI Agent)` - Test context retrieval

## Files Modified

### Models
- ✏️ `strategy_api/models.py` - StrategyTemplate model enhanced
- ✏️ `auth_api/models.py` - ChatSession model enhanced

### Views
- ✏️ `strategy_api/views.py` - Added template management logic

### Documentation
- ➕ `TEMPLATE_WORKFLOW_GUIDE.md` - Complete usage guide
- ➕ `TEMPLATE_MIGRATION_STEPS.md` - Migration instructions

### API Collections
- ✏️ `postman_collections/Strategy_API_Collection.json` - New endpoints added

## Next Steps

1. **Run Migrations** (see `TEMPLATE_MIGRATION_STEPS.md`)
2. **Test Endpoints** (use Postman collection)
3. **Implement AI Agent Logic** (see `TEMPLATE_WORKFLOW_GUIDE.md`)
4. **Create System Templates** (optional - for pre-built templates)

## Key API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/create_strategy/` | POST | Create strategy (auto-creates template if needed) |
| `/templates/{id}/sync_from_strategy/` | POST | Sync template with strategy updates |
| `/templates/{id}/get_context/` | GET | Get full template context for AI |
| `/templates/` | GET | List all templates |
| `/templates/{id}/` | GET/PUT | Get/Update specific template |

## Success Criteria

- [x] `template_id` is optional in create_strategy
- [x] Auto-creates template when not provided
- [x] Template tracks strategy evolution
- [x] Chat history stored in template
- [x] AI can sync updates easily
- [x] AI can retrieve full context
- [x] ChatSession links to template
- [x] Documentation complete
- [x] Postman collection updated
- [ ] Migrations applied (run migrations)
- [ ] Endpoints tested

## Questions or Issues?

Refer to:
- `TEMPLATE_WORKFLOW_GUIDE.md` for detailed usage
- `TEMPLATE_MIGRATION_STEPS.md` for migration help
- Postman collection for API examples
