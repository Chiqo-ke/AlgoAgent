# Migrating from Google Gemini to GitHub Models (GitHub Copilot/OpenCode)

This guide will help you migrate your multi-agent system from Google Gemini to GitHub Models while preserving your key rotation and rate limiting infrastructure.

## Table of Contents

1. [Overview](#overview)
2. [Why GitHub Models?](#why-github-models)
3. [Prerequisites](#prerequisites)
4. [Step-by-Step Migration](#step-by-step-migration)
5. [Configuration](#configuration)
6. [Available Models](#available-models)
7. [Rate Limits](#rate-limits)
8. [Troubleshooting](#troubleshooting)

## Overview

**GitHub Models** is GitHub's free AI model service that provides access to various LLMs including:
- OpenAI models (GPT-4o, GPT-4o-mini, o1, o1-mini)
- Microsoft models (Phi-4)
- Open-source models (Mistral, Llama, etc.)

The service is **OpenAI-compatible**, making integration seamless with existing OpenAI-based codebases.

### Key Features:
✅ **Free tier** with generous rate limits  
✅ **OpenAI-compatible API** (easy migration)  
✅ **Multiple models** from different providers  
✅ **Key rotation support** (use multiple GitHub accounts)  
✅ **Built-in rate limiting** (handled by your existing infrastructure)  

## Why GitHub Models?

**Advantages over Gemini:**
- Free tier with competitive rate limits
- Access to OpenAI's latest models (GPT-4o, o1-mini)
- OpenAI-compatible API (easier to use)
- Multiple model providers in one endpoint
- Better compatibility with existing tools

**Comparison:**

| Feature | GitHub Models (Free) | Google Gemini (Free) |
|---------|---------------------|----------------------|
| **gpt-4o / High models** | 10-15 RPM, 50-150 RPD | N/A |
| **Phi-4 / Low models** | 15 RPM, 150 RPD | 10 RPM, 1500 RPD |
| **API Format** | OpenAI-compatible | Gemini-specific |
| **Authentication** | GitHub PAT | API Key |
| **Endpoint** | `models.inference.ai.azure.com` | `generativelanguage.googleapis.com` |

## Prerequisites

### 1. GitHub Authentication

**Recommended: Device Flow (Easy!)**

Just run this command and follow the prompts:

```bash
python scripts/github_device_auth.py
```

This will:
1. Show you a code to enter at https://github.com/login/device
2. Wait for you to authorize
3. Automatically save the token to `.env`
4. Verify the token works

**Alternative: Manual Personal Access Token**

<details>
<summary>Click to expand manual PAT instructions</summary>

Create a GitHub Personal Access Token:

1. Go to: https://github.com/settings/tokens
2. Click **"Generate new token (classic)"**
3. Give it a name: `AI Models Access`
4. Select permissions: **`models`**
5. Click **"Generate token"**
6. **Copy the token**

> **Note:** Device flow is recommended as it's easier and tokens are managed automatically.

</details>

### 2. Install/Update Dependencies

Your system should already have the OpenAI SDK installed. If not:

```bash
pip install openai>=1.0.0
```

## Step-by-Step Migration

### Step 1: Authenticate with GitHub

**Using Device Flow (Recommended):** in `keys.json`:

```json
{
  "keys": [
    {
      "key_id": "github-models-01",  # ← Matches .env key
      "model_name": "gpt-4o-mini",
      "provider": "github-models",
      "rpm": 15,
      "tpm": 150000,
      "rpd": 150,
      "active": true,
      "tags": {
        "tier": "free",
        "workload": "medium",
        "priority": 1
      },
      "created_at": "2025-11-11T00:00:00Z",
      "updated_at": "2025-11-11T00:00:00Z"
    }
  ]
}
```

> **Note:** The `key_id` in `keys.json` must match the suffix in your `.env` variable.  
> Example: `key_id: "github-models-01"` → `.env` has `API_KEY_github-models-01`

### Step 3: Verify
      "tags": {
        "tier": "free",
        "workload": "light",
        "priority": 1
      },
      "created_at": "2025-11-11T00:00:00Z",
      "updated_at": "2025-11-11T00:00:00Z"
    }
  ],
  "config": {
    "max_retries": 2,
    "base_backoff_ms": 500,
    "enable_fallback": true,
    "conversation_ttl_seconds": 86400
  }
}
```

### Step 2: Update `.env`

Add your GitHub Personal Access Tokens:

```bash
# GitHub Models Configuration
API_KEY_github-gpt4o-01=github_pat_YOUR_TOKEN_HERE
API_KEY_github-gpt4o-mini-01=github_pat_YOUR_TOKEN_HERE
API_KEY_github-phi4-01=github_pat_YOUR_TOKEN_HERE

# Optional: Keep Gemini as fallback (lower priority)
# API_KEY_gemini-flash-01=AIzaSy...
```

> **Key Rotation:** If you have multiple GitHub accounts, create a PAT for each and use different `key_id` values.

### Step 3: Update Agent Configuration

If your agents specify model preferences, update them:

**Before (Gemini):**
```python
model_preference="gemini-2.5-flash"
workload="light"
```

**After (GitHub Models):**
```python
model_preference="gpt-4o-mini"  # or "Phi-4" for light workloads
workload="light"
```

### Step 4: Test the Integration

Run a quick test:

```python
from llm.router import RequestRouter

router = RequestRouter()

response = router.send_one_shot(
    prompt="Write a Python function to calculate fibonacci numbers",
    model_preference="gpt-4o-mini",
    workload="light"
)

print(response)
```

Expected output:
```python
{
    'success': True,
    'content': '...',  # Generated code
    'model': 'gpt-4o-mini',
    'key_id': 'github-gpt4o-mini-01',
    'tokens': {'input': 15, 'output': 120, 'total': 135}
}
```

### Step 5: Verify Key Rotation

Test that key rotation is working:

```bash
# Check Redis for rate limiting
redis-cli
> KEYS rpm:github-gpt4o-*
> KEYS tpm:github-gpt4o-*
```

## Configuration

### Workload Mapping

Map your workload types to appropriate models:

| Workload | Recommended Model | RPM | Use Case |
|----------|------------------|-----|----------|
| `light` mediumhi-4** | 15 | Simple queries, fast responses |
| `medium` | **gpt-4o-mini** | 15 | Code generation, analysis |
| `heavy` | **gpt-4o** | 15 | Complex reasoning, long tasks |
| `reasoning` | **o1-mini** | 2 | Advanced problem solving |

### Priority Configuration

Set priorities to control fallback order:

```json
{
  "tags": {
    "priority": 1  // Lower = higher priority
  }
}
```

**Recommended Setup:**
1. **Priority 1:** GitHub Models (primary)
2. **Priority 2:** Gemini (fallback, if kept)
3. **Priority 3:** OpenAI paid (emergency fallback)

## Available Models

### High-Tier Models (Heavy Workload)

| Model | RPM | RPD | Input Tokens | Output Tokens |
|-------|-----|-----|--------------|---------------|
| **gpt-4o** | 10-15 | 50-150 | 8,000 | 4,000 |
| **o1** | 1 | 8 | 4,000 | 4,000 |
| **Mistral-large** | 10 | 50 | 8,000 | 4,000 |

### Medium-Tier Models (Medium  (Optional)

If you want key rotation for higher throughput, run the auth script multiple times:

```bash
# Authenticate multiple times with different key IDs
python scripts/github_device_auth.py
# Enter key ID: github-models-01

python scripts/github_device_auth.py
# Enter key ID: github-models-02

python scripts/github_device_auth.py
# Enter key ID: github-models-03
```

Then add all keys to `keys.json`:

```json
{
  "keys": [
    {"key_id": "github-models-01", "model_name": "gpt-4o-mini", ...},
    {"key_id": "github-models-02", "model_name": "gpt-4o-mini", ...},
    {"key_id": "github-models-03", "model_name": "gpt-4o-mini", ...}
  ]
}
```Workload)

| Model | RPM | RPD | Input Tokens | Output Tokens |
|-------|-----|-----|--------------|---------------|
| **gpt-4o-mini** | 15 | 150 | 8,000 | 4,000 |
| **o1-mini** | 2 | 12 | 4,000 | 4,000 |

### Low-Tier Models (Light Workload)

| Model | RPM | RPD | Input Tokens | Output Tokens |
|-------|-----|-----|--------------|---------------|
| **Phi-4** | 15 | 150 | 8,000 | 4,000 |
| **mistral-small** | 15 | 150 | 8,000 | 4,000 |

> **Note:** Rate limits depend on your GitHub Copilot subscription tier. Free tier shown above.

## Rate Limits

### Understanding GitHub Models Rate Limits

GitHub Models enforces rate limits based on:
- **Requests Per Minute (RPM)**
- **Requests Per Day (RPD)**
- **Tokens Per Request**
- **Concurrent Requests**

Your existing `KeyManager` and `RequestRouter` handle these automatically through:
- Redis-based RPM/TPM tracking
- Automatic key rotation on 429 errors
- Cooldown management

### Handling Rate Limits

The system automatically:
1. **Tracks usage** via Redis
2. **Rotates keys** when limits are reached
3. **Sets cooldowns** on rate-limited keys
4. **Retries** with different keys

**Example flow:**
```
Request → github-gpt4o-01 (rate limited)
  ↓
Retry → github-gpt4o-mini-01 (success)
  ↓
Cooldown github-gpt4o-01 for 60s
```

## Troubleshooting

### Error: "GitHub Models API error: 401 Unauthorized"

**Cause:** Invalid GitHub Personal Access Token

**Solution:**
1. Check that your PAT is correctly set in `.env`
2. Verify the PAT has `models:read` permission
3. Ensure the PAT hasn't expired

### Error: "GitHub Models API error: 429 Rate Limit"

**Cause:** Hit rate limits for current key

**Solution:** The system should automatically:
1. Mark the key as unhealthy (cooldown)
2. Try the next available key
3. Rotate through all configured keys

**Manual check:**
```bash
# Check Redis cooldowns
redis-cli
> KEYS cooldown:github-*
> TTL cooldown:github-gpt4o-01
```

### Error: "All keys exhausted"

**Cause:** All configured keys are rate-limited

**Solutions:**
1. **Add more keys** from different GitHub accounts
2. **Wait** for cooldowns to expire (typically 60s)
3. **Configure fallback** to Gemini or OpenAI
4. **Reduce request rate** in your application

### Provider Not Found

**Error:** `ProviderError: Unknown provider: github-models`

**Cause:** Provider not registered in registry

**Solution:** Ensure `providers.py` has been updated:
```python
_PROVIDERS = {
    'gemini': GeminiClient(),
    'openai': OpenAIClient(),
    'github-models': GitHubModelsClient(),  # ← Must be present
    ...
}
```

### Model Not Available

**Error:** Model not found or unavailable

**Solution:** Check available models at:
https://github.com/marketplace/models

Not all models are available on all tiers. Update your `keys.json` with supported models.

## Best Practices

### 1. Key Rotation Strategy

For production use, configure multiple keys:

```json
{
  "keys": [
    {"key_id": "github-gpt4o-01", "priority": 1},
    {"key_id": "github-gpt4o-02", "priority": 1},
    {"key_id": "github-gpt4o-03", "priority": 1},
    {"key_id": "gemini-flash-01", "priority": 2}
  ]
}
```

Benefits:
- **Higher throughput** (3x RPM/RPD limits)
- **Automatic failover** (no single point of failure)
- **Load distribution** (balanced across keys)

### 2. Workload Optimization

Choose models based on task complexity:

```python
# Light tasks (simple queries)
workload="light"  # → Phi-4 (fast, cheap)

# Medium tasks (code generation)
workload="medium"  # → gpt-4o-mini (balanced)

# Heavy tasks (complex reasoning)
workload="heavy"  # → gpt-4o (powerful)
```

### 3. Monitor Usage

Track your usage to avoid hitting limits:

```python
from llm.router import RequestRouter

router = RequestRouter()
# Your router automatically tracks usage in Redis

# Check usage programmatically
from llm.redis_client import get_redis_limiter

limiter = get_redis_limiter()
rpm_count = limiter.get_rpm_count("github-gpt4o-01")
tpm_count = limiter.get_tpm_count("github-gpt4o-01")

print(f"RPM: {rpm_count}/15")
print(f"TPM: {tpm_count}/150000")
```

### 4. Keep Gemini as Fallback

During migration, keep Gemini keys active but with lower priority:

```json
{
  "keys": [
    {"key_id": "github-gpt4o-01", "priority": 1},
    {"key_id": "gemini-flash-01", "priority": 2, "active": true}
  ]
}
```

This ensures continuity if GitHub Models has issues.

## Migration Checklist

- [ ] Authenticated using device flow (`python scripts/github_device_auth.py`)
  - Alternative: Created GitHub Personal Access Token manually
- [ ] Updated `keys.json` with GitHub Models configuration
- [ ] Verified `.env` has correct API_KEY entries (auto-saved by device flow)
- [ ] Installed dependencies: `pip install -r requirements_llm.txt`
- [ ] Started Redis: `docker run -d -p 6379:6379 redis:latest`
- [ ] Tested basic request with `send_one_shot()`
- [ ] Verified key rotation is working
- [ ] Updated agent model preferences (if needed)
- [ ] Monitored Redis for rate limit tracking
- [ ] Configured fallback providers (optional)
- [ ] Removed/disabled old Gemini keys (optional)
- [ ] Documented changes for team

## Additional Resources

- **GitHub Models Documentation:** https://docs.github.com/en/github-models
- **Model Catalog:** https://github.com/marketplace/models
- **Create GitHub PAT:** https://github.com/settings/tokens
- **OpenAI API Docs:** https://platform.openai.com/docs/api-reference
- **Azure AI Inference SDK:** https://learn.microsoft.com/azure/ai-studio/

## Support

If you encounter issues:

1. Check this documentation first
2. Review error logs: `logs/router.log`
3. Verify Redis is running: `redis-cli ping`
4. Check GitHub Models status: https://www.githubstatus.com/
5. Test with a simple curl request:

```bash
curl -X POST https://models.inference.ai.azure.com/chat/completions \
  -H "Authorization: Bearer github_pat_YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

---

**Migration completed!** Your system now uses GitHub Models with full key rotation support.
