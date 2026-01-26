# Copilot Integration for Strategy Validation

## Changes Made

### 1. Default AI Provider Changed to Copilot

**Location:** `strategy_api/views.py` - `validate_strategy_with_ai` endpoint

**Before:**
- `use_gemini`: Default `True`
- Always tried to use Gemini API first

**After:**
- `ai_provider`: Default `"copilot"`
- `use_gemini`: Deprecated (backward compatibility)
- Automatically uses Copilot when Gemini keys are commented out

### 2. StrategyValidatorBot Updated

**Location:** `Strategy/strategy_validator.py`

**New Initialization Logic:**
1. If `use_gemini=False`, try to initialize Copilot first
2. Check for valid Copilot authentication
3. Fall back to Gemini only if Copilot unavailable or `use_gemini=True`
4. Use mock responses only as last resort

**Capabilities:**
- ✅ Copilot strategy analysis
- ✅ AI-enhanced insights
- ✅ Conversation memory (via session_id)
- ✅ Backward compatible with Gemini

### 3. API Request Format

**New Format (Recommended):**
```json
{
  "strategy_text": "Buy when RSI < 30, sell when RSI > 70",
  "ai_provider": "copilot",
  "input_type": "auto",
  "strict_mode": false,
  "session_id": "chat_abc123",
  "use_context": true
}
```

**Backward Compatible:**
```json
{
  "strategy_text": "...",
  "use_gemini": false,  // Will use Copilot instead
  "input_type": "auto"
}
```

**AI Provider Values:**
- `"copilot"` - Use GitHub Copilot (default)
- `"gemini"` - Use Google Gemini (if keys available)
- If omitted, defaults to Copilot

---

## What This Fixes

### Problem
When Gemini API keys were commented out in `.env`, the system showed:
```
⚠ No Gemini API key found. Using mock responses.
```

### Solution
Now the system automatically:
1. Detects no Gemini keys available
2. Switches to Copilot authentication
3. Uses Copilot for AI-enhanced validation
4. Shows: `✓ AI-enhanced strategy analysis enabled (GitHub Copilot)`

---

## Testing

### 1. Verify Copilot is Being Used

**Check server logs on startup:**
```
✓ AI-enhanced strategy analysis enabled (GitHub Copilot)
✓ Conversation memory enabled for session chat_...
```

**Look for in request logs:**
```
INFO:strategy_api.views:Using Copilot for AI-enhanced validation response
```

### 2. Test from Frontend

Send a strategy validation request and check the response:

```json
{
  "status": "success",
  "ai_provider": "copilot",  // ← Should show "copilot"
  "ai_insights": "...",       // ← AI analysis from Copilot
  "classification": "...",
  ...
}
```

### 3. Manual Test

```bash
curl -X POST http://localhost:8000/api/strategies/api/validate_strategy_with_ai/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "strategy_text": "Buy when RSI < 30, sell when RSI > 70",
    "ai_provider": "copilot"
  }'
```

Check response for `"ai_provider": "copilot"`

---

## Configuration

### Use Copilot Only (Current Setup)

**.env file:**
```bash
# Gemini keys commented out
# GEMINI_API_KEY_PRO_01=...
# GEMINI_API_KEY_FLASH_01=...

# Copilot auth active
COPILOT_AUTH_TOKEN=ghp_...
```

**Result:** All AI requests use Copilot

### Use Both (Optional)

**.env file:**
```bash
# Keep both active
GEMINI_API_KEY_PRO_01=...
COPILOT_AUTH_TOKEN=ghp_...
```

**API Request:**
```json
{
  "strategy_text": "...",
  "ai_provider": "copilot"  // Choose per request
}
```

### Frontend Default

To make frontend use Copilot by default, update API calls:

**Before:**
```typescript
const response = await fetch('/api/strategies/api/validate_strategy_with_ai/', {
  body: JSON.stringify({
    strategy_text: text,
    use_gemini: true  // Old way
  })
});
```

**After:**
```typescript
const response = await fetch('/api/strategies/api/validate_strategy_with_ai/', {
  body: JSON.stringify({
    strategy_text: text,
    ai_provider: 'copilot'  // New way (optional, it's default)
  })
});
```

Or simply omit `ai_provider` - it defaults to Copilot now.

---

## Troubleshooting

### Issue: Still seeing "Using mock responses"

**Check:**
1. Copilot token is valid (not expired)
   ```bash
   python -c "from algoagent_api.copilot_auth import get_auth_manager; print(get_auth_manager())"
   ```

2. Token in database is current
   ```python
   from strategy_api.models import CopilotAuth
   token = CopilotAuth.get_latest_token()
   print(f"Token expires: {token['expires_at']}")
   ```

3. Restart Django server after .env changes

### Issue: Copilot auth errors

**Solution:**
Re-authenticate with Copilot:
```bash
# Check current auth
python manage.py shell -c "from strategy_api.models import CopilotAuth; print(CopilotAuth.objects.first())"

# If needed, re-authenticate through frontend or API
```

### Issue: Want to force Gemini

**Option 1 - Per Request:**
```json
{
  "strategy_text": "...",
  "ai_provider": "gemini",
  "use_gemini": true
}
```

**Option 2 - Change Default:**
In `strategy_api/views.py`, line ~1600:
```python
ai_provider = data.get('ai_provider', 'gemini')  # Change from 'copilot'
```

---

## Summary

✅ **Completed:**
- Copilot is now the default AI provider
- Automatic fallback when Gemini unavailable
- Backward compatible with existing code
- AI-enhanced validation works with Copilot
- No more "mock responses" when Gemini keys are commented out

✅ **Benefits:**
- Uses your GitHub Copilot subscription
- No need for Gemini API keys
- Same AI-enhanced features
- Consistent with strategy generation (also uses Copilot)

✅ **Next Time You Restart Server:**
You should see:
```
✓ AI-enhanced strategy analysis enabled (GitHub Copilot)
```
Instead of:
```
⚠ No Gemini API key found. Using mock responses.
```

🎉 **Your system is now fully configured to use GitHub Copilot!**
