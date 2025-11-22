# Quick Test Guide - Safety Filter Retry

## What We Changed

Your system now automatically retries with Gemini 2.5 Pro when safety filters block code generation.

## Test It Now

### 1. Check Configuration ✅
```bash
python test_safety_config.py
```

Expected: "✅ RETRY MECHANISM READY"

### 2. Start CLI
```bash
python cli.py
```

You should see:
```
✓ Loaded GEMINI_API_KEY from .env
[PlannerService] Initialized with RequestRouter (model: gemini-2.5-flash)
[KeyManager] Loaded 5 active keys from keys.json
```

### 3. Submit Test Request

Try this request (contains terms that trigger safety filters):

```
>>> submit Buy when 20 EMA crosses above 40 EMA. Set the stop loss 10 pips below entry and take profit 40 pips above entry.
```

### 4. Watch For Retry Messages

**Scenario A: Flash Succeeds (Best Case)**
```
[CoderAgent] Generating code...
✓ Code generated in 34.56s
```

**Scenario B: Flash Fails, Pro Succeeds (Retry Working!)**
```
[CoderAgent] Generating code...
[CoderAgent] Safety filter triggered with gemini-2.5-flash
[CoderAgent] 🔄 Retrying with Gemini 2.5 Pro...
[CoderAgent] ✓ Pro model succeeded
✓ Code generated in 45.23s
```

**Scenario C: Both Fail, Template Used (Graceful Degradation)**
```
[CoderAgent] Generating code...
[CoderAgent] Safety filter triggered with gemini-2.5-flash
[CoderAgent] 🔄 Retrying with Gemini 2.5 Pro...
[CoderAgent] Pro model also failed
[CoderAgent] ⚠️  Falling back to template mode...
✓ Strategy file created (from template)
```

### 5. Execute the Workflow

```
>>> execute wf_xxxxx
```

Watch for:
- Task 1: Data loading (CoderAgent)
- Task 2: Indicators (ArchitectAgent) ← May trigger retry
- Task 3: Entry logic (CoderAgent) ← May trigger retry
- Task 4: Exit logic (CoderAgent) ← May trigger retry

### 6. Check Results

```bash
# View generated strategy
ls Backtest/codes/ai_strategy_*.py

# View workflow status
>>> status wf_xxxxx
```

## What Success Looks Like

### With Retry Working
- Higher success rate for AI generation
- Fewer template fallbacks
- Better quality code (Pro model understanding)
- Logs show retry activity

### Expected Retry Rate
- ~20-30% of requests trigger safety filters
- ~80-90% of retries succeed with Pro
- ~10-20% fall back to template

## Troubleshooting

### No Retry Happening
**Check:**
1. Pro keys configured? `API_KEY_gemini_pro_01` in .env
2. Router enabled? `LLM_MULTI_KEY_ROUTER_ENABLED=true`
3. Redis running? `docker ps | findstr redis`

### Always Falls Back to Template
**Possible causes:**
1. Both Flash and Pro keys hitting quota
2. Prompt triggers even Pro's safety filters
3. API keys invalid

**Solution:** Check API key validity on Google AI Studio

### Router Disabled
**If you see:** "RequestRouter disabled - falling back to direct API calls"

**Fix:**
1. Verify `.env` location (should be in AlgoAgent root)
2. Check `LLM_MULTI_KEY_ROUTER_ENABLED=true`
3. Restart CLI after changes

## Key Metrics to Track

### Success Rates
- Flash-only success: ~50%
- Flash + Pro retry: ~80-90%
- Template fallback: ~10-20%

### Performance
- Flash generation: 10-20 seconds
- Pro generation: 30-60 seconds
- Template generation: <1 second

### Cost
- Flash: $0.10 per 1M tokens
- Pro: $0.30 per 1M tokens
- Template: Free

## Common Requests to Test

### Low Risk (Flash Should Work)
```
>>> submit Load OHLCV data from CSV and calculate 14-period RSI indicator
```

### Medium Risk (May Trigger Retry)
```
>>> submit Create MACD crossover strategy with entry and exit signals
```

### High Risk (Likely Triggers Retry)
```
>>> submit Buy when RSI<30 with stop loss 2% below entry and take profit 5% above entry
```

### Very High Risk (May Need Template)
```
>>> submit Implement scalping strategy with 10 pip stop loss and 20 pip take profit for EURUSD trading
```

## Next Steps After Testing

1. **Monitor Metrics**
   - Track retry rates in logs
   - Calculate cost per generation
   - Measure success rates

2. **Optimize Strategy**
   - Use Pro for complex tasks
   - Use Flash for simple tasks
   - Adjust based on retry patterns

3. **Production Tuning**
   - Add monitoring/alerting
   - Implement cost caps
   - Set up API key rotation

## Quick Commands

```bash
# Check configuration
python test_safety_config.py

# Start CLI
python cli.py

# Submit test request
>>> submit Buy when 20 EMA crosses above 40 EMA. Set stop loss 10 pips below and take profit 40 pips above.

# Execute workflow
>>> execute wf_xxxxx

# Check status
>>> status wf_xxxxx

# List all workflows
>>> list

# Exit
>>> exit
```

---

**Ready to test!** The retry mechanism is now active and will automatically use Gemini Pro when Flash hits safety filters. 🚀
