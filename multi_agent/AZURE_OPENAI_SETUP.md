# Azure OpenAI Fallback Setup Guide

## Overview

Your multi-agent system now supports **Azure OpenAI** as a fallback provider when Gemini API keys are exhausted or on cooldown. The existing `RequestRouter` will automatically failover to Azure models when Gemini keys are unavailable.

## What Was Added

### 1. Azure OpenAI Provider (`llm/providers.py`)
- **AzureOpenAIClient** class implementing the `ProviderClient` interface
- Registered as `azure-openai` provider in the provider registry
- Supports Azure-specific endpoint configuration and API versioning

### 2. Configuration Files Updated

#### `.env` (Your Active Configuration)
```bash
# Azure OpenAI Endpoint
AZURE_OPENAI_ENDPOINT=https://algoagent.openai.azure.com/

# Azure OpenAI API Version
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Azure API Keys (replace with your actual keys)
API_KEY_azure-gpt4o-mini-01=your_azure_openai_api_key_here
API_KEY_azure-gpt4o-01=your_azure_openai_api_key_here
```

#### `keys.json` (Key Metadata)
Added two Azure models with **priority 2** (fallback tier):

```json
{
  "key_id": "azure-gpt4o-mini-01",
  "provider": "azure-openai",
  "model_name": "gpt-4o-mini",
  "rpm": 450,
  "tpm": 200000,
  "rpd": 30000,
  "workload": "light",
  "priority": 2
}
```

```json
{
  "key_id": "azure-gpt4o-01",
  "provider": "azure-openai",
  "model_name": "gpt-4o",
  "rpm": 450,
  "tpm": 450000,
  "rpd": 30000,
  "workload": "medium",
  "priority": 2
}
```

### 3. Dependencies (`requirements_llm.txt`)
- `openai>=1.0.0` (Azure OpenAI SDK)
- `azure-identity>=1.15.0` (for Azure authentication)

## Setup Steps

### Step 1: Install Dependencies
```powershell
cd C:\Users\nyaga\Documents\AlgoAgent\multi_agent
pip install -r requirements_llm.txt
```

### Step 2: Configure Azure Deployments

In your Azure OpenAI resource at `https://algoagent.openai.azure.com/`:

1. **Create Model Deployments** with these exact names:
   - `gpt-4o-mini` (for light workloads)
   - `gpt-4o` (for medium/heavy workloads)

   > ⚠️ **Important**: Deployment names in Azure **must match** the `model_name` in `keys.json`

2. **Get API Keys**:
   - Navigate to Azure Portal → Azure OpenAI Service → Keys and Endpoint
   - Copy the API key(s)

### Step 3: Update `.env` with Your API Key
```bash
# Replace these placeholders with your actual Azure OpenAI API key
API_KEY_azure-gpt4o-mini-01=abc123def456ghi789...
API_KEY_azure-gpt4o-01=abc123def456ghi789...
```

### Step 4: Test the Setup

Run this test to verify Azure fallback works:

```python
from llm.router import get_request_router

router = get_request_router()

# Test Azure OpenAI directly
response = router.send_one_shot(
    prompt="Hello! Respond with 'Azure OpenAI is working!'",
    workload="light",
    model_preference="gpt-4o-mini",
    max_output_tokens=50
)

print(response.get('content'))
print(f"Model used: {response.get('model')}")
print(f"Success: {response.get('success')}")
```

## How Fallback Works

### Priority-Based Selection

The `KeyManager` selects keys based on **priority** (lower = preferred):

1. **Priority 1**: All Gemini keys (flash_01, flash_02, pro_01, etc.)
2. **Priority 2**: Azure OpenAI keys (azure-gpt4o-mini-01, azure-gpt4o-01)

### Automatic Failover Scenarios

Azure OpenAI will be used when:

1. **All Gemini keys on cooldown** (429 rate limit errors)
2. **Gemini keys exhausted** (RPM/TPM capacity reached)
3. **Gemini safety blocks** (after retry escalation fails)
4. **Gemini provider errors** (503, 504 gateway timeouts)

### Workload Mapping

The router will select models based on workload tier:

- **Light**: `gemini-2.0-flash` → fallback to `gpt-4o-mini`
- **Medium**: `gemini-2.0-flash` → `gemini-2.5-pro` → fallback to `gpt-4o`
- **Heavy**: `gemini-2.5-pro` → fallback to `gpt-4o`

## Usage Examples

### Example 1: Agent with Automatic Fallback

```python
from llm.router import get_request_router

router = get_request_router()

# RequestRouter will automatically try Gemini first, then Azure
response = router.send_chat(
    conv_id="strategy_001",
    prompt="Generate a trading strategy for AAPL",
    workload="medium",  # Will try gemini-2.0-flash, then gpt-4o
    max_output_tokens=4096,
    temperature=0.1
)

if response.get('success'):
    print(response['content'])
    print(f"Provider used: {response.get('provider', 'unknown')}")
else:
    print(f"Error: {response.get('error')}")
```

### Example 2: Force Azure OpenAI

```python
# Explicitly request Azure model
response = router.send_one_shot(
    prompt="Analyze this code...",
    model_preference="gpt-4o",  # Azure deployment name
    workload="medium",
    max_output_tokens=2048
)
```

### Example 3: Monitor Key Health

```python
from keys.manager import KeyManager

manager = KeyManager.get_instance()

# Check which keys are healthy
healthy_keys = [
    (key.key_id, key.provider, key.model_name)
    for key in manager.active_keys
    if not manager.rate_limiter.is_in_cooldown(key.key_id)
]

print("Healthy keys:")
for key_id, provider, model in healthy_keys:
    print(f"  - {key_id} ({provider}/{model})")
```

## Rate Limits (Azure vs Gemini)

### Gemini (Free Tier)
- **Flash models**: 15 RPM, 1M TPM
- **Pro models**: 2 RPM (some), 15 RPM (others)

### Azure OpenAI (Pay-as-you-go)
- **gpt-4o-mini**: 450 RPM, 200K TPM ⚡
- **gpt-4o**: 450 RPM, 450K TPM ⚡

**Result**: Azure provides **30x more capacity** than Gemini free tier!

## Cost Considerations

### Pricing Comparison (Approximate)
- **Gemini 2.0 Flash**: Free (rate-limited)
- **Azure gpt-4o-mini**: ~$0.15 per 1M input tokens
- **Azure gpt-4o**: ~$2.50 per 1M input tokens

**Recommendation**: Use Gemini as primary (free), Azure as fallback for:
- High-traffic periods
- When Gemini rate limits are hit
- Production workloads requiring guaranteed availability

## Monitoring & Debugging

### Enable Debug Logging

```python
import logging
logging.getLogger('llm.router').setLevel(logging.DEBUG)
logging.getLogger('keys.manager').setLevel(logging.DEBUG)
```

### Check Redis for Rate Limit Status

```powershell
# Connect to Redis
redis-cli

# Check key cooldowns
KEYS cooldown:*

# Check RPM usage
KEYS rpm:*

# Check TPM reservations
KEYS tpm:*
```

## Troubleshooting

### Issue: "AZURE_OPENAI_ENDPOINT not configured"

**Solution**: Ensure `.env` contains:
```bash
AZURE_OPENAI_ENDPOINT=https://algoagent.openai.azure.com/
```

### Issue: "Model 'gpt-4o' not found"

**Solution**: 
1. Verify deployment name in Azure Portal matches `keys.json`
2. Check Azure resource endpoint is correct
3. Ensure API key has access to the deployment

### Issue: Azure always used (not falling back from Gemini)

**Possible Causes**:
1. Gemini keys have `priority: 2` or higher (should be `priority: 1`)
2. All Gemini keys marked as `active: false`
3. Redis not running (rate limiting fails)

**Solution**: Check `keys.json` priorities and Redis connectivity

### Issue: 401 Unauthorized from Azure

**Solution**: 
1. Verify API key is correct in `.env`
2. Check API key permissions in Azure Portal
3. Ensure deployment is in the same region as the endpoint

## Advanced: Cost Optimization

### Track Token Usage

```python
response = router.send_chat(
    conv_id="test",
    prompt="Hello",
    workload="light"
)

tokens = response.get('tokens', {})
print(f"Input: {tokens.get('input')} tokens")
print(f"Output: {tokens.get('output')} tokens")
print(f"Total: {tokens.get('total')} tokens")
```

### Prefer Cheaper Models

Adjust `workload_model_mapping` in `keys.json`:

```json
{
  "workload_model_mapping": {
    "light": ["gemini-2.0-flash", "gpt-4o-mini"],
    "medium": ["gemini-2.0-flash", "gpt-4o-mini", "gpt-4o"],
    "heavy": ["gemini-2.5-pro", "gpt-4o"]
  }
}
```

This ensures `gpt-4o-mini` is tried before `gpt-4o` for medium workloads.

## Next Steps

1. **Install dependencies**: `pip install -r requirements_llm.txt`
2. **Create Azure deployments**: `gpt-4o-mini` and `gpt-4o`
3. **Add your Azure API key** to `.env`
4. **Test the integration** with the test script above
5. **Monitor usage** via Azure Portal and Redis

---

**Questions?** Check the [Azure OpenAI Python Quickstart](https://learn.microsoft.com/en-us/azure/ai-services/openai/quickstart?tabs=command-line&pivots=programming-language-python)
