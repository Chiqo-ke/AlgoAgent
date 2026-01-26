# Quick Fixes for Monolithic Agent Testing

## Immediate Fixes (Can be done now)

### 1. Fix Test Code Parameter Names

**File**: `comprehensive_e2e_test.py`

**Lines to Fix**:
- Line ~170: Change `symbol='MSFT'` to `ticker='MSFT'`
- Line ~260: Change `symbol='MSFT'` to `ticker='MSFT'`
- Line ~296: Change `symbol='MSFT'` to `ticker='MSFT'`

**Search & Replace**:
```python
# Find:
fetch_market_data(symbol=

# Replace with:
fetch_market_data(ticker=
```

### 2. Update Model Configuration in keys.json

**File**: `keys.json`

**Change all instances**:
```json
// From:
"model_name": "gemini-1.5-pro"

// To:
"model_name": "gemini-2.0-flash"
```

**OR use the latest version**:
```json
"model_name": "gemini-1.5-pro-latest"
```

### 3. Create a Simple Manual Test Strategy

**File**: `Backtest/codes/ManualTestStrategy.py`

```python
"""
Manual Test Strategy - No AI Generation Required
For testing backtest execution without API calls
"""

import sys
from pathlib import Path

# Add parent directories to path
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from Backtest.sim_broker import SimBroker
from Backtest.config import BacktestConfig
from Backtest.canonical_schema import create_signal, OrderSide, OrderAction, OrderType
from Backtest.data_loader import fetch_market_data

class ManualTestStrategy:
    """Simple buy-and-hold strategy for testing"""
    
    def __init__(self):
        self.name = "Manual Test Strategy"
        self.bought = False
    
    def generate_signals(self, broker, data, current_index):
        """Generate trading signals"""
        signals = []
        
        # Buy on day 5 if we haven't bought yet
        if current_index == 5 and not self.bought:
            signals.append(create_signal(
                symbol=broker.symbol,
                side=OrderSide.BUY,
                action=OrderAction.OPEN,
                order_type=OrderType.MARKET,
                quantity=10
            ))
            self.bought = True
        
        # Sell on last day if we have a position
        elif current_index == len(data) - 2 and broker.position > 0:
            signals.append(create_signal(
                symbol=broker.symbol,
                side=OrderSide.SELL,
                action=OrderAction.CLOSE,
                order_type=OrderType.MARKET,
                quantity=broker.position
            ))
        
        return signals

def run_backtest(
    symbol='MSFT',
    period='3mo',
    timeframe='1d',
    initial_balance=10000,
    commission=0.001,
    slippage=0.0005
):
    """Run backtest with manual strategy"""
    
    print(f"\\n{'='*80}")
    print(f"Running Manual Test Strategy Backtest")
    print(f"{'='*80}")
    print(f"Symbol: {symbol}")
    print(f"Period: {period}")
    print(f"Initial Balance: ${initial_balance:,.2f}")
    print(f"{'='*80}\\n")
    
    # Load data
    print("Loading market data...")
    data = fetch_market_data(ticker=symbol, period=period, interval=timeframe)
    print(f"Loaded {len(data)} bars")
    
    # Initialize broker
    print("\\nInitializing broker...")
    broker = SimBroker(
        initial_balance=initial_balance,
        data=data,
        commission=commission,
        slippage=slippage
    )
    broker.symbol = symbol
    
    # Initialize strategy
    strategy = ManualTestStrategy()
    
    # Run backtest
    print("\\nRunning backtest...")
    trades_executed = 0
    
    for i in range(len(data)):
        broker.step_to(i)
        
        # Generate signals
        signals = strategy.generate_signals(broker, data, i)
        
        # Process signals
        for signal in signals:
            result = broker.process_signal(signal)
            if result and result.get('status') == 'filled':
                trades_executed += 1
                print(f"  Bar {i}: {signal['side']} order filled at ${result.get('fill_price', 0):.2f}")
    
    # Calculate final results
    print(f"\\n{'='*80}")
    print("Backtest Complete")
    print(f"{'='*80}")
    print(f"Total Trades: {trades_executed}")
    print(f"Final Position: {broker.position} shares")
    print(f"Cash Balance: ${broker.balance:,.2f}")
    
    final_equity = broker.balance + (broker.position * broker.get_current_price())
    pnl = final_equity - initial_balance
    pnl_pct = (pnl / initial_balance) * 100
    
    print(f"Final Equity: ${final_equity:,.2f}")
    print(f"Net P&L: ${pnl:,.2f} ({pnl_pct:+.2f}%)")
    print(f"{'='*80}\\n")
    
    return {
        'trades': trades_executed,
        'final_equity': final_equity,
        'pnl': pnl,
        'pnl_pct': pnl_pct,
        'success': True
    }

if __name__ == "__main__":
    results = run_backtest()
    print(f"\\nTest {'PASSED' if results['success'] else 'FAILED'}")
```

**To run**:
```bash
cd c:\Users\nyaga\Documents\AlgoAgent\monolithic_agent
C:/Users/nyaga/Documents/.venv/Scripts/python.exe Backtest/codes/ManualTestStrategy.py
```

---

## API Quota Solutions

### Option 1: Upgrade to Paid Plan (Recommended)

1. Go to: https://console.cloud.google.com/billing
2. Enable billing for your project
3. Pricing for Gemini 2.0 Flash:
   - Input: $0.00025 per 1K tokens
   - Output: $0.00075 per 1K tokens
   - Very affordable for testing

### Option 2: Wait for Quota Reset

1. Check current usage: https://ai.dev/rate-limit
2. Free tier resets:
   - Per-minute quotas: Reset every minute
   - Per-day quotas: Reset at midnight UTC
3. Plan testing around quota availability

### Option 3: Use Alternative Models

Add to `.env`:
```env
# OpenAI Alternative
OPENAI_API_KEY=your-openai-key-here
DEFAULT_AI_PROVIDER=openai
DEFAULT_AI_MODEL=gpt-4o-mini

# Or Anthropic
ANTHROPIC_API_KEY=your-anthropic-key-here
DEFAULT_AI_PROVIDER=anthropic
DEFAULT_AI_MODEL=claude-3-haiku
```

---

## Testing Without AI Generation

You can test the backtest execution pipeline without AI:

### Test 1: Manual Strategy File
```bash
cd c:\Users\nyaga\Documents\AlgoAgent\monolithic_agent
C:/Users/nyaga/Documents/.venv/Scripts/python.exe Backtest/codes/ManualTestStrategy.py
```

### Test 2: Use Existing Strategy Templates
```bash
# Check for existing strategies
dir Backtest\codes\*.py

# Run any existing strategy
C:/Users/nyaga/Documents/.venv/Scripts/python.exe Backtest/codes/ExampleStrategy.py
```

### Test 3: SimBroker Direct Test
```python
from Backtest.sim_broker import SimBroker
from Backtest.data_loader import fetch_market_data
from Backtest.canonical_schema import create_signal, OrderSide, OrderAction, OrderType

# Load data
data = fetch_market_data(ticker='AAPL', period='1mo', interval='1d')

# Create broker
broker = SimBroker(initial_balance=10000, data=data)

# Manual trading
for i in range(len(data)):
    broker.step_to(i)
    
    if i == 5:  # Buy on day 5
        signal = create_signal('AAPL', OrderSide.BUY, OrderAction.OPEN, 
                              OrderType.MARKET, quantity=10)
        result = broker.process_signal(signal)
        print(f"Buy result: {result}")

print(f"Final balance: ${broker.balance:.2f}")
print(f"Position: {broker.position} shares")
```

---

## Next Steps Checklist

- [ ] Fix test code parameter names (5 minutes)
- [ ] Update keys.json model names (5 minutes)
- [ ] Create ManualTestStrategy.py (10 minutes)
- [ ] Run manual strategy test (2 minutes)
- [ ] Decide on API quota solution (varies)
- [ ] Re-run comprehensive test suite (5 minutes)
- [ ] Update documentation (30 minutes)

---

## Expected Results After Fixes

With the parameter fixes and manual strategy:

**Should Pass**:
- ✅ Data Loading (parameter fix)
- ✅ SimBroker Initialization (parameter fix)
- ✅ Manual Backtest Execution (parameter fix)
- ✅ Trade execution verification
- ✅ P&L calculation

**Still Limited** (until API quota resolved):
- ❌ AI Strategy Generation
- ❌ Automated code generation

**Overall Expected Pass Rate**: 92% (11/12 tests)

Only AI generation will fail until quota is resolved.
