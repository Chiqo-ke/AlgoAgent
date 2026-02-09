# OpenCode Setup Guide

## Quick Start (5 Minutes)

### 1. Get OpenCode API Key

1. Visit: https://opencode.ai
2. Sign up for an account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (starts with `opencode_`)

### 2. Configure Environment

Add your OpenCode API key to `.env`:

```bash
# OpenCode API Keys (unified access to Claude, GPT-4, Gemini, etc.)
API_KEY_opencode-claude-01=opencode_YOUR_KEY_HERE
API_KEY_opencode-gpt4o-01=opencode_YOUR_KEY_HERE
API_KEY_opencode-gemini-01=opencode_YOUR_KEY_HERE
```

**Note**: You can use the same API key for all three entries - OpenCode provides access to all models through one key.

### 3. Verify keys.json

Your `keys.json` should already have OpenCode configured:

```json
{
  "keys": [
    {
      "key_id": "opencode-claude-01",
      "model_name": "claude-sonnet-4-20250514",
      "provider": "opencode",
      "rpm": 60,
      "tpm": 100000,
      "rpd": 1000,
      "active": true,
      "tags": {
        "workload": "heavy",
        "priority": 1,
        "use_case": "code_generation"
      }
    }
  ]
}
```

### 4. Test the Integration

```bash
cd AlgoAgent/multi_agent
.venv\Scripts\Activate.ps1
python tests/test_providers.py
```

You should see:
```
✅ SUCCESS
📝 Response: Hello from AI!
🤖 Model: claude-sonnet-4-20250514
🔢 Tokens: {'input': 12, 'output': 5, 'total': 17}
```

### 5. Use in Your Agents

```python
from llm.request_router import RequestRouter

router = RequestRouter()

# Use Claude Sonnet 4 for complex code generation
response = router.send_one_shot(
    messages=[
        {"role": "user", "content": "Generate a Python function to calculate fibonacci"}
    ],
    model_preference="claude-sonnet-4-20250514",
    temperature=0.7
)

print(response['content'])
```

## Available Models Through OpenCode

### Anthropic Claude
- `claude-sonnet-4-20250514` - Latest Claude Sonnet 4 (recommended for code)
- `claude-3-5-sonnet-20241022` - Claude 3.5 Sonnet
- `claude-3-opus-20240229` - Claude 3 Opus

### OpenAI
- `gpt-4o` - Latest GPT-4 Omni
- `gpt-4o-mini` - Fast, efficient GPT-4
- `gpt-4-turbo` - GPT-4 Turbo

### Google Gemini
- `gemini-2.0-flash-exp` - Gemini 2.0 Flash (fast)
- `gemini-1.5-pro` - Gemini 1.5 Pro

### Meta Llama
- `llama-3.1-405b` - Llama 3.1 405B
- `llama-3.1-70b` - Llama 3.1 70B

### Mistral AI
- `mistral-large` - Mistral Large
- `mistral-medium` - Mistral Medium

## Benefits of OpenCode

✅ **Single API Key** - Access all providers through one key  
✅ **Unified Billing** - One invoice for all usage  
✅ **OpenAI-Compatible** - Works with existing OpenAI SDK  
✅ **No Provider Lock-in** - Switch models without code changes  
✅ **Automatic Failover** - Your RequestRouter handles provider switching  

## Pricing

Check current pricing at: https://opencode.ai/pricing

Typically more cost-effective than direct provider APIs for multi-model usage.

## Troubleshooting

### "401 Unauthorized"
- Check your API key is correct in `.env`
- Ensure key starts with `opencode_`
- Verify key is active on https://opencode.ai

### "Model not found"
- Check available models at https://opencode.ai/docs/models
- Ensure model name is spelled correctly
- Some models may require specific plan tiers

### Rate Limits
- Default: 60 RPM, 100K TPM, 1000 RPD
- Adjust in `keys.json` if you have higher limits
- RequestRouter will automatically failover to other keys

## Support

- Docs: https://opencode.ai/docs
- API Reference: https://opencode.ai/docs/api
- Discord: https://discord.gg/opencode (check their website for link)

---

## Migration from GitHub Models

If you were using GitHub Models before:

1. **Keep GitHub Models as fallback**:
   ```json
   {
     "key_id": "github-models-01",
     "active": true,
     "tags": {"priority": 4}
   }
   ```

2. **Set OpenCode as primary**:
   ```json
   {
     "key_id": "opencode-claude-01",
     "active": true,
     "tags": {"priority": 1}
   }
   ```

3. **RequestRouter will failover automatically** if OpenCode is down or rate-limited

Your system now has multi-provider redundancy! 🚀
