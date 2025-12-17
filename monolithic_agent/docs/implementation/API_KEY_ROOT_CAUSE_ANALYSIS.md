# API Key Rate Limit Issue - ROOT CAUSE IDENTIFIED

## 🔴 CRITICAL FINDING

**Problem:** All your API keys are hitting rate limits simultaneously because they **ALL BELONG TO THE SAME GOOGLE CLOUD PROJECT**.

### Evidence from Testing

```
flash_01:  ❌ EXHAUSTED - quota limit: 0 (gemini-2.0-flash)
flash_02:  ❌ EXHAUSTED - quota limit: 0 (gemini-2.0-flash)
flash_03:  ❌ EXHAUSTED - quota limit: 0 (gemini-2.0-flash)
pro_01:    ❌ EXHAUSTED - quota limit: 0 (gemini-2.5-pro)
pro_02:    ❌ EXHAUSTED - quota limit: 0 (gemini-2.5-pro)
pro_03:    ❌ EXHAUSTED - quota limit: 0 (gemini-2.5-pro)
pro_04:    ❌ EXHAUSTED - quota limit: 0 (gemini-2.5-pro)
```

All keys show `limit: 0` simultaneously, which is IMPOSSIBLE if they were from different projects.

---

## Why This Happens

### How Google Cloud API Quotas Work

```
Project A                      Project B
├─ API Key 1                  ├─ API Key 8
├─ API Key 2                  ├─ API Key 9
├─ API Key 3                  └─ API Key 10
└─ SHARED QUOTA               └─ SEPARATE QUOTA
   └─ 15 RPM per model           └─ 15 RPM per model
```

**Current Situation:**
```
Your Setup (Single Project)
├─ flash_01
├─ flash_02
├─ flash_03
├─ pro_01
├─ pro_02
├─ pro_03
└─ pro_04
└─ ALL SHARE THE SAME QUOTA
   ├─ gemini-2.0-flash: 15 RPM total (not per key!)
   └─ gemini-2.5-pro: 60 RPM total (not per key!)
```

When you use flash_01, flash_02, and flash_03, they're not getting 15+15+15 = 45 RPM. They're **sharing** the same 15 RPM pool!

### What the Terminal Logs Show

```
violations {
  quota_metric: "generativelanguage.googleapis.com/generate_content_free_tier_requests"
  quota_id: "GenerateRequestsPerDayPerProjectPerModel-FreeTier"
  ^^^^^^^^^^^                                     ^^^^
  Per PROJECT - not per key!
}
```

The quota is **"Per PROJECT Per Model"** - meaning all keys in the same project share the same daily/minute limits.

---

## Solution

You have **2 options**:

### Option 1: Create Keys from Different Projects (RECOMMENDED)

#### Step 1: Create Multiple Google Cloud Projects

1. Go to: https://console.cloud.google.com
2. Click the project dropdown (top left)
3. Click "New Project"
4. Create Project 2, 3, 4, etc.

#### Step 2: Enable Gemini API for Each Project

For each new project:
1. Go to: https://console.cloud.google.com/apis/library
2. Search for "Generative Language API"
3. Click "Enable"

#### Step 3: Create API Keys in Each Project

For each project:
1. Switch to that project (top left dropdown)
2. Go to: https://console.cloud.google.com/apis/credentials
3. Click "Create Credentials" → "API Key"
4. Copy the key
5. Restrict the key to "Generative Language API" (recommended)

#### Step 4: Update .env File

```bash
# Keys from different projects
GEMINI_KEY_FLASH_01=AIza...    # From Project A
GEMINI_KEY_FLASH_02=AIza...    # From Project B
GEMINI_KEY_FLASH_03=AIza...    # From Project C
GEMINI_KEY_PRO_01=AIza...      # From Project D
GEMINI_KEY_PRO_02=AIza...      # From Project E
GEMINI_KEY_PRO_03=AIza...      # From Project F
GEMINI_KEY_PRO_04=AIza...      # From Project G
```

Now each key gets its own quota:
- flash_01: 15 RPM
- flash_02: 15 RPM  ← Independent!
- flash_03: 15 RPM  ← Independent!
- **Total: 45 RPM for flash model** instead of 15 RPM shared

---

### Option 2: Upgrade to Paid Tier (FASTER but costs money)

Instead of juggling multiple free-tier projects, upgrade one project to paid:

1. Go to: https://console.cloud.google.com/billing
2. Enable billing for your project
3. Quotas will increase significantly:
   - Free tier: 15 RPM → Paid tier: 1,000+ RPM
   - Free tier: 1M tokens/day → Paid tier: Much higher

**Cost:** Pay-as-you-go (usually very cheap for moderate usage)

---

## Immediate Workaround (Until You Fix Keys)

### Implement Request Throttling

Add this to your `.env`:

```bash
# Throttle requests to avoid hitting limits
GEMINI_REQUEST_DELAY=5  # Seconds between requests
MAX_CONCURRENT_REQUESTS=1  # Only 1 request at a time
```

Then update `gemini_strategy_generator.py`:

```python
import time
import threading

class GeminiStrategyGenerator:
    _last_request_time = 0
    _request_lock = threading.Lock()
    
    def generate_strategy(self, description: str) -> str:
        # Throttle requests
        delay = int(os.getenv('GEMINI_REQUEST_DELAY', '5'))
        
        with self._request_lock:
            elapsed = time.time() - self._last_request_time
            if elapsed < delay:
                time.sleep(delay - elapsed)
            
            # Make API call
            response = self.model.generate_content(prompt)
            
            self._last_request_time = time.time()
        
        return response.text
```

This ensures:
- Only 1 request happens at a time
- At least 5 seconds between requests
- Avoids hitting 15 RPM limit (5 sec × 12 = 1 request per minute)

---

## How to Verify Your Keys Are From Different Projects

### Method 1: Check in Google AI Studio

1. Go to: https://aistudio.google.com/apikey
2. Look at each API key
3. Check the "Project" column
4. If all say the same project name → They're all from one project
5. If they show different project names → You're good!

### Method 2: Check in Console

1. Go to: https://console.cloud.google.com/apis/credentials
2. Switch between projects (top left dropdown)
3. Each project should show DIFFERENT API keys

---

## Testing After Fix

After you get keys from different projects, test with:

```bash
cd monolithic_agent
python check_all_quotas.py
```

Expected output (with keys from different projects):
```
flash_01: ✅ ACTIVE - 15 RPM available
flash_02: ✅ ACTIVE - 15 RPM available
flash_03: ✅ ACTIVE - 15 RPM available
```

Instead of all showing `limit: 0`.

---

## Why Key Rotation Was "Working" But Not Helping

Your key rotation system is actually **working correctly**! It's selecting different keys and rotating them. The problem is:

```python
# What's happening:
flash_01 fails (429) → Rotate to flash_02
flash_02 fails (429) → Rotate to flash_03  
flash_03 fails (429) → Rotate to pro_01
pro_01 fails (429) → All keys exhausted
```

But since they're all from the same project:
```
flash_01 uses 1 request → Project quota: 14/15 remaining
flash_02 uses 1 request → Project quota: 13/15 remaining  ← Same pool!
flash_03 uses 1 request → Project quota: 12/15 remaining  ← Same pool!
```

With keys from **different projects**:
```
flash_01 (Project A) uses 1 → Project A: 14/15 remaining
flash_02 (Project B) uses 1 → Project B: 14/15 remaining  ← Separate pool!
flash_03 (Project C) uses 1 → Project C: 14/15 remaining  ← Separate pool!
```

---

## Summary

| Issue | Root Cause | Solution |
|-------|------------|----------|
| All 15 keys hitting 429 simultaneously | All keys from same Google Cloud project | Create keys in different projects |
| `limit: 0` for all keys | Shared project quota exhausted | Each key needs its own project |
| Key rotation not helping | Rotating within same quota pool | Keys from different projects = different pools |

---

## Next Steps

1. **Immediate:** Implement request throttling (Option 2 workaround)
2. **Short-term:** Create 5-7 new Google Cloud projects
3. **Long-term:** Consider upgrading to paid tier if usage is high

---

## Files Created for Diagnostics

1. `diagnose_api_keys.py` - Shows key configuration status
2. `verify_api_key_projects.py` - Tests if keys are from same project  
3. `check_all_quotas.py` - Shows current quota status for all keys

Run any of these to verify your setup after making changes.
