# GitHub Models Quick Start Guide

Get started with GitHub Models in 3 minutes using device flow authentication!

## Step 1: Authenticate with GitHub (Easy Way!)

**No manual token creation needed!** Just run this script:

```bash
python scripts/github_device_auth.py
```

Then:
1. 🌐 Visit: **https://github.com/login/device**
2. 📝 Enter the code shown in your terminal
3. ✅ Click "Authorize" on GitHub
4. 🎉 Done! Token automatically saved to `.env`

**What this does:**
- Authenticates you with GitHub using device flow
- Automatically saves your access token to `.env`
- Verifies the token works with GitHub Models
- No manual PAT creation or copying needed!

<details>
<summary>📖 Alternative: Manual Token Creation (Click to expand)</summary>

If you prefer to create a token manually:

1. Go to: https://github.com/settings/tokens
2. Click **"Generate new token (classic)"**
3. Name: `AI Models Access`
4. Select permission: **`models`** ✓
5. Click **"Generate token"**
6. **Copy the token** and add to `.env`:
   ```bash
   API_KEY_github-models-01=github_pat_YOUR_TOKEN_HERE
   ```

</details>

## Step 2: Configure Your System

### Create `keys.json`

```bash
cp keys_example.json keys.json
```

Edit `keys.json`:

```json
{
  "keys": [
    {
      "key_id": "github-gpt4o-01",
      "model_name": "gpt-4o",
      "provider": "github-models",
      "rpm": 15,
      "tpm": 150000,
      "rpd": 150,
      "active": true,
      "tags": {"workload": "heavy", "priority": 1}
    },
    {
      "key_id": "github-gpt4o-mini-01",
      "model_name": "gpt-4o-mini",
      "provider": "github-models",
      "rpm": 15,
      "tpm": 150000,
      "rpd": 150,
      "active": true,
      "tags": {"workload": "medium", "priority": 1}
    },
    {
      "key_id": "github-phi4-01",
      "model_name": "Phi-4",
      "provider": "github-models",
      "rpm": 15,
      "tpm": 150000,
      "rpd": 150,
      "active": true,
      "tags": {"workload": "light", "priority": 1}
    }
  ],
  "config": {
    "max_retries": 2,
    "base_backoff_ms": 500,
    "enable_fallback": true
  }
}
```

### Configure `.env` (Optional)

If you used the device auth script in Step 1, your `.env` is already configured! ✅

Otherwise, create it manually:

```bash
cp .env.example .env
```

Edit `.env`:

```bash
# Redis (required for rate limiting)
REDIS_URL=redis://localhost:6379/0

# Secret Storage
SECRET_STORE_TYPE=env

# GitHub Models - device flow (automatically added by script)
API_KEY_github-models-01=ghu_YOUR_TOKEN_HERE
```

> **Note:** Device flow tokens start with `ghu_` instead of `github_pat_`

## Step 3: Start Redis

```bash
# Windows (if using Docker)
docker run -d -p 6379:6379 redis:latest

# Or use start-servers.ps1 if you have it
.\start-servers.ps1
```

## Step 4: Test It!

```python
from llm.router import RequestRouter

router = RequestRouter()

# Test 1: Simple request
response = router.send_one_shot(
    prompt="Write a Python function to reverse a string",
    model_preference="gpt-4o-mini"
)

if response['success']:
    print("✅ Success!")
    print(f"Model: {response['model']}")
    print(f"Response: {response['content'][:200]}...")
else:
    print(f"❌ Error: {response['error']}")
```

## Step 5: Use in Your Agents

Update your agent initialization to use GitHub Models:

```python
from agents.coder_agent.coder import CoderAgent

agent = CoderAgent(
    agent_id="coder_test",
    use_router=True,  # ← Enable RequestRouter
    model_name="gpt-4o-mini"  # ← Specify GitHub model
)

result = agent.execute_task({
    "requirement": "Create a trading strategy with EMA crossover",
    "task_metadata": {...}
})
```

## Workload Mapping

Use the `workload` parameter for automatic model selection:

```python
# Light tasks (Phi-4)
router.send_one_shot(prompt="...", workload="light")

# Medium tasks (gpt-4o-mini)
router.send_one_shot(prompt="...", workload="medium")

# Heavy tasks (gpt-4o)
router.send_one_shot(prompt="...", workload="heavy")
```

## Key Rotation

Add multiple tokens for automatic rotation using device flow:

```bash
# Run the auth script multiple times with different key IDs
python scripts/github_device_auth.py  # First token: github-models-01
python scripts/github_device_auth.py  # Second token: github-models-02
python scripts/github_device_auth.py  # Third token: github-models-03
```

Update `keys.json`:

```json
{
  "keys": [
    {"key_id": "github-models-01", "model_name": "gpt-4o-mini", ...},
    {"key_id": "github-models-02", "model_name": "gpt-4o-mini", ...},
    {"key_id": "github-models-03", "model_name": "gpt-4o-mini", ...}
  ]
}
```

Result: **3x throughput** (45 RPM instead of 15 RPM)!

> **Tip:** You can use the same GitHub account for all tokens - just run the script multiple times

## Troubleshootingmodels-01"

**Fix:** Re-run the device auth script:
```bash
python scripts/github_device_auth.py
```

Or check your `.env` file has the correct format:
```bash
API_KEY_github-models-01=ghu_...
```

### ❌ "Redis error connecting to localhost:6379"

**Fix:** Start Redis:
```bash
docker run -d -p 6379:6379 redis:latest
```

### ❌ "Provider not found: github-models"

**Fix:** Restart your Python environment to load the updated `providers.py`

### ❌ "401 Unauthorized"

**Fix:** Re-authenticate with device flow:
```bash
python scripts/github_device_auth.py
```

The script will verify your token automatically.

### ❌ Device flow authentication fails

**Possible causes:**
1. **You didn't complete authorization:** Make sure you visit the URL and enter the code
2. **Code expired:** Codes expire after 15 minutes - run the script again
3. **Network issues:** Check your internet connectionvalid
2. Ensure it has `models:read` permission
3. Verify no typos in `.env`

## Available Models

| Model | Best For | Speed | Quality |
|-------|----------|-------|---------|
| **Phi-4** | Simple queries | ⚡⚡⚡ | ⭐⭐ |
| **gpt-4o-mini** | Code generation | ⚡⚡ | ⭐⭐⭐ |
| **gpt-4o** | Complex tasks | ⚡ | ⭐⭐⭐⭐ |
| **o1-mini** | Math/reasoning | ⚡ | ⭐⭐⭐⭐⭐ |

## Next Steps

- **Browse models:** https://github.com/marketplace/models
- **Monitor usage:** `redis-cli KEYS rpm:*`
- **Full migration guide:** [GITHUB_MODELS_MIGRATION.md](GITHUB_MODELS_MIGRATION.md)
- **Device auth details:** [scripts/README.md](scripts/README.md)

## Why Device Flow?

**Before (Manual PATs):**
```
1. Go to GitHub settings
2. Create token
3. Set permissions
4. Copy token
5. Paste into .env
6. Hope you didn't make a typo
```

**Now (Device Flow):**
```bash
python scripts/github_device_auth.py
# Visit URL, enter code, done! ✨
```

**Benefits:**
- ✅ No manual token management
- ✅ No copy-paste errors
- ✅ Automatic verification
- ✅ Easy key rotation (just re-run)
- ✅ Same GitHub account works multiple times
- ✅ Revoke from GitHub settings anytime

You're all set! 🚀
