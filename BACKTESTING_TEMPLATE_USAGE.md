# AlgoAgent Backtesting Template & Usage Guide

**Framework:** backtesting.py  
**Strategy API:** Django REST Framework  
**Validation:** Automated background validation  

---

## Template 1: Basic Strategy Structure

```python
# Example: strategies/simple_moving_average.py

from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.test import SMA, GOOG
import pandas as pd

class SimpleMovingAverageStrategy(Strategy):
    """
    Basic SMA crossover strategy
    - Enter: When fast SMA crosses above slow SMA
    - Exit: When fast SMA crosses below slow SMA
    """
    
    # Define parameters with defaults
    n1 = 10  # Fast moving average period
    n2 = 20  # Slow moving average period
    
    def init(self):
        """Initialize strategy indicators"""
        # Precompute indicators (faster execution)
        price = self.data.Close
        self.ma1 = self.I(lambda x: pd.Series(x).rolling(self.n1).mean(), price)
        self.ma2 = self.I(lambda x: pd.Series(x).rolling(self.n2).mean(), price)
    
    def next(self):
        """Execute strategy logic on each bar"""
        # Trading signals
        if crossover(self.ma1, self.ma2):
            # Fast MA crosses above slow MA = BUY signal
            if not self.position:
                self.buy()
        elif crossover(self.ma2, self.ma1):
            # Fast MA crosses below slow MA = SELL signal
            if self.position:
                self.position.close()

# Usage
if __name__ == '__main__':
    bt = Backtest(GOOG, SimpleMovingAverageStrategy, 
                  cash=10000, commission=.002)
    results = bt.run()
    print(results)
```

---

## Template 2: Advanced Strategy with Risk Management

```python
# Example: strategies/advanced_momentum.py

from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd

class AdvancedMomentumStrategy(Strategy):
    """
    Momentum strategy with risk management
    - Entry: Momentum confirmation
    - Exit: Stop loss or profit target
    - Risk Management: Position sizing, max drawdown
    """
    
    # Parameters
    momentum_period = 14
    stop_loss_pct = 2.0
    profit_target_pct = 5.0
    max_position_size = 0.1  # 10% of portfolio per trade
    
    def init(self):
        """Initialize indicators"""
        close = self.data.Close
        
        # Calculate momentum (ROC - Rate of Change)
        self.momentum = self.I(self._calculate_momentum, close, self.momentum_period)
        
        # Track entry prices for stop loss/target
        self.entry_price = None
    
    @staticmethod
    def _calculate_momentum(close, period):
        """Calculate momentum indicator"""
        momentum = pd.Series(close) / pd.Series(close).shift(period) - 1
        return momentum * 100
    
    def next(self):
        """Execute strategy with risk management"""
        
        if self.position:
            # Check stop loss
            current_return = (self.data.Close[-1] - self.entry_price) / self.entry_price
            if current_return <= -self.stop_loss_pct / 100:
                self.position.close()
                return
            
            # Check profit target
            if current_return >= self.profit_target_pct / 100:
                self.position.close()
                return
        else:
            # Entry signals
            if self.momentum[-1] > 0 and self.momentum[-2] <= 0:
                # Momentum crossed above zero
                position_size = self.max_position_size
                self.buy(size=position_size)
                self.entry_price = self.data.Close[-1]
```

---

## Template 3: Multi-Timeframe Strategy

```python
# Example: strategies/multi_timeframe.py

from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd

class MultiTimeframeStrategy(Strategy):
    """
    Strategy combining multiple timeframes
    - Trend: Daily timeframe
    - Entry: 4-hour timeframe
    - Exit: Intraday signals
    """
    
    def init(self):
        """Initialize multi-timeframe indicators"""
        # Daily trend (slower indicators)
        daily_high = self.I(self._rolling_high, self.data.High, 20)
        daily_low = self.I(self._rolling_low, self.data.Low, 20)
        
        # 4-hour trend (medium indicators)
        hourly_ma = self.I(lambda x: pd.Series(x).rolling(10).mean(), self.data.Close)
        
        self.daily_trend = daily_high  # Trend reference
        self.hourly_ma = hourly_ma      # Entry reference
    
    @staticmethod
    def _rolling_high(high, period):
        return pd.Series(high).rolling(period).max()
    
    @staticmethod
    def _rolling_low(low, period):
        return pd.Series(low).rolling(period).min()
    
    def next(self):
        """Multi-timeframe trading logic"""
        if len(self) < 50:
            return
        
        # Entry: Price above hourly MA in uptrend
        if self.data.Close[-1] > self.hourly_ma[-1]:
            if not self.position and self.daily_trend[-1] > self.daily_trend[-2]:
                self.buy()
        
        # Exit: Price below hourly MA
        elif self.data.Close[-1] < self.hourly_ma[-1]:
            if self.position:
                self.position.close()
```

---

## Template 4: Machine Learning Strategy

```python
# Example: strategies/ml_strategy.py

from backtesting import Backtest, Strategy
import pandas as pd
import numpy as np

class MLStrategy(Strategy):
    """
    ML-based strategy with feature engineering
    - Features: Technical indicators
    - Model: Simple decision rules (expandable to sklearn/xgboost)
    - Entry: ML signal > threshold
    """
    
    ml_threshold = 0.6
    
    def init(self):
        """Initialize ML features"""
        self.features_history = []
    
    def _extract_features(self):
        """Extract features for ML model"""
        close = self.data.Close
        high = self.data.High
        low = self.data.Low
        volume = self.data.Volume
        
        # Feature engineering
        features = {
            'roc': (close[-1] - close[-20]) / close[-20],  # Rate of change
            'volatility': np.std(close[-20:]),             # Volatility
            'volume_trend': volume[-1] / np.mean(volume[-20:]),  # Volume trend
            'high_low_ratio': (high[-1] - low[-1]) / close[-1],  # Daily range
            'price_momentum': (close[-1] - close[-5]) / close[-5],  # 5-bar momentum
        }
        
        return features
    
    def _score_features(self, features):
        """Simple scoring function (replace with ML model)"""
        score = 0
        score += features['roc'] * 0.3
        score += features['price_momentum'] * 0.3
        score += (1 - features['high_low_ratio']) * 0.2
        score += min(features['volume_trend'] / 2, 0.2)
        return max(min(score, 1.0), 0.0)  # Normalize to 0-1
    
    def next(self):
        """ML-based trading logic"""
        if len(self) < 20:
            return
        
        features = self._extract_features()
        signal = self._score_features(features)
        
        if signal > self.ml_threshold:
            if not self.position:
                self.buy()
        elif signal < 0.4:
            if self.position:
                self.position.close()
```

---

## API Usage: Creating a Strategy via REST

### Step 1: Create Strategy via API

```bash
curl -X POST http://127.0.0.1:8000/api/strategies/api/create_strategy/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MyMovingAverage",
    "description": "SMA crossover strategy with risk management",
    "category": "technical",
    "strategy_type": "momentum",
    "framework": "backtesting.py",
    "strategy_code": "from backtesting import Backtest, Strategy\n..."
  }'
```

**Response:**
```json
{
  "id": 7,
  "name": "MyMovingAverage",
  "status": "pending",
  "created_at": "2025-12-02T16:05:52.152Z",
  "description": "SMA crossover strategy with risk management"
}
```

---

### Step 2: Generate Executable Code

```bash
curl -X POST http://127.0.0.1:8000/api/strategies/api/generate_executable_code/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_id": 7,
    "framework": "backtesting.py",
    "test_period": "1 year",
    "start_date": "2024-01-01",
    "end_date": "2025-01-01"
  }'
```

**Response:**
```json
{
  "status": "generated",
  "code_path": "C:\\...\\Backtest\\codes\\MyMovingAverage.py",
  "execution_time": 8.24,
  "message": "Strategy code saved successfully"
}
```

---

### Step 3: Run Backtest Validation

```bash
curl -X POST http://127.0.0.1:8000/api/production/strategies/validate-code/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_id": 7,
    "code_path": "C:\\...\\Backtest\\codes\\MyMovingAverage.py",
    "data_source": "yahoo",
    "symbol": "AAPL",
    "test_period": "1 year"
  }'
```

**Response:**
```json
{
  "strategy_id": 7,
  "status": "passed",
  "valid": true,
  "trades_executed": 45,
  "total_return": 12.5,
  "sharpe_ratio": 1.28,
  "drawdown": -8.5,
  "passed_checks": [
    "Syntax valid",
    "Required components present",
    "No security issues"
  ],
  "warnings": [
    "High transaction costs detected"
  ],
  "suggestions": [
    "Consider increasing trade frequency",
    "Optimize entry/exit conditions"
  ]
}
```

---

## Database Model: Validation Storage

```python
# StrategyValidation fields that get populated:

{
  "strategy_id": 7,
  "validation_type": "backtest",
  "status": "passed",  # pending, running, passed, failed, error
  "score": 75.5,  # 0-100
  "passed_checks": [
    "Syntax valid",
    "Required components present",
    "No security issues"
  ],
  "failed_checks": [],
  "warnings": [
    "High transaction costs",
    "Low profit factor"
  ],
  "recommendations": [
    "Optimize entry conditions",
    "Increase trade frequency"
  ],
  "validation_config": {
    "framework": "backtesting.py",
    "test_period": "1 year",
    "data_source": "yahoo",
    "symbol": "AAPL"
  },
  "execution_time": 8.24,  # seconds
  "completed_at": "2025-12-02T16:06:00Z"
}
```

---

## Full Workflow Example

### 1. Create Strategy
```python
strategy_code = '''
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd

class TrendStrategy(Strategy):
    n = 20
    
    def init(self):
        self.ma = self.I(lambda x: pd.Series(x).rolling(self.n).mean(), 
                         self.data.Close)
    
    def next(self):
        if self.data.Close[-1] > self.ma[-1]:
            if not self.position:
                self.buy()
        else:
            if self.position:
                self.position.close()
'''

# POST /api/strategies/api/create_strategy/
response = create_strategy(
    name="TrendFollower",
    strategy_code=strategy_code
)
strategy_id = response['id']  # 7
```

### 2. Generate Code
```python
# POST /api/strategies/api/generate_executable_code/
response = generate_code(
    strategy_id=7,
    framework="backtesting.py",
    test_period="1 year"
)
# Background validation starts automatically
```

### 3. Monitor Validation
```python
# GET /api/strategies/strategies/7/
response = get_strategy(7)
print(response['status'])  # 'invalid' or 'valid'
print(response['validations'])  # List of validation results
```

### 4. Check Results
```python
# GET /api/strategy-validations/
validations = get_validations(strategy_id=7)
for v in validations:
    print(f"Status: {v['status']}")
    print(f"Score: {v['score']}")
    print(f"Passed checks: {v['passed_checks']}")
    print(f"Warnings: {v['warnings']}")
    print(f"Recommendations: {v['recommendations']}")
```

---

## Best Practices

### 1. Strategy Structure
✓ Always define `init()` method  
✓ Always define `next()` method  
✓ Use `self.I()` for indicators  
✓ Use `self.buy()` and `self.position.close()` for trades  

### 2. Risk Management
✓ Implement position sizing  
✓ Use stop loss levels  
✓ Set profit targets  
✓ Limit max drawdown  

### 3. Code Quality
✓ Include docstrings  
✓ Use descriptive variable names  
✓ Add comments for complex logic  
✓ Keep functions small and focused  

### 4. Backtesting
✓ Use realistic slippage/commissions  
✓ Test on multiple symbols  
✓ Validate on out-of-sample data  
✓ Check for overfitting  

---

## Common Issues & Solutions

### Issue: "Missing required components"
**Cause:** Strategy missing `class`, `init()`, or `next()`  
**Solution:** Ensure all three are defined in strategy code

### Issue: "Invalid field names"
**Cause:** Using old field names in validation  
**Solution:** Use correct fields: `passed_checks`, `failed_checks`, `warnings`, `recommendations`

### Issue: Validation fails with FieldError
**Cause:** Database fields don't match code  
**Solution:** Run `python manage.py migrate` to update schema

### Issue: Strategy not validating automatically
**Cause:** Background thread not running  
**Solution:** Check logs for thread errors, ensure threading is enabled

---

## Next Steps

1. ✓ Create strategy via API (POST /api/strategies/api/create_strategy/)
2. ✓ Generate executable code (POST /api/strategies/api/generate_executable_code/)
3. ✓ Validation runs automatically in background
4. ✓ Monitor status (GET /api/strategies/strategies/{id}/)
5. ✓ Review validation results (GET /api/strategy-validations/)
6. ✓ Deploy to live trading (when ready)

---

**Last Updated:** December 2, 2025  
**Framework:** backtesting.py  
**Status:** ✓ Templates Ready for Use
