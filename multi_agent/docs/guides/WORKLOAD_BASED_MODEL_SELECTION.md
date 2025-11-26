# Workload-Based Model Selection Guide

## Overview

The LLM Router now supports intelligent workload-based model selection, allowing you to automatically use the most appropriate Gemini model based on task complexity:

- **Light workload**: `gemini-2.0-flash-exp` - Fast, cost-effective for simple tasks
- **Medium workload**: `gemini-1.5-pro` - Balanced performance for moderate complexity
- **Heavy workload**: `gemini-exp-1206` - Advanced model for complex reasoning

## Model Configuration

### Current Setup (`keys.json`)

```json
{
  "keys": [
    {
      "key_id": "gemini-key-01",
      "model_name": "gemini-2.0-flash-exp",
      "provider": "gemini",
      "tags": {
        "workload": "light",
        "priority": 1
      }
    },
    {
      "key_id": "gemini-key-04",
      "model_name": "gemini-1.5-pro",
      "provider": "gemini",
      "tags": {
        "workload": "medium",
        "priority": 4
      }
    },
    {
      "key_id": "gemini-key-05",
      "model_name": "gemini-exp-1206",
      "provider": "gemini",
      "tags": {
        "workload": "heavy",
        "priority": 5
      }
    }
  ]
}
```

### Rate Limits by Model

| Model | RPM | TPM | RPD | Best For |
|-------|-----|-----|-----|----------|
| `gemini-2.0-flash-exp` | 15 | 1M | 1500 | Quick responses, simple tasks |
| `gemini-1.5-pro` | 2 | 32K | 50 | Complex reasoning, longer context |
| `gemini-exp-1206` | 2 | 32K | 50 | Advanced reasoning, critical tasks |

## Safety Settings

All models have safety filters **disabled** for code generation:

```python
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
]
```

This ensures code generation isn't blocked by false positives.

## Usage Examples

### 1. Using Workload Parameter

```python
from llm.router import get_request_router

router = get_request_router()

# Light workload - use Flash
response = router.send_one_shot(
    prompt="Generate a simple TODO list",
    workload="light",
    max_output_tokens=500
)

# Medium workload - use Pro
response = router.send_one_shot(
    prompt="Analyze this strategy and suggest improvements",
    workload="medium",
    max_output_tokens=2000
)

# Heavy workload - use Pro Preview
response = router.send_one_shot(
    prompt="Design a complex multi-strategy trading system with risk management",
    workload="heavy",
    max_output_tokens=4000
)
```

### 2. Using Model Preference

```python
# Explicitly request a specific model
response = router.send_one_shot(
    prompt="Generate strategy code",
    model_preference="gemini-exp-1206",
    max_output_tokens=3000
)
```

### 3. Let Router Choose (Default)

```python
# Router selects based on availability and rate limits
response = router.send_one_shot(
    prompt="Create a simple EMA crossover strategy",
    max_output_tokens=1500
)
```

## Workload Selection Guidelines

### Light Workload (`gemini-2.0-flash-exp`)

**Use for:**
- Simple TODO list generation
- Basic data validation
- Quick summaries
- Template-based code generation
- Chat responses
- Simple indicator calculations

**Characteristics:**
- Fastest response time
- Highest rate limits (15 RPM)
- Most cost-effective
- Good for iteration

### Medium Workload (`gemini-1.5-pro`)

**Use for:**
- Strategy analysis and improvements
- Complex indicator logic
- Multi-step reasoning
- Code review and debugging
- Integration tasks
- Risk management logic

**Characteristics:**
- Balanced performance
- Moderate rate limits (2 RPM)
- Better reasoning than Flash
- Longer context window

### Heavy Workload (`gemini-exp-1206`)

**Use for:**
- Complex system architecture
- Multi-strategy coordination
- Advanced backtesting logic
- Critical production code
- Mathematical modeling
- Portfolio optimization

**Characteristics:**
- Best reasoning capabilities
- Lower rate limits (2 RPM)
- Latest experimental features
- Reserve for complex tasks

## Fallback Strategy

The router automatically falls back in this order:

1. **First**: Try keys with matching workload tag
2. **Second**: If none available, try any workload
3. **Third**: If model preference specified, try any model
4. **Finally**: Return error if all keys exhausted

Example fallback flow:
```
Request: workload="heavy", model_preference="gemini-exp-1206"
  ↓
Try keys with workload="heavy" and model="gemini-exp-1206"
  ↓ (rate limited)
Try keys with any workload and model="gemini-exp-1206"
  ↓ (rate limited)
Try any available key
  ↓ (all exhausted)
Return error with retry-after
```

## Integration with Existing Code

### Planner Service

```python
# planner_service/planner.py
response = router.send_one_shot(
    prompt=planner_prompt,
    workload="light",  # TODO generation is simple
    max_output_tokens=2000
)
```

### Coder Agent

```python
# agents/coder_agent/coder.py
response = router.send_one_shot(
    prompt=code_generation_prompt,
    workload="medium",  # Code generation needs reasoning
    max_output_tokens=4000
)
```

### Debugger Agent

```python
# agents/debugger_agent/debugger.py
response = router.send_one_shot(
    prompt=debug_analysis_prompt,
    workload="heavy",  # Complex debugging needs best model
    max_output_tokens=3000
)
```

## Monitoring and Metrics

### Check Key Status

```python
from keys.manager import get_key_manager

manager = get_key_manager()

# Get all key statuses
statuses = manager.get_all_key_statuses()
for status in statuses:
    print(f"{status['key_id']}: {status['model']} - "
          f"Cooldown: {status['in_cooldown']} - "
          f"RPM: {status['rpm_usage']}")
```

### Health Check

```python
from llm.router import get_request_router

router = get_request_router()
health = router.health_check()

if not health['healthy']:
    print(f"Router unhealthy: {health}")
```

## Troubleshooting

### Error: "models/any is not found"

**Cause**: Invalid model name in `keys.json`

**Fix**: Update all keys to use valid model names:
- `gemini-2.0-flash-exp`
- `gemini-1.5-pro`
- `gemini-exp-1206`

### Error: "All keys exhausted"

**Cause**: All keys in cooldown due to rate limits

**Solutions**:
1. Wait for cooldown to expire (30-60 seconds)
2. Add more API keys to `keys.json` and `.env`
3. Use lighter workload to access faster models
4. Reduce request frequency

### Safety Filter Blocking Responses

**Status**: ✅ Fixed - All safety filters disabled

The updated `GeminiClient` bypasses all safety filters using `BLOCK_NONE` threshold.

### Keys Not Loading

**Check**:
1. `keys.json` exists in `multi_agent/` directory
2. `.env` file has `API_KEY_gemini_key_XX` entries
3. Redis is running: `docker start redis`
4. Key format matches: underscores in env, hyphens in keys.json

## Best Practices

1. **Match workload to task complexity**
   - Don't use heavy models for simple tasks
   - Reserve Pro Preview for critical work

2. **Monitor rate limits**
   - Flash models have higher limits
   - Distribute load across multiple keys

3. **Use conversation memory wisely**
   - Long conversations consume more tokens
   - Truncate history for simple tasks

4. **Handle failures gracefully**
   - Check `success` field in response
   - Retry with different workload if needed
   - Log failures for debugging

5. **Test with different workloads**
   - Compare quality vs speed
   - Find optimal workload for each task type

## Environment Variables

Required in `.env`:

```bash
# Enable multi-key router
LLM_MULTI_KEY_ROUTER_ENABLED=true

# Retry configuration
LLM_MAX_RETRIES=3
LLM_BASE_BACKOFF_MS=500

# Redis
REDIS_URL=redis://localhost:6379/0

# API Keys (match keys.json key_id)
API_KEY_gemini_key_01=AIzaSy...
API_KEY_gemini_key_02=AIzaSy...
# ... etc
```

## Summary

✅ **Fixed Issues:**
- Invalid model name `"any"` → Valid Gemini models
- Safety filters blocking responses → All filters disabled
- No workload-based selection → Added workload parameter

✅ **New Capabilities:**
- Automatic model selection by workload
- Intelligent fallback strategy
- Safety filter bypass for code generation
- Better rate limit management

✅ **Models Available:**
- `gemini-2.0-flash-exp` - Light workloads (15 RPM)
- `gemini-1.5-pro` - Medium workloads (2 RPM)
- `gemini-exp-1206` - Heavy workloads (2 RPM)
