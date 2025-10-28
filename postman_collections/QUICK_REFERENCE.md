# 🎯 Quick Reference: AI Strategy Validation API

## Import to Postman
📥 **File:** `Quick_AI_Strategy_Validation.json`

## Endpoints at a Glance

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/validate_strategy_with_ai/` | POST | Validate only (no DB record) |
| `/create_strategy_with_ai/` | POST | Validate + Create + Save |
| `/{{id}}/update_strategy_with_ai/` | PUT | Update existing with AI |
| `/health/` | GET | Check API status |

## Request Format

### Validate Strategy
```json
POST /api/strategies/api/validate_strategy_with_ai/
{
  "strategy_text": "Your strategy here...",
  "input_type": "auto",     // auto, numbered, freetext, url
  "use_gemini": true,       // Enable AI
  "strict_mode": false      // Security level
}
```

### Create Strategy
```json
POST /api/strategies/api/create_strategy_with_ai/
{
  "strategy_text": "Your strategy...",
  "name": "Strategy Name",           // Optional
  "description": "Description",      // Optional
  "tags": ["tag1", "tag2"],         // Optional
  "save_to_backtest": true          // Save to Backtest/codes/
}
```

### Update Strategy
```json
PUT /api/strategies/api/1/update_strategy_with_ai/
{
  "strategy_text": "Updated strategy...",
  "update_description": "What changed"
}
```

## Response Fields

✅ **Always Returns:**
- `status` - success/error/approval_required
- `canonicalized_steps` - Structured steps array
- `classification` - Strategy type & risk tier
- `recommendations` - AI improvement suggestions
- `confidence` - high/medium/low
- `canonical_json` - Complete canonical schema

⚠️ **May Include:**
- `warnings` - Security/risk alerts
- `next_actions` - Recommended improvements
- `issues` - Validation errors

## Input Types

| Type | Example |
|------|---------|
| `auto` | Automatically detects format |
| `numbered` | `1. Buy when...\n2. Sell when...` |
| `freetext` | `Buy when RSI is oversold...` |
| `url` | `https://youtube.com/watch?v=...` |

## Common Patterns

### Pattern 1: Validate Before Creating
```bash
# 1. Validate first
POST /validate_strategy_with_ai/
{...}

# 2. Review AI recommendations

# 3. Create if satisfied
POST /create_strategy_with_ai/
{...}
```

### Pattern 2: Quick Create
```bash
# Create directly with AI validation
POST /create_strategy_with_ai/
{
  "strategy_text": "...",
  "save_to_backtest": true
}
```

### Pattern 3: Iterative Development
```bash
# 1. Create initial version
POST /create_strategy_with_ai/ → ID: 1

# 2. Update based on AI feedback
PUT /1/update_strategy_with_ai/
{
  "strategy_text": "Enhanced version...",
  "update_description": "Added SMA filter"
}
```

## Example Strategies (Included in Collection)

### 1. RSI Mean Reversion
```
Buy when RSI(14) < 30
Sell when RSI(14) > 70
Stop: 2% | Size: 1% risk
```

### 2. EMA Golden Cross
```
1. Buy: 50 EMA crosses above 200 EMA
2. Sell: 50 EMA crosses below 200 EMA
3. Stop: 2% | Profit: 5%
4. Size: 1% risk per trade
```

### 3. Bollinger Breakout
```
Entry: Price closes outside Bollinger Bands (20,2)
Exit: Price returns to middle band
Stop: 1.5% | Volume filter: Above 20-day avg
```

## Environment Variables

Auto-configured in Quick collection:
- `base_url` = `http://localhost:8000`
- `strategy_id` = Auto-saved from create requests

## Tests Included

✅ Automatic validation:
- Status code checks (200, 201)
- Response structure validation
- AI field presence verification
- Auto-save strategy_id for updates

## Tips & Tricks

💡 **Auto-generate names:** Omit `name` field, AI creates descriptive name

💡 **Save to Backtest:** Use `save_to_backtest: true` for instant file creation

💡 **Track evolution:** Templates auto-track changes in chat history

💡 **Batch testing:** Run entire collection to test all scenarios

💡 **Review warnings:** Check `warnings` array for risk alerts

## Quick Test Flow

1. **Health Check** → Verify API is ready
2. **Validate Freetext** → Test AI extraction
3. **Validate Numbered** → Test structured format
4. **Create Strategy** → Get strategy_id saved
5. **Update Strategy** → Uses saved strategy_id
6. **Check Backtest/codes/** → See saved JSON

## Troubleshooting

| Error | Solution |
|-------|----------|
| 503 Service Unavailable | Start Django server |
| Validator not available | Check Strategy module path |
| Gemini API error | Verify GEMINI_API_KEY env var |
| Template not found | Use auto-create (omit template_id) |

## Start Testing Now!

```bash
# 1. Start server
cd AlgoAgent
python manage.py runserver

# 2. Import to Postman
# Quick_AI_Strategy_Validation.json

# 3. Run "Health Check"
# 4. Run "Validate Strategy with AI"
# 5. Run "Create Strategy with AI"

# ✅ Done!
```

---

📚 **Full Documentation:** `AI_STRATEGY_API_GUIDE.md`  
🧪 **Test Script:** `test_ai_strategy_api.py`  
📦 **Full Collection:** `Strategy_AI_Validation_Collection.json`
