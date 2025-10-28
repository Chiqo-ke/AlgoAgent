# Migration Steps for Template Workflow Feature

## Quick Start

Execute these commands to apply the new template workflow feature:

```powershell
# Navigate to AlgoAgent directory
cd c:\Users\nyaga\Documents\AlgoAgent

# Create migrations for both apps
python manage.py makemigrations strategy_api
python manage.py makemigrations auth_api

# Apply migrations
python manage.py migrate

# Verify migrations were successful
python manage.py showmigrations
```

## What Changed

### Strategy API (`strategy_api/models.py`)

**StrategyTemplate model - New fields:**
- `linked_strategy` - ForeignKey to Strategy (allows template to reference the strategy it tracks)
- `is_system_template` - Boolean (distinguishes pre-built vs user-generated templates)
- `latest_strategy_code` - TextField (stores most recent strategy code)
- `latest_parameters` - JSONField (stores most recent parameters)
- `chat_history` - JSONField (stores conversation history)

### Auth API (`auth_api/models.py`)

**ChatSession model - New field:**
- `strategy_template_id` - Integer (links chat session to strategy template)

### Strategy API Views (`strategy_api/views.py`)

**StrategyTemplateViewSet - New actions:**
- `sync_from_strategy` - POST endpoint for AI to update templates
- `get_context` - GET endpoint to retrieve full template context

**StrategyAPIViewSet - Enhanced:**
- `create_strategy` - Now auto-creates templates when `template_id` is not provided

## Expected Migration Output

```
Migrations for 'strategy_api':
  strategy_api\migrations\0002_auto_<timestamp>.py
    - Add field linked_strategy to strategytemplate
    - Add field is_system_template to strategytemplate
    - Add field latest_strategy_code to strategytemplate
    - Add field latest_parameters to strategytemplate
    - Add field chat_history to strategytemplate

Migrations for 'auth_api':
  auth_api\migrations\0002_auto_<timestamp>.py
    - Add field strategy_template_id to chatsession
```

## Rollback (If Needed)

If you need to rollback these changes:

```powershell
# Rollback strategy_api
python manage.py migrate strategy_api 0001

# Rollback auth_api
python manage.py migrate auth_api 0001

# Or rollback both completely
python manage.py migrate strategy_api zero
python manage.py migrate auth_api zero
```

## Post-Migration Verification

### 1. Check Database Schema

```powershell
python manage.py dbshell
```

Then in the database shell:
```sql
-- Check StrategyTemplate table
PRAGMA table_info(strategy_api_strategytemplate);

-- Check ChatSession table
PRAGMA table_info(auth_api_chatsession);
```

### 2. Test API Endpoints

Use the Postman collection to test:

1. **Create Strategy (Auto Template)**
   - Use: `Create Strategy (Simple - Auto Template)` request
   - Verify: Response includes `auto_created_template`

2. **Sync Template**
   - Use: `Sync Template from Strategy (AI Agent)` request
   - Verify: Template updated successfully

3. **Get Context**
   - Use: `Get Template Context (AI Agent)` request
   - Verify: Returns full context with chat history

### 3. Check Admin Panel

```powershell
python manage.py runserver
```

Visit: `http://127.0.0.1:8000/admin/`

Navigate to:
- Strategy API → Strategy Templates
- Verify new fields are visible and editable

## Common Issues

### Issue: Migration conflicts

**Solution:**
```powershell
# Delete migration files (except __init__.py)
# Then recreate
python manage.py makemigrations
python manage.py migrate
```

### Issue: Field already exists

**Solution:**
```powershell
# Check current migrations
python manage.py showmigrations

# Apply specific migration
python manage.py migrate strategy_api <migration_name>
```

### Issue: SQLite locked

**Solution:**
```powershell
# Stop Django server
# Delete db.sqlite3-journal if exists
# Retry migration
python manage.py migrate
```

## Data Preservation

All existing data is preserved:
- ✅ Existing strategies unchanged
- ✅ Existing templates unchanged
- ✅ New fields have sensible defaults
- ✅ No data loss

New fields defaults:
- `linked_strategy`: `null=True` (optional)
- `is_system_template`: `False`
- `latest_strategy_code`: `""` (empty string)
- `latest_parameters`: `{}` (empty dict)
- `chat_history`: `[]` (empty list)
- `strategy_template_id`: `null=True` (optional)

## Testing Checklist

- [ ] Migrations created successfully
- [ ] Migrations applied without errors
- [ ] Existing strategies still accessible
- [ ] Can create new strategy without template_id
- [ ] Auto-template created correctly
- [ ] Can sync template from strategy
- [ ] Can get template context
- [ ] Chat session can link to template
- [ ] Admin panel shows new fields
- [ ] API endpoints return correct data

## Next Steps

After successful migration:

1. **Update AI Agent Code**
   - Implement template auto-creation logic
   - Add sync_from_strategy calls after strategy updates
   - Use get_context when resuming chat sessions

2. **Update Frontend (if applicable)**
   - Display template information in UI
   - Show chat history
   - Allow users to edit strategies

3. **Populate System Templates**
   - Create pre-built templates with `is_system_template=True`
   - Categorize properly
   - Add comprehensive parameter schemas

## Support

If you encounter issues:
1. Check migration output for errors
2. Review `TEMPLATE_WORKFLOW_GUIDE.md` for usage
3. Test with Postman collection
4. Check Django logs for detailed errors
