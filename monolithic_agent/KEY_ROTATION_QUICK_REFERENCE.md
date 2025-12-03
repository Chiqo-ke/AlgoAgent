# Key Rotation Quick Reference

## TL;DR - Get Started in 2 Minutes

### Development (Single Key)
```bash
export GEMINI_API_KEY=your-key-here
python -m Backtest.gemini_strategy_generator "Your strategy description"
```
✓ Works immediately, no setup needed.

### Production (Multi-Key)
```bash
# 1. Create keys.json from template
cp keys_example.json keys.json
# Edit keys.json with your key metadata

# 2. Configure .env
cat >> .env << EOF
ENABLE_KEY_ROTATION=true
SECRET_STORE_TYPE=env
GEMINI_KEY_flash_01=your-key-1
GEMINI_KEY_flash_02=your-key-2
EOF

# 3. Start using
python -m Backtest.gemini_strategy_generator "Your strategy description"
```
✓ Automatic failover, load distribution, rate limiting.

---

## File Reference

| File | Purpose | When to Edit |
|------|---------|--------------|
| `.env.example` | Environment template | Reference for setup |
| `keys_example.json` | Key metadata template | Copy to `keys.json` |
| `Backtest/key_rotation.py` | Key manager implementation | Almost never |
| `Backtest/gemini_strategy_generator.py` | AI strategy generator | Already integrated |
| `KEY_ROTATION_INTEGRATION.md` | Full documentation | Reference guide |

---

## Configuration Cheatsheet

### Enable Rotation
```bash
ENABLE_KEY_ROTATION=true
```

### Secret Storage Options
```bash
# Environment variables (development)
SECRET_STORE_TYPE=env
GEMINI_KEY_flash_01=sk-...
GEMINI_KEY_flash_02=sk-...

# HashiCorp Vault (production)
SECRET_STORE_TYPE=vault
VAULT_ADDR=https://vault.example.com
VAULT_TOKEN=s.xxx

# AWS Secrets Manager (production)
SECRET_STORE_TYPE=aws
AWS_REGION=us-east-1

# Azure Key Vault (production)
SECRET_STORE_TYPE=azure
AZURE_VAULT_URL=https://your-vault.vault.azure.net/
```

### Rate Limiting (in keys.json)
```json
{
  "key_id": "flash_01",
  "rpm": 60,        // requests per minute
  "tpm": 1000000,   // tokens per minute
  "rpd": 500        // requests per day
}
```

### Optional: Redis
```bash
REDIS_URL=redis://localhost:6379/0
```

---

## Usage Examples

### Automatic (Recommended)
```python
from Backtest.gemini_strategy_generator import GeminiStrategyGenerator

# Uses rotation if ENABLE_KEY_ROTATION=true, else single key
generator = GeminiStrategyGenerator()
code = generator.generate_strategy("Buy on RSI < 30")
```

### Explicit Single Key
```python
generator = GeminiStrategyGenerator(use_key_rotation=False)
```

### Explicit Multi-Key
```python
generator = GeminiStrategyGenerator(use_key_rotation=True)
```

### Check Key Health
```python
from Backtest.key_rotation import get_key_manager

manager = get_key_manager()
health = manager.get_health_status()
print(health)
```

---

## Common Tasks

### Add a New Key

1. **Update keys.json**:
```json
{
  "key_id": "flash_03",
  "model_name": "gemini-2.5-flash",
  "rpm": 60,
  "tpm": 1000000
}
```

2. **Add to .env**:
```bash
GEMINI_KEY_flash_03=your-new-key
```

3. **Done!** System picks it up automatically on next restart.

### Monitor Keys

```python
from Backtest.key_rotation import get_key_manager

manager = get_key_manager()
health = manager.get_health_status()

for key_id, status in health.items():
    print(f"{key_id}: {status['success_count']} successes, {status['error_count']} errors")
```

### Force Disable Rotation

```bash
# Remove or set to false
ENABLE_KEY_ROTATION=false

# Or just keep GEMINI_API_KEY set
export GEMINI_API_KEY=your-key
# System will use single key mode
```

### Handle Failover

Already automatic! If a key fails:
- Exponential backoff cooldown applied
- Next available key tried
- Request succeeds or fails after all keys exhausted

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No API keys available" | Check `ENABLE_KEY_ROTATION=true` and `keys.json` exists |
| Keys in cooldown | Check error logs, verify API keys are valid |
| Redis fails | Ensure Redis running or disable with `REDIS_URL=""` |
| Secret not found | Verify `GEMINI_KEY_{key_id}` variables are set |
| Generation slow | Multiple keys provided? Reduce `rpm`/`tpm` limits |

---

## Fallback Behavior

If rotation fails, system **doesn't break**:
- ✓ Single `GEMINI_API_KEY` still works
- ✓ Redis connection failure = continue without rate limiting
- ✓ Key error = try next key automatically
- ✓ All keys exhausted = raise exception with clear message

---

## Security Notes

✓ Never commit `.env` or `keys.json` to git  
✓ Use `.env.example` as template for developers  
✓ Production: Use Vault/AWS/Azure, not environment variables  
✓ Rotate keys every 90 days  
✓ Monitor key usage in logs  

---

## Files Created

```
monolithic_agent/
├── .env.example                    # Environment template
├── keys_example.json               # Key metadata template
├── KEY_ROTATION_INTEGRATION.md     # Full documentation (this file's parent)
├── KEY_ROTATION_QUICK_REFERENCE.md # This file
└── Backtest/
    ├── key_rotation.py             # Key manager (395 lines)
    └── gemini_strategy_generator.py # Updated with rotation support
```

---

## Next Steps

1. ✓ Copy `keys_example.json` to `keys.json`
2. ✓ Add your API keys to `.env`
3. ✓ Set `ENABLE_KEY_ROTATION=true`
4. ✓ Run your first strategy with rotation enabled
5. ✓ Monitor health with `manager.get_health_status()`
6. ✓ (Optional) Set up Redis for atomic rate limiting
7. ✓ (Optional) Move to Vault/AWS/Azure for production

---

**That's it!** The system handles the rest automatically.
