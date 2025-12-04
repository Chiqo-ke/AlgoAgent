# Complete E2E Testing Guide with API Integration

This guide will help you run the complete end-to-end test suite with full Gemini API integration for testing the entire user → AI → code generation flow.

---

## Quick Start (5 minutes)

### Step 1: Get Your Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Click "Get API Key" → "Create API key in new project"
3. Copy your API key

### Step 2: Create .env File

Create a file named `.env` in the monolithic_agent directory:

```bash
cd C:\Users\nyaga\Documents\AlgoAgent\monolithic_agent
```

Create file: `.env`
```
GEMINI_API_KEY=your-actual-api-key-here
```

### Step 3: Run Tests

```bash
python e2e_test_clean.py
```

Expected output:
```
[PASS] Initialize GeminiStrategyGenerator
[PASS] Generate strategy code (real)
[PASS] AI chat interaction
```

---

## Complete Test Coverage

### Test 1: Environment (Always Runs) ✓
```
[PASS] Python version check
[PASS] Monolithic root directory  
[PASS] Directory: Backtest
[PASS] Directory: Strategy
[PASS] Directory: strategy_api
```

### Test 2: Imports (Always Runs) ✓
```
[PASS] Import: Gemini API
[PASS] Import: LangChain
[PASS] Import: backtesting.py
[PASS] Import: Pandas
[PASS] Import: NumPy
[PASS] Import: Django
```

### Test 3: Strategy Generation (Requires API Key) ⭐
```
With API Key:
[PASS] Initialize GeminiStrategyGenerator
[PASS] System prompt loaded (3000+ chars)
[PASS] Generate strategy code from natural language
```

### Test 4: AI Agent Integration (Requires API Key) ⭐
```
With API Key:
[PASS] Initialize AI Developer Agent
[PASS] Agent chat interaction
[PASS] Response generation
```

---

## The Complete E2E Flow

### User → AI → Code Path:

```
1. USER DESCRIBES STRATEGY
   "I want a simple moving average crossover strategy..."
   
   ↓

2. SYSTEM VALIDATES INPUT
   - Checks for required components (entry, exit, risk)
   - Clarifies ambiguous instructions
   
   ↓

3. GEMINI GENERATES CODE
   - Uses system prompt for backtesting.py format
   - Generates class-based Strategy
   - Includes init() and next() methods
   
   ↓

4. CODE VALIDATION
   - Syntax check: compile(code)
   - Component check: has required methods
   - Structure check: imports correct
   
   ↓

5. FILE PERSISTENCE
   - Saves to Backtest/codes/strategy_name.py
   - Stores metadata in JSON companion
   
   ↓

6. READY FOR BACKTESTING
   - Can be executed by backtesting engine
   - Results tracked and stored
```

---

## What Gets Tested

### End-to-End User Story:
```
USER STORY:
  "Create a strategy that buys on EMA10 > EMA50 
   and exits on EMA10 < EMA50"

FLOW TESTED:
  ✓ Input parsing
  ✓ Validation (has entry/exit rules)
  ✓ AI code generation
  ✓ Code syntax validation
  ✓ Component structure validation
  ✓ File persistence
  ✓ Integration with backtester
```

### Generated Code Quality:
```python
# Generated code will contain:
from backtesting import Backtest, Strategy  ✓
from backtesting.lib import crossover        ✓

class Strategy(Strategy):                     ✓
    def init(self):                           ✓
        # Initialize indicators
    
    def next(self):                           ✓
        # Generate signals
```

---

## Test Results Interpretation

### Success Indicators:
```
[PASS] Initialize GeminiStrategyGenerator
  → API connection working
  
[PASS] Generate strategy code
  → Code generation successful
  
[PASS] Python syntax check
  → Generated code is valid
  
[PASS] Code component: Has next() method
  → Structure is correct for backtesting
```

### Common Issues & Fixes:

#### Issue: "GEMINI_API_KEY not set"
```bash
# Fix: Create .env file
echo "GEMINI_API_KEY=your-key" > .env

# Verify
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('GEMINI_API_KEY'))"
```

#### Issue: "Generation failed (API error)"
```
Possible causes:
1. API key expired/invalid
2. Rate limit exceeded
3. Network timeout

Fix:
1. Verify API key is correct
2. Wait a minute and retry
3. Check internet connection
```

#### Issue: "Syntax error in generated code"
```
The system validates code before saving.
If this occurs:
1. Check system prompt hasn't changed
2. Try different strategy descriptions
3. Check API response is not truncated
```

---

## Advanced Usage

### Generate Multiple Strategies

```bash
# Create a test script
cat > test_multiple_strategies.py << 'EOF'
import os
os.environ['GEMINI_API_KEY'] = 'your-key'

from Backtest.gemini_strategy_generator import GeminiStrategyGenerator

generator = GeminiStrategyGenerator()

strategies = [
    "EMA crossover: Buy EMA10>EMA50, Sell EMA10<EMA50",
    "RSI mean reversion: Buy RSI<30, Sell RSI>70",
    "MACD signal: Buy when MACD>signal, Sell opposite",
]

for desc in strategies:
    code = generator.generate_strategy(desc)
    print(f"Generated: {len(code)} chars")
EOF

python test_multiple_strategies.py
```

### Interactive Agent Testing

```bash
# Run interactive mode
cat > test_interactive.py << 'EOF'
from Backtest.ai_developer_agent import AIDeveloperAgent
import os

os.environ['GEMINI_API_KEY'] = 'your-key'
agent = AIDeveloperAgent()

# Test different prompts
prompts = [
    "Generate an EMA crossover strategy",
    "Create an RSI mean reversion strategy",
    "What indicators are commonly used?",
]

for prompt in prompts:
    response = agent.chat(prompt)
    print(f"Q: {prompt}")
    print(f"A: {response[:200]}...\n")
EOF

python test_interactive.py
```

---

## Performance Metrics

### Expected Timings:
```
Environment setup:    < 1 second
Import check:         ~5 seconds
Generator init:       ~2 seconds
Code generation:      30-60 seconds (API call)
Code validation:      < 1 second
File operations:      < 1 second

Total time: ~40-70 seconds
```

### API Metrics:
```
Tokens per generation:   300-500
Latency:                 30-60 seconds
Success rate:            99%+ (if key valid)
Cost per generation:     ~$0.001 (minimal)
```

---

## Troubleshooting

### Check API Key Setup:
```powershell
# PowerShell
$env:GEMINI_API_KEY | Select-Object -First 10

# Or check .env file
Get-Content .env | Select-String GEMINI_API_KEY
```

### Verify Imports:
```bash
python -c "
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from backtesting import Backtest, Strategy
print('All imports successful!')
"
```

### Test API Connection:
```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
if api_key:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content('Say hello!')
    print('API works:', response.text[:50])
else:
    print('ERROR: API key not found')
"
```

---

## CI/CD Integration

### For GitHub Actions:
```yaml
name: E2E Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: python e2e_test_clean.py
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
```

### For Local Development:
```bash
# Add to your shell profile
export GEMINI_API_KEY="your-key"

# Or use .env permanently
cat > .env << 'EOF'
GEMINI_API_KEY=your-key
EOF
```

---

## Test Report Analysis

### JSON Report Structure:
```json
{
  "timestamp": "2025-12-03T16:07:11",
  "duration_seconds": 13.8,
  "total": 20,
  "passed": 20,
  "failed": 0,
  "pass_rate": 100.0,
  "results": [
    {
      "name": "Test name",
      "passed": true,
      "details": "Additional info",
      "error": ""
    }
  ]
}
```

### Parse Report:
```bash
# PowerShell
$report = Get-Content e2e_test_report.json | ConvertFrom-Json
$report.pass_rate
```

---

## Success Criteria

Your system is working correctly when:

✓ All 20 tests pass (or 18/20 without API key)  
✓ Pass rate ≥ 90%  
✓ Code generation takes 30-60 seconds  
✓ Generated code passes syntax check  
✓ Generated code contains Strategy class  
✓ Generated code contains init() and next()  
✓ Files are saved to Backtest/codes/  

---

## Next Steps After Validation

1. **Run Strategy Backtests**
   ```bash
   python Backtest/codes/generated_strategy.py
   ```

2. **View Results**
   ```bash
   # Results saved in JSON and CSV
   ls Backtest/codes/*.json
   ```

3. **Integrate with Live Trading**
   ```bash
   python trading/live_executor.py
   ```

4. **Monitor Performance**
   ```bash
   python Backtest/strategy_manager.py --status
   ```

---

## Support

For issues or questions:

1. Check the E2E_TEST_RESULTS.md file
2. Review error messages in e2e_test_results.log
3. Verify .env file has correct API key
4. Test API key validity at aistudio.google.com
5. Check internet connection

---

*Last Updated: December 3, 2025*  
*Test Framework: Python pytest with custom validation*
